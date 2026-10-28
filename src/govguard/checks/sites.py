"""Findings grouped by site (Fundstelle): one place in the document and every finding that points
at it, so a reader fixes the place once (#81). Only re-orders, the findings stay as they are."""

from collections import Counter

from pydantic import BaseModel

from govguard.models import SEVERITY, Finding, Status

NEAR = 2  # lines a border may differ and still be the same place: 5–27 next to 6–27

Span = tuple[int, int]


class Site(BaseModel):
    line_start: int
    line_end: int
    findings: list[Finding]  # worst status first

    @property
    def worst(self) -> Status:
        return max((f.status for f in self.findings), key=SEVERITY.__getitem__)

    @property
    def status_counts(self) -> list[tuple[Status, int]]:  # worst first, e.g. [("FAIL", 2)]
        counted = Counter(f.status for f in self.findings)
        return sorted(counted.items(), key=lambda item: SEVERITY[item[0]], reverse=True)

    @property
    def width(self) -> int:  # lines
        return self.line_end - self.line_start + 1


class Sites(BaseModel):
    whole: list[Site]  # over half the document: no place, the reader fixes it everywhere
    placed: list[Site]  # by line
    without_lines: list[Finding]


def _span(finding: Finding) -> Span:
    assert finding.line_start is not None and finding.last_line is not None
    return finding.line_start, finding.last_line


def _near(a: Span, b: Span) -> bool:
    return abs(a[0] - b[0]) <= NEAR and abs(a[1] - b[1]) <= NEAR


def _centres(counted: Counter[Span]) -> dict[Span, Span]:
    """Span -> the centre of its site. The most used range comes first and takes every free
    range near it; a range already taken is no centre, so sites are never chained."""
    centre_of: dict[Span, Span] = {}
    for span in sorted(counted, key=lambda s: (-counted[s], s[0] - s[1], s[0])):
        if span not in centre_of:
            for other in counted:
                if other not in centre_of and _near(span, other):
                    centre_of[other] = span
    return centre_of


def group_sites(findings: list[Finding], total_lines: int) -> Sites:
    """A range joins the site whose centre it is near (NEAR, both borders), not every finding of
    it: two findings of one site may lie up to 2 * NEAR lines apart (FUNKTIONSWEISE 5)."""
    located = [f for f in findings if f.line_start is not None]
    centre_of = _centres(Counter(_span(f) for f in located))
    groups: dict[Span, list[Finding]] = {}
    for finding in located:
        groups.setdefault(centre_of[_span(finding)], []).append(finding)
    sites = [Site(line_start=min(_span(f)[0] for f in items),
                  line_end=max(_span(f)[1] for f in items),
                  findings=sorted(items, key=lambda f: -SEVERITY[f.status]))
             for items in groups.values()]
    sites.sort(key=lambda s: (s.line_start, s.line_end))
    whole = [s for s in sites if 2 * s.width > total_lines]
    return Sites(whole=whole, placed=[s for s in sites if s not in whole],
                 without_lines=[f for f in findings if f.line_start is None])
