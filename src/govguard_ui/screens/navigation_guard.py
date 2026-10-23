"""Guard against a page switch while an audit runs, as own component (CCv2, #77).

A page link starts a new script run and Streamlit stops the audit in it; the report is lost.
st.dialog needs a script run itself, so the question comes from the browser: an own <dialog>,
since confirm() labels its buttons "OK"/"Abbrechen" and "Abbrechen" would mean "stay".
"""

from collections.abc import Iterator
from contextlib import contextmanager

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

QUESTION = "Audit läuft noch. Wenn Sie die Seite wechseln, geht es verloren."
STAY = "Weiter prüfen"
LEAVE = "Audit abbrechen und wechseln"

_HTML = f"""<dialog aria-labelledby="gg-guard-question">
<p id="gg-guard-question">{QUESTION}</p>
<div class="row"><button class="stay" autofocus>{STAY}</button>
<button class="leave">{LEAVE}</button></div></dialog>"""

_CSS = """
dialog{max-width:28rem;padding:24px;border:1px solid var(--st-border-color);border-radius:8px;
  color:var(--st-text-color);background:var(--st-background-color);font-family:var(--st-font)}
dialog::backdrop{background:rgb(26 34 51 / 40%)}
p{margin:0 0 20px;line-height:1.5}
.row{display:flex;gap:12px;justify-content:flex-end;flex-wrap:wrap}
button{padding:6px 14px;border-radius:8px;font:inherit;cursor:pointer;
  border:1px solid var(--st-border-color);background:var(--st-background-color);
  color:var(--st-text-color)}
.stay{border-color:var(--st-primary-color);background:var(--st-primary-color);color:#FFFFFF}
"""

_JS = """
const LINKS = '[data-testid="stSidebar"] [data-testid="stPageLink-NavLink"]'

export default function ({ parentElement }) {
  const dialog = parentElement.querySelector("dialog")
  let chosen = null  // the link the person leaves through, let pass once
  const hold = (event) => {
    const link = event.target.closest?.(LINKS)
    if (!link || link === chosen) return
    event.preventDefault()
    event.stopImmediatePropagation()  // before Streamlit's own click handler
    chosen = link
    dialog.showModal()
  }
  parentElement.querySelector(".stay").onclick = () => {
    chosen = null
    dialog.close()
  }
  parentElement.querySelector(".leave").onclick = () => {
    dialog.close()
    chosen.click()
  }
  window.addEventListener("click", hold, true)  // capture: runs before any link handler
  return () => window.removeEventListener("click", hold, true)
}
"""


@contextmanager
def guard_navigation(slot: DeltaGenerator) -> Iterator[None]:
    """While the block runs, a click on a page link asks first; afterwards links are free.

    slot: an st.empty() the page creates at the same place in every run. A rerun drops the
    unsent slot.empty() below, so only the next run's own st.empty() removes the guard; at a
    fixed place it does so at once, not after the whole page.
    """
    guard = st.components.v2.component("govguard_navigation_guard", html=_HTML, css=_CSS, js=_JS)
    with slot:
        guard(key="navigation_guard")
    try:
        yield
    finally:
        slot.empty()  # also after a failed audit, which shows its error without a rerun
