import pytest
from pydantic import ValidationError

from kb_build.extracted_models import ExtractedSource, Requirement, merge_sources


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


def test_merge_sources_joins_sdm_modules_into_one_source() -> None:
    m60 = ExtractedSource(source="SDM", version="V1.0a", origin="loeschen.pdf",
                          requirements=[requirement("M60.D01")])
    m50 = ExtractedSource(source="SDM", version="V1.0", origin="trennen.pdf",
                          requirements=[requirement("M50.D01")])
    merged = merge_sources([m60, m50])
    assert merged.source == "SDM"
    assert merged.version == "V1.0a, V1.0"
    assert merged.origin == "loeschen.pdf, trennen.pdf"
    assert [r.id for r in merged.requirements] == ["M60.D01", "M50.D01"]


def test_merge_sources_keeps_a_single_source_unchanged() -> None:
    bsi = ExtractedSource(source="BSI", version="sha", origin="o", requirements=[])
    assert merge_sources([bsi]) == bsi
