"""Architecture audit on "Audits ansehen": one table with status and source filter, like the
spec audit, via AppTest (#45).

Numbers of arch-antragseingang-fehlerhaft: 36 FAIL, 27 PASS, 1 WARN, 111 N/A, no gaps;
BSI 39 findings, C5 11, CIS 20 (✕4 ✓4), FSBP 105.
"""

from test_ui_pages import gallery_script, page, shown_text
from ui_helpers import arch_key, arch_page, finding_tables, table_rows


def test_arch_findings_stand_in_one_table_with_a_head_na_hidden() -> None:
    app = arch_page()

    assert len(finding_tables(app)) == 1
    assert len(table_rows(app)) == 36 + 27 + 1
    assert "64 Befunde angezeigt · sortiert: FAIL zuerst, dann nach Zeile" in shown_text(app)
    assert "Ausgeblendet: 111 N/A." in shown_text(app)


def test_the_arch_status_filter_counts_like_the_spec_one() -> None:
    pills = arch_page().pills(key=arch_key("status"))

    assert pills.options == ["✕ FAIL 36", "! WARN · Prüfbedarf 1", "✓ PASS 27", "– N/A 111"]


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
    assert "Lücken stehen unter der Tabelle" in shown_text(app)
