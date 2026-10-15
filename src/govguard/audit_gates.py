"""Gates on the audit answer: pure checks, every problem becomes a retry prompt (DESIGN 2.2)."""

from collections import Counter

from govguard.corrections import Problem
from govguard.evidence import evidence_problem
from govguard.models import FindingDraft


def completeness_problems(expected: set[str], drafts: list[FindingDraft]) -> list[Problem]:
    """Exactly one finding per expected rule, no unknown rule IDs (DESIGN 2.2 step 2)."""
    counts = Counter(f.rule_id for f in drafts)
    return [
        Problem(rule_id, f"{label}: {rule_id}")
        for label, ids in [
            ("Befund fehlt für", sorted(expected - counts.keys())),
            ("Unbekannte rule_id", sorted(counts.keys() - expected)),
            # per package repairs.py keeps one finding per rule; guards the merged packages
            ("Mehr als ein Befund für", sorted(r for r, n in counts.items() if n > 1)),
        ]
        for rule_id in ids
    ]


def answer_problems(
    expected: set[str], drafts: list[FindingDraft], text: str, na_forbidden: str | None
) -> list[Problem]:
    """All gates on one answer; each problem is a line of the retry prompt (DESIGN 2.2)."""
    problems = completeness_problems(expected, drafts)
    problems += [p for f in drafts if (p := field_problem(f, text))]
    if na_forbidden:
        problems += [Problem(f.rule_id, f"{f.rule_id}: N/A ist verboten, die Prüfregel ist laut "
                                 "Ressourceninventar anwendbar")
                     for f in drafts if f.status == "N/A"]
    return problems


def field_problem(finding: FindingDraft, input_text: str) -> Problem | None:
    """Evidence by line reference (ADR 0017); WARN/FAIL need a recommendation."""
    if problem := evidence_problem(finding, input_text):
        return problem
    if finding.status in ("WARN", "FAIL") and not finding.recommendation:
        rule_id = finding.rule_id
        return Problem(rule_id, f"{rule_id}: Empfehlung fehlt (Pflicht bei {finding.status})")
    return None
