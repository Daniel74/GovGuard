"""Build entry point: python -m kb_build [extract|select|rules|cfn-properties] (ARCHITECTURE)."""

import argparse
import logging
from pathlib import Path

from pydantic_ai.models import Model

from govguard.aws_services import GLOBAL_MODEL_ID, bedrock_model
from govguard.groq_services import groq_model
from kb_build.extract.run import extract_all
from kb_build.paths import BuildPaths
from kb_build.reference.run import snapshot_scope
from kb_build.rules.run import formulate_all
from kb_build.select.run import select_all


def model_for(provider: str) -> Model:
    """Groq is the build default (ADR 0014); Bedrock profiles are explicit opt-ins (ADR 0012)."""
    providers = {
        "bedrock": bedrock_model,
        "bedrock-global": lambda: bedrock_model(model_id=GLOBAL_MODEL_ID),
        "groq": groq_model,
    }
    if provider not in providers:
        raise ValueError(f"unknown provider {provider!r}, choose one of {sorted(providers)}")
    return providers[provider]()


def configure_logging(log_file: Path) -> None:
    """Terminal and file get the same lines; the file is checked in next to the result (#29).

    Only the kb_build logger goes to the file: progress, retries, tokens, no HTTP noise.
    """
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(message)s", datefmt="%H:%M:%S")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    to_file = logging.FileHandler(log_file, mode="w", encoding="utf-8")  # one run per file
    to_file.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s",
                                           datefmt="%Y-%m-%dT%H:%M:%S"))
    logger = logging.getLogger("kb_build")
    logger.setLevel(logging.INFO)
    logger.addHandler(to_file)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="python -m kb_build")
    parser.add_argument("command", nargs="?", default="extract",
                        choices=["extract", "select", "rules", "cfn-properties"])
    parser.add_argument("--provider", default="groq",
                        choices=["bedrock", "bedrock-global", "groq"])
    parser.add_argument("--audit-type", choices=["spec", "architecture"], default=None)
    parser.add_argument("--schema-dir", type=Path, default=Path("schemas"))  # describe-type
    return parser.parse_args(argv)


if __name__ == "__main__":
    args = parse_args()
    configure_logging(BuildPaths().build_log(args.command, args.audit_type))
    if args.command == "select":
        select_all(model_for(args.provider), only=args.audit_type)
    elif args.command == "rules":
        formulate_all(model_for(args.provider), only=args.audit_type)
    elif args.command == "cfn-properties":
        snapshot_scope(args.schema_dir)
    else:
        extract_all()
