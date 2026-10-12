"""Shared parser for Prowler compliance JSON: CIS, FSBP and C5 (ADR 0008, pure, no I/O)."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from govguard.models import SourceName
from govguard.text import normalize
from kb_build.extracted_models import ExtractedSource, Prefilter, Requirement, mark_prefilter

Entry = dict[str, Any]
# UTF-8 bytes read as Latin-1 upstream, e.g. "\u00e2\u0080\u0099" for "\u2019" (FSBP ECS.3)
_DOUBLE_ENCODED = re.compile("[\u00c2-\u00f4][\u0080-\u00bf]+")


@dataclass(frozen=True)
class ProwlerFormat:
    """What differs per framework; the parser itself is the same."""

    source: SourceName
    anchor: Callable[[str, str], str]  # (requirement id, version) -> primary anchor
    title: Callable[[Entry], str]
    text: Callable[[Entry], str]
    attributes: Callable[[Entry], dict[str, str | int | bool]]
    prefilter: Prefilter


def _repair(match: re.Match[str]) -> str:
    try:
        return match.group().encode("latin-1").decode("utf-8")
    except UnicodeDecodeError:  # a genuine "\u00e2" followed by a control character stays
        return match.group()


def strip_markdown(text: str) -> str:
    # ADR 0008: anchors are checked against the Prowler text without markdown markers
    text = _DOUBLE_ENCODED.sub(_repair, text)
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
