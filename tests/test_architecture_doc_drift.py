"""ARCHITECTURE.md and FUNKTIONSWEISE.md must not drift from the code: shown paths, classes,
names and tests exist."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
ARCHITECTURE = (ROOT / "docs" / "ARCHITECTURE.md").read_text(encoding="utf-8")
FUNKTIONSWEISE = (ROOT / "docs" / "FUNKTIONSWEISE.md").read_text(encoding="utf-8")
DOCS = ARCHITECTURE + "\n" + FUNKTIONSWEISE  # every check below covers both
MERMAID = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
FILE_OR_DIR = re.compile(r"(?<![\w/.-])(?:[\w-]+/)*\w+\.py|(?<![\w/.-])(?:\w+/)+(?![\w])")
SNAKE_OR_CAMEL = re.compile(r"(?<![\w/])(?:[a-z]+(?:_[a-z]+)+|[A-Z][a-z]+(?:[A-Z][a-z]+)+)\b(?!\.)")
NOT_CODE = {"CloudFormation", "CloudWatch", "GitHub", "GovGuard"}  # product names, not code names


def diagram_labels() -> list[str]:
    """Quoted label texts of all diagrams, `<br/>` as a space; in sequence diagrams also the
    message texts and the participant names."""
    labels = []
    for block in MERMAID.findall(DOCS):
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
    assert sorted(tokens - identifiers_in_src()) == []  # fields count: class diagrams name them


def test_every_path_in_the_text_exists() -> None:
    """Python paths in backticks anywhere in the doc; the next test checks tests more strictly."""
    paths = re.findall(r"`((?:[\w-]+/)*\w+\.py)`", DOCS)
    assert len(paths) >= 10, "too few paths found in the text"
    assert sorted({p for p in paths if not path_exists(p)}) == []


def test_every_test_named_in_the_text_exists() -> None:
    files = set(re.findall(r"`(?:tests/)?(test_\w+\.py)`", DOCS))
    assert files, "no tests named in ARCHITECTURE.md"
    assert sorted(f for f in files if not (ROOT / "tests" / f).exists()) == []


EXTERNAL = {"FunctionModel", "NativeOutput", "ToolOutput"}  # Pydantic AI, not in src/
# Backtick names that are settings, JSON values or libraries, not code names of src/
NOT_IN_SRC = {"APP_PASSWORD", "GROQ_API_KEY", "GROQ_MODEL", "llm_error", "unstated", "local",
              "html.escape", "hmac.compare_digest", "subprocess", "uv.lock"}


def section(heading: str) -> str:
    """Text from `heading` to the next heading of the same or a higher level."""
    start = ARCHITECTURE.index(heading)
    level = len(heading) - len(heading.lstrip("#"))
    rest = ARCHITECTURE[start + len(heading):]
    end = re.search(rf"\n#{{1,{level}}} ", rest)
    return rest[:end.start()] if end else rest


def classes_in_src() -> set[str]:
    return {
        node.name
        for path in SRC.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ClassDef)
    }


def identifiers_in_src() -> set[str]:
    """Every name the code binds or uses: classes, functions, fields, arguments, constants."""
    names = code_names()
    for path in SRC.rglob("*.py"):
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            if isinstance(node, ast.Name):
                names.add(node.id)
            elif isinstance(node, ast.arg):
                names.add(node.arg)
            elif isinstance(node, ast.Attribute):
                names.add(node.attr)
    return names


def code_tokens(span: str) -> set[str]:
    """Identifiers in one backtick span that look like code: snake_case, CamelCase, CONSTANT."""
    if span in NOT_IN_SRC or "/" in span or span.startswith(("-", "test_", "<")):
        return set()
    if span.endswith((".py", ".json", ".toml", ".md")):  # files: the path tests cover them
        return set()
    words = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", span)
    shaped = [w for w in words if re.fullmatch(
        r"[a-z]+(?:_[a-z0-9]+)+|[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+|[A-Z]+(?:_[A-Z0-9]+)+", w)]
    return {w for w in shaped if w not in NOT_IN_SRC} - EXTERNAL


def test_every_code_name_in_backticks_exists_in_src() -> None:
    """Functions, classes, fields and constants named anywhere in the doc are real."""
    spans = re.findall(r"`([^`\n]+)`", DOCS)
    tokens = {w for span in spans for w in code_tokens(span)}
    assert len(tokens) >= 40, "too few code names found: the regex no longer matches the doc"
    assert sorted(tokens - identifiers_in_src()) == []


def test_every_class_named_in_the_text_exists() -> None:
    """CamelCase names in backticks are classes (`Finding(FindingDraft)` names two)."""
    spans = re.findall(r"`([^`\n]+)`", DOCS)
    names = {n for span in spans for n in re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+\b", span)}
    names -= EXTERNAL
    assert len(names) >= 6, "too few class names found in the text"
    assert sorted(names - classes_in_src()) == []


def test_the_code_structure_tree_names_real_folders() -> None:
    """Every folder in the Code-Struktur block exists; `name/` sits below its package."""
    tree = section("### Code-Struktur")
    block = re.search(r"```\n(src/govguard/.*?)```", tree, re.DOTALL)
    assert block, "the Code-Struktur block is gone"
    lines = block.group(1).splitlines()
    assert len(lines) >= 6, "too few lines in the Code-Struktur block"
    for line in lines:
        folder, description = line.split(None, 1)
        assert (ROOT / folder).is_dir(), folder
        package = folder.removeprefix("src/").strip("/")
        steps = re.search(r"Ordner: ([\w, ]+)$", description)
        for step in steps.group(1).split(", ") if steps else []:
            assert (SRC / package / step).is_dir(), (folder, step)
        for sub in re.findall(r"\b(\w+)/", description):
            assert (SRC / package / sub).is_dir() or (ROOT / "data" / sub).is_dir(), (folder, sub)


def test_every_rule_in_the_rules_table_points_at_real_code_and_tests() -> None:
    """Section 4.6: each backticked name exists in src/, each `tests/...` file in tests/."""
    table = section("### 4.6 Regeln in Klartext: wo erzwingt der Code sie?")
    rows = [r for r in table.splitlines() if r.startswith("| ") and "`" in r]
    assert len(rows) >= 12, "too few rules found: the table format changed"
    known = identifiers_in_src() | EXTERNAL
    for row in rows:
        for token in re.findall(r"`([^`]+)`", row):
            if token.startswith("tests/"):
                assert (ROOT / token).exists(), token
            elif token.endswith(".py") or token.endswith("/"):
                assert path_exists(token), token
            else:
                assert token in known | {"unstated"}, token


def test_every_test_function_named_in_the_text_exists() -> None:
    named = set(re.findall(r"`(test_\w+)`", DOCS))
    defined = {
        node.name
        for path in (ROOT / "tests").rglob("test_*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef)
    }
    assert len(named) >= 5, "too few test names found in the text"
    assert sorted(named - defined) == []


def test_every_data_path_named_in_the_text_exists() -> None:
    paths = {p.rstrip("/,.") for p in re.findall(r"`(data/[\w./<>|*-]+)`", DOCS)}
    paths = {p for p in paths if not re.search(r"[<>|*]", p)}
    assert len(paths) >= 3, "too few data paths found in the text"
    assert sorted(p for p in paths if not (ROOT / p).exists()) == []
