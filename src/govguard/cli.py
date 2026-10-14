"""CLI entry point: local audit, wires file I/O, the model and `run_audit()` together."""

import argparse
import hashlib
import os
import sys
import uuid
from pathlib import Path

from pydantic_ai.models import Model

from govguard.audit_engine import AuditValidationError, run_audit
from govguard.aws_services import bedrock_model
from govguard.models import RuleCatalog, Trace

SPEC_CATALOG = Path("data/knowledge_base/rules_spec.json")
ARCH_CATALOG = Path("data/knowledge_base/rules_arch.json")


def main(argv: list[str] | None = None, model: Model | None = None) -> int:
    args = _parser().parse_args(argv)
    input_text = args.file.read_text(encoding="utf-8")
    catalog_bytes = args.catalog.read_bytes()
    trace = Trace(
        audit_id=str(uuid.uuid4()),
        input_sha256=hashlib.sha256(input_text.encode()).hexdigest(),
        catalog_sha256=hashlib.sha256(catalog_bytes).hexdigest(),
        kb_commit=os.environ.get("KB_COMMIT", "local"),
    )
    if model is None:
        model = bedrock_model()
    try:
        report = run_audit(RuleCatalog.model_validate_json(catalog_bytes), input_text, model, trace)
    except AuditValidationError as error:  # fail closed, like HTTP 502
        print(_failure_text(error), file=sys.stderr)
        return 2
    print(report.model_dump_json(indent=2))
    return 0


def _failure_text(error: AuditValidationError) -> str:
    """One plain sentence, then the reasons per rule; never the library's error text."""
    if error.api_error:
        return ("Audit fehlgeschlagen: Der KI-Dienst war nicht erreichbar oder überlastet. "
                "Bitte später erneut versuchen.")
    reasons = "\n".join(f"  - {p.text}" for p in error.problems)
    return ("Audit fehlgeschlagen: Die Antwort der KI war auch nach einer Korrektur nicht "
            f"verwertbar. Gründe je Prüfregel:\n{reasons}")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="govguard.cli", description="GovGuard Audit lokal")
    commands = parser.add_subparsers(dest="command", required=True)
    for name, help_text, file_help, catalog in [
        ("spec", "Spec-Audit (DSGVO/SDM)", "Spezifikation als Textdatei", SPEC_CATALOG),
        ("arch", "Architektur-Audit (BSI/CIS)", "CloudFormation-Template oder Freitext",
         ARCH_CATALOG),
    ]:
        command = commands.add_parser(name, help=help_text)
        command.add_argument("file", type=Path, help=file_help)
        command.add_argument("--catalog", type=Path, default=catalog, help=catalog.name)
    return parser


if __name__ == "__main__":
    sys.exit(main())
