"""The password for every LLM call from the UI (ADR 0023): checked fail closed and in constant
time, and asked once per session, for "Audit erstellen" and "Maßnahme vorschlagen" alike (#82).
A screen module: the report view only shows, a page hands it what asks the model."""

import hmac
import os
from typing import Literal

import streamlit as st

CONFIRMED = "password_confirmed"  # session flag: the right password was given once


def secret(name: str) -> str | None:
    """Streamlit secrets first; Community Cloud also exports them as environment variables."""
    try:
        return st.secrets.get(name) or os.getenv(name)
    except FileNotFoundError:  # no secrets.toml, e.g. a local run
        return os.getenv(name)


def configured(password: str | None) -> bool:
    """Fail closed: without a configured password no LLM call starts, whatever the session says."""
    return bool(password)


def password_problem(password: str, secret_value: str | None) -> Literal["missing", "wrong"] | None:
    """Why the call must not start, or None. Checked before any LLM call: no cost."""
    if not configured(secret_value):
        return "missing"
    if not hmac.compare_digest(password.encode(), (secret_value or "").encode()):  # constant time
        return "wrong"
    return None


def confirmed() -> bool:
    return st.session_state.get(CONFIRMED, False)


def confirm() -> None:
    st.session_state[CONFIRMED] = True
