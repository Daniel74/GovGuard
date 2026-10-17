"""Smoke tests of the Streamlit pages, headless via AppTest (#11). Layout: tests/visual (#40)."""

import re

from streamlit.testing.v1 import AppTest

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
    text = re.sub(r"\\(.)", r"\1", text)  # escaped LLM text reads without backslashes
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
    assert all(term in text for term in ("Primäranker", "Audit-Art", "Gesamtstatus", "Lücke"))


def first_gap_rule() -> str:
    """Rule id of the first gap in the stored spec report, to show a gap in the detail."""
    from govguard_ui.gallery import load_gallery
    from govguard_ui.paths import GALLERY, PRESETS
    from govguard_ui.review import category

    entries = {e.preset_id: e for e in load_gallery(PRESETS, GALLERY)}
    report = entries["spec-meldeportal-gesundheit"].report
    return next(f.rule_id for f in report.findings if category(f) == "GAP")


def test_the_detail_shows_status_and_meaning_as_one_mark() -> None:
    app = page(gallery_script)

    detail = next(n.proto.body for n in app.get("html") if "gg-badge" in n.proto.body)
    assert detail == '<span class="gg-badge gg-fail">✕ FAIL · Verstoß belegt</span>'
