"""The script of the document with its sites (CCv2, #81, #84): lines, bars, the way back. The box
under a site is in site_box_script (#86), the DOM helpers in site_dom_js; the three are one
script. LLM text goes into the page as textContent: never a link, image or tag."""

from govguard_ui.report.site_box_script import BOX_JS
from govguard_ui.report.site_dom_js import DOM_JS

_DOCUMENT_JS = """
function back(info) {  // a finding over several sections: its lines stand marked, the way back
  const div = el("div", "back")
  div.appendChild(el("span", "", "Markiert: " + info.title + " · " + info.lines))
  const link = div.appendChild(el("button", "link", "↑ zurück zum Befund"))
  press(link, () => {  // the chosen item of the group: in the page, outside this shadow root
    const item = document.querySelector('[class*="_multi_item_sel_"]')
    if (!item) return
    const group = item.closest("details")  // the group is shut by default: open it the way the
    if (group && !group.open) group.querySelector("summary").click()  // reader would (#86)
    setTimeout(() => item.scrollIntoView({ block: "center", behavior: "smooth" }), 100)
  })
  return div
}

function onScreen(node) {  // inside the window, below the header of the page
  const r = node.getBoundingClientRect()
  return r.top >= 64 && r.bottom <= window.innerHeight
}

function bar(cell, data, send, lineDivs) {
  const site = data.sites[cell.site]
  const span = el("span", "bar f-" + site.look + (cell.top ? " top" : "") +
                  (cell.end ? " end" : "") + (cell.site === data.current ? " cur" : ""))
  if (cell.top) span.appendChild(el("span", "", site.count))
  span.title = site.tip
  span.tabIndex = 0
  span.setAttribute("role", "button")
  press(span, () => send("site", String(cell.site)))
  const hover = (on) => {
    for (let n = site.start; n <= site.end; n++) lineDivs[n - 1].classList.toggle("hov", on)
  }
  span.onmouseenter = () => hover(true)
  span.onmouseleave = () => hover(false)
  return span
}

function focusKey(doc) {  // the row with the focus: the redraw replaces every node
  const active = doc.getRootNode().activeElement
  return active && active.dataset ? active.dataset.key : undefined
}

function paint(ctx) {  // the whole document; also a click on a fold, which is no rerun
  const { data, send, doc } = ctx
  const kept = doc.scrollTop
  const focus = focusKey(doc)
  const rows = data.back ? [back(data.back)] : []
  const lineDivs = []
  for (const line of data.lines) {
    const div = el("div", "l" + (line.tint ? " t-" + line.tint : "") +
                   (line.in_site ? " in-site" : "") + (line.in_finding ? " in-finding" : ""))
    const lane = div.appendChild(el("span", "lane"))  // one lane: sections never overlap
    if (line.bar) lane.appendChild(bar(line.bar, data, send, lineDivs))
    div.appendChild(el("span", "n", line.n))
    div.appendChild(el("span", "", line.text || " "))
    if (line.bar) {
      div.classList.add("click")
      div.title = data.sites[line.bar.site].tip
      div.onclick = () => send("site", String(line.bar.site))
    }
    rows.push(div)
    lineDivs.push(div)
    const current = data.sites[data.current]
    if (data.open && current && current.end === line.n) rows.push(box(data.current, ctx))
  }
  doc.replaceChildren(...rows)
  const chosen = doc.querySelector(".l.in-finding")  // first line of the finding, in any section
  // a new choice, not a rerun; one made at the box (its line clicked) leaves the view where it is
  const fresh = doc.dataset.selected !== data.selected && !ctx.ui.stay
  const top = chosen ? chosen.offsetTop - doc.offsetTop : 0
  const hidden = top < kept || top > kept + doc.clientHeight - 80  // out of sight in the box
  doc.scrollTop = chosen && fresh && hidden ? top - 60 : kept
  if (chosen && fresh && doc.dataset.selected !== undefined && !onScreen(chosen)) {
    chosen.scrollIntoView({ block: "center", behavior: "smooth" })  // the page too, not at load
  }
  doc.dataset.selected = data.selected
  const again = focus && doc.querySelector('[data-key="' + CSS.escape(focus) + '"]')
  if (again) again.focus({ preventScroll: true })  // Enter on a row must not lose the focus
}

function foldState(doc, data) {  // what is open in the box lives here, in the browser (#86)
  const ui = doc._ui || (doc._ui = { openMeasures: {}, openCovers: {}, openFindings: {} })
  const site = data.sites[data.current]
  const section = site ? site.start + "-" + site.end : null  // not the list index: a filter or
  if (ui.section !== section) {  // a new audit moves other sections there; another one is fresh
    Object.assign(ui, { openMeasures: {}, openCovers: {}, openFindings: {}, section })
    delete ui.restOpen
  }
  if (ui.selected !== data.selected) {  // a finding starts shut, unless its line was clicked
    const clicked = ui.opening === data.selected
    Object.assign(ui, { openFindings: clicked ? { [data.selected]: true } : {},
                        selected: data.selected, stay: clicked })  // stay: the view stays put
    delete ui.opening
    if (site && site.rest_auto) delete ui.restOpen  // the fold opens when the choice lies inside
  }
  return ui
}

export default function ({ data, parentElement, setTriggerValue }) {
  const doc = parentElement.querySelector(".doc")
  const ctx = { data, doc, send: setTriggerValue, ui: foldState(doc, data), draw: null }
  ctx.draw = () => paint(ctx)
  paint(ctx)
}
"""

JS = DOM_JS + BOX_JS + _DOCUMENT_JS
