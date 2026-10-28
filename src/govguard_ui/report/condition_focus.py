"""The jump from a condition into the document: state and the card that replaces the detail
(#61). Ends when the reader picks a finding."""

from typing import NamedTuple

import streamlit as st
from pydantic import BaseModel

from govguard.condition_models import ConditionDef, ConditionResult
from govguard_ui.report.condition_review import (
    Evidence,
    Kind,
    criterion,
    evidence_of,
    lines_label,
    rules_text,
)
from govguard_ui.report.findings_view import selections, show_by_rule
from govguard_ui.texts import VALUE_WORDS


class ConditionFocus(BaseModel):
    cond: ConditionDef
    result: ConditionResult
    evidence: Evidence
    criterion: str  # the sentence the marked lines satisfy


class Jump(NamedTuple):  # what the reader clicked, and how many findings were chosen by then
    cond_id: str
    kind: Kind
    selections: int


def _state(key: str) -> str:
    return f"{key}_condition_focus"


def popover_key(key: str, cond_id: str) -> str:
    """Changes with every jump: a popover has no close call, a new identity opens it closed."""
    return f"{key}_condition_{cond_id}_{st.session_state.get(_jumps(key), 0)}"


def _jumps(key: str) -> str:
    return f"{key}_condition_jumps"


def focus_on(key: str, cond_id: str, kind: Kind) -> None:
    """Callback of the jump button: remembers the jump and the count of chosen findings, to
    notice a later choice. The popover would cover the page, so it gets a new identity."""
    show_by_rule(key)  # "nach Fundstelle" has no detail column to mark the lines in (#81)
    st.session_state[_jumps(key)] = st.session_state.get(_jumps(key), 0) + 1
    st.session_state[_state(key)] = Jump(cond_id, kind, selections(key))


def clear_focus(key: str) -> None:
    st.session_state[_state(key)] = None


def active_focus(rows: list[tuple[ConditionDef, ConditionResult]], key: str
                 ) -> ConditionFocus | None:
    """None once a finding was chosen since the jump, even the one already shown."""
    jump: Jump | None = st.session_state.get(_state(key))
    if not jump or jump.selections != selections(key):
        return None
    by_id = {cond.id: cond for cond, _ in rows}
    for cond, result in rows:
        for evidence in evidence_of(result):
            if cond.id == jump.cond_id and evidence.kind == jump.kind:
                return ConditionFocus(cond=cond, result=result, evidence=evidence,
                                      criterion=criterion(cond, result, jump.kind, by_id))
    return None


def render_focus(focus: ConditionFocus, key: str) -> None:
    cond, result = focus.cond, focus.result
    with st.container(border=True):
        st.markdown(f"#### Bedingung: {cond.name} · {VALUE_WORDS[result.value]}")
        st.markdown(focus.criterion)
        st.caption(f"Markiert: {lines_label(focus.evidence.ranges)} im Dokument. "
                   f"Davon hängen ab: {rules_text(cond)}.")
        st.button("Zurück zum Befund", icon=":material/close:", type="tertiary",
                  key=f"{key}_condition_close", on_click=clear_focus, args=(key,))
