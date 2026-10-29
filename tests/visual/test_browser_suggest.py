"""Maßnahme vorschlagen as only a real browser shows it: the button in the box, the dialog with
the password, the block above the findings (#82).

Run: `uv run pytest -m visual`.
"""

import re

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


def ask(page: Page) -> None:
    """The button, the dialog with the password, the proposal."""
    page.locator(".box .sugg-btn").click()
    dialog = page.get_by_role("dialog")
    dialog.get_by_label("Passwort").fill(PASSWORD)
    dialog.get_by_role("button", name="Vorschlagen").click()
    settled(page)


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
    expect(block.locator(".ai")).to_have_text(["KI", "KI"])  # the heading and the measure
    expect(block).to_contain_text(re.compile(r"deckt \d+ Befunde? ab"))
    expect(page.locator(".box .sugg-btn")).to_have_text("✦ neu vorschlagen")
    expect(page.locator(".box .note")).to_have_text(NOTICE)
    page.locator(".box .sugg-btn").click()  # the password holds: no second dialog
    settled(page)
    expect(page.get_by_role("dialog")).to_have_count(0)
    expect(page.locator(".box .sugg")).to_have_count(1)


def open_all_covers(page: Page) -> None:
    """Opens the row "deckt n Befunde ab" of each measure; they start shut (#86)."""
    expect(page.locator(".box .one.cov").first).to_be_visible()  # the proposal is drawn
    for n in range(page.locator(".box .one.cov").count()):
        page.locator(".box .one.cov").nth(n).click()
    expect(page.locator(".box .one.cov[aria-expanded=false]")).to_have_count(0)


def test_a_measure_is_one_line_until_it_is_opened_then_it_shows_before_and_after(
        page: Page, suggest_url: str) -> None:
    open_site_with_button(page, suggest_url)
    ask(page)
    block = page.locator(".box .sugg")
    expect(block.locator(".m-code")).to_have_count(0)  # one line until it is opened

    measure = block.locator(".mrow .one").first
    caret, sentence = measure.locator(".caret"), measure.locator(".m-t")
    assert abs(caret.bounding_box()["y"] - sentence.bounding_box()["y"]) < 8  # one line, #86
    measure.click()

    expect(block.locator(".m-code").first).to_have_text(CODE)
    expect(block).to_contain_text("deckt ab: ")
    after = block.locator(".m-l", has_text="Nachher")
    expect(after.locator(".ai")).to_have_text("KI")  # the model wrote it
    before = block.locator(".m-l", has_text="Vorher")
    expect(before.locator(".ai")).to_have_count(0)  # the code cut it, no marker
    block.locator(".mrow .one").first.click()
    expect(block.locator(".m-code")).to_have_count(0)


def test_without_a_proposal_the_findings_stand_under_the_heading_befunde(
        page: Page, suggest_url: str) -> None:
    open_site_with_button(page, suggest_url)

    expect(page.locator(".box .sec-h")).to_have_text(["Befunde"])  # no proposal, no "Maßnahmen"
    expect(page.locator(".box .sec-h .ai")).to_have_count(0)  # the code checked the findings
    expect(page.locator(".box .frow").first).to_be_visible()


def test_with_a_proposal_the_findings_stand_under_the_measure_that_covers_them(
        page: Page, suggest_url: str) -> None:
    """#86: "Maßnahmen" first, no heading "Befunde"; the covered findings stand under their
    measure, in sight even while the measure is shut; the note stays under the button."""
    open_site_with_button(page, suggest_url)

    ask(page)

    headings = page.locator(".box .sec-h")
    expect(headings).to_have_text(re.compile("Maßnahmen"))  # the one heading
    expect(headings.locator(".ai")).to_have_text("KI")
    measure = page.locator(".box .mrow").first
    expect(measure.locator(".mfinds")).to_have_count(0)  # behind "deckt n Befunde ab", shut
    covers = measure.locator(".one.cov")
    expect(covers).to_have_text(re.compile(r"deckt \d+ Befunde? ab"))
    expect(covers).to_have_attribute("aria-expanded", "false")
    open_all_covers(page)
    findings = measure.locator(".mfinds .frow")
    expect(findings.first).to_be_visible()  # the measure is shut, its findings are in sight
    expect(measure.locator(".m-code")).to_have_count(0)
    everywhere = page.locator(".box .frow").count() - page.locator(".box .rest .frow").count()
    assert page.locator(".box .mrow .mfinds .frow").count() == everywhere  # none got lost
    note = page.locator(".box .note").bounding_box()
    assert note["y"] < headings.first.bounding_box()["y"]  # under the button, above the measures


def test_a_finding_under_a_measure_behaves_like_any_one_liner_and_the_measure_opens_above_it(
        page: Page, suggest_url: str) -> None:
    open_site_with_button(page, suggest_url)
    ask(page)
    measure = page.locator(".box .mrow").first
    open_all_covers(page)
    other = measure.locator(".mfinds .frow:not(.sel) .one").first

    other.click()
    settled(page)

    expect(page.locator(".box .frow.sel")).to_have_count(1)
    expect(page.locator(".box .frow.sel .detail")).to_have_count(1)  # chosen and opened by click
    measure.locator(".one").first.click()  # the measure opens between its line and its findings
    expect(measure.locator(".m-code").first).to_have_text(CODE)
    expect(measure.locator(".mfinds .frow.sel")).to_have_count(1)  # the open list stays open
    detail, found = (measure.locator("> .detail").bounding_box(),
                     measure.locator(".mfinds").bounding_box())
    assert detail["y"] + detail["height"] <= found["y"] + 1
    page.locator(".box .frow.sel .one").click()  # a second click shuts the finding
    expect(page.locator(".box .frow .detail")).to_have_count(0)


def test_a_new_proposal_starts_closed_even_when_the_old_one_stood_open(
        page: Page, suggest_url: str) -> None:
    """#86: what is open lives in the browser; it must not carry over to other measures."""
    open_site_with_button(page, suggest_url)
    ask(page)
    page.locator(".box .mrow .one").first.click()
    expect(page.locator(".box .m-code").first).to_have_text(CODE)

    page.locator(".box .sugg-btn").click()  # "neu vorschlagen": another model call, other text
    settled(page)

    expect(page.locator(".box .mrow")).to_have_count(1)
    expect(page.locator(".box .m-code")).to_have_count(0)
