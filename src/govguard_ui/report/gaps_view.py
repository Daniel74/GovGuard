"""Gaps below the finding table: the old checklist, or with conditions split by condition
(#11, #61)."""

from collections import defaultdict

import streamlit as st

from govguard.models import AuditReport, Finding
from govguard_ui.report.condition_review import condition_rows, group_gaps
from govguard_ui.report.finding_detail import plain
from govguard_ui.report.review import category, of_source
from govguard_ui.style import LOOKS
from govguard_ui.texts import HELP

GAPS_HEIGHT = 360  # a long gap list scrolls
GROUP_HEIGHT = 300


def render_gaps(report: AuditReport, source: str | None, key: str) -> None:
    """The key keeps a list open while its label counts the gaps of another source."""
    gaps = [f for f in of_source(report.findings, source) if category(f) == "GAP"]
    if not gaps:
        return
    rows = condition_rows(report)
    if rows:
        _by_condition(gaps, rows, key)
    else:
        _checklist(gaps, key)


def _gap_list(gaps: list[Finding]) -> None:
    """Grouped by source (DSGVO) or SDM module (SDM Löschen)."""
    groups: dict[str, list[Finding]] = defaultdict(list)
    for finding in gaps:
        groups[_gap_group(finding.primary_anchor)].append(finding)
    for name, items in groups.items():
        st.markdown(f"**{plain(name)}** · {len(items)}")
        st.markdown("\n".join(f"- {plain(f.title)} · {plain(f.primary_anchor)}" for f in items))


def _gap_group(anchor: str) -> str:
    parts = anchor.split(" ")
    return " ".join(parts[:-1]) if parts[0] == "SDM" else parts[0]


def _checklist(gaps: list[Finding], key: str) -> None:
    with st.expander(f"Was die Eingabe nicht beschreibt · {len(gaps)} Lücken", key=f"{key}_gaps"):
        st.caption("Kein Verstoß. Zu diesen Prüfregeln sagt die Eingabe nichts; vor der "
                   "Umsetzung klären oder bewusst ausschließen. Im JSON-Report haben sie den "
                   f"Status {LOOKS['GAP'].code}.")
        with st.container(height=GAPS_HEIGHT, border=False):
            _gap_list(gaps)


def _by_condition(gaps: list[Finding], rows, key: str) -> None:
    defs = [cond for cond, _ in rows]
    groups = group_gaps(gaps, defs, {cond.id: result for cond, result in rows})
    conditional = sum(len(items) for items in groups.by_condition.values())
    st.markdown(f"### Lücken · {len(gaps)}", help=HELP["gaps"])
    st.caption(f"Jede Lücke steht genau einmal: {len(groups.common)} gelten für jedes Vorhaben, "
               f"{conditional} nur unter einer Bedingung, die die Eingabe offen lässt.")
    if groups.common:
        with st.expander(f"Für jedes Vorhaben zu klären · {len(groups.common)} Lücken",
                         icon=":material/checklist:", key=f"{key}_gaps_common"):
            st.caption("Diese Prüfregeln gelten unabhängig von den Bedingungen.")
            with st.container(height=GAPS_HEIGHT, border=False):
                _gap_list(groups.common)
    for cond in defs:
        if items := groups.by_condition.get(cond.id):
            with st.expander(f"Nur wenn {cond.only_if} · {len(items)} Lücken",
                             icon=":material/help:", key=f"{key}_gaps_{cond.id}"):
                st.caption(f"Die Eingabe sagt nicht, ob {cond.only_if}. Trifft das nicht zu, "
                           "entfallen diese Lücken. Trifft es zu, gehören sie zu „Für jedes "
                           "Vorhaben zu klären“.")
                with st.container(height=GROUP_HEIGHT, border=False):
                    _gap_list(items)
