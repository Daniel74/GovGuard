"""What the code corrected in the model's answer: retry reasons and downgrades (#27).

A problem is `(rule_id, text)` the model must fix: the text is the line it reads in the retry
prompt and the reason the report shows. A correction has the same shape, but the code acted
itself, without a retry (CONTEXT.md: Korrektur).
"""

from typing import NamedTuple

from pydantic import BaseModel
from pydantic_ai.exceptions import ModelAPIError, ModelHTTPError

from govguard.models import FailJudgeCount, FindingDraft, Status


class Problem(NamedTuple):
    rule_id: str  # "" when no rule is meant, e.g. a broken schema or the resource inventory
    text: str  # readable reason, the same line in the retry prompt and in the report


class Correction(NamedTuple):
    rule_id: str
    text: str  # readable reason in the report, e.g. a repair or a verdict of the FAIL judge


SCHEMA_PROBLEM = Problem("", "Die Antwort der KI entsprach nicht dem vorgegebenen Schema.")

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


def service_down(error: Exception) -> bool:
    """Throttled or down, not an invalid answer; Groq rejects a broken tool call with HTTP 400,
    that is an invalid answer too (#26)."""
    invalid = isinstance(error, ModelHTTPError) and error.status_code == 400
    return isinstance(error, ModelAPIError) and not invalid


class AuditValidationError(Exception):
    """LLM answer still invalid after the retry, or the model API failed; fail closed (HTTP 502).

    `problems` are the reasons of the last attempt, the same list later in the 502 body.
    """

    def __init__(self, problems: list[Problem], *, api_error: bool = False) -> None:
        self.problems, self.api_error = problems, api_error
        super().__init__("\n".join(p.text for p in problems) or "Der KI-Dienst ist ausgefallen")


class Corrections(BaseModel):
    """Collects what the validator corrects, over all packages of one audit."""

    downgrades: Downgrades = {}  # rule_id -> (original status, reason)
    repairs: list[Correction] = []  # what the code filled in or chose itself, no retry (#32)
    retry_problems: list[Problem] = []  # every problem that sent a package back to the model
    retries: int = 0  # packages (and the pre-run and the FAIL judge) with a retry
    failed: list[Problem] = []  # problems of a last attempt: the audit fails closed (HTTP 502)
    verdicts: list[Correction] = []  # verdicts of the FAIL judge that keep the FAIL (#31)
    fail_judge: FailJudgeCount = FailJudgeCount()

    def record_verdict(self, rule_id: str, confirmed: bool, text: str) -> None:
        """A rejected FAIL becomes WARN like an unproven one (ADR 0017), without a retry."""
        self.fail_judge.checked += 1
        if confirmed:
            self.fail_judge.confirmed += 1
            self.verdicts.append(
                Correction(rule_id, f"{rule_id}: Prüfer bestätigt das FAIL: {text}"))
        else:
            self.fail_judge.downgraded += 1
            self.downgrades[rule_id] = (
                "FAIL", f"{rule_id}: Prüfer bestätigt das FAIL nicht, wird WARN: {text}")

    def record_unchecked(self, rule_id: str, reason: str) -> None:
        """No verdict: the FAIL stays, the stricter status (#31)."""
        self.fail_judge.checked += 1
        self.fail_judge.unavailable += 1
        self.verdicts.append(
            Correction(rule_id, f"{rule_id}: Prüfer nicht verfügbar ({reason}), FAIL ungeprüft"))

    def record_retry(self, reason_sent: bool) -> None:
        """Once per package, on its retry; without a reason from the code the schema broke."""
        self.retries += 1
        if not reason_sent:
            self.retry_problems.append(SCHEMA_PROBLEM)

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

    def record_repairs(self, rule_ids: set[str], repairs: list[Correction]) -> None:
        """Like a downgrade, a repair counts only from the last attempt."""
        self.repairs = [c for c in self.repairs if c.rule_id not in rule_ids] + repairs

    def fail_closed(self, error: Exception) -> AuditValidationError:
        """Throttled or down: own sentence. Invalid after the retry: its reasons."""
        if service_down(error):
            return AuditValidationError([], api_error=True)
        return AuditValidationError(self.failed or [SCHEMA_PROBLEM])

    def unassigned(self, rule_ids: set[str]) -> list[str]:
        """Reasons that name no rule of the catalog, e.g. an invented rule_id."""
        return [p.text for p in self.retry_problems if p.rule_id not in rule_ids]

    def for_rule(self, rule_id: str) -> dict:
        """The fields `downgraded_from` and `corrections` of the finding of this rule."""
        original, reason = self.downgrades.get(rule_id, (None, None))
        reasons = [r.text for r in [*self.retry_problems, *self.repairs, *self.verdicts]
                   if r.rule_id == rule_id]
        return {"downgraded_from": original, "corrections": reasons + ([reason] if reason else [])}
