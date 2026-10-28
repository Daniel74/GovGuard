"""The report "nach Fundstelle": the audited document in full width, a bar per site, the findings
of a site open under it. Only re-orders the findings of the table (#81)."""

import streamlit as st

from govguard.checks.sites import Sites, group_sites
from govguard.models import AuditReport, Finding
from govguard_ui.report.findings_view import (
    current_selection,
    render_head,
    select,
    selected_of,
)
from govguard_ui.report.gaps_view import render_gaps
from govguard_ui.report.site_assets import CSS, HTML
from govguard_ui.report.site_data import site_data
from govguard_ui.report.site_groups import WHOLE, WITHOUT, render_group
from govguard_ui.report.site_script import JS

LEGEND = ("Balken am Rand = eine Fundstelle, so lang wie ihre Zeilen; Farbe = schwerster Status, "
          "Zahl = Befunde. Ein Klick auf Balken oder Zeile öffnet die Befunde unter der Stelle.")


def render_by_site(report: AuditReport, source: tuple[str, str], key: str) -> None:
    """source: file name and text of the audited input."""
    chosen_source, shown = render_head(report, key)
    name, text = source
    total_lines = len(text.splitlines())
    sites = group_sites(shown, total_lines)
    selected = selected_of(report.findings, shown, key)  # before a click the table's first row
    render_group(WHOLE, [f for s in sites.whole for f in s.findings], selected, f"{key}_whole")
    with st.container(border=True, key=f"{key}_site_document"):  # frame, head as by rule
        with st.container(key=f"{key}_site_document_head"):  # own keys: no reuse on a switch
            st.markdown(f"**Geprüftes Dokument** · `{name}` · {total_lines} Zeilen")
        st.caption(LEGEND)
        _render_document(sites, text, selected, key)
    render_group(WITHOUT, sites.without_lines, selected, f"{key}_without")
    render_gaps(report, chosen_source, key)


def _closed_key(key: str) -> str:
    return f"{key}_site_closed"


def _render_document(sites: Sites, text: str, selected: Finding, key: str) -> None:
    closed = st.session_state.get(_closed_key(key)) == selected.rule_id
    state = f"{key}_sites"

    def site_clicked() -> None:  # the bar or a line: the worst finding of the site is chosen
        if index := st.session_state[state].site:
            st.session_state.pop(_closed_key(key), None)
            select(key, sites.placed[int(index)].findings[0].rule_id)

    def finding_clicked() -> None:
        if rule_id := st.session_state[state].clicked:
            select(key, rule_id)

    def box_closed() -> None:  # the choice in the state, not the sent one: a click may be newer
        if sent := st.session_state[state].closed:
            st.session_state[_closed_key(key)] = current_selection(key) or sent

    # registered on every run: each runtime (also AppTest) needs it, an equal one stays silent
    site_document = st.components.v2.component("govguard_site_document", html=HTML, css=CSS, js=JS)
    site_document(data=site_data(sites, text, selected, closed), key=state,
                  on_site_change=site_clicked, on_clicked_change=finding_clicked,
                  on_closed_change=box_closed)
