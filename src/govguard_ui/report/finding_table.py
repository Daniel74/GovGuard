"""Finding table as own component (CCv2): columns, row click, arrow keys (#45) and a click on a
column head that asks Python to sort (#80).

No Streamlit widget is a table whose rows are buttons (prototype of #43, variant A). LLM text
reaches the browser raw and goes into the cells as textContent: never a link, image or tag.
"""

from collections.abc import Callable

import streamlit as st

from govguard_ui.style import badge_css

TABLE_HEIGHT = 560  # the table scrolls inside, like the document next to it
COLUMNS = {"status": "Status", "title": "Prüfregel", "primary_anchor": "Normanker",
           "lines": "Zeilen"}  # field of a row (review.SortColumn) -> head

_HEAD = "".join(f'<th data-col="{field}" tabindex="0">{label}</th>'  # a button inside would
                for field, label in COLUMNS.items())  # shift the text by subpixels per run
_HTML = f"""<div class="wrap"><table role="grid" aria-label="Befunde">
<thead><tr>{_HEAD}</tr></thead>
<tbody></tbody></table></div>"""

_CSS = f"""
.wrap{{font-size:14px;line-height:1.5;max-height:{TABLE_HEIGHT}px;overflow:auto;
  border:1px solid #D5DAE1;border-radius:8px;scrollbar-color:#A7AFBA transparent}}
  /* Streamlit passes down a transparent scrollbar-color: the bar would be invisible */
table{{width:100%;border-collapse:collapse}}
th{{position:sticky;top:0;z-index:1;background:#F5F6F8;color:#4A5361;font-weight:600;
  text-align:left;padding:8px}}
th{{cursor:pointer}}
th:hover{{color:#0B4F8A}}
th:focus-visible{{outline:2px solid #0B4F8A;outline-offset:-2px}}
th[aria-sort]::after{{font-size:.8em;margin-left:4px}}
th[aria-sort=ascending]::after{{content:"▲" / ""}}  /* aria-sort says it */
th[aria-sort=descending]::after{{content:"▼" / ""}}
td{{padding:10px 8px;vertical-align:top;border-top:1px solid #E3E7EC;overflow-wrap:break-word}}
th:first-child,td:first-child,th:last-child,td:last-child{{width:1%;white-space:nowrap}}
td:first-child{{white-space:pre}}  /* the downgrade "↓ von …" goes on its own line */
th:nth-child(3){{width:11em}}  /* fits "BSI GS++ KONF.12.1.10", longer ones wrap */
tbody tr{{cursor:pointer}}
tbody tr:hover{{background:#F2F5F9}}
tbody tr.sel{{background:#E3EEF9}}
tbody tr.sel td:nth-child(2){{font-weight:700}}
tbody tr:focus-visible{{outline:2px solid #0B4F8A;outline-offset:-2px}}
.badge{{display:inline-block;padding:0 6px;border:1px solid;border-radius:4px;font-size:13px;
  font-weight:600}}
""" + badge_css("b-")  # the shadow DOM sees no page CSS

_JS = """
const CELLS = [["status", "badge b-"], ["title", ""], ["primary_anchor", ""], ["lines", ""]]

function move(from, to) {  // roving tabindex: the one Tab stop goes with the focus
  from.tabIndex = -1
  to.tabIndex = 0
  to.focus()
}

function rowElement(row, selected, choose) {
  const tr = document.createElement("tr")
  tr.dataset.id = row.id
  tr.tabIndex = -1
  tr.classList.toggle("sel", row.id === selected)
  tr.setAttribute("aria-selected", row.id === selected)
  for (const [field, css] of CELLS) {
    const td = tr.insertCell()
    const text = css ? td.appendChild(document.createElement("span")) : td
    if (css) text.className = css + row.look
    text.textContent = row[field]  // LLM text: textContent, never innerHTML
  }
  tr.onclick = () => choose(row.id)
  tr.onkeydown = (event) => {
    const next = {ArrowDown: tr.nextElementSibling, ArrowUp: tr.previousElementSibling}[event.key]
    if (next || event.key === "Enter") event.preventDefault()
    if (next) move(tr, next)
    if (event.key === "Enter") choose(row.id)
  }
  return tr
}

function markSorted(head, sort, sortBy) {  // the arrow comes from the CSS
  for (const th of head.querySelectorAll("th")) {
    if (th.dataset.col === sort.column) {
      th.setAttribute("aria-sort", sort.descending ? "descending" : "ascending")
    } else {
      th.removeAttribute("aria-sort")
    }
    th.onclick = () => sortBy(th.dataset.col)
    th.onkeydown = (event) => {  // Enter or Space, like a button
      if (event.key !== "Enter" && event.key !== " ") return
      event.preventDefault()
      sortBy(th.dataset.col)
    }
  }
}

export default function ({ data, parentElement, setTriggerValue }) {
  const wrap = parentElement.querySelector(".wrap")
  const body = parentElement.querySelector("tbody")
  const focused = parentElement.activeElement?.dataset?.id  // survives the rebuild below
  const scrolled = wrap.scrollTop
  const choose = (id) => setTriggerValue("clicked", id)
  markSorted(parentElement.querySelector("thead"), data.sort,
             (column) => setTriggerValue("sorted", column))
  body.replaceChildren(...data.rows.map((row) => rowElement(row, data.selected, choose)))
  const order = JSON.stringify(data.sort)  // a new order starts at the top
  wrap.scrollTop = wrap.dataset.order === order ? scrolled : 0
  wrap.dataset.order = order
  // one Tab stop for the whole table, on the selected row after each rebuild
  const start = body.querySelector("tr.sel") ?? body.firstElementChild
  if (start) start.tabIndex = 0
  const again = focused && body.querySelector(`[data-id="${CSS.escape(focused)}"]`)
  again?.focus({preventScroll: true})
}
"""


def render_table(data: dict, key: str, on_select: Callable[[str], None],
                 on_sort: Callable[[str], None]) -> None:
    """data: rows (findings_view.table_rows), the selected rule id and the sort (review.Sorting);
    a click or Enter on a row calls on_select, on a column head on_sort."""
    def clicked() -> None:
        if rule_id := st.session_state[key].clicked:
            on_select(rule_id)

    def resorted() -> None:
        if column := st.session_state[key].sorted:
            on_sort(column)

    # registered on every run: each runtime (also AppTest) needs it, an equal one stays silent
    finding_table = st.components.v2.component(
        "govguard_finding_table", html=_HTML, css=_CSS, js=_JS)
    finding_table(data=data, key=key, on_clicked_change=clicked, on_sorted_change=resorted)
