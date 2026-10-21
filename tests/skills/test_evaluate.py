"""Evaluation script of the measurement campaign (#54): key figures on small fixtures."""

import importlib.util
import json
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parents[2] / ".claude/skills/audit-messen/evaluate.py"
spec = importlib.util.spec_from_file_location("evaluate", SCRIPT)
evaluate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluate)

EXPECTED = {"overall_status": "FAIL",
            "required_findings": [{"anchor": "Anchor A", "status": "FAIL"}],
            "conditions": {"processor": "yes"}}


def finding(rule: str, status: str, lines: bool = True, anchor: str | None = None) -> dict:
    return {"rule_id": rule, "status": status, "line_start": 1 if lines else None,
            "line_end": 1 if lines else None, "rationale": "r", "recommendation": None,
            "evidence": None, "title": rule, "primary_anchor": anchor or rule,
            "cross_references": []}


def report(*findings: dict, overall: str = "FAIL", processor: str = "yes") -> dict:
    return {"audit_type": "spec", "overall_status": overall, "findings": list(findings),
            "model_id": "m", "trace": {"audit_id": "a", "input_sha256": "x",
                                       "catalog_sha256": "y", "kb_commit": "z"},
            "conditions": {"processor": {"value": processor}}}


def stats(**values) -> dict:
    return {"input_tokens": 100, "output_tokens": 10, "calls": 4, "wall_s": 20.0,
            "slowest_call_s": 5.0, "retries": 0, "cost_usd": 0.1, **values}


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    runs = [
        report(finding("R1", "FAIL", anchor="Anchor A"), finding("R2", "PASS"),
               finding("R3", "WARN"), finding("R4", "N/A")),
        report(finding("R1", "FAIL", anchor="Anchor A"), finding("R2", "PASS"),
               finding("R3", "WARN", lines=False), finding("R4", "N/A")),
        report(finding("R1", "WARN", anchor="Anchor A"), finding("R2", "PASS"),
               finding("R3", "WARN", lines=False), finding("R4", "PASS"),
               overall="WARN", processor="no"),
    ]
    for n, run in enumerate(runs, start=1):
        (tmp_path / f"demo-{n}.json").write_text(json.dumps(run))
        (tmp_path / f"demo-{n}.stats.json").write_text(
            json.dumps(stats(input_tokens=100 * n, wall_s=10.0 * n, retries=n - 1)))
    return tmp_path


@pytest.fixture
def presets(tmp_path: Path) -> Path:
    (tmp_path / "presets" / "demo").mkdir(parents=True)
    (tmp_path / "presets" / "demo" / "preset.json").write_text(json.dumps({"expected": EXPECTED}))
    return tmp_path / "presets"


def test_target_met_in_two_of_three_runs(folder: Path, presets: Path) -> None:
    runs = evaluate.load_runs(folder)["demo"]
    reports = [run["report"] for run in runs.values()]

    hits, conditions = evaluate.target_hits(reports, evaluate.load_expected("demo", presets))

    assert (hits, conditions) == (2, 2)


def test_stability_counts_rules_with_same_status_and_switches_by_category(folder: Path) -> None:
    reports = [run["report"] for run in evaluate.load_runs(folder)["demo"].values()]

    stable, total, switches = evaluate.stability(reports)

    assert (stable, total) == (2, 4)  # R1 and R4 switch the status; R3 only gap <-> WARN
    assert switches[("WARN", "GAP")] == 1  # R3
    assert switches[("FAIL", "WARN")] == 1  # R1
    assert switches[("PASS", "N/A")] == 1  # R4


def test_spread_is_median_min_max() -> None:
    assert evaluate.spread([3, 1, 2]) == (2, 1, 3)


def test_section_is_markdown_with_all_key_figures(folder: Path, presets: Path) -> None:
    runs = evaluate.load_runs(folder)["demo"]

    section = "\n".join(evaluate.preset_section("demo", runs, presets))

    assert "Soll erfüllt in 2 von 3 Läufen" in section
    assert "2 von 4 Prüfregeln (50%)" in section
    assert "| WARN mit Beleg ↔ Lücke | 1 |" in section
    assert "| Input-Tokens | 200 | 100 | 300 |" in section
    assert "| Retry-Prompts | 1 | 0 | 2 |" in section


def test_run_without_report_misses_the_target(folder: Path, presets: Path) -> None:
    (folder / "demo-3.json").unlink()
    runs = evaluate.load_runs(folder)["demo"]

    section = "\n".join(evaluate.preset_section("demo", runs, presets))

    assert "3 Läufe, 2 mit Report" in section
    assert "Soll erfüllt in 2 von 3 Läufen" in section


def test_empty_report_of_a_fail_closed_run_counts_as_no_report(folder: Path) -> None:
    (folder / "demo-3.json").write_text("")  # measure.py on exit 2: stdout stays empty

    runs = evaluate.load_runs(folder)["demo"]

    assert runs[3]["report"] is None and runs[3]["stats"] is not None


def test_key_figures_only_from_complete_runs_aborts_listed_apart(folder: Path,
                                                                 presets: Path) -> None:
    (folder / "demo-3.json").write_text("")  # fail closed: exit 2, one call, a few seconds
    (folder / "demo-3.stats.json").write_text(json.dumps(stats(exit=2, input_tokens=5, calls=1)))
    runs = evaluate.load_runs(folder)["demo"]

    section = "\n".join(evaluate.preset_section("demo", runs, presets))

    assert "| Input-Tokens | 150 | 100 | 200 |" in section  # runs 1 and 2 only
    assert "Abgebrochen (fail closed): Lauf 3" in section


def test_rule_missing_in_one_run_counts_as_unstable(folder: Path) -> None:
    reports = [run["report"] for run in evaluate.load_runs(folder)["demo"].values()]
    reports[0].findings.append(reports[0].findings[0].model_copy(update={"rule_id": "R5"}))

    stable, total, _ = evaluate.stability(reports)

    assert (stable, total) == (2, 5)
