"""Findings and sites for the tests of "nach Fundstelle" (#81)."""

from govguard.checks.sites import Site
from govguard.models import Finding, Status


def finding(rule_id: str, status: Status = "FAIL", start: int | None = 5,
            end: int | None = 27) -> Finding:
    return Finding(rule_id=rule_id, status=status, line_start=start, line_end=end,
                   rationale=f"why {rule_id}", recommendation=f"do {rule_id}", evidence=None,
                   title=f"title {rule_id}", primary_anchor="BSI OPS.1.1.2.A3",
                   cross_references=[])


def site(start: int, end: int, status: Status = "FAIL") -> Site:
    return Site(line_start=start, line_end=end,
                findings=[finding("R", status, start=start, end=end)])
