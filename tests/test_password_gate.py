"""One password for every LLM call from the UI, asked once per session (ADR 0023, #82)."""

import pytest
from ui_helpers import create_page, fake_groq, shown_text, start

from govguard_ui.screens.audit_runner import start_problem
from govguard_ui.screens.password_gate import configured, password_problem

SECRET = "korrekt-pferd"


def test_the_right_password_passes() -> None:
    assert password_problem(SECRET, SECRET) is None


@pytest.mark.parametrize("password", ["", "falsch", "korrekt-pferd "])
def test_any_other_password_is_wrong(password: str) -> None:
    assert password_problem(password, SECRET) == "wrong"


@pytest.mark.parametrize("secret", [None, ""])
def test_without_a_configured_password_nobody_passes_fail_closed(secret: str | None) -> None:
    assert password_problem("", secret) == "missing"
    assert password_problem("x", secret) == "missing"


@pytest.mark.parametrize(("secret", "expected"), [("x", True), ("", False), (None, False)])
def test_a_password_is_configured_only_if_it_is_not_empty(
    secret: str | None, expected: bool,
) -> None:
    assert configured(secret) is expected


def test_a_confirmed_session_starts_the_audit_without_typing_the_password() -> None:
    assert start_problem("Text", password="", secret=SECRET, confirmed=True) is None


def test_a_confirmed_session_does_not_open_the_door_without_a_configured_password() -> None:
    assert "nicht eingerichtet" in start_problem("Text", "", secret=None, confirmed=True)


def test_the_right_password_on_audit_erstellen_confirms_the_session(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_groq(monkeypatch, [])
    app = create_page()

    start(app)

    assert app.session_state["password_confirmed"] is True


def test_a_wrong_password_does_not_confirm_the_session() -> None:
    app = create_page()
    app.text_input(key="password").input("falsch")
    app.button(key="start").click().run()

    assert "password_confirmed" not in app.session_state


def test_a_confirmed_session_is_not_asked_again_on_audit_erstellen(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_groq(monkeypatch, [])
    app = create_page()
    app.session_state["password_confirmed"] = True
    app.run()

    assert not app.text_input
    assert "Passwort bestätigt" in shown_text(app)
    app.button(key="start").click().run()
    assert "Audit fertig" in shown_text(app)
