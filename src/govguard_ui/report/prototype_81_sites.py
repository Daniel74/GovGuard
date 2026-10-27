"""PROTOTYPE #81 – throwaway, lives only on branch prototype/81-fundstelle.

Three variants of the view "nach Fundstelle" on the real gallery, switchable via ?variant=A|B|C;
the grouping rule is switchable via ?grouping=gleich|enthalten. Grouping and floating bar here.
"""

from collections import Counter

import streamlit as st
from pydantic import BaseModel

from govguard.models import Finding
from govguard_ui.report.review import CATEGORIES, Category, category
from govguard_ui.style import LOOKS

VARIANTS = {"A": "Gruppenzeilen in der Tabelle", "B": "Fundstellen mit Maßnahmenliste",
            "C": "Dokument mit Randmarken", "D": "Tabelle + farbiges Dokument",
            "E": "Dokument im Mittelpunkt"}
GROUPINGS = {"gleich": "gleicher Bereich", "nah": "±2 Zeilen",
             "enthalten": "+ enthaltene (≤ 12 Z.)"}
NEAR = 2  # the LLM shifts a border by a line or two: 5–27 next to 6–27
CONTAINED_LIMIT = 12  # a wider range would swallow half the document (1–287 in the gallery)
VIEWS = ["nach Prüfregel", "nach Fundstelle"]


class Site(BaseModel):  # Fundstelle: one line range and every finding pointing at it
    line_start: int | None
    line_end: int | None
    findings: list[Finding]

    @property
    def worst(self) -> Category:
        return min((category(f) for f in self.findings), key=CATEGORIES.index)

    @property
    def mix(self) -> list[tuple[Category, int]]:
        counted = Counter(category(f) for f in self.findings)
        return [(c, counted[c]) for c in CATEGORIES if counted[c]]

    @property
    def lines(self) -> str:
        if self.line_start is None:
            return "ohne Zeilen"
        if self.line_start == self.line_end:
            return f"Zeile {self.line_start}"
        return f"Zeilen {self.line_start}–{self.line_end}"

    @property
    def anchors(self) -> list[str]:
        return list(dict.fromkeys(f.primary_anchor for f in self.findings))

    @property
    def id(self) -> str:
        return f"{self.line_start}-{self.line_end}"


def mix_text(site: Site) -> str:
    return " · ".join(f"{LOOKS[c].symbol} {n}" for c, n in site.mix)


def _span(finding: Finding) -> tuple[int, int]:
    return finding.line_start, finding.line_end or finding.line_start


def _homes(counted: Counter, rule: str) -> dict[tuple[int, int], tuple[int, int]]:
    """Range -> range of the site it joins."""
    spans = set(counted)
    home = {span: span for span in spans}
    if rule == "nah":  # to the most used range whose borders lie within ±2, never chained
        for span in spans:
            near = [h for h in spans if abs(h[0] - span[0]) <= NEAR and abs(h[1] - span[1]) <= NEAR]
            home[span] = max(near, key=lambda h: (counted[h], h[1] - h[0], -h[0]))
    if rule == "enthalten":  # into the widest short range that contains it, never chained
        short = [s for s in spans if s[1] - s[0] + 1 <= CONTAINED_LIMIT]
        for span in spans:
            hosts = [h for h in short if h[0] <= span[0] and span[1] <= h[1]]
            if hosts:
                home[span] = max(hosts, key=lambda h: (h[1] - h[0], -h[0]))
    return home


def group_sites(findings: list[Finding], rule: str, by_severity: bool = False) -> list[Site]:
    """Sites by line, or worst and biggest first; worst status first inside a site;
    findings without lines last."""
    home = _homes(Counter(_span(f) for f in findings if f.line_start is not None), rule)
    groups: dict[tuple[int, int], list[Finding]] = {}
    for finding in findings:
        if finding.line_start is not None:
            groups.setdefault(home[_span(finding)], []).append(finding)
    by_status = lambda f: CATEGORIES.index(category(f))  # noqa: E731 – prototype
    sites = [Site(line_start=min(f.line_start for f in items),  # the union of its ranges
                  line_end=max(_span(f)[1] for f in items), findings=sorted(items, key=by_status))
             for _, items in sorted(groups.items())]
    if by_severity:  # "fix this place first": FAIL sites with the most findings on top
        sites.sort(key=lambda s: (CATEGORIES.index(s.worst), -len(s.findings), s.line_start))
    rest = [f for f in findings if f.line_start is None]
    if rest:
        sites.append(Site(line_start=None, line_end=None, findings=sorted(rest, key=by_status)))
    return sites


def site_of(sites: list[Site], finding: Finding) -> Site | None:
    return next((s for s in sites if finding in s.findings), None)


def variant() -> str:
    return st.session_state.get("variant") or "A"


def grouping() -> str:
    return st.session_state.get("grouping") or "gleich"


def _step(offset: int) -> None:
    keys = list(VARIANTS)
    st.session_state["variant"] = keys[(keys.index(variant()) + offset) % len(keys)]


_BAR_CSS = """<style>
.st-key-proto81_bar{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);z-index:999;
  width:max-content!important;max-width:none!important;background:#1F2430;border-radius:999px;
  padding:6px 14px;
  box-shadow:0 6px 24px rgba(0,0,0,.35);gap:8px;flex-wrap:nowrap!important}
.st-key-proto81_bar>div{width:auto!important;flex:0 0 auto!important}
.st-key-proto81_bar [data-testid="stButtonGroup"]>div{flex-wrap:nowrap}
.st-key-proto81_bar p,.st-key-proto81_bar span{color:#FFFFFF!important}
.st-key-proto81_bar button{background:transparent!important;border-color:#5A6170!important;
  white-space:nowrap}
.st-key-proto81_bar button[aria-checked="true"],.st-key-proto81_bar button[kind*="Active"]{
  background:#FFD54A!important;border-color:#FFD54A!important}
.st-key-proto81_bar button[aria-checked="true"] p{color:#1F2430!important;font-weight:700}
</style>"""

# ← → cycle the variant unless the focus sits in a field (the table uses ↑ ↓ only)
_KEYS_JS = """<script>
if (!window.proto81) {
  window.proto81 = true
  document.addEventListener("keydown", (e) => {
    const t = e.target
    if (t.closest?.("input,textarea,[contenteditable]")) return
    const side = {ArrowLeft: "prev", ArrowRight: "next"}[e.key]
    if (side) document.querySelector(`.st-key-proto81_${side} button`)?.click()
  })
}
</script>"""


def render_bar() -> None:
    """Floating switcher, obviously not part of the design. Never on main: Streamlit Community
    Cloud deploys main, this branch is never merged."""
    st.html(_BAR_CSS + _KEYS_JS, unsafe_allow_javascript=True)
    with st.container(horizontal=True, vertical_alignment="center", key="proto81_bar"):
        st.button("←", key="proto81_prev", on_click=_step, args=(-1,), type="tertiary")
        chosen = st.segmented_control("Variante", list(VARIANTS), key="variant",
                                      bind="query-params", default="A", required=True,
                                      label_visibility="collapsed")
        st.markdown(f"**{VARIANTS[chosen or 'A']}**", width="content")
        st.button("→", key="proto81_next", on_click=_step, args=(1,), type="tertiary")
        st.segmented_control("Gruppierung", list(GROUPINGS), key="grouping",
                             bind="query-params", default="gleich", required=True,
                             label_visibility="collapsed")
        st.markdown(GROUPINGS[grouping()], width="content")  # bind keeps the URL value plain
