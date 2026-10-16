"""Pages and sidebar of the demo UI: brand above the page links, as in the design (#11, #41).

The start page lives in app.py, so start_page can link to the other pages without a cycle.
"""

import base64

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from govguard_ui import create_page, gallery_page

SHIELD = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
          'fill="none" stroke="#0B4F8A" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round">'
          '<path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5z"/>'
          '<path d="m8.5 12 2.5 2.5 4.5-5"/></svg>')
# st.html drops an inline <svg>, an image keeps it
LOGO = "data:image/svg+xml;base64," + base64.b64encode(SHIELD.encode()).decode()
BRAND = (f'<div class="gg-brand"><img src="{LOGO}" alt=""><div><b>GovGuard</b>'
         '<span>Compliance Copilot</span></div></div>')


def audits_page() -> StreamlitPage:
    return st.Page(gallery_page.render, title="Audits ansehen", url_path="audits")


def create_audit_page() -> StreamlitPage:
    return st.Page(create_page.render, title="Audit erstellen", url_path="erstellen")


def sidebar(pages: list[StreamlitPage]) -> None:
    """Brand, one link per page, demo note; replaces Streamlit's own navigation."""
    with st.sidebar:
        st.html(BRAND)
        for page in pages:
            st.page_link(page)
        st.space("small")  # air above the note, as in the design
        st.caption("Demo-Stand · nur fiktive Daten")
