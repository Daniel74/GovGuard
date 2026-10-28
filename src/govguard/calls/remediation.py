"""Measure proposal for one site: a concrete change per group of WARN/FAIL (#82).

One LLM call on request, never inside an audit. The model sees the whole document with the site
marked and the open findings of the site; the code cuts the lines the model names and checks the
answer (checks/remediation.py), sending it back once. After that: no proposal, no crash. Same
provider as the audit (ADR 0016, 0023).
"""

import json

from pydantic_ai import RunContext
from pydantic_ai.exceptions import ModelAPIError, UnexpectedModelBehavior
from pydantic_ai.models import Model

from govguard.calls.model_call import Answer, CallDeps, agents_for, ask, count_retry, send_back
from govguard.checks.corrections import Corrections
from govguard.checks.remediation import (
    MAX_MEASURES,
    MeasureProblem,
    open_findings,
    resolve_measures,
)
from govguard.checks.remediation_models import Measure, MeasuresResponse
from govguard.checks.sites import Site

REMEDIATION_PROMPT = f"""\
Du schlägst konkrete Änderungen für eine Fundstelle eines geprüften Dokuments vor.
Du bekommst die Befunde (WARN, FAIL) der Fundstelle und das ganze Dokument. Jede Zeile
beginnt mit ihrer Nummer, z. B. "12| "; Zeilen der Fundstelle sind mit ">" markiert.
Fasse die Befunde zu höchstens {MAX_MEASURES} Maßnahmen zusammen. Jede Maßnahme hat:
- "sentence": ein Satz, was zu ändern ist.
- "from_line", "to_line": die erste und letzte Nummer der Zeilen der Fundstelle, die sich
  ändern; so wenige wie möglich.
- "after": die neuen Zeilen, die diese ersetzen, mit derselben Einrückung, ohne
  Zeilennummern.
- "rule_ids": die Regel-IDs der Befunde, die diese Maßnahme behebt.
Jeder Befund gehört zu genau einer Maßnahme. Die Zeilenbereiche von zwei Maßnahmen dürfen sich
nicht überschneiden. Fehlt dir ein Wert, den nur der Betreiber kennt, schreibe im "after" einen
Platzhalter in eckigen Klammern, z. B. [Bucket-ARN]. Erfinde nichts.
Schreibe Satz und Platzhalter auf Deutsch."""

_SETTINGS = {"temperature": 0, "max_tokens": 8000}  # like the audit (#28)


class RemediationDeps(CallDeps):  # input of the validator, and where it keeps its result
    site: Site
    document: str
    measures: list[Measure] = []  # the checked answer: set by the validator, read by the caller


def _validate(ctx: RunContext[RemediationDeps], response: MeasuresResponse) -> MeasuresResponse:
    """One retry with every reason the code found; after it the caller gives up."""
    count_retry(ctx)
    try:
        ctx.deps.measures = resolve_measures(response.measures, ctx.deps.site, ctx.deps.document)
    except MeasureProblem as problem:
        send_back(ctx, str(problem))
    return response


_AGENTS = agents_for(
    Answer(MeasuresResponse, "submit_measures",
           f"Gib höchstens {MAX_MEASURES} Maßnahmen für die Fundstelle ab.", strict=True),
    deps_type=RemediationDeps, instructions=REMEDIATION_PROMPT, validator=_validate,
    settings=_SETTINGS)


async def suggest_measures(site: Site, document: str, model: Model) -> list[Measure] | None:
    """The checked measures of the site, or None: no proposal possible (never raises for a model
    failure: the reader keeps the findings as they are)."""
    deps = RemediationDeps(site=site, document=document, corrections=Corrections())
    try:
        await ask(_AGENTS, model, _user_prompt(site, document), deps)
    except (UnexpectedModelBehavior, ModelAPIError):  # invalid after the retry / service down
        return None
    return deps.measures  # the validator checked the answer it let through


def _user_prompt(site: Site, document: str) -> str:
    items = [{"rule_id": f.rule_id, "status": f.status, "rationale": f.rationale,
              "recommendation": f.recommendation} for f in open_findings(site)]
    return (f"Fundstelle {site.name}: Zeilen {site.line_start}–{site.line_end}.\n\n"
            f"Befunde der Fundstelle:\n{json.dumps(items, ensure_ascii=False, indent=1)}\n\n"
            f"Dokument:\n<dokument>\n{_marked(site, document)}\n</dokument>")


def _marked(site: Site, document: str) -> str:
    """The document with numbers; the lines of the site start with ">", the others with a blank."""
    lines = document.splitlines()
    width = len(str(len(lines)))
    return "\n".join(
        f"{'>' if site.line_start <= n <= site.line_end else ' '} {n:>{width}}| {line}"
        for n, line in enumerate(lines, 1))
