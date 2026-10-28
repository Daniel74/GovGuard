"""Findings grouped by site (Fundstelle): a section of the document with every finding whose lines
lie inside it, so a reader fixes one unit once (#84). Only re-orders, the findings stay as they
are."""

from bisect import bisect_right
from collections import Counter

from pydantic import BaseModel

from govguard.checks.sections import DocSection
from govguard.models import SEVERITY, Finding, Status


def by_lines(finding: Finding) -> tuple[int, int, int, str]:
    """Sort key of a located finding: top to bottom, on equal lines the worst status first."""
    assert finding.line_start is not None and finding.last_line is not None
    return finding.line_start, finding.last_line, -SEVERITY[finding.status], finding.rule_id


class Site(BaseModel):
    name: str  # of the section: chapter, resource or path
    line_start: int
    line_end: int
    findings: list[Finding]  # by lines (by_lines)

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
    multi: list[Finding]  # lines in several sections: no single place; by lines (by_lines)
    placed: list[Site]  # by line, never overlapping
    without_lines: list[Finding]


def _section_of(finding: Finding, starts: list[int], sections: list[DocSection]) -> int | None:
    """Index of the one section holding all lines of the finding, else None. Lines beyond the end
    of the document give None too (cannot happen in practice: range_problem drops such ranges)."""
    assert finding.line_start is not None and finding.last_line is not None
    first = bisect_right(starts, finding.line_start) - 1
    last = bisect_right(starts, finding.last_line) - 1
    if first < 0 or first != last:  # also: no sections at all
        return None
    return first if finding.last_line <= sections[first].line_end else None


def group_sites(findings: list[Finding], sections: list[DocSection]) -> Sites:
    """sections: from split_sections, in line order. A finding inside one section belongs to its
    site; one over several sections (or outside all) stands apart (FUNKTIONSWEISE 5)."""
    starts = [s.line_start for s in sections]
    held: dict[int, list[Finding]] = {}
    multi = []
    for finding in findings:
        if finding.line_start is None:
            continue
        index = _section_of(finding, starts, sections)
        if index is None:
            multi.append(finding)
        else:
            held.setdefault(index, []).append(finding)
    sites = [Site(name=sections[i].name, line_start=sections[i].line_start,
                  line_end=sections[i].line_end,
                  findings=sorted(items, key=by_lines))
             for i, items in sorted(held.items())]
    multi.sort(key=by_lines)
    return Sites(multi=multi, placed=sites,
                 without_lines=[f for f in findings if f.line_start is None])
