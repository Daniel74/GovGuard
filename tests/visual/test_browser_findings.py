"""Finding list on "Audits ansehen" as only a real browser shows it: CSS and open state (#43).

Run: `uv run pytest -m visual`.
"""

import re

import pytest
from playwright.sync_api import Locator, Page, expect
from test_browser import rgb
from test_screens import open_view, settled

from govguard_ui.style import LOOKS

pytestmark = pytest.mark.visual

ZWECK = '[class*="_row_SPEC-SDM-M50-D01"] button'  # "Dokumentation von Zweckbeschreibung ..."
ART9 = '[class*="_row_SPEC-DSGVO-Art-9"] button'  # Streamlit turns "." of a key into "-"


def spec(page: Page, app_url: str) -> Page:
    open_view(page, app_url, "gallery-spec")
    return page


def style(element: Locator, name: str) -> str:
    return element.evaluate(f"e => getComputedStyle(e).{name}")


def source(page: Page, name: str) -> Locator:
    return page.get_by_role("radio", name=re.compile(f"^{name} "))


def test_a_long_title_wraps_and_the_list_has_no_table_lines_or_checkboxes(page: Page,
                                                                         app_url: str) -> None:
    row = spec(page, app_url).locator(ZWECK)
    text = row.locator("p")

    line = float(style(text, "lineHeight").removesuffix("px"))
    assert text.bounding_box()["height"] >= 2 * line  # wrapped, not cut
    assert text.evaluate("e => e.scrollWidth <= e.clientWidth")
    assert page.get_by_test_id("stDataFrame").count() == 0  # its rows had checkboxes and lines
    assert style(row, "borderTopStyle") == "none" or style(row, "borderTopColor").endswith(", 0)")


def test_a_click_on_a_row_selects_the_finding_and_marks_only_this_row(page: Page,
                                                                     app_url: str) -> None:
    spec(page, app_url).locator(ART9).click()

    heading = page.get_by_role("heading", name="Einwilligung für besondere Kategorien")
    expect(heading).to_be_visible()
    assert style(page.locator(ART9), "backgroundColor") == rgb("#E3EEF9")
    assert style(page.locator(ZWECK), "backgroundColor") != rgb("#E3EEF9")


def test_a_click_on_the_active_source_keeps_it(page: Page, app_url: str) -> None:
    spec(page, app_url)
    expect(source(page, "Alle")).to_have_attribute("aria-checked", "true")
    source(page, "DSGVO").click()
    settled(page)

    source(page, "DSGVO").click()
    settled(page)

    expect(source(page, "DSGVO")).to_have_attribute("aria-checked", "true")


def test_the_gap_list_stays_open_when_the_source_changes_and_scrolls(page: Page,
                                                                    app_url: str) -> None:
    gaps = spec(page, app_url).get_by_test_id("stExpander").filter(has_text="nicht beschreibt")
    gaps.locator("summary").click()
    expect(gaps.locator("details")).to_have_attribute("open", "")

    source(page, "DSGVO").click()
    expect(gaps.locator("summary")).to_contain_text("18 Lücken")

    expect(gaps.locator("details")).to_have_attribute("open", "")
    source(page, "Alle").click()
    expect(gaps.locator("summary")).to_contain_text("106 Lücken")
    scroller = gaps.locator('[data-testid="stVerticalBlock"][height]').last
    assert scroller.evaluate("e => e.scrollHeight > e.clientHeight")


def test_the_status_pills_carry_the_status_colours(page: Page, app_url: str) -> None:
    pills = spec(page, app_url).locator('button[data-variant="pills"]')
    fail, na = pills.filter(has_text="FAIL"), pills.filter(has_text="N/A")

    assert style(fail, "backgroundColor") == rgb(LOOKS["FAIL"].background)
    assert style(fail, "borderTopColor") == rgb(LOOKS["FAIL"].border)
    assert style(na, "backgroundColor") != rgb(LOOKS["N/A"].background)  # off: no colour


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


def test_a_jump_to_a_required_finding_opens_its_source_group(page: Page, app_url: str) -> None:
    open_view(page, app_url, "gallery-arch")
    cis = page.get_by_test_id("stExpander").filter(
        has=page.locator("summary", has_text="CIS AWS Foundations")).first
    expect(cis.locator("details").first).not_to_have_attribute("open", "")

    page.get_by_role("button", name=re.compile("CIS AWS v7.0.0 3.1.4: Soll FAIL")).click()

    expect(cis.locator("details").first).to_have_attribute("open", "")
    expect(page.get_by_role("heading", name="Block Public Access für S3 Buckets")).to_be_visible()
