"""Section starts of a Markdown document: by chapter heading, else by paragraph (#84)."""

import re
from collections import Counter

from govguard.checks.sections_start import Start

_HEADING = re.compile(r"^ {0,3}(#{1,6})\s+(.+?)(?:\s+#+)?\s*$")  # "#Heading" is none
_UNDERLINE = re.compile(r"^ {0,3}(=+|-{2,})\s*$")  # setext: "Title" over "====" or "----"
_FENCES = ("```", "~~~")
_FRONT_LINE = re.compile(r"^(?:[\w-]+:|\s+\S|- )")  # a key, or a continuation of it
# start of a line that is no title: other heading, quote, table, HTML, code, list item, rule
_NOT_TITLE = re.compile(r"^(?:[#>|<`~=+-]|\*(?:\s|$)|\d+[.)]\s)")


def _front_matter_end(lines: list[str]) -> int:
    """Line of the closing --- of a front matter block at the top, else 0: only keys between,
    otherwise the first --- is a rule."""
    if not lines or lines[0].strip() != "---":
        return 0
    for number, line in enumerate(lines[1:], 2):
        if line.strip() in ("---", "..."):
            return number
        if line.strip() and not _FRONT_LINE.match(line):
            return 0
    return 0


def _skipped(lines: list[str]) -> set[int]:
    """Numbers of the lines that hold no headings: front matter at the top and code fences,
    which only their own marker closes ('# x' there is a comment)."""
    skipped = set(range(1, _front_matter_end(lines) + 1))
    fence = None
    for number, line in enumerate(lines, 1):
        marker = next((m for m in _FENCES if line.lstrip().startswith(m)), None)
        if marker and fence in (None, marker):
            fence = None if fence else marker
            skipped.add(number)
        elif fence:
            skipped.add(number)
    return skipped


def _is_title(line: str) -> bool:
    return bool(line.strip()) and not line.startswith(("    ", "\t")) \
        and not _NOT_TITLE.match(line.strip())


def _setext_title(lines: list[str], number: int, skipped: set[int]) -> tuple[int, str] | None:
    """First line and text of the paragraph standing over the underline at line number."""
    start = number - 1
    if start < 1 or start in skipped or not _is_title(lines[start - 1]):
        return None
    while start > 1 and start - 1 not in skipped and _is_title(lines[start - 2]):
        start -= 1
    return start, " ".join(line.strip() for line in lines[start - 1:number - 1])


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    """(line, level, text) of every heading, # style or underlined."""
    skipped, found = _skipped(lines), []
    for number, line in enumerate(lines, 1):
        if number in skipped:
            continue
        if match := _HEADING.match(line):
            found.append((number, len(match[1]), match[2]))
        elif (under := _UNDERLINE.match(line)) and (title := _setext_title(lines, number, skipped)):
            found.append((title[0], 1 if under[1][0] == "=" else 2, title[1]))
    return found


def chapter_starts(lines: list[str]) -> list[Start]:
    """The level is the most frequent one used at least twice, the deeper one on a tie. Every
    heading of that level or a higher one (fewer #) starts a section: a chapter intro above its
    subsections stands alone, so sections stay about one screen long."""
    headings = _headings(lines)
    counted = Counter(level for _, level, _ in headings)
    levels = [lv for lv, n in counted.items() if n >= 2]
    if not levels:
        return []
    level = max(levels, key=lambda lv: (counted[lv], lv))
    return [(number, text) for number, lv, text in headings if lv <= level]


def paragraph_starts(lines: list[str]) -> list[Start]:
    """Text without headings: paragraphs divided by blank lines. The blank lines after a
    paragraph belong to it; blank lines at the start go to the first one (see sections.py)."""
    starts, previous_blank = [], True
    for number, line in enumerate(lines, 1):
        if line.strip() and previous_blank:
            starts.append((number, f"Absatz {len(starts) + 1}"))
        previous_blank = not line.strip()
    return starts
