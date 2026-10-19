"""Formex reader for EU acts from CELLAR (DSGVO, KI-VO): XML -> articles. Pure, no I/O."""

import xml.etree.ElementTree as ET
from collections.abc import Iterator
from dataclasses import dataclass

from govguard.text import normalize
from kb_build.extract.models import Section

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
    sections: tuple[Section, ...] = ()


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


def _items(alinea: ET.Element, mark: str) -> list[Section]:
    """One section per list item; the words around the list are its lead-in."""
    lead_in = normalize(" ".join(_render(c) for c in alinea if c.tag != "LIST"))
    sections = []
    for item in alinea.find("LIST").findall("ITEM"):
        label = item.findtext("NP/NO.P", "")  # "a)"; a nested list stays in the item's text
        text = normalize(_render(item)).removeprefix(label).strip()
        sections.append(Section(mark=f"{mark} lit. {label.strip('(). ')}", text=text,
                                lead_in=lead_in))
    return sections


def _paragraph(parts: list[ET.Element], mark: str) -> list[Section]:
    """A paragraph without a list is one section; with one, each item and each other
    subparagraph (UAbs.) is a section of its own. Formex has at most one list per paragraph.
    """
    if all(part.find("LIST") is None for part in parts):
        return [Section(mark=mark, text=normalize(" ".join(_render(p) for p in parts)))]
    sections = []
    for n, part in enumerate(parts, start=1):
        if part.find("LIST") is not None:
            sections += _items(part, mark)
        else:
            sections.append(Section(mark=f"{mark} UAbs. {n}", text=normalize(_render(part))))
    return sections


def _sections(element: ET.Element, mark: str) -> list[Section]:
    parags = element.findall("PARAG") or [element]  # some articles have no numbered paragraphs
    sections = []
    for parag in parags:
        number = parag.findtext("NO.PARAG")
        parts = [c for c in parag if c.tag not in {"NO.PARAG", "TI.ART", "STI.ART"}]
        sections += _paragraph(parts, f"{mark} Abs. {number.strip('(). ')}" if number else mark)
    return sections


def _article(element: ET.Element, chapter: int) -> Article:
    body = [child for child in element if child.tag not in {"TI.ART", "STI.ART"}]
    number = element.attrib["IDENTIFIER"].lstrip("0").lower()  # "004A" -> "4a"
    return Article(
        number=number,
        chapter=chapter,
        title=normalize(_render(element.find("STI.ART"))),
        text=normalize(" ".join(_render(child) for child in body)),
        sections=tuple(_sections(element, f"Art. {number}")),
    )


def articles(xml: bytes) -> list[Article]:
    """Every article in document order; ElementTree drops processing instructions (<?PAGE?>)."""
    root = ET.fromstring(xml)
    return [
        _article(element, chapter)
        for chapter, division in _chapters(root)
        for element in division.iter("ARTICLE")
    ]
