"""One audit report next to its source document; used by gallery and new audits (#11)."""

import streamlit as st

from govguard.condition_models import LineRange
from govguard.models import AuditReport, Expected
from govguard_ui.report.condition_focus import active_focus, render_focus
from govguard_ui.report.condition_review import condition_rows
from govguard_ui.report.conditions_view import render_conditions
from govguard_ui.report.finding_detail import render_detail, render_document
from govguard_ui.report.findings_view import current_source, render_findings, select
from govguard_ui.report.prototype_81_document import (  # PROTOTYPE #81
    render_site_document,
    render_site_panel,
)
from govguard_ui.report.prototype_81_sites import VIEWS, render_bar, site_of, variant
from govguard_ui.report.report_header import render_expected, render_header


def render_report(
    report: AuditReport, title: str, source: tuple[str, str], expected: Expected | None,
    key: str,
) -> None:
    """source: file name and text of the audited input; key separates widget state."""
    render_bar()  # PROTOTYPE #81
    render_header(report, title, key)
    render_conditions(report, source[1], current_source(key), key)
    if expected:
        render_expected(report, expected, key)
    if st.session_state.get(f"{key}_view") == VIEWS[1] and variant() == "E":
        render_findings(report, key, source[1])  # PROTOTYPE #81: the document, full width
        return
    findings, detail = st.columns([3, 2])  # table without side scroll at 1280 px too (#51)
    with findings:
        selected = render_findings(report, key, source[1])
    with detail:
        focus = active_focus(condition_rows(report), key)
        by_site = st.session_state.get(f"{key}_view") == VIEWS[1]
        site = site_of(st.session_state.get(f"{key}_p81_sites", []), selected)
        if by_site and variant() == "C" and not focus:  # PROTOTYPE #81: the document is left
            render_site_panel(site, selected, key, lambda rule_id: select(key, rule_id))
            return
        if by_site and variant() == "D" and not focus:  # PROTOTYPE #81: A's table, C's colours
            st.markdown(f"**Geprüftes Dokument** · `{source[0]}` · "
                        f"{len(source[1].splitlines())} Zeilen")
            render_site_document(st.session_state[f"{key}_p81_sites"], source[1], selected, key,
                                 lambda rule_id: select(key, rule_id))
            render_detail(selected)
            return
        if by_site and variant() == "B" and site and site.line_start and not focus:
            render_detail(selected)
            render_document(*source, selected, key, [LineRange(
                line_start=site.line_start, line_end=site.line_end)])
            return
        if focus:
            render_focus(focus, key)
        else:
            render_detail(selected)
        render_document(*source, selected, key, focus.evidence.ranges if focus else None)
