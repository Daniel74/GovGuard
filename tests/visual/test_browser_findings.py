"""Finding list on "Audits ansehen" as only a real browser shows it: CSS and open state (#43).

Run: `uv run pytest -m visual`.
"""

import re

import pytest
from playwright.sync_api import Locator, Page, Playwright, expect
from poisoned_app import POISON
from test_browser import rgb
from test_screens import open_view, settled

from govguard_ui.style import LOOKS, STATUS_FILTERS

pytestmark = pytest.mark.visual

FIRST = 'tr[data-id="SPEC-SDM-M50.S15"]'  # "Definition von Revisionsaktivitäten", first row
FIFTH = 'tr[data-id="SPEC-SDM-M50.D01"]'  # "Dokumentation von Zweckbeschreibung ...", fifth
ART9 = 'tr[data-id="SPEC-DSGVO-Art.9Abs.2"]'  # the locator pierces the shadow root


def spec(page: Page, app_url: str) -> Page:
    open_view(page, app_url, "gallery-spec")
    return page


def style(element: Locator, name: str) -> str:
    return element.evaluate(f"e => getComputedStyle(e).{name}")


def source(page: Page, name: str) -> Locator:
    return page.get_by_role("radio", name=re.compile(f"^{name} "))


def table_of(row: Locator) -> Locator:
    return row.locator("xpath=ancestor::table")


def test_the_spec_table_has_a_head_lines_between_rows_wraps_long_titles_and_scrolls(
        page: Page, app_url: str) -> None:
    row = spec(page, app_url).locator(FIFTH)  # long title: wraps
    title = row.locator("td").nth(1)

    expect(table_of(row).locator("th")).to_have_text(["Status", "Prüfregel", "Normanker",
                                                       "Zeilen"])
    assert style(title, "borderTopStyle") == "solid"
    line = float(style(title, "lineHeight").removesuffix("px"))
    assert title.bounding_box()["height"] >= 2 * line  # wrapped, not cut
    assert title.evaluate("e => e.scrollWidth <= e.clientWidth")
    scroller = table_of(row).locator("xpath=..")
    assert scroller.evaluate("e => e.scrollHeight > e.clientHeight")


def test_the_table_shows_its_own_scrollbar(playwright: Playwright, browser_context_args: dict,
                                           app_url: str) -> None:
    """Playwright hides every bar (--hide-scrollbars), so this test only starts its own Chromium;
    the screenshots keep showing none."""
    browser = playwright.chromium.launch(ignore_default_args=["--hide-scrollbars"])
    try:
        scroller = table_of(spec(browser.new_page(**browser_context_args), app_url)
                            .locator(FIRST)).locator("xpath=..")
        bar = "e => e.offsetWidth - e.clientWidth - 2 * e.clientLeft"  # minus the two borders
        assert scroller.evaluate(bar) > 0
        thumb = style(scroller, "scrollbarColor").split(" rgba")[0]  # Streamlit's is transparent
        assert thumb == rgb("#A7AFBA")
    finally:
        browser.close()


def test_a_click_on_a_row_selects_the_finding_and_marks_only_this_row(page: Page,
                                                                     app_url: str) -> None:
    spec(page, app_url).locator(ART9).click()

    heading = page.get_by_role("heading", name="Einwilligung als Ausnahme")
    expect(heading).to_be_visible()
    page.mouse.move(0, 0)  # hover paints the row, too
    assert style(page.locator(ART9), "backgroundColor") == rgb("#E3EEF9")
    assert style(page.locator(FIRST), "backgroundColor") != rgb("#E3EEF9")


def test_arrows_move_the_focus_enter_selects_and_the_focus_stays_after_the_rerun(
        page: Page, app_url: str) -> None:
    spec(page, app_url).locator(FIRST).focus()

    for _ in range(4):
        page.keyboard.press("ArrowDown")
    expect(page.locator(FIFTH)).to_be_focused()
    expect(page.locator('tr[tabindex="0"]')).to_have_count(1)  # roving tabindex: the one Tab
    expect(page.locator(FIFTH)).to_have_attribute("tabindex", "0")  # stop moves with the focus
    page.keyboard.press("Enter")

    heading = page.get_by_role("heading", name="Dokumentation von Zweckbeschreibung und -bindung")
    expect(heading).to_be_visible()
    settled(page)
    grid = page.get_by_role("grid", name="Befunde")  # aria-selected is valid on a grid row
    expect(grid.get_by_role("row", selected=True)).to_have_attribute("data-id", "SPEC-SDM-M50.D01")
    expect(page.locator(FIFTH)).to_be_focused()
    page.keyboard.press("ArrowUp")
    expect(page.locator(f"{FIFTH} >> xpath=preceding-sibling::tr[1]")).to_be_focused()


def test_llm_text_stands_in_the_cells_as_text_never_as_link_image_or_tag(
        page: Page, poisoned_url: str) -> None:
    page.goto(poisoned_url)
    settled(page)
    rows = page.locator("tr[data-id]")
    expect(rows.first).to_be_visible()

    assert rows.locator("a, img, b").count() == 0
    for cell in (1, 2):  # rule and anchor
        expect(rows.first.locator("td").nth(cell)).to_contain_text(POISON)


def test_a_click_on_the_active_source_keeps_it(page: Page, app_url: str) -> None:
    spec(page, app_url)
    expect(source(page, "Alle")).to_have_attribute("aria-checked", "true")
    source(page, "DSGVO").click()
    settled(page)

    source(page, "DSGVO").click()
    settled(page)

    expect(source(page, "DSGVO")).to_have_attribute("aria-checked", "true")


