"""Frozen catalog (ADR 0025, SPEC G13): old rules stay as they are, only missing ones are new."""

import hashlib
import json

from govguard.models import Rule, RuleCatalog
from kb_build.paths import BuildPaths
from kb_build.rules.frozen import merge, missing
from kb_build.select.models import SelectedRequirement, Selection


def selected(source: str, requirement_id: str) -> SelectedRequirement:
    return SelectedRequirement(requirement_id=requirement_id, source=source, rationale="Prüfbar.",
                               cfn_resource_types=[])


def rule(source: str, requirement_id: str, title: str = "alt") -> Rule:
    anchor = f"{source} {requirement_id}"
    return Rule(
        id=f"SPEC-{source}-{requirement_id.replace(' ', '')}", audit_type="spec", source=source,
        primary_anchor=anchor, selection_rationale="Prüfbar.", source_quote="Zitat", title=title,
        compliant_if="ok", violation_if="Verstoß", recommendation="Abhilfe",
    )


def catalog(rules: list[Rule], versions: dict[str, str], model_id: str = "old") -> RuleCatalog:
    return RuleCatalog(audit_type="spec", source_versions=versions, model_id=model_id, rules=rules)


SELECTION = Selection(audit_type="spec", model_id="m", selected=[
    selected("DSGVO", "Art. 5"), selected("SDM", "M60.D01"), selected("KI-VO", "Art. 50"),
])
EXISTING = catalog([rule("DSGVO", "Art. 5"), rule("DSGVO", "Art. 99"), rule("SDM", "M60.D01")],
                   {"DSGVO": "000.003", "SDM": "V1.0a"})


def test_missing_keeps_only_requirements_without_a_rule() -> None:
    todo = missing(SELECTION, EXISTING)

    assert [(s.source, s.requirement_id) for s in todo.selected] == [("KI-VO", "Art. 50")]
    assert (todo.audit_type, todo.model_id) == ("spec", "m")


def test_merge_keeps_old_rules_unchanged_in_selection_order() -> None:
    new = catalog([rule("KI-VO", "Art. 50", title="neu")], {"KI-VO": "001.002.0"}, "new")

    merged = merge(SELECTION, EXISTING, new)

    assert merged.rules == [EXISTING.rules[0], EXISTING.rules[2], new.rules[0]]  # Art. 99 dropped
    assert merged.source_versions == {"DSGVO": "000.003", "SDM": "V1.0a", "KI-VO": "001.002.0"}
    assert merged.model_id == "old"  # the frozen part names the catalog's origin


# Catalog of 18.10.2026 (step 12l): 151 rules from DSGVO and SDM, the base of every gallery report
FROZEN_RULES = 151
FROZEN_SHA256 = "b8a381b97460cd5884a602cc902f8595a8cd94d3e121625e599ec92324cc13ea"


def test_the_checked_in_spec_catalog_keeps_the_151_frozen_rules_byte_for_byte() -> None:
    # SPEC G13: changing them means a new gallery and new Soll results for every preset
    raw = json.loads((BuildPaths().knowledge_base / "rules_spec.json").read_text("utf-8"))
    frozen = [r for r in raw["rules"] if r["source"] in ("DSGVO", "SDM")]
    canonical = json.dumps(frozen, sort_keys=True, ensure_ascii=False).encode()

    assert len(frozen) == FROZEN_RULES
    assert hashlib.sha256(canonical).hexdigest() == FROZEN_SHA256
    assert raw["rules"][:FROZEN_RULES] == frozen  # new sources only append
