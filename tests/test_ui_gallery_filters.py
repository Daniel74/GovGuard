"""Status and source filter of the spec audit on "Audits ansehen", via AppTest (#44, #43, #45).

Numbers of the spec report as in the design artefact of #11: 16 FAIL, 14 WARN with evidence,
7 PASS, 8 N/A, 106 gaps; without gaps DSGVO 17 findings (✕10 !1 ✓4 –2), SDM 28.
"""

from streamlit.testing.v1 import AppTest
from ui_helpers import finding_tables, shown_text, spec_key, spec_page, table_rows


def listed(app: AppTest) -> int:
    return len(table_rows(app))


def test_by_default_fail_warn_and_pass_are_listed_and_na_is_hidden() -> None:
    app = spec_page()

    assert listed(app) == 16 + 14 + 7
    assert "37 von 45 Befunden angezeigt" in shown_text(app)
    assert "Ausgeblendet" not in shown_text(app)  # "37 von 45" says it


def test_the_spec_findings_stand_in_one_table_the_first_row_selected() -> None:
    [table] = finding_tables(spec_page())

    assert table["selected"] == table["rows"][0]["id"] == "SPEC-SDM-M50.D01"


def test_switching_a_status_on_or_off_changes_the_list_and_its_count() -> None:
    app = spec_page()

    app.pills(key=spec_key("status")).set_value(["FAIL", "N/A"]).run()

    assert listed(app) == 16 + 8
    assert "24 von 45 Befunden angezeigt" in shown_text(app)
    assert not app.exception


def test_without_any_status_the_list_is_empty_and_everything_is_hidden() -> None:
    app = spec_page()

    app.pills(key=spec_key("status")).set_value([]).run()

    assert not app.exception
    assert listed(app) == 0
    assert "0 von 45 Befunden angezeigt" in shown_text(app)


def test_the_status_filter_shows_counts_and_no_label() -> None:
    pills = spec_page().pills(key=spec_key("status"))

    assert pills.options == [
        "✕ Verstoß belegt 16", "! Prüfbedarf 14", "✓ Einhaltung belegt 7", "– Nicht anwendbar 8"]
    assert pills.proto.label_visibility.value == pills.proto.label_visibility.COLLAPSED


def test_the_source_filter_starts_with_all_and_counts_each_source_without_gaps() -> None:
    sources = spec_page().segmented_control(key=spec_key("source"))

    assert sources.value == "Alle"
    assert sources.options == ["Alle (45)", "DSGVO (17)", "SDM (28)"]


def test_the_source_filter_keeps_only_findings_of_that_source() -> None:
    app = spec_page()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert listed(app) == 10 + 1 + 4  # FAIL, WARN with evidence, PASS of DSGVO


def test_the_status_filter_counts_the_findings_of_the_chosen_source() -> None:
    app = spec_page()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert app.pills(key=spec_key("status")).options == [
        "✕ Verstoß belegt 10", "! Prüfbedarf 1", "✓ Einhaltung belegt 4", "– Nicht anwendbar 2"]
    assert "15 von 17 Befunden angezeigt" in shown_text(app)


def test_the_chosen_status_stays_when_the_source_changes() -> None:
    app = spec_page()
    app.pills(key=spec_key("status")).set_value(["FAIL"]).run()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert app.pills(key=spec_key("status")).value == ["FAIL"]
    assert listed(app) == 10



def gap_list(app: AppTest) -> str:
    return next(e.label for e in app.expander if "nicht beschreibt" in e.label)


def test_the_gap_list_counts_the_gaps_of_the_chosen_source() -> None:
    app = spec_page()
    assert gap_list(app) == "Was die Eingabe nicht beschreibt · 106 Lücken"

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert gap_list(app) == "Was die Eingabe nicht beschreibt · 18 Lücken"
