"""The box under a site, part of the script of the document (CCv2, #86). WARN and FAIL stand as
one-liners, a click chooses and opens the text; PASS and N/A are folded behind one row. With a
proposal each measure is one line (opens to its before and after) with a shut row "deckt n
Befunde ab" under it that opens to the findings it covers; without one the findings stand under
the heading "Befunde". What is open or folded lives in the browser (ctx.ui), not in the
session: a click on a fold is no rerun. All LLM text goes in as textContent, never innerHTML. The
split, the order, the assignment of the findings to the measures and the texts of the counts come
ready from site_box.py and remediation_data.py. Uses the helpers of site_dom_js.py (one script
together)."""

BOX_JS = """
function foldable(css, open, ctx, key, action) {  // a row that folds: caret, keyboard, aria
  const div = el("div", css)
  div.tabIndex = 0
  div.dataset.key = key  // the document finds the row again after a redraw and gives it the focus
  div.setAttribute("role", "button")
  div.setAttribute("aria-expanded", String(open))
  const caret = div.appendChild(el("span", "caret", open ? "▾" : "▸"))
  caret.setAttribute("aria-hidden", "true")  // the state says aria-expanded, not the symbol
  press(div, () => { action(); ctx.draw() })
  return div
}

function detail(f, ai) {  // twin of _finding() in site_groups.py: the texts, change both
  const div = el("div", "detail")
  div.appendChild(el("div", "a", f.anchor))
  const code = (name) => f.by_code.includes(name)  // texts the code wrote: no marker
  // order of the detail view: why, then what
  div.appendChild(labelled("w", "Begründung", f.rationale, ai, code("rationale")))
  if (f.recommendation) {
    div.appendChild(labelled("r", "Empfehlung", f.recommendation, ai, code("recommendation")))
  }
  return div
}

function finding(f, ctx) {  // one line; a click chooses and opens it, a second click shuts it
  const { data, send, ui } = ctx
  const chosen = f.id === data.selected
  const open = chosen && !!ui.openFindings[f.id]  // chosen alone does not open: see foldState
  const wrap = el("div", "frow" + (chosen ? " sel" : ""))
  const line = wrap.appendChild(foldable("one", open, ctx, "f:" + f.id, () => {
    if (chosen) {
      ui.openFindings[f.id] = !open
    } else {
      ui.opening = f.id  // the rerun brings it back as the choice: foldState keeps it open
      send("clicked", f.id)
    }
  }))
  line.appendChild(el("span", "badge b-" + f.look, f.status))
  line.appendChild(el("span", "t", f.title))
  line.appendChild(el("span", "muted", f.lines))
  if (open) wrap.appendChild(detail(f, data.ai))
  return wrap
}

function covered(m, ctx, rows) {  // "deckt n Befunde ab": shut until clicked, then its findings
  const { ui } = ctx
  const open = !!ui.openCovers[m.id]
  const wrap = el("div", "covers")
  const toggle = () => { ui.openCovers[m.id] = !open }
  wrap.appendChild(foldable("one cov", open, ctx, "c:" + m.id, toggle))
    .appendChild(el("span", "muted", m.covers))
  if (open && rows.length) {
    const list = wrap.appendChild(el("div", "mfinds"))
    rows.forEach((row) => list.appendChild(row))
  }
  return wrap
}

function measure(m, i, block, ctx, rows) {  // one line, opens to before, after, anchors; under it
  // the row of the findings it covers
  const open = !!ctx.ui.openMeasures[m.id]  // m.id follows the content: a new one starts shut
  const wrap = el("div", "mrow")
  const line = wrap.appendChild(foldable("one", open, ctx, "m:" + m.id, () => {
    ctx.ui.openMeasures[m.id] = !open
  }))
  line.appendChild(el("span", "m-t", (i + 1) + ". " + m.sentence)).appendChild(aiMark(block.ai))
  if (open) {
    const body = wrap.appendChild(el("div", "detail"))
    body.appendChild(el("div", "m-l", "Vorher · " + m.lines))  // cut by the code: no marker
    body.appendChild(el("pre", "m-code", m.before))
    const after = body.appendChild(el("div", "m-l", "Nachher "))
    after.appendChild(aiMark(block.ai))  // written by the model
    body.appendChild(el("pre", "m-code", m.after))
    body.appendChild(el("div", "m-c", "deckt ab: " + m.anchors.join(" · ")))
  }
  wrap.appendChild(covered(m, ctx, rows))
  return wrap
}

function heading(text, ai, hint) {  // "Befunde" (no marker: the code checked them), "Maßnahmen"
  const head = el("div", "sec-h")
  head.appendChild(el("strong", "", text))
  if (ai) head.appendChild(aiMark(ai))
  if (hint) head.appendChild(el("span", "muted", hint))
  return head
}

function measures(block, site, byId, ctx) {  // the measures, each with the findings it covers
  const div = el("div", "sugg")
  div.appendChild(heading(block.heading, block.ai, block.hint))
  if (block.failed) div.appendChild(el("div", "m-none", block.text))
  block.measures.forEach((m, i) => {
    const rows = (site.by_measure[m.id] || []).map((id) => finding(byId.get(id), ctx))
    div.appendChild(measure(m, i, block, ctx, rows))
  })
  return div
}

function fold(site, byId, ctx) {  // PASS and N/A behind one row; a chosen one opens it
  const { ui } = ctx
  if (ui.restOpen === undefined && site.rest_auto) ui.restOpen = true  // stays open
  const open = !!ui.restOpen
  const wrap = el("div", "rest")
  wrap.appendChild(foldable("one", open, ctx, "r", () => { ui.restOpen = !open }))
    .appendChild(el("span", "muted", site.rest_text))
  if (open) {
    for (const id of site.rest) wrap.appendChild(finding(byId.get(id), ctx))
  }
  return wrap
}

function icon(text, title, key, action, disabled) {  // a symbol button with tooltip and name
  const button = el("button", "icon", text)
  button.dataset.key = key  // the focus finds it again after the redraw
  button.title = title
  button.setAttribute("aria-label", title)
  button.disabled = disabled
  press(button, action)
  return button
}

function head(index, ctx) {
  const { data, send } = ctx
  const site = data.sites[index]
  const div = el("div", "head")
  div.appendChild(el("b", "", site.label))
  if (site.suggest) {  // #82: the button for the measures
    const button = div.appendChild(el("button", "sugg-btn", site.suggest.label))
    button.dataset.key = "b:suggest"
    press(button, () => send("suggest", String(index)))
  }
  const step = (by) => () => send("site", String(index + by))
  div.appendChild(icon("‹", "vorige Fundstelle", "b:prev", step(-1), !data.sites[index - 1]))
  div.appendChild(icon("›", "nächste Fundstelle", "b:next", step(1), !data.sites[index + 1]))
  div.appendChild(icon("✕", "schließen", "b:close", () => send("closed", data.selected), false))
  return div
}

function box(index, ctx) {
  const site = ctx.data.sites[index]
  const div = el("div", "box")
  div.appendChild(head(index, ctx))
  const suggest = site.suggest
  if (suggest && suggest.note) div.appendChild(el("div", "note", suggest.note))  // under the button
  const block = suggest && suggest.block
  const byId = new Map(site.findings.map((f) => [f.id, f]))
  const grouped = block && !block.failed && block.measures.length > 0
  if (grouped) {  // the findings stand under their measure; none may get lost
    div.appendChild(measures(block, site, byId, ctx))
    if (site.leftover.length) div.appendChild(heading("Weitere Befunde"))
    for (const id of site.leftover) div.appendChild(finding(byId.get(id), ctx))
  } else {
    div.appendChild(heading("Befunde"))
    for (const id of site.open) div.appendChild(finding(byId.get(id), ctx))
  }
  if (site.rest.length) div.appendChild(fold(site, byId, ctx))
  if (block && !grouped) div.appendChild(measures(block, site, byId, ctx))  // "kein Vorschlag"
  return div
}
"""
