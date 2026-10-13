"""Stage 5 of the build (ARCHITECTURE 1): one rule per selected requirement (ADR 0005).

Pure logic: gets the Pydantic AI model injected, no boto3. The code adds identity and origin.
"""

import logging
from dataclasses import dataclass

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.models import AuditType, Rule, RuleCatalog, RuleDraft
from govguard.text import normalize
from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.gates import (
    Anchors,
    check_rules,
    invalid_cross_references,
    is_quoted,
    requirements_by_anchor,
)
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.scope import Scope
from kb_build.rules.criteria import criteria_problems
from kb_build.select.models import SelectedRequirement, Selection

logger = logging.getLogger("kb_build")

PROMPT = """\
Du formulierst aus genau einer Anforderung eines Regelwerks für Behörden-IT genau eine
Prüfregel für ein {audit}. Inhalte auf Deutsch, außer dem Zitat.
- "source_quote": wörtlicher Auszug aus dem Text in <anforderung>, der die Kernpflicht trägt:
  ein Satz oder Satzteil, mind. 15 Zeichen und höchstens 25 Wörter, Zeichen für Zeichen
  kopiert. Original-Sprache, nichts übersetzen, kürzen, ergänzen oder grammatisch anpassen.
- "title": kurzer Titel, höchstens 8 Wörter.
- "compliant_if" / "violation_if": je ein Satz, woran man {subject} Einhaltung bzw. Verstoß
  erkennt.
- "recommendation": ein Satz zur Abhilfe.
- "cross_references": nur Anforderungen einer anderen Quelle, die du sicher kennst, im exakten
  Format, z. B. "BSI GS++ DET.3.1", "DSGVO Art. 32", "AWS FSBP S3.1". Im Zweifel leer lassen."""

ARCHITECTURE_CRITERIA = """
- Architektur: "compliant_if" und "violation_if" nennen mindestens einen der Ressourcentypen
  wörtlich (z. B. AWS::RDS::DBInstance) und die konkrete Eigenschaft mit Wert (z. B.
  DeletionProtection: true). Keine Wörter, die Wissen außerhalb des Templates brauchen, z. B.
  "relevant", "erforderlich", "angemessen", "entsprechend". Gilt die Pflicht nur für eine
  Variante (z. B. bestimmte Engines oder Protokolle), nenne diese Bedingung."""

# Per audit type: prefix of the rule ID and system prompt
ID_PREFIX: dict[AuditType, str] = {"architecture": "ARCH", "spec": "SPEC"}
PROMPTS: dict[AuditType, str] = {
    "architecture": PROMPT.format(audit="Architektur-Audit eines CloudFormation-Templates",
                                  subject="am Template") + ARCHITECTURE_CRITERIA,
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
    selected: SelectedRequirement  # source, rationale and resource types come from here
    requirement: Requirement
    anchors: Anchors  # every requirement of every source, for the cross references
    properties: PropertyIndex  # real properties per type, for the invented ones
    scope: Scope  # criteria may name nothing else (#19)


formulate_agent = Agent(
    output_type=ToolOutput(RuleDraft, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=FormulateDeps,
    retries=3,  # build only, no 29 s timeout (ADR 0005 limits the runtime agents to one retry)
    model_settings={"temperature": 0},
)


@formulate_agent.instructions
def _instructions(ctx: RunContext[FormulateDeps]) -> str:
    return PROMPTS[ctx.deps.audit_type]


def _deviation(text: str, quote: str) -> str:
    """Where the quote leaves the text: the longest quoted start found, then both continuations."""
    words, text = normalize(quote).split(" "), normalize(text)
    for n in range(len(words) - 1, 0, -1):
        start = text.find(" ".join(words[:n]))
        if start >= 0:
            rest = text[start + len(" ".join(words[:n])):].split()
            return (f"Ab „{' '.join(words[n:n + 5])}“ weicht es ab; im Text steht dort "
                    f"„{' '.join(rest[:5])}“.")
    return "Schon der Anfang des Zitats fehlt im Text."


@formulate_agent.output_validator
def _validate(ctx: RunContext[FormulateDeps], draft: RuleDraft) -> RuleDraft:
    """Same checks as the gate, but early: the model gets a second chance (ADR 0005)."""
    problems = []
    if not is_quoted(ctx.deps.requirement, draft.source_quote):
        deviation = _deviation(ctx.deps.requirement.text, draft.source_quote)
        problems.append(f"Das Zitat steht nicht wörtlich im Text in <anforderung>. {deviation}")
    if ctx.deps.audit_type == "architecture":
        problems += criteria_problems(
            draft, ctx.deps.selected.cfn_resource_types, ctx.deps.properties,
            ctx.deps.scope,
        )
    invalid = invalid_cross_references(draft, ctx.deps.selected.source, ctx.deps.anchors)
    if invalid:
        problems.append(f"Diese Querverweise gibt es nicht in einer anderen Quelle, lass sie weg: "
                        f"{invalid}")
    if problems:
        raise ModelRetry(" ".join(problems))
    return draft


def user_prompt(deps: FormulateDeps) -> str:
    selected, requirement = deps.selected, deps.requirement
    types = selected.cfn_resource_types
    return USER_PROMPT.format(
        source=selected.source, id=requirement.id, title=requirement.title,
        rationale=selected.rationale, text=requirement.text,
        types=f"Ressourcentypen: {', '.join(types)}\n" if types else "",
    )


def formulate_rule(deps: FormulateDeps, model: Model) -> RuleDraft:
    return formulate_agent.run_sync(user_prompt(deps), model=model, deps=deps).output


def _complete_rule(deps: FormulateDeps, model: Model) -> Rule:
    """The LLM writes the draft; identity and origin come from the selection, never the LLM."""
    selected, requirement = deps.selected, deps.requirement
    try:
        draft = formulate_rule(deps, model)
    except UnexpectedModelBehavior as error:  # fail closed: no rule may silently go missing
        raise ValueError(f"{selected.source} {requirement.id}: no valid rule: {error}") from error
    return Rule(
        **draft.model_dump(),
        id=f"{ID_PREFIX[deps.audit_type]}-{selected.source}-{requirement.id.replace(' ', '')}",
        audit_type=deps.audit_type, source=selected.source,
        primary_anchor=requirement.primary_anchor, selection_rationale=selected.rationale,
        cfn_resource_types=selected.cfn_resource_types,
    )


def formulate_rules(
    model: Model, selection: Selection, sources: list[ExtractedSource],
    properties: PropertyIndex, scope: Scope,
) -> RuleCatalog:
    """One rule per selected requirement, in selection order; then the gate (ARCHITECTURE 1)."""
    anchors = requirements_by_anchor(sources)
    by_id = {(s.source, r.id): r for s in sources for r in s.requirements}
    rules = []
    for n, selected in enumerate(selection.selected, start=1):
        requirement = by_id[(selected.source, selected.requirement_id)]
        deps = FormulateDeps(
            selection.audit_type, selected, requirement, anchors, properties, scope)
        rules.append(_complete_rule(deps, model))
        logger.info("%s %d/%d %s", selection.audit_type, n, len(selection.selected), rules[-1].id)
    used = {s.source for s in selection.selected}
    catalog = RuleCatalog(
        audit_type=selection.audit_type, model_id=model.model_name, rules=rules,
        source_versions={s.source: s.version for s in sources if s.source in used},
    )
    check_rules(catalog, selection, sources, scope)
    return catalog
