"""Screenshots of the design artefact's artboards (#11) as target images for the visual tests (#40).

Attaches over CDP to a Chrome the user is logged into; never logs in itself.
usage: shoot.py <out_dir> [board ...]   (default: all boards)
"""

import sys
import time
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

CDP = "http://127.0.0.1:9333"
ARTIFACT = "https://claude.ai/artifact/7aHtX79kJsv8EX8PjzLn2q"
BOARDS = {  # file name -> play id of the artboard (toolbar ▷ → Prototypes shows it in the URL)
    "start": "e3841f552080",
    "gallery-spec": "15dd8cd198dd",
    "gallery-arch": "5aa49afc0388",
    "create": "1fef2003fd56",
}
WIDTH, HEIGHT = 1440, 4200  # tall enough for the longest artboard, trimmed afterwards
TOP = 80  # claude.ai bar plus play bar above the artboard
HIDE_HINT = """() => { for (const el of document.querySelectorAll('div,section,aside')) {
  const t = el.innerText || '';
  if ((t.startsWith('Artifacts sind standardmäßig privat') || t.startsWith('Artifacts are private'))
      && el.getBoundingClientRect().width < 300) el.style.visibility = 'hidden'; } }"""


def content_end(image: Image.Image) -> int:
    """Last row with anything but white right of the sidebar."""
    rgb, (w, h) = image.convert("RGB"), image.size
    px = rgb.load()
    rows = [y for y in range(h) if any(px[x, y] != (255, 255, 255) for x in range(300, w - 40, 7))]
    return rows[-1] if rows else h


def shoot(page, play_id: str, out: Path) -> None:
    page.goto(f"{ARTIFACT}#play-{play_id}")
    page.reload()  # a hash change alone does not switch the artboard
    page.wait_for_selector("iframe", timeout=30_000)
    time.sleep(6)  # artboards fetch their report data after mounting
    page.evaluate(HIDE_HINT)
    page.screenshot(path=out, clip={"x": 0, "y": TOP, "width": WIDTH, "height": HEIGHT - TOP})
    image = Image.open(out)
    image.crop((0, 0, WIDTH, min(image.size[1], content_end(image) + 48))).save(out, optimize=True)


def main() -> None:
    out_dir, *names = sys.argv[1:]
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(CDP)
        page = browser.contexts[0].new_page()
        page.set_viewport_size({"width": WIDTH, "height": HEIGHT})
        for name in names or BOARDS:
            shoot(page, BOARDS[name], Path(out_dir) / f"{name}.png")
            print("saved", name)
        page.close()


if __name__ == "__main__":
    main()
