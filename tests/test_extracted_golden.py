"""Golden numbers against the real sources (Issues #4, #5); skipped without the local cache."""

from pathlib import Path

import pytest

from kb_build.__main__ import ADAPTERS
from kb_build.extracted_models import ExtractedSource, merge_sources
from kb_build.source_fetch import fetch_to_cache, load_sources_json, read_cached

ROOT = Path(__file__).parent.parent
SPECS = load_sources_json(ROOT / "data/sources.json")
CACHE = ROOT / "data/sources"


def extract_cached(filename: str) -> ExtractedSource:
    adapter, keys = ADAPTERS[filename]
    parts = []
    for spec in (SPECS[key] for key in keys):
        if not (CACHE / spec.filename).exists():
            pytest.skip(f"{spec.filename} not cached, run python -m kb_build")
        path = fetch_to_cache(spec, cache_dir=CACHE)  # cache hit: verifies SHA-256, no HTTP
        parts.append(adapter.extract(str(path), read_cached(path), spec.version))
    return merge_sources(parts)


def test_bsi_all_1000_controls_and_380_candidates() -> None:
    reqs = extract_cached("bsi.json").requirements
    assert len(reqs) == 1000
    assert sum(r.prefilter_passed for r in reqs) == 380


def test_cis_exactly_70_recommendations_and_45_candidates() -> None:
    reqs = extract_cached("cis.json").requirements
    assert len(reqs) == 70
    assert sum(r.prefilter_passed for r in reqs) == 45


def test_dsgvo_exactly_99_articles_and_chapters_2_to_5_as_candidates() -> None:
    reqs = {r.id: r for r in extract_cached("dsgvo.json").requirements}
    assert len(reqs) == 99
    assert [rid for rid, r in reqs.items() if r.prefilter_passed] == [
        f"Art. {n}" for n in range(5, 51)  # chapter V ends with Art. 50
    ]
    assert reqs["Art. 32"].title == "Sicherheit der Verarbeitung"
    assert reqs["Art. 32"].text.startswith("(1) Unter Berücksichtigung des Stands der Technik")


def test_sdm_all_147_measures_and_55_data_or_system_candidates() -> None:
    reqs = {r.id: r for r in extract_cached("sdm.json").requirements}
    assert len(reqs) == 147
    assert sum(r.prefilter_passed for r in reqs.values()) == 55
    assert reqs["M60.D01"].text.startswith("Datenstrukturen und Speicherarten, die das Löschen")
    assert reqs["M60.D01"].primary_anchor == "SDM Löschen M60.D01"


def test_checked_in_extracts_match_a_fresh_build() -> None:
    for filename in ("bsi.json", "dsgvo.json", "sdm.json"):
        checked_in = (ROOT / "data/extracted" / filename).read_text(encoding="utf-8")
        assert ExtractedSource.model_validate_json(checked_in).requirements == (
            extract_cached(filename).requirements
        ), filename
