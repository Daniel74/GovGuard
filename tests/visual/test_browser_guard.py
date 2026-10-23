"""The guard against a page switch while an audit runs; only a real browser clicks (#77).

Run: `uv run pytest -m visual`.
"""

import pytest
from playwright.sync_api import Locator, Page
from slow_audit_app import PASSWORD
from test_screens import settled

from govguard_ui.screens.create_page import STAY_NOTE
from govguard_ui.screens.navigation_guard import LEAVE, QUESTION, STAY

pytestmark = pytest.mark.visual


def link(page: Page, name: str) -> Locator:
    return page.get_by_test_id("stSidebar").get_by_role("link", name=name)


def heading(page: Page, name: str) -> Locator:
    return page.get_by_role("heading", name=name, level=1)


def start_audit(page: Page, url: str) -> None:
    page.goto(f"{url}/erstellen")
    settled(page)
    page.get_by_label("Passwort").fill(PASSWORD)
    page.get_by_role("button", name="Audit starten").click()
    page.get_by_text(STAY_NOTE).wait_for()


def test_stay_keeps_the_audit_running_and_afterwards_links_switch_freely(
        page: Page, slow_url: str) -> None:
    start_audit(page, slow_url)

    link(page, "Audits ansehen").click()
    page.get_by_role("dialog").get_by_text(QUESTION).wait_for()
    page.get_by_role("button", name=STAY).click()

    page.get_by_text("Audit fertig nach").wait_for(timeout=20_000)
    assert heading(page, "Audit erstellen").is_visible()
    link(page, "Audits ansehen").click()  # the guard is gone with the run
    heading(page, "Audits ansehen").wait_for()
    assert not page.get_by_role("dialog").is_visible()


def test_leave_cancels_the_audit_and_opens_the_chosen_page(page: Page, slow_url: str) -> None:
    start_audit(page, slow_url)

    link(page, "Audits ansehen").click()
    page.get_by_role("button", name=LEAVE).click()

    heading(page, "Audits ansehen").wait_for()
    link(page, "Audit erstellen").click()
    page.get_by_role("button", name="Audit starten").wait_for()
    assert not page.get_by_text("Audit fertig nach").count()


def test_without_an_audit_the_links_switch_without_a_question(page: Page, slow_url: str) -> None:
    page.goto(f"{slow_url}/erstellen")
    settled(page)

    link(page, "Audits ansehen").click()

    heading(page, "Audits ansehen").wait_for()
    assert not page.get_by_role("dialog").is_visible()
