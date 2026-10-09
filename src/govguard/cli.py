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

DEFAULT_CATALOG = Path("data/knowledge_base/rules_spec.json")


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
        print(f"Audit fehlgeschlagen: LLM-Antwort ungültig ({error})", file=sys.stderr)
        return 2
    print(report.model_dump_json(indent=2))
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="govguard.cli", description="GovGuard Audit lokal")
    commands = parser.add_subparsers(dest="command", required=True)
    spec = commands.add_parser("spec", help="Spec-Audit (DSGVO/SDM)")
    spec.add_argument("file", type=Path, help="Spezifikation als Textdatei")
    spec.add_argument("--catalog", type=Path, default=DEFAULT_CATALOG, help="rules_spec.json")
    return parser


if __name__ == "__main__":
    sys.exit(main())
