"""PROTOTYPE #81 – variant E: the document in the middle, full width. Each site is a bar in a
margin lane (its length = its lines), a click opens its findings inline below its last line.
Sites over half the document are no place: they stand above as "das ganze Dokument".
Throwaway, only on branch prototype/81-fundstelle."""

from collections.abc import Callable

import streamlit as st

from govguard.models import Finding
from govguard_ui.report.prototype_81_sites import Site, mix_text, site_of
from govguard_ui.report.review import CATEGORIES, category
from govguard_ui.style import LOOKS, badge_css

NARROW = 15  # lines; a narrower site also tints its lines, a wider one shows only its bar
WHOLE = 0.5  # share of the document from which a site counts as "das ganze Dokument"

_HTML = '<div class="top"></div><div class="doc"></div><div class="bottom"></div>'
_CSS = """
.doc{font-family:'Source Code Pro',ui-monospace,monospace;font-size:13px;line-height:1.6;
  max-height:720px;overflow:auto;border:1px solid #D5DAE1;border-radius:8px;padding:6px 0;
  font-variant-ligatures:none}
.l{display:grid;grid-template-columns:var(--lanes) 40px 1fr;gap:10px;white-space:pre-wrap;
  padding-right:12px}
.lanes{display:grid;grid-template-columns:repeat(var(--n),16px);gap:3px;padding-left:6px}
.bar{cursor:pointer;margin:0 3px;border-radius:0}
.bar.top{border-radius:4px 4px 0 0;margin-top:3px}
.bar.end{border-radius:0 0 4px 4px;margin-bottom:3px}
.bar.top.end{border-radius:4px}
.bar span{display:block;font:700 10px/16px system-ui,sans-serif;text-align:center;margin:0 -3px}
.f-fail{background:#E07A7A;color:#FFFFFF}.f-warn{background:#E0B54A;color:#3A2600}
.f-pass{background:#7CBF92;color:#0F3A1F}.f-na{background:#C9CFD8;color:#2A3038}
.bar.cur{box-shadow:0 0 0 2px #0B4F8A}
.bar:hover{filter:brightness(.9)}
.n{text-align:right;color:#6B7482}
.l.t-fail{background:#FDF3F3}.l.t-warn{background:#FFF8E6}.l.t-pass{background:#F1F9F3}
.l.sel{background:#E3EEF9}
.l.sel .n{color:#0B4F8A;font-weight:700}
.l.hov{box-shadow:inset 0 0 0 999px rgba(11,79,138,.07)}
.l.click{cursor:pointer}
.box{font-family:system-ui,sans-serif;font-size:14px;line-height:1.5;margin:6px 12px 10px 60px;
  border:1px solid #0B4F8A;border-radius:8px;background:#FFFFFF;
  box-shadow:0 4px 16px rgba(11,79,138,.15)}
.box .head{display:flex;gap:8px;align-items:center;padding:8px 12px;background:#E3EEF9;
  border-radius:7px 7px 0 0}
.box .head b{flex:1}
.box button{font:inherit;font-size:13px;border:1px solid #A7AFBA;background:#FFFFFF;
  border-radius:6px;padding:2px 10px;cursor:pointer}
.item{padding:10px 12px;border-top:1px solid #E3E7EC;cursor:pointer}
.item:hover{background:#F7F9FC}
.item.sel{background:#F2F6FB;box-shadow:inset 4px 0 #0B4F8A}
.item .t{font-weight:600}
.item .a{color:#4A5361;font-size:13px}
.item .r{margin-top:4px}
.item .r::before{content:"Empfehlung: ";font-weight:600}
.item .w{margin-top:4px;color:#4A5361}
.item .w::before{content:"Begründung: ";font-weight:600}
.badge{display:inline-block;padding:0 6px;border:1px solid;border-radius:4px;font-size:13px;
  font-weight:600;margin-right:6px}
.group{font-family:system-ui,sans-serif;font-size:14px;border:1px dashed #A7AFBA;
  border-radius:8px;margin:0 0 10px}
.group>summary{padding:8px 12px;cursor:pointer}
.bottom .group{margin:10px 0 0}
.legend{font-family:system-ui,sans-serif;font-size:13px;color:#4A5361;margin:0 0 8px}
""" + badge_css("b-")

