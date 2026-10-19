"""Screenshot regression of the demo UI against approved reference images (#40).

Run: `uv run pytest -m visual`; write new reference images: `--update-snapshots`.
"""

import re
from pathlib import Path

import pytest
from PIL import Image
from playwright.sync_api import Page
from snapshots import compare, side_by_side

HERE = Path(__file__).parent
DESIGN = HERE / "design"  # artboards of the design artefact (#11), see /design-screenshots
OUTPUT = HERE / "output"  # screenshots, diff and side-by-side images, not committed

pytestmark = pytest.mark.visual


def settled(page: Page) -> None:
    """Waits until the script has run and the fonts are loaded."""
    page.locator('[data-testid="stApp"][data-test-script-state="notRunning"]').wait_for()
    page.evaluate("document.fonts.ready")


def fit_height(page: Page) -> None:
    """Streamlit scrolls inside stMain, so full_page misses the rest: grow the viewport instead."""
    for _ in range(3):  # a taller viewport can reflow the page once more
        height = page.locator('[data-testid="stMain"]').evaluate("e => e.scrollHeight")
        if height == page.viewport_size["height"]:
            return
        page.set_viewport_size({"width": page.viewport_size["width"], "height": height})
        page.wait_for_timeout(300)


def check_snapshot(page: Page, name: str, update: bool) -> None:
    reference, actual_path, diff_path = (HERE / f"{name}.png", OUTPUT / f"{name}.png",
                                         OUTPUT / f"{name}-diff.png")
    OUTPUT.mkdir(exist_ok=True)
    diff_path.unlink(missing_ok=True)  # a diff from an earlier run would mislead
    page.evaluate("document.activeElement?.blur()")  # no focus ring from the last click
    fit_height(page)
    page.screenshot(path=actual_path, animations="disabled", caret="hide")
    side_by_side(Image.open(DESIGN / f"{name}.png"), Image.open(actual_path)).save(
        OUTPUT / f"{name}-design.png")
    if update:
        reference.write_bytes(actual_path.read_bytes())
        return
    assert reference.exists(), f"no reference image {reference.name}, run with --update-snapshots"
    diff = compare(Image.open(actual_path), Image.open(reference))
    if diff is not None:
        diff.save(diff_path)
        pytest.fail(f"{name} differs from its reference image, see {diff_path}")


VIEWS = {  # name of the design artboard -> url path, gallery preset to pick, heading to wait for
    "start": ("", None, "GovGuard – Prüfassistent"),
    "gallery-spec": ("audits", None, "Online-Anmeldung zur Schuleingangsuntersuchung"),
    "gallery-arch": ("audits", "Antragseingang mit Sicherheitsmängeln",
                     "Antragseingang mit Sicherheitsmängeln"),
    "create": ("erstellen", None, "Audit erstellen"),
}


def open_view(page: Page, app_url: str, name: str) -> None:
    path, preset, heading = VIEWS[name]
    page.goto(f"{app_url}/{path}")
    settled(page)
    if preset:
        page.get_by_test_id("stSelectbox").click()
        page.get_by_role("option", name=re.compile(preset)).click()
    page.get_by_role("heading", name=re.compile(heading)).first.wait_for()
    settled(page)


@pytest.mark.parametrize("name", VIEWS)
def test_view_matches_its_reference(page: Page, app_url: str, update_snapshots: bool,
                                    name: str) -> None:
    open_view(page, app_url, name)

    check_snapshot(page, name, update_snapshots)
