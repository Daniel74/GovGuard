"""Smoke tests of the page "Audit erstellen", headless via AppTest (#11, #41)."""

from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from pydantic_ai.models.function import FunctionModel
from streamlit.delta_generator import DeltaGenerator
from streamlit.proto.SelectWidgetFilterMode_pb2 import FILTER_MODE_NONE
from test_run_audit_progress import warn_for_every_rule
from ui_helpers import (
    DATA_WARNING,
    create_page,
    create_script,
    frames,
    gallery_script,
    open_text_tab,
    page,
    shown_text,
    start,
)

from govguard.audit_engine import MAX_INPUT_CHARS, AuditValidationError, with_thousand_dots
from govguard_ui.screens import create_page as create_module
from govguard_ui.screens.create_page import STAY_NOTE


def test_create_page_without_the_password_starts_no_audit() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    app.text_input(key="password").input("falsch")
    app.button(key="start").click().run()

    assert not app.exception
    assert DATA_WARNING in shown_text(app)
    assert "(USA)" not in shown_text(app)  # no data flow note: everything runs in the USA
    assert "Passwort falsch" in shown_text(app)
    assert "created" not in app.session_state


def test_create_page_shows_the_input_limit_and_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    app = open_text_tab(create_page())

    assert f"0 / {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen" in shown_text(app)
    assert "openai/gpt-oss-20b" in app.radio(key="model").options[0]


def test_create_page_puts_each_step_in_its_own_frame() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    steps = frames(app)

    assert [s.split("\n")[0] for s in steps] == [
        "#### 1 · Audit-Art", "#### 2 · Eingabe", "#### 3 · Modell", "#### 4 · Starten"]
    assert "Musterfall (fiktive Beispiel-Eingabe mit Soll-Ergebnis)" in steps[1]
    assert "Datenfluss" not in steps[2]
    assert "Passwort" in steps[3] and "Audit starten" in steps[3]


def test_create_page_names_norms_and_formats_of_each_audit_type() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    assert app.radio(key="audit_type").options == [
        "**Spezifikation** · DSGVO, KI-VO, SDM · Markdown oder OpenAPI",
        "**Architektur** · BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP · CloudFormation-JSON, "
        "Terraform oder Freitext",
    ]


def test_the_preset_tab_names_file_format_size_and_expected_status() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    assert [tab.label for tab in app.tabs] == ["Musterfall laden", "Text einfügen"]
    assert "input.md · Markdown · 3.996 Zeichen · Soll: Verstoß belegt" in shown_text(app)


def test_bedrock_is_shown_as_a_model_that_is_not_available_in_the_ui() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    bedrock = app.radio(key="model_bedrock")
    assert bedrock.disabled and bedrock.value is None
    assert bedrock.options == ["Claude Haiku über AWS Bedrock (EU)"]


def test_the_gallery_choice_is_a_frame_with_a_heading_like_a_step() -> None:
    app = page(gallery_script)

    choice = app.selectbox(key="gallery_preset")
    assert "#### Gespeichertes Audit aus der Galerie" in [f.split("\n")[0] for f in frames(app)]
    assert choice.proto.label_visibility.value == choice.proto.label_visibility.COLLAPSED


def test_the_preset_choice_on_both_pages_takes_no_typing() -> None:
    gallery = page(gallery_script)
    create = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    choices = [gallery.selectbox(key="gallery_preset"),
               create.selectbox(key="create_preset_spec")]

    assert [c.proto.filter_mode for c in choices] == [FILTER_MODE_NONE] * 2


def test_create_page_refuses_a_backend_other_than_local() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="lambda")

    assert "#38" in shown_text(app)
    assert not app.button


def test_with_the_password_the_audit_runs_and_stays_only_in_the_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr("govguard_ui.screens.create_page.groq_model",
                        lambda: FunctionModel(warn_for_every_rule, model_name="fake-groq"))
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    app.text_input(key="password").input("geheim")
    app.button(key="start").click().run()

    assert not app.exception
    report = app.session_state["created"]["report"]
    assert (report.audit_type, report.model_id) == ("spec", "fake-groq")
    assert "Audit fertig" in shown_text(app)
    assert "Soll-Abweichung" in shown_text(app)  # all WARN: the preset expects FAIL


def failing_audit(monkeypatch: pytest.MonkeyPatch, calls: list[str]) -> None:
    """The audit fails at once: the page keeps bar, note and error, no rerun hides them."""
    def run(*_args) -> None:
        calls.append("audit")
        raise AuditValidationError([], api_error=True)

    monkeypatch.setattr("govguard_ui.screens.create_page.groq_model", lambda: None)
    monkeypatch.setattr("govguard_ui.screens.create_page.run_local", run)


def test_while_the_audit_runs_a_note_asks_to_stay_on_the_page(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    failing_audit(monkeypatch, [])

    app = start(create_page())

    assert "Audit fehlgeschlagen" in shown_text(app)
    assert STAY_NOTE in shown_text(app)


def test_the_navigation_guard_watches_only_while_the_audit_runs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    failing_audit(monkeypatch, calls)
    guard = create_module.guard_navigation

    @contextmanager
    def noted_guard(slot: DeltaGenerator) -> Iterator[None]:
        calls.append("guard")
        with guard(slot):
            yield

    monkeypatch.setattr("govguard_ui.screens.create_page.guard_navigation", noted_guard)

    app = start(create_page())

    assert calls == ["guard", "audit"]
    assert not app.get("bidi_component")  # gone after the run: links switch freely again
