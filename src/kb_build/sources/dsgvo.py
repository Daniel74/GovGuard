"""DSGVO adapter: CELLAR Formex XML -> ExtractedSource (pure, no I/O)."""

import xml.etree.ElementTree as ET
from collections.abc import Iterator

from govguard.text import normalize
from kb_build.extracted_models import ExtractedSource, Requirement, mark_prefilter

CHAPTERS = frozenset({2, 3, 4, 5})  # Kapitel II-V = Art. 5-49 (ARCHITECTURE 1.1)
ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6,
         "VII": 7, "VIII": 8, "IX": 9, "X": 10, "XI": 11}

# Source: DSGVO Art. 83 (constant on purpose, Art. 83 itself is not parsed)
FINE_TIER_4 = frozenset({5, 6, 7, 9, *range(12, 23), *range(44, 50), 58})  # Art. 83 Abs. 5
FINE_TIER_2 = frozenset({8, 11, *range(25, 40), 41, 42, 43})  # Art. 83 Abs. 4

# Formex layout elements become word breaks; quote marks are empty elements
BLOCKS = frozenset({"PARAG", "NO.PARAG", "ALINEA", "P", "LIST", "ITEM", "NP", "NO.P", "TXT"})
QUOTES = {"QUOT.START": "„", "QUOT.END": "“"}


def _fine_tier(article: int) -> int:
    if article in FINE_TIER_4:
        return 4
    return 2 if article in FINE_TIER_2 else 0


def _render(element: ET.Element) -> str:
    """Element text with quote marks; footnotes (NOTE) are not article text."""
    parts = [element.text or ""]
    for child in element:
        if child.tag in QUOTES:
            parts.append(QUOTES[child.tag])
        elif child.tag != "NOTE":
            inner = _render(child)
            parts.append(f" {inner} " if child.tag in BLOCKS else inner)
        parts.append(child.tail or "")
    return "".join(parts)


def _chapters(root: ET.Element) -> Iterator[tuple[int, ET.Element]]:
    for division in root.iter("DIVISION"):
        heading = normalize(_render(division.find("TITLE/TI")))
        if heading.startswith("KAPITEL "):
            yield ROMAN[heading.removeprefix("KAPITEL ")], division


def _requirement(article: ET.Element, chapter: int) -> Requirement:
    number = int(article.attrib["IDENTIFIER"])
    body = [child for child in article if child.tag not in {"TI.ART", "STI.ART"}]
    return Requirement(
        id=f"Art. {number}",
        title=normalize(_render(article.find("STI.ART"))),
        text=normalize(" ".join(_render(child) for child in body)),
        primary_anchor=f"DSGVO Art. {number}",
        attributes={"chapter": chapter, "fine_tier": _fine_tier(number)},
        prefilter_passed=False,
    )


def prefilter(requirement: Requirement) -> bool:
    """Keeps chapters II-V, Art. 5-49 (ARCHITECTURE 1.1)."""
    return requirement.attributes.get("chapter") in CHAPTERS


def extract(origin: str, xml: bytes, version: str) -> ExtractedSource:
    """All 99 articles; ElementTree drops processing instructions such as <?CLG.MDFO?>."""
    root = ET.fromstring(xml)
    requirements = [
        _requirement(article, chapter)
        for chapter, division in _chapters(root)
        for article in division.iter("ARTICLE")
    ]
    return ExtractedSource(
        source="DSGVO", version=version, origin=origin,
        requirements=mark_prefilter(requirements, prefilter),
    )
