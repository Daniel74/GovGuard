"""CIS AWS v7 adapter: Prowler `cis_7.0_aws.json` -> ExtractedSource (pure, no I/O)."""

from typing import Any

from govguard.text import normalize
from kb_build.extracted_models import ExtractedSource, Requirement, mark_prefilter

CHAPTERS = frozenset({2, 3, 4})  # IAM, Storage, Logging (ARCHITECTURE 1.1)
LEVELS = {"Level 1": 1, "Level 2": 2}
ASSESSMENT = {"Automated": True, "Manual": False}


def _strip_markdown(text: str) -> str:
    # ADR 0008: anchors are checked against the Prowler text without markdown markers
    return normalize(text.replace("**", "").replace("`", ""))


def _attributes(rid: str, details: dict[str, Any]) -> dict[str, int | bool]:
    facts = {
        "chapter": int(rid.split(".", 1)[0]),
        "level": LEVELS.get(details.get("Profile")),
        "automated": ASSESSMENT.get(details.get("AssessmentStatus")),
    }
    return {key: value for key, value in facts.items() if value is not None}


def _requirement(entry: dict[str, Any], version: str) -> Requirement:
    rid = entry["Id"]
    details = entry["Attributes"][0]
    return Requirement(
        id=rid,
        title=_strip_markdown(entry["Description"]),
        text=_strip_markdown(details["Description"]),
        primary_anchor=f"CIS AWS {version} {rid}",
        attributes=_attributes(rid, details),
        prefilter_passed=False,
    )


def prefilter(requirement: Requirement) -> bool:
    """Keeps chapters 2 IAM, 3 Storage and 4 Logging (ARCHITECTURE 1.1)."""
    return requirement.attributes.get("chapter") in CHAPTERS


def extract(origin: str, prowler: dict[str, Any], version: str) -> ExtractedSource:
    """All 70 recommendations; `version` from data/sources.json, Prowler only says "7.0"."""
    requirements = [_requirement(entry, version) for entry in prowler["Requirements"]]
    return ExtractedSource(
        source="CIS", version=version, origin=origin,
        requirements=mark_prefilter(requirements, prefilter),
    )
