"""Grouping findings by site (Fundstelle): a section of the document with every finding whose
lines lie inside it (#84). Pure: no model, no Streamlit."""

from site_factories import finding

from govguard.checks.sections import DocSection
from govguard.checks.sites import group_sites
from govguard.models import Finding

SECTIONS = [DocSection(name="Intro", line_start=1, line_end=9),
            DocSection(name="Body", line_start=10, line_end=29),
            DocSection(name="End", line_start=30, line_end=40)]


def places(findings: list[Finding]) -> list[tuple[str, int, int, list[str]]]:
    return [(s.name, s.line_start, s.line_end, [f.rule_id for f in s.findings])
            for s in group_sites(findings, SECTIONS).placed]


def test_a_finding_inside_a_section_belongs_to_the_site_with_the_lines_of_the_section() -> None:
    findings = [finding("A", start=12, end=15), finding("B", start=2, end=2),
                finding("C", start=20, end=29)]

    assert places(findings) == [("Intro", 1, 9, ["B"]), ("Body", 10, 29, ["A", "C"])]


def test_a_finding_without_end_line_is_one_line() -> None:
    assert places([finding("A", start=30, end=None)]) == [("End", 30, 40, ["A"])]


def test_sections_without_findings_are_no_sites() -> None:
    assert [s.name for s in group_sites([finding("A", start=35, end=36)], SECTIONS).placed] == [
        "End"]


def test_a_finding_over_several_sections_goes_to_the_group_of_several_sections() -> None:
    findings = [finding("A", start=5, end=12), finding("B", start=3, end=4)]

    sites = group_sites(findings, SECTIONS)

    assert [f.rule_id for f in sites.multi] == ["A"]
    assert [s.name for s in sites.placed] == ["Intro"]


def test_a_finding_to_the_edge_of_a_section_still_belongs_to_it() -> None:
    assert places([finding("A", start=10, end=29)]) == [("Body", 10, 29, ["A"])]


def test_a_finding_outside_every_section_cannot_be_placed_and_joins_the_group_of_several() -> None:
    assert [f.rule_id for f in group_sites([finding("A", start=39, end=45)], SECTIONS).multi] == [
        "A"]


def test_a_site_knows_its_worst_status_and_the_mix() -> None:
    """PASS next to FAIL stays visible: the bar takes the colour of the FAIL, the mix lists both,
    wherever the FAIL stands in the list."""
    findings = [finding("A", "PASS", 12, 13), finding("B", "WARN", 12, 13),
                finding("C", "FAIL", 14, 15), finding("D", "PASS", 12, 13)]

    site = group_sites(findings, SECTIONS).placed[0]

    assert site.worst == "FAIL"
    assert site.status_counts == [("FAIL", 1), ("WARN", 1), ("PASS", 2)]


def test_the_findings_of_a_site_are_sorted_by_lines_then_worst_status_then_rule() -> None:
    """Top to bottom through the document, like the group of several sections."""
    findings = [finding("A", "PASS", 12, 13), finding("B", "WARN", 12, 13),
                finding("C", "FAIL", 14, 15), finding("D", "PASS", 12, 13),
                finding("E", "FAIL", 11, 20), finding("F", "FAIL", 11, 12)]

    site = group_sites(findings, SECTIONS).placed[0]

    assert [f.rule_id for f in site.findings] == ["F", "E", "B", "A", "D", "C"]


def test_findings_without_lines_come_last_and_stay_apart() -> None:
    findings = [finding("A", "WARN", start=None, end=None), finding("B", start=12, end=13)]

    sites = group_sites(findings, SECTIONS)

    assert [f.rule_id for f in sites.without_lines] == ["A"]
    assert [f.rule_id for s in sites.placed for f in s.findings] == ["B"]


def test_without_sections_every_located_finding_stands_apart() -> None:
    sites = group_sites([finding("A", start=3, end=4)], [])

    assert [f.rule_id for f in sites.multi] == ["A"] and sites.placed == []


def test_the_group_of_several_sections_is_sorted_by_lines_then_worst_status_then_rule() -> None:
    findings = [finding("D", "PASS", 8, 28), finding("C", "WARN", 5, 12),
                finding("B", "FAIL", 5, 12), finding("A", "FAIL", 5, 12),
                finding("E", "FAIL", 5, 35), finding("F", "FAIL", 1, 12)]

    assert [f.rule_id for f in group_sites(findings, SECTIONS).multi] == [
        "F", "A", "B", "C", "E", "D"]
