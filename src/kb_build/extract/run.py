"""Writes the extracted requirements per source (ADR 0008). No LLM.

The file I/O of the extraction lives here: sources.json and the download cache in, extracted out.
"""

from kb_build.extract import bsi, c5, cis, dsgvo, fsbp, sdm
from kb_build.extract.models import merge_sources
from kb_build.paths import BuildPaths
from kb_build.source_fetch import fetch_to_cache, load_sources_json, read_cached

# output file -> (adapter, sources.json keys); cis/fsbp/c5.json stay local (ADR 0008, .gitignore)
ADAPTERS = {
    "bsi.json": (bsi, ["bsi_gspp_oscal"]),
    "cis.json": (cis, ["cis_aws_v7_prowler"]),
    "fsbp.json": (fsbp, ["fsbp_aws_prowler"]),
    "c5.json": (c5, ["c5_aws_prowler"]),
    "dsgvo.json": (dsgvo, ["dsgvo_formex"]),
    "sdm.json": (
        sdm, ["sdm_m60_loeschen_pdf", "sdm_m50_trennen_pdf", "sdm_m51_zugriffe_regeln_pdf"]
    ),
}


def extract_all(paths: BuildPaths = BuildPaths()) -> None:
    specs = load_sources_json(paths.sources_json)
    paths.extracted.mkdir(parents=True, exist_ok=True)
    for filename, (adapter, keys) in ADAPTERS.items():
        cached = [(fetch_to_cache(specs[key], cache_dir=paths.source_cache), specs[key].version)
                  for key in keys]
        extracted = merge_sources([adapter.extract(str(p), read_cached(p), v) for p, v in cached])
        (paths.extracted / filename).write_text(extracted.model_dump_json(indent=2) + "\n", "utf-8")
