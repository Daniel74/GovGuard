"""Writes the rule catalogs from the selection lists (ARCHITECTURE 1). Gets the model injected.

The file I/O of stage 5 lives here: selection lists and sources in, rules_*.json out.
"""

import json
import logging
from pathlib import Path

from pydantic_ai.models import Model

from govguard.models import AuditType
from kb_build.cfn_properties import CFN_PROPERTIES_FILE, PropertyIndex
from kb_build.cfn_types import CFN_TYPES_FILE, load_cfn_types
from kb_build.formulate import formulate_rules
from kb_build.quality import quality_report
from kb_build.selection_models import Selection
from kb_build.selection_run import SELECTIONS, BuildPaths, chosen, read_sources

logger = logging.getLogger("kb_build")

# every source, not only those of the audit type: cross references may point anywhere
ALL_SOURCES = [name for names in SELECTIONS.values() for name in names]


def read_property_index(data: Path) -> PropertyIndex:
    raw = json.loads((data / CFN_PROPERTIES_FILE.name).read_text(encoding="utf-8"))
    names = (t.rpartition("::")[2] for t in load_cfn_types(data / CFN_TYPES_FILE.name))
    return PropertyIndex({t: frozenset(paths) for t, paths in raw.items()}, frozenset(names))


def formulate_all(
    model: Model, paths: BuildPaths = BuildPaths(), only: AuditType | None = None
) -> None:
    """Per audit type (or just `only`): rules_*.json next to its selection list.

    A file is written only after the gate passed; otherwise the old catalog stays.
    """
    sources = read_sources(paths.data, ALL_SOURCES)
    properties = read_property_index(paths.data)
    for audit_type in chosen(only):
        raw = paths.out_file("selection", audit_type).read_text(encoding="utf-8")
        catalog = formulate_rules(
            model, Selection.model_validate_json(raw), sources, properties
        )
        rules_file = paths.out_file("rules", audit_type)
        rules_file.write_text(catalog.model_dump_json(indent=2) + "\n", encoding="utf-8")
        logger.info("%s: %d rules written to %s", audit_type, len(catalog.rules), rules_file)
        for source, counts in quality_report(catalog, properties).items():
            logger.info("%s quality %s: %s", audit_type, source, counts)
