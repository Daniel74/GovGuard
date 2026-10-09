"""Build contract for extracted sources (DESIGN 1.1): the evidence base for later gates."""

from collections import Counter
from collections.abc import Callable
from typing import Literal

from pydantic import BaseModel, model_validator


class Requirement(BaseModel):
    id: str
    title: str
    text: str
    primary_anchor: str
    attributes: dict[str, str | int | bool]
    prefilter_passed: bool


class ExtractedSource(BaseModel):
    source: Literal["BSI", "CIS", "DSGVO", "SDM"]
    version: str
    origin: str
    requirements: list[Requirement]

    @model_validator(mode="after")
    def _each_id_once(self) -> "ExtractedSource":
        duplicates = [rid for rid, n in Counter(r.id for r in self.requirements).items() if n > 1]
        if duplicates:
            raise ValueError(f"duplicate {self.source} ids: {duplicates}")
        return self


def mark_prefilter(
    requirements: list[Requirement], prefilter: Callable[[Requirement], bool]
) -> list[Requirement]:
    """Stores each adapter's prefilter verdict in `prefilter_passed` (ARCHITECTURE 1.1)."""
    return [r.model_copy(update={"prefilter_passed": prefilter(r)}) for r in requirements]


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
