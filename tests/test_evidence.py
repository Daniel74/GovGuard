"""Evidence by line reference (ADR 0017): range checks shared by audit and free-text pre-run."""

from govguard.evidence import range_problem
from govguard.text import contains_quote

TEXT = "**S3-Bucket** ist\nDer Archiv-Bucket blockiert öffentlichen Zugriff."


def test_range_measures_min_length_like_a_quote_without_markdown() -> None:
    # 17 chars with asterisks, 13 without: as short as the same text as a build quote (DESIGN 3)
    assert not contains_quote(TEXT, "**S3-Bucket** ist")
    assert "zu kurz" in range_problem(TEXT, 1, 1)


def test_range_with_enough_text_is_fine() -> None:
    assert range_problem(TEXT, 2, 2) is None
