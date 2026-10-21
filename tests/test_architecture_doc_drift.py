"""docs/ARCHITECTURE.md must not drift from the code (#64): shown paths, names, tests exist."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
ARCHITECTURE = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
MERMAID = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
FILE_OR_DIR = re.compile(r"(?<![\w/.-])(?:[\w-]+/)*\w+\.py|(?<![\w/.-])(?:\w+/)+(?![\w])")
SNAKE_OR_CAMEL = re.compile(r"(?<![\w/])(?:[a-z]+(?:_[a-z]+)+|[A-Z][a-z]+(?:[A-Z][a-z]+)+)\b(?!\.)")
NOT_CODE = {"CloudWatch", "GitHub", "GovGuard"}  # product names in labels, not code names


def diagram_labels() -> list[str]:
    """Quoted label texts of all diagrams, `<br/>` as a space; in sequence diagrams also the
    message texts and the participant names."""
    labels = []
    for block in MERMAID.findall(ARCHITECTURE):
        labels += [text.replace("<br/>", " ") for text in re.findall(r'"([^"]*)"', block)]
        if block.startswith("sequenceDiagram"):
            labels += [line.split(":", 1)[1] for line in block.splitlines() if ":" in line]
            labels += re.findall(r"^\s*(?:participant|actor) \w+ as (.+)$", block, re.MULTILINE)
    return labels


def code_names() -> set[str]:
    """Classes, functions, file stems and folder names under src/."""
    names = {path.stem for path in SRC.rglob("*.py")}
    names |= {path.name for path in SRC.rglob("*") if path.is_dir()}
    for path in SRC.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names |= {node.name for node in ast.walk(tree)
                  if isinstance(node, ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)}
    return names


def path_exists(token: str) -> bool:
    """A path shown in the doc is real: from the repo root, from src/, or as the tail of a real
    path below src/, tests/ or .claude/ (`calls/` matches `src/govguard/calls`)."""
    tail = token.rstrip("/")
    last = tail.rsplit("/", 1)[-1]
    searched = [ROOT / ".claude", ROOT / "tests", SRC]
    return (ROOT / token).exists() or (SRC / token).exists() or any(
        path.as_posix().endswith("/" + tail)
        for base in searched if base.exists() for path in base.rglob(last)
    )


def test_every_path_in_the_diagrams_exists() -> None:
    tokens = [t for label in diagram_labels() for t in FILE_OR_DIR.findall(label)]
    assert len(tokens) >= 8, "too few paths found: the regex no longer matches the diagrams"
    assert sorted({t for t in tokens if not path_exists(t)}) == []


def test_every_code_name_in_the_diagrams_exists() -> None:
    tokens = {t for label in diagram_labels() for t in SNAKE_OR_CAMEL.findall(label)} - NOT_CODE
    assert tokens, "no code names found: the regex no longer matches the diagrams"
    assert sorted(tokens - code_names()) == []


def test_every_path_in_the_text_exists() -> None:
    """Python paths in backticks anywhere in the doc; the next test checks tests more strictly."""
    paths = re.findall(r"`((?:[\w-]+/)*\w+\.py)`", ARCHITECTURE)
    assert len(paths) >= 10, "too few paths found in the text"
    assert sorted({p for p in paths if not path_exists(p)}) == []


def test_every_test_named_in_the_text_exists() -> None:
    files = set(re.findall(r"`(?:tests/)?(test_\w+\.py)`", ARCHITECTURE))
    assert files, "no tests named in ARCHITECTURE.md"
    assert sorted(f for f in files if not (ROOT / "tests" / f).exists()) == []
