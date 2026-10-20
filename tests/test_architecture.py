"""Guardrails from CLAUDE.md and ARCHITECTURE -> Code-Struktur."""

import ast
from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src"
MAX_MODULE_LINES = 200
ADAPTER_ONLY: dict[str, str | None] = {  # I/O import -> the only module allowed (None: none)
    "boto3": "govguard/adapters/aws_services.py",
    "botocore": "govguard/adapters/aws_services.py",
    "pydantic_ai.models.bedrock": "govguard/adapters/aws_services.py",
    "pydantic_ai.providers.bedrock": "govguard/adapters/aws_services.py",
    "groq": "govguard/adapters/groq_services.py",  # runtime and build default (ADR 0014, 0023)
    "pydantic_ai.models.groq": "govguard/adapters/groq_services.py",
    "pydantic_ai.providers.groq": "govguard/adapters/groq_services.py",
    "subprocess": None,  # no cdk_runner.py, no archetypes are built (ADR 0019)
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
def test_io_imports_only_in_their_adapter(module: str, adapter: str | None) -> None:
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


DATA_PATH_OWNERS = {"kb_build/paths.py", "govguard/audit_setup.py",  # the two catalogs
                    "govguard_ui/paths.py"}


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


def module_file(name: str) -> Path | None:
    path = SRC / (name.replace(".", "/") + ".py")
    return path if path.exists() else None


def reachable_modules(start: Path) -> set[str]:
    """Own modules `start` loads, directly or through other own modules."""
    seen: set[str] = set()
    todo = [start]
    while todo:
        for name in imported_modules(todo.pop()):
            if name not in seen and (path := module_file(name)):
                seen.add(name)
                todo.append(path)
    return seen


def modules_in(folder: str) -> list[Path]:
    return sorted((SRC / folder).rglob("*.py"))


def rel_id(path: Path) -> str:
    return path.relative_to(SRC).as_posix()


@pytest.mark.parametrize("path", modules_in("govguard_ui"), ids=rel_id)
def test_demo_ui_loads_no_aws_and_no_entry_point(path: Path) -> None:
    """Demo without AWS (ADR 0023): the UI never imports the CLI or the Bedrock adapter."""
    forbidden = {"govguard.cli", "govguard.adapters.aws_services"}
    assert reachable_modules(path) & forbidden == set()


@pytest.mark.parametrize("path", modules_in("govguard/checks"), ids=rel_id)
def test_checks_import_neither_calls_nor_adapters(path: Path) -> None:
    """ADR 0027: a pure check never reaches a model call or an adapter, not even indirectly."""
    loaded = reachable_modules(path)
    assert [m for m in loaded if m.startswith(("govguard.calls", "govguard.adapters"))] == []


@pytest.mark.parametrize("path", modules_in("govguard_ui/report"), ids=rel_id)
def test_the_report_view_imports_no_screen(path: Path) -> None:
    """ADR 0027: screens use the report view, never the other way round."""
    loaded = reachable_modules(path)
    assert [m for m in loaded if m.startswith("govguard_ui.screens")] == []


ROOTS = {  # ADR 0027: only entry points and contracts that others import
    "govguard": {"audit_engine", "models", "open_world", "text", "audit_setup", "cli"},
    "govguard_ui": {"app", "navigation", "gallery", "paths", "style", "texts"},
}


@pytest.mark.parametrize("package", ROOTS)
def test_the_root_holds_only_entry_points_and_contracts(package: str) -> None:
    found = {p.stem for p in (SRC / package).glob("*.py")} - {"__init__"}
    assert found == ROOTS[package]
