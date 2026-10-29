"""The small DOM helpers of the component of "nach Fundstelle" (CCv2): shared by the document
(site_script) and the box under a site (site_box_script), which come after it in one script.
LLM text goes in as textContent: never a link, image or tag."""

DOM_JS = """
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

function aiMark(ai) {  // the "KI" next to model text, like ai_label()
  const mark = el("span", "ai", ai.marker)
  mark.title = ai.tip
  return mark
}

function labelled(css, name, text, ai, byCode) {  // "Begründung KI: text", like ai_label()
  const div = el("div", css)
  div.appendChild(el("strong", "", name))
  if (!byCode) div.appendChild(aiMark(ai))  // not on text the code wrote
  div.appendChild(document.createTextNode(": "))
  div.appendChild(el("span", "", text))  // LLM text: textContent, never innerHTML
  return div
}
"""
