"""Finding table with status and source filter, the gap checklist and the selected finding;
the same for spec and architecture audits (#11, #43, #45)."""

from collections import defaultdict

import streamlit as st

from govguard.models import AuditReport, Finding
from govguard_ui.finding_detail import plain
from govguard_ui.finding_list import render_rows
from govguard_ui.review import (
    ALL_SOURCES,
    category,
    category_counts,
    of_source,
    source_counts,
    visible_findings,
)
from govguard_ui.style import LOOKS, STATUS_FILTERS

DEFAULT_FILTERS = ["FAIL", "WARN", "PASS"]  # N/A hidden by default (design artefact)
GAPS_HEIGHT = 360  # a long gap list scrolls


def render_findings(report: AuditReport, key: str) -> Finding:
    """Draws the table and returns the selected finding (state key <key>_selected).
    Every number follows the source: source count = sum of the status counts."""
    st.markdown("### Befunde")
    source = _source_filter(report.findings, key)
    counts = category_counts(of_source(report.findings, source))
    chosen = st.pills("Status", STATUS_FILTERS, selection_mode="multi", default=DEFAULT_FILTERS,
                      key=f"{key}_status", format_func=lambda c: _filter_label(c, counts[c]),
                      label_visibility="collapsed")  # the colours say it (design artefact)
    shown = visible_findings(report.findings, set(chosen), source)
    listed = sum(counts[c] for c in STATUS_FILTERS)
    st.caption(f"{len(shown)} von {listed} Befunden angezeigt")
    selected = _selected(report.findings, shown, key)
    render_rows(shown, key, selected)
    _gap_checklist(report.findings, source, key)
    return selected


def _filter_label(name: str, count: int) -> str:
    look = LOOKS[name]
    return f"{look.symbol} {look.label} {count}"


def _source_filter(findings: list[Finding], key: str) -> str | None:
    """None: all sources; required, so a click on the active source keeps it."""
    counts = source_counts(findings)
    with st.container(horizontal=True, vertical_alignment="center"):
        st.markdown("Quelle", width="content")
        source = st.segmented_control(
            "Quelle", list(counts), default=ALL_SOURCES, required=True, key=f"{key}_source",
            format_func=lambda s: f"{s} ({counts[s]})", label_visibility="collapsed")
    return None if source == ALL_SOURCES else source


def _selected(findings: list[Finding], shown: list[Finding], key: str) -> Finding:
    by_rule = {f.rule_id: f for f in findings}
    selected = by_rule.get(st.session_state.get(f"{key}_selected"))
    return selected or (shown or findings)[0]


def _gap_checklist(findings: list[Finding], source: str | None, key: str) -> None:
    """The key keeps the list open while its label counts the gaps of another source."""
    groups: dict[str, list[Finding]] = defaultdict(list)
    for finding in of_source(findings, source):
        if category(finding) == "GAP":
            groups[_gap_group(finding.primary_anchor)].append(finding)
    total = sum(len(items) for items in groups.values())
    if not total:
        return
    with st.expander(f"Was die Eingabe nicht beschreibt · {total} Lücken", key=f"{key}_gaps"):
        st.caption("Kein Verstoß. Zu diesen Prüfregeln sagt die Eingabe nichts; vor der "
                   "Umsetzung klären oder bewusst ausschließen. Im JSON-Report haben sie den "
                   f"Status {LOOKS['GAP'].code}.")
        with st.container(height=GAPS_HEIGHT, border=False):
            for name, items in groups.items():
                st.markdown(f"**{plain(name)}** · {len(items)}")
                st.markdown("\n".join(f"- {plain(f.title)} · {plain(f.primary_anchor)}"
                                      for f in items))


def _gap_group(anchor: str) -> str:
    """SDM keeps its module (SDM Löschen), other sources group by name (DSGVO)."""
    parts = anchor.split(" ")
    return " ".join(parts[:-1]) if parts[0] == "SDM" else parts[0]
