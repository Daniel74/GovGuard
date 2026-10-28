"""The document line by line for "nach Fundstelle": which bars stand at a line, which site a click
on it opens, which colour tints it (#81). Pure view logic."""

from site_factories import site

from govguard_ui.report.site_lines import Bar, line_rows

TEXT = "\n".join(f"line {n}" for n in range(1, 41))


def test_one_row_per_line_with_the_bar_of_the_site_that_holds_it() -> None:
    rows = line_rows("a\nb\nc\nd", [site(2, 3)], current=None)

    assert [r.text for r in rows] == ["a", "b", "c", "d"]
    assert [r.bars for r in rows] == [
        [None], [Bar(site=0, top=True, end=False)], [Bar(site=0, top=False, end=True)], [None]]


def test_overlapping_sites_stand_side_by_side() -> None:
    rows = line_rows(TEXT, [site(1, 10), site(5, 7)], current=None)

    assert [b and b.site for b in rows[5].bars] == [0, 1]
    assert [b and b.site for b in rows[8].bars] == [0, None]


def test_a_click_on_a_line_opens_the_narrowest_site_holding_it() -> None:
    rows = line_rows(TEXT, [site(1, 30), site(5, 7)], current=None)

    assert [rows[0].owner, rows[5].owner, rows[39].owner] == [0, 1, None]


def test_only_narrow_sites_tint_their_lines_in_the_colour_of_their_worst_status() -> None:
    """Under 15 lines the site fills its lines; a wide one would colour half the document."""
    rows = line_rows(TEXT, [site(1, 30, "FAIL"), site(5, 7, "WARN"), site(6, 6, "PASS")],
                     current=None)

    assert [rows[0].tint, rows[4].tint, rows[5].tint] == [None, "WARN", "WARN"]


def test_the_lines_of_the_current_site_are_marked_selected() -> None:
    rows = line_rows(TEXT, [site(2, 3), site(10, 12)], current=1)

    assert [r.number for r in rows if r.selected] == [10, 11, 12]
