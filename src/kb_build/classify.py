"""Stage ② of the selection (ARCHITECTURE 1.1): one LLM verdict per requirement (ADR 0007).

Pure logic: gets the Pydantic AI model injected (ADR 0005), no boto3.
"""

import logging

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.models import AuditType, SourceName
from kb_build.cfn_types import load_cfn_types
from kb_build.extracted_models import Requirement
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

classify_agent = Agent(
    output_type=ToolOutput(Classification, name="classify_requirement",
                           description="Gib an, ob die Anforderung prüfbar ist."),
    deps_type=AuditType,
    retries=2,  # build only, no 29 s timeout (ADR 0005 limits the runtime agents to one retry)
    model_settings={"temperature": 0},  # same input, same selection (ARCHITECTURE 1.1)
)


@classify_agent.instructions
def _instructions(ctx: RunContext[AuditType]) -> str:
    return PROMPTS[ctx.deps]


@classify_agent.output_validator
def _validate(ctx: RunContext[AuditType], answer: Classification) -> Classification:
    if ctx.deps == "spec" or not answer.testable:
        return answer.model_copy(update={"cfn_resource_types": []})
    invalid = [t for t in answer.cfn_resource_types if t not in load_cfn_types()]
    if invalid or not answer.cfn_resource_types:
        raise ModelRetry(
            "Eine prüfbare Architektur-Anforderung braucht mindestens einen echten "
            f"CloudFormation-Typ (Format AWS::Dienst::Ressource). Diese gibt es nicht: {invalid}"
        )
    return answer


def classify_requirement(
    requirement: Requirement, source: SourceName, audit_type: AuditType, model: Model
) -> Classification:
    prompt = (
        f"Quelle: {source}\nID: {requirement.id}\nTitel: {requirement.title}\n"
        f"<anforderung>\n{requirement.text}\n</anforderung>"
    )
    return classify_agent.run_sync(prompt, model=model, deps=audit_type).output


class Judge:
    """Asks the LLM once per requirement, so the pinned pre-check never costs a second call.

    An answer that stays invalid after the retries excludes the requirement and shows up as
    `llm_error` in the report; it does not abort the whole run. Pinned anchors still abort.
    """

    def __init__(self, audit_type: AuditType, model: Model) -> None:
        self._audit_type, self._model = audit_type, model
        self._answers: dict[tuple[SourceName, str], Classification] = {}
        self.failed: set[tuple[SourceName, str]] = set()

    def __call__(self, source: SourceName, requirement: Requirement) -> Classification:
        key = (source, requirement.id)
        if key not in self._answers:
            self._answers[key] = self._ask(source, requirement)
        return self._answers[key]

    def _ask(self, source: SourceName, requirement: Requirement) -> Classification:
        try:
            return classify_requirement(requirement, source, self._audit_type, self._model)
        except UnexpectedModelBehavior as error:
            logger.warning("%s %s: invalid answer after retries: %s", source, requirement.id, error)
            self.failed.add((source, requirement.id))
            return Classification(testable=False, rationale="Antwort des Modells ungültig")
