"""Shared parser for Prowler compliance JSON: CIS, FSBP and C5 (ADR 0008, pure, no I/O)."""

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from govguard.models import SourceName
from govguard.text import normalize
from kb_build.extracted_models import ExtractedSource, Prefilter, Requirement, mark_prefilter

Entry = dict[str, Any]


@dataclass(frozen=True)
class ProwlerFormat:
    """What differs per framework; the parser itself is the same."""

    source: SourceName
    anchor: Callable[[str, str], str]  # (requirement id, version) -> primary anchor
    title: Callable[[Entry], str]
    text: Callable[[Entry], str]
    attributes: Callable[[Entry], dict[str, str | int | bool]]
    prefilter: Prefilter


def strip_markdown(text: str) -> str:
    # ADR 0008: anchors are checked against the Prowler text without markdown markers
    return normalize(text.replace("**", "").replace("`", ""))


def extract(fmt: ProwlerFormat, origin: str, prowler: Entry, version: str) -> ExtractedSource:
    """All entries of a Prowler file; `version` comes from data/sources.json."""
    requirements = [
        Requirement(
            id=entry["Id"], title=fmt.title(entry), text=fmt.text(entry),
            primary_anchor=fmt.anchor(entry["Id"], version),
            attributes=fmt.attributes(entry), prefilter_passed=False,
        )
        for entry in prowler["Requirements"]
    ]
    return ExtractedSource(
        source=fmt.source, version=version, origin=origin,
        requirements=mark_prefilter(requirements, fmt.prefilter),
    )
