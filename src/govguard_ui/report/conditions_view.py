"""Frame "Bedingungen" of a spec report: one pill per condition, its popover explains the
result with quote, effect and criteria (#61, ADR 0028)."""

import streamlit as st

from govguard.checks.conditions import CONTRADICTION
from govguard.condition_models import ConditionDef, ConditionResult
from govguard.models import AuditReport
from govguard_ui.report.condition_focus import focus_on, popover_key
from govguard_ui.report.condition_review import (
    condition_rows,
    criterion,
    effect_text,
    evidence_of,
    lines_label,
    rule_counts,
)
from govguard_ui.report.finding_detail import plain
from govguard_ui.report.quote import quote
from govguard_ui.texts import HELP, VALUE_WORDS

ICONS = {"yes": ":material/check:", "no": ":material/block:", "unstated": ":material/help:"}
CONTRADICTION_ICON = ":material/warning:"  # the stricter value wins, the reader should look
NOT_STATED = "Die Eingabe sagt nichts dazu."


def render_conditions(report: AuditReport, source_text: str, source: str | None,
                      key: str) -> None:
    """source: the source filter of the table; the gaps in the popovers count only that one."""
    rows = condition_rows(report)
    if not rows:
        return
    counts = rule_counts([cond for cond, _ in rows], report.findings, source)
    by_id = {cond.id: cond for cond, _ in rows}
    with st.container(border=True, key=f"{key}_conditions"):
        st.markdown("#### Bedingungen", help=HELP["conditions"])
        st.caption("Was sagt die Eingabe zu den Bedingungen?")
        with st.container(horizontal=True, vertical_alignment="center"):
            for cond, result in rows:
                _pill(cond, result, (by_id, counts[cond.id], source_text), key)


def _pill(cond: ConditionDef, result: ConditionResult,
          context: tuple[dict[str, ConditionDef], tuple[int, int], str], key: str) -> None:
    by_id, (rules, gaps), source_text = context
    contradiction = result.note == CONTRADICTION
    label = f"{cond.name[:1].upper()}{cond.name[1:]}: {VALUE_WORDS[result.value]}"
    icon = CONTRADICTION_ICON if contradiction else ICONS[result.value]
    with st.popover(label, icon=icon, key=popover_key(key, cond.id)):
        st.markdown(f"**{cond.name}**")
        st.caption(cond.meaning)
        st.markdown(f"**Ergebnis: {VALUE_WORDS[result.value]}**")
        _result_block(cond, result, by_id, source_text, key)
        st.markdown("**Wirkung**")
        st.caption(effect_text(cond, result.value, rules, gaps))
        st.markdown("**Kriterien**")
        st.caption(f"ja: {cond.yes}  \nnein: {cond.no}  \nnicht genannt: {NOT_STATED}")


def _result_block(cond: ConditionDef, result: ConditionResult, by_id: dict[str, ConditionDef],
                  source_text: str, key: str) -> None:
    if result.value == "unstated":
        st.caption(f"Die Eingabe sagt nicht, ob {cond.only_if}.")
    if result.derived_from in by_id:
        source = by_id[result.derived_from]
        st.caption(f"Folgt aus der Bedingung {source.name}: {source.no}")
    elif result.note:  # a contradiction, or why the pre-run could not decide
        st.caption(result.note)
    for evidence in evidence_of(result):
        where = lines_label(evidence.ranges)
        counter = evidence.kind == "denying" and result.value == "yes"
        st.caption(f"{'Gegenbeleg' if counter else 'Beleg'} ({where}): "
                   f"„{plain(quote(source_text, evidence.ranges))}“  \nErfülltes Kriterium: "
                   f"{criterion(cond, result, evidence.kind, by_id)}")
        st.button(f"{where} im Dokument", type="tertiary", icon=":material/arrow_forward:",
                  key=f"{key}_condition_go_{cond.id}_{evidence.kind}",
                  on_click=focus_on, args=(key, cond.id, evidence.kind))
