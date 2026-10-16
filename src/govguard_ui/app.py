"""Streamlit entry point: page set-up and navigation only, no logic (#11)."""

import streamlit as st

from govguard_ui import navigation, start_page


def main() -> None:
    st.set_page_config(page_title="GovGuard", page_icon="🛡️", layout="wide")
    pages = [
        st.Page(start_page.render, title="Start & Hilfe", default=True),  # served at /
        navigation.audits_page(),
        navigation.create_audit_page(),
    ]
    current = st.navigation(pages, position="hidden")
    navigation.sidebar(pages)
    current.run()