def test_each_source_is_its_own_button_with_a_gap_and_the_active_one_is_dark_blue(
        page: Page, app_url: str) -> None:
    alle, dsgvo = source(spec(page, app_url), "Alle"), source(page, "DSGVO")
    page.mouse.move(0, 0)

    assert style(alle, "backgroundColor") == rgb("#0B4F8A")  # design artefact of #11
    assert style(alle.locator("p"), "color") == rgb("#FFFFFF")
    assert style(dsgvo, "backgroundColor") == rgb("#FFFFFF")
    left, right = alle.bounding_box(), dsgvo.bounding_box()
    assert right["x"] >= left["x"] + left["width"] + 8  # apart, not one joined block
    assert style(dsgvo, "borderTopLeftRadius") == style(dsgvo, "borderTopRightRadius") != "0px"


def test_the_gap_list_stays_open_when_the_source_changes_and_scrolls(page: Page,
                                                                    app_url: str) -> None:
    summary = spec(page, app_url).locator("summary").filter(has_text="Für jedes Vorhaben zu klären")
    details = summary.locator("xpath=..")
    summary.click()
    expect(details).to_have_attribute("open", "")

    source(page, "DSGVO").click()
    expect(summary).to_contain_text(re.compile(r"· \d+ Lücken"))
    dsgvo = summary.inner_text()

    expect(details).to_have_attribute("open", "")
    source(page, "Alle").click()
    expect(summary).not_to_have_text(dsgvo)  # the count follows the source
    scroller = details.locator('[data-testid="stVerticalBlock"][height]').last
    assert scroller.evaluate("e => e.scrollHeight > e.clientHeight")


def test_the_status_pills_carry_the_status_colours(page: Page, app_url: str) -> None:
    """Every status, not only two: the CSS finds a pill by its position (style.py)."""
    pills = spec(page, app_url).locator('button[data-variant="pills"]')
    na = pills.filter(has_text=LOOKS["N/A"].label)
    assert style(na, "backgroundColor") != rgb(LOOKS["N/A"].background)  # off: no colour

    na.click()
    expect(na).to_have_attribute("aria-pressed", "true")
    page.mouse.move(0, 0)  # hover and focus would paint over the colours
    na.blur()

    for name in STATUS_FILTERS:
        pill = pills.filter(has_text=LOOKS[name].label)
        assert style(pill, "backgroundColor") == rgb(LOOKS[name].background), name
        assert style(pill, "borderTopColor") == rgb(LOOKS[name].border), name


def test_document_title_and_whole_document_stand_in_one_row_inside_the_frame(
        page: Page, app_url: str) -> None:
    frame = spec(page, app_url).locator('[class*="_document"]').first.bounding_box()
    title = page.get_by_text("Geprüftes Dokument").bounding_box()
    toggle = page.get_by_test_id("stCheckbox").filter(has_text="Ganzes Dokument").bounding_box()

    assert toggle["x"] > title["x"] + title["width"]
    assert title["y"] < toggle["y"] + toggle["height"]  # one row: the boxes overlap vertically
    assert toggle["y"] < title["y"] + title["height"]
    for box in (title, toggle):
        assert frame["x"] < box["x"] and box["x"] + box["width"] < frame["x"] + frame["width"]
        assert frame["y"] < box["y"]


def test_the_german_status_pills_wrap_instead_of_being_cut_off(page: Page, app_url: str) -> None:
    """German words are longer than the codes (#51): every pill stays fully visible."""
    pills = spec(page, app_url).locator('button[data-variant="pills"]')
    column = pills.first.locator('xpath=ancestor::*[@data-testid="stColumn"][1]').bounding_box()

    for index in range(pills.count()):
        box = pills.nth(index).bounding_box()
        assert box["x"] + box["width"] <= column["x"] + column["width"], index


def test_the_popover_of_a_condition_closes_when_the_jump_into_the_document_is_clicked(
        page: Page, app_url: str) -> None:
    spec(page, app_url).get_by_role("button", name=re.compile("Einwilligung: nein")).click()
    jump = page.get_by_role("button", name=re.compile("Zeile 47 im Dokument"))
    expect(jump).to_be_visible()

    jump.click()

    expect(page.get_by_text("Bedingung: Einwilligung")).to_be_visible()  # the card, in the detail
    expect(jump).to_be_hidden()  # the popover no longer covers the page


def test_a_click_on_a_column_head_sorts_ascending_and_enter_on_it_flips_the_order(
        page: Page, app_url: str) -> None:
    """Python sorts (review.sorted_findings, #80); here: the head sends the column, shows it."""
    status = spec(page, app_url).locator('th[data-col="status"]')
    anchor = page.locator('th[data-col="primary_anchor"]')
    first = page.locator("tr[data-id]").first.locator("td").nth(2)  # its anchor
    expect(status).to_have_attribute("aria-sort", "ascending")  # the order of the list

    anchor.click()
    expect(anchor).to_have_attribute("aria-sort", "ascending")
    expect(page.locator("th[aria-sort]")).to_have_count(1)
    expect(first).to_have_text(re.compile(r"^DSGVO "))  # sources: DSGVO, KI-VO, SDM
    arrow = anchor.evaluate( "e => getComputedStyle(e, '::after').content")
    assert arrow.startswith('"▲"')

    anchor.press("Enter")
    expect(anchor).to_have_attribute("aria-sort", "descending")
    expect(first).to_have_text(re.compile(r"^SDM "))
    expect(anchor).to_be_focused()
