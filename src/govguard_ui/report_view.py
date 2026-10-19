"""One audit report next to its source document; used by gallery and new audits (#11)."""

import streamlit as st

from govguard.models import AuditReport, Expected
from govguard_ui.finding_detail import render_detail, render_document
from govguard_ui.findings_view import render_findings
from govguard_ui.report_header import render_expected, render_header


def render_report(
    report: AuditReport, title: str, source: tuple[str, str], expected: Expected | None,
    key: str,
) -> None:
    """source: file name and text of the audited input; key separates widget state."""
    render_header(report, title, key)
    if expected:
        render_expected(report, expected, key)
    findings, detail = st.columns([3, 2])  # table without side scroll at 1280 px too (#51)
    with findings:
        selected = render_findings(report, key)
    with detail:
        render_detail(selected)
        render_document(*source, selected, key)
