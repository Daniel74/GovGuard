"""Stage 5 of the build (ARCHITECTURE 1): one rule per selected requirement (ADR 0005).

Pure logic: gets the Pydantic AI model injected, no boto3. The code adds identity and origin.
"""

from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput
from pydantic_ai.models import Model

from govguard.models import AuditType, RuleDraft, SourceName
from kb_build.extracted_models import Requirement
from kb_build.gates import Anchors, invalid_cross_references, is_quoted
from kb_build.selection_models import SelectedRequirement

PROMPT = """\
Du formulierst aus genau einer Anforderung eines Regelwerks für Behörden-IT genau eine
Prüfregel für ein {audit}. Inhalte auf Deutsch, außer dem Zitat.
- "source_quote": wörtlicher Auszug (mind. 15 Zeichen) aus dem Text in <anforderung>, der die
  Kernpflicht trägt. Original-Sprache, nichts übersetzen, kürzen oder ergänzen.
- "title": kurzer Titel, höchstens 8 Wörter.
- "compliant_if" / "violation_if": je ein Satz, woran man {subject} Einhaltung bzw. Verstoß
  erkennt.
- "recommendation": ein Satz zur Abhilfe.
- "cross_references": nur Anforderungen einer anderen Quelle, die du sicher kennst, im exakten
  Format, z. B. "BSI GS++ DET.3.1", "DSGVO Art. 32", "AWS FSBP S3.1". Im Zweifel leer lassen."""

PROMPTS: dict[AuditType, str] = {
    "architecture": PROMPT.format(audit="Architektur-Audit eines CloudFormation-Templates",
                                  subject="am Template"),
    "spec": PROMPT.format(audit="Spec-Audit einer fachlichen Spezifikation",
                          subject="an der Spezifikation"),
}

USER_PROMPT = (
    "Quelle: {source}\nID: {id}\nTitel: {title}\nBegründung der Auswahl: {rationale}\n{types}"
    "<anforderung>\n{text}\n</anforderung>"
)
TOOL_NAME = "formulate_rule"
TOOL_DESCRIPTION = "Gib genau eine Prüfregel zur Anforderung ab."


@dataclass(frozen=True)
class FormulateDeps:
    """Run dependencies of the agent (ADR 0005): what the validator checks against."""

    audit_type: AuditType
    source: SourceName
    requirement: Requirement
    anchors: Anchors  # every requirement of every source, for the cross references


formulate_agent = Agent(
    output_type=ToolOutput(RuleDraft, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=FormulateDeps,
    retries=2,  # build only, no 29 s timeout (ADR 0005 limits the runtime agents to one retry)
    model_settings={"temperature": 0},
)


@formulate_agent.instructions
def _instructions(ctx: RunContext[FormulateDeps]) -> str:
    return PROMPTS[ctx.deps.audit_type]


@formulate_agent.output_validator
def _validate(ctx: RunContext[FormulateDeps], draft: RuleDraft) -> RuleDraft:
    """Same checks as the gate, but early: the model gets a second chance (ADR 0005)."""
    problems = []
    if not is_quoted(ctx.deps.requirement, draft.source_quote):
        problems.append("Das Zitat steht nicht wörtlich im Text in <anforderung>.")
    invalid = invalid_cross_references(draft, ctx.deps.source, ctx.deps.anchors)
    if invalid:
        problems.append(f"Diese Querverweise gibt es nicht in einer anderen Quelle, lass sie weg: "
                        f"{invalid}")
    if problems:
        raise ModelRetry(" ".join(problems))
    return draft


def user_prompt(selected: SelectedRequirement, requirement: Requirement) -> str:
    types = selected.cfn_resource_types
    return USER_PROMPT.format(
        source=selected.source, id=requirement.id, title=requirement.title,
        rationale=selected.rationale, text=requirement.text,
        types=f"Ressourcentypen: {', '.join(types)}\n" if types else "",
    )


def formulate_rule(selected: SelectedRequirement, deps: FormulateDeps, model: Model) -> RuleDraft:
    prompt = user_prompt(selected, deps.requirement)
    return formulate_agent.run_sync(prompt, model=model, deps=deps).output
