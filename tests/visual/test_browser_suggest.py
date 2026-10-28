"""Maßnahme vorschlagen as only a real browser shows it: the button in the box, the dialog with
the password, the block above the findings (#82).

Run: `uv run pytest -m visual`.
"""

import pytest
from playwright.sync_api import Page, expect
from suggest_app import CODE, PASSWORD
from test_screens import open_view, settled

from govguard_ui.report.remediation_data import notice

pytestmark = pytest.mark.visual
NOTICE = notice("GPT-OSS 120B")


def open_site_with_button(page: Page, url: str) -> None:
    open_view(page, url, "gallery-arch")  # "nach Fundstelle" is the default
    for index in range(page.locator(".doc .bar.top").count()):
        page.locator(".doc .bar.top").nth(index).click()  # a site with fewer WARN/FAIL: no button
        settled(page)
        if page.locator(".box .sugg-btn").count():
            return
    raise AssertionError("no site offers the button")


def test_the_dialog_asks_once_then_the_block_stands_above_the_findings(
        page: Page, suggest_url: str) -> None:
    open_site_with_button(page, suggest_url)
    button = page.locator(".box .sugg-btn")
    expect(button).to_have_text("✦ Maßnahme vorschlagen")

    button.click()
    settled(page)
    dialog = page.get_by_role("dialog")
    expect(dialog).to_contain_text(NOTICE)
    dialog.get_by_label("Passwort").fill("falsch")
    dialog.get_by_role("button", name="Vorschlagen").click()
    expect(dialog).to_contain_text("Passwort falsch")
    dialog.get_by_label("Passwort").fill(PASSWORD)
    dialog.get_by_role("button", name="Vorschlagen").click()
    settled(page)

    expect(page.get_by_role("dialog")).to_have_count(0)
    block = page.locator(".box .sugg")
    expect(block).to_contain_text("Bucket-Ziel eintragen.")
    expect(block.locator(".ai")).to_have_text("KI")
    expect(block.locator(".m-code").first).to_have_text(CODE)
    expect(block).to_contain_text("deckt ab: ")
    expect(page.locator(".box .sugg-btn")).to_have_text("✦ neu vorschlagen")
    expect(page.locator(".box .note")).to_have_text(NOTICE)
    page.locator(".box .sugg-btn").click()  # the password holds: no second dialog
    settled(page)
    expect(page.get_by_role("dialog")).to_have_count(0)
    expect(page.locator(".box .sugg")).to_have_count(1)
