"""Image comparison and side-by-side image of the screenshot regression, no browser (#40)."""

from PIL import Image
from snapshots import HEADER, compare, side_by_side


def blank(width: int = 40, height: int = 30) -> Image.Image:
    return Image.new("RGB", (width, height), "white")


def test_identical_images_have_no_diff() -> None:
    assert compare(blank(), blank()) is None


def test_a_few_changed_pixels_still_count_as_equal() -> None:
    actual = blank(1440, 2000)
    actual.paste((0, 0, 0), (10, 10, 15, 15))

    assert compare(actual, blank(1440, 2000)) is None


def test_a_thin_line_on_a_tall_page_yields_a_diff_image() -> None:
    actual = blank(1440, 2000)
    actual.paste((0, 0, 0), (100, 100, 1100, 101))

    assert compare(actual, blank(1440, 2000)) is not None


def test_a_changed_area_yields_a_diff_image() -> None:
    actual = blank()
    actual.paste((0, 0, 0), (10, 10, 30, 30))

    diff = compare(actual, blank())

    assert diff is not None
    assert diff.size == (40, 30)


def test_a_different_size_is_a_diff_even_if_the_overlap_is_equal() -> None:
    diff = compare(blank(height=50), blank())

    assert diff is not None
    assert diff.size == (40, 50)


def test_side_by_side_puts_design_left_and_streamlit_right_under_a_header() -> None:
    design, streamlit = blank(40, 30), Image.new("RGB", (60, 50), "black")

    image = side_by_side(design, streamlit)

    assert image.size == (100, 50 + HEADER)
    assert image.getpixel((70, HEADER + 10)) == (0, 0, 0)
    assert image.getpixel((20, HEADER + 40)) != (0, 0, 0)
