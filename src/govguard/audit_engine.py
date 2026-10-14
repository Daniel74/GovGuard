"""Audit engine: pure audit logic, gets the model injected (ADR 0005). No boto3."""

import asyncio
import json
from collections import Counter
from collections.abc import Iterable

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model

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
from govguard.text import MIN_QUOTE_LENGTH, contains_quote

SYSTEM_PROMPT = """\
Du bist ein Compliance-Prüfer für Behörden-IT. Bewerte die Eingabe gegen jede Prüfregel.
- PASS: Einhaltung ist in der Eingabe belegt.
- FAIL: Ein Verstoß ist in der Eingabe belegt.
- WARN: Aus der Eingabe nicht entscheidbar; was fehlt, ist WARN, nicht FAIL.
- N/A: Die Prüfregel ist auf die Eingabe nicht anwendbar.
Bei PASS und FAIL ist "evidence" Pflicht.
Jedes "evidence" ist ein wörtliches Zitat aus der Eingabe (mindestens 15 Zeichen).
Bei WARN und FAIL ist "recommendation" Pflicht. Schreibe Begründungen auf Deutsch."""

PACKAGE_SIZE = 10  # rules per model call; 166 architecture rules -> 17 parallel calls

# Worst status wins; N/A only if every finding is N/A (DESIGN 2.1)
_SEVERITY: dict[Status, int] = {"N/A": 0, "PASS": 1, "WARN": 2, "FAIL": 3}


class AuditValidationError(Exception):
    """LLM answer still invalid after the retry; fail closed (HTTP 502)."""


class AuditDeps(BaseModel):  # deps_type of the audit agent, input for the code checks
    rules: list[Rule]
    input_text: str
    na_forbidden: str | None  # prompt hint; set when N/A was already decided by code (ADR 0011)


audit_agent = Agent(
    output_type=ToolOutput(AuditResponse, name="submit_audit",
                           description="Gib genau einen Befund je Prüfregel ab."),
    instructions=SYSTEM_PROMPT,
    deps_type=AuditDeps,
    retries=1,  # exactly one retry, 29 s API Gateway timeout
)


@audit_agent.output_validator
def _validate(ctx: RunContext[AuditDeps], response: AuditResponse) -> AuditResponse:
    expected = {rule.id for rule in ctx.deps.rules}
    problems = _completeness_problems(expected, response.findings)
    problems += [p for f in response.findings if (p := _field_problem(f, ctx.deps.input_text))]
    if ctx.deps.na_forbidden:
        problems += [f"{f.rule_id}: N/A ist verboten, der Ressourcentyp kommt in der Eingabe vor"
                     for f in response.findings if f.status == "N/A"]
    if problems:
        raise ModelRetry("\n".join(problems))
    return response


def _completeness_problems(expected: set[str], drafts: list[FindingDraft]) -> list[str]:
    """Exactly one finding per expected rule, no unknown rule IDs (DESIGN 2.2 step 2)."""
    counts = Counter(f.rule_id for f in drafts)
    missing = sorted(expected - counts.keys())
    unknown = sorted(counts.keys() - expected)
    duplicate = sorted(rule_id for rule_id, n in counts.items() if n > 1)
    return [
        f"{label}: {', '.join(ids)}"
        for label, ids in [("Befund fehlt für", missing), ("Unbekannte rule_id", unknown),
                           ("Mehr als ein Befund für", duplicate)]
        if ids
    ]


def _field_problem(finding: FindingDraft, input_text: str) -> str | None:
    """PASS/FAIL need evidence, any evidence is quoted verbatim; WARN/FAIL need a recommendation."""
    if finding.status in ("PASS", "FAIL") and not finding.evidence:
        return f"{finding.rule_id}: Beleg fehlt (Pflicht bei {finding.status})"
    if finding.evidence and not contains_quote(input_text, finding.evidence):
        return (f"{finding.rule_id}: Beleg ist kein wörtliches Zitat aus der Eingabe "
                f"(mind. {MIN_QUOTE_LENGTH} Zeichen)")
    if finding.status in ("WARN", "FAIL") and not finding.recommendation:
        return f"{finding.rule_id}: Empfehlung fehlt (Pflicht bei {finding.status})"
    return None


