"""Status and source filter of the spec audit on "Audits ansehen", via AppTest (#44, #43).

Numbers of the spec report as in the design artefact of #11: 16 FAIL, 14 WARN with evidence,
7 PASS, 8 N/A, 106 gaps; DSGVO 35 findings, SDM 116.
"""

from streamlit.testing.v1 import AppTest
from test_ui_pages import shown_text
from ui_helpers import spec_key, spec_page


def listed(app: AppTest) -> int:
    return sum(1 for button in app.button if "_row_" in button.key)


def test_by_default_fail_warn_and_pass_are_listed_and_na_is_hidden() -> None:
    app = spec_page()

    assert listed(app) == 16 + 14 + 7
    assert "37 Befunde angezeigt" in shown_text(app)
    assert "Ausgeblendet: 8 N/A." in shown_text(app)


def test_switching_a_status_on_or_off_changes_the_list_and_the_hidden_note() -> None:
    app = spec_page()

    app.pills(key=spec_key("status")).set_value(["FAIL", "N/A"]).run()

    assert listed(app) == 16 + 8
    assert "Ausgeblendet: 14 WARN, 7 PASS." in shown_text(app)
    assert not app.exception


def test_without_any_status_the_list_is_empty_and_everything_is_hidden() -> None:
    app = spec_page()

    app.pills(key=spec_key("status")).set_value([]).run()

    assert not app.exception
    assert listed(app) == 0
    assert "0 Befunde angezeigt" in shown_text(app)


def test_the_status_filter_shows_counts_and_no_label() -> None:
    pills = spec_page().pills(key=spec_key("status"))

    assert pills.options == [
        "✕ FAIL 16", "! WARN · Prüfbedarf 14", "✓ PASS 7", "– N/A 8"]
    assert pills.proto.label_visibility.value == pills.proto.label_visibility.COLLAPSED


def test_the_source_filter_starts_with_all_and_counts_each_source() -> None:
    sources = spec_page().segmented_control(key=spec_key("source"))

    assert sources.value == "Alle"
    assert sources.options == [
        "Alle (151)", "DSGVO (35)", "SDM (116)"]


def test_the_source_filter_keeps_only_findings_of_that_source() -> None:
    app = spec_page()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert listed(app) == 10 + 1 + 4  # FAIL, WARN with evidence, PASS of DSGVO



def gap_list(app: AppTest) -> str:
    return next(e.label for e in app.expander if "nicht beschreibt" in e.label)


def test_the_gap_list_counts_the_gaps_of_the_chosen_source() -> None:
    app = spec_page()
    assert gap_list(app) == "Was die Eingabe nicht beschreibt · 106 Lücken"

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert gap_list(app) == "Was die Eingabe nicht beschreibt · 18 Lücken"
