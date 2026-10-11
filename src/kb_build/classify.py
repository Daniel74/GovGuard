"""Stage ② of the selection (ARCHITECTURE 1.1): one LLM verdict per requirement (ADR 0007).

Pure logic: gets the Pydantic AI model injected (ADR 0005), no boto3.
"""

import logging
from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.models import AuditType, SourceName
from kb_build.cfn_types import load_cfn_types
from kb_build.extracted_models import Requirement
from kb_build.judgement_cache import JudgementCache, cache_key
from kb_build.selection_models import Classification

logger = logging.getLogger("kb_build")

PROMPTS: dict[AuditType, str] = {
    "architecture": """\
Du bewertest genau eine Anforderung aus einem Regelwerk für Behörden-IT.
Frage: Lässt sich ein Verstoß oder die Einhaltung an der Konfiguration von Ressourcen in einem
einzelnen CloudFormation-Template erkennen (z. B. IAM-Policies, Verschlüsselung, Logging,
Netzwerk, Zugriffsrechte)? Auch allgemeine Prinzipien wie "geringste Berechtigungen" zählen,
wenn sie sich an Ressourcen festmachen lassen. Nein gilt bei Konto- oder Organisationsebene
(z. B. Support-Rolle, CloudTrail, Passwort-Richtlinie), Personal, Verträgen und Prozessen.
- "testable": ja oder nein. "rationale": ein deutscher Satz zur Begründung.
- "cfn_resource_types": die betroffenen CloudFormation-Typen (z. B. AWS::S3::Bucket),
  der wichtigste zuerst. Ist die Anforderung nicht prüfbar, bleibt die Liste leer.""",
    "spec": """\
Du bewertest genau eine Anforderung aus einem Regelwerk für Behörden-IT.
Frage: Kann eine Spezifikation (Freitext oder OpenAPI) Hinweise enthalten, ob die Anforderung
erfüllt oder verletzt wird, oder sich dazu bewusst ausschweigen? Dann ist sie prüfbar; fehlende
Angaben ergeben später eine Warnung. Beispiele: Rechtsgrundlagen, Zwecke, Löschfristen,
Verschlüsselung, Zugriffsrechte, Auftragsverarbeiter, Übermittlung in Drittländer.
Nein gilt nur für Pflichten der Behörde, die keine Spezifikation berühren (z. B.
Bußgeldverfahren, Befugnisse der Aufsicht, Zertifizierung).
- "testable": ja oder nein. "rationale": ein deutscher Satz zur Begründung.
- "cfn_resource_types" bleibt leer.""",
}

SCOPE_PROMPT = """\
Der Prüfumfang (Dienste, für die wir Prüfregeln führen) umfasst: {services}.
Nenne den wichtigsten Typ zuerst, auch wenn er außerhalb des Prüfumfangs liegt;
über die Relevanz entscheidet danach der Code."""


@dataclass(frozen=True)
class Brief:
    audit_type: AuditType
    instructions: str


def build_brief(audit_type: AuditType, scope: dict[str, list[str]] | None = None) -> Brief:
    """The scope belongs to the architecture prompt only (ADR 0011)."""
    text = PROMPTS[audit_type]
    if audit_type == "architecture" and scope:
        text += "\n" + SCOPE_PROMPT.format(services=", ".join(scope))
    return Brief(audit_type, text)


classify_agent = Agent(
    output_type=ToolOutput(Classification, name="classify_requirement",
                           description="Gib an, ob die Anforderung prüfbar ist."),
    deps_type=Brief,
    retries=2,  # build only, no 29 s timeout (ADR 0005 limits the runtime agents to one retry)
    model_settings={"temperature": 0},  # same input, same selection (ARCHITECTURE 1.1)
)


@classify_agent.instructions
def _instructions(ctx: RunContext[Brief]) -> str:
    return ctx.deps.instructions


@classify_agent.output_validator
def _validate(ctx: RunContext[Brief], answer: Classification) -> Classification:
    if ctx.deps.audit_type == "spec" or not answer.testable:
        return answer.model_copy(update={"cfn_resource_types": []})
    invalid = [t for t in answer.cfn_resource_types if t not in load_cfn_types()]
    if invalid or not answer.cfn_resource_types:
        raise ModelRetry(
            "Eine prüfbare Architektur-Anforderung braucht mindestens einen echten "
            f"CloudFormation-Typ (Format AWS::Dienst::Ressource). Diese gibt es nicht: {invalid}"
        )
    return answer


def classify_requirement(
    requirement: Requirement, source: SourceName, audit_type: AuditType, model: Model,
    scope: dict[str, list[str]] | None = None,
) -> Classification:
    prompt = (
        f"Quelle: {source}\nID: {requirement.id}\nTitel: {requirement.title}\n"
        f"<anforderung>\n{requirement.text}\n</anforderung>"
    )
    return classify_agent.run_sync(prompt, model=model, deps=build_brief(audit_type, scope)).output


class Judge:
    """Asks the LLM once per requirement; a known answer comes from the cache (ADR 0011).

    An answer that stays invalid after the retries excludes the requirement and shows up as
    `llm_error` in the report; it does not abort the whole run, and it is never cached.
    """

    def __init__(
        self, audit_type: AuditType, model: Model,
        scope: dict[str, list[str]] | None = None, cache: JudgementCache | None = None,
    ) -> None:
        self.audit_type, self.model_id = audit_type, model.model_name
        self._model, self._scope = model, scope
        self._brief = build_brief(audit_type, scope)
        self._cache = cache if cache is not None else JudgementCache()
        self._answers: dict[tuple[SourceName, str], Classification] = {}
        self.failed: set[tuple[SourceName, str]] = set()

    def __call__(self, source: SourceName, requirement: Requirement) -> Classification:
        key = (source, requirement.id)
        if key not in self._answers:
            self._answers[key] = self._cached_or_ask(source, requirement)
        return self._answers[key]

    def _cached_or_ask(self, source: SourceName, requirement: Requirement) -> Classification:
        cache_key_ = cache_key(requirement, self._brief.instructions, self.model_id)
        known = self._cache.get(cache_key_)
        if known is not None:
            return known
        answer = self._ask(source, requirement)
        if (source, requirement.id) not in self.failed:
            self._cache.put(cache_key_, answer)
        return answer

    def _ask(self, source: SourceName, requirement: Requirement) -> Classification:
        try:
            return classify_requirement(
                requirement, source, self.audit_type, self._model, self._scope)
        except UnexpectedModelBehavior as error:
            logger.warning("%s %s: invalid answer after retries: %s", source, requirement.id, error)
            self.failed.add((source, requirement.id))
            return Classification(testable=False, rationale="Antwort des Modells ungültig")
