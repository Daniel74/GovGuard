"""Writes selection list and selection protocol (ADR 0011). Gets the model injected (ADR 0005)."""

from pathlib import Path

from pydantic import TypeAdapter
from pydantic_ai.models import Model

from govguard.models import AuditType, Preset, SourceName
from kb_build.archetype_profiles import load_profiles
from kb_build.classify import Judge
from kb_build.curation import curate, pinned_anchors
from kb_build.extracted_models import ExtractedSource
from kb_build.judgement_cache import JudgementCache
from kb_build.scope import load_scope, scope_types
from kb_build.selection_models import Verdict

CACHE_NAME = "judgement_cache.json"

# audit type -> (output file, extracted sources in catalog order)
SELECTIONS: dict[AuditType, tuple[str, list[SourceName]]] = {
    "architecture": ("selection_arch.json", ["BSI", "C5", "CIS", "FSBP"]),
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
    """Per audit type (or just `only`): selection list plus the selection protocol.

    The cache is saved even if a gate aborts the build: the answers are paid for.
    """
    out_dir = out_dir or data / "knowledge_base"
    cache = JudgementCache.load(out_dir / CACHE_NAME)
    try:
        for audit_type, (filename, names) in SELECTIONS.items():
            if only and audit_type != only:
                continue
            _select(audit_type, names, filename, model, data, out_dir, cache)
    finally:
        cache.save(out_dir / CACHE_NAME)


def _select(  # noqa: PLR0913 (one call site; the arguments are the run's context)
    audit_type: AuditType, names: list[SourceName], filename: str,
    model: Model, data: Path, out_dir: Path, cache: JudgementCache,
) -> None:
    profiles, presets = load_profiles(data / "archetype_profiles.json"), _read_presets(data)
    scope = load_scope(data / "scope.json")
    components = frozenset(t for p in profiles for t in p.required_types)
    judge = Judge(audit_type, model, scope, cache)
    result = curate(
        judge, _read_sources(data, names), pinned_anchors(presets, audit_type),
        scope_types(data / "scope.json"), components,
    )
    out_dir.mkdir(parents=True, exist_ok=True)  # only after a successful run
    (out_dir / filename).write_text(result.selection.model_dump_json(indent=2) + "\n", "utf-8")
    protocol = TypeAdapter(list[Verdict]).dump_json(result.verdicts, indent=2)
    (out_dir / filename.replace("selection_", "verdicts_")).write_bytes(protocol + b"\n")
