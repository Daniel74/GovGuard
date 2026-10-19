"""CLI entry point: local audit, wires file I/O, the model and `run_audit()` together."""

import argparse
import sys
from pathlib import Path
from typing import get_args

from pydantic_ai.models import Model

from govguard.audit_engine import (
    AuditValidationError,
    InputTooLongError,
    check_input_length,
    run_audit,
)
from govguard.audit_setup import ARCH_CATALOG, SPEC_CATALOG, failure_text, make_trace
from govguard.aws_services import bedrock_model
from govguard.groq_services import MissingApiKeyError, groq_model
from govguard.models import Provider, RuleCatalog


def model_for(provider: Provider) -> Model:
    """Groq is the default (ADR 0023); no silent switch, a missing key raises (ADR 0016)."""
    return {"groq": groq_model, "bedrock": bedrock_model}[provider]()


def main(argv: list[str] | None = None, model: Model | None = None) -> int:
    args = parse_args(argv)
    input_text = args.file.read_text(encoding="utf-8")
    catalog_bytes = args.catalog.read_bytes()
    trace = make_trace(input_text, catalog_bytes)
    try:
        check_input_length(input_text)  # before the model: no key needed to learn it's too long
        model = model or model_for(args.provider)
        report = run_audit(RuleCatalog.model_validate_json(catalog_bytes), input_text, model, trace)
    except InputTooLongError as error:  # rejected before the first LLM call
        print(error, file=sys.stderr)
        return 1
    except MissingApiKeyError as error:  # no silent switch to Bedrock (ADR 0016)
        print(error, file=sys.stderr)
        return 3
    except AuditValidationError as error:  # fail closed, like HTTP 502
        print(failure_text(error), file=sys.stderr)
        return 2
    print(report.model_dump_json(indent=2))
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(prog="govguard.cli", description="GovGuard Audit lokal")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text, file_help, catalog in [
        ("spec", "Spec-Audit (DSGVO/KI-VO/SDM)", "Spezifikation als Textdatei", SPEC_CATALOG),
        ("arch", "Architektur-Audit (BSI/CIS)", "CloudFormation-Template oder Freitext",
         ARCH_CATALOG),
    ]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("file", type=Path, help=file_help)
        command.add_argument("--catalog", type=Path, default=catalog, help=catalog.name)
        command.add_argument("--provider", choices=get_args(Provider), default="groq",
                             help="groq: nur fiktive Daten (USA); bedrock: eu., echte Daten")
    return parser.parse_args(argv)


if __name__ == "__main__":
    sys.exit(main())
