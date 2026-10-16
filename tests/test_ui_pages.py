"""Smoke tests of the Streamlit pages, headless via AppTest (#11). Layout is checked by hand."""

import pytest
from pydantic_ai.models.function import FunctionModel
from streamlit.proto.SelectWidgetFilterMode_pb2 import FILTER_MODE_NONE
from streamlit.testing.v1 import AppTest
from test_run_audit_progress import warn_for_every_rule

from govguard.audit_engine import MAX_INPUT_CHARS, with_thousand_dots

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
    text = "\n".join([str(part.value) for part in parts] + html)
    return text.replace("**", "").replace("  \n", " ")  # as read, without markdown


def test_start_page_warns_about_data_and_explains_the_report() -> None:
    app = page(start_script)

    assert not app.exception
    assert DATA_WARNING in shown_text(app)
    assert "So lesen Sie einen Audit-Report" in shown_text(app)
    assert f"höchstens {with_thousand_dots(MAX_INPUT_CHARS)} Zeichen" in shown_text(app)


def test_the_start_page_explains_the_gallery_one_sentence_per_line() -> None:
    app = page(start_script)

    text = next(m.value for m in app.markdown if m.value.startswith("Die Galerie zeigt"))
    lines = text.split("  \n")  # markdown line break
    assert len(lines) == 4
    assert all(line.endswith(".") for line in lines)


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


def test_the_app_opens_on_start_and_help() -> None:
    app = AppTest.from_file("../streamlit_app.py", default_timeout=30).run()

    assert not app.exception
    assert DATA_WARNING in shown_text(app)


def sidebar_items(app: AppTest) -> list[str]:
    """Sidebar from top to bottom: page links by label, everything else by its text."""
    items = []
    for node in app.sidebar:
        if node.type == "page_link":
            items.append(node.proto.label)
        elif node.type in ("html", "markdown", "caption"):
            items.append(node.proto.body)
    return items


def test_the_sidebar_shows_the_brand_above_the_navigation() -> None:
    app = AppTest.from_file("../streamlit_app.py", default_timeout=30).run()

    items = sidebar_items(app)
    assert "Compliance Copilot" in items[0]
    assert items[1:4] == ["Start & Hilfe", "Audits ansehen", "Audit erstellen"]
    assert "Demo-Stand" in items[4]


def test_every_category_has_one_look_and_the_start_page_explains_it() -> None:
    from govguard_ui.review import CATEGORIES
    from govguard_ui.style import LOOKS

    app = page(start_script)

    assert set(LOOKS) == set(CATEGORIES)
    for look in LOOKS.values():
        assert look.meaning in shown_text(app) and look.todo in shown_text(app)


AVOIDED = ("Normanker", "Audit-Typ", "Trace", "nicht entscheidbar")  # CONTEXT.md: Vermeiden


def all_labels(app: AppTest) -> str:
    """Shown text plus expander, radio and table column labels."""
    labels = [e.label for e in app.expander] + [r.label for r in app.radio]
    columns = [str(c) for frame in app.dataframe for c in frame.value.columns]
    return "\n".join([shown_text(app), *labels, *columns])


def test_the_ui_uses_the_glossary_terms() -> None:
    gallery = page(gallery_script)
    gallery.session_state["gallery_spec-meldeportal-gesundheit_selected"] = first_gap_rule()
    gallery.run()
    text = "\n".join(all_labels(app) for app in (page(start_script), gallery, page(create_script)))

    assert not gallery.exception
    assert [word for word in AVOIDED if word in text] == []
    assert all(term in text for term in ("Primäranker", "Audit-Art", "Rückverfolgung", "Lücke"))


def first_gap_rule() -> str:
    """Rule id of the first gap in the stored spec report, to show a gap in the detail."""
    from govguard_ui.gallery import load_gallery
    from govguard_ui.paths import GALLERY, PRESETS
    from govguard_ui.review import category

    entries = {e.preset_id: e for e in load_gallery(PRESETS, GALLERY)}
    report = entries["spec-meldeportal-gesundheit"].report
    return next(f.rule_id for f in report.findings if category(f) == "GAP")
