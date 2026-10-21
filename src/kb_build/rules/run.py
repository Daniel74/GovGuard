"""Writes the rule catalogs from the selection lists (ARCHITECTURE 5.1). Gets the model injected.

The file I/O of stage 5 lives here: selection lists and sources in, rules_*.json out.
"""

import json
import logging
from pathlib import Path

from pydantic import TypeAdapter
from pydantic_ai.models import Model

from govguard.models import AuditType, Rule, RuleCatalog
from kb_build.build_inputs import SELECTIONS, chosen, read_scope, read_sources
from kb_build.paths import BuildPaths
from kb_build.reference.cfn_properties import PropertyIndex
from kb_build.reference.cfn_types import load_cfn_types
from kb_build.rules.catalog import RuleInputs, formulate_rules
from kb_build.rules.frozen import merge, missing, quoted_by_code
from kb_build.rules.gates import check_rules, requirements_by_anchor
from kb_build.rules.quality import quality_report
from kb_build.select.models import Selection

logger = logging.getLogger("kb_build")

# every source, not only those of the audit type: cross references may point anywhere
ALL_SOURCES = [name for names in SELECTIONS.values() for name in names]


def read_property_index(paths: BuildPaths) -> PropertyIndex:
    raw = json.loads(paths.cfn_properties.read_text(encoding="utf-8"))
    names = (t.rpartition("::")[2] for t in load_cfn_types(paths.cfn_types))
    return PropertyIndex({t: frozenset(props) for t, props in raw.items()}, frozenset(names))


_RULES = TypeAdapter(list[Rule])


def _read_catalog(rules_file: Path) -> RuleCatalog:
    return RuleCatalog.model_validate_json(rules_file.read_text(encoding="utf-8"))


def _read_checkpoint(path: Path) -> list[Rule]:
    return _RULES.validate_json(path.read_bytes()) if path.exists() else []


def _formulate_missing(
    model: Model, selection: Selection, inputs: RuleInputs, paths: BuildPaths
) -> RuleCatalog:
    """Keeps the rules on disk and those of an aborted run (checkpoint); formulates the rest.

    Every new valid rule goes to the checkpoint at once, so an abort loses nothing paid (#53).
    The merged catalog passes the whole gate: the frozen rules' cross references included.
    """
    checkpoint = paths.rules_checkpoint(selection.audit_type)
    existing, saved = _read_catalog(paths.out_file("rules", selection.audit_type)), []
    saved.extend(_read_checkpoint(checkpoint))
    known = existing.model_copy(update={"rules": [*existing.rules, *saved]})
    todo = missing(selection, known)
    logger.info("%s: %d new rules to formulate, %d from the checkpoint", selection.audit_type,
                len(todo.selected), len(saved))

    def save(rule: Rule) -> None:
        saved.append(rule)
        checkpoint.write_bytes(_RULES.dump_json(saved, indent=2) + b"\n")

    new = formulate_rules(model, todo, inputs, on_rule=save) if (
        todo.selected) else known  # nothing missing: an empty catalog would be invalid
    catalog = quoted_by_code(merge(selection, known, new), requirements_by_anchor(inputs.sources))
    check_rules(catalog, selection, inputs.sources, inputs.scope)
    return catalog


def formulate_all(
    model: Model, paths: BuildPaths = BuildPaths(), only: AuditType | None = None,
    only_missing: bool = False,
) -> None:
    """Per audit type (or just `only`): rules_*.json from its selection list.

    `only_missing` keeps the rules already on disk and formulates the rest (ADR 0025).
    A file is written only after the gate passed; otherwise the old catalog stays.
    """
    if only_missing and only != "spec":
        raise ValueError("--only-missing is built only for the spec audit (ADR 0025)")
    properties = read_property_index(paths)
    inputs = RuleInputs(read_sources(paths, ALL_SOURCES), properties, read_scope(paths.scope))
    for audit_type in chosen(only):
        rules_file = paths.out_file("rules", audit_type)
        raw = paths.out_file("selection", audit_type).read_text(encoding="utf-8")
        selection = Selection.model_validate_json(raw)
        if not only_missing:
            catalog = formulate_rules(model, selection, inputs)
        else:
            catalog = _formulate_missing(model, selection, inputs, paths)
        rules_file.parent.mkdir(parents=True, exist_ok=True)  # only after the gate passed
        rules_file.write_text(catalog.model_dump_json(indent=2) + "\n", encoding="utf-8")
        paths.rules_checkpoint(audit_type).unlink(missing_ok=True)  # the catalog holds it now
        logger.info("%s: %d rules written to %s", audit_type, len(catalog.rules), rules_file)
        for source, counts in quality_report(catalog, properties).items():
            logger.info("%s quality %s: %s", audit_type, source, counts)
