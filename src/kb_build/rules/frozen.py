"""Frozen catalog (ADR 0025, SPEC G13): old rules stay byte for byte, only missing ones cost a call.

Pure logic: the catalog on disk comes in, the merged catalog goes out; run.py does the I/O.
"""

from govguard.models import RuleCatalog
from kb_build.rules.formulate import rule_id
from kb_build.select.models import SelectedRequirement, Selection


def _id(selection: Selection, selected: SelectedRequirement) -> str:
    return rule_id(selection.audit_type, selected.source, selected.requirement_id)


def missing(selection: Selection, existing: RuleCatalog) -> Selection:
    """The selection without the requirements that already have a rule."""
    known = {r.id for r in existing.rules}
    todo = [s for s in selection.selected if _id(selection, s) not in known]
    return selection.model_copy(update={"selected": todo})


def merge(selection: Selection, existing: RuleCatalog, new: RuleCatalog) -> RuleCatalog:
    """Old and new rules in selection order; a rule no longer selected drops out."""
    by_id = {r.id: r for r in [*existing.rules, *new.rules]}
    rules = [by_id[_id(selection, s)] for s in selection.selected]
    used = {r.source for r in rules}
    versions = {**existing.source_versions, **new.source_versions}
    return existing.model_copy(update={  # model_id stays: the frozen part names the origin
        "rules": rules, "source_versions": {s: v for s, v in versions.items() if s in used},
    })
