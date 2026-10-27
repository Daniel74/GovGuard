"""PROTOTYPE #81 – variant A: the finding table with one collapsible head row per site;
throwaway, only on branch prototype/81-fundstelle."""

from collections.abc import Callable

import streamlit as st

from govguard.models import Finding
from govguard_ui.report.prototype_81_sites import Site, mix_text, site_of
from govguard_ui.report.review import CATEGORIES, _natural, category
from govguard_ui.style import LOOKS, badge_css

_HTML = """<div class="wrap"><table aria-label="Befunde nach Fundstelle">
<thead><tr><th data-col="lines" tabindex="0">Fundstelle</th>
<th data-col="status" tabindex="0">Status</th>
<th data-col="anchors" tabindex="0">Prüfregel / Normanker</th>
<th data-col="count" tabindex="0">Befunde</th></tr></thead><tbody></tbody></table></div>"""

_CSS = """
.wrap{font-size:14px;line-height:1.5;max-height:560px;overflow:auto;border:1px solid #D5DAE1;
  border-radius:8px}
table{width:100%;border-collapse:collapse}
th{position:sticky;top:0;z-index:1;background:#F5F6F8;color:#4A5361;text-align:left;
  padding:8px;cursor:pointer}
th:hover{color:#0B4F8A}
th[aria-sort]::after{font-size:.8em;margin-left:4px}
th[aria-sort=ascending]::after{content:"▲" / ""}
th[aria-sort=descending]::after{content:"▼" / ""}
td{padding:8px;vertical-align:top;border-top:1px solid #E3E7EC}
tr.site{cursor:pointer;background:#FAFBFC}
tr.site td{font-weight:600}
tr.site td:first-child{white-space:nowrap}
tr.site:hover{background:#F2F5F9}
tr.site.cur{background:#E3EEF9;box-shadow:inset 4px 0 #0B4F8A}
tr.site .tri{display:inline-block;width:1em;color:#6B7482}
tr.site .anchors{font-weight:400;color:#4A5361;font-size:13px}
tr.child{cursor:pointer}
tr.child td:first-child{padding-left:28px;color:#6B7482}
tr.child:hover{background:#F2F5F9}
tr.child.sel{background:#E3EEF9}
tr.child.sel .t{font-weight:700}
.rec{color:#4A5361;font-size:13px;margin-top:2px}
.rec::before{content:"Empfehlung: ";font-weight:600}
.badge{display:inline-block;padding:0 6px;border:1px solid;border-radius:4px;font-size:13px;
  font-weight:600;white-space:nowrap}
.mix{display:block;font-weight:400;color:#4A5361;font-size:12px;margin-top:2px}
""" + badge_css("b-")

_JS = """
function cell(tr, text, css) {
  const td = tr.insertCell()
  if (css) { const s = td.appendChild(document.createElement("span")); s.className = css;
             s.textContent = text } else td.textContent = text
  return td
}

function markSorted(head, sort, sortBy) {
  for (const th of head.querySelectorAll("th")) {
    if (th.dataset.col === sort.column) {
      th.setAttribute("aria-sort", sort.descending ? "descending" : "ascending")
    } else th.removeAttribute("aria-sort")
    th.onclick = () => sortBy(th.dataset.col)
  }
}

export default function ({ data, parentElement, setTriggerValue }) {
  markSorted(parentElement.querySelector("thead"), data.sort,
             (column) => setTriggerValue("sorted", column))
  const body = parentElement.querySelector("tbody")
  const rows = []
  for (const site of data.sites) {
    const head = document.createElement("tr")
    head.className = "site" + (site.current ? " cur" : "")
    head.title = site.current ? "Gewählte Fundstelle · Klick klappt sie zu oder auf"
                              : "Klick wählt die Fundstelle und markiert sie im Dokument"
    const first = head.insertCell()
    const tri = first.appendChild(document.createElement("span"))
    tri.className = "tri"
    tri.textContent = site.open ? "▾" : "▸"
    first.append(site.lines)
    const status = cell(head, site.worst, "badge b-" + site.look)
    const mix = status.appendChild(document.createElement("span"))
    mix.className = "mix"
    mix.textContent = site.mix
    const anchors = head.insertCell()
    anchors.className = "anchors"
    anchors.textContent = site.anchors  // LLM text: textContent only
    cell(head, site.count)
    head.onclick = () => setTriggerValue("site", site.id)
    rows.push(head)
    if (!site.open) continue
    for (const f of site.findings) {
      const tr = document.createElement("tr")
      tr.className = "child" + (f.id === data.selected ? " sel" : "")
      cell(tr, "")
      cell(tr, f.status, "badge b-" + f.look)
      const td = tr.insertCell()
      const t = td.appendChild(document.createElement("div"))
      t.className = "t"
      t.textContent = f.title + " · " + f.anchor
      if (f.rec) { const r = td.appendChild(document.createElement("div"))
                   r.className = "rec"; r.textContent = f.rec }
      cell(tr, "")
      tr.onclick = () => setTriggerValue("clicked", f.id)
      rows.push(tr)
    }
  }
  body.replaceChildren(...rows)
  const wrap = parentElement.querySelector(".wrap")
  let head = body.querySelector("tr.sel")  // jump to the head row of the chosen site
  while (head && !head.classList.contains("site")) head = head.previousElementSibling
  if (data.jump && head) {
    wrap.scrollTop += head.getBoundingClientRect().top - wrap.getBoundingClientRect().top - 40
  }
}
"""


