"""Stage ② of the selection (ARCHITECTURE 1.1): one LLM verdict per requirement (ADR 0007).

Pure logic: gets the Pydantic AI model injected (ADR 0005), no boto3.
"""

import json
import logging
from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.exceptions import ModelHTTPError
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, SourceName
from kb_build.extract.models import Requirement
from kb_build.reference.cfn_types import load_cfn_types
from kb_build.reference.scope import Scope
from kb_build.select.judgement_cache import JudgementCache, cache_key, prompt_version
from kb_build.select.models import Classification

logger = logging.getLogger("kb_build")

PROMPTS: dict[AuditType, str] = {
    "architecture": """\
Du bewertest genau eine Anforderung aus einem Regelwerk für Behörden-IT.
Frage: Lässt sich ein Verstoß oder die Einhaltung an der Konfiguration von Ressourcen in einem
einzelnen CloudFormation-Template erkennen (z. B. IAM-Policies, Verschlüsselung, Logging,
Netzwerk, Zugriffsrechte)? Auch allgemeine Prinzipien wie "geringste Berechtigungen" zählen,
wenn sie sich an Ressourcen festmachen lassen. Nein gilt bei Verträgen und Prozessen.
- "testable": ja oder nein. "rationale": ein deutscher Satz zur Begründung.
- "scope_level": Wessen Pflicht ist das? "template" = das Workload selbst, am Template
  erkennbar (Bucket, Rolle, Funktion). "account" = Konto oder Organisation (CloudTrail-Bucket,
  Support-Rolle, Passwort-Richtlinie, Root-MFA). "people" = Personen und Prozesse
  (MFA für Administratoren, Schulung, Verträge). "provider" = Cloud-Anbieter (Rechenzentrum,
  Hypervisor).
  Hängt die Pflicht nur an Konto, Personen oder Anbieter, wähle das, auch wenn eine Ressource
  sie technisch umsetzen könnte, z. B. an einer bestimmten Konto-Ressource wie dem
  CloudTrail-Bucket. Gilt sie zugleich für jede Ressource des Workloads (z. B. Block Public
  Access an jedem Bucket), wähle "template".
- "cfn_resource_types": alle CloudFormation-Typen, an deren Konfiguration sich die Anforderung
  zeigt (z. B. bei Verschlüsselung jeder Speicher- und Transportdienst wie AWS::S3::Bucket,
  AWS::KinesisFirehose::DeliveryStream), der wichtigste zuerst. Nur Typen, die es in
  CloudFormation gibt. Ist die Anforderung nicht prüfbar, bleibt die Liste leer.""",
    "spec": """\
Du bewertest genau eine Anforderung aus einem Regelwerk für Behörden-IT.
Eine Spezifikation ist die fachliche Beschreibung eines Vorhabens, nicht nur die technische:
Sie nennt z. B. Zwecke, Rechtsgrundlagen, Rollen, Abläufe und Auftragsverarbeiter.
Frage: Kann eine Spezifikation (Freitext oder OpenAPI) Hinweise enthalten, ob die Anforderung
erfüllt oder verletzt wird, oder sich dazu bewusst ausschweigen? Dann ist sie prüfbar; fehlende
Angaben ergeben später eine Warnung. Beispiele: Rechtsgrundlagen, Zwecke, Löschfristen,
Verschlüsselung, Zugriffsrechte, Auftragsverarbeiter, Übermittlung in Drittländer.
Nein gilt nur für Pflichten der Behörde, die keine Spezifikation berühren (z. B.
Bußgeldverfahren, Befugnisse der Aufsicht, Zertifizierung).
- "testable": ja oder nein. "rationale": ein deutscher Satz zur Begründung.
- "scope_level" bleibt "template". "cfn_resource_types" bleibt leer.""",
}

SCOPE_PROMPT = """\
Der Prüfumfang (Dienste, für die wir Prüfregeln führen) umfasst: {services}.
Nenne den wichtigsten Typ zuerst, auch wenn er außerhalb des Prüfumfangs liegt;
über die Relevanz entscheidet danach der Code."""

USER_PROMPT = "Quelle: {source}\nID: {id}\nTitel: {title}\n<anforderung>\n{text}\n</anforderung>"
TOOL_NAME = "classify_requirement"
TOOL_DESCRIPTION = "Gib an, ob die Anforderung prüfbar ist."


@dataclass(frozen=True)
class ClassifyDeps:
    """Run dependencies of the agent (ADR 0005): built once per audit type."""

    audit_type: AuditType
    instructions: str


