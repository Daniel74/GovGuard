"""Status colours, page frame and small HTML pieces of the design artefact (#11, #41).

Never colour alone: every status carries a symbol and a word; all pairs meet WCAG AA.
Every dynamic text goes through html.escape: it comes from the LLM or from the user.
"""

import html

from pydantic import BaseModel

from govguard_ui.review import Category


class Look(BaseModel):  # the one table per category: badge, counter, help and start page
    symbol: str
    label: str  # German word on screen, e.g. "Verstoß belegt" (#51)
    code: str  # how the JSON report shows it (#51); a gap is a WARN without evidence lines
    css: str  # class suffix in CSS
    meaning: str  # what the category says about the finding
    todo: str  # what the reader should do
    text: str  # colours of badge, tile and box
    background: str
    border: str
    border_style: str = "solid"


JUDGE_NAME = "Verstoß-Prüfer"  # UI name of the FAIL judge (CONTEXT: judge_fails)

LOOKS: dict[Category, Look] = {
    "FAIL": Look(
        symbol="✕", label="Verstoß belegt", code="FAIL", css="fail",
        meaning="Die Belegzeilen legen etwas fest, das der Prüfregel widerspricht. Fehlt nur "
                "eine Angabe, ist das kein Verstoß, sondern eine Lücke.",
        todo="Beheben. Die Empfehlung im Befund nennt einen Weg.",
        text="#A3191B", background="#FCEBEB", border="#F0B9B9"),
    "WARN": Look(
        symbol="!", label="Prüfbedarf", code="WARN", css="warn",
        meaning="Prüfbedarf mit Beleg: Die Zeilen reichen für kein klares Urteil, oder der Code "
                "hat eine Einhaltung oder einen Verstoß herabgestuft, den die KI nicht belegt "
                f"oder der {JUDGE_NAME} nicht bestätigt hat.",
        todo="Fachlich nachprüfen.", text="#7A4A00", background="#FFF3D1", border="#EBCB7A"),
    "GAP": Look(
        symbol="○", label="Lücke", code="WARN ohne Belegzeilen", css="gap",
        meaning="Prüfbedarf ohne Belegzeilen: Die Eingabe beschreibt die Anforderung nicht. Eine "
                "Spezifikation ist eine offene Welt, deshalb ist das kein Verstoß, sondern eine "
                "offene Frage.",
        todo="Als Checkliste unter der Befundliste nutzen: vor der Umsetzung klären oder bewusst "
             "ausschließen.",
        text="#4A5361", background="#FFFFFF", border="#A7AFBA", border_style="dashed"),
    "PASS": Look(
        symbol="✓", label="Einhaltung belegt", code="PASS", css="pass",
        meaning="Die Belegzeilen zeigen, dass die Anforderung erfüllt ist.",
        todo="Nichts. Der Beleg dient als Nachweis.",
        text="#1B6236", background="#E6F3EA", border="#A8D3B5"),
    "N/A": Look(
        symbol="–", label="Nicht anwendbar", code="N/A", css="na",
        meaning="Die Prüfregel betrifft die Eingabe nicht, z. B. Mandantentrennung bei einem "
                "System für nur eine Behörde oder ein AWS-Dienst, der in der Architektur nicht "
                "vorkommt.",
        todo="Nichts. In der Liste standardmäßig ausgeblendet.",
        text="#4A5361", background="#EDEFF2", border="#C9CFD8"),
}


def status_word(status: str) -> str:
    """German word of a status code; other words such as "fehlt" stay as they are."""
    return LOOKS[status].label if status in LOOKS else status


STATUS_FILTERS: tuple[Category, ...] = ("FAIL", "WARN", "PASS", "N/A")  # gaps: own list


def badge_css(prefix: str) -> str:
    """Badge colours per category: on the page (gg-) and in the shadow DOM of the table (b-)."""
    return "".join(f".{prefix}{look.css}{{color:{look.text};background:{look.background};"
                   f"border-color:{look.border};border-style:{look.border_style}}}"
                   for look in LOOKS.values())


