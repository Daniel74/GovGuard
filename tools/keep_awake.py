"""Keep the demo on Streamlit Community Cloud awake (#79).

Community Cloud puts an app to sleep after 12 hours without a visit; a scheduled
GitHub Actions run opens it in a real browser and presses the wake button if needed.

  python -m tools.keep_awake https://govguard.streamlit.app/
"""

import os
import re
import sys
import time
from collections.abc import Callable
from typing import Protocol

import playwright.sync_api as playwright

TIMEOUT_S = 180
POLL_S = 2
APP_TEXT = "GovGuard"  # sidebar title of the app; not on Streamlit's sleep page
WAKE_BUTTON = re.compile(r"get this app back up", re.IGNORECASE)


class Page(Protocol):
    def shows_app(self) -> bool: ...

    def press_wake_button(self) -> bool: ...


class BrowserPage:
    """A Playwright page; Community Cloud shows the app in an iframe, so search every frame."""

    def __init__(self, page: playwright.Page) -> None:
        self.page = page

    def shows_app(self) -> bool:
        return any(APP_TEXT in body_text(frame) for frame in self.page.frames)

    def press_wake_button(self) -> bool:
        for frame in self.page.frames:
            button = frame.get_by_role("button", name=WAKE_BUTTON)
            if button.count():
                button.first.click()
                return True
        return False


def body_text(frame: playwright.Frame) -> str:
    """Empty while a frame is still loading or already gone."""
    try:
        return frame.locator("body").inner_text(timeout=1000)
    except playwright.Error:
        return ""


def wake(
    page: Page,
    timeout_s: float = TIMEOUT_S,
    clock: Callable[[], float] = time.monotonic,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Result line for the run log; poll until the app shows, press the button at most once."""
    start, woken = clock(), False
    while clock() - start < timeout_s:
        if page.shows_app():
            waited = round(clock() - start)
            return f"App schlief, nach {waited} s geweckt." if woken else "App war wach."
        woken = woken or page.press_wake_button()
        sleep(POLL_S)
    raise TimeoutError(f"App nach {timeout_s:.0f} s nicht erschienen.")


def report(line: str) -> None:
    """Print to the run log; on GitHub also to the run summary shown without opening the log."""
    print(line)
    if summary := os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(summary, "a", encoding="utf-8") as file:
            file.write(f"{line}\n")


def main(url: str) -> int:
    """Exit code 1 turns the GitHub run red, and GitHub mails the owner of the schedule."""
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(url, wait_until="domcontentloaded")
        try:
            line, code = wake(BrowserPage(page)), 0
        except TimeoutError as error:
            line, code = str(error), 1
        browser.close()
    report(line)
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
