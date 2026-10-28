"""Plain values for the document of "nach Fundstelle": the component draws them (#81, #84)."""

from functools import partial

import site_factories

from govguard.checks.sections import DocSection
from govguard.checks.sites import group_sites
from govguard.models import Finding
from govguard_ui.report.site_data import site_data

TEXT = "\n".join(f"line {n}" for n in range(1, 41))
finding = partial(site_factories.finding, end=7)
SECTIONS = [DocSection(name="Einleitung", line_start=1, line_end=10),
            DocSection(name="Mitte", line_start=11, line_end=25),
            DocSection(name="Ende", line_start=26, line_end=40)]


def data_for(findings: list[Finding], selected: str, closed: bool = False) -> dict:
    chosen = next(f for f in findings if f.rule_id == selected)
    return site_data(group_sites(findings, SECTIONS), TEXT, chosen, closed)


def test_a_site_carries_its_lines_its_worst_status_and_its_findings_in_the_order_of_lines() -> None:
    data = data_for([finding("A", "PASS"), finding("B", "FAIL"), finding("C", "FAIL")], "A")

    [site] = data["sites"]
    assert site["label"] == "Einleitung · Zeilen 1–10 · 3 Befunde · ✕ 2 · ✓ 1"
    assert (site["start"], site["end"]) == (1, 10)
    assert (site["look"], site["count"]) == ("fail", "3")
    assert [f["id"] for f in site["findings"]] == ["B", "C", "A"]


def test_a_finding_carries_what_the_reader_needs_to_fix_the_place() -> None:
    data = data_for([finding("A")], "A")

    assert data["sites"][0]["findings"][0] == {  # its own lines, not those of the section
        "id": "A", "look": "fail", "status": "✕ Verstoß belegt", "title": "title A",
        "anchor": "BSI OPS.1.1.2.A3", "lines": "Zeilen 5–7", "rationale": "why A",
        "recommendation": "do A", "by_code": []}


def test_llm_text_reaches_the_component_unchanged_the_browser_shows_it_as_text() -> None:
    poisoned = finding("A").model_copy(update={"title": "[x](y) <b>z</b>"})

    data = data_for([poisoned], "A")

    assert data["sites"][0]["findings"][0]["title"] == "[x](y) <b>z</b>"


def test_the_site_of_the_selected_finding_is_open_until_the_reader_closes_it() -> None:
    findings = [finding("A"), finding("B", start=20, end=21)]

    opened = data_for(findings, "B")
    closed = data_for(findings, "B", closed=True)

    assert (opened["current"], opened["open"], opened["selected"]) == (1, True, "B")
    assert (closed["current"], closed["open"]) == (1, False)


def test_the_lines_follow_the_sites_and_mark_the_selected_one() -> None:
    data = data_for([finding("A"), finding("B", start=20, end=21)], "B")

    assert [n["n"] for n in data["lines"] if n["in_site"]] == list(range(11, 26))
    assert [n["n"] for n in data["lines"] if n["in_finding"]] == [20, 21]
    assert data["lines"][4] == {"n": 5, "text": "line 5", "bar": {"site": 0, "top": False,
                                "end": False}, "tint": "fail", "in_site": False,
                                "in_finding": False}


def test_a_finding_in_no_bar_opens_no_box() -> None:
    """Over several sections or without lines: the groups above and below the document."""
    findings = [finding("A", start=1, end=30), finding("B", "WARN", start=None, end=None),
                finding("C")]

    data = data_for(findings, "A")

    assert (data["current"], data["selected"]) == (None, "A")
    assert [f["id"] for s in data["sites"] for f in s["findings"]] == ["C"]


def test_a_finding_over_several_sections_marks_its_lines_without_a_current_site() -> None:
    data = data_for([finding("A", start=8, end=12), finding("B")], "A")

    assert data["current"] is None
    assert [n["n"] for n in data["lines"] if n["in_finding"]] == [8, 9, 10, 11, 12]
    assert not any(n["in_site"] for n in data["lines"])


def test_a_selected_finding_without_lines_marks_nothing() -> None:
    data = data_for([finding("A", start=None, end=None), finding("B")], "A")

    assert not any(n["in_site"] or n["in_finding"] for n in data["lines"])


def test_a_finding_over_several_sections_gets_a_way_back_to_its_place_in_the_group() -> None:
    data = data_for([finding("A", start=8, end=12), finding("B")], "A")

    assert data["back"] == {"title": "title A", "lines": "Zeilen 8–12"}


def test_a_finding_of_a_site_or_without_lines_has_no_way_back() -> None:
    assert data_for([finding("A"), finding("B", start=20, end=21)], "B")["back"] is None
    assert data_for([finding("A", start=None, end=None), finding("B")], "A")["back"] is None
