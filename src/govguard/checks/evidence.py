"""Evidence by line reference (ADR 0017): the model points to lines, the code cuts the quote."""

from govguard.checks.corrections import Correction, Problem
from govguard.models import FindingDraft
from govguard.text import MIN_QUOTE_LENGTH, too_short_to_prove

MAX_SPAN = 200  # lines per evidence, about one section; 40 was too tight (prototype #26)
UNPROVEN_PASS = ("Einhaltung selbst prüfen: Die KI hat PASS vergeben, aber auch nach einer "
                 "Korrektur keinen brauchbaren Zeilenbereich als Beleg genannt.")
NUMBERED_LINES = 'Jede Zeile der Eingabe beginnt mit ihrer Nummer, z. B. "12| ".'  # prompt hint


def numbered(text: str) -> str:
    """Prefix every line with its number, e.g. "12| ", so the model can point to it."""
    return "\n".join(f"{i}| {line}" for i, line in enumerate(text.splitlines(), 1))


def evidence_problem(draft: FindingDraft, text: str) -> Problem | None:
    """PASS needs a line range; any range must be valid. FAIL without one is downgraded."""
    lines = _lines(draft)
    label = f"{draft.rule_id} ({draft.status})"  # the status shows in the fail-closed message
    if draft.status == "PASS" and lines is None:
        return Problem(draft.rule_id, f"{label}: Zeilenbereich fehlt (Pflicht bei PASS)")
    if lines and (problem := range_problem(text, *lines)):
        return Problem(draft.rule_id, f"{label}: {problem}")
    return None


def without_unproven_verdict(draft: FindingDraft, text: str, last_attempt: bool) -> FindingDraft:
    """What is not proven is WARN: FAIL at once, PASS only after its retry (ADR 0017).

    Only PASS needs a usable range; at WARN, FAIL and N/A an unusable one counts as no range.
    """
    lines = _lines(draft)
    if draft.status != "PASS" and lines and range_problem(text, *lines):
        draft = draft.model_copy(update={"line_start": None, "line_end": None})
    if draft.status == "FAIL" and _lines(draft) is None:
        return draft.model_copy(update={"status": "WARN"})
    if draft.status == "PASS" and last_attempt and evidence_problem(draft, text):
        return draft.model_copy(update={"status": "WARN", "line_start": None, "line_end": None,
                                        "recommendation": UNPROVEN_PASS})
    return draft


def dropped_ranges(
    before: list[FindingDraft], after: list[FindingDraft], text: str
) -> list[Correction]:
    """A range dropped at WARN, FAIL or N/A stays visible as a correction (#74); an unproven
    PASS already shows its retry reason and its downgrade."""
    return [
        Correction(old.rule_id,
                   f"{old.rule_id}: {range_problem(text, *lines)}, vom Code gestrichen")
        for old, new in zip(before, after, strict=True)
        if old.status != "PASS" and (lines := _lines(old)) and _lines(new) is None
    ]


def evidence_of(draft: FindingDraft, text: str) -> str | None:
    """The quote comes from the input, so it is verbatim by construction."""
    lines = _lines(draft)
    return _cut(text, *lines) if lines else None


def _lines(draft: FindingDraft) -> tuple[int, int] | None:
    """The line range, or None if the model gave none (a half range counts as none)."""
    if draft.line_start is None or draft.line_end is None:
        return None
    return draft.line_start, draft.line_end


def _cut(text: str, line_start: int, line_end: int) -> str:
    """Lines line_start to line_end (1-based, inclusive), verbatim incl. line breaks (CRLF)."""
    lines = text.splitlines(keepends=True)[line_start - 1:line_end]
    if not lines:
        return ""
    return "".join(lines[:-1]) + lines[-1].splitlines()[0]  # without the final line break


def range_problem(text: str, line_start: int, line_end: int) -> str | None:
    """The range lies in the input, spans at most MAX_SPAN lines and proves something."""
    label = f"Zeilenbereich {line_start}-{line_end}"
    last = len(text.splitlines())
    if not 1 <= line_start <= line_end <= last:
        return f"{label} ungültig (die Eingabe hat die Zeilen 1-{last})"
    if line_end - line_start + 1 > MAX_SPAN:
        return f"{label} zu groß (höchstens {MAX_SPAN} Zeilen)"
    if too_short_to_prove(_cut(text, line_start, line_end)):
        return f"{label} zu kurz als Beleg (mind. {MIN_QUOTE_LENGTH} Zeichen)"
    return None
