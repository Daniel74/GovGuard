"""PROTOTYPE #26, throwaway: evidence by line reference instead of a verbatim quote.

The code numbers the input, the LLM returns only line_start/line_end, the code cuts the quote.
Bedrock: ToolOutput(strict=True), forced tool choice (ADR 0005).
Groq: NativeOutput, json_schema strict with constrained decoding (deviation, ADR 0016).
Hooked in by `.claude/skills/audit-messen/measure.py` with MEASURE_EVIDENCE=ref. Pure, no boto3.
"""

import sys
from collections import Counter

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext, ToolOutput
from pydantic_ai.models import Model

from govguard import audit_engine
from govguard.audit_engine import AuditDeps, _completeness_problems, _user_prompt
from govguard.models import FindingDraft, Status
from govguard.text import MIN_QUOTE_LENGTH, normalize

MAX_SPAN = 200  # lines per evidence, about one section; 15 and 40 were too tight

PROMPT = audit_engine.SYSTEM_PROMPT.replace(
    'Jedes "evidence" ist ein wörtliches Zitat aus der Eingabe (mindestens 15 Zeichen).',
    'Jede Zeile der Eingabe beginnt mit ihrer Nummer, z. B. "12| ". Belege per Zeilenbereich:\n'
    '"line_start" und "line_end" nennen die Zeilen, die den Befund belegen '
    f"(höchstens {MAX_SPAN} Zeilen). Bei PASS und FAIL sind sie Pflicht, sonst null.",
).replace('Bei PASS und FAIL ist "evidence" Pflicht.\n', "")


class FindingRefDraft(BaseModel):  # every field required, no defaults: Groq strict
    rule_id: str
    status: Status
    line_start: int | None
    line_end: int | None
    rationale: str
    recommendation: str | None


class AuditRefResponse(BaseModel):
    findings: list[FindingRefDraft]


_NAME, _DESCRIPTION = "submit_audit", "Gib genau einen Befund je Prüfregel ab."
_bedrock_agent = Agent(
    output_type=ToolOutput(AuditRefResponse, name=_NAME, description=_DESCRIPTION, strict=True),
    instructions=PROMPT, deps_type=AuditDeps, retries=1,
)
_groq_agent = Agent(
    output_type=NativeOutput(AuditRefResponse, name=_NAME, description=_DESCRIPTION, strict=True),
    instructions=PROMPT, deps_type=AuditDeps, retries=1,
)


def numbered(text: str) -> str:
    return "\n".join(f"{i}| {line}" for i, line in enumerate(text.splitlines(), 1))


def cut(text: str, start: int, end: int) -> str:
    return "\n".join(text.splitlines()[start - 1:end])


def _validate(ctx: RunContext[AuditDeps], response: AuditRefResponse) -> AuditRefResponse:
    expected = {rule.id for rule in ctx.deps.rules}
    drafts = [FindingDraft(rule_id=f.rule_id, status=f.status, evidence=None,
                           rationale=f.rationale, recommendation=f.recommendation)
              for f in response.findings]
    problems = _completeness_problems(expected, drafts)
    problems += [p for f in response.findings if (p := _problem(f, ctx.deps.input_text))]
    statuses = Counter(f.status for f in response.findings)
    print(f"VALIDATION findings={len(response.findings)}/{len(expected)} {dict(statuses)} "
          f"problems={problems}", file=sys.stderr)  # prototype diagnostics, incl. last try
    if problems:
        raise ModelRetry("\n".join(problems))
    return response


_bedrock_agent.output_validator(_validate)
_groq_agent.output_validator(_validate)


def _problem(f: FindingRefDraft, text: str) -> str | None:
    has_range = f.line_start is not None and f.line_end is not None
    if f.status == "PASS" and not has_range:  # FAIL without range: downgraded to WARN
        return f"{f.rule_id}: Zeilenbereich fehlt (Pflicht bei PASS)"
    if has_range and (p := _range_problem(f.line_start, f.line_end, text)):
        return f"{f.rule_id}: {p}"
    if f.status in ("WARN", "FAIL") and not f.recommendation:
        return f"{f.rule_id}: Empfehlung fehlt (Pflicht bei {f.status})"
    return None


def _range_problem(start: int, end: int, text: str) -> str | None:
    last = len(text.splitlines())
    if not 1 <= start <= end <= last:
        return f"Zeilenbereich {start}-{end} ungültig (Eingabe hat Zeilen 1-{last})"
    if end - start >= MAX_SPAN:
        return f"Zeilenbereich {start}-{end} zu groß (höchstens {MAX_SPAN} Zeilen)"
    if len(normalize(cut(text, start, end))) < MIN_QUOTE_LENGTH:
        return f"Zeilen {start}-{end} sind zu kurz als Beleg (mind. {MIN_QUOTE_LENGTH} Zeichen)"
    return None


async def ask_model_by_ref(deps: AuditDeps, model: Model) -> list[FindingDraft]:
    """Drop-in for `audit_engine._ask_model`; the code cuts the evidence from the input."""
    agent = _groq_agent if model.system == "groq" else _bedrock_agent
    prompt = _user_prompt(deps.model_copy(update={"input_text": numbered(deps.input_text)}))
    result = await agent.run(prompt, model=model, deps=deps)
    return [
        FindingDraft(
            rule_id=f.rule_id, status=_status(f), rationale=f.rationale,
            recommendation=f.recommendation,
            evidence=cut(deps.input_text, f.line_start, f.line_end)
            if f.line_start is not None and f.line_end is not None else None,
        )
        for f in result.output.findings
    ]


def _status(f: FindingRefDraft) -> Status:
    """What is missing is WARN, not FAIL: the code enforces the prompt rule (decision #26)."""
    return "WARN" if f.status == "FAIL" and f.line_start is None else f.status
