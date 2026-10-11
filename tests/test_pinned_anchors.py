"""Pinned anchors come from the human-made presets (ADR 0011, DESIGN 1.4)."""

import json
from pathlib import Path

import pytest

from govguard.models import Preset
from kb_build.extracted_models import ExtractedSource
from kb_build.gates import pinned_anchors

ROOT = Path(__file__).parent.parent
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


@pytest.mark.parametrize("source", ["bsi", "c5", "cis", "dsgvo", "fsbp", "sdm"])
def test_every_pinned_anchor_exists_in_the_extracted_sources(source: str) -> None:
    path = ROOT / "data" / "extracted" / f"{source}.json"
    if not path.exists():  # cis.json stays local (ADR 0008)
        pytest.skip(f"{path.name} not extracted on this machine")
    extracted = ExtractedSource.model_validate_json(path.read_text(encoding="utf-8"))
    anchors = {r.primary_anchor for r in extracted.requirements}
    pinned = pinned_anchors(PRESETS, "spec") | pinned_anchors(PRESETS, "architecture")
    own = {a for a in pinned if a.startswith(ANCHOR_PREFIX[extracted.source])}
    assert own <= anchors



@pytest.mark.parametrize("source", ["bsi", "c5", "cis", "dsgvo", "fsbp", "sdm"])
def test_every_pinned_anchor_is_in_the_checked_in_catalog(source: str) -> None:
    path = ROOT / "data" / "extracted" / f"{source}.json"
    if not path.exists():  # cis.json stays local (ADR 0008)
        pytest.skip(f"{path.name} not extracted on this machine")
    extracted = ExtractedSource.model_validate_json(path.read_text(encoding="utf-8"))
    ids = {r.primary_anchor: r.id for r in extracted.requirements}
    selected = {
        s["requirement_id"]
        for file in ["selection_spec.json", "selection_arch.json"]
        for s in json.loads((ROOT / "data" / "knowledge_base" / file).read_text(encoding="utf-8"))[
            "selected"
        ]
        if s["source"] == extracted.source
    }
    pinned = pinned_anchors(PRESETS, "spec") | pinned_anchors(PRESETS, "architecture")
    own = {a for a in pinned if a.startswith(ANCHOR_PREFIX[extracted.source])}
    assert {ids[a] for a in own} <= selected  # gate of issue #6, without a kb_build run
