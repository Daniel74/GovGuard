"""Status colours, page frame and small HTML pieces of the design artefact (#11, #41).

Never colour alone: every status carries a symbol and a word; all pairs meet WCAG AA.
Every dynamic text goes through html.escape: it comes from the LLM or from the user.
"""

import html

from pydantic import BaseModel

from govguard_ui.review import Category


class Look(BaseModel):  # the one table per category: badge, counter, help and start page
    symbol: str
    label: str
    word: str  # short meaning, e.g. "Verstoß belegt"
    css: str  # class suffix in CSS
    meaning: str  # what the category says about the finding
    todo: str  # what the reader should do


LOOKS: dict[Category, Look] = {
    "FAIL": Look(
        symbol="✕", label="FAIL", word="Verstoß belegt", css="fail",
        meaning="Verstoß belegt: Die Belegzeilen legen etwas fest, das der Prüfregel widerspricht. "
                "Fehlt nur eine Angabe, ist das kein FAIL, sondern eine Lücke.",
        todo="Beheben. Die Empfehlung im Befund nennt einen Weg."),
    "WARN": Look(
        symbol="!", label="WARN", word="Prüfbedarf", css="warn",
        meaning="Prüfbedarf mit Beleg: Die Zeilen reichen für kein klares Urteil, oder der Code "
                "hat ein PASS oder FAIL herabgestuft, das die KI nicht belegt oder der "
                "FAIL-Prüfer nicht bestätigt hat.",
        todo="Fachlich nachprüfen."),
    "GAP": Look(
        symbol="○", label="Lücke", word="nicht beschrieben", css="gap",
        meaning="WARN ohne Belegzeilen: Die Eingabe beschreibt die Anforderung nicht. Eine "
                "Spezifikation ist eine offene Welt, deshalb ist das kein Verstoß, sondern eine "
                "offene Frage.",
        todo="Als Checkliste unter der Befundliste nutzen: vor der Umsetzung klären oder bewusst "
             "ausschließen."),
    "PASS": Look(
        symbol="✓", label="PASS", word="Einhaltung belegt", css="pass",
        meaning="Einhaltung belegt: Die Belegzeilen zeigen, dass die Anforderung erfüllt ist.",
        todo="Nichts. Der Beleg dient als Nachweis."),
    "N/A": Look(
        symbol="–", label="N/A", word="nicht anwendbar", css="na",
        meaning="Nicht anwendbar, z. B. weil der Ressourcentyp in der Architektur nicht vorkommt.",
        todo="Nichts. In der Liste standardmäßig ausgeblendet."),
}

CSS = """<style>
[data-testid="stMainBlockContainer"]{max-width:calc(1040px + 10rem);padding:3rem 5rem 4rem}
[data-testid="stSidebar"]{width:240px!important;min-width:240px;max-width:240px}
[data-testid="stSidebarHeader"]{height:2rem;padding:0}
[data-testid="stSidebarContent"]{padding:0}
[data-testid="stSidebarUserContent"]{padding:0 16px 16px}
[data-testid="stSidebar"] [data-testid="stPageLink"] p{font-size:15px}
[data-testid="stSidebar"] [data-testid="stPageLink"] a{padding:10px 12px}
[data-testid="stSidebarUserContent"] [data-testid="stVerticalBlock"]{gap:4px}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]){
  border:1px solid #EAC475}
.gg-brand{display:flex;gap:10px;align-items:flex-start;padding:0 8px 16px}
.gg-brand img{margin-top:4px}
.gg-brand b{display:block;font-size:17px;line-height:1.3}
.gg-brand span{font-size:13px;color:#4A5361}
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
.gg-frame{border:1px solid #D5DAE1;border-radius:8px;overflow:hidden}
.gg-frame tr:first-child th{border-top:0}
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
