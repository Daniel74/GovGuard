"""Head of a report on "Audits ansehen": frame, tiles and expected result, via AppTest (#42)."""

import json

import pytest
from streamlit.runtime.media_file_manager import MediaFileManager
from streamlit.testing.v1 import AppTest
from test_ui_create_page import frames
from test_ui_pages import gallery_script, page

from govguard_ui.texts import HELP

ARCH = "arch-antragseingang-fehlerhaft"


def test_the_head_has_the_json_download_but_no_trace_expander() -> None:
    app = page(gallery_script)

    assert not app.exception
    assert [e.label for e in app.expander if e.label == "Rückverfolgung"] == []
    assert [b.proto.label for b in app.get("download_button")] == [
        "Report als JSON herunterladen"]


def test_the_json_download_keeps_the_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    downloads: list[bytes] = []
    add = MediaFileManager.add

    def recording_add(self, data, *args, **kwargs) -> str:  # where the download bytes go
        downloads.append(data)
        return add(self, data, *args, **kwargs)

    monkeypatch.setattr(MediaFileManager, "add", recording_add)

    page(gallery_script)

    assert json.loads(downloads[0])["trace"]["audit_id"]


def test_overall_status_and_expected_strip_carry_a_help() -> None:
    app = page(gallery_script)

    helps = {m.value: m.proto.help for m in app.markdown}
    assert helps["Gesamtstatus"] == HELP["overall"]
    assert helps["**Soll-Abgleich: wie erwartet**"] == HELP["expected"]


def head_frame(app) -> str:
    return next(frame for frame in frames(app) if "Report als JSON herunterladen" in frame)


def test_title_meta_download_and_overall_status_share_one_frame() -> None:
    head = head_frame(page(gallery_script))

    assert "Online-Anmeldung zur Schuleingangsuntersuchung mit US-Analysedienst" in head
    for term, value in (("Audit-Art", "Spezifikation (DSGVO, SDM)"),
                        ("Modell", "openai/gpt-oss-120b"), ("Retries", "0")):
        assert f"<th>{term}</th><td>{value}</td>" in head
    assert "Gesamtstatus" in head and "Verstoß belegt" in head
    assert "151 Befunde" not in head  # the tiles count, the head does not


def test_each_tile_is_a_frame_with_its_explanation_inside() -> None:
    app = page(gallery_script)

    tiles = [frame for frame in frames(app) if frame in SPEC_TILES]
    assert tiles == SPEC_TILES
    assert [m.value for m in app.metric] == ["16", "14", "7", "8", "106", "23"]


SPEC_TILES = [  # label and explanation of the stored spec report, as in the design artefact
    "✕ FAIL\nVerstoß belegt",
    "! WARN · Prüfbedarf\nmit Beleg · davon 7 herabgestuft",
    "✓ PASS\nEinhaltung belegt",
    "– N/A\nnicht anwendbar",
    "○ Lücken\nnicht beschrieben · kein Verstoß",
    "FAIL-Prüfer\ngeprüft · 16 bestätigt · 7 herabgestuft · 0 nicht verfügbar",
]


def test_an_architecture_without_gaps_has_no_gap_tile_and_no_fail_judge() -> None:
    app = page(gallery_script)
    app.selectbox(key="gallery_preset").select(ARCH).run()

    assert [(m.label, m.value) for m in app.metric] == [
        ("✕ FAIL", "36"), ("! WARN · Prüfbedarf", "1"), ("✓ PASS", "27"), ("– N/A", "111"),
        ("FAIL-Prüfer", "entfällt")]
    assert "! WARN · Prüfbedarf\nmit Beleg" in frames(app)  # no "davon 0 herabgestuft"
    assert "– N/A\nRessourcentyp nicht in der Architektur" in frames(app)
    assert "FAIL-Prüfer\nNur bei offener Welt: Spezifikation, Architektur als Freitext." \
        in frames(app)  # the stored architecture is a template, a closed world (#46)


def free_text_without_fail_script() -> None:
    from govguard.models import FailJudgeCount
    from govguard_ui.gallery import load_gallery
    from govguard_ui.paths import GALLERY, PRESETS
    from govguard_ui.report_header import render_header

    entry = next(e for e in load_gallery(PRESETS, GALLERY) if e.preset_id == "arch-protokollarchiv")
    render_header(entry.report.model_copy(update={"fail_judge": FailJudgeCount()}), "t", "ft")


def test_free_text_architecture_without_fail_shows_zero_checked_not_omitted() -> None:
    app = AppTest.from_function(free_text_without_fail_script, default_timeout=30).run()

    assert not app.exception
    assert ("FAIL-Prüfer", "0") in [(m.label, m.value) for m in app.metric]  # open world (#46)


def test_the_expected_result_is_one_strip_and_overall_status_is_no_button() -> None:
    app = page(gallery_script)

    strip = next(frame for frame in frames(app) if "Soll-Abgleich: wie erwartet" in frame)
    assert strip.split("\n")[1:] == ["✓ Gesamtstatus Soll FAIL, Ist FAIL",
                                     "DSGVO Art. 9: Soll FAIL, Ist FAIL",
                                     "SDM Löschen M60.P01: Soll FAIL, Ist FAIL"]
    assert [b.label for b in app.button if "Gesamtstatus" in b.label] == []


def test_a_click_on_a_required_finding_shows_it_in_the_detail() -> None:
    app = page(gallery_script)

    next(b for b in app.button if b.label.startswith("DSGVO Art. 9")).click().run()

    assert "#### Einwilligung für besondere Kategorien" in [m.value for m in app.markdown]


def deviating_script() -> None:
    from govguard.models import Expected
    from govguard_ui.gallery import load_gallery
    from govguard_ui.paths import GALLERY, PRESETS
    from govguard_ui.report_header import render_expected

    entry = load_gallery(PRESETS, GALLERY)[0]
    render_expected(entry.report, Expected(overall_status="PASS", required_findings=[]), "dev")


def test_a_deviation_is_a_strip_with_a_cross_and_a_help() -> None:
    app = AppTest.from_function(deviating_script, default_timeout=30).run()

    assert not app.exception
    strip = next(frame for frame in frames(app) if "Soll-Abweichung" in frame)
    assert strip.split("\n")[1:] == ["✕ Gesamtstatus Soll PASS, Ist FAIL"]
    assert {m.value: m.proto.help for m in app.markdown}["**Soll-Abweichung**"] == HELP["expected"]
