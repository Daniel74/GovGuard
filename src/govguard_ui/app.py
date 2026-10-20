"""Streamlit entry point: page set-up and navigation only, no logic (#11)."""

import streamlit as st

from govguard_ui import navigation


def main() -> None:
    st.set_page_config(page_title="GovGuard", page_icon="🛡️", layout="wide")
    pages = navigation.pages()
    current = st.navigation(pages, position="hidden")
    navigation.sidebar(pages)
    current.run()
