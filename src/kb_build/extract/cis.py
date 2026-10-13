"""CIS AWS v7 adapter: Prowler `cis_7.0_aws.json` -> ExtractedSource (pure, no I/O)."""

from typing import Any

from kb_build.extracted_models import ExtractedSource, Requirement
from kb_build.sources import prowler
from kb_build.sources.prowler import ProwlerFormat, strip_markdown

# Networking holds the security groups for Aurora (ARCHITECTURE 1.1)
CHAPTERS = {2: "IAM", 3: "Storage", 4: "Logging", 6: "Networking"}
LEVELS = {"Level 1": 1, "Level 2": 2}
ASSESSMENT = {"Automated": True, "Manual": False}


def _attributes(entry: dict[str, Any]) -> dict[str, int | bool]:
    details = entry["Attributes"][0]
    facts = {
        "chapter": int(entry["Id"].split(".", 1)[0]),
        "level": LEVELS.get(details.get("Profile")),
        "automated": ASSESSMENT.get(details.get("AssessmentStatus")),
    }
    return {key: value for key, value in facts.items() if value is not None}


def prefilter(requirement: Requirement) -> str | None:
    """Keeps chapters 2 IAM, 3 Storage, 4 Logging and 6 Networking (ARCHITECTURE 1.1)."""
    if requirement.attributes.get("chapter") in CHAPTERS:
        return None
    chapters = ", ".join(f"{number} {name}" for number, name in CHAPTERS.items())
    return f"Kapitel gehört nicht zu {chapters}."


FORMAT = ProwlerFormat(
    source="CIS",
    anchor=lambda rid, version: f"CIS AWS {version} {rid}",
    title=lambda entry: strip_markdown(entry["Description"]),
    text=lambda entry: strip_markdown(entry["Attributes"][0]["Description"]),
    attributes=_attributes,
    prefilter=prefilter,
)


def extract(origin: str, data: dict[str, Any], version: str) -> ExtractedSource:
    """All 70 recommendations; `version` from data/sources.json, Prowler only says "7.0"."""
    return prowler.extract(FORMAT, origin, data, version)
