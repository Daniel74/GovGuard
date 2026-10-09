"""SDM adapter: measure tables of the module PDFs -> ExtractedSource (pure, no I/O).

The prose only cites measure IDs in brackets; the table in section 5 is the only place
where each ID stands next to its measure, so the adapter reads the table alone.
"""

import re
from collections.abc import Iterator
from io import BytesIO

from pypdf import PdfReader

from govguard.text import normalize
from kb_build.extracted_models import ExtractedSource, Requirement, mark_prefilter

LAYERS = frozenset({"D", "S"})  # Daten, Systeme; not Prozesse (ARCHITECTURE 1.1)
# Modules in data/sources.json; Protokollieren (M43) is left out on purpose (ARCHITECTURE 1.1)
MODULE_NAMES = {"M60": "Löschen", "M50": "Trennen", "M51": "Zugriffe regeln"}

TABLE_HEADER = "Nr. Maßnahme"
ROW_START = re.compile(r"(M\d{2}\.[DSP]\d{2}) (.+)")
# A row ends with the PDCA column (may be empty) and the validity column, e.g. "P, D V1.0"
ROW_END = re.compile(r"(.*?)(?:\s+[PDCA](?:,\s*[PDCA])*)?\s+V\d+\.\d+[a-z]?")


def _rows(text: str) -> Iterator[tuple[str, str]]:
    """(measure ID, measure text) per table row; a row may span several lines."""
    start = text.find(TABLE_HEADER)
    if start < 0:
        raise ValueError("SDM measure table not found")
    rid, pieces = None, []
    for line in text[start:].splitlines():
        line = line.strip()
        if rid is None:
            row = ROW_START.fullmatch(line)
            if not row:
                continue
            rid, pieces = row.group(1), [row.group(2)]
        else:
            pieces.append(line)
        if end := ROW_END.fullmatch(" ".join(pieces)):
            yield rid, end.group(1)
            rid = None
    if rid is not None:
        raise ValueError(f"SDM row {rid} has no validity column")


def _requirement(rid: str, measure: str) -> Requirement:
    module, layer = rid[:3], rid[4]
    text = normalize(measure)
    return Requirement(
        id=rid,
        title=text,
        text=text,
        primary_anchor=f"SDM {MODULE_NAMES[module]} {rid}",
        attributes={"module": module, "layer": layer},
        prefilter_passed=False,
    )


def prefilter(requirement: Requirement) -> bool:
    """Keeps layers Daten and Systeme (ARCHITECTURE 1.1)."""
    return requirement.attributes.get("layer") in LAYERS


def extract_from_text(origin: str, text: str, version: str) -> ExtractedSource:
    """All measures of all layers D, S and P (DESIGN 1.1)."""
    requirements = [_requirement(rid, measure) for rid, measure in _rows(text)]
    return ExtractedSource(
        source="SDM", version=version, origin=origin,
        requirements=mark_prefilter(requirements, prefilter),
    )


def extract(origin: str, pdf: bytes, version: str) -> ExtractedSource:
    pages = PdfReader(BytesIO(pdf)).pages
    return extract_from_text(origin, "\n".join(page.extract_text() for page in pages), version)
