"""Frozen catalog (ADR 0025, SPEC G13): old rules stay as they are, only missing ones are new."""

import hashlib
import json

from govguard.models import Rule, RuleCatalog
from kb_build.extract.models import Requirement
from kb_build.paths import BuildPaths
from kb_build.rules.frozen import merge, missing, quoted_by_code
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


# Frozen catalog (step 12l): 116 SDM rules. DSGVO is decomposed anew (#53, ADR 0026);
# the SDM rules stay byte for byte, and with them their cross references to whole articles
FROZEN_RULES = 116
FROZEN_SHA256 = "47e0186e60590f63894a26a456537315e9647f55af8562f8ef2b344eb65c0bc3"


def test_the_checked_in_spec_catalog_keeps_the_116_frozen_sdm_rules_byte_for_byte() -> None:
    # SPEC G13: changing them means a new gallery and new Soll results for every preset
    raw = json.loads((BuildPaths().knowledge_base / "rules_spec.json").read_text("utf-8"))
    frozen = [r for r in raw["rules"] if r["source"] == "SDM"]
    canonical = json.dumps(frozen, sort_keys=True, ensure_ascii=False).encode()

    assert len(frozen) == FROZEN_RULES
    assert hashlib.sha256(canonical).hexdigest() == FROZEN_SHA256


def test_parts_of_a_decomposed_act_get_the_code_quote_and_sdm_keeps_its_own() -> None:
    # ADR 0026: a rule of an earlier run gets the quote of its section, no LLM call
    part = Requirement(id="Art. 5 Abs. 1 lit. a", title="t", text="Daten müssen a) rechtmäßig sein",
                       primary_anchor="DSGVO Art. 5 Abs. 1 lit. a", prefilter_passed=True,
                       attributes={"article": "Art. 5", "quote": "a) rechtmäßig sein"})
    sdm = Requirement(id="M60.D01", title="t", text="Zitat", primary_anchor="SDM M60.D01",
                      attributes={}, prefilter_passed=True)
    anchors = {"DSGVO Art. 5 Abs. 1 lit. a": ("DSGVO", part), "DSGVO Art. 5": ("DSGVO", part),
               "SDM M60.D01": ("SDM", sdm)}
    old = catalog([rule("DSGVO", "Art. 5 Abs. 1 lit. a"), rule("DSGVO", "Art. 5"),
                   rule("SDM", "M60.D01")], {})

    quotes = [r.source_quote for r in quoted_by_code(old, anchors).rules]

    assert quotes == ["a) rechtmäßig sein", "Zitat", "Zitat"]  # an article anchor is no part