def _open_key(key: str) -> str:
    return f"{key}_proto81_open"


def _toggle(key: str, site_id: str) -> None:
    opened = st.session_state.setdefault(_open_key(key), set())
    opened.symmetric_difference_update({site_id})


_SORT_KEYS = {  # status: worst first, then the biggest site
    "lines": lambda s: s.line_start,
    "status": lambda s: (CATEGORIES.index(s.worst), -len(s.findings)),
    "anchors": lambda s: _natural(s.anchors[0]),
    "count": lambda s: len(s.findings),
}


def _sorting(key: str) -> tuple[str, bool]:
    return st.session_state.get(f"{key}_p81_sort", ("status", False))


def _sort_by(key: str, column: str) -> None:
    current, descending = _sorting(key)
    st.session_state[f"{key}_p81_sort"] = (column, current == column and not descending)


def sorted_sites(sites: list[Site], key: str) -> list[Site]:
    """Sites without lines stay last both ways."""
    column, descending = _sorting(key)
    placed = sorted((s for s in sites if s.line_start is not None), key=_SORT_KEYS[column],
                    reverse=descending)
    return placed + [s for s in sites if s.line_start is None]


def _follow(sites: list[Site], selected: Finding, key: str) -> tuple[Site | None, bool]:
    """A new selection opens its site and lets the table jump there."""
    opened = st.session_state.setdefault(_open_key(key), set())
    home = site_of(sites, selected)
    jump = st.session_state.get(f"{key}_proto81_seen") != selected.rule_id
    if home and jump:
        opened.add(home.id)
    st.session_state[f"{key}_proto81_seen"] = selected.rule_id
    return home, jump


def _site_row(s: Site, current: bool, open_: bool) -> dict:
    return {
        "id": s.id, "current": current, "lines": s.lines, "look": LOOKS[s.worst].css,
        "worst": f"{LOOKS[s.worst].symbol} {LOOKS[s.worst].label}", "mix": mix_text(s),
        "count": str(len(s.findings)), "anchors": " · ".join(s.anchors), "open": open_,
        "findings": [{"id": f.rule_id, "look": LOOKS[category(f)].css,
                      "status": f"{LOOKS[category(f)].symbol} {LOOKS[category(f)].label}",
                      "title": f.title, "anchor": f.primary_anchor,
                      "rec": f.recommendation or ""} for f in s.findings]}


def render_site_table(sites: list[Site], selected: Finding, key: str,
                      on_select: Callable[[str], None]) -> None:
    sites = sorted_sites(sites, key)
    home, jump = _follow(sites, selected, key)
    opened = st.session_state[_open_key(key)]
    column, descending = _sorting(key)
    data = {"selected": selected.rule_id, "jump": jump,
            "sort": {"column": column, "descending": descending},
            "sites": [_site_row(s, s is home, s.id in opened) for s in sites]}
    tkey = f"{key}_proto81_table"

    def clicked() -> None:
        if rule_id := st.session_state[tkey].clicked:
            on_select(rule_id)

    def picked() -> None:  # a click on the chosen site folds it, on another one chooses it
        if not (site_id := st.session_state[tkey].site):
            return
        if home and home.id == site_id:
            _toggle(key, site_id)
        else:
            on_select(next(s for s in sites if s.id == site_id).findings[0].rule_id)
            st.session_state[_open_key(key)].add(site_id)

    def resorted() -> None:
        if column := st.session_state[tkey].sorted:
            _sort_by(key, column)

    table = st.components.v2.component("proto81_site_table", html=_HTML, css=_CSS, js=_JS)
    table(data=data, key=tkey, on_clicked_change=clicked, on_site_change=picked,
          on_sorted_change=resorted)
