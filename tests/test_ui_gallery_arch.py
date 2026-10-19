"""Architecture audit on "Audits ansehen": one table with status and source filter, like the
spec audit, via AppTest (#45).

Numbers of arch-antragseingang-fehlerhaft: 36 FAIL, 27 PASS, 1 WARN, 111 N/A, no gaps;
BSI 39 findings, C5 11, CIS 20 (✕4 ✓4), FSBP 105.
"""

from ui_helpers import (
    arch_key,
    arch_page,
    finding_tables,
    gallery_script,
    page,
    shown_text,
    table_rows,
)


def test_arch_findings_stand_in_one_table_with_a_head_na_hidden() -> None:
    app = arch_page()

    assert len(finding_tables(app)) == 1
    assert len(table_rows(app)) == 36 + 27 + 1
    assert "64 von 175 Befunden angezeigt" in shown_text(app)
    assert "sortiert" not in shown_text(app)  # the reader sees the order


def test_the_arch_status_filter_counts_like_the_spec_one() -> None:
    pills = arch_page().pills(key=arch_key("status"))

    assert pills.options == [
        "✕ Verstoß belegt 36", "! Prüfbedarf 1", "✓ Einhaltung belegt 27", "– Nicht anwendbar 111"]


def test_the_arch_source_filter_starts_with_all_and_keeps_only_that_source() -> None:
    app = arch_page()
    sources = app.segmented_control(key=arch_key("source"))
    assert sources.value == "Alle"
    assert sources.options == ["Alle (175)", "BSI (39)", "C5 (11)", "CIS (20)", "FSBP (105)"]

    sources.set_value("CIS").run()

    assert len(table_rows(app)) == 4 + 4


def test_gaps_of_an_arch_audit_stand_below_the_table() -> None:
    app = page(gallery_script)
    app.selectbox(key="gallery_preset").select("arch-fristenwecker").run()

    assert any(e.label == "Was die Eingabe nicht beschreibt · 3 Lücken" for e in app.expander)
    assert "Befunden angezeigt" in shown_text(app)  # the gaps are not counted there
    assert "Lücken stehen" not in shown_text(app)
