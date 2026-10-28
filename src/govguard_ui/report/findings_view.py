"""Finding table with status and source filter, the gap checklist and the selected finding;
the same for spec and architecture audits. The selection (<key>_selected) and the order
(<key>_sort) are read and written only here (#11, #43, #45, #80)."""

from functools import partial

import streamlit as st

from govguard.models import AuditReport, Finding
from govguard_ui.report.finding_table import render_table
from govguard_ui.report.gaps_view import render_gaps
from govguard_ui.report.review import (
    ALL_SOURCES,
    SortColumn,
    Sorting,
    category,
    category_counts,
    lines_text,
    of_source,
    sorted_findings,
    source_counts,
    visible_findings,
)
from govguard_ui.style import LOOKS, STATUS_FILTERS, status_text

DEFAULT_FILTERS = ["FAIL", "WARN", "PASS"]  # N/A hidden by default (design artefact)


VIEWS = ["nach Fundstelle", "nach Prüfregel"]  # the document with its sites, or the table (#81)
BY_SITE, BY_RULE = VIEWS  # nach Fundstelle is the default: fix a place once, not seven findings


def current_view(key: str) -> str:
    return st.session_state.get(f"{key}_view") or BY_SITE


def show_by_rule(key: str) -> None:
    """The table again, e.g. for a condition: its focus works only there (#61)."""
    st.session_state[f"{key}_view"] = BY_RULE


def render_findings(report: AuditReport, key: str) -> Finding:
    """Draws the table and returns the selected finding (state key <key>_selected)."""
    source, shown = render_head(report, key)
    selected = selected_of(report.findings, shown, key)
    render_rows(shown, key, selected)
    render_gaps(report, source, key)
    return selected


def render_head(report: AuditReport, key: str) -> tuple[str | None, list[Finding]]:
    """Switch, source and status filter of both views; returns the source and the findings
    shown. Every number follows the source: source count = sum of the status counts."""
    st.markdown("### Befunde")
    st.segmented_control("Ansicht", VIEWS, default=BY_SITE, required=True, key=f"{key}_view",
                         label_visibility="collapsed")
    source = _source_filter(report.findings, key)
    counts = category_counts(of_source(report.findings, source))
    chosen = st.pills("Status", STATUS_FILTERS, selection_mode="multi", default=DEFAULT_FILTERS,
                      key=f"{key}_status", format_func=lambda c: _filter_label(c, counts[c]),
                      label_visibility="collapsed")  # the colours say it (design artefact)
    shown = sorted_findings(visible_findings(report.findings, set(chosen), source),
                            current_sorting(key))
    listed = sum(counts[c] for c in STATUS_FILTERS)
    st.caption(f"{len(shown)} von {listed} Befunden angezeigt")
    return source, shown


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


def selected_of(findings: list[Finding], shown: list[Finding], key: str) -> Finding:
    by_rule = {f.rule_id: f for f in findings}
    selected = by_rule.get(st.session_state.get(_selection_key(key)))
    return selected or (shown or findings)[0]


def _selection_key(key: str) -> str:
    return f"{key}_selected"


def current_selection(key: str) -> str | None:
    """Rule id the reader chose; None until the first click (the first row stands in)."""
    return st.session_state.get(_selection_key(key))


def select(key: str, rule_id: str | None) -> None:
    """Writes the selection; also the callback of an expected check in the header. Every call
    counts, a click on the finding that is already chosen too (see condition_focus)."""
    st.session_state[_selection_key(key)] = rule_id
    st.session_state[_clicks_key(key)] = selections(key) + 1


def _clicks_key(key: str) -> str:
    return f"{key}_selections"


def selections(key: str) -> int:
    """How often the reader chose a finding (table row or expected check)."""
    return st.session_state.get(_clicks_key(key), 0)


def current_source(key: str) -> str | None:
    """The source chosen in the filter; None for all (also before the filter is drawn)."""
    source = st.session_state.get(f"{key}_source")
    return None if source in (None, ALL_SOURCES) else source


def current_sorting(key: str) -> Sorting:
    """The order the reader chose with a click on a column head; status ascending before (#80)."""
    return st.session_state.get(f"{key}_sort", Sorting())


def sort_by(key: str, column: SortColumn) -> None:
    st.session_state[f"{key}_sort"] = current_sorting(key).clicked(column)


def render_rows(findings: list[Finding], key: str, selected: Finding) -> None:
    data = {"rows": table_rows(findings), "selected": selected.rule_id,
            "sort": current_sorting(key).model_dump()}
    render_table(data, f"{key}_table", on_select=partial(select, key),
                 on_sort=partial(sort_by, key))


def table_rows(findings: list[Finding]) -> list[dict[str, str]]:
    """Plain values for the finding table; LLM text stays raw, the cell sets it as textContent."""
    return [{"id": f.rule_id, "look": LOOKS[category(f)].css, "status": status_text(f),
             "title": f.title, "primary_anchor": f.primary_anchor, "lines": lines_text(f)}
            for f in findings]
