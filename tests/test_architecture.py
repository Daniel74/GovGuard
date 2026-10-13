"""Guardrails from CLAUDE.md and ARCHITECTURE -> Code-Struktur."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src"
MAX_MODULE_LINES = 200
ADAPTER_ONLY = {  # I/O import -> the only module allowed to import it
    "boto3": "govguard/aws_services.py",
    "botocore": "govguard/aws_services.py",
    "pydantic_ai.models.bedrock": "govguard/aws_services.py",
    "pydantic_ai.providers.bedrock": "govguard/aws_services.py",
    "groq": "kb_build/groq_services.py",  # build-only fallback (ADR 0010)
    "pydantic_ai.models.groq": "kb_build/groq_services.py",
    "pydantic_ai.providers.groq": "kb_build/groq_services.py",
    "subprocess": "kb_build/cdk_runner.py",
    "urllib.request": "kb_build/source_fetch.py",
    "http.client": "kb_build/source_fetch.py",
    "requests": "kb_build/source_fetch.py",
    "httpx": "kb_build/source_fetch.py",
}


def imported_modules(path: Path) -> set[str]:
    """Full dotted names; `from a import b` yields both a and a.b."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names |= {alias.name for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            names |= {node.module} | {f"{node.module}.{alias.name}" for alias in node.names}
    return names


def imports(path: Path, module: str) -> bool:
    return any(name == module or name.startswith(f"{module}.") for name in imported_modules(path))


@pytest.mark.parametrize(("module", "adapter"), ADAPTER_ONLY.items())
def test_io_imports_only_in_their_adapter(module: str, adapter: str) -> None:
    offenders = [
        rel
        for path in SRC.rglob("*.py")
        if (rel := path.relative_to(SRC).as_posix()) != adapter and imports(path, module)
    ]
    assert offenders == []


def test_modules_stay_small() -> None:
    too_long = {
        str(path.relative_to(SRC)): n
        for path in SRC.rglob("*.py")
        if (n := len(path.read_text(encoding="utf-8").splitlines())) > MAX_MODULE_LINES
    }
    assert too_long == {}


DATA_PATH_OWNERS = {"kb_build/paths.py", "govguard/cli.py"}  # cli.py: one default catalog


def data_path_literals(path: Path) -> list[str]:
    """String constants like "data" or "data/…"; docstrings do not count."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {id(node.value) for node in ast.walk(tree) if isinstance(node, ast.Expr)}
    return [
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and id(node) not in docstrings and (node.value == "data" or node.value.startswith("data/"))
    ]


def test_data_paths_only_in_the_paths_module() -> None:
    offenders = {
        rel: literals
        for path in SRC.rglob("*.py")
        if (rel := path.relative_to(SRC).as_posix()) not in DATA_PATH_OWNERS
        and (literals := data_path_literals(path))
    }
    assert offenders == {}
