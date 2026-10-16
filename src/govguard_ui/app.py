"""Streamlit entry point: page set-up and navigation only, no logic (#11)."""

import streamlit as st

from govguard_ui import create_page, gallery_page, start_page


def main() -> None:
    st.set_page_config(page_title="GovGuard", page_icon="🛡️", layout="wide")
    pages = [
        st.Page(start_page.render, title="Start & Hilfe", default=True),  # served at /
        st.Page(gallery_page.render, title="Audits ansehen", url_path="audits"),
        st.Page(create_page.render, title="Audit erstellen", url_path="erstellen"),
    ]
    with st.sidebar:
        st.markdown("**GovGuard**  \nCompliance Copilot")
        st.caption("Demo-Stand · nur fiktive Daten")
    st.navigation(pages).run()
