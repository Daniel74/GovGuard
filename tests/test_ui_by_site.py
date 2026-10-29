"""The switch "nach Fundstelle / nach Prüfregel" of the report, via AppTest (#81).

"nach Fundstelle" is the default. Its document is an own component: AppTest cannot click it, so
these tests read the data it gets and set the selection in the session state, as a click does;
the browser test in tests/visual draws and clicks it.
"""

import json

from streamlit.testing.v1 import AppTest
from ui_helpers import (
    SPEC,
    arch_key,
    arch_page,
    conditions_page,
    finding_tables,
    shown_text,
    spec_key,
    spec_page,
)

from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS
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
    several = next(int(m.value.split("·")[1]) for m in app.markdown
                   if m.value.startswith("#### Betrifft mehrere"))  # FAIL always has lines
    assert f"{len(shown) + several} von 175 Befunden angezeigt" in shown_text(app)


def test_the_document_has_a_heading_with_the_count_and_a_caption_like_the_groups() -> None:
    app = arch_page(view=None)

    heading = next(m for m in app.markdown if m.value.startswith("#### Geprüftes Dokument"))
    assert heading.value == "#### Geprüftes Dokument · 8 Fundstellen"
    assert "ist ein Dokumentabschnitt" in heading.proto.help
    [caption] = [c for c in app.caption if "Balken am Rand = eine Fundstelle" in c.value]
    assert caption.value.startswith("`template.json` · 485 Zeilen · Balken am Rand")


def test_one_site_is_called_a_site_in_the_singular() -> None:
    app = spec_page(view=None)
    app.pills(key=spec_key("status")).set_value(["N/A"]).run()

    heading = next(m for m in app.markdown if m.value.startswith("#### Geprüftes Dokument"))
    assert heading.value == "#### Geprüftes Dokument · 1 Fundstelle"


def test_findings_over_several_sections_stand_above_the_document() -> None:
    app = spec_page(view=None)

    heading = next(m for m in app.markdown if m.value.startswith("#### Betrifft mehrere"))
    assert heading.value == "#### Betrifft mehrere Abschnitte · 8"
    assert "in mehreren Abschnitten" in heading.proto.help
    [several] = [e for e in app.expander if "aus mehreren Abschnitten" in e.label]
    assert several.label == "8 Befunde mit Belegen aus mehreren Abschnitten"


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
    chosen = next(f for f in current["findings"] if f["id"] == document["selected"])
    assert chosen["look"] == "fail" and document["open"]


def test_without_a_click_the_view_change_keeps_the_finding() -> None:
    app = arch_page(view=None)
    [document] = site_documents(app)

    [table] = [t for t in finding_tables(by_rule(app)) if "rows" in t]

    assert table["selected"] == document["selected"]


def test_a_finding_over_several_sections_chosen_in_the_table_is_marked_in_the_document() -> None:
    """ARCH-CIS-2.20 names lines 1–200: no site is current, the lines stand marked all the same."""
    app = arch_page(view=BY_RULE)
    app.session_state[SELECTED] = "ARCH-CIS-2.20"
    app.run()

    app.segmented_control(key=VIEW).set_value(BY_SITE).run()

    [document] = site_documents(app)
    assert document["current"] is None and document["selected"] == "ARCH-CIS-2.20"
    assert [n["n"] for n in document["lines"] if n["in_finding"]] == list(range(1, 201))


MULTI_FINDING = "ARCH-CIS-2.20"  # lines 1–200: over several sections
SHOW = arch_key(f"multi_show_{MULTI_FINDING}")


def test_a_click_on_a_finding_over_several_sections_selects_it_and_marks_its_lines() -> None:
    """The group has no bar to click: each finding carries a button that selects it (#84)."""
    app = arch_page(view=None)
    assert [e for e in app.expander if "aus mehreren Abschnitten" in e.label]

    app.button(key=SHOW).click().run()

    [document] = site_documents(app)
    assert (document["selected"], document["current"]) == (MULTI_FINDING, None)
    assert [n["n"] for n in document["lines"] if n["in_finding"]] == list(range(1, 201))
    [several] = [e for e in app.expander if "aus mehreren Abschnitten" in e.label]
    assert not several.proto.expanded  # shut by default, also while it holds the selected one


def has(app: AppTest, key: str) -> bool:
    try:
        return bool(app.get_by_key(key))
    except KeyError:
        return False


def test_the_selected_finding_of_the_group_is_marked_and_the_others_are_not() -> None:
    """The mark is a CSS class of the keyed container, like .frow.sel in the box under a site."""
    marked, idle = (arch_key(f"multi_item_{state}ARCH-CIS-2.20") for state in ("sel_", ""))
    other = arch_key("multi_item_ARCH-CIS-2.15")
    app = arch_page(view=None)
    assert not has(app, marked) and has(app, idle)

    app.button(key=SHOW).click().run()

    assert has(app, marked) and not has(app, idle) and has(app, other)


def test_findings_without_lines_have_no_button_to_show_lines() -> None:
    app = spec_page(view=None)
    app.pills(key=spec_key("status")).set_value(["N/A"]).run()

    assert any(e.label.endswith("Befunde ohne Zeilen im Dokument") for e in app.expander)
    assert not [b for b in app.button if b.key and "_show_" in b.key]


def test_the_fold_row_opens_by_itself_when_the_selected_finding_lies_inside() -> None:
    """#86: a PASS chosen in the document must not hide behind a closed row."""
    app = arch_page(view=None)
    [document] = site_documents(app)
    assert not any(s["rest_auto"] for s in document["sites"])  # the first row is a FAIL
    passing = next(f["id"] for s in document["sites"] for f in s["findings"]
                   if f["id"] in s["rest"])

    app.session_state[SELECTED] = passing
    app.run()

    [document] = site_documents(app)
    opened = [s for s in document["sites"] if s["rest_auto"]]
    assert len(opened) == 1 and passing in opened[0]["rest"]


def test_each_site_lists_warn_and_fail_apart_from_the_findings_without_need_to_act() -> None:
    [document] = site_documents(arch_page(view=None))

    for site in document["sites"]:
        look = {f["id"]: f["look"] for f in site["findings"]}
        assert {look[i] for i in site["open"]} <= {"fail", "warn"}
        assert not {look[i] for i in site["rest"]} & {"fail", "warn"}
        assert sorted(site["open"] + site["rest"]) == sorted(look)


def test_the_group_over_several_sections_is_shut_even_when_it_holds_the_selected_finding() -> None:
    """#86: the reader opens it; the group without lines still opens with its selected finding."""
    app = arch_page(view=None)
    app.session_state[SELECTED] = MULTI_FINDING
    app.run()

    [several] = [e for e in app.expander if "aus mehreren Abschnitten" in e.label]

    assert not several.proto.expanded
    assert has(app, arch_key(f"multi_item_sel_{MULTI_FINDING}"))  # marked, hidden in the shut group


def test_the_group_without_lines_still_opens_with_its_selected_finding() -> None:
    entry = next(e for e in load_gallery(PRESETS, GALLERY) if e.preset_id == SPEC)
    unplaced = next(f.rule_id for f in entry.report.findings
                    if f.line_start is None and f.status == "N/A")
    app = spec_page(view=None)
    app.pills(key=spec_key("status")).set_value(["N/A"]).run()  # the group shows N/A
    label = "Befunde ohne Zeilen im Dokument"
    assert not any(e.proto.expanded for e in app.expander if e.label.endswith(label))

    app.session_state[spec_key("selected")] = unplaced
    app.run()

    assert next(e for e in app.expander if e.label.endswith(label)).proto.expanded
