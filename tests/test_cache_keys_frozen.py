"""Frozen catalog (ADR 0025, 0027): a refactoring changes neither prompts nor cache keys."""

import json
from pathlib import Path

import pytest

from kb_build.build_inputs import read_scope
from kb_build.decompose.split import DecompositionCache, request_version
from kb_build.paths import BuildPaths
from kb_build.select.classify import build_deps
from kb_build.select.classify import request_version as classify_version
from kb_build.select.judgement_cache import JudgementCache

PATHS = BuildPaths()


def versions_in(path: Path) -> set[str]:
    """The prompt version is the middle part of each key: text hash | version | model_id."""
    return {key.split("|")[1] for key in json.loads(path.read_text(encoding="utf-8"))}


@pytest.mark.parametrize("audit_type", ["architecture", "spec"])
def test_the_classification_prompt_matches_the_checked_in_cache(audit_type: str) -> None:
    scope = read_scope(PATHS.scope) if audit_type == "architecture" else None

    version = classify_version(build_deps(audit_type, scope))  # type: ignore[arg-type]

    assert version in versions_in(PATHS.judgement_cache)


def test_the_decomposition_prompt_matches_the_checked_in_cache() -> None:
    assert request_version() in versions_in(PATHS.decomposition_cache)


@pytest.mark.parametrize(("cache", "path"), [
    (JudgementCache, PATHS.judgement_cache),
    (DecompositionCache, PATHS.decomposition_cache),
])
def test_a_checked_in_cache_is_written_back_byte_for_byte(cache, path) -> None:
    raw = path.read_bytes()

    assert cache.from_json(raw.decode("utf-8")).to_json() == raw
