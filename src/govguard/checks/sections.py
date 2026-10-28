"""Dokumentabschnitte (sections) of an audited document: chapter, resource or path, without gap
and overlap, at a fixed level per format, so a line belongs to exactly one site (#84). Pure."""

import re

from pydantic import BaseModel

from govguard.checks.sections_json import template_starts
from govguard.checks.sections_markdown import chapter_starts, paragraph_starts
from govguard.checks.sections_start import Start
from govguard.checks.sections_yaml import openapi_starts

PREAMBLE = "Vorspann"
# openapi: or swagger: as the first key, after blank lines, comments and a --- only
_OPENAPI = re.compile(r"(?:[ \t]*(?:#[^\n]*)?\r?\n|---[ \t]*\r?\n)*(?:openapi|swagger):")


class DocSection(BaseModel):
    name: str
    line_start: int
    line_end: int


def _sections(starts: list[Start], total: int) -> list[DocSection]:
    """Each section runs to the line before the next one; the first starts at line 1."""
    starts = [(1, starts[0][1]), *starts[1:]]
    ends = [line - 1 for line, _ in starts[1:]] + [total]
    return [DocSection(name=name, line_start=line, line_end=end)
            for (line, name), end in zip(starts, ends, strict=True)]


def _starts(name: str, text: str, lines: list[str]) -> list[Start]:
    """The format by file name or content: a .md file is Markdown; else JSON if it starts with a
    brace, OpenAPI if `openapi:` or `swagger:` is the first key, else Markdown (FUNKTIONSWEISE 5).
    """
    if not name.endswith(".md"):
        if name.endswith(".json") or text.lstrip().startswith("{"):
            return template_starts(lines)
        if name.endswith((".yaml", ".yml")) or _OPENAPI.match(text):
            return openapi_starts(lines)
    chapters = chapter_starts(lines)
    if chapters and chapters[0][0] > 1:  # the text before the first heading
        chapters = [(1, PREAMBLE), *chapters]
    return chapters


def split_sections(name: str, text: str) -> list[DocSection]:
    """name: file name of the input; the format decides the level (FUNKTIONSWEISE 5)."""
    lines = text.splitlines()
    if not lines:
        return []
    starts = _starts(name, text, lines) or paragraph_starts(lines) or [(1, PREAMBLE)]
    return _sections(starts, len(lines))
