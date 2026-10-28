"""Checks of the measure proposal for one site (#82): the code, not the model, decides what the
reader sees. The model names line numbers inside the site and the code cuts the "before" from the
document, so it is verbatim by construction. The measures must not overlap and every WARN/FAIL
belongs to exactly one measure. Pure."""

import re
from collections import Counter

from govguard.checks.remediation_models import Measure, MeasureDraft
from govguard.checks.sites import Site
from govguard.models import Finding

MAX_MEASURES = 3
MIN_OPEN = 2  # fewer WARN/FAIL need no summary
OPEN_STATUS = ("WARN", "FAIL")
NUMBERED = re.compile(r"^>? *\d+\|(?: |$)")  # the line prefix of the marked document


class MeasureProblem(Exception):
    """The reasons the model must fix, one per line; the text is the retry prompt."""


def open_findings(site: Site) -> list[Finding]:
    return [f for f in site.findings if f.status in OPEN_STATUS]


def offers_measures(site: Site) -> bool:
    return len(open_findings(site)) >= MIN_OPEN


def _range_of(number: int, draft: MeasureDraft, site: Site, document: str,
              ) -> tuple[tuple[int, int] | None, str | None]:
    """The line range of the draft, or the reason it is unusable."""
    start, end = draft.from_line, draft.to_line
    where = f"Zeilen {site.line_start}–{site.line_end}"
    if not site.line_start <= start <= end <= site.line_end:
        return None, (f"Maßnahme {number}: from_line {start} und to_line {end} müssen in der "
                      f"Fundstelle liegen ({where}), und from_line darf nicht nach to_line "
                      "kommen.")
    if not "".join(document.splitlines()[start - 1:end]).strip():  # empty = "insert" (#85)
        return None, (f"Maßnahme {number}: Die Zeilen {start}–{end} sind leer. Nenne die Zeilen, "
                      "die sich ändern.")
    return (start, end), None


def _overlaps(ranges: dict[int, tuple[int, int]]) -> list[str]:
    numbers = sorted(ranges)
    return [f"Maßnahme {a} und Maßnahme {b} überschneiden sich im Vorher (Zeile "
            f"{max(ranges[a][0], ranges[b][0])}). Jede Zeile darf nur in einer Maßnahme stehen."
            for i, a in enumerate(numbers) for b in numbers[i + 1:]
            if ranges[a][0] <= ranges[b][1] and ranges[b][0] <= ranges[a][1]]


def _assignment_problems(drafts: list[MeasureDraft], site: Site) -> list[str]:
    open_ids = [f.rule_id for f in open_findings(site)]
    problems = [f"Maßnahme {n}: Keine Regel-ID. Jede Maßnahme behebt mindestens einen Befund."
                for n, d in enumerate(drafts, 1) if not d.rule_ids]
    problems += [f"Maßnahme {n}: {rule_id} ist kein WARN oder FAIL dieser Fundstelle."
                for n, d in enumerate(drafts, 1) for rule_id in d.rule_ids
                if rule_id not in open_ids]
    counted = Counter(rule_id for d in drafts for rule_id in set(d.rule_ids) if rule_id in open_ids)
    problems += [f"{rule_id} steht in mehreren Maßnahmen, es gehört zu genau einer."
                 for rule_id, n in counted.items() if n > 1]
    if missing := [rule_id for rule_id in open_ids if rule_id not in counted]:
        problems.append(f"Keiner Maßnahme zugeordnet: {', '.join(missing)}.")
    return problems


def resolve_measures(drafts: list[MeasureDraft], site: Site, document: str) -> list[Measure]:
    """The measures of the model as checked ones, or MeasureProblem with every reason at once."""
    problems = [f"Höchstens {MAX_MEASURES} Maßnahmen, du hast {len(drafts)} abgegeben."] \
        if len(drafts) > MAX_MEASURES else []
    ranges: dict[int, tuple[int, int]] = {}
    for number, draft in enumerate(drafts, 1):
        found, reason = _range_of(number, draft, site, document)
        if found:
            ranges[number] = found
        if reason:
            problems.append(reason)
    problems += _overlaps(ranges) + _assignment_problems(drafts, site)
    if problems:
        raise MeasureProblem("\n".join(problems))
    return [_measure(d, ranges[n], site, document) for n, d in enumerate(drafts, 1)]


def _measure(draft: MeasureDraft, lines: tuple[int, int], site: Site, document: str) -> Measure:
    start, end = lines
    anchors = {f.rule_id: f.primary_anchor for f in site.findings}
    unique = list(dict.fromkeys(anchors[rule_id] for rule_id in draft.rule_ids))
    return Measure(sentence=draft.sentence, after=_unnumbered(draft.after), rule_ids=draft.rule_ids,
                   before="\n".join(document.splitlines()[start - 1:end]),
                   line_start=start, line_end=end, anchors=unique)


def _unnumbered(after: str) -> str:
    """The after without the "43| " the model copied from the marked document. Only when every
    line carries it: a single numbered line may be content."""
    lines = after.splitlines()
    if not any(lines) or not all(NUMBERED.match(line) for line in lines if line.strip()):
        return after
    return "\n".join(NUMBERED.sub("", line, count=1) for line in lines)
