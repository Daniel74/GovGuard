"""The document line by line for "nach Fundstelle": the bars in the margin, the site a click on
the line opens and the tint (#81). Pure view logic, no Streamlit."""

from pydantic import BaseModel

from govguard.checks.sites import Site
from govguard.models import SEVERITY, Status
from govguard_ui.report.site_lanes import assign_lanes

TINT_BELOW = 15  # lines; a wider site shows only its bar, else it would colour half the document


class Bar(BaseModel):  # the part of a site's bar that stands at one line
    site: int  # index in the list of placed sites
    top: bool  # first line of the site: the count is written here
    end: bool


class LineRow(BaseModel):
    number: int
    text: str
    bars: list[Bar | None]  # one cell per lane
    owner: int | None  # site a click on the line opens: the narrowest one holding it
    tint: Status | None
    selected: bool


def line_rows(text: str, sites: list[Site], current: int | None) -> list[LineRow]:
    lane_of = assign_lanes(sites)
    lanes = max(lane_of, default=-1) + 1
    rows = []
    for number, line in enumerate(text.splitlines(), 1):
        holding = [i for i, s in enumerate(sites) if s.line_start <= number <= s.line_end]
        bars: list[Bar | None] = [None] * lanes
        for i in holding:
            bars[lane_of[i]] = Bar(site=i, top=sites[i].line_start == number,
                                   end=sites[i].line_end == number)
        narrow = [sites[i].worst for i in holding if sites[i].width < TINT_BELOW]
        rows.append(LineRow(
            number=number, text=line, bars=bars,
            owner=min(holding, key=lambda i: sites[i].width, default=None),
            tint=max(narrow, key=SEVERITY.__getitem__, default=None), selected=current in holding))
    return rows
