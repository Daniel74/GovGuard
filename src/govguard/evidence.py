"""Evidence by line reference (ADR 0017): the model points to lines, the code cuts the quote."""

from govguard.models import FindingDraft
from govguard.text import MIN_QUOTE_LENGTH, normalize

MAX_SPAN = 200  # lines per evidence, about one section; 40 was too tight (prototype #26)


def numbered(text: str) -> str:
    """Prefix every line with its number, e.g. "12| ", so the model can point to it."""
    return "\n".join(f"{i}| {line}" for i, line in enumerate(text.splitlines(), 1))


def evidence_problem(draft: FindingDraft, text: str) -> str | None:
    """PASS needs a line range; any range must be valid. FAIL without one is downgraded."""
    lines = _lines(draft)
    if draft.status == "PASS" and lines is None:
        return f"{draft.rule_id}: Zeilenbereich fehlt (Pflicht bei PASS)"
    if lines and (problem := _range_problem(text, *lines)):
        return f"{draft.rule_id}: {problem}"
    return None


def without_unproven_fail(draft: FindingDraft) -> FindingDraft:
    """What is missing is WARN, not FAIL: the code enforces the prompt rule without a retry.

    At WARN/FAIL a range over MAX_SPAN counts as no range; only PASS is retried for it.
    """
    if draft.status in ("WARN", "FAIL") and _too_large(draft):
        draft = draft.model_copy(update={"line_start": None, "line_end": None})
    if draft.status == "FAIL" and _lines(draft) is None:
        return draft.model_copy(update={"status": "WARN"})
    return draft


def evidence_of(draft: FindingDraft, text: str) -> str | None:
    """The quote comes from the input, so it is verbatim by construction."""
    lines = _lines(draft)
    return _cut(text, *lines) if lines else None


def _lines(draft: FindingDraft) -> tuple[int, int] | None:
    """The line range, or None if the model gave none (a half range counts as none)."""
    if draft.line_start is None or draft.line_end is None:
        return None
    return draft.line_start, draft.line_end


def _too_large(draft: FindingDraft) -> bool:
    lines = _lines(draft)
    return lines is not None and lines[1] - lines[0] + 1 > MAX_SPAN


def _cut(text: str, line_start: int, line_end: int) -> str:
    """Lines line_start to line_end (1-based, inclusive), verbatim from the input."""
    return "\n".join(text.splitlines()[line_start - 1:line_end])


def _range_problem(text: str, line_start: int, line_end: int) -> str | None:
    """The range lies in the input, spans at most MAX_SPAN lines and proves something."""
    label = f"Zeilenbereich {line_start}-{line_end}"
    last = len(text.splitlines())
    if not 1 <= line_start <= line_end <= last:
        return f"{label} ungültig (die Eingabe hat die Zeilen 1-{last})"
    if line_end - line_start + 1 > MAX_SPAN:
        return f"{label} zu groß (höchstens {MAX_SPAN} Zeilen)"
    if len(normalize(_cut(text, line_start, line_end))) < MIN_QUOTE_LENGTH:
        return f"{label} zu kurz als Beleg (mind. {MIN_QUOTE_LENGTH} Zeichen)"
    return None
