"""The script of the document with its sites (CCv2, #81, #84). LLM text goes into the page as
textContent: never a link, image or tag."""

JS = """
function el(tag, css, text) {
  const e = document.createElement(tag)
  if (css) e.className = css
  if (text !== undefined) e.textContent = text  // LLM text: textContent, never innerHTML
  return e
}

function press(node, action) {  // a click, or Enter and Space like a button
  node.onclick = (event) => { event.stopPropagation(); action() }
  node.onkeydown = (event) => {
    if (event.key !== "Enter" && event.key !== " ") return
    event.preventDefault()
    event.stopPropagation()
    action()
  }
}

function labelled(css, name, text, ai, byCode) {  // "Begründung KI: text", like ai_label()
  const div = el("div", css)
  div.appendChild(el("strong", "", name))
  if (!byCode) div.appendChild(el("span", "ai", ai.marker)).title = ai.tip  // not on code text
  div.appendChild(document.createTextNode(": "))
  div.appendChild(el("span", "", text))  // LLM text: textContent, never innerHTML
  return div
}

function item(f, selected, choose, ai) {  // twin of _finding() in site_groups.py: change both
  const div = el("div", "item" + (f.id === selected ? " sel" : ""))
  div.tabIndex = 0
  const head = div.appendChild(el("div"))
  head.appendChild(el("span", "badge b-" + f.look, f.status))
  head.appendChild(el("span", "t", f.title))
  div.appendChild(el("div", "a", f.anchor + " · " + f.lines))
  const code = (name) => f.by_code.includes(name)  // texts the code wrote: no marker
  // order of the detail view: why, then what
  div.appendChild(labelled("w", "Begründung", f.rationale, ai, code("rationale")))
  if (f.recommendation) {
    div.appendChild(labelled("r", "Empfehlung", f.recommendation, ai, code("recommendation")))
  }
  press(div, () => choose(f.id))
  return div
}

function box(index, data, send) {
  const site = data.sites[index]
  const div = el("div", "box")
  const head = div.appendChild(el("div", "head"))
  head.appendChild(el("b", "", site.label))
  for (const [text, step] of [["‹ vorige", -1], ["nächste ›", 1]]) {
    const button = head.appendChild(el("button", "", text))
    button.disabled = !data.sites[index + step]
    press(button, () => send("site", String(index + step)))
  }
  press(head.appendChild(el("button", "", "schließen")), () => send("closed", data.selected))
  const choose = (id) => send("clicked", id)
  for (const f of site.findings) div.appendChild(item(f, data.selected, choose, data.ai))
  return div
}

function back(info) {  // a finding over several sections: its lines stand marked, the way back
  const div = el("div", "back")
  div.appendChild(el("span", "", "Markiert: " + info.title + " · " + info.lines))
  const link = div.appendChild(el("button", "link", "↑ zurück zum Befund"))
  press(link, () => {  // the chosen item of the group: in the page, outside this shadow root
    const item = document.querySelector('[class*="_multi_item_sel_"]')
    if (item) item.scrollIntoView({ block: "center", behavior: "smooth" })
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

export default function ({ data, parentElement, setTriggerValue }) {
  const send = setTriggerValue
  const doc = parentElement.querySelector(".doc")
  const kept = doc.scrollTop
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
    if (data.open && current && current.end === line.n) rows.push(box(data.current, data, send))
  }
  doc.replaceChildren(...rows)
  const chosen = doc.querySelector(".l.in-finding")  // first line of the finding, in any section
  const fresh = doc.dataset.selected !== data.selected  // a new choice, not a rerun
  const top = chosen ? chosen.offsetTop - doc.offsetTop : 0
  const hidden = top < kept || top > kept + doc.clientHeight - 80  // out of sight in the box
  doc.scrollTop = chosen && fresh && hidden ? top - 60 : kept
  if (chosen && fresh && doc.dataset.selected !== undefined && !onScreen(chosen)) {
    chosen.scrollIntoView({ block: "center", behavior: "smooth" })  // the page too, not at load
  }
  doc.dataset.selected = data.selected
}
"""
