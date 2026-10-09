"""Pinned anchors come from the human-made presets (ADR 0007, DESIGN 1.4)."""

from pathlib import Path

import pytest

from govguard.models import Preset
from kb_build.curation import MAX_PINNED, pinned_anchors
from kb_build.extracted_models import ExtractedSource

ROOT = Path(__file__).parent.parent
PRESETS = [
    Preset.model_validate_json(path.read_text(encoding="utf-8"))
    for path in sorted((ROOT / "data" / "presets").glob("*/preset.json"))
]


def test_spec_audit_pins_the_required_findings_of_the_spec_presets() -> None:
    assert pinned_anchors(PRESETS, "spec") == {"DSGVO Art. 9", "SDM Löschen M60.P01"}


def test_architecture_audit_pins_each_anchor_once() -> None:
    assert pinned_anchors(PRESETS, "architecture") == {
        "CIS AWS v7.0.0 3.1.4", "CIS AWS v7.0.0 4.6", "BSI GS++ BER.4.1",
    }


@pytest.mark.parametrize("audit_type", ["spec", "architecture"])
def test_at_most_four_pinned_anchors(audit_type: str) -> None:
    assert len(pinned_anchors(PRESETS, audit_type)) <= MAX_PINNED


@pytest.mark.parametrize("source", ["bsi", "cis", "dsgvo", "sdm"])
def test_every_pinned_anchor_exists_in_the_extracted_sources(source: str) -> None:
    path = ROOT / "data" / "extracted" / f"{source}.json"
    if not path.exists():  # cis.json stays local (ADR 0008)
        pytest.skip(f"{path.name} not extracted on this machine")
    extracted = ExtractedSource.model_validate_json(path.read_text(encoding="utf-8"))
    anchors = {r.primary_anchor for r in extracted.requirements}
    pinned = pinned_anchors(PRESETS, "spec") | pinned_anchors(PRESETS, "architecture")
    own = {a for a in pinned if a.split()[0] == extracted.source}
    assert own <= anchors
