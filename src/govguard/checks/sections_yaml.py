"""Section starts of an OpenAPI YAML document: one per path, one per schema, one per other block
of the top level; a block that holds Markdown in a block scalar (info.description) is split by
its headings (#84). Line-based by indentation, no YAML library."""

import re
import textwrap

from govguard.checks.sections_markdown import chapter_starts
from govguard.checks.sections_start import Start

_KEY = re.compile(r"""^( *)(?:"([^"]+)"|'([^']+)'|([^\s#'"\-].*?)):(?:\s+(\S.*))?\s*$""")
# "description: |", "|2-", "| # note": the lines below are text
_BLOCK_SCALAR = re.compile(r"^[|>]([+-]?\d?|\d?[+-]?)(\s+#.*)?$")
_CONTAINERS = {("paths",), ("components",), ("components", "schemas")}  # only their children count


def _keys(lines: list[str]) -> list[tuple[int, int, str, bool]]:
    """(line, indent, key, opens a block scalar) of every mapping key outside a block scalar."""
    found, skip_deeper_than = [], None
    for number, line in enumerate(lines, 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if skip_deeper_than is not None and indent > skip_deeper_than:
            continue
        skip_deeper_than = None
        if match := _KEY.match(line):
            scalar = bool(_BLOCK_SCALAR.match(match[5] or ""))
            found.append((number, indent, match[2] or match[3] or match[4], scalar))
            skip_deeper_than = indent if scalar else None
    return found


def _scalar_lines(lines: list[str], number: int, indent: int) -> list[str]:
    """The text of the block scalar whose key stands at line number, without its indentation."""
    body: list[str] = []
    for line in lines[number:]:
        if line.strip() and len(line) - len(line.lstrip()) <= indent:
            break
        body.append(line)
    while body and not body[-1].strip():
        body.pop()
    return textwrap.dedent("\n".join(body)).splitlines()


def _name(path: tuple[str, ...]) -> str | None:
    """Name of the section a key at this path starts, None if it is part of a bigger one."""
    if len(path) == 1 and path not in _CONTAINERS:
        return path[0]
    if path[0] == "paths" and len(path) == 2:
        return path[1]
    if path[0] == "components" and len(path) == 2 and path[1] != "schemas":
        return f"components/{path[1]}"
    if path[:2] == ("components", "schemas") and len(path) == 3:
        return f"Schema {path[2]}"
    return None


def openapi_starts(lines: list[str]) -> list[Start]:
    """Empty if the text has no mapping key. The line of a container (paths:, components:,
    schemas:) belongs to its first child."""
    starts: list[Start] = []
    stack: list[tuple[int, str]] = []  # indent and key of the parents
    pending = None  # line of a container header, taken by the next section
    after_scalar = False  # a split scalar just ended: the next key of its block is no chapter
    for number, indent, key, scalar in _keys(lines):
        while stack and stack[-1][0] >= indent:
            stack.pop()
        stack.append((indent, key))
        path = tuple(k for _, k in stack)
        if after_scalar and len(path) > 1:
            starts.append((number, path[0]))
        after_scalar = False
        if path in _CONTAINERS and pending is None:
            pending = number
        elif name := _name(path):
            starts.append((pending or number, name))
            pending = None
        if scalar and len(path) > 1 and path[0] not in ("paths", "components"):
            chapters = chapter_starts(_scalar_lines(lines, number, indent))
            starts += [(number + line, title) for line, title in chapters]
            after_scalar = bool(chapters)
    return starts
