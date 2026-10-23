"""The keep-awake job (#79) in a real browser on local stand-ins of the Community Cloud page.

Run: `uv run pytest -m visual`.
"""

import importlib.util
from pathlib import Path

import pytest
from playwright.sync_api import Page

SCRIPT = Path(__file__).parents[2] / "tools/keep_awake.py"
spec = importlib.util.spec_from_file_location("keep_awake", SCRIPT)
keep_awake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keep_awake)

pytestmark = pytest.mark.visual

# Community Cloud runs the app in an iframe below /~/+/; the outer page only has the footer.
APP = '<iframe srcdoc="<p>GovGuard</p><p>Prüfassistent</p>"></iframe>'
AWAKE = f"<p>Hosted with Streamlit</p>{APP}"
ASLEEP = (
    "<p>Zzzz – This app has gone to sleep due to inactivity.</p>"
    f"<button onclick='document.body.innerHTML = `{APP}`'>Yes, get this app back up!</button>"
)


def test_an_awake_app_is_seen_inside_its_frame(page: Page) -> None:
    page.set_content(AWAKE)
    assert keep_awake.wake(keep_awake.BrowserPage(page)) == "App war wach."


def test_a_sleeping_app_is_woken_by_its_button(page: Page) -> None:
    page.set_content(ASLEEP)
    assert keep_awake.wake(keep_awake.BrowserPage(page)).startswith("App schlief, nach ")
    assert page.get_by_role("button").count() == 0
