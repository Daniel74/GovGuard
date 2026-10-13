"""Build contract for extracted sources (DESIGN 1.1): the evidence base for later gates."""

from collections import Counter
from collections.abc import Callable

from pydantic import BaseModel, model_validator

from govguard.models import SourceName


class Requirement(BaseModel):
    id: str
    title: str
    text: str
    primary_anchor: str
    attributes: dict[str, str | int | bool]
    prefilter_passed: bool
    prefilter_reason: str | None = None  # fixed sentence if the prefilter rejected it (ADR 0011)


class ExtractedSource(BaseModel):
    source: SourceName
    version: str
    origin: str
    requirements: list[Requirement]

    @model_validator(mode="after")
    def _each_id_once(self) -> "ExtractedSource":
        duplicates = [rid for rid, n in Counter(r.id for r in self.requirements).items() if n > 1]
        if duplicates:
            raise ValueError(f"duplicate {self.source} ids: {duplicates}")
        return self


# None keeps the requirement, a fixed sentence rejects it (ARCHITECTURE 1.1)
Prefilter = Callable[[Requirement], str | None]


def mark_prefilter(requirements: list[Requirement], prefilter: Prefilter) -> list[Requirement]:
    """Stores each adapter's verdict: `None` keeps the requirement, a sentence rejects it."""
    marked = []
    for requirement in requirements:
        reason = prefilter(requirement)
        update = {"prefilter_passed": reason is None, "prefilter_reason": reason}
        marked.append(requirement.model_copy(update=update))
    return marked


def merge_sources(parts: list[ExtractedSource]) -> ExtractedSource:
    """One output file per source; SDM ships one PDF per module (ADR 0008)."""
    if len(parts) == 1:
        return parts[0]
    return ExtractedSource(
        source=parts[0].source,
        version=", ".join(p.version for p in parts),
        origin=", ".join(p.origin for p in parts),
        requirements=[r for p in parts for r in p.requirements],
    )
