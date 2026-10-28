"""The switch "nach Fundstelle / nach Prüfregel" of the report, via AppTest (#81).

"nach Fundstelle" is the default. Its document is an own component: AppTest cannot click it, so
these tests read the data it gets and set the selection in the session state, as a click does;
the browser test in tests/visual draws and clicks it.
"""

import json

from streamlit.testing.v1 import AppTest
from ui_helpers import (
    arch_key,
    arch_page,
    conditions_page,
    finding_tables,
    shown_text,
    spec_key,
    spec_page,
)

from govguard_ui.report.findings_view import BY_RULE, BY_SITE

VIEW = arch_key("view")
SELECTED = arch_key("selected")
S3_PUBLIC_ACCESS = "ARCH-CIS-3.1.4"  # template.json lines 120–125 of 485


def by_rule(app: AppTest) -> AppTest:
    app.segmented_control(key=VIEW).set_value(BY_RULE).run()
    return app


def site_documents(app: AppTest) -> list[dict]:
    return [json.loads(n.proto.json) for n in app.get("bidi_component")
            if "sites" in json.loads(n.proto.json)]


def test_by_default_the_report_is_by_site_with_the_document() -> None:
    app = arch_page(view=None)

    assert app.segmented_control(key=VIEW).value == BY_SITE
    [document] = site_documents(app)
    assert document["sites"] and len(document["lines"]) == 485
    assert not [t for t in finding_tables(app) if "rows" in t]


def test_by_rule_shows_the_table_with_the_detail_column() -> None:
    app = by_rule(arch_page(view=None))

    assert not app.exception
    assert finding_tables(app) and not site_documents(app)
    assert any("Geprüftes Dokument" in m.value for m in app.markdown)


def test_the_chosen_finding_stays_chosen_when_the_view_changes() -> None:
    app = arch_page(view=BY_RULE)
    app.session_state[SELECTED] = S3_PUBLIC_ACCESS
    app.run()

    app.segmented_control(key=VIEW).set_value(BY_SITE).run()

    [document] = site_documents(app)
    assert document["selected"] == S3_PUBLIC_ACCESS
    current = document["sites"][document["current"]]
    assert S3_PUBLIC_ACCESS in [f["id"] for f in current["findings"]]


def test_the_status_filter_decides_which_findings_stand_in_the_sites() -> None:
    app = arch_page(view=None)

    app.pills(key=arch_key("status")).set_value(["FAIL"]).run()

    [document] = site_documents(app)
    shown = [f for s in document["sites"] for f in s["findings"]]
    assert {f["look"] for f in shown} == {"fail"}
    assert f"{len(shown)} von 175 Befunden angezeigt" in shown_text(app)  # FAIL always has lines


def test_the_document_has_the_frame_and_head_of_the_table_view() -> None:
    app = arch_page(view=None)

    assert "Geprüftes Dokument · template.json · 485 Zeilen" in shown_text(app).replace("`", "")
    assert "Balken am Rand = eine Fundstelle" in shown_text(app)


def test_findings_over_the_whole_document_stand_above_it_with_the_help_of_the_page() -> None:
    app = spec_page(view=None)

    heading = next(m for m in app.markdown if m.value.startswith("#### Betrifft das ganze"))
    assert heading.value == "#### Betrifft das ganze Dokument · 6"
    assert "mehr als die Hälfte des Dokuments" in heading.proto.help
    [whole] = [e for e in app.expander if "Hälfte des Dokuments" in e.label]
    assert whole.label == "6 Befunde mit mehr als der Hälfte des Dokuments als Beleg"


def test_findings_without_lines_stand_below_the_document() -> None:
    app = spec_page(view=None)
    app.pills(key=spec_key("status")).set_value(["N/A"]).run()

    heading = next(m for m in app.markdown if m.value.startswith("#### Ohne Zeilen"))
    assert heading.proto.help
    assert any(e.label.endswith("Befunde ohne Zeilen im Dokument") for e in app.expander)


def test_the_spec_report_has_the_switch_too_by_site_first() -> None:
    app = spec_page(view=None)

    assert app.segmented_control(key=spec_key("view")).options == [BY_SITE, BY_RULE]


def test_a_jump_from_a_condition_goes_back_to_the_table_where_the_focus_works() -> None:
    """#61: a condition marks its lines in the detail column, which "nach Fundstelle" lacks."""
    app = conditions_page(view=None)
    assert site_documents(app)

    app.button(key="report_condition_go_third_country_affirming").click().run()

    assert app.segmented_control(key="report_view").value == BY_RULE
    assert "Bedingung: Drittlandübermittlung" in shown_text(app)
    assert not site_documents(app)


def test_before_a_click_the_site_of_the_worst_finding_is_open() -> None:
    """The first row of the table stands in, FAIL first: the reader starts where it hurts most."""
    [document] = site_documents(arch_page(view=None))

    current = document["sites"][document["current"]]
    assert current["findings"][0]["look"] == "fail" and document["open"]
    assert document["selected"] in [f["id"] for f in current["findings"]]


def test_without_a_click_the_view_change_keeps_the_finding() -> None:
    app = arch_page(view=None)
    [document] = site_documents(app)

    [table] = [t for t in finding_tables(by_rule(app)) if "rows" in t]

    assert table["selected"] == document["selected"]
