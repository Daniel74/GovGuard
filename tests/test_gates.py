"""Gates of the bounded catalog (ADR 0011): the build stops instead of shipping a gap."""

import re

import pytest
from conftest import make_requirement

from govguard.models import CrossReference, Rule, RuleCatalog
from kb_build.extract.models import ExtractedSource
from kb_build.gates import check_coverage, check_pinned, check_rules, is_quoted
from kb_build.reference.scope import Scope
from kb_build.select.models import SelectedRequirement, Selection

SCOPE = Scope({"S3": ["AWS::S3::Bucket"], "KMS": ["AWS::KMS::Key"]})


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


# --- Gate: every rule is schema-valid, anchored and quoted verbatim (ARCHITECTURE 1) -----------

CIS_TEXT = "Amazon S3 provides Block public access (bucket settings) for every bucket."


SOURCES = [
    ExtractedSource(source="CIS", version="v7.0.0", origin="o", requirements=[
        make_requirement("3.1.4", "CIS AWS v7.0.0 3.1.4", CIS_TEXT),
        make_requirement("3.1.5", "CIS AWS v7.0.0 3.1.5",
                         "Ensure that every bucket encrypts data."),
    ]),
    ExtractedSource(source="BSI", version="sha", origin="o", requirements=[
        make_requirement("DET.3.1", "BSI GS++ DET.3.1", "Protokolldaten SOLLTEN zentral liegen."),
    ]),
]


def rule(rid: str = "3.1.4", **changes) -> Rule:
    fields = {
        "id": f"ARCH-CIS-{rid}", "audit_type": "architecture", "source": "CIS",
        "primary_anchor": f"CIS AWS v7.0.0 {rid}", "selection_rationale": "prüfbar",
        "cfn_resource_types": ["AWS::S3::Bucket"], "source_quote": "Block public access",
        "title": "t", "compliant_if": "c", "violation_if": "v", "recommendation": "r",
    }
    return Rule(**fields | changes)


def catalog(*rules: Rule) -> RuleCatalog:
    return RuleCatalog(audit_type="architecture", source_versions={"CIS": "v7.0.0"},
                       model_id="m", rules=list(rules))


def selection_of(*ids: str) -> Selection:
    return Selection(audit_type="architecture", model_id="m",
                     selected=[selected("AWS::S3::Bucket").model_copy(update={"requirement_id": i})
                               for i in ids])


def test_a_rule_anchored_and_quoted_verbatim_passes() -> None:
    check_rules(catalog(rule()), selection_of("3.1.4"), SOURCES, SCOPE)


def test_a_primary_anchor_missing_in_the_source_aborts_and_is_named() -> None:
    invented = rule(primary_anchor="CIS AWS v7.0.0 3.1.99")

    with pytest.raises(ValueError, match=r"ARCH-CIS-3.1.4: primary anchor .*3\.1\.99"):
        check_rules(catalog(invented), selection_of("3.1.4"), SOURCES, SCOPE)


def test_a_quote_from_the_neighbouring_requirement_aborts() -> None:
    # verbatim in CIS 3.1.5, but the rule is anchored to CIS 3.1.4
    borrowed = rule(source_quote="Ensure that every bucket encrypts data.")

    with pytest.raises(ValueError, match="ARCH-CIS-3.1.4: source_quote"):
        check_rules(catalog(borrowed), selection_of("3.1.4"), SOURCES, SCOPE)


def ai_suggested(anchor: str) -> CrossReference:
    return CrossReference(anchor=anchor, origin="ai_suggested")


def test_a_cross_reference_to_an_existing_requirement_of_another_source_passes() -> None:
    linked = rule(cross_references=[ai_suggested("BSI GS++ DET.3.1")])

    check_rules(catalog(linked), selection_of("3.1.4"), SOURCES, SCOPE)


@pytest.mark.parametrize("anchor", ["BSI GS++ DET.3.99", "CIS AWS v7.0.0 3.1.5"],
                         ids=["invented", "same source"])
def test_an_invented_or_same_source_cross_reference_aborts_and_is_named(anchor: str) -> None:
    linked = rule(cross_references=[ai_suggested(anchor)])

    with pytest.raises(ValueError, match=re.escape(f"ARCH-CIS-3.1.4: cross reference {anchor!r}")):
        check_rules(catalog(linked), selection_of("3.1.4"), SOURCES, SCOPE)


def test_a_selected_requirement_without_a_rule_aborts_and_is_named() -> None:
    with pytest.raises(ValueError, match=r"without a rule: \['CIS 3\.1\.5'\]"):
        check_rules(catalog(rule()), selection_of("3.1.4", "3.1.5"), SOURCES, SCOPE)


def test_a_requirement_with_two_rules_aborts() -> None:
    with pytest.raises(ValueError, match=r"more than one rule: \['CIS 3\.1\.4'\]"):
        check_rules(catalog(rule(), rule()), selection_of("3.1.4"), SOURCES, SCOPE)


def test_a_rule_for_a_requirement_that_was_not_selected_aborts() -> None:
    with pytest.raises(ValueError, match=r"not selected: \['CIS 3\.1\.5'\]"):
        check_rules(catalog(rule(), rule("3.1.5", source_quote="every bucket encrypts data")),
                    selection_of("3.1.4"), SOURCES, SCOPE)


def test_a_rule_with_a_type_outside_the_scope_aborts_and_names_it() -> None:
    outside = rule(cfn_resource_types=["AWS::S3::Bucket", "AWS::CloudTrail::Trail"])

    with pytest.raises(ValueError, match=r"outside the scope: \['AWS::CloudTrail::Trail'\]"):
        check_rules(catalog(outside), selection_of("3.1.4"), SOURCES, SCOPE)


def test_criteria_naming_a_type_outside_the_scope_abort() -> None:
    outside = rule(violation_if="AWS::EFS::FileSystem ist unverschlüsselt.")

    with pytest.raises(ValueError, match=r"outside the scope: \['AWS::EFS::FileSystem'\]"):
        check_rules(catalog(outside), selection_of("3.1.4"), SOURCES, SCOPE)


def test_a_text_shorter_than_the_minimum_quote_may_be_quoted_whole() -> None:
    # SDM M60.P03 consists of the one word "Löschkonzept"
    whole = make_requirement("M60.P03", "SDM Löschen M60.P03", "Löschkonzept")
    assert is_quoted(whole, "Löschkonzept")


def test_a_short_part_of_a_longer_text_still_proves_nothing() -> None:
    assert not is_quoted(make_requirement("3.1.4", "CIS AWS v7.0.0 3.1.4", CIS_TEXT), "Amazon S3")
