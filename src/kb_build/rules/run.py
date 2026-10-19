"""Writes the rule catalogs from the selection lists (ARCHITECTURE 1). Gets the model injected.

The file I/O of stage 5 lives here: selection lists and sources in, rules_*.json out.
"""

import json
import logging
from pathlib import Path

from pydantic_ai.models import Model

from govguard.models import AuditType, RuleCatalog
from kb_build.paths import BuildPaths
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.cfn_types import load_cfn_types
from kb_build.reference.run import read_scope
from kb_build.rules.catalog import formulate_rules
from kb_build.rules.frozen import merge, missing
from kb_build.rules.quality import quality_report
from kb_build.select.models import Selection
from kb_build.select.run import SELECTIONS, chosen, read_sources

logger = logging.getLogger("kb_build")

# every source, not only those of the audit type: cross references may point anywhere
ALL_SOURCES = [name for names in SELECTIONS.values() for name in names]


def read_property_index(paths: BuildPaths) -> PropertyIndex:
    raw = json.loads(paths.cfn_properties.read_text(encoding="utf-8"))
    names = (t.rpartition("::")[2] for t in load_cfn_types(paths.cfn_types))
    return PropertyIndex({t: frozenset(props) for t, props in raw.items()}, frozenset(names))


def _read_catalog(rules_file: Path) -> RuleCatalog:
    return RuleCatalog.model_validate_json(rules_file.read_text(encoding="utf-8"))


def formulate_all(
    model: Model, paths: BuildPaths = BuildPaths(), only: AuditType | None = None,
    only_missing: bool = False,
) -> None:
    """Per audit type (or just `only`): rules_*.json from its selection list.

    `only_missing` keeps the rules already on disk and formulates the rest (ADR 0025).
    A file is written only after the gate passed; otherwise the old catalog stays.
    """
    sources = read_sources(paths.extracted, ALL_SOURCES)
    properties = read_property_index(paths)
    scope = read_scope(paths.scope)
    for audit_type in chosen(only):
        rules_file = paths.out_file("rules", audit_type)
        raw = paths.out_file("selection", audit_type).read_text(encoding="utf-8")
        selection = Selection.model_validate_json(raw)
        if not only_missing:
            catalog = formulate_rules(model, selection, sources, properties, scope)
        else:
            existing = _read_catalog(rules_file)
            todo = missing(selection, existing)
            logger.info("%s: %d new rules to formulate", audit_type, len(todo.selected))
            new = formulate_rules(model, todo, sources, properties, scope) if todo.selected else (
                existing)  # nothing missing: an empty catalog would be invalid
            catalog = merge(selection, existing, new)
        rules_file.parent.mkdir(parents=True, exist_ok=True)  # only after the gate passed
        rules_file.write_text(catalog.model_dump_json(indent=2) + "\n", encoding="utf-8")
        logger.info("%s: %d rules written to %s", audit_type, len(catalog.rules), rules_file)
        for source, counts in quality_report(catalog, properties).items():
            logger.info("%s quality %s: %s", audit_type, source, counts)
