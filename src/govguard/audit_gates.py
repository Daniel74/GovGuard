"""Gates on the audit answer: pure checks, every problem becomes a retry prompt (DESIGN 2.2)."""

from collections import Counter

from govguard.evidence import evidence_problem
from govguard.models import FindingDraft


def completeness_problems(expected: set[str], drafts: list[FindingDraft]) -> list[str]:
    """Exactly one finding per expected rule, no unknown rule IDs (DESIGN 2.2 step 2)."""
    counts = Counter(f.rule_id for f in drafts)
    missing = sorted(expected - counts.keys())
    unknown = sorted(counts.keys() - expected)
    duplicate = sorted(rule_id for rule_id, n in counts.items() if n > 1)
    return [
        f"{label}: {', '.join(ids)}"
        for label, ids in [("Befund fehlt für", missing), ("Unbekannte rule_id", unknown),
                           ("Mehr als ein Befund für", duplicate)]
        if ids
    ]


def without_equal_duplicates(drafts: list[FindingDraft]) -> list[FindingDraft]:
    """Keep the first of several findings with the same rule and status; a contradiction stays."""
    seen: set[tuple[str, str]] = set()
    kept = []
    for draft in drafts:
        if (draft.rule_id, draft.status) not in seen:
            seen.add((draft.rule_id, draft.status))
            kept.append(draft)
    return kept


def field_problem(finding: FindingDraft, input_text: str) -> str | None:
    """Evidence by line reference (ADR 0017); WARN/FAIL need a recommendation."""
    if problem := evidence_problem(finding, input_text):
        return problem
    if finding.status in ("WARN", "FAIL") and not finding.recommendation:
        return f"{finding.rule_id}: Empfehlung fehlt (Pflicht bei {finding.status})"
    return None
