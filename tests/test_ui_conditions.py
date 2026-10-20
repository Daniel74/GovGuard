"""Conditions in the spec report: frame, pills with popover, jump into the document (#61).

AppTest sees the popovers and their buttons; the browser look is in tests/visual.
"""

import re

from streamlit.testing.v1 import AppTest
from ui_helpers import (
    SPEC,
    conditions_page,
    gallery_entry,
    report_page,
    shown_text,
    with_conditions,
    without_conditions,
)

from govguard.audit_setup import conditions_for
from govguard_ui.report.review import category


def pills(app: AppTest) -> dict[str, str]:
    return {p.proto.popover.label: p.proto.popover.icon for p in app.get("popover")}


def popover(app: AppTest, label: str):
    return next(p for p in app.get("popover") if p.proto.popover.label == label)


def popover_text(app: AppTest, label: str) -> str:
    block = popover(app, label)
    text = "\n".join(str(n.value) for n in [*block.get("markdown"), *block.get("caption")])
    return re.sub(r"\\(.)", r"\1", text)  # escaped LLM text reads without backslashes


def test_a_report_without_conditions_has_neither_frame_nor_pills() -> None:
    app = report_page(without_conditions(gallery_entry(SPEC)))

    assert not app.exception
    assert app.get("popover") == []
    assert "Bedingungen" not in [m.value for m in app.markdown]


def test_each_condition_is_a_pill_with_its_result_and_a_warning_on_a_contradiction() -> None:
    app = conditions_page()

    assert not app.exception
    assert pills(app) == {
        "KI-System: nein": ":material/block:",
        "Hochrisiko-KI: nein": ":material/block:",
        "Drittlandübermittlung: ja": ":material/check:",
        "Auftragsverarbeiter: ja": ":material/warning:",
        "Einwilligung: nein": ":material/block:",
        "Mandantenfähigkeit: nicht genannt": ":material/help:",
        "Automatisierte Entscheidung: nicht genannt": ":material/help:"}


def test_the_frame_explains_the_conditions_under_the_tiles() -> None:
    app = conditions_page()

    heading = next(m for m in app.markdown if m.value == "#### Bedingungen")
    assert "Nur ein **nein** mit Beleg macht Prüfregeln nicht anwendbar" in heading.proto.help
    assert "Was sagt die Eingabe zu den Bedingungen?" in [c.value for c in app.caption]


def test_the_popover_of_a_yes_names_meaning_criterion_quote_effect_and_all_criteria() -> None:
    text = popover_text(conditions_page(), "Drittlandübermittlung: ja")

    assert "**Drittlandübermittlung**" in text
    assert "Personenbezogene Daten gehen an einen Empfänger außerhalb der EU" in text  # meaning
    assert "**Ergebnis: ja**" in text
    assert "Die Eingabe nennt eine Übermittlung personenbezogener Daten in ein Drittland." in text
    assert "Beleg (Zeilen 53–55): „Für die Auswertung nach Abschnitt 4 bindet" in text
    assert "(DSGVO Art. 44, 45, 46, 48 und 49) werden geprüft." in text
    assert "nicht genannt: Die Eingabe sagt nichts dazu." in text
    assert "nein: Die Eingabe sagt ausdrücklich, dass alle Daten in der EU" in text


def test_the_popover_of_a_no_counts_the_rules_that_are_not_applicable() -> None:
    text = popover_text(conditions_page(), "Einwilligung: nein")

    assert "**Ergebnis: nein**" in text
    assert "Beleg (Zeile 47): „Eine Einwilligung der Eltern wird für diese Auswertung nicht " \
        "eingeholt; die Verarbeitung der Gesundheitsangaben" in text
    assert "nach Art. 6 Abs. 1 lit. f DSGVO.“" in text  # whole sentences, not the cut line
    assert "Prüfregeln (DSGVO Art. 7 und 8) sind nicht anwendbar." in text


def test_a_derived_no_says_which_condition_it_follows_from() -> None:
    text = popover_text(conditions_page(), "Hochrisiko-KI: nein")

    assert "Folgt aus der Bedingung KI-System: Die Eingabe schließt ein KI-System ausdrücklich" \
        " aus." in text
    assert "Beleg (Zeile 10)" in text


def test_a_contradiction_shows_the_note_and_the_counter_evidence() -> None:
    text = popover_text(conditions_page(), "Auftragsverarbeiter: ja")

    assert "Widerspruch: Die Spezifikation belegt und verneint die Bedingung" in text
    assert "Gegenbeleg (Zeile 20)" in text


def test_an_unstated_condition_says_so_and_points_to_the_gaps() -> None:
    text = popover_text(conditions_page(), "Mandantenfähigkeit: nicht genannt")

    assert "**Ergebnis: nicht genannt**" in text
    assert "Die Eingabe sagt nicht, ob das System mehrere Mandanten bedient." in text
    assert "Lücken stehen unter „Nur wenn …“." in text
    assert "Beleg" not in text


