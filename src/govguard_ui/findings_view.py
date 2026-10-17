"""Finding list with filters, the gap checklist and the selected finding (#11)."""

from collections import defaultdict

import streamlit as st

from govguard.models import AuditReport, Finding
from govguard_ui.review import (
    category,
    category_counts,
    new_click,
    source_of,
    visible_findings,
)
from govguard_ui.style import LOOKS

FILTERS = ("FAIL", "WARN", "PASS", "N/A")  # gaps are no filter: they stand below the list
DEFAULT_FILTERS = ["FAIL", "WARN", "PASS"]  # N/A hidden by default (design artefact)
COLUMNS = {"Status": st.column_config.TextColumn(width="small"),
           "Prüfregel": st.column_config.TextColumn(width="medium"),
           "Primäranker": st.column_config.TextColumn(width="small"),
           "Zeilen": st.column_config.TextColumn(width="small")}


def render_findings(report: AuditReport, key: str) -> Finding:
    """Draws the list and returns the selected finding (state key <key>_selected)."""
    counts = category_counts(report.findings)
    chosen = st.pills("Status", FILTERS, selection_mode="multi", default=DEFAULT_FILTERS,
                      key=f"{key}_status", format_func=lambda c: _filter_label(c, counts[c]))
    sources = sorted({source_of(f) for f in report.findings})
    source = st.segmented_control("Quelle", sources, key=f"{key}_source")  # None: all
    shown = visible_findings(report.findings, set(chosen), source)
    st.caption(f"{len(shown)} Befunde angezeigt · {counts['GAP']} Lücken stehen unter der Liste "
               "· sortiert: FAIL zuerst, dann nach Zeile")
    _pick_from_table(shown, key, table_key=f"{key}_table_{'-'.join(chosen)}_{source}")
    if hidden := [f"{counts[c]} {c}" for c in FILTERS if c not in chosen and counts[c]]:
        st.caption(f"Ausgeblendet: {', '.join(hidden)}.")
    _gap_checklist(report.findings, source)
    return _selected(report.findings, shown, key)


def _filter_label(name: str, count: int) -> str:
    look = LOOKS[name]
    label = "WARN · Prüfbedarf" if name == "WARN" else look.label
    return f"{look.symbol} {label} ({count})"


def _pick_from_table(shown: list[Finding], key: str, table_key: str) -> None:
    rows = [{"Status": _status_text(f), "Prüfregel": f.title, "Primäranker": f.primary_anchor,
             "Zeilen": lines_text(f)} for f in shown]
    event = st.dataframe(rows, hide_index=True, on_select="rerun", selection_mode="single-row",
                         key=table_key, height=420, column_config=COLUMNS)
    if click := new_click(event.selection.rows, table_key, st.session_state.get(f"{key}_picked")):
        st.session_state[f"{key}_picked"] = click
        st.session_state[f"{key}_selected"] = shown[click[1]].rule_id


def _status_text(finding: Finding) -> str:
    """Symbol and status; a downgrade stays visible in the list (ADR 0017)."""
    text = f"{LOOKS[category(finding)].symbol} {finding.status}"
    return f"{text} ↓ von {finding.downgraded_from}" if finding.downgraded_from else text


def _selected(findings: list[Finding], shown: list[Finding], key: str) -> Finding:
    by_rule = {f.rule_id: f for f in findings}
    selected = by_rule.get(st.session_state.get(f"{key}_selected"))
    return selected or (shown or findings)[0]


def _gap_checklist(findings: list[Finding], source: str | None) -> None:
    groups: dict[str, list[Finding]] = defaultdict(list)
    for finding in findings:
        if category(finding) == "GAP" and source in (None, source_of(finding)):
            groups[_gap_group(finding.primary_anchor)].append(finding)
    total = sum(len(items) for items in groups.values())
    if not total:
        return
    with st.expander(f"○ Was die Eingabe nicht beschreibt · {total} Lücken"):
        st.caption("Kein Verstoß. Zu diesen Prüfregeln sagt die Eingabe nichts; vor der "
                   "Umsetzung klären oder bewusst ausschließen. Im Report haben sie den Status "
                   "WARN ohne Belegzeilen.")
        for name, items in groups.items():
            st.markdown(f"**{name}** · {len(items)}")
            st.markdown("\n".join(f"- {f.title} · {f.primary_anchor}" for f in items))


def _gap_group(anchor: str) -> str:
    """SDM keeps its module (SDM Löschen), other sources group by name (DSGVO)."""
    parts = anchor.split(" ")
    return " ".join(parts[:-1]) if parts[0] == "SDM" else parts[0]


def lines_text(finding: Finding) -> str:
    if finding.line_start is None:
        return "–"
    if finding.line_start == finding.line_end:
        return str(finding.line_start)
    return f"{finding.line_start}–{finding.line_end}"
