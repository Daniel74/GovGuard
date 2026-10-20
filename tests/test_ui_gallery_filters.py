"""Status and source filter of the spec audit on "Audits ansehen", via AppTest (#44, #43, #45).

Numbers of the spec report after #61 (350 rules, condition pre-run): 33 FAIL, 17 WARN with
evidence, 28 PASS, 38 N/A, 234 gaps; without gaps DSGVO 68 findings (✕20 !14 ✓23 –11), KI-VO 20,
SDM 28.
"""

from streamlit.testing.v1 import AppTest
from ui_helpers import finding_tables, shown_text, spec_key, spec_page, table_rows


def listed(app: AppTest) -> int:
    return len(table_rows(app))


def test_by_default_fail_warn_and_pass_are_listed_and_na_is_hidden() -> None:
    app = spec_page()

    assert listed(app) == 33 + 17 + 28
    assert "78 von 116 Befunden angezeigt" in shown_text(app)
    assert "Ausgeblendet" not in shown_text(app)  # "78 von 116" says it


def test_the_spec_findings_stand_in_one_table_the_first_row_selected() -> None:
    [table] = finding_tables(spec_page())

    assert table["selected"] == table["rows"][0]["id"] == "SPEC-SDM-M50.S15"


def test_switching_a_status_on_or_off_changes_the_list_and_its_count() -> None:
    app = spec_page()

    app.pills(key=spec_key("status")).set_value(["FAIL", "N/A"]).run()

    assert listed(app) == 33 + 38
    assert "71 von 116 Befunden angezeigt" in shown_text(app)
    assert not app.exception


def test_without_any_status_the_list_is_empty_and_everything_is_hidden() -> None:
    app = spec_page()

    app.pills(key=spec_key("status")).set_value([]).run()

    assert not app.exception
    assert listed(app) == 0
    assert "0 von 116 Befunden angezeigt" in shown_text(app)


def test_the_status_filter_shows_counts_and_no_label() -> None:
    pills = spec_page().pills(key=spec_key("status"))

    assert pills.options == [
        "✕ Verstoß belegt 33", "! Prüfbedarf 17", "✓ Einhaltung belegt 28", "– Nicht anwendbar 38"]
    assert pills.proto.label_visibility.value == pills.proto.label_visibility.COLLAPSED


def test_the_source_filter_starts_with_all_and_counts_each_source_without_gaps() -> None:
    sources = spec_page().segmented_control(key=spec_key("source"))

    assert sources.value == "Alle"
    assert sources.options == ["Alle (116)", "DSGVO (68)", "KI-VO (20)", "SDM (28)"]


def test_the_source_filter_keeps_only_findings_of_that_source() -> None:
    app = spec_page()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert listed(app) == 20 + 14 + 23  # FAIL, WARN with evidence, PASS of DSGVO


def test_the_status_filter_counts_the_findings_of_the_chosen_source() -> None:
    app = spec_page()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert app.pills(key=spec_key("status")).options == [
        "✕ Verstoß belegt 20", "! Prüfbedarf 14", "✓ Einhaltung belegt 23", "– Nicht anwendbar 11"]
    assert "57 von 68 Befunden angezeigt" in shown_text(app)


def test_the_chosen_status_stays_when_the_source_changes() -> None:
    app = spec_page()
    app.pills(key=spec_key("status")).set_value(["FAIL"]).run()

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert app.pills(key=spec_key("status")).value == ["FAIL"]
    assert listed(app) == 20



def gap_heading(app: AppTest) -> str:
    """The report has conditions: the gaps are the section "Lücken · N"."""
    return next(m.value for m in app.markdown if m.value.startswith("### Lücken · "))


def test_the_gap_section_counts_the_gaps_of_the_chosen_source() -> None:
    app = spec_page()
    assert gap_heading(app) == "### Lücken · 234"

    app.segmented_control(key=spec_key("source")).set_value("DSGVO").run()

    assert gap_heading(app) == "### Lücken · 101"
