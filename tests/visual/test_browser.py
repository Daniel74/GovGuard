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
