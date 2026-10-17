"""PROTOTYPE – throwaway, never merge into src/ (question for #43).

Question: does a click on a finding row need our own component (CCv2), or do styled
Streamlit widgets give the same UX? Three variants on one gallery report, switchable via
?variant=A|B|C or the floating bar (arrow keys work, too).

Run: uv run streamlit run prototypes/row_click.py
"""

import re
import time

import streamlit as st

from govguard.models import Finding
from govguard_ui.finding_detail import render_detail, render_document
from govguard_ui.findings_view import lines_text
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report_header import render_header
from govguard_ui.review import category, visible_findings
from govguard_ui.style import CSS, LOOKS, badge

PRESET = "spec-meldeportal-gesundheit"  # long titles, many rows: the hard case
VARIANTS = {"A": "Eigene Komponente (CCv2)", "B": "Native Buttons als Liste",
            "C": "Spalten + unsichtbarer Button"}
FILTERS = ("FAIL", "WARN", "PASS", "N/A")


# --- variant A: own component, HTML table, click -> trigger value --------------------------

def _component_css() -> str:
    looks = "\n".join(
        f".b-{look.css}{{color:{look.text};background:{look.background};"
        f"border:1px {look.border_style} {look.border}}}" for look in LOOKS.values())
    return """
.wrap{max-height:520px;overflow:auto;font-family:var(--st-font);color:var(--st-text-color)}
table{width:100%;border-collapse:collapse;font-size:15px}
th{position:sticky;top:0;background:#EEF0F4;color:#4A5361;font-size:14px;text-align:left;
  padding:8px 10px;font-weight:600}
td{padding:8px 10px;vertical-align:top}
tbody tr{cursor:pointer;border-left:3px solid transparent}
tbody tr:hover{background:#F2F5F9}
tbody tr:focus{outline:2px solid #0B4F8A;outline-offset:-2px}
tbody tr.sel{background:#E3EEF9;border-left-color:#0B4F8A}
.badge{display:inline-block;padding:1px 8px;border-radius:4px;font-weight:700;
  white-space:nowrap;font-size:14px}
.muted{color:#4A5361;font-size:14px}
""" + looks


_TABLE_JS = """
export default function (component) {
  const { data, parentElement, setTriggerValue } = component
  const body = parentElement.querySelector("tbody")
  const focused = parentElement.activeElement?.dataset?.id  // survives the rebuild below
  body.replaceChildren()
  for (const row of data.rows) {
    const tr = document.createElement("tr")
    tr.dataset.id = row.id
    // roving tabindex: one Tab stop for the whole table, arrows move inside
    tr.tabIndex = row.id === data.selected ? 0 : -1
    if (row.id === data.selected) tr.className = "sel"
    const cells = [["badge b-" + row.css, row.status], ["", row.title],
                   ["muted", row.anchor], ["muted", row.lines]]
    for (const [cls, text] of cells) {
      const td = document.createElement("td")
      const span = document.createElement("span")
      span.className = cls
      span.textContent = text  // LLM text: textContent, never innerHTML
      td.appendChild(span)
      tr.appendChild(td)
    }
    tr.onclick = () => setTriggerValue("clicked", row.id)
    tr.onkeydown = (e) => {
      const next = {ArrowDown: tr.nextElementSibling, ArrowUp: tr.previousElementSibling}[e.key]
      if (next) { e.preventDefault(); e.stopPropagation(); next.focus(); return }
      if (e.key !== "Enter" && e.key !== " ") return
      e.preventDefault()
      setTriggerValue("clicked", row.id)
    }
    body.appendChild(tr)
  }
  if (!body.querySelector("[tabindex='0']") && body.firstChild) body.firstChild.tabIndex = 0
  if (focused) body.querySelector(`[data-id="${CSS.escape(focused)}"]`)?.focus()
}
"""

ROW_TABLE = st.components.v2.component(
    "proto_row_table",
    html="""
<div class="wrap"><table>
  <thead><tr><th>Status</th><th>Prüfregel</th><th>Primäranker</th><th>Zeilen</th></tr></thead>
  <tbody></tbody>
</table></div>
""",
    css=_component_css(),
    js=_TABLE_JS,
)


def _on_component_click() -> None:
    clicked = st.session_state["proto_a_table"].clicked
    if clicked:
        st.session_state["proto_selected"] = clicked


def variant_a(shown: list[Finding], selected: str) -> None:
    rows = [{"id": f.rule_id, "css": LOOKS[category(f)].css, "status": _status_text(f),
             "title": f.title, "anchor": f.primary_anchor, "lines": lines_text(f)}
            for f in shown]
    ROW_TABLE(data={"rows": rows, "selected": selected}, key="proto_a_table",
              on_clicked_change=_on_component_click)


# --- variant B: one native button per row, label in markdown --------------------------------

BADGE_COLOUR = {"FAIL": "red", "WARN": "orange", "GAP": "gray", "PASS": "green", "N/A": "gray"}


def variant_b(shown: list[Finding], selected: str) -> None:
    # selection only via CSS: key and type stay, so the focused button is not remounted
    st.html("""<style>
.st-key-proto_b button{justify-content:flex-start;padding:6px 10px}
.st-key-proto_b button > div{justify-content:flex-start;width:100%}
.st-key-proto_b button p{text-align:left}
.st-key-proto_b [data-testid="stVerticalBlock"]{gap:2px}
</style>""" + f"""<style>.st-key-proto_b_{_css_key(selected)} button{{background:#E3EEF9;
  box-shadow:inset 3px 0 0 #0B4F8A}}</style>""")
    with st.container(key="proto_b", height=520, border=False):
        for f in shown:
            kind = category(f)
            label = (f":{BADGE_COLOUR[kind]}-badge[{LOOKS[kind].symbol} {f.status}] "
                     f"**{f.title}** · :gray[{f.primary_anchor} · Z. {lines_text(f)}]")
            st.button(label, key=f"proto_b_{f.rule_id}", width="stretch", wrap=True,
                      type="tertiary", on_click=_select, args=(f.rule_id,))


