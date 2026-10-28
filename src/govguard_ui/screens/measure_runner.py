"""Maßnahme vorschlagen for the report view: password, dialog and model call (#82). The report
view only shows (ADR 0027); this module is the hook a page hands it. The model is called only
after a click, and only with the right password, which holds once per session (ADR 0023)."""

import asyncio

import streamlit as st

from govguard.adapters.groq_services import (
    DEFAULT_MODEL,
    MissingApiKeyError,
    groq_model,
    model_name,
)
from govguard.calls.remediation import suggest_measures
from govguard.checks.sites import Site
from govguard_ui.report.remediation_data import document_digest, notice, suggestion_key
from govguard_ui.report.remediation_view import Proposer, proposals
from govguard_ui.screens.password_gate import (
    configured,
    confirm,
    confirmed,
    password_problem,
    secret,
)

NO_KEY = "Maßnahme vorschlagen ist nicht eingerichtet: GROQ_API_KEY fehlt in den Secrets."
REFUSED = {"missing": "Maßnahme vorschlagen ist nicht eingerichtet: Das Passwort fehlt in den "
                      "Secrets.",
           "wrong": "Passwort falsch. Ohne Passwort kein Vorschlag."}
DEFAULT_LABEL = "GPT-OSS 120B"  # the default model, written as people read it


def _notice() -> str:
    name = model_name()
    return notice(DEFAULT_LABEL if name == DEFAULT_MODEL else name)


def proposer() -> Proposer:
    """The hook of the pages for render_report."""
    return Proposer(run=run, unlocked=confirmed, notice=_notice())


def run(site: Site, text: str, key: str) -> None:
    """A proposal was asked for: at once if the session gave the password, else the dialog asks.
    Both end in a rerun that draws the block in the site's box."""
    if not confirmed():
        _dialog(site, text, key)
    elif not configured(secret("APP_PASSWORD")):  # fail closed, the flag alone does not open it
        st.error(REFUSED["missing"])
    elif _suggest(site, text, key):
        st.rerun()


@st.dialog("Maßnahme vorschlagen")
def _dialog(site: Site, text: str, key: str) -> None:
    password_form(site, text, key)


def password_form(site: Site, text: str, key: str) -> None:
    """Notice, password and button. The right password confirms the session and asks the model."""
    st.markdown(_notice())
    password = st.text_input("Passwort", type="password", key=f"{key}_measure_password")
    if not st.button("Vorschlagen", type="primary", key=f"{key}_measure_go"):
        return
    if problem := password_problem(password, secret("APP_PASSWORD")):
        st.error(REFUSED[problem])
        return
    confirm()  # one password for every LLM call of the session (ADR 0023)
    if _suggest(site, text, key):
        st.rerun()  # closes the dialog; the box shows the block


def _suggest(site: Site, text: str, key: str) -> bool:
    """Asks the model and keeps the answer; False when it could not even be asked."""
    try:
        model = groq_model()
    except MissingApiKeyError:
        st.error(NO_KEY)
        return False
    with st.spinner("Das Sprachmodell schlägt Maßnahmen vor …"):
        measures = asyncio.run(suggest_measures(site, text, model))
    proposals(key)[suggestion_key(site, document_digest(text))] = measures
    return True
