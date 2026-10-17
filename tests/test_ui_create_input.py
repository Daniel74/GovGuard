"""Input of "Audit erstellen": audit type, preset and own text, via AppTest (#44)."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel
from streamlit.testing.v1 import AppTest
from test_run_audit_progress import warn_for_every_rule
from test_ui_pages import create_script, page, shown_text

from govguard.audit_engine import MAX_INPUT_CHARS, with_thousand_dots


def create_page() -> AppTest:
    return page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")


def text_tab(app: AppTest, text: str | None = None) -> AppTest:
    """Opens the second tab; AppTest forgets the open tab on a rerun, so every run sets it."""
    if text is not None:
        app.text_area(key="text").input(text)
    app.session_state["input_mode"] = "Text einfügen"
    return app.run()


def test_the_audit_type_decides_which_presets_can_be_chosen() -> None:
    app = create_page()
    assert app.selectbox(key="create_preset_spec").value == "spec-meldeportal-gesundheit"

    app.radio(key="audit_type").set_value("architecture").run()

    assert not app.exception
    assert app.selectbox(key="create_preset_architecture").value == "arch-antragseingang-fehlerhaft"
    assert [s.key for s in app.selectbox if s.key.startswith("create_preset_")] == [
        "create_preset_architecture"]
    assert "template.json · JSON · 12.591 Zeichen · Soll: FAIL" in shown_text(app)


def test_another_preset_changes_file_format_size_and_expected_status() -> None:
    app = create_page()

    app.selectbox(key="create_preset_spec").select("spec-wohngeld-openapi").run()

    assert not app.exception
    assert "openapi.yaml · YAML · 83.210 Zeichen · Soll: WARN" in shown_text(app)
    assert "input.md" not in shown_text(app)


def test_a_preset_without_a_stored_report_can_still_be_chosen() -> None:
    app = create_page()
    app.radio(key="audit_type").set_value("architecture").run()

    app.selectbox(key="create_preset_architecture").select("arch-protokollarchiv").run()

    assert not app.exception
    assert "input.md · Markdown · 2.730 Zeichen · Soll: WARN" in shown_text(app)


def test_the_text_tab_counts_the_typed_characters_against_the_limit() -> None:
    app = text_tab(text_tab(create_page()), "Alle Zugriffe erfolgen über TLS 1.3.")

    assert f"36 / {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen" in shown_text(app)


def test_the_text_tab_hides_the_preset_choice() -> None:
    app = text_tab(create_page())

    assert not [s for s in app.selectbox if s.key.startswith("create_preset_")]
    assert app.text_area(key="text").placeholder.startswith("Hier die fiktive Spezifikation")


def start(app: AppTest, tab: str = "Preset laden") -> AppTest:
    """Types the password and starts; the open tab is set again for this rerun too."""
    app.text_input(key="password").input("geheim")
    app.button(key="start").click()
    app.session_state["input_mode"] = tab
    return app.run()


def fake_groq(monkeypatch: pytest.MonkeyPatch, seen: list[str]) -> None:
    """Groq replaced by a FunctionModel that notes what the audit sent to the model."""
    def answer(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(str(messages[0]))
        return warn_for_every_rule(messages, info)

    monkeypatch.setattr("govguard_ui.create_page.groq_model",
                        lambda: FunctionModel(answer, model_name="fake-groq"))


def test_an_audit_of_pasted_text_checks_exactly_this_text(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []
    fake_groq(monkeypatch, seen)
    app = text_tab(text_tab(create_page()), "Alle Zugriffe erfolgen ausschließlich über TLS 1.3.")

    start(app, "Text einfügen")

    assert not app.exception
    created = app.session_state["created"]
    assert created["title"] == "Eigene Eingabe"
    assert created["source"] == ("Eingabe", "Alle Zugriffe erfolgen ausschließlich über TLS 1.3.")
    assert created["expected"] is None
    assert "Alle Zugriffe erfolgen ausschließlich über TLS 1.3." in seen[0]
    assert "Soll-Abweichung" not in shown_text(app)  # a pasted text has no expected result


def test_an_audit_of_an_architecture_preset_runs_the_architecture_catalog(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_groq(monkeypatch, [])
    app = create_page()
    app.radio(key="audit_type").set_value("architecture").run()

    start(app)

    assert not app.exception
    created = app.session_state["created"]
    assert created["report"].audit_type == "architecture"
    assert created["source"][0] == "template.json"
    assert created["expected"].overall_status == "FAIL"


@pytest.mark.parametrize(("text", "message"), [
    ("   ", "Die Eingabe ist leer"),
    ("x" * (MAX_INPUT_CHARS + 1), "zu lang"),
])
def test_empty_or_too_long_text_starts_no_audit(
    monkeypatch: pytest.MonkeyPatch, text: str, message: str
) -> None:
    seen: list[str] = []
    fake_groq(monkeypatch, seen)
    app = text_tab(text_tab(create_page()), text)

    start(app, "Text einfügen")

    assert not app.exception
    assert message in shown_text(app)
    assert "created" not in app.session_state and seen == []  # no model call, no cost
