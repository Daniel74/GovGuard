import pytest

from kb_build.sources.cis import extract

VERSION = "v7.0.0"


def recommendation(rid: str) -> dict:
    """Minimal entry as in Prowler `cis_7.0_aws.json`."""
    return {
        "Id": rid,
        "Description": f"Ensure **{rid}** is `on`",
        "Attributes": [
            {
                "Description": f"Text  for {rid} with **bold** and `code`.",
                "Profile": "Level 1",
                "AssessmentStatus": "Automated",
            }
        ],
    }


def extract_by_id(*ids: str) -> dict:
    cis = {"Version": "7.0", "Requirements": [recommendation(rid) for rid in ids]}
    return {r.id: r for r in extract("memory://cis", cis, VERSION).requirements}


def test_3_1_4_has_facts_anchor_and_clean_text() -> None:
    rec = extract_by_id("3.1.4")["3.1.4"]
    assert rec.attributes == {"chapter": 3, "level": 1, "automated": True}
    assert rec.primary_anchor == "CIS AWS v7.0.0 3.1.4"
    assert rec.title == "Ensure 3.1.4 is on"
    assert rec.text == "Text for 3.1.4 with bold and code."


def test_version_comes_from_sources_json_not_prowler() -> None:
    cis = {"Version": "7.0", "Requirements": [recommendation("3.1.4")]}
    assert extract("memory://cis", cis, VERSION).version == VERSION


@pytest.mark.parametrize(
    ("rid", "passed"),
    [("1.1", False), ("2.1.1", True), ("3.1.4", True), ("4.1", True), ("5.1", False)],
)
def test_prefilter_keeps_chapters_2_3_4(rid: str, passed: bool) -> None:
    assert extract_by_id(rid)[rid].prefilter_passed is passed


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="3.1.4"):
        extract_by_id("3.1.4", "3.1.4")
