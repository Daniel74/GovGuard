"""Writes the decomposed legal acts and the decomposition protocol (#53). Gets the model injected.

The file I/O of the decomposition lives here: extracted acts and cache in, decomposed out.
"""

import logging
from pathlib import Path

from pydantic import TypeAdapter
from pydantic_ai.models import Model

from govguard.models import SourceName
from kb_build.decompose.cache import DecompositionCache
from kb_build.decompose.models import ArticleDecomposition, Decomposition
from kb_build.decompose.parts import Split, decompose_source
from kb_build.decompose.split import Splitter
from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.gates import usage_line
from kb_build.paths import DECOMPOSED, BuildPaths

logger = logging.getLogger("kb_build")


def _read_cache(path: Path) -> DecompositionCache:
    if not path.exists():
        return DecompositionCache()
    return DecompositionCache.from_json(path.read_text(encoding="utf-8"))


def _logged(splitter: Splitter) -> Split:
    def split(source: SourceName, article: Requirement) -> Decomposition | None:
        answer = splitter(source, article)
        result = "stays whole" if answer is None else f"{len(answer.groups)} groups"
        logger.info("decompose %s %s %s", source, article.id, result)
        return answer

    return split


def _decompose(
    name: SourceName, splitter: Splitter, paths: BuildPaths
) -> list[ArticleDecomposition]:
    raw = (paths.extracted / f"{name.lower()}.json").read_text(encoding="utf-8")
    decomposed, protocol = decompose_source(ExtractedSource.model_validate_json(raw),
                                            _logged(splitter))
    paths.decomposed.mkdir(parents=True, exist_ok=True)
    paths.source_file(name).write_text(decomposed.model_dump_json(indent=2) + "\n", "utf-8")
    return protocol


def decompose_all(model: Model, paths: BuildPaths = BuildPaths()) -> None:
    """Every legal act; the cache is saved even if a call aborts the run: answers are paid for."""
    cache = _read_cache(paths.decomposition_cache)
    splitter = Splitter(model, cache)
    try:
        protocol = [entry for name in DECOMPOSED for entry in _decompose(name, splitter, paths)]
    finally:
        paths.decomposition_cache.write_bytes(cache.to_json())
        logger.info(usage_line("spec", splitter.usage))
        logger.info(splitter.counts.line("spec", "decompose"))
    dump = TypeAdapter(list[ArticleDecomposition]).dump_json(protocol, indent=2)
    paths.out_file("decompositions", "spec").write_bytes(dump + b"\n")
