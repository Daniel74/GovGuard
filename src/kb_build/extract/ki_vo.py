"""KI-VO adapter: CELLAR Formex ZIP -> ExtractedSource (pure, unzips in memory, ADR 0025)."""

import io
import zipfile

from kb_build.extract.formex import Article, articles
from kb_build.extract.models import ExtractedSource, Requirement, mark_prefilter

# Slim selection (issue #52): AI literacy, prohibitions, high-risk classification, the high-risk
# duties a specification can show, fundamental rights impact assessment, transparency
KEPT = frozenset({"4", "5", "6", "13", "14", "26", "27", "50"})
PREFILTER_REASON = "Artikel gehört nicht zur Auswahl Art. 4, 5, 6, 13, 14, 26, 27 und 50 (#52)."


def _act(archive: bytes) -> bytes:
    """The ZIP holds a bibliographic .doc.xml next to the act itself."""
    with zipfile.ZipFile(io.BytesIO(archive)) as zf:
        [name] = [n for n in zf.namelist() if n.endswith(".xml") and not n.endswith(".doc.xml")]
        return zf.read(name)


def _requirement(article: Article) -> Requirement:
    return Requirement(
        id=f"Art. {article.number}",
        title=article.title,
        text=article.text,
        primary_anchor=f"KI-VO Art. {article.number}",
        attributes={"chapter": article.chapter},
        prefilter_passed=False,
        sections=list(article.sections),
    )


def prefilter(requirement: Requirement) -> str | None:
    """Keeps the articles of the slim selection (issue #52)."""
    if requirement.id.removeprefix("Art. ") in KEPT:
        return None
    return PREFILTER_REASON


def extract(origin: str, archive: bytes, version: str) -> ExtractedSource:
    """All articles of the consolidated text, inserted ones (Art. 4a) included."""
    requirements = [_requirement(article) for article in articles(_act(archive))]
    return ExtractedSource(
        source="KI-VO", version=version, origin=origin,
        requirements=mark_prefilter(requirements, prefilter),
    )
