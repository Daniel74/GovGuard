"""Pinned anchors come from the human-made presets (ADR 0011, DESIGN 1.4)."""

from pathlib import Path

import pytest

from govguard.models import Preset
from kb_build.extracted_models import ExtractedSource
from kb_build.gates import pinned_anchors
from kb_build.selection_models import Selection

ROOT = Path(__file__).parent.parent
SOURCES = ["bsi", "c5", "cis", "dsgvo", "fsbp", "sdm"]
ANCHOR_PREFIX = {  # the first word is ambiguous: "BSI C5 …" is not BSI GS++, "AWS FSBP …" is FSBP
    "BSI": "BSI GS++ ", "C5": "BSI C5 ", "CIS": "CIS AWS ", "FSBP": "AWS FSBP ",
    "DSGVO": "DSGVO ", "SDM": "SDM ",
}
PRESETS = [
    Preset.model_validate_json(path.read_text(encoding="utf-8"))
    for path in sorted((ROOT / "data" / "presets").glob("*/preset.json"))
]


def test_spec_audit_pins_the_required_findings_of_the_spec_presets() -> None:
    assert pinned_anchors(PRESETS, "spec") == {"DSGVO Art. 9", "SDM Löschen M60.P01"}


def test_architecture_audit_pins_each_anchor_once() -> None:
    assert pinned_anchors(PRESETS, "architecture") == {
        "CIS AWS v7.0.0 3.1.4", "CIS AWS v7.0.0 4.6", "BSI GS++ BER.4.1",
        "AWS FSBP SNS.1", "AWS FSBP StepFunctions.1",
    }


def source_of(anchor: str) -> str:
    return next(source for source, prefix in ANCHOR_PREFIX.items() if anchor.startswith(prefix))


@pytest.mark.parametrize("source", SOURCES)
def test_every_pinned_anchor_exists_in_the_extracted_sources(source: str) -> None:
    path = ROOT / "data" / "extracted" / f"{source}.json"
    if not path.exists():  # cis.json, c5.json and fsbp.json stay local (ADR 0008)
        pytest.skip(f"{path.name} not extracted on this machine")
    extracted = ExtractedSource.model_validate_json(path.read_text(encoding="utf-8"))
    anchors = {r.primary_anchor for r in extracted.requirements}
    pinned = pinned_anchors(PRESETS, "spec") | pinned_anchors(PRESETS, "architecture")
    assert {a for a in pinned if source_of(a) == extracted.source} <= anchors


@pytest.mark.parametrize(("audit_type", "file"), [
    ("spec", "selection_spec.json"), ("architecture", "selection_arch.json"),
])
def test_every_pinned_anchor_is_in_the_checked_in_catalog(audit_type: str, file: str) -> None:
    """Gate of issue #6 without a kb_build run and without the local extracted sources."""
    path = ROOT / "data" / "knowledge_base" / file
    selected = Selection.model_validate_json(path.read_text(encoding="utf-8")).selected
    missing = [
        anchor for anchor in pinned_anchors(PRESETS, audit_type)
        if not any(  # every anchor ends with its requirement id, e.g. "AWS FSBP SNS.1"
            s.source == source_of(anchor) and anchor.endswith(f" {s.requirement_id}")
            for s in selected
        )
    ]
    assert not missing
