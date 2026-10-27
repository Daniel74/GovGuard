"""PROTOTYPE #81 – variant C: the document is the list; each site is a marker in its margin,
the chosen site opens in the right column; throwaway, only on branch prototype/81-fundstelle."""

from collections.abc import Callable

import streamlit as st

from govguard.models import Finding
from govguard_ui.report.finding_detail import plain
from govguard_ui.report.prototype_81_sites import Site, mix_text, site_of
from govguard_ui.report.review import category
from govguard_ui.style import LOOKS, badge, badge_css, paragraph

_HTML = '<div class="doc"></div>'
_CSS = """
.doc{font-family:'Source Code Pro',ui-monospace,monospace;font-size:13px;line-height:1.6;
  max-height:620px;overflow:auto;border:1px solid #D5DAE1;border-radius:8px;padding:6px 0}
.l{display:grid;grid-template-columns:84px 36px 1fr;gap:8px;white-space:pre-wrap;
  border-left:4px solid transparent}
.n{text-align:right;color:#6B7482}
.m{text-align:right;padding-right:4px}
.l.in{cursor:pointer}
.l.in.t-fail{border-left-color:#E07A7A;background:#FDF5F5}
.l.in.t-warn{border-left-color:#E0B54A;background:#FFFAEB}
.l.in.t-pass{border-left-color:#7CBF92;background:#F3FAF5}
.l.in.t-na{border-left-color:#C9CFD8;background:#F7F8FA}
.l.sel{background:#E3EEF9!important;border-left-color:#0B4F8A!important}
.l.sel .n{color:#0B4F8A;font-weight:700}
.l.hov{box-shadow:inset 0 0 0 999px rgba(11,79,138,.08)}
.m{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
.badge.cur{outline:2px solid #0B4F8A;outline-offset:1px}
.badge{display:inline-block;padding:0 5px;border:1px solid;border-radius:4px;font-size:11px;
  font-weight:600;cursor:pointer;font-family:system-ui,sans-serif}
""" + badge_css("b-")

_JS = """
export default function ({ data, parentElement, setTriggerValue }) {
  const doc = parentElement.querySelector(".doc")
  const kept = doc.scrollTop
  const byId = Object.fromEntries(data.sites.map((s) => [s.id, s]))
  let divs = []
  const hover = (id, on) => {  // outline every line of the site under the pointer
    const s = byId[id]
    for (let n = s.start; n <= s.end; n++) divs[n - 1]?.classList.toggle("hov", on)
  }
  divs = data.lines.map((line) => {
    const div = document.createElement("div")
    const owner = line.site && byId[line.site]
    div.className = "l" + (owner ? " in t-" + owner.tint : "") + (line.sel ? " sel" : "")
    const m = div.appendChild(document.createElement("span"))
    m.className = "m"
    for (const id of line.markers) {  // every site starting here, the narrow one last
      const s = byId[id]
      const b = m.appendChild(document.createElement("span"))
      b.className = "badge b-" + s.tint + (id === data.current ? " cur" : "")
      b.textContent = s.marker
      b.title = s.tip
      b.onclick = (event) => { event.stopPropagation(); setTriggerValue("site", id) }
      b.onmouseenter = () => hover(id, true)
      b.onmouseleave = () => hover(id, false)
    }
    const n = div.appendChild(document.createElement("span"))
    n.className = "n"
    n.textContent = line.n
    div.appendChild(document.createElement("span")).textContent = line.text || " "
    if (owner) {
      div.title = owner.tip
      div.onclick = () => setTriggerValue("site", owner.id)
      div.onmouseenter = () => hover(owner.id, true)
      div.onmouseleave = () => hover(owner.id, false)
    }
    return div
  })
  doc.replaceChildren(...divs)
  const target = doc.querySelector(".sel")
  if (data.jump && target) doc.scrollTop = target.offsetTop - 80
  else doc.scrollTop = kept
}
"""


