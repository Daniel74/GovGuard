"""Property paths of a CloudFormation resource schema (SPEC: no invented properties, #17)."""

import json
from pathlib import Path

from kb_build.cfn_properties import (
    build_snapshot,
    load_cfn_properties,
    property_candidates,
    property_paths,
    unknown_properties,
)

SCHEMA = {
    "properties": {
        "LoggingConfiguration": {"$ref": "#/definitions/LoggingConfiguration"},
        "Tags": {"type": "array", "items": {"$ref": "#/definitions/Tag"}},
        "BucketName": {"type": "string"},
    },
    "definitions": {
        "LoggingConfiguration": {
            "type": "object",
            "properties": {"LogFilePrefix": {"type": "string"}},
        },
        "Tag": {"type": "object", "properties": {"Key": {"type": "string"}}},
    },
}


def test_paths_follow_refs_and_array_items_to_the_nested_properties() -> None:
    assert property_paths(SCHEMA) == {
        "LoggingConfiguration", "LoggingConfiguration.LogFilePrefix",
        "Tags", "Tags.Key", "BucketName",
    }


def test_a_recursive_definition_is_expanded_only_once() -> None:
    schema = {
        "properties": {"Rule": {"$ref": "#/definitions/Rule"}},
        "definitions": {"Rule": {"properties": {"Child": {"$ref": "#/definitions/Rule"}}}},
    }

    assert property_paths(schema) == {"Rule", "Rule.Child"}


def test_the_snapshot_maps_each_type_to_its_sorted_paths(tmp_path: Path) -> None:
    schemas = {"AWS::S3::Bucket": json.dumps(SCHEMA)}

    snapshot = build_snapshot(schemas)

    assert snapshot["AWS::S3::Bucket"][:2] == ["BucketName", "LoggingConfiguration"]
    file = tmp_path / "props.json"
    file.write_text(json.dumps(snapshot), encoding="utf-8")
    assert "LoggingConfiguration.LogFilePrefix" in load_cfn_properties(file)["AWS::S3::Bucket"]


def test_candidates_are_dot_paths_and_multi_part_pascal_case_names() -> None:
    text = ("AWS::ElasticLoadBalancingV2::Listener mit DefaultActions.RedirectConfig.Protocol "
            "und SSEEnabled: true; Alle Eigenschaften, MultiAZ, IAM, TLS1.2, HTTPS ausgenommen.")

    assert property_candidates(text) == [
        "DefaultActions.RedirectConfig.Protocol", "SSEEnabled", "MultiAZ",
    ]


def test_product_names_iam_keys_and_function_names_are_no_candidates() -> None:
    text = ("Das CloudFormation-Template für DynamoDB und PostgreSQL nutzt "
            "aws:SecureTransport mit StringEquals und Fn::GetAtt, AWS::S3::Bucket.Arn.")

    assert property_candidates(text) == []


KNOWN = {
    "AWS::S3::Bucket": frozenset({"LoggingConfiguration", "LoggingConfiguration.LogFilePrefix"}),
    "AWS::ElasticLoadBalancingV2::Listener": frozenset({"DefaultActions", "DefaultActions.Type"}),
}


def test_an_invented_property_is_reported_and_a_real_one_is_not() -> None:
    text = "AWS::S3::Bucket hat LoggingConfiguration.TargetPrefix und LogFilePrefix"

    unknown = unknown_properties(text, ["AWS::S3::Bucket"], KNOWN)

    assert unknown == ["LoggingConfiguration.TargetPrefix"]


def test_a_dot_path_may_start_below_the_top_level_and_a_name_may_be_nested() -> None:
    text = "LogFilePrefix und LoggingConfiguration.LogFilePrefix"

    assert unknown_properties(text, ["AWS::S3::Bucket"], KNOWN) == []


def test_a_property_of_any_type_of_the_rule_counts() -> None:
    types = ["AWS::S3::Bucket", "AWS::ElasticLoadBalancingV2::Listener"]

    assert unknown_properties("DefaultActions und LogFilePrefix", types, KNOWN) == []


def test_without_a_snapshot_for_any_type_nothing_can_be_judged() -> None:
    assert unknown_properties("TargetPrefix", ["AWS::Foo::Bar"], KNOWN) == []


def test_names_of_other_resource_types_are_no_properties() -> None:
    # S3 BucketPolicy and EC2 NetworkAclEntry are resources of their own
    text = "AWS::S3::Bucket mit BucketPolicy und NetworkAclEntry"

    assert unknown_properties(text, ["AWS::S3::Bucket"], KNOWN) == []


def test_values_such_as_managed_policies_and_canned_acls_are_no_properties() -> None:
    text = "Weder AdministratorAccess noch AWSManagedRulesCommonRuleSet noch PublicReadWrite"

    assert unknown_properties(text, ["AWS::S3::Bucket"], KNOWN) == []


def test_a_rule_with_a_type_without_snapshot_is_not_judged() -> None:
    # the second type is outside the scope: its properties are unknown, so nothing is invented
    types = ["AWS::S3::Bucket", "AWS::CloudFront::Distribution"]

    assert unknown_properties("ViewerProtocolPolicy", types, KNOWN) == []


def test_a_type_named_in_the_text_counts_like_a_type_of_the_rule() -> None:
    # the model writes "AWS::EC2::SecurityGroup mit CidrIp" although the rule lists other types
    known = KNOWN | {"AWS::EC2::SecurityGroup": frozenset({"CidrIp"})}
    text = "AWS::S3::Bucket und AWS::EC2::SecurityGroup mit CidrIp und TargetPrefix"

    assert unknown_properties(text, ["AWS::S3::Bucket"], known) == ["TargetPrefix"]


def test_a_type_named_in_the_text_without_snapshot_makes_the_rule_unjudged() -> None:
    text = "AWS::S3::Bucket und AWS::CloudFront::Distribution mit ViewerProtocolPolicy"

    assert unknown_properties(text, ["AWS::S3::Bucket"], KNOWN) == []
