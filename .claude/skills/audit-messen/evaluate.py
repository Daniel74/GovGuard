"""Evaluate a measurement campaign: stability of the audit over repeated runs (#54, #64).

Usage: uv run python .claude/skills/audit-messen/evaluate.py [data/measurements]
Reads <preset>-<n>.json (report) and <preset>-<n>.stats.json (measure.py --stats) per run.
Writes a Markdown table per preset to stdout, for the issue comment.
"""

import json
import re
import statistics
import sys
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

from govguard.models import AuditReport, Expected
from govguard_ui.paths import PRESETS
from govguard_ui.report.review import CATEGORIES, category, expected_checks

RUN_FILE = re.compile(r"^(?P<preset>.+)-(?P<n>\d+)(?P<stats>\.stats)?\.json$")
CATEGORY_NAMES = {"FAIL": "FAIL", "WARN": "WARN mit Beleg", "GAP": "Lücke", "PASS": "PASS",
                  "N/A": "N/A"}
METRICS = [("input_tokens", "Input-Tokens"), ("output_tokens", "Output-Tokens"),
           ("calls", "Aufrufe"), ("wall_s", "Gesamtzeit (s)"),
           ("slowest_call_s", "Langsamster Aufruf (s)"), ("retries", "Retry-Prompts"),
           ("cost_usd", "Kosten (USD)")]


def load_runs(folder: Path) -> dict[str, dict[int, dict]]:
    """preset -> run number -> {"report": AuditReport | None, "stats": dict | None}."""
    runs: dict[str, dict[int, dict]] = defaultdict(dict)
    for path in sorted(folder.glob("*.json")):
        match = RUN_FILE.match(path.name)
        if not match:
            continue
        run = runs[match["preset"]].setdefault(int(match["n"]), {"report": None, "stats": None})
        if match["stats"]:
            run["stats"] = json.loads(path.read_text())
        elif text := path.read_text().strip():  # empty on fail closed (exit 2)
            run["report"] = AuditReport.model_validate_json(text)
    return runs


def load_expected(preset: str, presets_dir: Path = PRESETS) -> Expected:
    data = json.loads((presets_dir / preset / "preset.json").read_text())
    return Expected.model_validate(data["expected"])


def target_hits(reports: list[AuditReport | None], expected: Expected) -> tuple[int, int]:
    """(runs meeting the expected result, runs with conditions as expected); no report = miss."""
    hits = conditions = 0
    for report in reports:
        if report is None:
            continue
        hits += all(check.ok for check in expected_checks(report, expected))
        found = {key: result.value for key, result in report.conditions.items()}
        conditions += all(found.get(key) == value for key, value in expected.conditions.items())
    return hits, conditions


def stability(reports: list[AuditReport]) -> tuple[int, int, Counter]:
    """(rules with the same status in all runs, rules compared, switches by category pair).

    A rule missing in one run is unstable. A switch counts once per pair of categories the
    rule showed over the runs. Category, not status: a gap (WARN without lines) and a WARN
    with evidence are a switch, yet the same status.
    """
    by_run = [{f.rule_id: f for f in report.findings} for report in reports]
    rules = set().union(*by_run)
    stable = 0
    switches: Counter = Counter()
    for rule_id in sorted(rules):
        found = [run[rule_id] for run in by_run if rule_id in run]
        stable += len(found) == len(by_run) and len({f.status for f in found}) == 1
        names = sorted({category(f) for f in found}, key=CATEGORIES.index)
        switches.update(combinations(names, 2))
    return stable, len(rules), switches


def spread(values: list[float]) -> tuple[float, float, float]:
    return statistics.median(values), min(values), max(values)


def metric_rows(stats: list[dict]) -> list[str]:
    rows = []
    for key, label in METRICS:
        values = [s[key] for s in stats if s.get(key) is not None]
        if values:
            median, low, high = spread(values)
            rows.append(f"| {label} | {median:g} | {low:g} | {high:g} |")
    return rows


def preset_section(preset: str, runs: dict[int, dict], presets_dir: Path = PRESETS) -> list[str]:
    reports = [run["report"] for run in runs.values()]
    present = [r for r in reports if r is not None]
    lines = [f"### {preset}", "", f"{len(runs)} Läufe, {len(present)} mit Report."]
    if (presets_dir / preset / "preset.json").exists():
        expected = load_expected(preset, presets_dir)
        hits, conditions = target_hits(reports, expected)
        lines.append(f"- Soll erfüllt in {hits} von {len(runs)} Läufen.")
        if expected.conditions:
            lines.append(f"- Bedingungen wie erwartet in {conditions} von {len(runs)} Läufen.")
    if present:
        stable, total, switches = stability(present)
        lines.append(f"- Gleicher Status in allen Läufen: {stable} von {total} Prüfregeln"
                     f" ({stable / max(total, 1):.0%}).")
        lines += switch_table(switches)
    return lines + stats_lines(runs)


def stats_lines(runs: dict[int, dict]) -> list[str]:
    """Key figures of complete runs only: an abort after seconds would pull min and median."""
    complete = {n: run["stats"] for n, run in runs.items()
                if run["stats"] and run["stats"].get("exit", 0) == 0}
    aborted = [n for n, run in runs.items() if run["stats"] and n not in complete]
    lines = ["", f"Abgebrochen (fail closed): Lauf {', '.join(map(str, aborted))},"
             " ohne Kennzahlen unten."] if aborted else []
    if complete:
        lines += ["", "| Kennzahl | Median | Min | Max |", "|---|---|---|---|",
                  *metric_rows(list(complete.values()))]
    return lines


def switch_table(switches: Counter) -> list[str]:
    if not switches:
        return []
    rows = [f"| {CATEGORY_NAMES[a]} ↔ {CATEGORY_NAMES[b]} | {count} |"
            for (a, b), count in switches.most_common()]
    return ["", "| Wechsel | Prüfregeln |", "|---|---|", *rows, "",
            "Eine Prüfregel zählt je Paar; Lücke ↔ WARN mit Beleg bleibt derselbe Status."]


def main(argv: list[str]) -> int:
    folder = Path(argv[0]) if argv else Path("data/measurements")
    runs = load_runs(folder)
    if not runs:
        print(f"keine Messungen in {folder}", file=sys.stderr)
        return 1
    for preset in sorted(runs):
        print("\n".join(preset_section(preset, runs[preset])), end="\n\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
