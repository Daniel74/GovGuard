"""Frozen catalog (ADR 0025, SPEC G13): old rules stay byte for byte, only missing ones cost a call.

Pure logic: the catalog on disk comes in, the merged catalog goes out; run.py does the I/O.
"""

from govguard.models import RuleCatalog
from kb_build.rules.formulate import code_quote, rule_id
from kb_build.rules.gates import Anchors
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


def quoted_by_code(catalog: RuleCatalog, anchors: Anchors) -> RuleCatalog:
    """Every part of a decomposed act carries the code's quote, also a rule of an earlier run
    (ADR 0026). Any other rule keeps its own quote, byte for byte.
    """
    rules = []
    for rule in catalog.rules:
        found = anchors.get(rule.primary_anchor)
        quote = code_quote(found[1]) if found and found[1].primary_anchor == rule.primary_anchor \
            else None
        rules.append(rule.model_copy(update={"source_quote": quote}) if quote else rule)
    return catalog.model_copy(update={"rules": rules})
