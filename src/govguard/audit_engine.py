"""Audit engine: pure audit logic, gets the model injected (ADR 0005). No boto3."""

import json
from collections import Counter
from collections.abc import Iterable

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, RunContext, ToolOutput, UnexpectedModelBehavior
from pydantic_ai.models import Model

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
from govguard.text import MIN_QUOTE_LENGTH, contains_quote, template_resource_types

SYSTEM_PROMPT = """\
Du bist ein Compliance-Prüfer für Behörden-IT. Bewerte die Eingabe gegen jede Prüfregel.
- PASS: Einhaltung ist in der Eingabe belegt.
- FAIL: Ein Verstoß ist in der Eingabe belegt.
- WARN: Aus der Eingabe nicht entscheidbar; was fehlt, ist WARN, nicht FAIL.
- N/A: Die Prüfregel ist auf die Eingabe nicht anwendbar.
Bei PASS und FAIL ist "evidence" Pflicht.
Jedes "evidence" ist ein wörtliches Zitat aus der Eingabe (mindestens 15 Zeichen).
Bei WARN und FAIL ist "recommendation" Pflicht. Schreibe Begründungen auf Deutsch."""

# Rules without a matching resource type never reach the model (ADR 0007)
NA_BY_CODE = "Ressourcentyp nicht im Template"
NA_FORBIDDEN = ("Die Eingabe ist ein CloudFormation-Template. Jede Prüfregel betrifft einen "
                "Ressourcentyp im Template: N/A ist hier verboten.")

# Worst status wins; N/A only if every finding is N/A (DESIGN 2.1)
_SEVERITY: dict[Status, int] = {"N/A": 0, "PASS": 1, "WARN": 2, "FAIL": 3}


class AuditValidationError(Exception):
    """LLM answer still invalid after the retry; fail closed (HTTP 502)."""


class AuditDeps(BaseModel):  # deps_type of the audit agent, input for the code checks
    catalog: RuleCatalog
    input_text: str
    is_template: bool  # CloudFormation JSON: N/A was already set by code (ADR 0007)


audit_agent = Agent(
    output_type=ToolOutput(AuditResponse, name="submit_audit",
                           description="Gib genau einen Befund je Prüfregel ab."),
    instructions=SYSTEM_PROMPT,
    deps_type=AuditDeps,
    retries=1,  # exactly one retry, 29 s API Gateway timeout
)


@audit_agent.output_validator
def _validate(ctx: RunContext[AuditDeps], response: AuditResponse) -> AuditResponse:
    expected = {rule.id for rule in ctx.deps.catalog.rules}
    problems = _completeness_problems(expected, response)
    problems += [p for f in response.findings if (p := _field_problem(f, ctx.deps.input_text))]
    if ctx.deps.is_template:
        problems += [f"{f.rule_id}: N/A ist verboten, der Ressourcentyp kommt im Template vor"
                     for f in response.findings if f.status == "N/A"]
    if problems:
        raise ModelRetry("\n".join(problems))
    return response


def _completeness_problems(expected: set[str], response: AuditResponse) -> list[str]:
    """Exactly one finding per rule sent to the model, no unknown rule IDs (DESIGN 2.2 step 2)."""
    counts = Counter(f.rule_id for f in response.findings)
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
    is_arch = catalog.audit_type == "architecture"  # a template in a spec audit goes to the model
    types = template_resource_types(input_text) if is_arch else None  # None: no template
    to_model, not_applicable = _split_by_template(catalog, types)
    drafts = [_na_by_code(rule) for rule in not_applicable]
    if to_model.rules:
        deps = AuditDeps(catalog=to_model, input_text=input_text, is_template=types is not None)
        drafts += _ask_model(deps, model)
    findings = _complete_findings(catalog, drafts)
    return AuditReport(
        audit_type=catalog.audit_type,
        overall_status=overall_status(f.status for f in findings),
        findings=findings,
        model_id=model.model_name,
        trace=trace,
    )


def _split_by_template(
    catalog: RuleCatalog, types: set[str] | None
) -> tuple[RuleCatalog, list[Rule]]:
    """For CloudFormation JSON, rules without a matching resource type skip the model (ADR 0007)."""
    if types is None:
        return catalog, []
    applies = {rule.id: bool(types & set(rule.cfn_resource_types)) for rule in catalog.rules}
    to_model = [rule for rule in catalog.rules if applies[rule.id]]
    not_applicable = [rule for rule in catalog.rules if not applies[rule.id]]
    return catalog.model_copy(update={"rules": to_model}), not_applicable


def _na_by_code(rule: Rule) -> FindingDraft:
    return FindingDraft(rule_id=rule.id, status="N/A", evidence=None,
                        rationale=NA_BY_CODE, recommendation=None)


def _ask_model(deps: AuditDeps, model: Model) -> list[FindingDraft]:
    try:
        result = audit_agent.run_sync(_user_prompt(deps), model=model, deps=deps)
    except UnexpectedModelBehavior as error:  # still invalid after the retry: fail closed
        raise AuditValidationError(str(error)) from error
    return result.output.findings


def _user_prompt(deps: AuditDeps) -> str:
    rules = [
        r.model_dump(include={"id", "title", "compliant_if", "violation_if"})
        for r in deps.catalog.rules
    ]
    hint = f"{NA_FORBIDDEN}\n\n" if deps.is_template else ""
    return (
        f"Prüfregeln:\n{json.dumps(rules, ensure_ascii=False, indent=1)}\n\n{hint}"
        f"Eingabe:\n<eingabe>\n{deps.input_text}\n</eingabe>"
    )


def _complete_findings(catalog: RuleCatalog, drafts: list[FindingDraft]) -> list[Finding]:
    """Add title, anchor and cross references from the catalog, in catalog order."""
    by_rule = {d.rule_id: d for d in drafts}
    return [
        Finding(
            **by_rule[rule.id].model_dump(),
            title=rule.title,
            primary_anchor=rule.primary_anchor,
            cross_references=rule.cross_references,
        )
        for rule in catalog.rules
    ]
