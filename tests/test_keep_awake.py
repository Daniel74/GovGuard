"""Keep-awake job of the demo (#79): wake logic on a fake page, no browser."""

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[1]
SCRIPT = ROOT / "tools/keep_awake.py"
WORKFLOW = ROOT / ".github/workflows/keep-awake.yml"
spec = importlib.util.spec_from_file_location("keep_awake", SCRIPT)
keep_awake = importlib.util.module_from_spec(spec)
spec.loader.exec_module(keep_awake)


class FakePage:
    """A sleeping page shows the app only after the button, then after `ready_after` polls."""

    def __init__(self, asleep: bool, ready_after: int = 0) -> None:
        self.asleep, self.ready_after, self.presses = asleep, ready_after, 0

    def shows_app(self) -> bool:
        if self.asleep:
            return False
        self.ready_after -= 1
        return self.ready_after < 0

    def press_wake_button(self) -> bool:
        if not self.asleep:
            return False
        self.asleep, self.presses = False, self.presses + 1
        return True


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.now += seconds


def wake(page: FakePage, clock: FakeClock) -> str:
    return keep_awake.wake(page, clock=clock, sleep=clock.sleep)


def test_an_awake_app_is_left_alone() -> None:
    page = FakePage(asleep=False)
    assert wake(page, FakeClock()) == "App war wach."
    assert page.presses == 0


def test_a_sleeping_app_is_woken_once_and_the_wait_is_reported() -> None:
    page = FakePage(asleep=True, ready_after=3)
    assert wake(page, FakeClock()) == "App schlief, nach 8 s geweckt."
    assert page.presses == 1


def test_an_app_that_never_shows_fails_after_the_timeout() -> None:
    clock = FakeClock()
    with pytest.raises(TimeoutError, match="nach 180 s nicht erschienen"):
        wake(FakePage(asleep=False, ready_after=10_000), clock)
    assert clock.now == keep_awake.TIMEOUT_S


def test_the_result_line_goes_to_the_log_and_the_run_summary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    summary = tmp_path / "summary.md"
    monkeypatch.setenv("GITHUB_STEP_SUMMARY", str(summary))
    keep_awake.report("App war wach.")
    assert capsys.readouterr().out == "App war wach.\n"
    assert summary.read_text() == "App war wach.\n"


def test_without_github_the_result_line_only_goes_to_the_log(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("GITHUB_STEP_SUMMARY", raising=False)
    keep_awake.report("App war wach.")
    assert capsys.readouterr().out == "App war wach.\n"


def test_the_workflow_runs_every_six_hours_and_only_calls_python_modules() -> None:
    lines = [line.strip() for line in WORKFLOW.read_text().splitlines()]
    commands = [line.removeprefix("run:").strip() for line in lines if line.startswith("run:")]
    assert commands and all(c.startswith("uv run python -m ") for c in commands)  # CLAUDE.md
    assert "uv run python -m tools.keep_awake https://govguard.streamlit.app/" in commands
    assert '- cron: "17 */6 * * *"' in lines  # off the full hour, when GitHub queues most runs
    assert "workflow_dispatch:" in lines
