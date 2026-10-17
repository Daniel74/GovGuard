"""Pure view logic for reading an audit report; no Streamlit (#11)."""

from collections import Counter
from typing import Literal

from pydantic import BaseModel

from govguard.models import AuditReport, Expected, Finding, Status

# GAP: WARN without evidence lines, the input does not describe the rule (CONTEXT: Lücke)
Category = Literal["FAIL", "WARN", "GAP", "PASS", "N/A"]
CATEGORIES: tuple[Category, ...] = ("FAIL", "WARN", "GAP", "PASS", "N/A")
CONTEXT_LINES = 4  # shown above the evidence, so the reader sees where it stands


class ExpectedCheck(BaseModel):  # one line of the comparison with the preset's expected result
    label: str  # "Gesamtstatus" or the primary anchor of a required finding
    expected: Status
    actual: Status | str  # "fehlt": the anchor has no finding in the report
    rule_id: str | None  # finding to jump to

    @property
    def ok(self) -> bool:
        return self.actual == self.expected


def expected_checks(report: AuditReport, expected: Expected) -> list[ExpectedCheck]:
    """Shown, never re-rolled (ADR 0023): overall status first, then each required finding."""
    by_anchor = {finding.primary_anchor: finding for finding in report.findings}
    checks = [ExpectedCheck(label="Gesamtstatus", expected=expected.overall_status,
                            actual=report.overall_status, rule_id=None)]
    for required in expected.required_findings:
        finding = by_anchor.get(required.anchor)
        checks.append(ExpectedCheck(
            label=required.anchor, expected=required.status,
            actual=finding.status if finding else "fehlt",
            rule_id=finding.rule_id if finding else None))
    return checks


def category(finding: Finding) -> Category:
    """A downgrade always needs review, even without lines: it is never a gap (ADR 0017)."""
    is_gap = finding.line_start is None and finding.downgraded_from is None
    return "GAP" if finding.status == "WARN" and is_gap else finding.status


def category_counts(findings: list[Finding]) -> dict[Category, int]:
    counted = Counter(category(finding) for finding in findings)
    return {name: counted[name] for name in CATEGORIES}


def visible_findings(
    findings: list[Finding], categories: set[Category], source: str | None
) -> list[Finding]:
    """The finding list: gaps stand below it as a checklist; FAIL first, then by line."""
    shown = [f for f in findings if category(f) in categories - {"GAP"}
             and source in (None, source_of(f))]
    return sorted(shown, key=lambda f: (CATEGORIES.index(category(f)), f.line_start or 10**9))


def source_of(finding: Finding) -> str:
    """Rule ids read <SPEC|ARCH>-<SOURCE>-<requirement>, e.g. ARCH-CIS-3.1.4."""
    return finding.rule_id.split("-")[1]


class DocumentLine(BaseModel):
    number: int  # 1-based, counted like the engine counts (str.splitlines)
    text: str
    marked: bool  # evidence line of the selected finding


class DocumentWindow(BaseModel):
    lines: list[DocumentLine]
    hidden_above: int  # lines skipped before the window


def document_window(text: str, finding: Finding, full: bool) -> DocumentWindow:
    """Jump to the evidence: start a few lines above it, or show everything."""
    start, end = finding.line_start, finding.line_end
    first = 1 if full or start is None else max(1, start - CONTEXT_LINES)
    lines = [
        DocumentLine(number=number, text=line,
                     marked=start is not None and start <= number <= (end or start))
        for number, line in enumerate(text.splitlines(), 1) if number >= first
    ]
    return DocumentWindow(lines=lines, hidden_above=first - 1)


TableClick = tuple[str, int]  # table key, row; a filter change draws a new table


def new_click(rows: list[int], table_key: str, last: TableClick | None) -> TableClick | None:
    """The clicked row if the click is new; every rerun reports the old click again."""
    if rows and last != (table_key, rows[0]):
        return table_key, rows[0]
    return None
