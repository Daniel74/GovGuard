"""Page "Audit erstellen": password, progress, result only in the session (ADR 0023, #11)."""

import os
import time

import streamlit as st

from govguard.audit_engine import AuditValidationError
from govguard.cli import failure_text
from govguard.groq_services import DEFAULT_MODEL, MissingApiKeyError, groq_model
from govguard.models import AuditType, Expected
from govguard_ui.audit_runner import backend_problem, progress_view, run_local, start_problem
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report_view import render_report
from govguard_ui.style import CSS
from govguard_ui.texts import DATA_WARNING, TYPE_LABELS

DATA_FLOW = ("Datenfluss: Eingabe → Streamlit Community Cloud (USA) → Groq (USA). Nichts wird "
             "gespeichert; der Report bleibt nur in dieser Sitzung.")


def secret(name: str) -> str | None:
    """Streamlit secrets first; Community Cloud also exports them as environment variables."""
    try:
        return st.secrets.get(name) or os.getenv(name)
    except FileNotFoundError:  # no secrets.toml, e.g. a local run
        return os.getenv(name)


def render() -> None:
    st.html(CSS)
    st.title("Audit erstellen")
    st.warning(f"**{DATA_WARNING}**", icon="⚠️")
    if problem := backend_problem(secret("AUDIT_BACKEND")):
        st.error(problem)
        return
    if created := st.session_state.get("created"):
        _result(created)
        return
    audit_type, title, source, expected = _input_form()
    password = st.text_input("Passwort", type="password", key="password",
                             help="Schützt vor Kosten durch Fremde. Das Passwort erhalten Sie "
                                  "vom Betreiber der Demo.")
    if st.button("Audit starten", type="primary", key="start"):
        if problem := start_problem(source[1], password, secret("APP_PASSWORD")):
            st.error(problem)
        else:
            _run(audit_type, title, source, expected)


def _input_form() -> tuple[AuditType, str, tuple[str, str], Expected | None]:
    """Audit type, title, (file name, text) of the input and the preset's expected result."""
    audit_type = st.radio("1 · Audit-Typ", ["spec", "architecture"], horizontal=True,
                          format_func=TYPE_LABELS.get, key="audit_type")
    mode = st.radio("2 · Eingabe", ["Preset laden", "Text einfügen"], horizontal=True,
                    key="input_mode")
    if mode == "Preset laden":
        presets = {e.preset_id: e for e in load_gallery(PRESETS, GALLERY)
                   if e.preset.audit_type == audit_type}
        chosen = presets[st.selectbox("Preset (fiktive Beispiel-Eingabe mit Soll-Ergebnis)",
                                      list(presets), format_func=lambda i: presets[i].preset.title,
                                      key=f"create_preset_{audit_type}")]
        st.caption(f"{chosen.source_name} · {len(chosen.source_text):,} Zeichen".replace(",", "."))
        source = (chosen.source_name, chosen.source_text)
        title, expected = chosen.preset.title, chosen.preset.expected
    else:
        text = st.text_area("Spezifikation oder Architektur (fiktiv)", height=260, key="text",
                            placeholder="Hier die fiktive Spezifikation oder Architektur "
                                        "einfügen …")
        st.caption(f"{len(text):,} / 100.000 Zeichen".replace(",", "."))
        source, title, expected = ("Eingabe", text), "Eigene Eingabe", None
    st.markdown(f"**3 · Modell:** Groq · `{os.getenv('GROQ_MODEL', DEFAULT_MODEL)}` · "
                "ca. 2–3 Cent je Audit, 20–60 s")
    st.caption(DATA_FLOW + " Claude Haiku über AWS Bedrock (EU) gibt es nur per CLI.")
    return audit_type, title, source, expected


def _run(
    audit_type: AuditType, title: str, source: tuple[str, str], expected: Expected | None
) -> None:
    bar = st.progress(0.0, text="Audit startet …")
    started = time.monotonic()
    try:
        report = run_local(audit_type, source[1], groq_model(),
                           lambda progress: bar.progress(*progress_view(progress)))
    except MissingApiKeyError:
        st.error("Audit erstellen ist nicht eingerichtet: GROQ_API_KEY fehlt in den Secrets.")
        return
    except AuditValidationError as error:  # fail closed, no partial report
        st.error(failure_text(error))
        return
    st.session_state["created"] = {"report": report, "title": title, "source": source,
                                   "expected": expected,
                                   "seconds": round(time.monotonic() - started)}
    st.rerun()


def _result(created: dict) -> None:
    st.success(f"Audit fertig nach {created['seconds']} s. Der Report liegt nur in dieser "
               "Sitzung; laden Sie ihn herunter, wenn Sie ihn behalten möchten.")
    if st.button("Neues Audit", key="new_audit"):
        del st.session_state["created"]
        st.rerun()
    render_report(created["report"], created["title"], created["source"], created["expected"],
                  key="created")
