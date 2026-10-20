"""Conditions: which rules hang on a condition, and what the evidence says (#60, ADR 0028).

Pure logic: the pre-run in calls/conditions.py only collects the evidence lines.
"""

from govguard.checks.evidence import range_problem
from govguard.condition_models import (
    ConditionDef,
    ConditionDraft,
    ConditionResult,
    ConditionValue,
)
from govguard.models import FindingDraft, Rule


def _hits(condition: ConditionDef, rule: Rule) -> bool:
    """An anchor ends at the article: "DSGVO Art. 4" hits "... Art. 4 Abs. 2", not "... Art. 44"."""
    anchored = any(rule.primary_anchor == a or rule.primary_anchor.startswith(f"{a} ")
                   for a in condition.anchors)
    return anchored or rule.id in condition.rule_ids


def rules_of(condition: ConditionDef, rules: list[Rule]) -> list[Rule]:
    return [rule for rule in rules if _hits(condition, rule)]


CONTRADICTION = ("Widerspruch: Die Spezifikation belegt und verneint die Bedingung, "
                 "es gilt ja (der strengere Wert).")
FROM_AI_SYSTEM = "Folgt aus: Die Spezifikation schließt ein KI-System aus."
AI_SYSTEM, HIGH_RISK = "ki_system", "high_risk_ai"


def _result(draft: ConditionDraft | None) -> ConditionResult:
    """Only affirming lines: yes. Only denying lines: no. Both: yes, the stricter value."""
    if draft is None or not (draft.affirming or draft.denying):
        return ConditionResult(value="unstated")
    value: ConditionValue = "yes" if draft.affirming else "no"
    return ConditionResult(
        value=value, affirming=draft.affirming, denying=draft.denying,
        note=CONTRADICTION if draft.affirming and draft.denying else None)


def condition_results(
    conditions: list[ConditionDef], drafts: list[ConditionDraft]
) -> dict[str, ConditionResult]:
    """One result per condition of the file; a condition the model left out is unstated."""
    first: dict[str, ConditionDraft] = {}
    for draft in drafts:
        first.setdefault(draft.condition_id, draft)
    results = {c.id: _result(first.get(c.id)) for c in conditions}
    return _high_risk_from_ai_system(results)


def _high_risk_from_ai_system(results: dict[str, ConditionResult]) -> dict[str, ConditionResult]:
    """No AI system means no high-risk system, with the evidence of the first denial."""
    ai, high = results.get(AI_SYSTEM), results.get(HIGH_RISK)
    if ai is None or high is None or ai.value != "no":
        return results
    if high.value == "yes":  # a contradiction stays visible, the stricter value wins
        return results | {HIGH_RISK: high.model_copy(update={"note": CONTRADICTION})}
    return results | {HIGH_RISK: ConditionResult(
        value="no", denying=ai.denying + high.denying, note=FROM_AI_SYSTEM,
        derived_from=AI_SYSTEM)}


def unstated_results(conditions: list[ConditionDef], note: str) -> dict[str, ConditionResult]:
    """The pre-run failed: nothing is denied, so every rule goes to the model (no fail closed)."""
    return {c.id: ConditionResult(value="unstated", note=note) for c in conditions}


def na_drafts(
    conditions: list[ConditionDef], results: dict[str, ConditionResult], rules: list[Rule]
) -> list[FindingDraft]:
    """N/A for the rules of every denied condition, with the first denying lines as evidence.

    A "no" derived from another condition names that one: it is the one the lines deny.
    """
    names = {c.id: c.name for c in conditions}
    return [
        FindingDraft(rule_id=rule.id, status="N/A", line_start=denial.line_start,
                     line_end=denial.line_end, recommendation=None,
                     rationale=f"Die Spezifikation verneint: "
                               f"{names[result.derived_from or condition.id]}.")
        for condition in conditions
        if (result := results[condition.id]).value == "no" and (denial := result.denying[0])
        for rule in rules_of(condition, rules)
    ]


def answer_problems(
    conditions: list[ConditionDef], drafts: list[ConditionDraft], input_text: str
) -> list[str]:
    """What is wrong with the answer: each condition exactly once, known ids, valid lines."""
    known = {c.id for c in conditions}
    given = [d.condition_id for d in drafts]
    problems = [f"Unbekannte Bedingung: {i}" for i in dict.fromkeys(given) if i not in known]
    problems += [f"Bedingung fehlt: {c.id}" for c in conditions if c.id not in given]
    problems += [f"Bedingung mehrfach: {i}" for i in dict.fromkeys(given)
                 if i in known and given.count(i) > 1]
    for draft in drafts:
        for lines in [*draft.affirming, *draft.denying]:
            if problem := range_problem(input_text, lines.line_start, lines.line_end):
                problems.append(f"{draft.condition_id}: {problem}")
    return problems
