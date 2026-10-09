import pytest
from pydantic import ValidationError

from kb_build.extracted_models import ExtractedSource, Requirement


def requirement(rid: str, **attributes) -> Requirement:
    return Requirement(
        id=rid, title="t", text="x", primary_anchor=f"A {rid}",
        attributes=attributes, prefilter_passed=False,
    )


def test_each_id_exactly_once() -> None:
    with pytest.raises(ValidationError, match="DET.3.1"):
        ExtractedSource(
            source="BSI", version="sha", origin="o",
            requirements=[requirement("DET.3.1"), requirement("DET.3.1")],
        )


def test_attributes_reject_missing_values() -> None:
    # DESIGN 1.1: attributes are facts (str | int | bool); unknown facts are left out, not None.
    with pytest.raises(ValidationError):
        requirement("3.1.4", level=None)
