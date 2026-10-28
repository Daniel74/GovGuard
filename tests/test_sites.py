"""Grouping findings by site (Fundstelle): one place in the document, every finding pointing at it
(#81). Pure: no model, no Streamlit."""

from site_factories import finding

from govguard.checks.sites import group_sites
from govguard.models import Finding


def places(findings: list[Finding], total: int = 100) -> list[tuple[int, int, list[str]]]:
    return [(s.line_start, s.line_end, [f.rule_id for f in s.findings])
            for s in group_sites(findings, total).placed]


def test_findings_with_the_same_lines_are_one_site() -> None:
    findings = [finding("A"), finding("B", start=40, end=41), finding("C")]

    assert places(findings) == [(5, 27, ["A", "C"]), (40, 41, ["B"])]


def test_borders_that_differ_by_up_to_two_lines_are_one_site() -> None:
    """The model shifts a border by a line or two: 5–27 next to 6–27."""
    findings = [finding("A", start=5), finding("B", start=6), finding("C", start=7),
                finding("D", start=9)]

    assert places(findings) == [(5, 27, ["A", "B", "C"]), (9, 27, ["D"])]


def test_sites_are_not_chained() -> None:
    """5 joins 7 and 7 joins 9, yet 5 and 9 are four lines apart: chaining would swallow a
    document (52 findings became one site 1–287 in the gallery)."""
    findings = [finding("A", start=5), finding("B", start=7), finding("C", start=9),
                finding("D", start=11)]

    assert places(findings) == [(5, 27, ["A", "B"]), (9, 27, ["C", "D"])]


def test_the_most_used_range_is_the_centre_of_its_site() -> None:
    """A is first by line, but B and C are two findings on 6–27: they decide who joins."""
    findings = [finding("A", start=4), finding("B", start=6), finding("C", start=6),
                finding("D", start=8)]

    assert places(findings) == [(4, 27, ["A", "B", "C", "D"])]


def test_a_site_knows_its_worst_status_and_the_mix_and_lists_the_worst_first() -> None:
    """PASS next to FAIL stays visible: the bar takes the colour of the FAIL, the mix lists both."""
    findings = [finding("A", "PASS"), finding("B", "WARN"), finding("C", "FAIL"),
                finding("D", "PASS")]

    site = group_sites(findings, 100).placed[0]

    assert site.worst == "FAIL"
    assert site.status_counts == [("FAIL", 1), ("WARN", 1), ("PASS", 2)]
    assert [f.rule_id for f in site.findings] == ["C", "B", "A", "D"]


def test_a_site_over_more_than_half_the_document_concerns_the_whole_document() -> None:
    findings = [finding("A", start=1, end=51), finding("B", start=1, end=50),
                finding("C", start=10, end=20)]

    sites = group_sites(findings, total_lines=100)

    assert [(s.line_start, s.line_end, len(s.findings)) for s in sites.whole] == [(1, 51, 2)]
    assert [(s.line_start, s.line_end) for s in sites.placed] == [(10, 20)]


def test_exactly_half_the_document_is_still_a_place() -> None:
    sites = group_sites([finding("A", start=1, end=50)], total_lines=100)

    assert (len(sites.whole), len(sites.placed)) == (0, 1)


def test_findings_without_lines_come_last_and_stay_apart() -> None:
    findings = [finding("A", "WARN", start=None, end=None), finding("B")]

    sites = group_sites(findings, 100)

    assert [f.rule_id for f in sites.without_lines] == ["A"]
    assert [f.rule_id for s in sites.placed for f in s.findings] == ["B"]
