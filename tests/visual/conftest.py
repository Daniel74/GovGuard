"""Streamlit server and options of the screenshot regression (#40).

The server runs as a child process of the test; the subprocess ban (ADR 0019) covers src/ only.
"""

import os
import socket
import subprocess
import sys
import time
import urllib.request
from collections.abc import Iterator
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
WIDTH, HEIGHT = 1440, 900  # width of the design artboards (#11)
START_TIMEOUT = 30


@pytest.fixture
def update_snapshots(request: pytest.FixtureRequest) -> bool:
    return request.config.getoption("--update-snapshots")


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_until_healthy(url: str) -> None:
    deadline = time.monotonic() + START_TIMEOUT
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(f"{url}/_stcore/health", timeout=1):
                return
        except OSError:
            time.sleep(0.3)
    raise TimeoutError(f"Streamlit did not answer within {START_TIMEOUT} s: {url}")


@pytest.fixture(scope="session")
def app_url() -> Iterator[str]:
    """streamlit_app.py on a free local port, demo backend without secrets (ADR 0023)."""
    port = free_port()
    env = {**os.environ, "AUDIT_BACKEND": "local"}
    server = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "streamlit_app.py",
         "--server.headless=true", f"--server.port={port}",
         "--browser.gatherUsageStats=false"],
        cwd=ROOT, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = f"http://127.0.0.1:{port}"
    try:
        wait_until_healthy(url)
        yield url
    finally:
        server.terminate()
        server.wait(timeout=10)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict) -> dict:
    """Overrides the pytest-playwright fixture: artboard width, German UI, no motion."""
    return {**browser_context_args, "viewport": {"width": WIDTH, "height": HEIGHT},
            "locale": "de-DE", "reduced_motion": "reduce"}