# --- variant C: real columns per row, a transparent button lies over the whole row ----------

WIDTHS = [2.2, 6, 3, 1.3]


def variant_c(shown: list[Finding], selected: str) -> None:
    st.html("""<style>
.st-key-proto_c [data-testid="stVerticalBlock"]{gap:0}
[class*="st-key-proto_c_row_"]{position:relative;padding:6px 8px;border-left:3px solid transparent}
[class*="st-key-proto_c_row_"]:hover{background:#F2F5F9}
[class*="st-key-proto_c_row_"]:has(button:focus-visible){outline:2px solid #0B4F8A;
  outline-offset:-2px}
[class*="st-key-proto_c_row_"] p{margin:0}
[class*="st-key-proto_c_row_"] [data-testid="stElementContainer"]:has(button){
  position:absolute;inset:0;margin:0;z-index:1}
[class*="st-key-proto_c_row_"] button{width:100%;height:100%;opacity:0;cursor:pointer}
.st-key-proto_c_head{background:#EEF0F4;padding:8px 8px 4px}
</style>""" + f"""<style>.st-key-proto_c_row_{_css_key(selected)}{{background:#E3EEF9;
  border-left-color:#0B4F8A!important}}</style>""")
    with st.container(key="proto_c", height=520, border=False):
        with st.container(key="proto_c_head"):
            for col, name in zip(st.columns(WIDTHS), ("Status", "Prüfregel", "Primäranker",
                                                      "Zeilen"), strict=True):
                col.markdown(f"**{name}**")
        for f in shown:  # key by rule, not by position: a stable key keeps the focus
            with st.container(key=f"proto_c_row_{f.rule_id}"):
                status, title, anchor, lines = st.columns(WIDTHS)
                status.html(badge(category(f)))
                title.markdown(f.title)
                anchor.caption(f.primary_anchor)
                lines.caption(lines_text(f))
                st.button(f"Befund {f.title} wählen", key=f"proto_c_btn_{f.rule_id}",
                          on_click=_select, args=(f.rule_id,))


# --- shared frame: switcher, state, real header/detail/document ------------------------------

def _css_key(rule_id: str) -> str:
    """Streamlit turns the key into a class and replaces '.' by '-' (Art.9 -> Art-9)."""
    return re.sub(r"[^A-Za-z0-9_-]", "-", rule_id)


def _select(rule_id: str) -> None:
    st.session_state["proto_selected"] = rule_id


def _status_text(finding: Finding) -> str:
    text = f"{LOOKS[category(finding)].symbol} {finding.status}"
    return f"{text} ↓ von {finding.downgraded_from}" if finding.downgraded_from else text


def _step(delta: int) -> None:
    keys = list(VARIANTS)
    current = st.query_params.get("variant", "A")
    st.query_params["variant"] = keys[(keys.index(current) + delta) % len(keys)]


def switcher(variant: str, selected: str, table_ms: float) -> None:
    st.html("""<style>
.st-key-proto_switcher{position:fixed;bottom:16px;left:50%;transform:translateX(-50%);
  z-index:1000;width:auto!important;background:#111827;border-radius:999px;
  padding:4px 14px;box-shadow:0 6px 24px rgba(0,0,0,.35);align-items:center}
.st-key-proto_switcher p,.st-key-proto_switcher button{color:#F9FAFB!important}
.st-key-proto_switcher [data-testid="stCaptionContainer"] p{color:#9CA3AF!important}
</style>""")
    runs = st.session_state["proto_runs"] = st.session_state.get("proto_runs", 0) + 1
    with st.container(key="proto_switcher", horizontal=True, gap="small", width="content"):
        st.button("◀", key="proto_prev", type="tertiary", shortcut="Left",
                  on_click=_step, args=(-1,))
        st.markdown(f"**{variant} — {VARIANTS[variant]}**")
        st.button("▶", key="proto_next", type="tertiary", shortcut="Right",
                  on_click=_step, args=(1,))
        st.caption(f"gewählt: {selected} · Tabelle {table_ms:.0f} ms (Python) · Lauf {runs}")


@st.cache_data
def _entry():
    return next(e for e in load_gallery(PRESETS, GALLERY) if e.preset_id == PRESET)


def main() -> None:
    st.set_page_config(page_title="PROTOTYPE Zeilenklick", layout="wide")
    st.html(CSS)
    variant = st.query_params.get("variant", "A")
    if variant not in VARIANTS:
        variant = "A"
    entry = _entry()
    report = entry.report
    st.title("Audits ansehen")
    render_header(report, entry.preset.title, key="proto")
    left, right = st.columns([11, 10])
    with left:
        st.markdown("### Befunde")
        chosen = st.pills("Status", FILTERS, selection_mode="multi",
                          default=["FAIL", "WARN", "PASS"], key="proto_status")
        shown = visible_findings(report.findings, set(chosen), None)
        st.caption(f"{len(shown)} Befunde angezeigt")
        selected = st.session_state.setdefault("proto_selected", shown[0].rule_id)
        start = time.perf_counter()
        {"A": variant_a, "B": variant_b, "C": variant_c}[variant](shown, selected)
        table_ms = (time.perf_counter() - start) * 1000
    finding = next(f for f in report.findings if f.rule_id == st.session_state["proto_selected"])
    with right:
        render_detail(finding)
        render_document(entry.source_name, entry.source_text, finding, key="proto")
    switcher(variant, finding.rule_id, table_ms)


main()
