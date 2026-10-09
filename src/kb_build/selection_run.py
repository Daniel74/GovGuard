"""Writes the selection lists (issue #6). Reads files, gets the model injected (ADR 0005)."""

from pathlib import Path

from pydantic import TypeAdapter
from pydantic_ai.models import Model

from govguard.models import AuditType, Preset, SourceName
from kb_build.archetype_profiles import load_profiles
from kb_build.curation import curate, pinned_anchors
from kb_build.extracted_models import ExtractedSource
from kb_build.selection_models import Verdict

# audit type -> (output file, extracted sources in catalog order)
SELECTIONS: dict[AuditType, tuple[str, list[SourceName]]] = {
    "architecture": ("selection_arch.json", ["BSI", "CIS"]),
    "spec": ("selection_spec.json", ["DSGVO", "SDM"]),
}


def _read_sources(data: Path, names: list[SourceName]) -> list[ExtractedSource]:
    paths = [data / "extracted" / f"{name.lower()}.json" for name in names]
    return [ExtractedSource.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def _read_presets(data: Path) -> list[Preset]:
    paths = sorted((data / "presets").glob("*/preset.json"))
    return [Preset.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def select_all(
    model: Model,
    data: Path = Path("data"),
    out_dir: Path | None = None,
    only: AuditType | None = None,
) -> None:
    """Per audit type (or just `only`): selection list plus a local verdict report."""
    out_dir = out_dir or data / "knowledge_base"
    profiles, presets = load_profiles(data / "archetype_profiles.json"), _read_presets(data)
    for audit_type, (filename, names) in SELECTIONS.items():
        if only and audit_type != only:
            continue
        result = curate(
            audit_type, _read_sources(data, names), pinned_anchors(presets, audit_type),
            profiles, model,
        )
        out_dir.mkdir(parents=True, exist_ok=True)  # only after a successful run
        (out_dir / filename).write_text(result.selection.model_dump_json(indent=2) + "\n", "utf-8")
        report = TypeAdapter(list[Verdict]).dump_json(result.verdicts, indent=2)
        (out_dir / filename.replace("selection_", "verdicts_")).write_bytes(report + b"\n")
