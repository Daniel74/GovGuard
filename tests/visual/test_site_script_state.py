"""What the component of "nach Fundstelle" remembers in the browser about the box (#86).

foldState() of the script runs here in a blank page with plain objects as data: no server, no
click path through the gallery to the one list position where an old state could reach a wrong
section. Run: `uv run pytest -m visual`.
"""

import pytest
from playwright.sync_api import Page

from govguard_ui.report.site_script import JS

pytestmark = pytest.mark.visual
SCRIPT = JS.split("export default function")[0]  # the helpers; the entry point needs Streamlit


def site(start: int, end: int, rest_auto: bool = False) -> dict:
    return {"start": start, "end": end, "rest_auto": rest_auto}


def data(sites: list[dict], current: int | None, selected: str) -> dict:
    return {"sites": sites, "current": current, "selected": selected}


def run(page: Page, steps: list[tuple[dict, dict]]) -> list[dict]:
    """steps: (data of a draw, what the reader did before it, set on the state)."""
    return page.evaluate("""([src, steps]) => {
        const foldState = new Function(src + "; return foldState")()
        const doc = {}
        return steps.map(([data, did]) => {
            const ui = foldState(doc, data)
            Object.assign(ui, did)
            return JSON.parse(JSON.stringify(ui))
        })
    }""", [SCRIPT, steps])


A, B = site(1, 10), site(11, 20)
OPENED = {"restOpen": True, "openMeasures": {"m1": True}, "openFindings": {"F": True}}


def test_what_is_open_belongs_to_the_section_not_to_its_place_in_the_list(page: Page) -> None:
    """A filter or a new audit moves another section to the same index: it starts closed."""
    first, second = run(page, [(data([A, B], 0, "x"), OPENED), (data([B], 0, "x"), {})])

    assert first["restOpen"] is True
    assert "restOpen" not in second
    assert second["openMeasures"] == {} and second["openFindings"] == {}


def test_the_same_section_keeps_its_state_when_the_filter_moves_it_in_the_list(page: Page) -> None:
    _, after = run(page, [(data([A, B], 1, "x"), OPENED), (data([B], 0, "x"), {})])

    assert after["restOpen"] is True and after["openMeasures"] == {"m1": True}


def test_another_choice_shuts_the_finding_whatever_way_it_came(page: Page) -> None:
    """A click on a bar, the arrows, the table or the group: the chosen finding starts shut."""
    _, after = run(page, [(data([A], 0, "x"), OPENED), (data([A], 0, "y"), {})])

    assert after["openFindings"] == {}


def test_a_finding_the_reader_clicked_stays_open_when_its_choice_comes_back_from_the_rerun(
        page: Page) -> None:
    _, after = run(page, [(data([A], 0, "x"), {"opening": "y"}), (data([A], 0, "y"), {})])

    assert after["openFindings"] == {"y": True} and "opening" not in after


def test_a_click_that_led_to_another_choice_opens_nothing(page: Page) -> None:
    _, after = run(page, [(data([A], 0, "x"), {"opening": "y"}), (data([A], 0, "z"), {})])

    assert after["openFindings"] == {} and "opening" not in after


def test_a_fold_the_reader_opened_stays_open_when_he_chooses_something_that_needs_action(
        page: Page) -> None:
    _, after = run(page, [(data([A], 0, "x"), OPENED), (data([A], 0, "y"), {})])

    assert after["restOpen"] is True


def test_a_choice_inside_the_fold_opens_it_again_even_when_the_reader_had_shut_it(
        page: Page) -> None:
    """Decided for #86: the fold opens by itself whenever the chosen finding lies inside."""
    shut = {"restOpen": False}
    _, after = run(page, [(data([site(1, 10, True)], 0, "p2"), shut),
                          (data([site(1, 10, True)], 0, "p1"), {})])

    assert "restOpen" not in after


def test_a_choice_by_the_line_of_the_finding_in_the_box_does_not_move_the_view(
        page: Page) -> None:
    """#86: the reader sits at the box; the marked lines may lie out of sight, the view stays."""
    _, by_click, by_other_way = run(page, [
        (data([A], 0, "x"), {"opening": "y"}), (data([A], 0, "y"), {}),
        (data([A], 0, "z"), {})])

    assert by_click["stay"] is True
    assert by_other_way["stay"] is False
