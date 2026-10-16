"""Status colours and small HTML pieces of the design artefact (#11, artboard Statusfarben).

Never colour alone: every status carries a symbol and a word; all pairs meet WCAG AA.
Every dynamic text goes through html.escape: it comes from the LLM or from the user.
"""

import html

from pydantic import BaseModel

from govguard_ui.review import Category


class Look(BaseModel):
    symbol: str
    label: str
    word: str  # short meaning, e.g. "Verstoß belegt"
    css: str  # class suffix in CSS


LOOKS: dict[Category, Look] = {
    "FAIL": Look(symbol="✕", label="FAIL", word="Verstoß belegt", css="fail"),
    "WARN": Look(symbol="!", label="WARN", word="Prüfbedarf", css="warn"),
    "GAP": Look(symbol="○", label="Lücke", word="nicht beschrieben", css="gap"),
    "PASS": Look(symbol="✓", label="PASS", word="Einhaltung belegt", css="pass"),
    "N/A": Look(symbol="–", label="N/A", word="nicht anwendbar", css="na"),
}

CSS = """<style>
.gg-badge{display:inline-block;padding:2px 10px;border-radius:4px;font-weight:700;
  border:1px solid;white-space:nowrap}
.gg-big{font-size:24px;padding:8px 14px;border-width:2px;border-radius:8px}
.gg-fail{color:#A3191B;background:#FCEBEB;border-color:#F0B9B9}
.gg-warn{color:#7A4A00;background:#FFF3D1;border-color:#EBCB7A}
.gg-gap{color:#4A5361;background:#FFFFFF;border-color:#A7AFBA;border-style:dashed}
.gg-pass{color:#1B6236;background:#E6F3EA;border-color:#A8D3B5}
.gg-na{color:#4A5361;background:#EDEFF2;border-color:#C9CFD8}
.gg-tag{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:4px;
  font-size:14px;color:#4A5361;border:1px solid #C9CFD8}
.gg-doc{font-family:'Source Code Pro',ui-monospace,monospace;font-size:13px;line-height:1.6}
.gg-line{display:flex;gap:12px;white-space:pre-wrap;border-left:3px solid #E3E7EC;padding-left:6px}
.gg-line .n{flex:0 0 40px;text-align:right;color:#6B7482}
.gg-mark{background:#E3EEF9;border-left-color:#0B4F8A}
.gg-mark .n{color:#0B4F8A;font-weight:700}
.gg-table{width:100%;border-collapse:collapse}
.gg-table td,.gg-table th{text-align:left;vertical-align:top;padding:10px 12px;
  border-top:1px solid #E3E7EC}
.gg-table th{background:#F0F2F6;color:#4A5361;font-size:14px}
</style>"""


def badge(category: Category, big: bool = False) -> str:
    look = LOOKS[category]
    size = " gg-big" if big else ""
    return f'<span class="gg-badge gg-{look.css}{size}">{look.symbol} {look.label}</span>'


def tag(text: str) -> str:
    return f'<span class="gg-tag">{html.escape(text)}</span>'


def paragraph(text: str) -> str:
    """LLM text as plain text: no markdown, no links, no images."""
    return f"<p>{html.escape(text)}</p>"
