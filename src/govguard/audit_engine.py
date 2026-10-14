"""Audit engine: pure audit logic, gets the model injected (ADR 0005). No boto3."""

import asyncio
import json
from collections.abc import Iterable

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext, ToolOutput
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.audit_gates import answer_problems, completeness_problems, without_equal_duplicates
from govguard.corrections import AuditValidationError, Corrections, downgrades_of
from govguard.evidence import MAX_SPAN, evidence_of, numbered, without_unproven_verdict
from govguard.inventory import resource_inventory
from govguard.models import (
    AuditReport,
    AuditResponse,
    Finding,
    FindingDraft,
    Rule,
    RuleCatalog,
    Status,
    Trace,
)

SYSTEM_PROMPT = f"""\
Du bist ein Compliance-Prüfer für Behörden-IT. Bewerte die Eingabe gegen jede Prüfregel.
- PASS: Einhaltung ist in der Eingabe belegt.
- FAIL: Ein Verstoß ist in der Eingabe belegt.
- WARN: Aus der Eingabe nicht entscheidbar.
- N/A: Die Prüfregel ist auf die Eingabe nicht anwendbar.
Jede Zeile der Eingabe beginnt mit ihrer Nummer, z. B. "12| ". Belege per Zeilenbereich:
"line_start" und "line_end" nennen die Zeilen, die den Befund belegen (höchstens {MAX_SPAN} Zeilen).
Bei PASS und FAIL sind sie Pflicht, sonst null.
Bei WARN und FAIL ist "recommendation" Pflicht. Schreibe Begründungen auf Deutsch."""
# Spec audit only, open world; a template is a closed world: missing means default (ADR 0020)
SPEC_FAIL_RULE = """\
Spezifikation (offene Welt): Was die Eingabe nicht erwähnt, kann anderswo geregelt sein. \
Beschreibt "violation_if" ein Fehlen, belegt fehlender Text nur "nicht beschrieben": WARN. FAIL \
nur, wenn die Belegzeilen etwas festlegen, das der Prüfregel widerspricht; "rationale" nennt es."""

PACKAGE_SIZE = 10  # rules per model call; 166 architecture rules -> 17 parallel calls
GROQ_MAX_PARALLEL = 2  # ~110,000 tokens/min per slot measured (#26), Groq tier allows 250,000

# Worst status wins; N/A only if every finding is N/A (DESIGN 2.1)
_SEVERITY: dict[Status, int] = {"N/A": 0, "PASS": 1, "WARN": 2, "FAIL": 3}


class AuditDeps(BaseModel):  # deps_type of the audit agent, input for the code checks
    rules: list[Rule]
    input_text: str
    na_forbidden: str | None  # prompt hint; set when N/A was already decided by code (ADR 0011)
    corrections: Corrections  # shared by all packages; the validator reports into it (#27)
    reason_sent: bool = False  # the code sent the package back with reasons (#27)


_OUTPUT = {"name": "submit_audit", "description": "Gib genau einen Befund je Prüfregel ab.",
           "strict": True}  # static schema, every field required (ADR 0017)
_SETTINGS = {"temperature": 0, "max_tokens": 8000}  # same status; a loop ends in ~25 s (#28)
# Bedrock: forced tool (ADR 0005); Groq: json_schema with constrained decoding (ADR 0016)
_AGENTS = {
    system: Agent(output_type=output_type, instructions=SYSTEM_PROMPT, deps_type=AuditDeps,
                  model_settings=_SETTINGS, retries=1)  # one retry: within the 180 s (ADR 0018)
    for system, output_type in [("bedrock", ToolOutput(AuditResponse, **_OUTPUT)),
                                ("groq", NativeOutput(AuditResponse, **_OUTPUT))]
}
_MAX_PARALLEL = {"groq": GROQ_MAX_PARALLEL}  # Bedrock: no limit, all packages at once


def _validate(ctx: RunContext[AuditDeps], response: AuditResponse) -> AuditResponse:
    """Downgrade first, then check: what the code can fix needs no retry (ADR 0017)."""
    text, last = ctx.deps.input_text, ctx.last_attempt
    original = response.findings
    if ctx.retry:  # once per package: one retry at most
        ctx.deps.corrections.record_retry(ctx.deps.reason_sent)
    checked = [without_unproven_verdict(f, text, last) for f in response.findings]
    expected = {rule.id for rule in ctx.deps.rules}
    response = AuditResponse(findings=without_equal_duplicates(checked))
    problems = answer_problems(expected, response.findings, text, ctx.deps.na_forbidden)
    ctx.deps.corrections.record_attempt(
        sorted(expected), downgrades_of(original, checked), problems, last)
    if problems:
        ctx.deps.reason_sent = True
        raise ModelRetry("\n".join(p.text for p in problems))
    return response


