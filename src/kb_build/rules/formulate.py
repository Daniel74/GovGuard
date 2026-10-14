"""Stage 5 of the build (ARCHITECTURE 1): one rule per selected requirement (ADR 0005).

Pure logic: gets the Pydantic AI model injected, no boto3. The code adds identity and origin.
"""

import logging
from dataclasses import dataclass, field

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, Rule, RuleCatalog, RuleDraft
from govguard.text import normalize
from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.gates import (
    Anchors,
    GateCounts,
    check_rules,
    invalid_cross_references,
    is_quoted,
    requirements_by_anchor,
    usage_line,
)
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.scope import Scope
from kb_build.rules.criteria import criteria_problems
from kb_build.rules.prompts import PROMPTS, USER_PROMPT
from kb_build.rules.violation_judge import judge_violation
from kb_build.select.models import SelectedRequirement, Selection

logger = logging.getLogger("kb_build")

# Per audit type: prefix of the rule ID
ID_PREFIX: dict[AuditType, str] = {"architecture": "ARCH", "spec": "SPEC"}
TOOL_NAME = "formulate_rule"
TOOL_DESCRIPTION = "Gib genau eine Prüfregel zur Anforderung ab."
FORMULATE_RETRIES = 6  # build only, no 29 s timeout; Groq needs more than Haiku (ADR 0014)


@dataclass(frozen=True)
class FormulateDeps:
    """Run dependencies of the agent (ADR 0005): what the validator checks against."""

    audit_type: AuditType
    selected: SelectedRequirement  # source, rationale and resource types come from here
    requirement: Requirement
    anchors: Anchors  # every requirement of every source, for the cross references
    properties: PropertyIndex  # real properties per type, for the invented ones
    scope: Scope  # criteria may name nothing else (#19)
    counts: GateCounts = field(default_factory=GateCounts)  # shared by all rules of one run (#27)
    judge_counts: GateCounts = field(default_factory=GateCounts)  # absences sent back (#29)


formulate_agent = Agent(
    output_type=ToolOutput(RuleDraft, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=FormulateDeps,
    retries=FORMULATE_RETRIES,
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
async def _validate(ctx: RunContext[FormulateDeps], draft: RuleDraft) -> RuleDraft:
    """Same checks as the gate, but early: the model gets a second chance (ADR 0005)."""
    problems = _code_problems(ctx.deps, draft)
    if not problems and ctx.deps.audit_type == "spec":  # the judge costs a call: only valid drafts
        problems = await _absence_problems(ctx, draft)
    if problems:
        reason, deps = " ".join(problems), ctx.deps
        # the build log shows what the model reads (CONTEXT.md: Korrektur)
        logger.info("%s %s %s retry %d: %s", deps.audit_type, deps.selected.source,
                    deps.requirement.id, ctx.retry + 1, reason)
        raise ModelRetry(reason)
    ctx.deps.counts.retries += ctx.retry  # an accepted answer after n retries cost n retries
    return draft


async def _absence_problems(ctx: RunContext[FormulateDeps], draft: RuleDraft) -> list[str]:
    """Open world (ADR 0020): a violation the spec does not stipulate is only WARN (#29)."""
    try:
        check = await judge_violation(draft.violation_if, ctx.model, ctx.usage)
    except UnexpectedModelBehavior:  # fail closed: _complete_rule aborts the build
        ctx.deps.judge_counts.llm_errors += 1
        raise
    if not check.describes_absence:
        return []
    ctx.deps.judge_counts.retries += 1
    return [f"„violation_if“ „{draft.violation_if}“ beschreibt ein Fehlen: {check.reason} "
            "In der offenen Welt ist Fehlen nur WARN. Beschreibe eine Festlegung der "
            "Spezifikation, die der Anforderung widerspricht, auch einen erklärten Verzicht "
            "oder Aufschub."]


def _code_problems(deps: FormulateDeps, draft: RuleDraft) -> list[str]:
    problems = []
    if not is_quoted(deps.requirement, draft.source_quote):
        deviation = _deviation(deps.requirement.text, draft.source_quote)
        problems.append(f"Das Zitat steht nicht wörtlich im Text in <anforderung>. {deviation}")
    if deps.audit_type == "architecture":
        problems += criteria_problems(
            draft, deps.selected.cfn_resource_types, deps.properties, deps.scope)
    invalid = invalid_cross_references(draft, deps.selected.source, deps.anchors)
    if invalid:
        problems.append(f"Diese Querverweise gibt es nicht in einer anderen Quelle, lass sie weg: "
                        f"{invalid}")
    return problems


def user_prompt(deps: FormulateDeps) -> str:
    selected, requirement = deps.selected, deps.requirement
    types = selected.cfn_resource_types
    return USER_PROMPT.format(
        source=selected.source, id=requirement.id, title=requirement.title,
        rationale=selected.rationale, text=requirement.text,
        types=f"Ressourcentypen: {', '.join(types)}\n" if types else "",
    )


def formulate_rule(deps: FormulateDeps, model: Model, usage: RunUsage | None = None) -> RuleDraft:
    """`usage` collects the tokens of every request, retries and judge included."""
    return formulate_agent.run_sync(user_prompt(deps), model=model, deps=deps, usage=usage).output


def _complete_rule(deps: FormulateDeps, model: Model, total: RunUsage) -> Rule:
    """The LLM writes the draft; identity and origin come from the selection, never the LLM."""
    selected, requirement, usage = deps.selected, deps.requirement, RunUsage()
    try:  # one usage per call: Pydantic AI checks its request limit against it
        draft = formulate_rule(deps, model, usage)
    except UnexpectedModelBehavior as error:  # fail closed: no rule may silently go missing
        deps.counts.retries += FORMULATE_RETRIES  # every retry was spent
        deps.counts.llm_errors += 1
        raise ValueError(f"{selected.source} {requirement.id}: no valid rule: {error}") from error
    finally:
        total.incr(usage)  # failed retries cost tokens too
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
    rules, counts, judge_counts, usage = [], GateCounts(), GateCounts(), RunUsage()
    try:
        for n, selected in enumerate(selection.selected, start=1):
            requirement = by_id[(selected.source, selected.requirement_id)]
            deps = FormulateDeps(selection.audit_type, selected, requirement, anchors,
                                 properties, scope, counts, judge_counts)
            rules.append(_complete_rule(deps, model, usage))
            logger.info("%s %d/%d %s", selection.audit_type, n, len(selection.selected),
                        rules[-1].id)
    finally:  # an llm_error aborts the build; the quality report still counts it
        logger.info(usage_line(selection.audit_type, usage))
        logger.info(counts.line(selection.audit_type, "formulate"))
        if selection.audit_type == "spec":  # architecture rules are never judged
            logger.info(judge_counts.line(selection.audit_type, "judge"))
    used = {s.source for s in selection.selected}
    catalog = RuleCatalog(
        audit_type=selection.audit_type, model_id=model.model_name, rules=rules,
        source_versions={s.source: s.version for s in sources if s.source in used},
    )
    check_rules(catalog, selection, sources, scope)
    return catalog
