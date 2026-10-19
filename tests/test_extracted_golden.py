"""Golden numbers against the real sources (Issues #4, #5); skipped without the local cache."""


import pytest

from kb_build.extract.models import ExtractedSource, merge_sources
from kb_build.extract.run import ADAPTERS
from kb_build.paths import BuildPaths
from kb_build.source_fetch import fetch_to_cache, load_sources_json, read_cached

PATHS = BuildPaths()
SPECS = load_sources_json(PATHS.sources_json)
CACHE = PATHS.source_cache


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


def test_cis_exactly_70_recommendations_and_54_candidates() -> None:
    reqs = extract_cached("cis.json").requirements
    assert len(reqs) == 70
    assert sum(r.prefilter_passed for r in reqs) == 54  # chapters 2, 3, 4 and 6


def test_fsbp_all_286_controls_and_150_candidates() -> None:
    reqs = {r.id: r for r in extract_cached("fsbp.json").requirements}
    assert len(reqs) == 286
    assert sum(r.prefilter_passed for r in reqs.values()) == 150  # 125 + 25 EC2 (VPC types)
    assert reqs["SNS.1"].primary_anchor == "AWS FSBP SNS.1"
    assert reqs["EC2.2"].prefilter_passed  # default security group
    assert not reqs["CloudFront.1"].prefilter_passed


def test_c5_all_610_criteria_and_300_candidates() -> None:
    reqs = {r.id: r for r in extract_cached("c5.json").requirements}
    assert len(reqs) == 610
    assert sum(r.prefilter_passed for r in reqs.values()) == 300
    assert reqs["CRY-03.01B"].primary_anchor == "BSI C5 CRY-03.01B"
    assert reqs["CRY-03.01B"].prefilter_passed


def test_dsgvo_exactly_99_articles_and_chapters_2_to_5_as_candidates() -> None:
    reqs = {r.id: r for r in extract_cached("dsgvo.json").requirements}
    assert len(reqs) == 99
    assert [rid for rid, r in reqs.items() if r.prefilter_passed] == [
        f"Art. {n}" for n in range(5, 51)  # chapter V ends with Art. 50
    ]
    assert reqs["Art. 32"].title == "Sicherheit der Verarbeitung"
    assert reqs["Art. 32"].text.startswith("(1) Unter Berücksichtigung des Stands der Technik")


def test_ki_vo_all_119_articles_and_the_8_of_issue_52_as_candidates() -> None:
    reqs = {r.id: r for r in extract_cached("ki-vo.json").requirements}
    assert len(reqs) == 119  # 113 plus Art. 4a, 60a, 75a-75d of the 2026 amendment
    assert [rid for rid, r in reqs.items() if r.prefilter_passed] == [
        f"Art. {n}" for n in (4, 5, 6, 13, 14, 26, 27, 50)
    ]
    assert reqs["Art. 50"].title == (
        "Transparenzpflichten für Anbieter und Betreiber bestimmter KI-Systeme")
    assert reqs["Art. 6"].primary_anchor == "KI-VO Art. 6"


def test_sdm_all_147_measures_pass_the_prefilter() -> None:
    reqs = {r.id: r for r in extract_cached("sdm.json").requirements}
    assert len(reqs) == 147
    assert sum(r.prefilter_passed for r in reqs.values()) == 147  # all layers D, S, P
    assert reqs["M60.D01"].text.startswith("Datenstrukturen und Speicherarten, die das Löschen")
    assert reqs["M60.D01"].primary_anchor == "SDM Löschen M60.D01"


def test_checked_in_extracts_match_a_fresh_build() -> None:
    for filename in ("bsi.json", "dsgvo.json", "ki-vo.json", "sdm.json"):
        checked_in = (PATHS.extracted / filename).read_text(encoding="utf-8")
        assert ExtractedSource.model_validate_json(checked_in).requirements == (
            extract_cached(filename).requirements
        ), filename
