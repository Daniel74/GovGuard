"""Head of a report on "Audits ansehen": frame, tiles and expected result, via AppTest (#42)."""

from test_ui_create_page import frames
from test_ui_pages import gallery_script, page

ARCH = "arch-antragseingang-fehlerhaft"


def test_the_head_has_the_json_download_but_no_trace_expander() -> None:
    app = page(gallery_script)

    assert not app.exception
    assert [e.label for e in app.expander if e.label == "Rückverfolgung"] == []
    assert [b.proto.label for b in app.get("download_button")] == [
        "Report als JSON herunterladen"]


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
        ("✕ FAIL", "29"), ("! WARN · Prüfbedarf", "0"), ("✓ PASS", "28"), ("– N/A", "109"),
        ("FAIL-Prüfer", "entfällt")]
    assert "– N/A\nRessourcentyp nicht in der Architektur" in frames(app)
    assert "FAIL-Prüfer\nNur bei Spezifikationen." in frames(app)


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
