"""Behaviour of the demo UI that only a real browser shows: CSS and page switches (#41).

Run: `uv run pytest -m visual`.
"""

import re

import pytest
from playwright.sync_api import Page
from test_screens import settled

pytestmark = pytest.mark.visual

CONTENT_WIDTH = 1040  # content column of the design artboards (#11)


def test_on_a_wide_screen_the_content_is_at_most_1040_px_and_centred(page: Page,
                                                                     app_url: str) -> None:
    page.set_viewport_size({"width": 1920, "height": 1000})
    page.goto(app_url)
    settled(page)

    main = page.get_by_test_id("stMain").bounding_box()
    content = page.get_by_test_id("stMainBlockContainer").locator(
        '> [data-testid="stVerticalBlock"]').bounding_box()

    assert content["width"] <= CONTENT_WIDTH
    left = content["x"] - main["x"]
    right = main["x"] + main["width"] - content["x"] - content["width"]
    assert abs(left - right) <= 16  # a scrollbar may take a few pixels on one side


@pytest.mark.parametrize(("button", "path", "heading"), [
    ("Zu „Audit erstellen“", "/erstellen", "Audit erstellen"),
    ("Zu „Audits ansehen“", "/audits", "Audits ansehen"),
])
def test_the_start_page_buttons_open_their_page(page: Page, app_url: str, button: str, path: str,
                                                heading: str) -> None:
    page.goto(app_url)
    settled(page)

    page.get_by_role("button", name=button).click()

    page.get_by_role("heading", name=heading, level=1).wait_for()
    assert re.search(f"{path}$", page.url)


def rgb(colour: str) -> str:
    red, green, blue = bytes.fromhex(colour.removeprefix("#"))
    return f"rgb({red}, {green}, {blue})"


def test_tiles_overall_status_and_expected_strip_carry_the_status_colours(page: Page,
                                                                         app_url: str) -> None:
    from govguard_ui.style import LOOKS

    page.goto(f"{app_url}/audits")
    settled(page)

    for suffix, category in (("_tile_fail", "FAIL"), ("_tile_pass", "PASS"),
                             ("_overall_fail", "FAIL"), ("_expected_pass", "PASS")):
        box = page.locator(f'[class*="{suffix}"]').first
        colours = box.evaluate("e => [getComputedStyle(e).backgroundColor, "
                               "getComputedStyle(e).borderTopColor]")
        look = LOOKS[category]
        assert colours == [rgb(look.background), rgb(look.border)], suffix


def test_the_gallery_choice_stands_right_of_the_page_title(page: Page, app_url: str) -> None:
    page.goto(f"{app_url}/audits")
    settled(page)

    title = page.get_by_role("heading", name="Audits ansehen", level=1).bounding_box()
    choice = page.get_by_test_id("stSelectbox").bounding_box()

    assert choice["x"] > title["x"] + title["width"]
    assert choice["y"] < title["y"] + title["height"]  # one row: the boxes overlap vertically
    assert title["y"] < choice["y"] + choice["height"]


def test_the_help_icons_of_all_tiles_stand_at_one_height(page: Page, app_url: str) -> None:
    page.goto(f"{app_url}/audits")
    settled(page)

    icons = page.locator('[class*="_tile_"] [data-testid="stMetricLabel"] '
                         '[data-testid="stTooltipIcon"]').all()

    assert len({icon.bounding_box()["y"] for icon in icons}) == 1  # also with a wrapped label


@pytest.mark.parametrize(("link", "path", "heading"), [
    ("Start & Hilfe", "/", "GovGuard – Compliance Copilot für Behörden-IT"),
    ("Audits ansehen", "/audits", "Audits ansehen"),
    ("Audit erstellen", "/erstellen", "Audit erstellen"),
])
def test_the_sidebar_links_open_all_three_pages(page: Page, app_url: str, link: str, path: str,
                                                heading: str) -> None:
    start_elsewhere = "/audits" if path == "/" else "/"  # every link is clicked from another page
    page.goto(f"{app_url}{start_elsewhere}")
    settled(page)

    page.get_by_test_id("stSidebar").get_by_role("link", name=link).click()

    page.get_by_role("heading", name=heading, level=1).wait_for()
    assert page.url.removeprefix(app_url).rstrip("/") == path.rstrip("/")
