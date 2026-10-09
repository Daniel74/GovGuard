"""Archetype profiles (ARCHITECTURE 1.4): hand-maintained input of the relevance filter."""

from pathlib import Path

from pydantic import BaseModel, TypeAdapter

from govguard.models import ArchetypeId

PROFILES_FILE = Path("data/archetype_profiles.json")


class ArchetypeProfile(BaseModel):
    id: ArchetypeId
    name: str
    purpose: str  # German, shown to humans only
    constructs: list[str]
    required_types: list[str]
    resource_types: list[str]  # required types plus IAM role, KMS key, log group


def load_profiles(path: Path = PROFILES_FILE) -> list[ArchetypeProfile]:
    return TypeAdapter(list[ArchetypeProfile]).validate_json(path.read_text(encoding="utf-8"))


def relevant_resource_types(profiles: list[ArchetypeProfile]) -> set[str]:
    """Relevance filter (ADR 0007): a requirement counts only if it touches one of these."""
    return {t for profile in profiles for t in profile.resource_types}
