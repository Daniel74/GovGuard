"""Build entry point: python -m kb_build [extract|select] (ARCHITECTURE -> Code-Struktur)."""

import argparse
import logging
from pathlib import Path

from pydantic_ai.models import Model

from govguard.aws_services import bedrock_model
from kb_build.extracted_models import merge_sources
from kb_build.groq_services import groq_model
from kb_build.selection_run import select_all
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


def model_for(provider: str) -> Model:
    """Bedrock is the default; Groq is an explicit opt-in while Bedrock is blocked (ADR 0010)."""
    providers = {"bedrock": bedrock_model, "groq": groq_model}
    if provider not in providers:
        raise ValueError(f"unknown provider {provider!r}, choose one of {sorted(providers)}")
    return providers[provider]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m kb_build")
    parser.add_argument("command", nargs="?", default="extract", choices=["extract", "select"])
    parser.add_argument("--provider", default="bedrock", choices=["bedrock", "groq"])
    parser.add_argument("--audit-type", choices=["spec", "architecture"], default=None)
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("kb_build").setLevel(logging.INFO)  # progress only, no HTTP noise
    if args.command == "select":
        select_all(model_for(args.provider), only=args.audit_type)
    else:
        extract_all()
