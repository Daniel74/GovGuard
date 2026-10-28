"""Page "Audit erstellen": password, progress, result only in the session (ADR 0023, #11)."""

import time
from pathlib import Path

import streamlit as st
from streamlit.delta_generator import DeltaGenerator

from govguard.adapters.groq_services import MissingApiKeyError, groq_model, model_name
from govguard.audit_engine import MAX_INPUT_CHARS, AuditValidationError, with_thousand_dots
from govguard.audit_setup import failure_text
from govguard.models import AuditType, Expected
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report.remediation_view import forget_proposals
from govguard_ui.report.report_view import render_report
from govguard_ui.screens.audit_runner import (
    backend_problem,
    progress_view,
    run_local,
    start_problem,
)
from govguard_ui.screens.measure_runner import proposer
from govguard_ui.screens.navigation_guard import guard_navigation
from govguard_ui.screens.password_gate import confirm, confirmed, secret
from govguard_ui.style import CSS, status_word
from govguard_ui.texts import DATA_RULE, TYPE_CHOICES

FORMATS = {".md": "Markdown", ".yaml": "YAML", ".json": "JSON"}  # by file suffix of the preset
STAY_NOTE = "Bitte während des Audits auf dieser Seite bleiben."  # a page switch stops it (#77)


def render() -> None:
    st.html(CSS)
    st.title("Audit erstellen")
    st.warning(f"**{DATA_RULE}**", icon=":material/warning:")
    guard_slot = st.empty()  # same place in every run, see guard_navigation
    if problem := backend_problem(secret("AUDIT_BACKEND")):
        st.error(problem)
        return
    if created := st.session_state.get("created"):
        _result(created)
        return
    audit_type, title, source, expected = _input_form()
    with st.container(border=True):
        st.markdown("#### 4 · Starten")
        password = _password_field()
        if st.button("Audit starten", type="primary", key="start"):
            if problem := start_problem(source[1], password, secret("APP_PASSWORD"), confirmed()):
                st.error(problem)
            else:
                confirm()  # one password for every LLM call of the session (#82)
                _run(audit_type, title, source, expected, guard_slot)


def _password_field() -> str:
    """Asked once per session: after the right password (here or for a measure) only a note."""
    if confirmed():
        st.caption("Passwort bestätigt, es gilt für diese Sitzung.")
        return ""
    password = st.text_input("Passwort", type="password", key="password", width=360)
    st.caption("Schützt vor Kosten durch Fremde. Das Passwort erhalten Sie vom Betreiber der "
               "Demo.")
    return password


def _input_form() -> tuple[AuditType, str, tuple[str, str], Expected | None]:
    """Steps 1 to 3, each in a frame: audit type, input, model (#41)."""
    with st.container(border=True):
        st.markdown("#### 1 · Audit-Art")
        audit_type = st.radio("Audit-Art", ["spec", "architecture"],
                              format_func=TYPE_CHOICES.get, key="audit_type",
                              label_visibility="collapsed")
    with st.container(border=True):
        st.markdown("#### 2 · Eingabe")
        title, source, expected = _source(audit_type)
    with st.container(border=True):
        st.markdown("#### 3 · Modell")
        # display only, never read: Groq is the only model in the UI (ADR 0023)
        st.radio("Modell", [f"**Groq · {model_name()}** · ca. 2–3 Cent je Audit, 20–60 s"],
                 key="model", label_visibility="collapsed")
        st.radio("Nicht verfügbar", ["Claude Haiku über AWS Bedrock (EU)"],  # CLI only, ADR 0023
                 index=None, disabled=True, key="model_bedrock", label_visibility="collapsed")
    return audit_type, title, source, expected


def _source(audit_type: AuditType) -> tuple[str, tuple[str, str], Expected | None]:
    """Title, (file name, text) of the input and the preset's expected result."""
    preset_tab, text_tab = st.tabs(["Musterfall laden", "Text einfügen"], key="input_mode",
                                   on_change="rerun")  # only the open tab runs its input
    if preset_tab.open:
        with preset_tab:
            return _preset(audit_type)
    with text_tab:
        text = st.text_area("Spezifikation oder Architektur (fiktiv)", height=260, key="text",
                            placeholder="Hier die fiktive Spezifikation oder Architektur "
                                        "einfügen …")
        limit = with_thousand_dots(MAX_INPUT_CHARS)
        st.caption(f"{with_thousand_dots(len(text))} / {limit} Zeichen")
    return "Eigene Eingabe", ("Eingabe", text), None


def _preset(audit_type: AuditType) -> tuple[str, tuple[str, str], Expected | None]:
    presets = {e.preset_id: e for e in load_gallery(PRESETS, GALLERY)
               if e.preset.audit_type == audit_type}
    chosen = presets[st.selectbox("Musterfall (fiktive Beispiel-Eingabe mit Soll-Ergebnis)",
                                  list(presets), format_func=lambda i: presets[i].preset.title,
                                  key=f"create_preset_{audit_type}",
                                  filter_mode=None)]  # a choice, no typing (#41)
    size = with_thousand_dots(len(chosen.source_text))
    file_format = FORMATS.get(Path(chosen.source_name).suffix, "Text")
    st.caption(f"{chosen.source_name} · {file_format} · {size} Zeichen · "
               f"Soll: {status_word(chosen.preset.expected.overall_status)}")
    return chosen.preset.title, (chosen.source_name, chosen.source_text), chosen.preset.expected


def _run(
    audit_type: AuditType, title: str, source: tuple[str, str], expected: Expected | None,
    guard_slot: DeltaGenerator,
) -> None:
    bar = st.progress(0.0, text="Audit startet …")
    st.caption(STAY_NOTE)
    started = time.monotonic()
    try:
        with guard_navigation(guard_slot):
            report = run_local(audit_type, source[1], groq_model(),
                               lambda progress: bar.progress(*progress_view(progress)))
    except MissingApiKeyError:
        st.error("Audit erstellen ist nicht eingerichtet: GROQ_API_KEY fehlt in den Secrets.")
        return
    except AuditValidationError as error:  # fail closed, no partial report
        st.error(failure_text(error))
        return
    forget_proposals("created")  # a proposal belongs to the audit it saw
    st.session_state["created"] = {"report": report, "title": title, "source": source,
                                   "expected": expected,
                                   "seconds": round(time.monotonic() - started)}
    st.rerun()


def _result(created: dict) -> None:
    st.success(f"Audit fertig nach {created['seconds']} s. Der Report liegt nur in dieser "
               "Sitzung; laden Sie ihn herunter, wenn Sie ihn behalten möchten.")
    if st.button("Neues Audit", key="new_audit"):
        del st.session_state["created"]
        forget_proposals("created")
        st.rerun()
    render_report(created["report"], created["title"], created["source"], created["expected"],
                  key="created", propose=proposer())
