"""Pure view logic for the conditions of a spec report: grouping, counts, texts; no Streamlit
(#61, ADR 0028)."""

from functools import cache
from typing import Literal

from pydantic import BaseModel

from govguard.audit_setup import conditions_for
from govguard.checks.conditions import affects
from govguard.condition_models import ConditionDef, ConditionResult, ConditionValue, LineRange
from govguard.models import AuditReport, Finding
from govguard_ui.report.review import category, of_source

GAP_SENTENCE = "Ihre {gaps} Lücken stehen unter „Nur wenn …“."


def condition_of(defs: list[ConditionDef], finding: Finding) -> ConditionDef | None:
    """The one condition a rule hangs on; None for a rule that applies to every project."""
    return next((c for c in defs
                 if affects(c, finding.rule_id, finding.primary_anchor)), None)


class GapGroups(BaseModel):
    common: list[Finding]  # gaps to clarify for every project
    by_condition: dict[str, list[Finding]]  # condition id -> gaps that matter only if it holds


def group_gaps(gaps: list[Finding], defs: list[ConditionDef],
               results: dict[str, ConditionResult]) -> GapGroups:
    """Each gap once: under its condition if the specification leaves that open, else common.
    With "yes" the rule counts for this project; with "no" it is N/A and no gap at all."""
    groups = GapGroups(common=[], by_condition={c.id: [] for c in defs})
    for gap in gaps:
        cond = condition_of(defs, gap)
        result = results.get(cond.id) if cond else None
        open_ = cond is not None and result is not None and result.value == "unstated"
        (groups.by_condition[cond.id] if cond and open_ else groups.common).append(gap)
    groups.by_condition = {k: v for k, v in groups.by_condition.items() if v}
    return groups


def lines_label(ranges: list[LineRange]) -> str:
    """"Zeile 47" or "Zeilen 5, 9–10"."""
    parts = [str(r.line_start) if r.line_start == r.line_end else f"{r.line_start}–{r.line_end}"
             for r in ranges]
    single = len(ranges) == 1 and ranges[0].line_start == ranges[0].line_end
    return f"{'Zeile' if single else 'Zeilen'} {', '.join(parts)}"


Kind = Literal["affirming", "denying"]


class Evidence(BaseModel):
    kind: Kind
    ranges: list[LineRange]


def evidence_of(result: ConditionResult) -> list[Evidence]:
    """"yes" shows the affirming lines, "no" the denying ones; a contradiction (yes with
    denying lines) shows both, the counter-evidence second."""
    shown = [Evidence(kind="affirming", ranges=result.affirming)] if result.value == "yes" else []
    if result.denying and result.value in ("yes", "no"):
        shown.append(Evidence(kind="denying", ranges=result.denying))
    return shown


def criterion(cond: ConditionDef, result: ConditionResult, kind: Kind,
              by_id: dict[str, ConditionDef]) -> str:
    """The criterion the lines satisfy; a derived "no" satisfies the one of its source."""
    if kind == "affirming":
        return cond.yes
    return by_id[result.derived_from].no if result.derived_from in by_id else cond.no


def rules_text(cond: ConditionDef) -> str:
    """"KI-VO Art. 4 und 50, DSGVO Art. 7": the articles by source, plus listed rules."""
    numbers: dict[str, list[str]] = {}
    for anchor in cond.anchors:
        prefix, _, number = anchor.rpartition(" ")
        numbers.setdefault(prefix, []).append(number)
    parts = [f"{prefix} {_enumerate(nums)}" for prefix, nums in numbers.items()]
    if cond.rule_ids:
        parts.append(f"{len(cond.rule_ids)} ausgewählte Prüfregeln")
    return _enumerate(parts) if cond.anchors and cond.rule_ids else ", ".join(parts)


def _enumerate(items: list[str]) -> str:
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} und {items[-1]}"


def effect_text(cond: ConditionDef, value: ConditionValue, rules: int, gaps: int) -> str:
    head = f"{rules} Prüfregeln ({rules_text(cond)})"
    if value == "no":
        return f"{head} sind nicht anwendbar."
    if value == "yes":
        return f"{head} werden geprüft."
    return f"{head} werden geprüft. {GAP_SENTENCE.format(gaps=gaps)}"


@cache
def _spec_definitions() -> list[ConditionDef]:
    return conditions_for("spec")


def condition_rows(report: AuditReport) -> list[tuple[ConditionDef, ConditionResult]]:
    """The conditions of the report in the order of the file; empty for an architecture audit
    and for a report stored before the pre-run (#60)."""
    if report.audit_type != "spec":
        return []
    return [(c, report.conditions[c.id]) for c in _spec_definitions() if c.id in report.conditions]


def rule_counts(
    defs: list[ConditionDef], findings: list[Finding], source: str | None = None
) -> dict[str, tuple[int, int]]:
    """Per condition: how many rules hang on it, and how many of them are gaps. The gaps count
    only the chosen source (None: all), like the section "Lücken" below the table."""
    counts = {c.id: (0, 0) for c in defs}
    for finding in findings:
        if cond := condition_of(defs, finding):
            rules, gaps = counts[cond.id]
            is_gap = category(finding) == "GAP" and bool(of_source([finding], source))
            counts[cond.id] = (rules + 1, gaps + is_gap)
    return counts
