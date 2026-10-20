"""Audit engine: pure audit logic, gets the model injected (ADR 0005). No boto3."""

import asyncio
from collections.abc import Callable, Iterable

from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.calls.audit_packages import PackageRequest, package_requests
from govguard.calls.fail_judge import judge_fails
from govguard.calls.inventory import resource_inventory
from govguard.checks.audit_gates import completeness_problems
from govguard.checks.corrections import AuditValidationError, Corrections
from govguard.checks.evidence import evidence_of
from govguard.models import (
    SEVERITY,
    AuditReport,
    Finding,
    FindingDraft,
    Progress,
    Rule,
    RuleCatalog,
    Status,
    Trace,
)
from govguard.open_world import AuditInput, audit_input

__all__ = ["AuditValidationError", "InputTooLongError", "check_input_length", "overall_status",
           "run_audit"]

type OnProgress = Callable[[Progress], None]
MAX_INPUT_CHARS = 100_000  # largest preset fits the Lambda timeout (ADR 0018, 0023)


class InputTooLongError(ValueError):
    """Raised before the first LLM call, so a too long input costs nothing."""

    def __init__(self, length: int) -> None:
        super().__init__(f"Eingabe zu lang: {with_thousand_dots(length)} Zeichen, erlaubt sind "
                         f"höchstens {with_thousand_dots(MAX_INPUT_CHARS)}.")


def with_thousand_dots(number: int) -> str:
    return f"{number:,}".replace(",", ".")


def check_input_length(input_text: str) -> None:
    """Callers may check before building the model, run_audit checks again (ADR 0023)."""
    if len(input_text) > MAX_INPUT_CHARS:
        raise InputTooLongError(len(input_text))


def overall_status(statuses: Iterable[Status]) -> Status:
    return max(statuses, key=SEVERITY.__getitem__)


def run_audit(
    catalog: RuleCatalog, input_text: str, model: Model, trace: Trace,
    on_progress: OnProgress | None = None,
) -> AuditReport:
    """on_progress gets each phase and finished package; the audit logic stays pure (ADR 0023)."""
    check_input_length(input_text)
    corrections = Corrections()
    given = audit_input(catalog.audit_type, input_text)  # the code decides the world (#46)
    try:
        drafts = asyncio.run(_drafts(catalog, given, model, corrections,
                                     on_progress or (lambda _: None)))
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
        fail_judge=corrections.fail_judge,
        closed_world=given.world is None,
    )


async def _drafts(
    catalog: RuleCatalog, given: AuditInput, model: Model, corrections: Corrections,
    on_progress: OnProgress,
) -> list[FindingDraft]:
    """In an open world every FAIL goes to the judge (#31, #46)."""
    if catalog.audit_type == "architecture":
        drafts = await _architecture_drafts(catalog, given, model, corrections, on_progress)
    else:
        drafts = await _counted(
            package_requests(catalog.rules, given, None, model, corrections), on_progress)
    if given.world is None:  # closed world: a missing setting is the default, the FAIL stays
        return drafts
    if any(draft.status == "FAIL" for draft in drafts):  # the judge only runs on a FAIL
        on_progress(Progress(phase="fail_judge"))
    return await judge_fails(catalog.rules, drafts, given, model, corrections)


async def _architecture_drafts(
    catalog: RuleCatalog, given: AuditInput, model: Model, corrections: Corrections,
    on_progress: OnProgress,
) -> list[FindingDraft]:
    """N/A by code via the resource inventory, the rest goes to the model."""
    on_progress(Progress(phase="inventory"))
    inventory = await resource_inventory(catalog.rules, given.text, model, corrections)
    to_model = [rule for rule in catalog.rules if inventory.applies(rule)]
    drafts = [_na_by_code(rule, inventory.na_rationale)
              for rule in catalog.rules if not inventory.applies(rule)]
    return drafts + await _counted(package_requests(
        to_model, given, inventory.na_forbidden, model, corrections), on_progress)


async def _counted(
    requests: list[PackageRequest], on_progress: OnProgress
) -> list[FindingDraft]:
    """All packages at once; each finished one is reported."""
    total, done = len(requests), 0
    on_progress(Progress(phase="packages", packages_total=total))

    async def run_and_count(request: PackageRequest) -> list[FindingDraft]:
        nonlocal done
        drafts = await request
        done += 1
        on_progress(Progress(phase="packages", packages_done=done, packages_total=total))
        return drafts

    answers = await asyncio.gather(*(run_and_count(r) for r in requests))
    return [draft for answer in answers for draft in answer]


def _na_by_code(rule: Rule, rationale: str) -> FindingDraft:
    return FindingDraft(rule_id=rule.id, status="N/A", line_start=None, line_end=None,
                        rationale=rationale, recommendation=None)


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
