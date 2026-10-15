"""What the code repairs in the model's answer from the knowledge base, without a retry (#32).

Like a downgrade (ADR 0017): no retry, but a correction line in the finding.
"""

from govguard.corrections import Problem
from govguard.models import SEVERITY, FindingDraft, Rule

_RECOMMENDATION_PREFIX = {"WARN": "Falls nicht erfüllt: ", "FAIL": ""}  # WARN: maybe fine


def worst_of_duplicates(drafts: list[FindingDraft]) -> tuple[list[FindingDraft], list[Problem]]:
    """One finding per rule: the first with the worst status (DESIGN 2.1); equal ones silently."""
    by_rule: dict[str, list[FindingDraft]] = {}
    for draft in drafts:
        by_rule.setdefault(draft.rule_id, []).append(draft)
    kept, repairs = [], []
    for rule_id, same in by_rule.items():
        kept.append(max(same, key=lambda draft: SEVERITY[draft.status]))  # max keeps the first
        statuses = list(dict.fromkeys(draft.status for draft in same))
        if len(statuses) > 1:
            repairs.append(Problem(rule_id, f"{rule_id}: Widersprüchliche Befunde der KI "
                                   f"({', '.join(statuses)}): Der schwerere Status gilt."))
    return kept, repairs


def with_rule_recommendations(
    drafts: list[FindingDraft], rules: list[Rule]
) -> tuple[list[FindingDraft], list[Problem]]:
    """WARN and FAIL without a recommendation get the one of their rule."""
    by_id = {rule.id: rule for rule in rules}
    repaired, repairs = [], []
    for draft in drafts:
        rule = by_id.get(draft.rule_id)
        missing = draft.status in _RECOMMENDATION_PREFIX and not draft.recommendation
        if missing and rule and rule.recommendation:  # else the gate fails closed
            recommendation = _RECOMMENDATION_PREFIX[draft.status] + rule.recommendation
            draft = draft.model_copy(update={"recommendation": recommendation})
            repairs.append(Problem(draft.rule_id, f"{draft.rule_id}: Empfehlung aus der Prüfregel "
                                   f"ergänzt: Die KI hat bei {draft.status} keine genannt."))
        repaired.append(draft)
    return repaired, repairs
