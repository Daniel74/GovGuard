"""Relevance, pinned slots and round-robin ranking (ARCHITECTURE 1.1, ADR 0007). Pure code."""

import re
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass

from govguard.models import SourceName
from kb_build.extracted_models import Requirement
from kb_build.selection_models import Classification, SelectedRequirement

CAPS: dict[SourceName, int] = {"BSI": 12, "CIS": 12, "DSGVO": 16, "SDM": 8}  # ADR 0002


@dataclass(frozen=True)
class Candidate:
    requirement: Requirement
    classification: Classification


def _natural(text: str) -> list[str | int]:
    """'Art. 5' sorts before 'Art. 32'; split() alternates text and numbers."""
    return [int(part) if part.isdigit() else part for part in re.split(r"(\d+)", text)]


# Best first within a group (ARCHITECTURE 1.1); ties are broken by the natural ID order
CRITERIA: dict[SourceName, Callable[[dict], tuple]] = {
    "BSI": lambda a: (-a["cia_sum"],),
    "CIS": lambda a: (a["level"], not a["automated"]),
    "DSGVO": lambda a: (-a["fine_tier"],),
    "SDM": lambda a: (a["layer"],),  # D before S
}


def _sort_key(source: SourceName, candidate: Candidate) -> tuple:
    requirement = candidate.requirement
    return (CRITERIA[source](requirement.attributes), _natural(requirement.id))


def is_relevant(candidate: Candidate, relevant_types: set[str]) -> bool:
    """The first listed type is the most important one (ADR 0007); it must be an archetype type."""
    types = candidate.classification.cfn_resource_types
    return bool(types) and types[0] in relevant_types


def _group(source: SourceName, c: Candidate) -> str:
    """Resource type (BSI, CIS: first listed type), chapter (DSGVO) or module (SDM)."""
    if source == "DSGVO":
        return str(c.requirement.attributes["chapter"])
    if source == "SDM":
        return str(c.requirement.attributes["module"])
    return c.classification.cfn_resource_types[0]


def _round_robin(source: SourceName, candidates: list[Candidate], cap: int):
    groups = defaultdict(list)
    for c in sorted(candidates, key=lambda c: _sort_key(source, c)):
        groups[_group(source, c)].append(c)
    queues = sorted(groups.items(), key=lambda item: (_sort_key(source, item[1][0]), item[0]))
    picked: list[Candidate] = []
    while len(picked) < cap and any(queue for _, queue in queues):
        for _, queue in queues:
            if queue and len(picked) < cap:
                picked.append(queue.pop(0))
    return picked


def _split_pinned(
    source: SourceName, candidates: list[Candidate], pinned_ids: set[str], cap: int
) -> tuple[list[Candidate], list[Candidate]]:
    missing = pinned_ids - {c.requirement.id for c in candidates}
    if missing:
        raise ValueError(f"pinned {source} requirements without candidate: {sorted(missing)}")
    if len(pinned_ids) > cap:
        raise ValueError(f"{len(pinned_ids)} pinned {source} slots exceed the cap of {cap}")
    pinned = [c for c in candidates if c.requirement.id in pinned_ids]
    rest = [c for c in candidates if c.requirement.id not in pinned_ids]
    return sorted(pinned, key=lambda c: _sort_key(source, c)), rest


def rank_source(
    source: SourceName,
    candidates: list[Candidate],
    relevant_types: set[str] | None = None,
    cap: int | None = None,
    pinned_ids: set[str] = frozenset(),
) -> list[SelectedRequirement]:
    """`relevant_types` is set for architecture sources only (ADR 0007).

    Pinned slots skip the relevance filter, count towards the cap and take the first ranks.
    """
    cap = cap or CAPS[source]
    pinned, rest = _split_pinned(source, candidates, pinned_ids, cap)
    if relevant_types is not None:
        rest = [c for c in rest if is_relevant(c, relevant_types)]
    picked = pinned + _round_robin(source, rest, cap - len(pinned))
    return [
        SelectedRequirement(
            requirement_id=c.requirement.id, source=source,
            rationale=c.classification.rationale,
            cfn_resource_types=c.classification.cfn_resource_types,
            pinned=c.requirement.id in pinned_ids, rank=rank,
        )
        for rank, c in enumerate(picked, start=1)
    ]
