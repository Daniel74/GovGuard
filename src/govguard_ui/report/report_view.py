"""One audit report next to its source document; used by gallery and new audits (#11)."""

import streamlit as st

from govguard.models import AuditReport, Expected
from govguard_ui.report.condition_focus import active_focus, render_focus
from govguard_ui.report.condition_review import condition_rows
from govguard_ui.report.conditions_view import render_conditions
from govguard_ui.report.finding_detail import render_detail, render_document
from govguard_ui.report.findings_view import (
    BY_SITE,
    current_source,
    current_view,
    render_findings,
)
from govguard_ui.report.remediation_view import Proposer
from govguard_ui.report.report_header import render_expected, render_header
from govguard_ui.report.site_view import render_by_site


def render_report(  # noqa: PLR0913  # sixth arg: the page's hook (#82)
    report: AuditReport, title: str, source: tuple[str, str], expected: Expected | None,
    key: str, propose: Proposer | None = None,
) -> None:
    """source: file name and text of the audited input; key separates widget state. propose: the
    page's hook for "Maßnahme vorschlagen" (#82); without it the report has no such button."""
    render_header(report, title, key)
    render_conditions(report, source[1], current_source(key), key)
    if expected:
        render_expected(report, expected, key)
    if current_view(key) == BY_SITE:  # no detail column: the findings open under their site
        render_by_site(report, source, key, propose)
        return
    findings, detail = st.columns([3, 2])  # table without side scroll at 1280 px too (#51)
    with findings:
        selected = render_findings(report, key)
    with detail:
        focus = active_focus(condition_rows(report), key)
        if focus:
            render_focus(focus, key)
        else:
            render_detail(selected)
        render_document(*source, selected, key, focus.evidence.ranges if focus else None)
