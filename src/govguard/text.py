"""Pure text helpers shared by build and runtime: normalize, quote check, template types."""

import json
import re
import unicodedata

# EUR-Lex consolidation markers such as "►C2", "▼M1" and the closing "◄"
_EURLEX_MARKER = re.compile(r"[►▼][A-Z]\d*|◄")
_SOFT_HYPHEN = "\u00ad"
_TYPOGRAPHIC = str.maketrans({
    "„": '"', "“": '"', "”": '"', "«": '"', "»": '"',
    "‚": "'", "‘": "'", "’": "'",
    "–": "-", "—": "-",
})
_WHITESPACE = re.compile(r"\s+")
_MARKDOWN_EMPHASIS = re.compile(r"[*_`]")
# Models write "KI‐System" with U+2010; normalize() keeps it, so the frozen extracts stay (#52)
_HYPHENS = str.maketrans({"\u2010": "-"})

MIN_QUOTE_LENGTH = 15  # shorter quotes such as "S3" prove nothing


def normalize(text: str) -> str:
    """Apply the five steps from DESIGN 3 in fixed order; case is preserved."""
    text = unicodedata.normalize("NFKC", text)
    text = _EURLEX_MARKER.sub("", text)
    text = text.replace(_SOFT_HYPHEN, "")
    text = text.translate(_TYPOGRAPHIC)
    return _WHITESPACE.sub(" ", text).strip()


def _comparable(text: str) -> str:
    return _MARKDOWN_EMPHASIS.sub("", normalize(text)).translate(_HYPHENS)


def _without_spaces(text: str) -> str:
    return _comparable(text).replace(" ", "")


def too_short_to_prove(text: str) -> bool:
    """Shorter than MIN_QUOTE_LENGTH without markdown emphasis; one measure for quote and range."""
    return len(_comparable(text)) < MIN_QUOTE_LENGTH


def contains_quote(text: str, quote: str) -> bool:
    """True if the quote appears verbatim in the text after normalization.

    Spaces do not count: pypdf splits words in the SDM PDFs ("Protokollie rung").
    Markdown emphasis (`*`, `_`, backticks) does not count either: models quote
    "**Name:** text" without the asterisks.
    """
    if too_short_to_prove(quote):
        return False
    return _without_spaces(quote) in _without_spaces(text)


def template_resource_types(text: str) -> set[str] | None:
    """Resource types of a CloudFormation JSON template, None for anything else (ADR 0007)."""
    try:
        template = json.loads(text)
    except ValueError:
        return None
    resources = template.get("Resources") if isinstance(template, dict) else None
    if not isinstance(resources, dict):
        return None
    return {r["Type"] for r in resources.values() if isinstance(r, dict) and "Type" in r}
