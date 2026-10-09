import pytest

from govguard.audit_engine import overall_status


@pytest.mark.parametrize(
    ("statuses", "expected"),
    [
        (["PASS", "WARN", "FAIL", "N/A"], "FAIL"),
        (["N/A", "PASS", "WARN"], "WARN"),
        (["N/A", "PASS", "N/A"], "PASS"),
        (["N/A", "N/A"], "N/A"),
    ],
)
def test_overall_status_is_the_worst_status(statuses: list[str], expected: str) -> None:
    assert overall_status(statuses) == expected
