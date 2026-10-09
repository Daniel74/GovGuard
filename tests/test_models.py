import pytest
from pydantic import ValidationError

from govguard.models import RuleCatalog


def test_rule_catalog_needs_at_least_one_rule() -> None:
    with pytest.raises(ValidationError):  # no rules would mean no overall status
        RuleCatalog(audit_type="spec", source_versions={}, model_id="fake-model", rules=[])
