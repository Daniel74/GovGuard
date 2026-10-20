"""Pages and sidebar of the demo UI: brand above the page links, as in the design (#11, #41)."""

import base64

import streamlit as st
from streamlit.navigation.page import StreamlitPage

from govguard_ui.screens import create_page, gallery_page, start_page

SHIELD = ('<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" '
          'fill="none" stroke="#0B4F8A" stroke-width="2" stroke-linecap="round" '
          'stroke-linejoin="round">'
          '<path d="M12 2 4 5v6c0 5 3.4 9.3 8 11 4.6-1.7 8-6 8-11V5z"/>'
          '<path d="m8.5 12 2.5 2.5 4.5-5"/></svg>')
# st.html drops an inline <svg>, an image keeps it
LOGO = "data:image/svg+xml;base64," + base64.b64encode(SHIELD.encode()).decode()
REPO_URL = "https://github.com/Daniel74/GovGuard"
CONTACT_MAIL = "govguard@gmx.de"  # an own address for the project, not the private one
FOOTER = (f"[Quellcode auf GitHub]({REPO_URL})  \nLizenz: [MIT]({REPO_URL}/blob/main/LICENSE)  \n"
          f"Kontakt: [{CONTACT_MAIL}](mailto:{CONTACT_MAIL})")
# Attribution the licenses ask for where the rules are shown (CC BY-SA 4.0, dl-de/by-2-0)
CREDITS = f"""**Quellen der Prüfregeln**
- BSI IT-Grundschutz++: © BSI, [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/),
  verändert
- Standard-Datenschutzmodell (SDM): Datenschutzkonferenz,
  [Datenlizenz Deutschland – Namensnennung 2.0](https://www.govdata.de/dl-de/by-2-0), verändert
- DSGVO und KI-Verordnung: © Europäische Union, [EUR-Lex](https://eur-lex.europa.eu)
- CIS AWS Foundations Benchmark v7.0.0: © Center for Internet Security, Inc.
- BSI C5:2025 und AWS FSBP: Texte von BSI und Amazon Web Services
- Strukturdaten zu CIS, C5 und FSBP: [Prowler](https://github.com/prowler-cloud/prowler),
  Apache-2.0

Verändert heißt: Anforderungen extrahiert, gefiltert und zu Prüfregeln umformuliert. Alle
Vermerke stehen in [NOTICE]({REPO_URL}/blob/main/NOTICE).

**Werkzeuge**
- [Streamlit](https://streamlit.io), Apache-2.0
- [Pydantic](https://docs.pydantic.dev) und [Pydantic AI](https://ai.pydantic.dev), MIT
- Sprachmodelle über [Groq](https://groq.com); jeder Report nennt sein Modell"""
BRAND = (f'<div class="gg-brand"><img src="{LOGO}" alt=""><div><b>GovGuard</b>'
         '<span>Prüfassistent</span></div></div>')


def pages() -> list[StreamlitPage]:
    """All three pages, in the order of the sidebar."""
    return [home_page(), audits_page(), create_audit_page()]


def home_page() -> StreamlitPage:
    return st.Page(start_page.render, title="Start & Hilfe", default=True)  # served at /


def audits_page() -> StreamlitPage:
    return st.Page(gallery_page.render, title="Audits ansehen", url_path="audits")


def create_audit_page() -> StreamlitPage:
    return st.Page(create_page.render, title="Audit erstellen", url_path="erstellen")


def sidebar(entries: list[StreamlitPage]) -> None:
    """Brand, one link per page, demo note, credits, then source, license and contact;
    replaces Streamlit's own navigation."""
    with st.sidebar:
        st.html(BRAND)
        for page in entries:
            st.page_link(page)
        st.space("small")  # air above the note, as in the design
        st.caption("Demo-Stand · nur fiktive Daten")
        with st.popover("Credits", type="tertiary", icon=":material/info:"):
            st.markdown(CREDITS)
        st.caption(FOOTER)
