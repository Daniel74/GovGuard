"""Presets in data/presets/ (DESIGN 1.4, issue #3). The expected result comes from a human."""

import json
from pathlib import Path

import pytest

from govguard.models import Preset

DATA = Path(__file__).parent.parent / "data"
PRESETS = DATA / "presets"
PRESET_DIRS = sorted(path for path in PRESETS.iterdir() if path.is_dir())
MAX_INPUT_CHARS = 100_000


def load(preset_dir: Path) -> Preset:
    return Preset.model_validate_json((preset_dir / "preset.json").read_text(encoding="utf-8"))


def test_five_presets_with_expected_result() -> None:
    assert [path.name for path in PRESET_DIRS if (path / "preset.json").is_file()] == [
        path.name for path in PRESET_DIRS
    ]
    assert len(PRESET_DIRS) == 5


@pytest.mark.parametrize("preset_dir", PRESET_DIRS, ids=lambda path: path.name)
def test_input_is_small_enough(preset_dir: Path) -> None:
    inputs = [path for path in preset_dir.iterdir() if path.name != "preset.json"]
    assert len(inputs) == 1
    assert len(inputs[0].read_text(encoding="utf-8")) <= MAX_INPUT_CHARS


@pytest.mark.parametrize("preset_dir", PRESET_DIRS, ids=lambda path: path.name)
def test_preset_points_to_its_input(preset_dir: Path) -> None:
    assert (preset_dir / load(preset_dir).input_file).is_file()


def resources(preset_id: str) -> dict[str, dict]:
    template = json.loads((PRESETS / preset_id / "template.json").read_text(encoding="utf-8"))
    return template["Resources"]


def test_foreign_preset_shares_no_component_with_the_archetypes() -> None:  # ADR 0011, issue #15
    profiles = json.loads((DATA / "archetype_profiles.json").read_text(encoding="utf-8"))
    components = {t for profile in profiles for t in profile["required_types"]}
    types = {resource["Type"] for resource in resources("arch-fristenwecker").values()}
    assert not types & components
    assert "AWS::KMS::Key" not in types


def test_foreign_preset_carries_its_required_findings_as_properties() -> None:
    by_type = {r["Type"]: r.get("Properties", {}) for r in resources("arch-fristenwecker").values()}
    assert "KmsMasterKeyId" not in by_type["AWS::SNS::Topic"]  # FSBP SNS.1 = FAIL
    assert by_type["AWS::StepFunctions::StateMachine"]["LoggingConfiguration"]["Level"] == "ALL"
