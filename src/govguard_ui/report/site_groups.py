"""Findings of "nach Fundstelle" that have no bar: over several sections above the document,
without lines below it. Each group is a section like the gaps, its findings listed in full
(#81, #84)."""

import html
from typing import NamedTuple

import streamlit as st

from govguard.models import Finding
from govguard_ui.report.ai_label import ai_label
from govguard_ui.report.findings_view import select
from govguard_ui.report.review import category
from govguard_ui.report.site_data import place
from govguard_ui.style import badge
from govguard_ui.texts import HELP


class GroupTexts(NamedTuple):
    slug: str  # in the keys of the widgets of the group
    heading: str
    help: str
    label: str  # of the expander, after the count


MULTI = GroupTexts("multi", "Betrifft mehrere Abschnitte", HELP["multi_section"],
                   "Befunde mit Belegen aus mehreren Abschnitten")
WITHOUT = GroupTexts("without", "Ohne Zeilen", HELP["without_lines"],
                     "Befunde ohne Zeilen im Dokument")


def render_group(texts: GroupTexts, findings: list[Finding], selected: Finding, key: str) -> None:
    """key: of the report; the expander is open while it holds the selected finding."""
    if not findings:
        return
    st.markdown(f"#### {texts.heading} · {len(findings)}", help=texts.help)
    with st.expander(f"{len(findings)} {texts.label}", expanded=selected in findings,
                     key=f"{key}_{texts.slug}"):
        for finding in findings:
            _item(texts, finding, finding == selected, key)


def _item(texts: GroupTexts, finding: Finding, chosen: bool, key: str) -> None:
    """The finding in its block; one with lines has a button that selects it, since the group has
    no bar to click. The keyed container carries the mark of the chosen one (see style.py)."""
    mark = "sel_" if chosen else ""
    with st.container(key=f"{key}_{texts.slug}_item_{mark}{finding.rule_id}"):
        _finding(finding)
        if finding.line_start is not None:
            st.button("Zeilen im Dokument zeigen", type="tertiary", on_click=select,
                      args=(key, finding.rule_id), key=f"{key}_{texts.slug}_show_{finding.rule_id}")


def _text(label: str, text: str, by_code: bool) -> str:
    return f"<div>{ai_label(label, by_code)}: {html.escape(text)}</div>"


def _finding(finding: Finding) -> None:
    """Like the box under a site, in one block: status, rule, anchor and lines, why, then what.
    Twin of item() in site_script: the component draws in its own shadow root, a change of the
    layout goes to both."""
    parts = [f"<div>{badge(category(finding))} <strong>{html.escape(finding.title)}</strong></div>",
             f'<div style="color:#4A5361;font-size:14px">{html.escape(finding.primary_anchor)} · '
             f"{place(finding.line_start, finding.last_line)}</div>",
             _text("Begründung", finding.rationale, "rationale" in finding.by_code)]
    if finding.recommendation:
        code = "recommendation" in finding.by_code
        parts.append(_text("Empfehlung", finding.recommendation, code))
    st.html('<div style="display:flex;flex-direction:column;gap:4px;padding:8px 0">'
            + "".join(parts) + "</div>")
