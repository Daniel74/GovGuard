"""The document line by line for "nach Fundstelle": the bar in the margin, the site a click on the
line opens, the tint, and the marks of the current site and of the selected finding (#81, #84).
Sites never overlap, so one lane is enough. Pure view logic, no Streamlit."""

from pydantic import BaseModel

from govguard.checks.sites import Site
from govguard.models import Status

TINT_BELOW = 15  # lines; a wider site shows only its bar, else it would colour half the document


class Bar(BaseModel):  # the part of a site's bar that stands at one line
    site: int  # index in the list of placed sites; a click on the bar or the line opens it
    top: bool  # first line of the site: the count is written here
    end: bool


class LineRow(BaseModel):
    number: int
    text: str
    bar: Bar | None
    tint: Status | None
    in_site: bool  # a line of the current site: light
    in_finding: bool  # a line of the selected finding, in any section: strong


def _site_at(sites: list[Site]) -> dict[int, int]:
    """Line -> index of the site holding it."""
    return {n: i for i, s in enumerate(sites) for n in range(s.line_start, s.line_end + 1)}


def line_rows(text: str, sites: list[Site], current: int | None,
              span: tuple[int, int] | None) -> list[LineRow]:
    """current: index of the open site; span: first and last line of the selected finding."""
    held = _site_at(sites)
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        i = held.get(number)
        site = sites[i] if i is not None else None
        bar = site and Bar(site=i, top=site.line_start == number, end=site.line_end == number)
        tint = site.worst if site and site.width < TINT_BELOW else None
        rows.append(LineRow(number=number, text=line, bar=bar, tint=tint,
                            in_site=i is not None and i == current,
                            in_finding=span is not None and span[0] <= number <= span[1]))
    return rows
