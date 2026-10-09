"""Presets in data/presets/ (DESIGN 1.4, issue #3). The expected result comes from a human."""

from collections import defaultdict
from pathlib import Path

import pytest

from govguard.models import Preset

PRESETS = Path(__file__).parent.parent / "data" / "presets"
PRESET_DIRS = sorted(path for path in PRESETS.iterdir() if path.is_dir())
MAX_INPUT_CHARS = 100_000
MAX_PINNED_PER_AUDIT_TYPE = 4  # pinned anchors in the bounded catalog (ADR 0007)


def load(preset_dir: Path) -> Preset:
    return Preset.model_validate_json((preset_dir / "preset.json").read_text(encoding="utf-8"))


def test_four_presets_with_expected_result() -> None:
    assert [path.name for path in PRESET_DIRS if (path / "preset.json").is_file()] == [
        path.name for path in PRESET_DIRS
    ]
    assert len(PRESET_DIRS) == 4


@pytest.mark.parametrize("preset_dir", PRESET_DIRS, ids=lambda path: path.name)
def test_input_is_small_enough(preset_dir: Path) -> None:
    inputs = [path for path in preset_dir.iterdir() if path.name != "preset.json"]
    assert len(inputs) == 1
    assert len(inputs[0].read_text(encoding="utf-8")) <= MAX_INPUT_CHARS


@pytest.mark.parametrize("preset_dir", PRESET_DIRS, ids=lambda path: path.name)
def test_preset_points_to_its_input(preset_dir: Path) -> None:
    assert (preset_dir / load(preset_dir).input_file).is_file()


def test_at_most_four_pinned_anchors_per_audit_type() -> None:
    anchors = defaultdict(set)
    for preset in map(load, PRESET_DIRS):
        anchors[preset.audit_type] |= {f.anchor for f in preset.expected.required_findings}
    assert all(len(found) <= MAX_PINNED_PER_AUDIT_TYPE for found in anchors.values())
