"""The machine-readable AI label in the JSON report: field ai_disclosure (#83, KI-VO Art. 50)."""

import json

from ui_helpers import gallery_entry

from govguard.models import AuditReport

STORED = gallery_entry("spec-meldeportal-gesundheit").report


def test_the_json_report_says_what_the_model_wrote_and_on_which_legal_basis() -> None:
    dumped = json.loads(STORED.model_dump_json())

    assert dumped["ai_disclosure"] == {
        "ai_generated": True, "model": STORED.model_id,
        "fields": ["findings[].rationale", "findings[].recommendation"],
        "except_if_listed_in": "findings[].by_code",  # texts the code wrote itself
        "legal_basis": "KI-VO (EU) 2024/1689 Art. 50"}


def test_the_label_follows_the_model_and_a_dumped_report_loads_again() -> None:
    other = STORED.model_copy(update={"model_id": "other/model"})

    assert json.loads(other.model_dump_json())["ai_disclosure"]["model"] == "other/model"
    assert AuditReport.model_validate_json(STORED.model_dump_json()) == STORED
