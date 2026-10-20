"""DSGVO adapter: CELLAR Formex XML -> ExtractedSource (pure, no I/O)."""

from kb_build.extract.formex import Article, articles
from kb_build.extract.models import ExtractedSource, Requirement, mark_prefilter

CHAPTERS = frozenset({2, 3, 4, 5})  # Kapitel II-V = Art. 5-49 (ARCHITECTURE 1.1)

# Source: DSGVO Art. 83 (constant on purpose, Art. 83 itself is not parsed)
FINE_TIER_4 = frozenset({5, 6, 7, 9, *range(12, 23), *range(44, 50), 58})  # Art. 83 Abs. 5
FINE_TIER_2 = frozenset({8, 11, *range(25, 40), 41, 42, 43})  # Art. 83 Abs. 4


# Never apply to a German authority (#59, ADR 0028); fixed sentence for the selection protocol
NOT_FOR_AUTHORITIES = {
    "Art. 20": "Art. 20 Abs. 3: Das Recht auf Datenübertragbarkeit gilt nicht für Verarbeitungen "
               "in Wahrnehmung einer öffentlichen Aufgabe, also nicht für eine Behörde.",
    "Art. 27": "Art. 27 Abs. 1: Einen Vertreter benennen nur Verantwortliche ohne "
               "Niederlassung in der Union, nicht eine deutsche Behörde.",
    "Art. 41": "Art. 41 Abs. 6: Die Überwachung genehmigter Verhaltensregeln gilt nicht "
               "für Behörden und öffentliche Stellen.",
    "Art. 47": "Art. 47: Verbindliche interne Datenschutzvorschriften gibt es nur für "
               "Unternehmensgruppen, nicht für eine einzelne Behörde.",
}


def _fine_tier(article: int) -> int:
    if article in FINE_TIER_4:
        return 4
    return 2 if article in FINE_TIER_2 else 0


def _requirement(article: Article) -> Requirement:
    return Requirement(
        id=f"Art. {article.number}",
        title=article.title,
        text=article.text,
        primary_anchor=f"DSGVO Art. {article.number}",
        attributes={"chapter": article.chapter, "fine_tier": _fine_tier(int(article.number))},
        prefilter_passed=False,
        sections=list(article.sections),
    )


def prefilter(requirement: Requirement) -> str | None:
    """Keeps chapters II-V, Art. 5-49 (ARCHITECTURE 1.1), minus four articles for authorities."""
    if requirement.attributes.get("chapter") not in CHAPTERS:
        return "Kapitel gehört nicht zu II–V (Art. 5–49)."
    return NOT_FOR_AUTHORITIES.get(requirement.id)


def extract(origin: str, xml: bytes, version: str) -> ExtractedSource:
    """All 99 articles of the consolidated text."""
    requirements = [_requirement(article) for article in articles(xml)]
    return ExtractedSource(
        source="DSGVO", version=version, origin=origin,
        requirements=mark_prefilter(requirements, prefilter),
    )