def overall_status(statuses: Iterable[Status]) -> Status:
    return max(statuses, key=_SEVERITY.__getitem__)


def run_audit(catalog: RuleCatalog, input_text: str, model: Model, trace: Trace) -> AuditReport:
    try:
        drafts = asyncio.run(_drafts(catalog, input_text, model))
    except UnexpectedModelBehavior as error:  # still invalid after the retry: fail closed
        raise AuditValidationError(str(error)) from error
    if problems := _completeness_problems({rule.id for rule in catalog.rules}, drafts):
        raise AuditValidationError("\n".join(problems))  # merged packages: one finding per rule
    findings = _complete_findings(catalog, drafts)
    return AuditReport(
        audit_type=catalog.audit_type,
        overall_status=overall_status(f.status for f in findings),
        findings=findings,
        model_id=model.model_name,
        trace=trace,
    )


async def _drafts(catalog: RuleCatalog, input_text: str, model: Model) -> list[FindingDraft]:
    """N/A by code via the resource inventory; a template in a spec audit goes to the model."""
    if catalog.audit_type != "architecture":
        return await _ask_in_packages(catalog.rules, input_text, None, model)
    inventory = await resource_inventory(catalog.rules, input_text, model)
    to_model = [rule for rule in catalog.rules if inventory.applies(rule)]
    drafts = [_na_by_code(rule, inventory.na_rationale)
              for rule in catalog.rules if not inventory.applies(rule)]
    return drafts + await _ask_in_packages(to_model, input_text, inventory.na_forbidden, model)


async def _ask_in_packages(
    rules: list[Rule], input_text: str, na_forbidden: str | None, model: Model
) -> list[FindingDraft]:
    """All packages run at once to stay below the 29 s API Gateway timeout (ADR 0011)."""
    packages = [rules[i:i + PACKAGE_SIZE] for i in range(0, len(rules), PACKAGE_SIZE)]
    answers = await asyncio.gather(*(
        _ask_model(AuditDeps(rules=p, input_text=input_text, na_forbidden=na_forbidden), model)
        for p in packages
    ))
    return [draft for answer in answers for draft in answer]


def _na_by_code(rule: Rule, rationale: str) -> FindingDraft:
    return FindingDraft(rule_id=rule.id, status="N/A", evidence=None,
                        rationale=rationale, recommendation=None)


async def _ask_model(deps: AuditDeps, model: Model) -> list[FindingDraft]:
    result = await audit_agent.run(_user_prompt(deps), model=model, deps=deps)
    return result.output.findings


def _user_prompt(deps: AuditDeps) -> str:
    rules = [
        r.model_dump(include={"id", "title", "compliant_if", "violation_if"})
        for r in deps.rules
    ]
    hint = f"{deps.na_forbidden}\n\n" if deps.na_forbidden else ""
    return (
        f"Prüfregeln:\n{json.dumps(rules, ensure_ascii=False, indent=1)}\n\n{hint}"
        f"Eingabe:\n<eingabe>\n{deps.input_text}\n</eingabe>"
    )


def _complete_findings(catalog: RuleCatalog, drafts: list[FindingDraft]) -> list[Finding]:
    """Add title, anchor and cross references from the catalog, sorted by resource type.

    Duplicates across sources end up next to each other (ADR 0011); spec rules keep catalog order.
    """
    by_rule = {d.rule_id: d for d in drafts}
    return [
        Finding(
            **by_rule[rule.id].model_dump(),
            title=rule.title,
            primary_anchor=rule.primary_anchor,
            cross_references=rule.cross_references,
        )
        for rule in sorted(catalog.rules, key=lambda rule: rule.cfn_resource_types[:1])
    ]