LEGEND = ("**Farbe** = schwerster Status der Fundstelle · **Marke** am Rand = Befunde je Status "
          "(✕ 2 · ✓ 1: zwei Verstöße, eine Einhaltung) · **blau** = gewählte Fundstelle · "
          "**Klick** auf Zeile oder Marke wählt die Fundstelle in der Tabelle")


def _tip(site: Site) -> str:
    counts = ", ".join(f"{n} × {LOOKS[c].label}" for c, n in site.mix)
    return f"{site.lines}: {counts}. Klick wählt die Fundstelle in der Tabelle."


def render_site_document(sites: list[Site], text: str, selected: Finding, key: str,
                         on_select: Callable[[str], None]) -> None:
    """A line belongs to the narrowest site that holds it: its colour, its click. Each site has
    a marker on its first line; the chosen site is blue over its whole range."""
    home = site_of(sites, selected)
    placed = sorted((s for s in sites if s.line_start is not None),
                    key=lambda s: s.line_end - s.line_start, reverse=True)
    owner: dict[int, Site] = {}
    starts: dict[int, list[str]] = {}
    for site in placed:  # narrow sites last, so they win
        owner.update({n: site for n in range(site.line_start, site.line_end + 1)})
        starts.setdefault(site.line_start, []).append(site.id)
    chosen = range(home.line_start, home.line_end + 1) if home and home.line_start else range(0)
    lines = [{"n": number, "text": line, "site": owner[number].id if number in owner else None,
              "sel": number in chosen, "markers": starts.get(number, [])}
             for number, line in enumerate(text.splitlines(), 1)]
    info = [{"id": s.id, "start": s.line_start, "end": s.line_end, "tint": LOOKS[s.worst].css,
             "marker": mix_text(s), "tip": _tip(s)} for s in placed]
    jump = st.session_state.get(f"{key}_p81_jumped") != selected.rule_id
    st.session_state[f"{key}_p81_jumped"] = selected.rule_id
    dkey = f"{key}_p81_doc"

    def picked() -> None:
        if site_id := st.session_state[dkey].site:
            site = next(s for s in sites if s.id == site_id)
            on_select(site.findings[0].rule_id)

    st.caption(LEGEND)
    document = st.components.v2.component("proto81_site_document", html=_HTML, css=_CSS, js=_JS)
    document(data={"lines": lines, "sites": info, "current": home.id if home else None,
                   "jump": jump}, key=dkey, on_site_change=picked)
    if sites and sites[-1].line_start is None:
        st.caption(f"Ohne Zeilen: {len(sites[-1].findings)} Befunde (rechts, wenn gewählt)")
        if st.button("Befunde ohne Zeilen zeigen", key=f"{key}_p81_nolines", type="tertiary"):
            on_select(sites[-1].findings[0].rule_id)
            st.rerun()


def render_site_panel(site: Site | None, selected: Finding, key: str,
                      on_select: Callable[[str], None]) -> None:
    if site is None:
        st.info("Wähle links eine markierte Stelle im Dokument.")
        return
    with st.container(border=True):
        st.html(badge(site.worst) + f' <b style="font-size:18px">{site.lines}</b>')
        st.caption(f"{len(site.findings)} Befunde · {mix_text(site)} · "
                   + " · ".join(plain(a) for a in site.anchors))
        with st.container(height=520, border=False):
            for finding in site.findings:
                with st.container(border=finding is selected):
                    st.html(badge(category(finding)) + f" <b>{paragraph(finding.title)[3:-4]}</b>")
                    st.caption(plain(finding.primary_anchor))
                    if finding.recommendation:
                        st.html(f"<div style='font-size:14px'><b>Empfehlung:</b> "
                                f"{paragraph(finding.recommendation)[3:-4]}</div>")
                    with st.popover("Begründung", type="tertiary"):
                        st.html(paragraph(finding.rationale))
                    if finding is not selected:
                        st.button("auswählen", key=f"{key}_p81_c_{finding.rule_id}",
                                  type="tertiary", on_click=on_select, args=(finding.rule_id,))
