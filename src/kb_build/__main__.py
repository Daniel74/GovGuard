"""Build entry point: python -m kb_build [extract|select|rules|cfn-properties] (ARCHITECTURE)."""

import argparse
import logging
from pathlib import Path

from pydantic_ai.models import Model

from govguard.aws_services import GLOBAL_MODEL_ID, bedrock_model
from kb_build.extract.run import extract_all
from kb_build.groq_services import groq_model
from kb_build.reference.run import snapshot_scope
from kb_build.rules.run import formulate_all
from kb_build.select.run import select_all


def model_for(provider: str) -> Model:
    """Bedrock `eu.` is the default; the others are explicit build opt-ins (ADR 0010, 0012)."""
    providers = {
        "bedrock": bedrock_model,
        "bedrock-global": lambda: bedrock_model(model_id=GLOBAL_MODEL_ID),
        "groq": groq_model,
    }
    if provider not in providers:
        raise ValueError(f"unknown provider {provider!r}, choose one of {sorted(providers)}")
    return providers[provider]()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="python -m kb_build")
    parser.add_argument("command", nargs="?", default="extract",
                        choices=["extract", "select", "rules", "cfn-properties"])
    parser.add_argument("--provider", default="bedrock",
                        choices=["bedrock", "bedrock-global", "groq"])
    parser.add_argument("--audit-type", choices=["spec", "architecture"], default=None)
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"))  # describe-type
    args = parser.parse_args()
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    logging.getLogger("kb_build").setLevel(logging.INFO)  # progress only, no HTTP noise
    if args.command == "select":
        select_all(model_for(args.provider), only=args.audit_type)
    elif args.command == "rules":
        formulate_all(model_for(args.provider), only=args.audit_type)
    elif args.command == "cfn-properties":
        snapshot_scope(args.schema_dir)
    else:
        extract_all()
