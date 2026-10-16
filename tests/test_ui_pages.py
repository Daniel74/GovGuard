"""Smoke tests of the Streamlit pages, headless via AppTest (#11). Layout is checked by hand."""

import pytest
from pydantic_ai.models.function import FunctionModel
from streamlit.testing.v1 import AppTest
from test_run_audit_progress import warn_for_every_rule

DATA_WARNING = ("Keine echten oder personenbezogenen Daten eingeben. "
                "Eingaben gehen zur Inferenz an Groq in die USA.")


def start_script() -> None:
    from govguard_ui.start_page import render
    render()


def gallery_script() -> None:
    from govguard_ui.gallery_page import render
    render()


def create_script() -> None:
    from govguard_ui.create_page import render
    render()


def page(script, **secrets: str) -> AppTest:
    app = AppTest.from_function(script, default_timeout=30)
    for name, value in secrets.items():
        app.secrets[name] = value
    return app.run()


def shown_text(app: AppTest) -> str:
    """Headings, markdown, captions, alerts and raw HTML of the page in one string."""
    parts = [*app.title, *app.header, *app.subheader, *app.markdown, *app.caption,
             *app.warning, *app.error, *app.info, *app.success]
    html = [node.proto.body for node in app.get("html")]
    return "\n".join([str(part.value) for part in parts] + html)


def test_start_page_warns_about_data_and_explains_the_report() -> None:
    app = page(start_script)

    assert not app.exception
    assert DATA_WARNING in shown_text(app)
    assert "So lesen Sie einen Audit-Report" in shown_text(app)


def test_gallery_shows_the_first_preset_with_its_source_and_expected_result() -> None:
    app = page(gallery_script)

    assert not app.exception
    text = shown_text(app)
    assert "Online-Anmeldung zur Schuleingangsuntersuchung" in text
    assert "Soll-Abgleich: wie erwartet" in text
    assert "input.md" in text


def test_gallery_shows_the_deviation_of_the_arch_preset() -> None:
    app = page(gallery_script)

    app.selectbox(key="gallery_preset").select("arch-antragseingang-fehlerhaft").run()

    assert not app.exception
    assert "BSI GS++ BER.4.1: Soll FAIL, Ist PASS" in [b.label for b in app.button]


def test_create_page_without_the_password_starts_no_audit() -> None:
    app = page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")

    app.text_input(key="password").input("falsch")
    app.button(key="start").click().run()

    assert not app.exception
    assert DATA_WARNING in shown_text(app)
    assert "Passwort falsch" in shown_text(app)
    assert "created" not in app.session_state


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


def test_the_app_opens_on_start_and_help() -> None:
    app = AppTest.from_file("../streamlit_app.py", default_timeout=30).run()

    assert not app.exception
    assert DATA_WARNING in shown_text(app)
