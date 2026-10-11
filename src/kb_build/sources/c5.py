"""BSI C5:2025 adapter: Prowler `c5_aws.json` -> ExtractedSource (pure, no I/O)."""

from typing import Any

from kb_build.extracted_models import ExtractedSource, Requirement
from kb_build.sources import prowler
from kb_build.sources.prowler import ProwlerFormat, strip_markdown

AREAS = frozenset({"OPS", "IAM", "CRY", "COS", "PSS"})  # ARCHITECTURE 1.1


def prefilter(requirement: Requirement) -> str | None:
    """Keeps the areas OPS, IAM, CRY, COS and PSS (ARCHITECTURE 1.1)."""
    if requirement.attributes.get("area") in AREAS:
        return None
    return f"Bereich gehört nicht zu {', '.join(sorted(AREAS))}."


FORMAT = ProwlerFormat(
    source="C5",
    anchor=lambda rid, version: f"BSI C5 {rid}",
    title=lambda entry: strip_markdown(entry["Attributes"][0]["SubSection"]),  # C5 has no title
    text=lambda entry: strip_markdown(entry["Description"]),
    attributes=lambda entry: {"area": entry["Id"].split("-", 1)[0]},
    prefilter=prefilter,
)


def extract(origin: str, data: dict[str, Any], version: str) -> ExtractedSource:
    """All criteria; `version` is the Prowler tag from data/sources.json (C5 itself says 2025)."""
    return prowler.extract(FORMAT, origin, data, version)