def build_deps(audit_type: AuditType, scope: Scope | None = None) -> ClassifyDeps:
    """The scope belongs to the architecture prompt only (ADR 0011)."""
    text = PROMPTS[audit_type]
    if audit_type == "architecture" and scope is not None:
        text += "\n" + SCOPE_PROMPT.format(services=", ".join(scope.services))
    return ClassifyDeps(audit_type, text)


def request_version(deps: ClassifyDeps) -> str:
    """Prompt version of the cache key: instructions, user message and tool definition."""
    schema = json.dumps(Classification.model_json_schema(), sort_keys=True)
    return prompt_version(deps.instructions, USER_PROMPT, TOOL_NAME, TOOL_DESCRIPTION, schema)


classify_agent = Agent(
    output_type=ToolOutput(Classification, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=ClassifyDeps,
    retries=2,  # build only, no 29 s timeout (ADR 0005 limits the runtime agents to one retry)
    model_settings={"temperature": 0},  # same input, same selection (ARCHITECTURE 1.1)
)


@classify_agent.instructions
def _instructions(ctx: RunContext[ClassifyDeps]) -> str:
    return ctx.deps.instructions


@classify_agent.output_validator
def _validate(ctx: RunContext[ClassifyDeps], answer: Classification) -> Classification:
    if ctx.deps.audit_type == "spec":
        return answer.model_copy(update={"cfn_resource_types": [], "scope_level": "template"})
    if not answer.testable:
        return answer.model_copy(update={"cfn_resource_types": []})
    known = load_cfn_types()
    real = [t for t in answer.cfn_resource_types if t in known]
    invalid = [t for t in answer.cfn_resource_types if t not in known]
    if not real:
        raise ModelRetry(
            "Eine prüfbare Architektur-Anforderung braucht mindestens einen echten "
            f"CloudFormation-Typ (Format AWS::Dienst::Ressource). Diese gibt es nicht: {invalid}"
        )
    if invalid:  # the code drops invented types, no retry needed (#18)
        logger.info("dropped invented resource types: %s", invalid)
    return answer.model_copy(update={"cfn_resource_types": real})


def classify_requirement(
    requirement: Requirement, source: SourceName, deps: ClassifyDeps, model: Model,
    usage: RunUsage | None = None,
) -> Classification:
    prompt = USER_PROMPT.format(
        source=source, id=requirement.id, title=requirement.title, text=requirement.text)
    return classify_agent.run_sync(prompt, model=model, deps=deps, usage=usage).output


class Judge:
    """Asks the LLM once per requirement; a known answer comes from the cache (ADR 0011).

    An answer that stays invalid after the retries gives `None` (outcome `llm_error`);
    it does not abort the whole run, and it is never cached.
    """

    def __init__(
        self, audit_type: AuditType, model: Model,
        scope: Scope | None = None, cache: JudgementCache | None = None,
    ) -> None:
        self.audit_type, self.model_id = audit_type, model.model_name
        self._model, self._deps = model, build_deps(audit_type, scope)
        self._version = request_version(self._deps)
        self._cache = cache if cache is not None else JudgementCache()
        self._answers: dict[tuple[SourceName, str], Classification | None] = {}
        self.usage = RunUsage()  # tokens of the calls the cache could not answer

    def __call__(self, source: SourceName, requirement: Requirement) -> Classification | None:
        key = (source, requirement.id)
        if key not in self._answers:
            self._answers[key] = self._cached_or_ask(source, requirement)
        return self._answers[key]

    def _cached_or_ask(self, source: SourceName, requirement: Requirement) -> Classification | None:
        key = cache_key(requirement, self._version, self.model_id)
        known = self._cache.get(key)
        if known is not None:
            return known
        answer = self._ask(source, requirement)
        if answer is not None:
            self._cache.put(key, answer)
        return answer

    def _ask(self, source: SourceName, requirement: Requirement) -> Classification | None:
        usage = RunUsage()  # one per call: Pydantic AI checks its request limit against it
        try:
            return classify_requirement(requirement, source, self._deps, self._model, usage)
        except (UnexpectedModelBehavior, ModelHTTPError) as error:
            if isinstance(error, ModelHTTPError) and error.status_code != 400:
                raise  # 401, 429 and server errors are no verdict on the requirement
            logger.warning("%s %s: invalid answer after retries: %s", source, requirement.id, error)
            return None
        finally:
            self.usage.incr(usage)  # failed retries cost tokens too
