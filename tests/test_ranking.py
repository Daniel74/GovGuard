"""Relevance, pinned slots and round-robin ranking (ARCHITECTURE 1.1, ADR 0007). Pure code."""

import pytest

from kb_build.extracted_models import Requirement
from kb_build.ranking import Candidate, rank_source
from kb_build.selection_models import Classification

PROFILE_TYPES = {"AWS::S3::Bucket", "AWS::Lambda::Function", "AWS::KMS::Key"}


def candidate(rid: str, types: list[str] | None = None, **attributes) -> Candidate:
    requirement = Requirement(
        id=rid, title="t", text="x", primary_anchor=f"A {rid}",
        attributes=attributes, prefilter_passed=True,
    )
    return Candidate(requirement, Classification(
        testable=True, rationale=f"why {rid}", cfn_resource_types=types or [],
    ))


def ids(selected) -> list[str]:
    return [s.requirement_id for s in selected]


def test_architecture_keeps_only_requirements_touching_a_profile_resource_type() -> None:
    candidates = [
        candidate("3.1.4", ["AWS::S3::Bucket"], level=1, automated=True),
        candidate("2.1.1", ["AWS::Organizations::Account"], level=1, automated=True),
        candidate("2.1.2", [], level=1, automated=True),
    ]

    selected = rank_source("CIS", candidates, relevant_types=PROFILE_TYPES)

    assert selected[0].model_dump() == {
        "requirement_id": "3.1.4", "source": "CIS", "rationale": "why 3.1.4",
        "cfn_resource_types": ["AWS::S3::Bucket"], "pinned": False, "rank": 1,
    }
    assert ids(selected) == ["3.1.4"]


def cis(rid: str, type_: str) -> Candidate:
    return candidate(rid, [type_], level=1, automated=True)


def test_round_robin_over_resource_types_until_the_cap() -> None:
    candidates = [
        cis("3.1.1", "AWS::S3::Bucket"), cis("3.1.2", "AWS::S3::Bucket"),
        cis("3.1.3", "AWS::S3::Bucket"),
        cis("3.2.1", "AWS::Lambda::Function"), cis("3.2.2", "AWS::Lambda::Function"),
        cis("3.3.1", "AWS::KMS::Key"),
    ]

    selected = rank_source("CIS", candidates, relevant_types=PROFILE_TYPES, cap=5)

    assert ids(selected) == ["3.1.1", "3.2.1", "3.3.1", "3.1.2", "3.2.2"]
    assert [s.rank for s in selected] == [1, 2, 3, 4, 5]


def test_relevance_looks_at_the_first_type_only() -> None:
    # CloudTrail is no archetype building block; a later S3 type must not smuggle the rule in
    trail_first = candidate("4.8", ["AWS::CloudTrail::Trail", "AWS::S3::Bucket"],
                            level=1, automated=True)
    candidates = [trail_first, cis("3.1.1", "AWS::S3::Bucket")]

    selected = rank_source("CIS", candidates, relevant_types=PROFILE_TYPES)

    assert ids(selected) == ["3.1.1"]


def test_a_requirement_with_several_types_counts_for_its_first_type() -> None:
    multi = candidate("3.9.1", ["AWS::Lambda::Function", "AWS::S3::Bucket"],
                      level=1, automated=True)
    candidates = [multi, cis("3.1.1", "AWS::S3::Bucket"), cis("3.2.1", "AWS::Lambda::Function")]

    selected = rank_source("CIS", candidates, relevant_types=PROFILE_TYPES, cap=3)

    # Lambda group = [3.2.1, 3.9.1]; 3.9.1 comes second in its group, not first in the S3 group
    assert ids(selected) == ["3.1.1", "3.2.1", "3.9.1"]


def test_dsgvo_rotates_over_chapters() -> None:
    candidates = [
        candidate(rid, chapter=chapter, fine_tier=4)
        for rid, chapter in [("Art. 5", 2), ("Art. 6", 2), ("Art. 12", 3), ("Art. 32", 4)]
    ]

    selected = rank_source("DSGVO", candidates, cap=3)

    assert ids(selected) == ["Art. 5", "Art. 12", "Art. 32"]


def test_sdm_rotates_over_modules() -> None:
    candidates = [
        candidate(rid, module=rid[:3], layer="D") for rid in ["M60.D01", "M60.D02", "M50.D01"]
    ]

    selected = rank_source("SDM", candidates, cap=3)

    assert ids(selected) == ["M50.D01", "M60.D01", "M60.D02"]


def test_bsi_orders_by_cia_sum_then_natural_id() -> None:
    bucket = ["AWS::S3::Bucket"]
    candidates = [
        candidate("DET.1.1", bucket, cia_sum=3),
        candidate("DET.3.10", bucket, cia_sum=5),
        candidate("DET.3.2", bucket, cia_sum=5),
    ]

    selected = rank_source("BSI", candidates, relevant_types=PROFILE_TYPES)

    assert ids(selected) == ["DET.3.2", "DET.3.10", "DET.1.1"]


def test_cis_orders_level_1_before_2_then_automated_before_manual() -> None:
    bucket = ["AWS::S3::Bucket"]
    candidates = [
        candidate("3.1.1", bucket, level=2, automated=True),
        candidate("3.1.2", bucket, level=1, automated=False),
        candidate("3.1.3", bucket, level=1, automated=True),
    ]

    selected = rank_source("CIS", candidates, relevant_types=PROFILE_TYPES)

    assert ids(selected) == ["3.1.3", "3.1.2", "3.1.1"]


def test_dsgvo_orders_higher_fine_tier_first() -> None:
    candidates = [
        candidate("Art. 5", chapter=2, fine_tier=0),
        candidate("Art. 6", chapter=2, fine_tier=2),
        candidate("Art. 32", chapter=2, fine_tier=4),
    ]

    assert ids(rank_source("DSGVO", candidates)) == ["Art. 32", "Art. 6", "Art. 5"]


def test_sdm_orders_data_layer_before_systems() -> None:
    candidates = [
        candidate("M60.S01", module="M60", layer="S"),
        candidate("M60.D02", module="M60", layer="D"),
    ]

    assert ids(rank_source("SDM", candidates)) == ["M60.D02", "M60.S01"]


def test_pinned_slots_come_first_skip_relevance_and_count_towards_the_cap() -> None:
    candidates = [
        cis("3.1.1", "AWS::S3::Bucket"),
        cis("3.2.1", "AWS::Lambda::Function"),
        cis("3.3.1", "AWS::KMS::Key"),
        candidate("4.6", ["AWS::CloudTrail::Trail"], level=2, automated=True),  # not relevant
    ]

    selected = rank_source(
        "CIS", candidates, relevant_types=PROFILE_TYPES, cap=3, pinned_ids={"4.6"}
    )

    assert ids(selected) == ["4.6", "3.1.1", "3.2.1"]
    assert [(s.pinned, s.rank) for s in selected] == [(True, 1), (False, 2), (False, 3)]


def test_more_pinned_slots_than_the_cap_is_an_error() -> None:
    candidates = [cis("3.1.1", "AWS::S3::Bucket"), cis("3.2.1", "AWS::Lambda::Function")]

    with pytest.raises(ValueError, match="cap"):
        rank_source("CIS", candidates, cap=1, pinned_ids={"3.1.1", "3.2.1"})


def test_a_pinned_slot_without_candidate_is_an_error() -> None:
    with pytest.raises(ValueError, match="9.9.9"):
        rank_source("CIS", [cis("3.1.1", "AWS::S3::Bucket")], pinned_ids={"9.9.9"})
