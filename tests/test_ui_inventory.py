"""Guard of the interaction inventory: every control of the demo UI has its test (ADR 0024, #44).

The inventory lists each widget, page link and download of src/govguard_ui with the test that
uses it. A control is any call with a key or of an own component (CCv2, #45), so a new widget type
needs no list here. A new control without an entry, an entry whose control is gone and an entry
whose test does not exist make this test red.
"""

import ast
from pathlib import Path

from ui_inventory import INVENTORY

TESTS = Path(__file__).parent
UI = TESTS.parent / "src" / "govguard_ui"
NO_CONTROL = {"container"}  # takes a key for its CSS class, nobody clicks it
WITHOUT_KEY = {"page_link", "switch_page"}  # page changes need no key


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


def components_in(tree: ast.AST) -> set[str]:
    """Names bound to an own component: NAME = st.components.v2.component(...)."""
    return {target.id for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "component"
            for target in node.targets if isinstance(target, ast.Name)}


def control_name(node: ast.AST, components: set[str]) -> str | None:
    """st.<widget>(..., key=...), a page change or a call of an own component."""
    if not isinstance(node, ast.Call):
        return None
    if isinstance(node.func, ast.Name):
        return node.func.id if node.func.id in components else None
    if not isinstance(node.func, ast.Attribute):
        return None
    name = node.func.attr
    has_key = any(keyword.arg == "key" for keyword in node.keywords)
    return name if name not in NO_CONTROL and (has_key or name in WITHOUT_KEY) else None


def controls_in(source: str) -> set[str]:
    tree = ast.parse(source)
    components = components_in(tree)
    return {f"{name}:{key_pattern(node)}" for node in ast.walk(tree)
            if (name := control_name(node, components))}


def controls_in_code() -> set[str]:
    return set().union(*(controls_in(path.read_text()) for path in sorted(UI.rglob("*.py"))))


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


def test_the_guard_sees_any_widget_with_a_key_and_every_page_change_but_no_container() -> None:
    source = ('st.checkbox("Neu", key="new")\nst.page_link("p.py")\nst.switch_page("p.py")\n'
              'tile.container(border=True, key=f"{key}_tile")\nst.markdown("Text")\n')

    assert controls_in(source) == {"checkbox:new", "page_link:-", "switch_page:-"}


def test_the_guard_sees_a_call_of_an_own_component_but_no_other_function_with_a_key() -> None:
    source = ('TABLE = st.components.v2.component("t", html="<table>")\n'
              'TABLE(data=rows, key=f"{key}_table")\nrender_report(report, key="created")\n')

    assert controls_in(source) == {"TABLE:{}_table"}
