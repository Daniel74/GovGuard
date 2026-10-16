"""Gallery: stored reports of the presets, each with its source document (ADR 0023, #11)."""

import hashlib
import shutil
from pathlib import Path

from govguard_ui.gallery import load_gallery
from govguard_ui.paths import GALLERY, PRESETS


def test_every_gallery_report_belongs_to_its_source_document() -> None:
    """Line references only make sense if the report audited exactly this text."""
    with_report = [entry for entry in load_gallery(PRESETS, GALLERY) if entry.report]

    assert {entry.preset_id for entry in with_report} >= {
        "spec-meldeportal-gesundheit", "arch-antragseingang-fehlerhaft"}
    for entry in with_report:
        source_hash = hashlib.sha256(entry.source_text.encode()).hexdigest()
        assert entry.report.trace.input_sha256 == source_hash, entry.preset_id


def test_spec_presets_come_first_and_each_names_its_source_file() -> None:
    entries = load_gallery(PRESETS, GALLERY)

    assert [e.preset.audit_type for e in entries][:2] == ["spec", "spec"]
    assert entries[0].preset_id == "spec-meldeportal-gesundheit"
    assert entries[0].source_name == "input.md"


def test_a_preset_without_a_stored_report_stays_in_the_gallery(tmp_path: Path) -> None:
    shutil.copytree(PRESETS / "arch-fristenwecker", tmp_path / "presets" / "arch-fristenwecker")

    [entry] = load_gallery(tmp_path / "presets", tmp_path / "gallery")

    assert entry.report is None
    assert entry.source_text.startswith("{")
