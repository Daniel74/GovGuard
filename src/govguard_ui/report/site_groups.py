"""Findings of "nach Fundstelle" that have no bar: over the whole document above the document,
without lines below it. Each group is a section like the gaps, its findings listed in full (#81)."""

import html
from typing import NamedTuple

import streamlit as st

from govguard.models import Finding
from govguard_ui.report.ai_label import ai_label
from govguard_ui.report.review import category
from govguard_ui.report.site_data import place
from govguard_ui.style import badge
from govguard_ui.texts import HELP


class GroupTexts(NamedTuple):
    heading: str
    help: str
    label: str  # of the expander, after the count


WHOLE = GroupTexts("Betrifft das ganze Dokument", HELP["whole_document"],
                   "Befunde mit mehr als der Hälfte des Dokuments als Beleg")
WITHOUT = GroupTexts("Ohne Zeilen", HELP["without_lines"], "Befunde ohne Zeilen im Dokument")


def render_group(texts: GroupTexts, findings: list[Finding], selected: Finding, key: str) -> None:
    """key: state key of the expander; open while it holds the selected finding."""
    if not findings:
        return
    st.markdown(f"#### {texts.heading} · {len(findings)}", help=texts.help)
    with st.expander(f"{len(findings)} {texts.label}", expanded=selected in findings, key=key):
        for finding in findings:
            _finding(finding)


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
    st.html('<div style="display:flex;flex-direction:column;gap:4px;padding:8px 0;'
            'border-bottom:1px solid #E3E7EC">' + "".join(parts) + "</div>")
