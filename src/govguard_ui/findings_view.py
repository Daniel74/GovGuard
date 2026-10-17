"""Finding list with filters (spec) or groups (architecture), the gap checklist and the
selected finding (#11, #43)."""

from collections import defaultdict

import streamlit as st

from govguard.models import AuditReport, Finding
from govguard_ui.finding_list import ROWS_HEIGHT, group_size, plain, render_groups, render_rows
from govguard_ui.review import (
    ALL_SOURCES,
    category,
    category_counts,
    source_counts,
    source_groups,
    source_of,
    visible_findings,
)
from govguard_ui.style import LOOKS, STATUS_FILTERS

DEFAULT_FILTERS = ["FAIL", "WARN", "PASS"]  # N/A hidden by default (design artefact)
GAPS_HEIGHT = 360  # a long gap list scrolls


def render_findings(report: AuditReport, key: str) -> Finding:
    """Draws the list and returns the selected finding (state key <key>_selected)."""
    if report.audit_type == "architecture":
        return _grouped(report, key)
    return _filtered(report, key)


def _grouped(report: AuditReport, key: str) -> Finding:
    """No filters: the groups replace the source filter, N/A is collapsed in each group."""
    st.markdown("### Befunde nach Quelle")
    groups = source_groups(report.findings)
    size = sum(group_size(group) for group in groups)
    st.caption(f"{size} Befunde in {len(groups)} Quellen · je Gruppe FAIL zuerst · N/A eingeklappt")
    listed = [f for group in groups for f in group.listed]
    collapsed = [f for group in groups for f in group.not_applicable]
    selected = _selected(report.findings, listed or collapsed, key)  # never a gap
    render_groups(groups, key, selected)
    _gap_checklist(report.findings, None, key)
    return selected


def _filtered(report: AuditReport, key: str) -> Finding:
    st.markdown("### Befunde")
    counts = category_counts(report.findings)
    chosen = st.pills("Status", STATUS_FILTERS, selection_mode="multi", default=DEFAULT_FILTERS,
                      key=f"{key}_status", format_func=lambda c: _filter_label(c, counts[c]),
                      label_visibility="collapsed")  # the colours say it (design artefact)
    source = _source_filter(report.findings, key)
    shown = visible_findings(report.findings, set(chosen), source)
    st.caption(f"{len(shown)} Befunde angezeigt · {counts['GAP']} Lücken stehen unter der Liste "
               "· sortiert: FAIL zuerst, dann nach Zeile")
    selected = _selected(report.findings, shown, key)
    with st.container(height=ROWS_HEIGHT, border=True):
        render_rows(shown, key, selected)
    if hidden := [f"{counts[c]} {c}" for c in STATUS_FILTERS if c not in chosen and counts[c]]:
        st.caption(f"Ausgeblendet: {', '.join(hidden)}.")
    _gap_checklist(report.findings, source, key)
    return selected


def _filter_label(name: str, count: int) -> str:
    look = LOOKS[name]
    label = "WARN · Prüfbedarf" if name == "WARN" else look.label
    return f"{look.symbol} {label} {count}"


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
    for finding in findings:
        if category(finding) == "GAP" and source in (None, source_of(finding)):
            groups[_gap_group(finding.primary_anchor)].append(finding)
    total = sum(len(items) for items in groups.values())
    if not total:
        return
    with st.expander(f"Was die Eingabe nicht beschreibt · {total} Lücken", key=f"{key}_gaps"):
        st.caption("Kein Verstoß. Zu diesen Prüfregeln sagt die Eingabe nichts; vor der "
                   "Umsetzung klären oder bewusst ausschließen. Im Report haben sie den Status "
                   "WARN ohne Belegzeilen.")
        with st.container(height=GAPS_HEIGHT, border=False):
            for name, items in groups.items():
                st.markdown(f"**{plain(name)}** · {len(items)}")
                st.markdown("\n".join(f"- {plain(f.title)} · {plain(f.primary_anchor)}"
                                      for f in items))


def _gap_group(anchor: str) -> str:
    """SDM keeps its module (SDM Löschen), other sources group by name (DSGVO)."""
    parts = anchor.split(" ")
    return " ".join(parts[:-1]) if parts[0] == "SDM" else parts[0]
