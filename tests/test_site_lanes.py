"""Margin lanes of the site bars: overlapping sites stand side by side (#81). Pure view logic."""

from site_factories import site

from govguard_ui.report.site_lanes import assign_lanes


def test_sites_that_do_not_overlap_share_a_lane() -> None:
    assert assign_lanes([site(1, 5), site(6, 9), site(20, 20)]) == [0, 0, 0]


def test_overlapping_sites_get_their_own_lanes() -> None:
    assert assign_lanes([site(1, 10), site(5, 7), site(8, 12)]) == [0, 1, 1]


def test_a_lane_is_free_again_after_the_last_line_of_its_site() -> None:
    """A site ending on line 5 and one starting on line 5 overlap: both own that line."""
    assert assign_lanes([site(1, 5), site(5, 8)]) == [0, 1]

