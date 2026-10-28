"""Section starts of a pretty-printed CloudFormation JSON template: one per resource under
Resources, one per other top-level key (#84). Line-based, the file is not parsed again."""

import re

from govguard.checks.sections_start import Start

_KEY = re.compile(r'^([ \t]*)"((?:[^"\\]|\\.)*)"\s*:')


def template_starts(lines: list[str]) -> list[Start]:
    """Empty if the text has no key at the start of a line (not pretty-printed). The lines of the
    braces belong to the section next to them (see sections.py)."""
    keys = [(number, match[1], match[2]) for number, line in enumerate(lines, 1)
            if (match := _KEY.match(line))]
    if not keys:
        return []
    top = len(keys[0][1])
    starts: list[Start] = []
    in_resources, child = False, None  # child: indent of the resources
    for number, spaces, key in keys:
        indent = len(spaces)
        if indent <= top:
            in_resources, child = key == "Resources", None
            starts.append((number, key))
        elif in_resources and child is None:  # the first resource takes the Resources line
            child = indent
            starts[-1] = (starts[-1][0], key)
        elif in_resources and indent == child:
            starts.append((number, key))
    return starts
