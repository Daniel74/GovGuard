"""Margin lanes for the site bars of "nach Fundstelle": sites that share lines stand side by side
(#81). Pure view logic, no Streamlit."""

from govguard.checks.sites import Site


def assign_lanes(sites: list[Site]) -> list[int]:
    """Lane of each site, in the order given (by first line): the first lane free again."""
    lane_ends: list[int] = []  # last line held by each lane
    lanes = []
    for site in sites:
        free = next((i for i, end in enumerate(lane_ends) if end < site.line_start), None)
        if free is None:
            free = len(lane_ends)
            lane_ends.append(site.line_end)
        lane_ends[free] = site.line_end
        lanes.append(free)
    return lanes
