"""The document line by line for "nach Fundstelle": which bar stands at a line, which site a click
on it opens, which colour tints it (#81, #84). Pure view logic."""

from site_factories import site

from govguard_ui.report.site_lines import Bar, line_rows

TEXT = "\n".join(f"line {n}" for n in range(1, 41))


def test_one_row_per_line_with_the_bar_of_the_site_that_holds_it() -> None:
    rows = line_rows("a\nb\nc\nd", [site(2, 3)], current=None, span=None)

    assert [r.text for r in rows] == ["a", "b", "c", "d"]
    assert [r.bar for r in rows] == [
        None, Bar(site=0, top=True, end=False), Bar(site=0, top=False, end=True), None]


def test_sites_that_follow_each_other_share_the_one_lane() -> None:
    rows = line_rows(TEXT, [site(1, 10), site(11, 20)], current=None, span=None)

    assert [rows[i].bar.site for i in (9, 10)] == [0, 1]
    assert [rows[i].bar.end for i in (9, 10)] == [True, False]


def test_a_click_on_a_line_opens_the_site_holding_it() -> None:
    rows = line_rows(TEXT, [site(1, 30), site(31, 35)], current=None, span=None)

    assert [r.bar and r.bar.site for r in (rows[0], rows[32], rows[39])] == [0, 1, None]


def test_only_narrow_sites_tint_their_lines_in_the_colour_of_their_worst_status() -> None:
    """Under 15 lines the site fills its lines; a wide one would colour half the document."""
    rows = line_rows(TEXT, [site(1, 20, "FAIL"), site(21, 23, "WARN")], current=None, span=None)

    assert [rows[0].tint, rows[21].tint, rows[30].tint] == [None, "WARN", None]


def test_the_lines_of_the_current_site_and_of_the_selected_finding_are_marked() -> None:
    rows = line_rows(TEXT, [site(2, 3), site(10, 15)], current=1, span=(11, 12))

    assert [r.number for r in rows if r.in_site] == [10, 11, 12, 13, 14, 15]
    assert [r.number for r in rows if r.in_finding] == [11, 12]


def test_without_a_current_site_the_finding_is_marked_across_the_sections() -> None:
    """A finding over several sections: no site is current, its lines are marked all the same."""
    rows = line_rows(TEXT, [site(2, 3), site(10, 15)], current=None, span=(3, 11))

    assert not any(r.in_site for r in rows)
    assert [r.number for r in rows if r.in_finding] == list(range(3, 12))


def test_a_finding_without_lines_marks_nothing() -> None:
    rows = line_rows(TEXT, [site(2, 3)], current=None, span=None)

    assert not any(r.in_site or r.in_finding for r in rows)
