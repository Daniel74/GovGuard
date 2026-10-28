"""The script of the document with its sites (CCv2, #81). LLM text goes into the page as
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

function item(f, selected, choose) {  // twin of _finding() in site_groups.py: change both

  const div = el("div", "item" + (f.id === selected ? " sel" : ""))
  div.tabIndex = 0
  const head = div.appendChild(el("div"))
  head.appendChild(el("span", "badge b-" + f.look, f.status))
  head.appendChild(el("span", "t", f.title))
  div.appendChild(el("div", "a", f.anchor + " · " + f.lines))
  div.appendChild(el("div", "w", f.rationale))  // order of the detail view: why, then what
  if (f.recommendation) div.appendChild(el("div", "r", f.recommendation))
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
  for (const f of site.findings) div.appendChild(item(f, data.selected, choose))
  return div
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
  doc.style.setProperty("--n", data.lanes)
  doc.style.setProperty("--lanes", (data.lanes * 19 + 6) + "px")
  const kept = doc.scrollTop
  const rows = []
  const lineDivs = []
  for (const line of data.lines) {
    const div = el("div", "l" + (line.tint ? " t-" + line.tint : "") +
                   (line.selected ? " sel" : ""))
    const lanes = div.appendChild(el("span", "lanes"))
    for (const cell of line.bars) {
      lanes.appendChild(cell ? bar(cell, data, send, lineDivs) : el("span"))
    }
    div.appendChild(el("span", "n", line.n))
    div.appendChild(el("span", "", line.text || " "))
    if (line.owner !== null) {
      div.classList.add("click")
      div.title = data.sites[line.owner].tip
      div.onclick = () => send("site", String(line.owner))
    }
    rows.push(div)
    lineDivs.push(div)
    const current = data.sites[data.current]
    if (data.open && current && current.end === line.n) rows.push(box(data.current, data, send))
  }
  doc.replaceChildren(...rows)
  const chosen = doc.querySelector(".l.sel")  // scroll only when a new choice is out of sight
  const top = chosen ? chosen.offsetTop - doc.offsetTop : 0
  const hidden = top < kept || top > kept + doc.clientHeight - 80
  doc.scrollTop = chosen && doc.dataset.selected !== data.selected && hidden ? top - 60 : kept
  doc.dataset.selected = data.selected
}
"""
