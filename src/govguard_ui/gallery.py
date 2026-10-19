"""Gallery: stored audit reports of the presets next to their source document (ADR 0023)."""

from pathlib import Path

from pydantic import BaseModel

from govguard.models import AuditReport, Preset

SELF_AUDIT = "spec-govguard"  # GovGuard audits its own SPEC.md (#36)


class GalleryEntry(BaseModel):
    preset_id: str
    preset: Preset
    source_name: str  # file name of the audited input, e.g. input.md
    source_text: str
    report: AuditReport | None  # None: no report committed yet


def load_gallery(presets_dir: Path, gallery_dir: Path) -> list[GalleryEntry]:
    """Every preset, spec audits first and the self-audit after the fictional ones;
    a missing report keeps the preset visible."""
    entries = [_entry(path, gallery_dir) for path in sorted(presets_dir.iterdir())
               if (path / "preset.json").is_file()]
    return sorted(entries, key=lambda e: (e.preset.audit_type != "spec", e.preset_id == SELF_AUDIT))


def _entry(preset_dir: Path, gallery_dir: Path) -> GalleryEntry:
    preset = Preset.model_validate_json((preset_dir / "preset.json").read_text(encoding="utf-8"))
    report_file = gallery_dir / f"{preset_dir.name}.json"
    report = (AuditReport.model_validate_json(report_file.read_text(encoding="utf-8"))
              if report_file.is_file() else None)
    return GalleryEntry(
        preset_id=preset_dir.name, preset=preset, source_name=preset.input_file,
        source_text=(preset_dir / preset.input_file).read_text(encoding="utf-8"), report=report)
