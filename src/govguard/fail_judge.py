"""FAIL judge: a second LLM opinion on every FAIL in an open world (ADR 0020, #31, #46).

Whether evidence lines lay down a violation is a question of meaning, no code gate decides it.
One request for all FAILs, with only criterion and evidence lines. Pure logic: model injected.
"""

import json

from pydantic import BaseModel
from pydantic_ai import Agent, ModelRetry, NativeOutput, RunContext, ToolOutput
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.corrections import Corrections, service_down
from govguard.evidence import evidence_of
from govguard.models import FindingDraft, Provider, Rule, provider_of
from govguard.open_world import AuditInput, OpenWorld

_DOWN = "KI-Dienst nicht erreichbar oder überlastet"  # never the library's error text
_INVALID = "Antwort auch nach einer Korrektur nicht verwertbar"

FAIL_JUDGE_PROMPT = """\
Du prüfst FAIL-Befunde aus dem Audit {audit_of}. {subject_sentence} ist
eine offene Welt: Was sie nicht erwähnt, kann anderswo geregelt sein. Ein FAIL ist nur
richtig, wenn die Belegzeilen selbst etwas festlegen, das das Verstoßkriterium
("violation_if") erfüllt: eine Festlegung, die der Prüfregel widerspricht, oder einen
erklärten Verzicht oder Aufschub.
Bestätige ein FAIL nicht, wenn die Belegzeilen das Kriterium nicht zeigen, also zum
Thema schweigen, es nur vage oder unvollständig beschreiben.
- Bestätigt: {confirmed}
- Nicht bestätigt: {rejected}
Gib je Befund genau ein Urteil ab: "confirmed" true oder false, "reason" ein Satz auf
Deutsch, woran du es erkennst."""


class FailVerdict(BaseModel):  # one item of submit_fail_verdicts; no defaults (strict)
    rule_id: str
    confirmed: bool
    reason: str


class FailVerdicts(BaseModel):  # schema of tool submit_fail_verdicts
    verdicts: list[FailVerdict]


class JudgeDeps(BaseModel):  # deps_type of the judge
    world: OpenWorld  # subject and example pair of the prompt (#46)
    fail_ids: list[str]  # rule_ids of the FAILs, each needs a verdict
    corrections: Corrections  # the judge's retry counts like a package retry (#27)
    reason_sent: bool = False  # the code asked for missing verdicts


_OUTPUT = {"name": "submit_fail_verdicts", "strict": True,
           "description": "Gib je FAIL-Befund genau ein Urteil ab."}
_SETTINGS = {"temperature": 0, "max_tokens": 8000}  # like the audit (#28)
# Bedrock: forced tool (ADR 0005); Groq: json_schema with constrained decoding (ADR 0016)
_JUDGES: dict[Provider, Agent] = {
    provider: Agent(output_type=output_type, deps_type=JudgeDeps, model_settings=_SETTINGS,
                    retries=1)  # one retry, for a schema slip or missing verdicts
    for provider, output_type in [("bedrock", ToolOutput(FailVerdicts, **_OUTPUT)),
                                  ("groq", NativeOutput(FailVerdicts, **_OUTPUT))]
}


def _all_judged(ctx: RunContext[JudgeDeps], output: FailVerdicts) -> FailVerdicts:
    """One retry for missing verdicts (5 of 27 measured, #31); after it the FAIL stays."""
    if ctx.retry:
        ctx.deps.corrections.record_retry(ctx.deps.reason_sent)
    judged = {verdict.rule_id for verdict in output.verdicts}
    if (no_verdict := [rule_id for rule_id in ctx.deps.fail_ids if rule_id not in judged]) \
            and not ctx.last_attempt:
        ctx.deps.reason_sent = True
        raise ModelRetry(f"Urteil fehlt für: {', '.join(no_verdict)}")
    return output


def _prompt(ctx: RunContext[JudgeDeps]) -> str:
    world = ctx.deps.world
    return FAIL_JUDGE_PROMPT.format(
        audit_of=world.audit_of, subject_sentence=world.subject_sentence,
        confirmed=world.confirmed, rejected=world.rejected)


for _judge in _JUDGES.values():
    _judge.output_validator(_all_judged)
    _judge.instructions(_prompt)


async def judge_fails(
    rules: list[Rule], drafts: list[FindingDraft], given: AuditInput, model: Model,
    corrections: Corrections,
) -> list[FindingDraft]:
    """Confirmed FAILs stay, rejected ones become WARN; every verdict lands in corrections.

    Without a verdict the FAIL stays unchecked: the stricter status, no fail closed (#31).
    A closed world (template) never gets here: a missing setting is the default (ADR 0020).
    """
    fails = {d.rule_id: d for d in drafts if d.status == "FAIL"}
    if not fails or given.world is None:
        return drafts
    deps = JudgeDeps(world=given.world, fail_ids=list(fails), corrections=corrections)
    verdicts, no_verdict_reason = await _verdicts(rules, list(fails.values()), given.text,
                                                  model, deps)
    for rule_id in fails:
        if verdict := verdicts.get(rule_id):
            corrections.record_verdict(rule_id, verdict.confirmed, verdict.reason)
        else:
            corrections.record_unchecked(rule_id, no_verdict_reason)
    rejected = {rule_id for rule_id in fails if rule_id in verdicts
                and not verdicts[rule_id].confirmed}
    return [d.model_copy(update={"status": "WARN"}) if d.status == "FAIL" and d.rule_id in rejected
            else d for d in drafts]


async def _verdicts(
    rules: list[Rule], fails: list[FindingDraft], input_text: str, model: Model, deps: JudgeDeps
) -> tuple[dict[str, FailVerdict], str]:
    """rule_id -> first verdict, and the reason for a FAIL without one."""
    try:
        result = await _JUDGES[provider_of(model)].run(
            _user_prompt(rules, fails, input_text), model=model, deps=deps)
    except UnexpectedModelBehavior:  # invalid after the retry; the validator never saw it
        deps.corrections.record_retry(deps.reason_sent)
        return {}, _INVALID
    except ModelAPIError as error:  # Groq rejects a broken answer with HTTP 400, no retry
        return {}, _DOWN if service_down(error) else _INVALID
    verdicts: dict[str, FailVerdict] = {}
    for verdict in result.output.verdicts:
        verdicts.setdefault(verdict.rule_id, verdict)
    return verdicts, "kein Urteil zu diesem Befund"


def _user_prompt(rules: list[Rule], fails: list[FindingDraft], input_text: str) -> str:
    """Without the audit's rationale: the judge echoed it and confirmed 12 of 13 (#31)."""
    by_id = {rule.id: rule for rule in rules}
    items = [{"rule_id": f.rule_id, "title": by_id[f.rule_id].title,
              "violation_if": by_id[f.rule_id].violation_if,
              "evidence": _numbered_evidence(f, input_text)}
             for f in fails]
    return ('FAIL-Befunde (Belegzeilen in "evidence"):\n'
            f"{json.dumps(items, ensure_ascii=False, indent=1)}")


def _numbered_evidence(fail: FindingDraft, input_text: str) -> str:
    """The evidence lines with their numbers from the input, e.g. "12| "."""
    lines = (evidence_of(fail, input_text) or "").splitlines()
    return "\n".join(f"{i}| {line}" for i, line in enumerate(lines, fail.line_start or 1))
