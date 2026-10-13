"""Writes selection list and selection protocol (ADR 0011). Gets the model injected (ADR 0005).

The file I/O of the selection lives here: sources, presets, scope and cache in, results out.
"""

import logging
from pathlib import Path

from pydantic import TypeAdapter
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, Preset, SourceName
from kb_build.extract.models import ExtractedSource
from kb_build.gates import pinned_anchors
from kb_build.paths import BuildPaths
from kb_build.reference.archetype_profiles import load_profiles
from kb_build.reference.run import read_scope
from kb_build.select.classify import Judge
from kb_build.select.curation import curate
from kb_build.select.judgement_cache import JudgementCache
from kb_build.select.models import Verdict

logger = logging.getLogger("kb_build")

# audit type -> extracted sources in catalog order
SELECTIONS: dict[AuditType, list[SourceName]] = {
    "architecture": ["BSI", "C5", "CIS", "FSBP"],
    "spec": ["DSGVO", "SDM"],
}


def chosen(only: AuditType | None) -> list[AuditType]:
    """Every audit type, or just `only`."""
    return [audit_type for audit_type in SELECTIONS if only in (None, audit_type)]


def read_sources(extracted: Path, names: list[SourceName]) -> list[ExtractedSource]:
    paths = [extracted / f"{name.lower()}.json" for name in names]
    return [ExtractedSource.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def _read_presets(presets: Path) -> list[Preset]:
    paths = sorted(presets.glob("*/preset.json"))
    return [Preset.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def _read_cache(path: Path) -> JudgementCache:
    if not path.exists():
        return JudgementCache()
    return JudgementCache.from_json(path.read_text(encoding="utf-8"))


def _write_cache(cache: JudgementCache, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(cache.to_json())


def _log_usage(audit_type: AuditType, usage: RunUsage) -> None:
    logger.info("%s: %d requests, %d input tokens, %d output tokens", audit_type,
                usage.requests, usage.input_tokens, usage.output_tokens)


def select_all(
    model: Model, paths: BuildPaths = BuildPaths(), only: AuditType | None = None
) -> None:
    """Per audit type (or just `only`): selection list plus the selection protocol.

    The cache is saved even if a gate aborts the build: the answers are paid for.
    """
    cache = _read_cache(paths.judgement_cache)
    try:
        for audit_type in chosen(only):
            _select(audit_type, model, paths, cache)
    finally:
        _write_cache(cache, paths.judgement_cache)


def _select(audit_type: AuditType, model: Model, paths: BuildPaths, cache: JudgementCache) -> None:
    names = SELECTIONS[audit_type]
    profiles = load_profiles(paths.archetype_profiles)
    components = frozenset(t for p in profiles for t in p.required_types)
    pinned = pinned_anchors(_read_presets(paths.presets), audit_type)
    judge = Judge(audit_type, model, read_scope(paths.scope), cache)  # it strips by scope
    try:
        result = curate(judge, read_sources(paths.extracted, names), pinned, components)
    finally:
        _log_usage(audit_type, judge.usage)
    selection_file = paths.out_file("selection", audit_type)
    selection_file.parent.mkdir(parents=True, exist_ok=True)  # only after a successful run
    selection_file.write_text(result.selection.model_dump_json(indent=2) + "\n", encoding="utf-8")
    protocol = TypeAdapter(list[Verdict]).dump_json(result.verdicts, indent=2)
    paths.out_file("verdicts", audit_type).write_bytes(protocol + b"\n")
