"""Input of "Audit erstellen": audit type, preset and own text, via AppTest (#44)."""

import pytest
from ui_helpers import (
    create_page,
    fake_groq,
    open_text_tab,
    preset_boxes,
    shown_text,
    start,
    typed_text,
)

from govguard.audit_engine import MAX_INPUT_CHARS, with_thousand_dots


def test_the_audit_type_decides_which_presets_can_be_chosen() -> None:
    app = create_page()
    assert app.selectbox(key="create_preset_spec").value == "spec-meldeportal-gesundheit"

    app.radio(key="audit_type").set_value("architecture").run()

    assert not app.exception
    assert app.selectbox(key="create_preset_architecture").value == "arch-antragseingang-fehlerhaft"
    assert preset_boxes(app) == ["create_preset_architecture"]
    assert "template.json · JSON · 12.591 Zeichen · Soll: Verstoß belegt" in shown_text(app)


def test_another_preset_changes_file_format_size_and_expected_status() -> None:
    app = create_page()

    app.selectbox(key="create_preset_spec").select("spec-wohngeld-openapi").run()

    assert not app.exception
    assert "openapi.yaml · YAML · 21.926 Zeichen · Soll: Prüfbedarf" in shown_text(app)
    assert "input.md" not in shown_text(app)


def test_a_preset_without_a_stored_report_can_still_be_chosen() -> None:
    app = create_page()
    app.radio(key="audit_type").set_value("architecture").run()

    app.selectbox(key="create_preset_architecture").select("arch-protokollarchiv").run()

    assert not app.exception
    assert "input.md · Markdown · 2.730 Zeichen · Soll: Prüfbedarf" in shown_text(app)


def test_the_text_tab_counts_the_typed_characters_against_the_limit() -> None:
    app = typed_text("Alle Zugriffe erfolgen über TLS 1.3.")

    assert f"36 / {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen" in shown_text(app)


def test_the_text_tab_hides_the_preset_choice() -> None:
    app = open_text_tab(create_page())

    assert preset_boxes(app) == []
    assert app.text_area(key="text").placeholder.startswith("Hier die fiktive Spezifikation")


def test_an_audit_of_pasted_text_checks_exactly_this_text(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []
    fake_groq(monkeypatch, seen)
    app = typed_text("Alle Zugriffe erfolgen ausschließlich über TLS 1.3.")

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
    ("   ", "Bitte einen Text einfügen oder einen Musterfall wählen."),
    ("x" * (MAX_INPUT_CHARS + 1), "zu lang"),
])
def test_empty_or_too_long_text_starts_no_audit(
    monkeypatch: pytest.MonkeyPatch, text: str, message: str
) -> None:
    seen: list[str] = []
    fake_groq(monkeypatch, seen)
    app = typed_text(text)

    start(app, "Text einfügen")

    assert not app.exception
    assert message in shown_text(app)
    assert "created" not in app.session_state and seen == []  # no model call, no cost