def document(app: AppTest) -> str:
    return next(n.proto.body for n in app.get("html") if "gg-doc" in n.proto.body)


def marked_numbers(app: AppTest) -> list[int]:
    return [int(n) for n in re.findall(
        r'gg-line gg-mark"><span class="n">(\d+)</span>', document(app))]


def test_the_jump_button_marks_the_evidence_lines_in_the_document() -> None:
    app = conditions_page()

    app.button(key="report_condition_go_third_country_affirming").click().run()

    assert not app.exception
    assert marked_numbers(app) == [53, 54, 55]
    assert "Bedingung: Drittlandübermittlung" in shown_text(app)


def test_the_counter_evidence_has_its_own_jump() -> None:
    app = conditions_page()

    app.button(key="report_condition_go_processor_denying").click().run()

    assert marked_numbers(app) == [20]


def test_back_to_the_finding_shows_the_finding_again() -> None:
    app = conditions_page()
    app.button(key="report_condition_go_consent_denying").click().run()

    app.button(key="report_condition_close").click().run()

    assert "Bedingung: Einwilligung" not in shown_text(app)
    assert "Beleg:" in shown_text(app)


def test_a_rule_made_not_applicable_by_a_condition_shows_the_denial_and_marks_the_line() -> None:
    app = conditions_page()
    app.session_state["report_selected"] = "SPEC-DSGVO-Art.7Abs.3"
    app.run()

    assert "Die Spezifikation verneint: Einwilligung." in shown_text(app)
    assert "Nicht anwendbar" in shown_text(app)
    assert marked_numbers(app) == [47]


def test_the_popover_closes_when_the_jump_button_is_clicked() -> None:
    """A popover cannot be closed by a call: the jump gives it a new identity, which is closed."""
    app = conditions_page()
    before = popover(app, "Drittlandübermittlung: ja").proto.id

    app.button(key="report_condition_go_third_country_affirming").click().run()

    after = popover(app, "Drittlandübermittlung: ja")
    assert after.proto.id != before
    assert not after.proto.popover.open
    assert marked_numbers(app)[0] == 53


def test_a_rule_made_not_applicable_by_a_derived_no_names_the_source_condition() -> None:
    app = conditions_page()
    app.session_state["report_selected"] = "SPEC-KI-VO-Art.13Abs.1"
    app.run()

    assert "Die Spezifikation verneint: KI-System." in shown_text(app)
    assert "Hochrisiko-KI" not in shown_text(app).split("Die Spezifikation verneint:")[1][:30]


def test_the_gaps_in_a_popover_follow_the_chosen_source_like_the_section_below() -> None:
    entry = with_conditions(gallery_entry(SPEC))
    cond = next(c for c in conditions_for("spec") if c.id == "multi_tenant")
    gaps = [f for f in entry.report.findings
            if f.rule_id in cond.rule_ids and category(f) == "GAP"]
    app = report_page(entry)
    label = "Mandantenfähigkeit: nicht genannt"
    assert f"Ihre {len(gaps)} Lücken stehen" in popover_text(app, label)

    app.segmented_control(key="report_source").set_value("DSGVO").run()

    assert "Ihre 0 Lücken stehen" in popover_text(app, label)  # multi-tenancy rules are SDM


def expected_script(entry_json: str) -> None:
    from govguard_ui.gallery import GalleryEntry
    from govguard_ui.report.report_view import render_report

    entry = GalleryEntry.model_validate_json(entry_json)
    render_report(entry.report, entry.preset.title, (entry.source_name, entry.source_text),
                  entry.preset.expected, key="report")


def expected_page() -> AppTest:
    """With the expected strip: its buttons choose a finding like a click on the table."""
    entry = with_conditions(gallery_entry(SPEC))
    return AppTest.from_function(expected_script, args=(entry.model_dump_json(),),
                                 default_timeout=30).run()


def choose_art9(app: AppTest) -> None:
    next(b for b in app.button if b.label.startswith("DSGVO Art. 9 Abs. 2")).click().run()


def test_choosing_a_finding_afterwards_drops_the_jump() -> None:
    app = expected_page()
    app.button(key="report_condition_go_consent_denying").click().run()
    assert marked_numbers(app) == [47]

    choose_art9(app)

    assert "Bedingung: Einwilligung" not in shown_text(app)
    assert marked_numbers(app)[0] == 46  # the lines of the finding, not of the condition


def test_a_click_on_the_finding_that_is_already_selected_ends_the_jump() -> None:
    app = expected_page()
    choose_art9(app)
    app.button(key="report_condition_go_consent_denying").click().run()
    assert "Bedingung: Einwilligung" in shown_text(app)

    choose_art9(app)

    assert "Bedingung: Einwilligung" not in shown_text(app)
