"""Run `govguard.cli.main()` against a real model; report wall time, tokens and retry reasons.

Usage: uv run python .claude/skills/audit-messen/measure.py spec|arch <file> [--catalog <json>]
       [--stats <json>]
--stats writes the key figures of the run as JSON (#54); evaluate.py reads them.
Report JSON -> stdout, measurements -> stderr, retries and downgrades from the report (#27),
the verdicts of the FAIL judge too (#31).
MEASURE_MODEL=groq measures Groq (ADR 0016).
On fail closed the CLI writes the problems of the last attempt to stderr (AuditValidationError).
"""

import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path

from pydantic_ai.messages import ModelRequest, RetryPromptPart
from pydantic_ai.models.wrapper import WrapperModel

from govguard import cli
from govguard.adapters.aws_services import bedrock_model

JUDGE_OUTPUT = "submit_fail_verdicts"  # output name of the FAIL judge in fail_judge.py


class Measuring(WrapperModel):
    def __init__(self, wrapped) -> None:
        super().__init__(wrapped)
        self.calls: list[tuple[float, int, int, str]] = []  # seconds, input, output, label
        self.retries: list[str] = []
        self.schema_retries = 0  # schema violations, not content problems

    async def request(self, messages, model_settings, model_request_parameters):
        last = messages[-1]
        retry = [p for p in last.parts if isinstance(p, RetryPromptPart)] \
            if isinstance(last, ModelRequest) else []
        self.retries += [p.model_response() for p in retry]
        self.schema_retries += sum(isinstance(p.content, list) for p in retry)  # pydantic errors
        start = time.perf_counter()
        response = await super().request(messages, model_settings, model_request_parameters)
        self.calls.append((time.perf_counter() - start, response.usage.input_tokens,
                           response.usage.output_tokens, _label(model_request_parameters, retry)))
        return response


def _label(params, retry: list) -> str:
    """JUDGE marks the request of the FAIL judge (#31), RETRY a package sent back."""
    names = [t.name for t in params.output_tools]
    names += [params.output_object.name] if params.output_object else []
    return (" JUDGE" if JUDGE_OUTPUT in names else "") + (" RETRY" if retry else "")


def _model_and_prices() -> tuple:
    """MEASURE_MODEL=groq: explicit option with fictitious presets only (ADR 0016)."""
    if os.getenv("MEASURE_MODEL") == "groq":
        from govguard.adapters.groq_services import groq_model
        return groq_model(), 0.15e-6, 0.60e-6  # gpt-oss-120b, Groq model docs
    return bedrock_model(), 1.10e-6, 5.50e-6  # Haiku 4.5 eu. profile: +10 % on 1 $/5 $


def _pop_stats_path(argv: list[str]) -> tuple[list[str], Path | None]:
    """--stats <path> is ours, the rest goes on to cli.main."""
    if "--stats" not in argv:
        return argv, None
    i = argv.index("--stats")
    if i + 1 == len(argv):
        sys.exit("--stats needs a path")
    return argv[:i] + argv[i + 2:], Path(argv[i + 1])


def _write_stats(path: Path, args: list[str], figures: dict) -> None:
    """Write the key figures; preset: folder of the input below presets/, else None."""
    source = args[1] if len(args) > 1 else None
    parent = Path(source).resolve().parent if source else None
    preset = parent.name if parent and parent.parent.name == "presets" else None
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"preset": preset, "input": source, **figures}, indent=2) + "\n")


def _print_corrections(report_json: str) -> None:
    """Retries and downgrades the code made, read from the report (#27)."""
    if not report_json.strip():  # fail closed: no report, the CLI wrote the reasons to stderr
        return
    report = json.loads(report_json)
    downgraded = [f["downgraded_from"] for f in report["findings"] if f["downgraded_from"]]
    print(f"retries (packages + judge): {report['retries']} downgrades: {len(downgraded)} "
          f"(PASS->WARN: {downgraded.count('PASS')}, FAIL->WARN: {downgraded.count('FAIL')}) "
          f"unassigned corrections: {len(report['unassigned_corrections'])}", file=sys.stderr)
    judge = report["fail_judge"]
    print(f"fail judge: checked {judge['checked']} confirmed {judge['confirmed']} "
          f"downgraded {judge['downgraded']} unavailable {judge['unavailable']}", file=sys.stderr)


cli_args, stats_path = _pop_stats_path(sys.argv[1:])
wrapped, price_in, price_out = _model_and_prices()
model = Measuring(wrapped)
start = time.perf_counter()
stdout = io.StringIO()
with contextlib.redirect_stdout(stdout):  # the report is counted here, then printed unchanged
    code = cli.main(cli_args, model=model)
print(stdout.getvalue(), end="")
wall = time.perf_counter() - start
tokens_in = sum(c[1] for c in model.calls)
tokens_out = sum(c[2] for c in model.calls)
cost = tokens_in * price_in + tokens_out * price_out
print(f"model={model.model_name}", file=sys.stderr)
print(f"exit={code} wall={wall:.1f}s calls={len(model.calls)} input_tokens={tokens_in} "
      f"output_tokens={tokens_out} cost_usd={cost:.2f}", file=sys.stderr)
if stats_path:
    _write_stats(stats_path, cli_args, {
        "model": model.model_name, "exit": code, "wall_s": round(wall, 1),
        "calls": len(model.calls), "input_tokens": tokens_in, "output_tokens": tokens_out,
        "slowest_call_s": round(max((c[0] for c in model.calls), default=0), 1),
        "retries": len(model.retries), "schema_retries": model.schema_retries,
        "cost_usd": round(cost, 4)})
for seconds, t_in, t_out, label in sorted(model.calls):
    print(f"  call {seconds:5.1f}s in={t_in} out={t_out}{label}", file=sys.stderr)
print(f"retry prompts sent: {len(model.retries)} (schema: {model.schema_retries}) "
      f"output_tokens_per_call={tokens_out / max(len(model.calls), 1):.0f}", file=sys.stderr)
_print_corrections(stdout.getvalue())
for text in model.retries:
    print(f"--- retry prompt ---\n{text}", file=sys.stderr)
sys.exit(code)
