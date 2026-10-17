"""Status and source filter of the finding list on "Audits ansehen", via AppTest (#44)."""

from streamlit.testing.v1 import AppTest
from test_ui_pages import gallery_script, page, shown_text

from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS

ARCH = "arch-antragseingang-fehlerhaft"  # 29 FAIL, 28 PASS, 109 N/A, no WARN


def arch_page() -> AppTest:
    app = page(gallery_script)
    app.selectbox(key="gallery_preset").select(ARCH).run()
    return app


def stored(status: str, source: str | None = None) -> int:
    """Findings of the stored report counted straight from the JSON, not by the view logic."""
    report = next(e.report for e in load_gallery(PRESETS, GALLERY) if e.preset_id == ARCH)
    return sum(1 for f in report.findings if f.status == status
               and source in (None, f.rule_id.split("-")[1]))


def listed(app: AppTest) -> int:
    return len(app.dataframe[0].value)


def test_by_default_fail_warn_and_pass_are_listed_and_na_is_hidden() -> None:
    app = arch_page()

    assert listed(app) == stored("FAIL") + stored("PASS") == 57
    assert f"{listed(app)} Befunde angezeigt" in shown_text(app)
    assert f"Ausgeblendet: {stored('N/A')} N/A." in shown_text(app)


def test_switching_a_status_on_or_off_changes_the_list_and_the_hidden_note() -> None:
    app = arch_page()
    pills = app.pills(key=f"gallery_{ARCH}_status")

    pills.set_value(["FAIL", "N/A"]).run()

    assert listed(app) == stored("FAIL") + stored("N/A")
    assert f"Ausgeblendet: {stored('PASS')} PASS." in shown_text(app)
    assert not app.exception


def test_without_any_status_the_list_is_empty_and_everything_is_hidden() -> None:
    app = arch_page()

    app.pills(key=f"gallery_{ARCH}_status").set_value([]).run()

    assert not app.exception
    assert listed(app) == 0
    assert "0 Befunde angezeigt" in shown_text(app)


def test_the_source_filter_keeps_only_findings_of_that_source() -> None:
    app = arch_page()
    sources = app.segmented_control(key=f"gallery_{ARCH}_source")
    assert sources.options == ["BSI", "C5", "CIS", "FSBP"]  # no choice: all sources

    sources.set_value("CIS").run()

    assert listed(app) == stored("FAIL", "CIS") + stored("PASS", "CIS")


def test_clearing_the_source_filter_lists_all_sources_again() -> None:
    app = arch_page()
    app.segmented_control(key=f"gallery_{ARCH}_source").set_value("CIS").run()

    app.segmented_control(key=f"gallery_{ARCH}_source").set_value(None).run()

    assert listed(app) == 57
