"""A new audit inside one session: result, "Neues Audit" and the next audit, via AppTest (#44)."""

import pytest
from streamlit.testing.v1 import AppTest
from test_ui_create_input import create_page, fake_groq, start
from test_ui_pages import shown_text


def finished_audit(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    fake_groq(monkeypatch, [])
    app = create_page()
    start(app)
    return app


def test_a_finished_audit_replaces_the_form_and_offers_the_json_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = finished_audit(monkeypatch)

    assert not app.exception
    assert "Audit fertig" in shown_text(app)
    assert not app.text_input and not app.radio  # no form, no password field
    assert [b.proto.label for b in app.get("download_button")] == [
        "Report als JSON herunterladen"]


def test_new_audit_clears_the_result_and_shows_the_form_again(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = finished_audit(monkeypatch)

    app.button(key="new_audit").click().run()

    assert not app.exception
    assert "created" not in app.session_state
    assert "Audit fertig" not in shown_text(app)
    assert app.button(key="start").label == "Audit starten"
    assert app.text_input(key="password").value == ""
    assert not app.get("download_button")


def test_a_second_audit_in_the_same_session_shows_its_own_report(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app = finished_audit(monkeypatch)
    assert app.session_state["created"]["report"].audit_type == "spec"
    app.button(key="new_audit").click().run()

    app.radio(key="audit_type").set_value("architecture").run()
    start(app)

    assert not app.exception
    created = app.session_state["created"]
    assert created["report"].audit_type == "architecture"
    assert created["source"][0] == "template.json"
    assert "Audit fertig" in shown_text(app)