def _status_css() -> str:
    """Badge, tile, overall status and expected strip share the colours of LOOKS (#42)."""
    rules = [badge_css("gg-")]
    for look in LOOKS.values():
        tile, overall, strip = (f'[class*="_{box}_{look.css}"]'
                                for box in ("tile", "overall", "expected"))
        colours = (f"background:{look.background};border-color:{look.border};"
                   f"border-style:{look.border_style}")
        rules += [f"{tile},{overall},{strip}{{{colours}}}",
                  f"{tile} :is(p,label),{overall} p,{strip} strong{{color:{look.text}}}"]
    for index, name in enumerate(STATUS_FILTERS, 1):  # an active status pill (#43)
        look = LOOKS[name]
        rules.append(f'[class*="_status"] button[aria-pressed="true"]:nth-of-type({index})'
                     f"{{color:{look.text};background:{look.background};"
                     f"border-color:{look.border}}}")
    return "\n".join(rules)


# Own CSS only where Streamlit has no option; tests/visual/test_browser.py guards the frame
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
.gg-overall{font-size:40px;font-weight:700;line-height:1.2;margin:0;text-align:center}
[class*="_overall_"] p{text-align:center}
[class*="_overall_"] [data-testid="stElementContainer"]:first-child p{font-size:13px;
  font-weight:700;letter-spacing:.06em;text-transform:uppercase}
[class*="_status"] [data-testid="stButtonGroup"]>div{flex-wrap:wrap}
[class*="_tile_"]{gap:4px}
[class*="_tile_"] [data-testid="stMetricLabel"]{align-items:flex-start}
[class*="_tile_"] [data-testid="stMetricLabel"] *{white-space:normal;overflow:visible}
[class*="_tile_"] [data-testid="stMetricValue"]{font-size:28px;font-weight:700}
[class*="_expected_"]{gap:4px 24px}
[class*="_expected_"] [data-testid="stBaseButton-tertiary"] p{text-decoration:underline}
.gg-meta th{font-weight:400;color:#4A5361;padding:2px 16px 2px 0;text-align:left}
.gg-meta td{padding:2px 0}
.gg-tag{display:inline-block;margin-left:8px;padding:1px 8px;border-radius:4px;
  font-size:14px;color:#4A5361;border:1px solid #C9CFD8}
.gg-doc{font-family:'Source Code Pro',ui-monospace,monospace;font-size:13px;line-height:1.6}
.gg-line{display:flex;gap:12px;white-space:pre-wrap;border-left:3px solid #E3E7EC;padding-left:6px}
.gg-line .n{flex:0 0 40px;text-align:right;color:#6B7482}
.gg-mark{background:#E3EEF9;border-left-color:#0B4F8A}
.gg-mark .n{color:#0B4F8A;font-weight:700}
[class*="_source"] [role="radiogroup"]{gap:8px}
[class*="_source"] [role="radiogroup"] button{margin:0;border:1px solid #C9CFD8;
  border-radius:6px;background:#FFFFFF}
[class*="_source"] [role="radiogroup"] button[aria-checked="true"]{background:#0B4F8A;
  border-color:#0B4F8A}
[class*="_source"] button[aria-checked="true"] p{color:#FFFFFF;font-weight:600}
[class*="_gaps"] details{border-style:dashed}
[class*="_document_head"]{background:#F5F6F8;margin:-15px -15px 0;width:calc(100% + 30px);
  max-width:none;padding:.5rem 15px;flex-wrap:nowrap;border-radius:7px 7px 0 0}
[class*="_document_head"] p{font-size:14px}
.gg-table{width:100%;border-collapse:collapse}
.gg-frame{border:1px solid #D5DAE1;border-radius:8px;overflow:hidden}
.gg-frame tr:first-child th{border-top:0}
.gg-table td,.gg-table th{text-align:left;vertical-align:top;padding:10px 12px;
  border-top:1px solid #E3E7EC}
.gg-table th{background:#EEF0F4;color:#4A5361;font-size:14px}
""" + _status_css() + "</style>"


def badge(category: Category) -> str:
    look = LOOKS[category]
    return f'<span class="gg-badge gg-{look.css}">{look.symbol} {look.label}</span>'


def tag(text: str) -> str:
    return f'<span class="gg-tag">{html.escape(text)}</span>'


def paragraph(text: str) -> str:
    """LLM text as plain text: no markdown, no links, no images."""
    return f"<p>{html.escape(text)}</p>"
