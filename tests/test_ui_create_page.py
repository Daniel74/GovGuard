"""Smoke tests of the page "Audit erstellen", headless via AppTest (#11, #41)."""

import pytest
from pydantic_ai.models.function import FunctionModel
from streamlit.proto.SelectWidgetFilterMode_pb2 import FILTER_MODE_NONE
from streamlit.testing.v1 import AppTest
from test_run_audit_progress import warn_for_every_rule
from test_ui_pages import DATA_WARNING, create_script, gallery_script, page, shown_text

from govguard.audit_engine import MAX_INPUT_CHARS, with_thousand_dots


def test_create_page_without_the_password_starts_no_audit() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    app.text_input(key="password").input("falsch")
    app.button(key="start").click().run()

    assert not app.exception
    assert DATA_WARNING in shown_text(app)
    assert "Passwort falsch" in shown_text(app)
    assert "created" not in app.session_state


def test_create_page_shows_the_input_limit_and_the_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    app.session_state["input_mode"] = "Text einfügen"  # the second tab
    app.run()

    assert f"0 / {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen" in shown_text(app)
    assert "openai/gpt-oss-20b" in app.radio(key="model").options[0]


def frames(app: AppTest) -> list[str]:
    """Text and widget labels of every bordered container, one string per container."""
    def text(node) -> str:
        return getattr(node.proto, "label", "") or getattr(node.proto, "body", "")

    bordered = [node for node in app.main if node.type == "flex_container"
                and node.proto.flex_container.border]
    return ["\n".join(text(n) for n in frame if n is not frame) for frame in bordered]


def test_create_page_puts_each_step_in_its_own_frame() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    steps = frames(app)

    assert [s.split("\n")[0] for s in steps] == [
        "#### 1 · Audit-Art", "#### 2 · Eingabe", "#### 3 · Modell", "#### 4 · Starten"]
    assert "Preset (fiktive Beispiel-Eingabe mit Soll-Ergebnis)" in steps[1]
    assert "Datenfluss" in steps[2]
    assert "Passwort" in steps[3] and "Audit starten" in steps[3]


def test_create_page_names_norms_and_formats_of_each_audit_type() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    assert app.radio(key="audit_type").options == [
        "**Spezifikation** · DSGVO, SDM · Markdown oder OpenAPI",
        "**Architektur** · BSI IT-Grundschutz, BSI C5, CIS, AWS FSBP · CloudFormation-JSON, "
        "Terraform oder Freitext",
    ]


def test_the_preset_tab_names_file_format_size_and_expected_status() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    assert [tab.label for tab in app.tabs] == ["Preset laden", "Text einfügen"]
    assert "input.md · Markdown · 3.996 Zeichen · Soll: FAIL" in shown_text(app)


def test_bedrock_is_shown_as_a_model_that_is_not_available_in_the_ui() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    bedrock = app.radio(key="model_bedrock")
    assert bedrock.disabled and bedrock.value is None
    assert "Claude Haiku über AWS Bedrock (EU)" in bedrock.options[0]
    assert "nur per CLI" in bedrock.options[0]


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
    monkeypatch.setattr("govguard_ui.create_page.groq_model",
                        lambda: FunctionModel(warn_for_every_rule, model_name="fake-groq"))
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    app.text_input(key="password").input("geheim")
    app.button(key="start").click().run()

    assert not app.exception
    report = app.session_state["created"]["report"]
    assert (report.audit_type, report.model_id) == ("spec", "fake-groq")
    assert "Audit fertig" in shown_text(app)
    assert "Soll-Abweichung" in shown_text(app)  # all WARN: the preset expects FAIL
