"""Finding table with status and source filter, the gap checklist and the selected finding;
the same for spec and architecture audits. The selection (<key>_selected) is read and written
only here (#11, #43, #45)."""

from collections import defaultdict
from functools import partial

import streamlit as st

from govguard.models import AuditReport, Finding
from govguard_ui.report.finding_detail import plain
from govguard_ui.report.finding_table import render_table
from govguard_ui.report.review import (
    ALL_SOURCES,
    category,
    category_counts,
    lines_text,
    of_source,
    source_counts,
    visible_findings,
)
from govguard_ui.style import LOOKS, STATUS_FILTERS, status_word

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
    selected = by_rule.get(st.session_state.get(_selection_key(key)))
    return selected or (shown or findings)[0]


def _selection_key(key: str) -> str:
    return f"{key}_selected"


def select(key: str, rule_id: str | None) -> None:
    """Writes the selection; also the callback of an expected check in the header."""
    st.session_state[_selection_key(key)] = rule_id


def render_rows(findings: list[Finding], key: str, selected: Finding) -> None:
    render_table(table_rows(findings), selected.rule_id, f"{key}_table",
                 on_select=partial(select, key))


def table_rows(findings: list[Finding]) -> list[dict[str, str]]:
    """Plain values for the finding table; LLM text stays raw, the cell sets it as textContent."""
    return [{"id": f.rule_id, "look": LOOKS[category(f)].css, "status": status_text(f),
             "title": f.title, "primary_anchor": f.primary_anchor, "lines": lines_text(f)}
            for f in findings]


def status_text(finding: Finding) -> str:
    look = LOOKS[category(finding)]
    status = f"{look.symbol} {look.label}"
    if finding.downgraded_from:  # a downgrade stays visible in the list (ADR 0017)
        status += f"\n↓ von {status_word(finding.downgraded_from)}"  # own line: narrow column
    return status


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
