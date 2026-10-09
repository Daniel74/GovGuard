"""Golden numbers against the real sources (Issue #4); skipped without the local cache."""

import json
from pathlib import Path

import pytest

from kb_build.source_fetch import fetch_to_cache, load_sources_json
from kb_build.sources import bsi, cis

ROOT = Path(__file__).parent.parent
SPECS = load_sources_json(ROOT / "data/sources.json")
CACHE = ROOT / "data/sources"


def extract_cached(key: str, adapter):
    spec = SPECS[key]
    if not (CACHE / spec.filename).exists():
        pytest.skip(f"{spec.filename} not cached, run python -m kb_build")
    path = fetch_to_cache(spec, cache_dir=CACHE)  # cache hit: verifies SHA-256, no HTTP
    return adapter.extract(str(path), json.loads(path.read_text(encoding="utf-8")), spec.version)


def test_bsi_all_1000_controls_and_380_candidates() -> None:
    reqs = extract_cached("bsi_gspp_oscal", bsi).requirements
    assert len(reqs) == 1000
    assert sum(r.prefilter_passed for r in reqs) == 380


def test_cis_exactly_70_recommendations_and_45_candidates() -> None:
    reqs = extract_cached("cis_aws_v7_prowler", cis).requirements
    assert len(reqs) == 70
    assert sum(r.prefilter_passed for r in reqs) == 45
