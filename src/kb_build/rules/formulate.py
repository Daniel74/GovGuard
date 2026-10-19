"""Stage 5 of the build (ARCHITECTURE 1): the rule of one selected requirement (ADR 0005).

Pure logic: gets the Pydantic AI model injected, no boto3. The code adds identity and origin.
The run over the whole selection is catalog.py's task.
"""

from dataclasses import dataclass, field

from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, Rule, RuleDraft
from kb_build.build_log import INVALID_ANSWER, logged_retries, raise_if_no_answer
from kb_build.extract.models import Requirement
from kb_build.gates import Anchors, GateCounts, invalid_cross_references, is_quoted, quote_deviation
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.scope import Scope
from kb_build.rules.criteria import criteria_problems
from kb_build.rules.prompts import KIND_LINES, PROMPTS, USER_PROMPT
from kb_build.rules.violation_judge import judge_violation
from kb_build.select.models import SelectedRequirement

# Per audit type: prefix of the rule ID
ID_PREFIX: dict[AuditType, str] = {"architecture": "ARCH", "spec": "SPEC"}
TOOL_NAME = "formulate_rule"
TOOL_DESCRIPTION = "Gib genau eine Prüfregel zur Anforderung ab."
FORMULATE_RETRIES = 6  # build only, no 29 s timeout; Groq needs more than Haiku (ADR 0014)


def rule_id(audit_type: AuditType, source: str, requirement_id: str) -> str:
    """Stable across builds, e.g. "SPEC-DSGVO-Art.5": the frozen catalog matches on it."""
    return f"{ID_PREFIX[audit_type]}-{source}-{requirement_id.replace(' ', '')}"


@dataclass(frozen=True)
class FormulateDeps:
    """Run dependencies of the agent (ADR 0005): what the validator checks against."""

    audit_type: AuditType
    selected: SelectedRequirement  # source, rationale and resource types come from here
    requirement: Requirement
    anchors: Anchors  # every requirement of every source, for the cross references
    properties: PropertyIndex  # real properties per type, for the invented ones
    scope: Scope  # criteria may name nothing else (#19)
    # Per rule, the run sums them up; each retry counts once, at the gate that sent it back
    counts: GateCounts = field(default_factory=GateCounts)  # schema and code problems (#27)
    judge_counts: GateCounts = field(default_factory=GateCounts)  # absences sent back (#29)
    judged: set[str] = field(default_factory=set)  # texts the judge sent back, for the log (#30)


formulate_agent = Agent(
    output_type=ToolOutput(RuleDraft, name=TOOL_NAME, description=TOOL_DESCRIPTION),
    deps_type=FormulateDeps,
    retries=FORMULATE_RETRIES,
    model_settings={"temperature": 0},
)


@formulate_agent.instructions
def _instructions(ctx: RunContext[FormulateDeps]) -> str:
    return PROMPTS[ctx.deps.audit_type]


@formulate_agent.output_validator
async def _validate(ctx: RunContext[FormulateDeps], draft: RuleDraft) -> RuleDraft:
    """Same checks as the gate, but early: the model gets a second chance (ADR 0005)."""
    problems = _code_problems(ctx.deps, draft)
    if not problems and ctx.deps.audit_type == "spec":  # the judge costs a call: only valid drafts
        problems = await _absence_problems(ctx, draft)
        ctx.deps.judged.update(problems)  # the build log names the judge as gate (#30)
    if problems:
        raise ModelRetry(" ".join(problems))  # the build log shows it, see formulate_rule
    _count_own_retries(ctx)
    return draft


def _count_own_retries(ctx: RunContext[FormulateDeps]) -> None:
    """n retries so far: the judge's are counted by the judge, the rest by formulate."""
    ctx.deps.counts.retries += ctx.retry - ctx.deps.judge_counts.retries


async def _absence_problems(ctx: RunContext[FormulateDeps], draft: RuleDraft) -> list[str]:
    """Open world (ADR 0020): a violation the spec does not stipulate is only WARN (#29)."""
    try:
        check = await judge_violation(draft.violation_if, ctx.model, ctx.usage, _label(ctx.deps))
    except UnexpectedModelBehavior:  # fail closed: complete_rule aborts the build
        _count_own_retries(ctx)
        ctx.deps.judge_counts.llm_errors += 1
        raise
    if not check.describes_absence:
        return []
    if ctx.retry < FORMULATE_RETRIES:  # the last rejection aborts instead of retrying
        ctx.deps.judge_counts.retries += 1
    return [f"„violation_if“ „{draft.violation_if}“ beschreibt ein Fehlen: {check.reason} "
            "In der offenen Welt ist Fehlen nur WARN. Beschreibe eine Festlegung der "
            "Spezifikation, die der Anforderung widerspricht, auch einen erklärten Verzicht "
            "oder Aufschub."]


def code_quote(requirement: Requirement) -> str | None:
    """A part of a decomposed legal act is quoted by the code, never by the LLM (ADR 0026)."""
    quote = requirement.attributes.get("quote")
    return quote if isinstance(quote, str) else None


def _code_problems(deps: FormulateDeps, draft: RuleDraft) -> list[str]:
    problems = []
    if code_quote(deps.requirement) is None and not is_quoted(deps.requirement, draft.source_quote):
        deviation = quote_deviation(deps.requirement.text, draft.source_quote)
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
        kind=KIND_LINES.get(str(requirement.attributes.get("kind")), ""),
    )


def _label(deps: FormulateDeps) -> str:
    return f"{deps.audit_type} {deps.selected.source} {deps.requirement.id}"


def formulate_rule(deps: FormulateDeps, model: Model, usage: RunUsage | None = None) -> RuleDraft:
    """`usage` collects the tokens of every request, retries and judge included.

    The build log shows each retry with the reason the model reads (CONTEXT.md: Korrektur, #30).
    """
    with logged_retries(_label(deps), lambda text: "judge" if text in deps.judged else "code"):
        return formulate_agent.run_sync(
            user_prompt(deps), model=model, deps=deps, usage=usage).output


def complete_rule(deps: FormulateDeps, model: Model, total: RunUsage) -> Rule:
    """The LLM writes the draft; identity and origin come from the selection, never the LLM."""
    selected, requirement, usage = deps.selected, deps.requirement, RunUsage()
    try:  # one usage per call: Pydantic AI checks its request limit against it
        draft = formulate_rule(deps, model, usage)
    except INVALID_ANSWER as error:  # fail closed: no rule is lost
        raise_if_no_answer(error)
        if not deps.judge_counts.llm_errors:  # a failed judge has counted already
            deps.counts.retries += FORMULATE_RETRIES - deps.judge_counts.retries  # all spent
            deps.counts.llm_errors += 1
        raise ValueError(f"{selected.source} {requirement.id}: no valid rule: {error}") from error
    finally:
        total.incr(usage)  # failed retries cost tokens too
    quote = code_quote(requirement) or draft.source_quote
    return Rule(
        **draft.model_dump() | {"source_quote": quote},
        id=rule_id(deps.audit_type, selected.source, requirement.id),
        audit_type=deps.audit_type, source=selected.source,
        primary_anchor=requirement.primary_anchor, selection_rationale=selected.rationale,
        cfn_resource_types=selected.cfn_resource_types,
    )

