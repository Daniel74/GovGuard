"""Build entry point: python -m kb_build (ARCHITECTURE -> Code-Struktur)."""

import json
from pathlib import Path

from kb_build.source_fetch import fetch_to_cache, load_sources_json
from kb_build.sources import bsi, cis

# sources.json key -> (adapter, output file); cis.json stays local (ADR 0008, .gitignore)
ADAPTERS = {
    "bsi_gspp_oscal": (bsi, "bsi.json"),
    "cis_aws_v7_prowler": (cis, "cis.json"),
}


def extract_all(sources: Path = Path("data/sources.json"), out_dir: Path = Path("data/extracted")):
    specs = load_sources_json(sources)
    out_dir.mkdir(parents=True, exist_ok=True)
    for key, (adapter, filename) in ADAPTERS.items():
        spec = specs[key]
        path = fetch_to_cache(spec)
        raw = json.loads(path.read_text(encoding="utf-8"))
        extracted = adapter.extract(str(path), raw, spec.version)
        (out_dir / filename).write_text(extracted.model_dump_json(indent=2) + "\n", "utf-8")


if __name__ == "__main__":
    extract_all()
