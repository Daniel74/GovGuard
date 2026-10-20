"""Inputs that more than one build step reads: which sources belong to which audit type,
the sources themselves and the scope (ADR 0027). Each step reads them from here, never from
the `run.py` of another step.
"""

import json
from pathlib import Path

from govguard.models import AuditType, SourceName
from kb_build.extract.models import ExtractedSource
from kb_build.paths import BuildPaths
from kb_build.reference.scope import Scope

# audit type -> extracted sources in catalog order
SELECTIONS: dict[AuditType, list[SourceName]] = {
    "architecture": ["BSI", "C5", "CIS", "FSBP"],
    "spec": ["DSGVO", "SDM", "KI-VO"],  # DSGVO and KI-VO come decomposed (ADR 0026)
}


def chosen(only: AuditType | None) -> list[AuditType]:
    """Every audit type, or just `only`."""
    return [audit_type for audit_type in SELECTIONS if only in (None, audit_type)]


def read_sources(paths: BuildPaths, names: list[SourceName]) -> list[ExtractedSource]:
    """Legal acts come decomposed (#53), every other source as extracted."""
    files = [paths.source_file(name) for name in names]
    return [ExtractedSource.model_validate_json(f.read_text(encoding="utf-8")) for f in files]


def read_scope(path: Path) -> Scope:
    return Scope(json.loads(path.read_text(encoding="utf-8")))
