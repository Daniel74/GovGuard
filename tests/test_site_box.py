"""What the box under a site shows first and what it folds away (#86). Pure, no Streamlit."""

from site_factories import finding

from govguard.checks.sites import Site
from govguard_ui.report.site_box import box_parts, first_to_look_at, to_act_on

MIXED = Site(name="Speicher", line_start=1, line_end=40, findings=[
    finding("P1", "PASS", 2, 2), finding("W1", "WARN", 3, 3), finding("F1", "FAIL", 5, 5),
    finding("N1", "N/A", 6, 6), finding("W2", "WARN", 8, 8), finding("F2", "FAIL", 9, 9),
    finding("P2", "PASS", 10, 10), finding("P3", "PASS", 11, 11)])
QUIET = Site(name="Ruhe", line_start=1, line_end=9, findings=[
    finding("P1", "PASS", 2, 2), finding("N1", "N/A", 4, 4)])


def ids(findings: list) -> list[str]:
    return [f.rule_id for f in findings]


def test_what_needs_action_is_warn_and_fail_with_fail_first_then_the_order_of_lines() -> None:
    assert ids(to_act_on(MIXED)) == ["F1", "F2", "W1", "W2"]


def test_a_click_on_a_site_chooses_its_first_warn_or_fail_in_that_order() -> None:
    assert first_to_look_at(MIXED).rule_id == "F1"  # not W1, which stands first by lines


def test_a_site_without_warn_or_fail_chooses_its_first_finding_by_lines() -> None:
    assert first_to_look_at(QUIET).rule_id == "P1"


def test_the_box_parts_split_open_from_without_need_and_name_the_fold_row() -> None:
    parts = box_parts(MIXED, "F1")

    assert parts["open"] == ["F1", "F2", "W1", "W2"]
    assert parts["rest"] == ["P1", "N1", "P2", "P3"]
    assert parts["rest_text"] == "4 ohne Handlungsbedarf (3 erfüllt, 1 nicht anwendbar)"


def test_open_and_rest_together_are_every_finding_whatever_the_status() -> None:
    """The rest is whatever is not open: no finding may vanish from the box."""
    odd = finding("X", start=7, end=7).model_copy(update={"status": "???"})
    site = Site(name="x", line_start=1, line_end=9, findings=[*MIXED.findings, odd])

    parts = box_parts(site, "F1")

    assert sorted(parts["open"] + parts["rest"]) == sorted(f.rule_id for f in site.findings)
    assert "X" in parts["rest"]
    assert parts["rest_text"] == "5 ohne Handlungsbedarf (3 erfüllt, 1 nicht anwendbar)"


def test_a_part_with_zero_findings_is_left_out_of_the_fold_row() -> None:
    only_pass = Site(name="x", line_start=1, line_end=9, findings=[
        finding("W", "WARN", 2, 2), finding("P", "PASS", 3, 3)])
    only_na = Site(name="x", line_start=1, line_end=9, findings=[finding("N", "N/A", 3, 3)])

    assert box_parts(only_pass, "W")["rest_text"] == "1 ohne Handlungsbedarf (1 erfüllt)"
    assert box_parts(only_na, "N")["rest_text"] == "1 ohne Handlungsbedarf (1 nicht anwendbar)"


def test_without_findings_of_that_kind_there_is_no_fold_row() -> None:
    all_open = Site(name="x", line_start=1, line_end=9, findings=[finding("W", "WARN", 2, 2)])

    parts = box_parts(all_open, "W")

    assert (parts["rest"], parts["rest_text"], parts["rest_auto"]) == ([], "", False)


def test_the_fold_row_opens_by_itself_when_the_selected_finding_lies_inside() -> None:
    assert box_parts(MIXED, "P2")["rest_auto"] is True
    assert box_parts(MIXED, "F1")["rest_auto"] is False


def under(site: Site, *covers: list[str]) -> dict:
    """box_parts for measures a, b, ... that cover the given rule ids."""
    measures = [{"id": chr(97 + n), "rule_ids": ids} for n, ids in enumerate(covers)]
    return box_parts(site, "F1", measures)


def test_the_findings_stand_under_the_measure_that_covers_them_fail_before_warn() -> None:
    parts = under(MIXED, ["W1", "F1"], ["W2", "F2"])

    assert parts["by_measure"] == {"a": ["F1", "W1"], "b": ["F2", "W2"]}
    assert parts["leftover"] == []


def test_a_measure_lists_only_the_visible_findings_a_filter_hides_the_others() -> None:
    """The proposal covers the unfiltered site; the box shows what the filter lets through."""
    shown = Site(name="x", line_start=1, line_end=40,
                 findings=[f for f in MIXED.findings if f.rule_id not in ("F1", "W2")])

    parts = under(shown, ["W1", "F1"], ["W2", "F2"])

    assert parts["by_measure"] == {"a": ["W1"], "b": ["F2"]}
    assert parts["leftover"] == []  # hidden by the filter is not lost


def test_a_visible_warn_or_fail_in_no_measure_is_kept_as_a_further_finding() -> None:
    parts = under(MIXED, ["F1"], ["W1"])

    assert parts["by_measure"] == {"a": ["F1"], "b": ["W1"]}
    assert parts["leftover"] == ["F2", "W2"]


def test_a_finding_named_by_two_measures_stands_once_under_the_first() -> None:
    parts = under(MIXED, ["F1", "F2"], ["F2", "W1", "W2"])

    assert parts["by_measure"] == {"a": ["F1", "F2"], "b": ["W1", "W2"]}


def test_without_measures_nothing_is_grouped() -> None:
    parts = box_parts(MIXED, "F1")

    assert (parts["by_measure"], parts["leftover"]) == ({}, [])
