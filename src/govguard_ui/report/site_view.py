"""The report "nach Fundstelle": the audited document in full width, a bar per site (a section
with findings), the findings of a site open under it. Only re-orders the findings of the table
(#81, #84)."""

import streamlit as st

from govguard.checks.sections import split_sections
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
from govguard_ui.report.site_groups import MULTI, WITHOUT, render_group
from govguard_ui.report.site_script import JS
from govguard_ui.texts import HELP

LEGEND = ("Balken am Rand = eine Fundstelle, also ein Abschnitt mit Befunden; Farbe = schwerster "
          "Status, Zahl = Befunde. Ein Klick auf Balken oder Zeile öffnet die Befunde unter dem "
          "Abschnitt.")


def render_by_site(report: AuditReport, source: tuple[str, str], key: str) -> None:
    """source: file name and text of the audited input."""
    chosen_source, shown = render_head(report, key)
    name, text = source
    total_lines = len(text.splitlines())
    sites = group_sites(shown, split_sections(name, text))
    selected = selected_of(report.findings, shown, key)  # before a click the table's first row
    render_group(MULTI, sites.multi, selected, key)
    count = len(sites.placed)
    noun = "Fundstelle" if count == 1 else "Fundstellen"
    st.markdown(f"#### Geprüftes Dokument · {count} {noun}", help=HELP["document"])
    st.caption(f"`{name}` · {total_lines} Zeilen · {LEGEND}")
    with st.container(border=True, key=f"{key}_site_document"):  # frame: only the document
        _render_document(sites, text, selected, key)
    render_group(WITHOUT, sites.without_lines, selected, key)
    render_gaps(report, chosen_source, key)


def _closed_key(key: str) -> str:
    return f"{key}_site_closed"


def _render_document(sites: Sites, text: str, selected: Finding, key: str) -> None:
    closed = st.session_state.get(_closed_key(key)) == selected.rule_id
    state = f"{key}_sites"

    def site_clicked() -> None:  # the bar or a line: the first finding of the site, by lines
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
