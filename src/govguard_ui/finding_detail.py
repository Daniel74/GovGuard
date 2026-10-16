"""Selected finding and the audited document with its evidence lines marked (#11)."""

import html

import streamlit as st

from govguard.models import Finding
from govguard_ui.findings_view import lines_text
from govguard_ui.review import category, document_window
from govguard_ui.style import LOOKS, badge, paragraph, tag


def render_detail(finding: Finding) -> None:
    kind = category(finding)
    tags = [LOOKS[kind].word]
    if finding.downgraded_from:
        tags.append(f"↓ herabgestuft von {finding.downgraded_from}")
    if kind == "GAP":
        tags.append("kein Verstoß")  # CONTEXT: Lücke, never "nicht entscheidbar"
    with st.container(border=True):
        st.html(badge(kind) + "".join(tag(t) for t in tags))
        st.markdown(f"#### {finding.title}")
        evidence = "keine Zeilen" if finding.line_start is None else f"Zeilen {lines_text(finding)}"
        st.caption(f"{finding.primary_anchor} · {finding.rule_id} · Beleg: {evidence}")
        st.markdown("**Begründung**")
        st.html(paragraph(finding.rationale))
        if finding.recommendation:
            st.markdown("**Empfehlung**")
            st.html(paragraph(finding.recommendation))
        if finding.corrections:
            st.markdown("**Korrekturen** (Eingriffe des Codes in die KI-Antwort)")
            st.html("<ul>" + "".join(
                f"<li>{html.escape(c.removeprefix(f'{finding.rule_id}: '))}</li>"
                for c in finding.corrections) + "</ul>")
        if finding.cross_references:
            st.markdown("**Querverweise** (Vorschlag der KI, ohne Einfluss auf den Status)")
            st.caption(" · ".join(ref.anchor for ref in finding.cross_references))


def render_document(source_name: str, source_text: str, finding: Finding, key: str) -> None:
    st.markdown(f"**Geprüftes Dokument** · `{source_name}` · "
                f"{len(source_text.splitlines())} Zeilen")
    full = st.toggle("Ganzes Dokument", key=f"{key}_full")
    window = document_window(source_text, finding, full)
    if finding.line_start is None:
        st.info("Kein Beleg: Zu dieser Prüfregel nennt der Befund keine Stelle im Dokument.")
    if window.hidden_above:
        st.caption(f"▲ Zeilen 1–{window.hidden_above} ausgeblendet (Belegzeilen stehen oben)")
    lines = "".join(
        f'<div class="gg-line{" gg-mark" if line.marked else ""}"><span class="n">{line.number}'
        f"</span><span>{html.escape(line.text) or ' '}</span></div>" for line in window.lines)
    with st.container(height=560, border=True):
        st.html(f'<div class="gg-doc">{lines}</div>')
