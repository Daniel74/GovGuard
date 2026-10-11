"""Gates of the bounded catalog (ADR 0011): the build stops instead of shipping a gap."""

import pytest

from kb_build.gates import check_coverage, check_pinned
from kb_build.selection_models import SelectedRequirement


def selected(*types: str) -> SelectedRequirement:
    return SelectedRequirement(requirement_id="3.1.4", source="CIS", rationale="x",
                               cfn_resource_types=list(types))


def test_selected_pinned_anchors_pass() -> None:
    check_pinned({"A 1"}, {"A 1": "selected"})


def test_a_pinned_anchor_with_another_outcome_aborts_and_names_the_outcome() -> None:
    with pytest.raises(ValueError, match=r"A 2 \(not_testable\)"):
        check_pinned({"A 1", "A 2"}, {"A 1": "selected", "A 2": "not_testable"})


def test_a_pinned_anchor_without_outcome_is_missing_in_the_sources() -> None:
    with pytest.raises(ValueError, match="not found in the sources: \\['A 9'\\]"):
        check_pinned({"A 9"}, {})


def test_every_component_with_a_rule_passes() -> None:
    check_coverage(frozenset({"AWS::S3::Bucket"}), [selected("AWS::S3::Bucket")])


def test_a_component_at_any_position_counts_like_the_runtime_pruning() -> None:
    # audit_engine sends a rule to the model if any of its types is in the template (ADR 0007)
    check_coverage(frozenset({"AWS::KinesisFirehose::DeliveryStream"}),
                   [selected("AWS::Logs::LogGroup", "AWS::KinesisFirehose::DeliveryStream")])


def test_a_component_without_a_rule_aborts_and_is_named() -> None:
    with pytest.raises(ValueError, match="AWS::SQS::Queue"):
        check_coverage(frozenset({"AWS::S3::Bucket", "AWS::SQS::Queue"}),
                       [selected("AWS::S3::Bucket")])