_JS = """
function el(tag, css, text) {
  const e = document.createElement(tag)
  if (css) e.className = css
  if (text !== undefined) e.textContent = text  // LLM text: textContent only
  return e
}

function item(f, selected, choose) {
  const div = el("div", "item" + (f.id === selected ? " sel" : ""))
  const head = div.appendChild(el("div"))
  head.appendChild(el("span", "badge b-" + f.look, f.status))
  head.appendChild(el("span", "t", f.title))
  div.appendChild(el("div", "a", f.anchor + " · " + f.lines))
  div.appendChild(el("div", "w", f.rationale))  // order of the detail view: why, then what
  if (f.rec) div.appendChild(el("div", "r", f.rec))
  div.onclick = () => choose(f.id)
  return div
}

function group(title, findings, selected, choose) {
  const box = el("details", "group")
  box.appendChild(el("summary", "", title))
  for (const f of findings) box.appendChild(item(f, selected, choose))
  return box
}

function inline(site, data, send) {
  const box = el("div", "box")
  const head = box.appendChild(el("div", "head"))
  head.appendChild(el("b", "", site.label))
  const at = data.order.indexOf(site.id)
  for (const [text, step] of [["‹ vorige", -1], ["nächste ›", 1]]) {
    const next = data.order[at + step]
    const b = head.appendChild(el("button", "", text))
    b.disabled = !next
    b.onclick = (event) => { event.stopPropagation(); send("site", next) }
  }
  const x = head.appendChild(el("button", "", "schließen"))
  x.onclick = (event) => { event.stopPropagation(); send("closed", data.selected) }
  const choose = (id) => send("clicked", id)
  for (const f of site.findings) box.appendChild(item(f, data.selected, choose))
  return box
}

export default function ({ data, parentElement, setTriggerValue }) {
  const send = setTriggerValue
  const choose = (id) => send("clicked", id)
  const top = parentElement.querySelector(".top")
  const legend = el("div", "legend", "Balken am Rand = eine Fundstelle, so lang wie ihre Zeilen; " +
    "Farbe = schwerster Status, Zahl = Befunde. Klick auf Balken oder Zeile öffnet die " +
    "Befunde direkt unter der Stelle.")
  top.replaceChildren(legend, ...(data.whole.length ? [group(data.wholeTitle, data.whole,
    data.selected, choose)] : []))
  const bottom = parentElement.querySelector(".bottom")
  bottom.replaceChildren(...(data.nolines.length ? [group(data.nolinesTitle, data.nolines,
    data.selected, choose)] : []))
  const doc = parentElement.querySelector(".doc")
  doc.style.setProperty("--n", data.lanes)
  doc.style.setProperty("--lanes", (data.lanes * 19 + 6) + "px")
  const kept = doc.scrollTop
  const rows = []
  const lineDivs = []
  const hover = (id, on) => {
    const s = data.sites[id]
    for (let n = s.start; n <= s.end; n++) lineDivs[n - 1].classList.toggle("hov", on)
  }
  for (const line of data.lines) {
    const div = el("div", "l" + (line.tint ? " t-" + line.tint : "") + (line.sel ? " sel" : ""))
    const lanes = div.appendChild(el("span", "lanes"))
    for (const cell of line.cells) {
      const c = lanes.appendChild(el("span"))
      if (!cell) continue
      const s = data.sites[cell.site]
      c.className = "bar f-" + s.tint + (cell.top ? " top" : "") + (cell.end ? " end" : "") +
                    (cell.site === data.current ? " cur" : "")
      if (cell.top) c.appendChild(el("span", "", s.count))
      c.title = s.tip
      c.onclick = (event) => { event.stopPropagation(); send("site", cell.site) }
      c.onmouseenter = () => hover(cell.site, true)
      c.onmouseleave = () => hover(cell.site, false)
    }
    div.appendChild(el("span", "n", line.n))
    div.appendChild(el("span", "", line.text || " "))
    if (line.owner) {
      div.classList.add("click")
      div.title = data.sites[line.owner].tip
      div.onclick = () => send("site", line.owner)
    }
    rows.push(div)
    lineDivs.push(div)
    const site = data.current && data.sites[data.current]
    if (data.open && site && site.end === line.n) rows.push(inline(site, data, send))
  }
  doc.replaceChildren(...rows)
  const first = doc.querySelector(".l.sel")
  if (data.jump && first) doc.scrollTop = first.offsetTop - doc.offsetTop - 60
  else doc.scrollTop = kept
}
"""


