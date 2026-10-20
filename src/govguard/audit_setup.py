"""What the CLI and the demo UI share around run_audit(): catalogs, trace, failure text.

No AWS here: the demo UI imports this module and must not load the Bedrock adapter (ADR 0023).
"""

import hashlib
import json
import os
import uuid
from pathlib import Path

from govguard.audit_engine import AuditValidationError
from govguard.condition_models import ConditionDef
from govguard.models import AuditType, Trace

SPEC_CATALOG = Path("data/knowledge_base/rules_spec.json")
ARCH_CATALOG = Path("data/knowledge_base/rules_arch.json")
CATALOGS: dict[AuditType, Path] = {"spec": SPEC_CATALOG, "architecture": ARCH_CATALOG}
CONDITIONS = Path("data/input/conditions.json")  # maintained by hand (ADR 0028)


def conditions_for(audit_type: AuditType) -> list[ConditionDef]:
    """The conditions of the spec audit; the architecture audit has none (#60)."""
    if audit_type != "spec":
        return []
    return [ConditionDef.model_validate(item)
            for item in json.loads(CONDITIONS.read_text(encoding="utf-8"))]


def make_trace(input_text: str, catalog_bytes: bytes) -> Trace:
    """Hashes only, never the input itself (ADR 0006)."""
    return Trace(
        audit_id=str(uuid.uuid4()),
        input_sha256=hashlib.sha256(input_text.encode()).hexdigest(),
        catalog_sha256=hashlib.sha256(catalog_bytes).hexdigest(),
        kb_commit=os.environ.get("KB_COMMIT", "local"),
    )


def failure_text(error: AuditValidationError) -> str:
    """One plain sentence, then the reasons per rule; never the library's error text."""
    if error.api_error:
        return ("Audit fehlgeschlagen: Der KI-Dienst war nicht erreichbar oder überlastet. "
                "Bitte später erneut versuchen.")
    reasons = "\n".join(f"  - {p.text}" for p in error.problems)
    return ("Audit fehlgeschlagen: Die Antwort der KI war auch nach einer Korrektur nicht "
            f"verwertbar. Gründe je Prüfregel:\n{reasons}")
