"""Run `govguard.cli.main()` against real Bedrock; report wall time, tokens and retry reasons.

Usage: uv run python .claude/skills/audit-messen/measure.py spec <file> [--catalog <json>]
Report JSON -> stdout, measurements -> stderr.
"""

import json
import os
import sys
import time

from pydantic_ai.messages import ModelRequest, RetryPromptPart, ToolCallPart
from pydantic_ai.models.wrapper import WrapperModel

from govguard import cli
from govguard.aws_services import bedrock_model
from govguard.text import contains_quote

INPUT = open(sys.argv[2], encoding="utf-8").read()


class Measuring(WrapperModel):
    def __init__(self, wrapped) -> None:
        super().__init__(wrapped)
        self.calls: list[tuple[float, int, int, bool]] = []  # seconds, input, output, is_retry
        self.retries: list[str] = []
        self.rejected: list[str] = []  # evidence that contains_quote() will reject

    async def request(self, messages, model_settings, model_request_parameters):
        last = messages[-1]
        retry = [p for p in last.parts if isinstance(p, RetryPromptPart)] \
            if isinstance(last, ModelRequest) else []
        self.retries += [p.model_response() for p in retry]
        start = time.perf_counter()
        response = await super().request(messages, model_settings, model_request_parameters)
        self.calls.append((time.perf_counter() - start, response.usage.input_tokens,
                           response.usage.output_tokens, bool(retry)))
        self.rejected += [f"{f.get('rule_id')}: {f['evidence']!r}" for f in _findings(response)
                          if isinstance(f, dict) and isinstance(f.get("evidence"), str)
                          and not contains_quote(INPUT, f["evidence"])]
        return response


def _findings(response) -> list[dict]:
    """Tool args of submit_audit; the model sometimes sends findings as a (broken) JSON string."""
    found = []
    for part in response.parts:
        if isinstance(part, ToolCallPart):
            items = part.args_as_dict().get("findings", [])
            try:
                items = json.loads(items) if isinstance(items, str) else items
                found += [json.loads(i) if isinstance(i, str) else i for i in items]
            except ValueError:
                print("UNPARSEABLE findings: sent as a string with invalid JSON", file=sys.stderr)
    return found


def _model_and_prices() -> tuple:
    """MEASURE_MODEL=groq: comparison only, Groq is not allowed at runtime (ADR 0001)."""
    if os.getenv("MEASURE_MODEL") == "groq":
        from kb_build.groq_services import groq_model
        return groq_model(), 0.15e-6, 0.60e-6  # gpt-oss-120b, Groq model docs
    return bedrock_model(), 1.10e-6, 5.50e-6  # Haiku 4.5 eu. profile: +10 % on 1 $/5 $


wrapped, price_in, price_out = _model_and_prices()
model = Measuring(wrapped)
start = time.perf_counter()
code = cli.main(sys.argv[1:], model=model)
wall = time.perf_counter() - start
tokens_in = sum(c[1] for c in model.calls)
tokens_out = sum(c[2] for c in model.calls)
cost = tokens_in * price_in + tokens_out * price_out
print(f"model={model.model_name}", file=sys.stderr)
print(f"exit={code} wall={wall:.1f}s calls={len(model.calls)} input_tokens={tokens_in} "
      f"output_tokens={tokens_out} cost_usd={cost:.2f}", file=sys.stderr)
for seconds, t_in, t_out, is_retry in sorted(model.calls):
    print(f"  call {seconds:5.1f}s in={t_in} out={t_out}{' RETRY' if is_retry else ''}",
          file=sys.stderr)
print(f"retry prompts sent: {len(model.retries)}", file=sys.stderr)
for text in model.retries:
    print(f"--- retry prompt ---\n{text}", file=sys.stderr)
for line in model.rejected:
    print(f"REJECTED EVIDENCE {line}", file=sys.stderr)
sys.exit(code)