def _lanes(sites: list[Site]) -> dict[str, int]:
    """Overlapping sites go side by side: the first lane that is free again (interval colouring)."""
    ends: list[int] = []
    lane_of = {}
    for site in sorted(sites, key=lambda s: (s.line_start, s.line_start - s.line_end)):
        lane = next((i for i, end in enumerate(ends) if end < site.line_start), len(ends))
        if lane == len(ends):
            ends.append(0)
        ends[lane] = site.line_end
        lane_of[site.id] = lane
    return lane_of


def _finding(f: Finding) -> dict:
    look = LOOKS[category(f)]
    lines = "keine Zeilen" if f.line_start is None else f"Zeilen {f.line_start}–{f.line_end}"
    return {"id": f.rule_id, "look": look.css, "status": f"{look.symbol} {look.label}",
            "title": f.title, "anchor": f.primary_anchor, "rec": f.recommendation or "",
            "rationale": f.rationale, "lines": lines}


def _site(s: Site) -> dict:
    counts = ", ".join(f"{n} × {LOOKS[c].label}" for c, n in s.mix)
    return {"id": s.id, "start": s.line_start, "end": s.line_end, "tint": LOOKS[s.worst].css,
            "count": str(len(s.findings)), "findings": [_finding(f) for f in s.findings],
            "label": f"{s.lines} · {len(s.findings)} Befunde · {mix_text(s)}",
            "tip": f"{s.lines}: {counts}. Klick öffnet die Befunde unter der Stelle."}


def _line_rows(text: str, placed: list[Site], home: Site | None) -> tuple[list[dict], int]:
    lane_of = _lanes(placed)
    lanes = max(lane_of.values(), default=-1) + 1
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        holding = [s for s in placed if s.line_start <= number <= s.line_end]
        cells: list[dict | None] = [None] * lanes
        for s in holding:
            cells[lane_of[s.id]] = {"site": s.id, "top": s.line_start == number,
                                    "end": s.line_end == number}
        narrow = min(holding, key=lambda s: s.line_end - s.line_start, default=None)
        tinted = [s for s in holding if s.line_end - s.line_start < NARROW]
        worst = min((s.worst for s in tinted), key=CATEGORIES.index, default=None)
        rows.append({"n": number, "text": line, "cells": cells, "owner": narrow and narrow.id,
                     "tint": LOOKS[worst].css if worst else "",
                     "sel": home is not None and home in holding})
    return rows, lanes


def render_site_inline(sites: list[Site], selected: Finding, key: str,
                       on_select: Callable[[str], None], text: str) -> None:
    total = max(1, len(text.splitlines()))
    whole = [s for s in sites if s.line_start is not None
             and s.line_end - s.line_start + 1 >= WHOLE * total]
    placed = sorted((s for s in sites if s.line_start is not None and s not in whole),
                    key=lambda s: (s.line_start, s.line_end))
    nolines = [f for s in sites if s.line_start is None for f in s.findings]
    home = site_of(placed, selected)
    rows, lanes = _line_rows(text, placed, home)
    jump = st.session_state.get(f"{key}_p81_e_seen") != selected.rule_id
    st.session_state[f"{key}_p81_e_seen"] = selected.rule_id
    whole_findings = [f for s in whole for f in s.findings]
    data = {"lines": rows, "lanes": lanes, "sites": {s.id: _site(s) for s in placed},
            "order": [s.id for s in placed], "current": home.id if home else None,
            "open": st.session_state.get(f"{key}_p81_closed") != selected.rule_id,
            "selected": selected.rule_id, "jump": jump,
            "whole": [_finding(f) for f in whole_findings],
            "wholeTitle": f"Betrifft das ganze Dokument · {len(whole_findings)} Befunde, "
                          "die fast alle Zeilen als Beleg nennen",
            "nolines": [_finding(f) for f in nolines],
            "nolinesTitle": f"Ohne Zeilen · {len(nolines)} Befunde"}
    ekey = f"{key}_p81_inline"
    by_id = {s.id: s for s in placed}

    def site() -> None:
        if site_id := st.session_state[ekey].site:
            st.session_state.pop(f"{key}_p81_closed", None)
            on_select(by_id[site_id].findings[0].rule_id)

    def clicked() -> None:
        if rule_id := st.session_state[ekey].clicked:
            on_select(rule_id)

    def closed() -> None:
        if rule_id := st.session_state[ekey].closed:
            st.session_state[f"{key}_p81_closed"] = rule_id

    document = st.components.v2.component("proto81_inline", html=_HTML, css=_CSS, js=_JS)
    document(data=data, key=ekey, on_site_change=site, on_clicked_change=clicked,
             on_closed_change=closed)
