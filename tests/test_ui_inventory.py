"""Guard of the interaction inventory: every control of the demo UI has its test (ADR 0024, #44).

The inventory lists each widget, page link and download of src/govguard_ui with the test that
uses it. A new control without an entry, an entry whose control is gone and an entry whose test
does not exist make this test red.
"""

import ast
from pathlib import Path

from ui_inventory import INVENTORY

TESTS = Path(__file__).parent
UI = TESTS.parent / "src" / "govguard_ui"
CONTROLS = {"button", "download_button", "page_link", "switch_page", "pills", "segmented_control",
            "toggle", "selectbox", "radio", "text_input", "text_area", "tabs", "dataframe"}


def key_pattern(call: ast.Call) -> str:
    """The key argument as written; an f-string shows its parts as {}, no key as -."""
    for keyword in call.keywords:
        if keyword.arg == "key":
            value = keyword.value
            if isinstance(value, ast.Constant):
                return str(value.value)
            if isinstance(value, ast.JoinedStr):
                return "".join(p.value if isinstance(p, ast.Constant) else "{}"
                               for p in value.values)
            return "{}"
    return "-"


def controls_in_code() -> set[str]:
    found = set()
    for path in sorted(UI.glob("*.py")):
        for node in ast.walk(ast.parse(path.read_text())):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr in CONTROLS):
                found.add(f"{node.func.attr}:{key_pattern(node)}")
    return found


def test_every_control_of_the_ui_is_in_the_inventory() -> None:
    assert sorted(controls_in_code() - INVENTORY.keys()) == []


def test_no_inventory_entry_names_a_control_that_is_gone() -> None:
    assert sorted(INVENTORY.keys() - controls_in_code()) == []


def test_every_inventory_entry_names_an_existing_test() -> None:
    def tests_in(file: str) -> set[str]:
        tree = ast.parse((TESTS.parent / file).read_text())
        return {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}

    missing = [f"{control} -> {test}" for control, test in INVENTORY.items()
               if test.split("::")[1] not in tests_in(test.split("::")[0])]
    assert missing == []
