"""Formex reader for EU acts from CELLAR (DSGVO, KI-VO): XML -> articles. Pure, no I/O."""

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

from govguard.text import normalize

ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8, "IX": 9,
         "X": 10, "XI": 11, "XII": 12, "XIII": 13}

# Formex layout elements become word breaks; quote marks are empty elements
BLOCKS = frozenset({"PARAG", "NO.PARAG", "ALINEA", "P", "LIST", "ITEM", "NP", "NO.P", "TXT"})
QUOTES = {"QUOT.START": "„", "QUOT.END": "“"}


@dataclass(frozen=True)
class Article:
    number: str  # "32", or "4a" for an article inserted by an amendment
    chapter: int
    title: str
    text: str


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


def _article(element: ET.Element, chapter: int) -> Article:
    body = [child for child in element if child.tag not in {"TI.ART", "STI.ART"}]
    return Article(
        number=element.attrib["IDENTIFIER"].lstrip("0").lower(),  # "004A" -> "4a"
        chapter=chapter,
        title=normalize(_render(element.find("STI.ART"))),
        text=normalize(" ".join(_render(child) for child in body)),
    )


def articles(xml: bytes) -> list[Article]:
    """Every article in document order; ElementTree drops processing instructions (<?PAGE?>)."""
    root = ET.fromstring(xml)
    return [
        _article(element, chapter)
        for chapter, division in _chapters(root)
        for element in division.iter("ARTICLE")
    ]
