"""Page "Audits ansehen": stored reports of the presets from the repo (ADR 0023, #11)."""

import streamlit as st

from govguard_ui.gallery import GalleryEntry, load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report.report_view import render_report
from govguard_ui.style import CSS
from govguard_ui.texts import TYPE_LABELS


@st.cache_data
def _gallery() -> list[GalleryEntry]:
    return load_gallery(PRESETS, GALLERY)


def render() -> None:
    st.html(CSS)
    st.title("Audits ansehen")
    entries = {entry.preset_id: entry for entry in _gallery()}
    with st.container(border=True):  # a frame with a heading, like a step on "Audit erstellen"
        st.markdown("#### Gespeichertes Audit aus der Galerie")
        preset_id = st.selectbox(  # full width: the longest title is not cut off
            "Gespeichertes Audit aus der Galerie", list(entries), key="gallery_preset",
            filter_mode=None, label_visibility="collapsed",  # a choice, no typing (#41)
            format_func=lambda i: f"{entries[i].preset.title} "
                                  f"({TYPE_LABELS[entries[i].preset.audit_type].split(' ')[0]})")
    entry = entries[preset_id]
    if entry.report is None:
        st.info("Zu diesem Musterfall liegt noch kein Report in der Galerie. Sie wächst nur per "
                "Commit; unter „Audit erstellen“ können Sie den Musterfall selbst prüfen.")
        return
    render_report(entry.report, entry.preset.title, (entry.source_name, entry.source_text),
                  entry.preset.expected, key=f"gallery_{preset_id}")
