import pytest

from kb_build.extract.c5 import AREAS, extract

VERSION = "5.44.0"
REASON = "Bereich gehört nicht zu COS, CRY, IAM, OPS, PSS."


def criterion(rid: str) -> dict:
    """Minimal entry as in Prowler `c5_aws.json` (no title, only text and a subsection)."""
    return {
        "Id": rid,
        "Description": f"The  provider  reviews **{rid}**.",
        "Attributes": [
            {
                "Section": "Cryptography and Key Management (CRY)",
                "SubSection": f"{rid[:6]} Review of  Practices",
                "Type": "Basic",
            }
        ],
    }


def extract_by_id(*ids: str) -> dict:
    c5 = {"Framework": "C5", "Version": "2025", "Requirements": [criterion(rid) for rid in ids]}
    return {r.id: r for r in extract("memory://c5", c5, VERSION).requirements}


def test_cry_03_01b_has_facts_anchor_and_clean_text() -> None:
    cry = extract_by_id("CRY-03.01B")["CRY-03.01B"]
    assert cry.attributes == {"area": "CRY"}
    assert cry.primary_anchor == "BSI C5 CRY-03.01B"
    assert cry.title == "CRY-03 Review of Practices"
    assert cry.text == "The provider reviews CRY-03.01B."


def test_source_is_c5_and_version_comes_from_sources_json() -> None:
    extracted = extract("memory://c5", {"Requirements": [criterion("CRY-03.01B")]}, VERSION)
    assert (extracted.source, extracted.version) == ("C5", VERSION)


@pytest.mark.parametrize(
    "rid", ["OPS-01.01B", "IAM-01.01B", "CRY-03.01B", "COS-01.01B", "PSS-01.01B"]
)
def test_prefilter_keeps_the_five_areas(rid: str) -> None:
    kept = extract_by_id(rid)[rid]
    assert kept.prefilter_passed
    assert kept.prefilter_reason is None


@pytest.mark.parametrize("rid", ["OIS-01.01B", "PS-01.01B", "HR-01.01B", "DEV-01.01B"])
def test_prefilter_rejects_other_areas_with_a_reason(rid: str) -> None:
    rejected = extract_by_id(rid)[rid]
    assert not rejected.prefilter_passed
    assert rejected.prefilter_reason == REASON


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="CRY-03.01B"):
        extract_by_id("CRY-03.01B", "CRY-03.01B")


def test_areas_are_pinned_to_architecture_1_1() -> None:
    # Changing this set changes the rule, not just the code: update ARCHITECTURE 1.1 first.
    assert AREAS == {"OPS", "IAM", "CRY", "COS", "PSS"}
