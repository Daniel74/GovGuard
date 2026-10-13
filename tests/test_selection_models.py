"""Classification: the level of the duty (issue #18)."""

import pytest
from pydantic import ValidationError

from kb_build.select.judgement_cache import JudgementCache
from kb_build.select.models import Classification


def test_scope_level_defaults_to_template() -> None:
    assert Classification(testable=True, rationale="x").scope_level == "template"


@pytest.mark.parametrize("level", ["template", "account", "people", "provider"])
def test_scope_level_accepts_the_four_levels(level: str) -> None:
    assert Classification(testable=True, rationale="x", scope_level=level).scope_level == level


def test_scope_level_rejects_any_other_value() -> None:
    with pytest.raises(ValidationError):
        Classification(testable=True, rationale="x", scope_level="organisation")


def test_a_cache_written_before_scope_level_stays_readable() -> None:
    raw = '{"k": {"testable": true, "rationale": "x", "cfn_resource_types": []}}'

    assert JudgementCache.from_json(raw).get("k").scope_level == "template"
