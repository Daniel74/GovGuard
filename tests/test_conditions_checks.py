"""Conditions: the code decides yes/no/unstated from the evidence lines (#60, ADR 0028)."""

from conftest import make_rule

from govguard.checks.conditions import condition_results, na_drafts, unstated_results
from govguard.condition_models import ConditionDef, ConditionDraft, LineRange
from govguard.models import CodeDraft

LINES = [LineRange(line_start=3, line_end=4)]
OTHER = [LineRange(line_start=9, line_end=9)]


def definition(condition_id: str, anchors: list[str] | None = None) -> ConditionDef:
    return ConditionDef(id=condition_id, name=f"Name {condition_id}", only_if="x", meaning="m",
                        yes="y", no="n", anchors=anchors or [])


def draft(condition_id: str, affirming=(), denying=()) -> ConditionDraft:
    return ConditionDraft(condition_id=condition_id, affirming=list(affirming),
                          denying=list(denying))


DEFS = [definition("ki_system"), definition("high_risk_ai"), definition("consent")]


def values(drafts: list[ConditionDraft]) -> dict[str, str]:
    return {k: v.value for k, v in condition_results(DEFS, drafts).items()}


def test_only_affirming_lines_mean_yes() -> None:
    results = condition_results(DEFS, [draft("consent", affirming=LINES)])

    assert (results["consent"].value, results["consent"].affirming) == ("yes", LINES)


def test_only_denying_lines_mean_no() -> None:
    results = condition_results(DEFS, [draft("consent", denying=LINES)])

    assert (results["consent"].value, results["consent"].denying) == ("no", LINES)


def test_no_lines_mean_unstated_silence_is_not_a_no() -> None:
    assert values([draft("consent")])["consent"] == "unstated"


def test_a_condition_the_model_did_not_name_is_unstated() -> None:
    assert values([])["consent"] == "unstated"


def test_both_kinds_of_lines_mean_yes_with_a_contradiction_note() -> None:
    result = condition_results(DEFS, [draft("consent", LINES, OTHER)])["consent"]

    assert result.value == "yes"
    assert result.note is not None and "Widerspruch" in result.note
    assert (result.affirming, result.denying) == (LINES, OTHER)  # both stay visible


def test_no_ai_system_means_no_high_risk_system_with_the_evidence_of_the_ai_system() -> None:
    results = condition_results(DEFS, [draft("ki_system", denying=LINES)])

    assert results["high_risk_ai"].value == "no"
    assert results["high_risk_ai"].denying == LINES


def test_own_denying_lines_of_the_high_risk_system_stay_next_to_the_ai_system_evidence() -> None:
    results = condition_results(DEFS, [draft("ki_system", denying=LINES),
                                       draft("high_risk_ai", denying=OTHER)])

    assert results["high_risk_ai"].denying == LINES + OTHER
    assert results["high_risk_ai"].derived_from == "ki_system"


def test_the_high_risk_rules_are_na_because_the_ai_system_is_denied() -> None:
    defs = [definition("ki_system", anchors=["DSGVO Art. 7"]),
            definition("high_risk_ai", anchors=["DSGVO Art. 13"])]
    rules = [make_rule("Art.7", "A"), make_rule("Art.13", "B")]
    results = condition_results(defs, [draft("ki_system", denying=LINES)])

    assert na_drafts(defs, results, rules) == [
        na_draft("SPEC-DSGVO-Art.7", "Die Spezifikation verneint: Name ki_system."),
        na_draft("SPEC-DSGVO-Art.13", "Die Spezifikation verneint: Name ki_system.")]


def test_a_high_risk_system_stays_yes_when_the_ai_system_is_denied() -> None:
    results = condition_results(DEFS, [draft("ki_system", denying=LINES),
                                       draft("high_risk_ai", affirming=OTHER)])

    assert results["high_risk_ai"].value == "yes"  # the stricter value
    assert "Widerspruch" in (results["high_risk_ai"].note or "")


def test_an_unstated_ai_system_does_not_decide_the_high_risk_system() -> None:
    assert values([draft("high_risk_ai", denying=LINES)])["high_risk_ai"] == "no"
    assert values([])["high_risk_ai"] == "unstated"


def test_unstated_results_carry_the_reason() -> None:
    results = unstated_results(DEFS, "Vorlauf nicht verfügbar")

    assert {r.value for r in results.values()} == {"unstated"}
    assert {r.note for r in results.values()} == {"Vorlauf nicht verfügbar"}


def test_a_denied_condition_makes_its_rules_na_with_the_denying_lines() -> None:
    defs = [definition("consent", anchors=["DSGVO Art. 7"])]
    rules = [make_rule("Art.7", "Einwilligung"), make_rule("Art.9", "Besondere Kategorien")]
    results = condition_results(defs, [draft("consent", denying=LINES + OTHER)])

    assert na_drafts(defs, results, rules) == [
        na_draft("SPEC-DSGVO-Art.7", "Die Spezifikation verneint: Name consent.")]


def na_draft(rule_id: str, rationale: str) -> CodeDraft:
    return CodeDraft(rule_id=rule_id, status="N/A", line_start=3, line_end=4,
                     rationale=rationale, recommendation=None, by_code=["rationale"])


def test_yes_and_unstated_conditions_keep_their_rules_for_the_model() -> None:
    defs = [definition("consent", anchors=["DSGVO Art. 7"])]
    rules = [make_rule("Art.7", "Einwilligung")]

    assert na_drafts(defs, condition_results(defs, [draft("consent", affirming=LINES)]),
                     rules) == []
    assert na_drafts(defs, unstated_results(defs, "x"), rules) == []
