"""Pure view logic for reading an audit report; no Streamlit (#11)."""

from collections import Counter
from typing import Literal, get_args

from pydantic import BaseModel

from govguard.condition_models import LineRange
from govguard.models import AuditReport, Expected, Finding, SourceName, Status

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
    """A downgrade or a dropped range always needs review, even without lines: it is never a gap
    (ADR 0017, #74)."""
    untouched = finding.downgraded_from is None and not finding.range_dropped
    is_gap = finding.line_start is None and untouched
    return "GAP" if finding.status == "WARN" and is_gap else finding.status


def warn_caption(findings: list[Finding]) -> str:
    """Caption of the Prüfbedarf tile: how many WARN the code made or touched (#51, #74)."""
    downgraded = sum(1 for f in findings if f.downgraded_from)
    dropped = sum(1 for f in findings  # a downgrade counts once, as a downgrade
                  if f.range_dropped and not f.downgraded_from and category(f) == "WARN")
    parts = []
    if downgraded:
        parts.append(f"{downgraded} herabgestuft")
    if dropped:
        parts.append(f"{dropped} mit gestrichenem Bereich")
    return "mit Beleg · davon " + ", ".join(parts) if parts else "mit Beleg"


def no_evidence_note(finding: Finding) -> str:
    """Why the detail shows no lines: none given, or the code dropped an unusable range (#74)."""
    if finding.range_dropped:
        return ("Kein Beleg: Die KI nannte einen ungültigen Zeilenbereich, der Code hat ihn "
                "gestrichen (siehe Korrekturen).")
    return "Kein Beleg: Zu dieser Prüfregel nennt der Befund keine Stelle im Dokument."


def category_counts(findings: list[Finding]) -> dict[Category, int]:
    counted = Counter(category(finding) for finding in findings)
    return {name: counted[name] for name in CATEGORIES}


def visible_findings(
    findings: list[Finding], categories: set[Category], source: str | None
) -> list[Finding]:
    """The finding list: gaps stand below it as a checklist; FAIL first, then by line."""
    shown = [f for f in of_source(findings, source) if category(f) in categories - {"GAP"}]
    return sorted(shown, key=lambda f: (CATEGORIES.index(category(f)), f.line_start or 10**9))


def source_of(finding: Finding) -> str:
    """Rule ids read <SPEC|ARCH>-<SOURCE>-<requirement>, e.g. ARCH-CIS-3.1.4; a source name
    may hold a hyphen itself (SPEC-KI-VO-Art.6Abs.2).
    """
    rest = finding.rule_id.partition("-")[2]
    return next(s for s in get_args(SourceName) if rest.startswith(f"{s}-"))


def of_source(findings: list[Finding], source: str | None) -> list[Finding]:
    """None: all sources."""
    return [f for f in findings if source in (None, source_of(f))]


ALL_SOURCES = "Alle"  # option of the source filter that keeps every source


def source_counts(findings: list[Finding]) -> dict[str, int]:
    """What the table can show, N/A included; gaps stand in their own list: "Alle" first."""
    listed = [finding for finding in findings if category(finding) != "GAP"]
    counted = Counter(source_of(finding) for finding in listed)
    return {ALL_SOURCES: len(listed), **dict(sorted(counted.items()))}


class DocumentLine(BaseModel):
    number: int  # 1-based, counted like the engine counts (str.splitlines)
    text: str
    marked: bool  # evidence line of the selected finding


class DocumentWindow(BaseModel):
    lines: list[DocumentLine]
    hidden_above: int  # lines skipped before the window


def document_window(
    text: str, finding: Finding, full: bool, marks: list[LineRange] | None = None
) -> DocumentWindow:
    """Jump to the evidence: start a few lines above it, or show everything.
    marks replace the finding's lines, e.g. the evidence of a condition (#61)."""
    if marks is None:
        start = finding.line_start
        marks = [] if start is None else [
            LineRange(line_start=start, line_end=finding.line_end or start)]
    first = 1 if full or not marks else max(1, min(m.line_start for m in marks) - CONTEXT_LINES)
    lines = [
        DocumentLine(number=number, text=line,
                     marked=any(m.line_start <= number <= m.line_end for m in marks))
        for number, line in enumerate(text.splitlines(), 1) if number >= first
    ]
    return DocumentWindow(lines=lines, hidden_above=first - 1)


def lines_text(finding: Finding) -> str:
    """Evidence lines for a table cell or caption: "–", "46" or "46–49"."""
    if finding.line_start is None:
        return "–"
    if finding.line_start == finding.line_end:
        return str(finding.line_start)
    return f"{finding.line_start}–{finding.line_end}"
