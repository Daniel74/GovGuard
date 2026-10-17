"""Rows of the finding table: the component gets plain values, its cells show them as text (#45)."""

from govguard_ui.finding_list import table_rows
from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS

ART9 = next(f for e in load_gallery(PRESETS, GALLERY) if e.report
            for f in e.report.findings if f.rule_id == "SPEC-DSGVO-Art.9")  # FAIL, lines 46–49


def test_a_row_holds_status_rule_anchor_and_lines() -> None:
    assert table_rows([ART9]) == [{
        "id": "SPEC-DSGVO-Art.9", "look": "fail", "status": "✕ FAIL",
        "title": "Einwilligung für besondere Kategorien", "primary_anchor": "DSGVO Art. 9",
        "lines": "46–49"}]


def test_llm_text_reaches_the_row_unchanged_the_cell_shows_it_as_text() -> None:
    """No escaping in Python: textContent in the browser does it (tests/visual)."""
    finding = ART9.model_copy(update={"title": "[x](y) <b>z</b>", "primary_anchor": "$a$"})

    row = table_rows([finding])[0]

    assert (row["title"], row["primary_anchor"]) == ("[x](y) <b>z</b>", "$a$")


def test_a_downgrade_stays_visible_in_the_row() -> None:
    """ADR 0017: the original status shows next to the WARN."""
    finding = ART9.model_copy(update={"status": "WARN", "downgraded_from": "FAIL"})

    assert table_rows([finding])[0]["status"] == "! WARN ↓ von FAIL"
    assert table_rows([finding])[0]["look"] == "warn"


def test_a_finding_without_lines_shows_a_dash() -> None:
    finding = ART9.model_copy(update={"status": "N/A", "line_start": None, "line_end": None})

    assert table_rows([finding])[0]["lines"] == "–"
