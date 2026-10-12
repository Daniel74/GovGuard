"""Writes selection list and selection protocol (ADR 0011). Gets the model injected (ADR 0005).

The file I/O of the selection lives here: sources, presets, scope and cache in, results out.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from pydantic import TypeAdapter
from pydantic_ai.models import Model
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType, Preset, SourceName
from kb_build.archetype_profiles import load_profiles
from kb_build.classify import Judge
from kb_build.curation import curate
from kb_build.extracted_models import ExtractedSource
from kb_build.gates import pinned_anchors
from kb_build.judgement_cache import JudgementCache
from kb_build.scope import Scope
from kb_build.selection_models import Verdict

logger = logging.getLogger("kb_build")

# audit type -> extracted sources in catalog order
SELECTIONS: dict[AuditType, list[SourceName]] = {
    "architecture": ["BSI", "C5", "CIS", "FSBP"],
    "spec": ["DSGVO", "SDM"],
}
_FILE_SUFFIX: dict[AuditType, str] = {"architecture": "arch", "spec": "spec"}
OutputKind = Literal["selection", "verdicts", "rules"]


@dataclass(frozen=True)
class BuildPaths:
    data: Path = Path("data")
    out_dir: Path = Path("data/knowledge_base")  # deployed to S3: results only, no cache
    cache_file: Path = Path("data/judgement_cache.json")

    def out_file(self, kind: OutputKind, audit_type: AuditType) -> Path:
        """E.g. selection_arch.json, verdicts_spec.json, rules_arch.json."""
        return self.out_dir / f"{kind}_{_FILE_SUFFIX[audit_type]}.json"


def chosen(only: AuditType | None) -> list[AuditType]:
    """Every audit type, or just `only`."""
    return [audit_type for audit_type in SELECTIONS if only in (None, audit_type)]


def read_sources(data: Path, names: list[SourceName]) -> list[ExtractedSource]:
    paths = [data / "extracted" / f"{name.lower()}.json" for name in names]
    return [ExtractedSource.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def _read_presets(data: Path) -> list[Preset]:
    paths = sorted((data / "presets").glob("*/preset.json"))
    return [Preset.model_validate_json(p.read_text(encoding="utf-8")) for p in paths]


def _read_scope(data: Path) -> Scope:
    return Scope(json.loads((data / "scope.json").read_text(encoding="utf-8")))


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
    cache = _read_cache(paths.cache_file)
    try:
        for audit_type in chosen(only):
            _select(audit_type, model, paths, cache)
    finally:
        _write_cache(cache, paths.cache_file)


def _select(audit_type: AuditType, model: Model, paths: BuildPaths, cache: JudgementCache) -> None:
    names = SELECTIONS[audit_type]
    profiles = load_profiles(paths.data / "archetype_profiles.json")
    components = frozenset(t for p in profiles for t in p.required_types)
    pinned = pinned_anchors(_read_presets(paths.data), audit_type)
    scope = _read_scope(paths.data)
    judge = Judge(audit_type, model, scope, cache)
    try:
        result = curate(judge, read_sources(paths.data, names), pinned, scope, components)
    finally:
        _log_usage(audit_type, judge.usage)
    paths.out_dir.mkdir(parents=True, exist_ok=True)  # only after a successful run
    selection = result.selection.model_dump_json(indent=2) + "\n"
    paths.out_file("selection", audit_type).write_text(selection, encoding="utf-8")
    protocol = TypeAdapter(list[Verdict]).dump_json(result.verdicts, indent=2)
    paths.out_file("verdicts", audit_type).write_bytes(protocol + b"\n")
