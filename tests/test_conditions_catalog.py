"""conditions.json: every condition hangs on rules of the catalog, no rule on two (#60)."""

import json
from pathlib import Path

import pytest
from conftest import make_rule

from govguard.checks.conditions import rules_of
from govguard.condition_models import ConditionDef
from govguard.models import Rule, RuleCatalog

DATA = Path("data")
IDS = ["ki_system", "high_risk_ai", "third_country", "processor", "consent", "multi_tenant",
       "automated_decision"]


@pytest.fixture(scope="module")
def conditions() -> list[ConditionDef]:
    raw = json.loads((DATA / "input/conditions.json").read_text(encoding="utf-8"))
    return [ConditionDef.model_validate(item) for item in raw]


@pytest.fixture(scope="module")
def catalog() -> RuleCatalog:
    return RuleCatalog.model_validate_json(
        (DATA / "knowledge_base/rules_spec.json").read_bytes())


def test_the_seven_conditions_are_in_the_file(conditions: list[ConditionDef]) -> None:
    assert [c.id for c in conditions] == IDS


def test_every_condition_hits_at_least_one_rule_of_the_catalog(
    conditions: list[ConditionDef], catalog: RuleCatalog
) -> None:
    assert {c.id: len(rules_of(c, catalog.rules)) for c in conditions if
            not rules_of(c, catalog.rules)} == {}


def test_no_rule_hangs_on_two_conditions(
    conditions: list[ConditionDef], catalog: RuleCatalog
) -> None:
    owners: dict[str, list[str]] = {}
    for condition in conditions:
        for rule in rules_of(condition, catalog.rules):
            owners.setdefault(rule.id, []).append(condition.id)
    assert {rule_id: ids for rule_id, ids in owners.items() if len(ids) > 1} == {}


def test_every_condition_has_texts_for_the_prompt_and_the_ui(
    conditions: list[ConditionDef],
) -> None:
    for condition in conditions:
        assert all([condition.name, condition.only_if, condition.meaning, condition.yes,
                    condition.no])


def with_anchor(requirement_id: str, anchor: str) -> Rule:
    return make_rule(requirement_id, "Titel").model_copy(update={"primary_anchor": anchor})


def test_an_article_anchor_stops_at_the_article_boundary() -> None:
    art_4 = ConditionDef(id="x", name="X", only_if="x", meaning="m", yes="y", no="n",
                         anchors=["DSGVO Art. 4"])
    rules = [with_anchor("Art.44", "DSGVO Art. 44 Abs. 1"), make_rule("Art.4", "Begriffe"),
             with_anchor("Art.4b", "DSGVO Art. 4 Abs. 2"), with_anchor("Art.4a", "DSGVO Art. 4a")]

    assert [r.id for r in rules_of(art_4, rules)] == ["SPEC-DSGVO-Art.4", "SPEC-DSGVO-Art.4b"]


def test_a_rule_id_list_picks_rules_without_an_article() -> None:
    by_id = ConditionDef(id="x", name="X", only_if="x", meaning="m", yes="y", no="n",
                         rule_ids=["SPEC-DSGVO-Art.7"])

    assert [r.id for r in rules_of(by_id, [make_rule("Art.7", "A"), make_rule("Art.8", "B")])] \
        == ["SPEC-DSGVO-Art.7"]


def test_the_catalog_assignment_of_the_prompt_comment() -> None:
    """DSGVO Art. 44-49 for third_country, Art. 28 and 29 for the processor, and so on."""
    # the numbers of the sources the issue names; the counts guard against a drifting list
    raw = json.loads((DATA / "input/conditions.json").read_text(encoding="utf-8"))
    anchors = {item["id"]: item.get("anchors", []) for item in raw}
    # Art. 47 (BCR) is prefiltered for authorities (ADR 0028): an anchor without a rule is dead
    assert anchors["third_country"] == [f"DSGVO Art. {n}" for n in (44, 45, 46, 48, 49)]
    assert anchors["processor"] == ["DSGVO Art. 28", "DSGVO Art. 29"]
    assert anchors["consent"] == ["DSGVO Art. 7", "DSGVO Art. 8"]
    assert anchors["automated_decision"] == ["DSGVO Art. 22"]
    assert anchors["ki_system"] == [f"KI-VO Art. {n}" for n in (4, 5, 6, 50)]
    assert anchors["high_risk_ai"] == [f"KI-VO Art. {n}" for n in (13, 14, 26, 27)]
