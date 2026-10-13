"""Relevance (ADR 0011): the first resource type of a requirement lies in the scope."""

from kb_build.reference.scope import Scope
from kb_build.select.models import Classification
from kb_build.select.relevance import is_relevant

SCOPE = Scope({"S3": ["AWS::S3::Bucket"], "Lambda": ["AWS::Lambda::Function"]})


def classification(*types: str) -> Classification:
    return Classification(testable=True, rationale="x", cfn_resource_types=list(types))


def test_a_requirement_is_relevant_if_its_first_type_is_in_scope() -> None:
    assert is_relevant(classification("AWS::S3::Bucket"), SCOPE)


def test_a_later_type_in_scope_is_not_enough() -> None:
    # CloudTrail rules name S3 as a second type (ADR 0007)
    assert not is_relevant(classification("AWS::CloudTrail::Trail", "AWS::S3::Bucket"), SCOPE)


def test_a_requirement_without_types_is_not_relevant() -> None:
    assert not is_relevant(classification(), SCOPE)
