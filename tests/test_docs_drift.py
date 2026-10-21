"""docs/DESIGN.md must not drift from the code (#63): every class and path it names exists."""

import ast
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
SRC = ROOT / "src"
DESIGN = (ROOT / "docs" / "DESIGN.md").read_text(encoding="utf-8")
MERMAID = re.compile(r"```mermaid\n(.*?)```", re.DOTALL)
PACKAGES = ("govguard", "govguard_ui", "kb_build")


def mermaid_blocks(kind: str) -> list[str]:
    return [block for block in MERMAID.findall(DESIGN) if block.startswith(kind)]


def classes_in_src() -> set[str]:
    return {
        node.name
        for path in SRC.rglob("*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.ClassDef)
    }


def test_design_has_the_class_diagrams() -> None:
    assert len(mermaid_blocks("classDiagram")) >= 3  # D12, D13, D13b


def drawn_classes(block: str) -> set[str]:
    """Names from `class X` lines and from both ends of every relation line."""
    names = set(re.findall(r"^\s*class (\w+)\s*(?:\{|:::|$)", block, re.MULTILINE))
    for line in block.splitlines():
        if re.search(r"--|\.\.", line):
            ends = re.sub(r'"[^"]*"', " ", line.split(" : ")[0])
            names |= set(re.findall(r"\w+", ends))
    return names


def test_every_class_in_a_class_diagram_exists_in_src() -> None:
    drawn = set().union(*map(drawn_classes, mermaid_blocks("classDiagram")))
    assert drawn, "no classes found: the regex no longer matches the diagrams"
    assert sorted(drawn - classes_in_src()) == []


def d11_block() -> str:
    [block] = [b for b in mermaid_blocks("flowchart TB") if "subgraph GG" in b]
    return block


def module_tokens(block: str) -> list[tuple[str, str]]:
    """(package, token) per file or folder named in a label; the subgraph sets the package."""
    package, found = "", []
    for line in block.splitlines():
        if title := re.match(r'\s*subgraph \w+\["[^"]*· (\w+)/"\]', line):
            package = title.group(1)
            continue
        if line.strip() == "end":
            package = ""
            continue
        for label in re.findall(r'\["([^"]*)"\]', line):
            label = label.replace("<br/>", " ")
            found += [(package, t) for t in re.findall(r"\w+\.py|\w+/", label)]
    return found


def test_every_module_path_in_d11_exists() -> None:
    tokens = module_tokens(d11_block())
    assert len(tokens) >= 25, "too few paths found: the regex no longer matches D11"
    missing = [
        f"{package}/{token}" for package, token in tokens
        if not ((SRC / package if package else ROOT) / token).exists()
    ]
    assert missing == []


def table_paths(section: str) -> list[str]:
    """Paths in table cells; a bare file name after a full path shares its folder."""
    paths = []
    for row in re.findall(r"^\|.*\|$", section, re.MULTILINE):
        folder = ""
        for code in re.findall(r"`([^`]+)`", row):
            if code.split("/")[0] in PACKAGES:
                folder = code.rsplit("/", 1)[0] if code.endswith(".py") else ""
                paths.append(code)
            elif folder and re.fullmatch(r"\w+\.py", code):
                paths.append(f"{folder}/{code}")
    return paths


def test_every_path_in_the_d11_tables_exists() -> None:
    paths = table_paths(DESIGN[DESIGN.index("## D11"):DESIGN.index("## D12")])
    assert len(paths) >= 25, "too few paths found in the D11 tables"
    assert [p for p in paths if not (SRC / p).exists()] == []


def test_every_named_test_exists() -> None:
    tests = ROOT / "tests"
    files = set(re.findall(r"`(?:tests/)?(test_\w+\.py)`", DESIGN))
    names = set(re.findall(r"`(test_\w+)`", DESIGN))
    defined = {
        node.name
        for path in tests.rglob("test_*.py")
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8")))
        if isinstance(node, ast.FunctionDef)
    }
    assert files and names, "no tests named in DESIGN.md"
    assert sorted(f for f in files if not (tests / f).exists()) == []
    assert sorted(names - defined) == []
