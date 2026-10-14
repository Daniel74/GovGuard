"""What the code corrected in the model's answer: retry reasons and downgrades (#27).

A problem is `(rule_id, text)`; the text is the line the model reads in the retry prompt and
the reason the report shows (CONTEXT.md: Korrektur).
"""

from pydantic import BaseModel

from govguard.models import FindingDraft, Status

Problem = tuple[str, str]  # (rule_id, readable text)

SCHEMA_PROBLEM: Problem = ("", "Die Antwort der KI entsprach nicht dem vorgegebenen Schema.")

_DOWNGRADE_REASON: dict[Status, str] = {
    "FAIL": "FAIL ohne brauchbaren Zeilenbereich, was nicht belegt ist, wird WARN",
    "PASS": "PASS auch nach der Korrektur ohne brauchbaren Zeilenbereich, wird WARN",
}


Downgrades = dict[str, tuple[Status, str]]


def downgrades_of(before: list[FindingDraft], after: list[FindingDraft]) -> Downgrades:
    """rule_id -> (original status, reason) for findings the code set to WARN (ADR 0017)."""
    return {
        new.rule_id: (old.status, f"{new.rule_id}: {_DOWNGRADE_REASON[old.status]}")
        for old, new in zip(before, after, strict=True)
        if old.status in _DOWNGRADE_REASON and new.status == "WARN"
    }


class AuditValidationError(Exception):
    """LLM answer still invalid after the retry, or the model API failed; fail closed (HTTP 502).

    `problems` are the reasons of the last attempt, the same list later in the 502 body.
    """

    def __init__(self, problems: list[Problem], *, api_error: bool = False) -> None:
        self.problems, self.api_error = problems, api_error
        super().__init__("\n".join(text for _, text in problems) or "Der KI-Dienst ist ausgefallen")


class Corrections(BaseModel):
    """Collects what the validator corrects, over all packages of one audit."""

    downgrades: Downgrades = {}  # rule_id -> (original status, reason)
    retry_problems: list[Problem] = []  # every problem that sent a package back to the model
    retries: int = 0  # packages with a retry
    failed: list[Problem] = []  # problems of a last attempt: the audit fails closed (HTTP 502)

    def record_attempt(
        self, rule_ids: list[str], downgrades: Downgrades, problems: list[Problem],
        last_attempt: bool,
    ) -> None:
        """A downgrade counts only from the last attempt (the model answers anew after a
        retry); a retry reason stays, it is what the model was told."""
        for rule_id in rule_ids:
            self.downgrades.pop(rule_id, None)
        self.downgrades.update(downgrades)
        self.retry_problems += problems
        if last_attempt:
            self.failed += problems

    def unassigned(self, rule_ids: set[str]) -> list[str]:
        """Reasons that name no rule of the catalog, e.g. an invented rule_id."""
        return [text for id_, text in self.retry_problems if id_ not in rule_ids]

    def for_rule(self, rule_id: str) -> dict:
        """The fields `downgraded_from` and `corrections` of the finding of this rule."""
        original, reason = self.downgrades.get(rule_id, (None, None))
        reasons = [text for id_, text in self.retry_problems if id_ == rule_id]
        return {"downgraded_from": original, "corrections": reasons + ([reason] if reason else [])}