def _status_rule(ctx: RunContext[AuditDeps]) -> str:
    return SPEC_FAIL_RULE if ctx.deps.rules[0].audit_type == "spec" else ""  # one type per catalog


for _agent in _AGENTS.values():  # the same gates for both models (ADR 0016)
    _agent.output_validator(_validate)
    _agent.instructions(_status_rule)


def overall_status(statuses: Iterable[Status]) -> Status:
    return max(statuses, key=_SEVERITY.__getitem__)


def run_audit(catalog: RuleCatalog, input_text: str, model: Model, trace: Trace) -> AuditReport:
    corrections = Corrections()
    try:
        drafts = asyncio.run(_drafts(catalog, input_text, model, corrections))
    except (ModelAPIError, UnexpectedModelBehavior) as error:
        raise corrections.fail_closed(error) from error
    if problems := completeness_problems({rule.id for rule in catalog.rules}, drafts):
        raise AuditValidationError(problems)  # merged packages: one finding per rule
    findings = _complete_findings(catalog, drafts, input_text, corrections)
    return AuditReport(
        audit_type=catalog.audit_type,
        overall_status=overall_status(f.status for f in findings),
        findings=findings,
        model_id=model.model_name,
        trace=trace,
        unassigned_corrections=corrections.unassigned({rule.id for rule in catalog.rules}),
        retries=corrections.retries,
    )


async def _drafts(
    catalog: RuleCatalog, input_text: str, model: Model, corrections: Corrections
) -> list[FindingDraft]:
    """N/A by code via the resource inventory; a template in a spec audit goes to the model."""
    if catalog.audit_type != "architecture":
        return await _ask_in_packages(catalog.rules, input_text, None, model, corrections)
    inventory = await resource_inventory(catalog.rules, input_text, model, corrections)
    to_model = [rule for rule in catalog.rules if inventory.applies(rule)]
    drafts = [_na_by_code(rule, inventory.na_rationale)
              for rule in catalog.rules if not inventory.applies(rule)]
    return drafts + await _ask_in_packages(
        to_model, input_text, inventory.na_forbidden, model, corrections)


async def _ask_in_packages(
    rules: list[Rule], input_text: str, na_forbidden: str | None, model: Model,
    corrections: Corrections,
) -> list[FindingDraft]:
    """Packages in parallel, so the audit stays within the 180 s (ADR 0018); Groq throttled."""
    packages = [rules[i:i + PACKAGE_SIZE] for i in range(0, len(rules), PACKAGE_SIZE)]
    slots = asyncio.Semaphore(_MAX_PARALLEL.get(_provider(model), len(packages) or 1))

    async def ask(package: list[Rule]) -> list[FindingDraft]:
        async with slots:
            deps = AuditDeps(rules=package, input_text=input_text, na_forbidden=na_forbidden,
                             corrections=corrections)
            return await _ask_model(deps, model)

    answers = await asyncio.gather(*(ask(p) for p in packages))
    return [draft for answer in answers for draft in answer]


def _na_by_code(rule: Rule, rationale: str) -> FindingDraft:
    return FindingDraft(rule_id=rule.id, status="N/A", line_start=None, line_end=None,
                        rationale=rationale, recommendation=None)


async def _ask_model(deps: AuditDeps, model: Model) -> list[FindingDraft]:
    agent = _AGENTS[_provider(model)]
    result = await agent.run(_user_prompt(deps), model=model, deps=deps)
    return result.output.findings


def _provider(model: Model) -> str:
    """Groq or Bedrock; test models (FunctionModel) behave like Bedrock."""
    return "groq" if model.system == "groq" else "bedrock"


def _user_prompt(deps: AuditDeps) -> str:
    rules = [
        r.model_dump(include={"id", "title", "compliant_if", "violation_if"})
        for r in deps.rules
    ]
    hint = f"{deps.na_forbidden}\n\n" if deps.na_forbidden else ""
    return (
        f"Prüfregeln:\n{json.dumps(rules, ensure_ascii=False, indent=1)}\n\n{hint}"
        f"Eingabe:\n<eingabe>\n{numbered(deps.input_text)}\n</eingabe>"
    )


def _complete_findings(
    catalog: RuleCatalog, drafts: list[FindingDraft], input_text: str, corrections: Corrections
) -> list[Finding]:
    """Cut the evidence, add title, anchor and cross references, sort by resource type.

    Duplicates across sources end up next to each other (ADR 0011); spec rules keep catalog order.
    """
    by_rule = {d.rule_id: d for d in drafts}
    return [
        Finding(
            **by_rule[rule.id].model_dump(),
            evidence=evidence_of(by_rule[rule.id], input_text),
            title=rule.title,
            primary_anchor=rule.primary_anchor,
            cross_references=rule.cross_references,
            **corrections.for_rule(rule.id),
        )
        for rule in sorted(catalog.rules, key=lambda rule: rule.cfn_resource_types[:1])
    ]
