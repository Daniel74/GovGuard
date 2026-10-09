"""Build entry point: python -m kb_build (ARCHITECTURE -> Code-Struktur)."""

from pathlib import Path

from kb_build.extracted_models import merge_sources
from kb_build.source_fetch import fetch_to_cache, load_sources_json, read_cached
from kb_build.sources import bsi, cis, dsgvo, sdm

# output file -> (adapter, sources.json keys); cis.json stays local (ADR 0008, .gitignore)
ADAPTERS = {
    "bsi.json": (bsi, ["bsi_gspp_oscal"]),
    "cis.json": (cis, ["cis_aws_v7_prowler"]),
    "dsgvo.json": (dsgvo, ["dsgvo_formex"]),
    "sdm.json": (
        sdm, ["sdm_m60_loeschen_pdf", "sdm_m50_trennen_pdf", "sdm_m51_zugriffe_regeln_pdf"]
    ),
}


def extract_all(sources: Path = Path("data/sources.json"), out_dir: Path = Path("data/extracted")):
    specs = load_sources_json(sources)
    out_dir.mkdir(parents=True, exist_ok=True)
    for filename, (adapter, keys) in ADAPTERS.items():
        paths = [(fetch_to_cache(specs[key]), specs[key].version) for key in keys]
        extracted = merge_sources([adapter.extract(str(p), read_cached(p), v) for p, v in paths])
        (out_dir / filename).write_text(extracted.model_dump_json(indent=2) + "\n", "utf-8")


if __name__ == "__main__":
    extract_all()
