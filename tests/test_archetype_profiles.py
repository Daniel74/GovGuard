"""Archetype profiles (ARCHITECTURE 1.4): the only fixed input to the relevance filter."""

from kb_build.archetype_profiles import load_profiles, relevant_resource_types

# Sub-resources that every serverless CDK template contains next to the required types
ALWAYS_RELEVANT = {
    "AWS::IAM::Role", "AWS::IAM::Policy", "AWS::KMS::Key", "AWS::Logs::LogGroup",
    "AWS::ApiGateway::Stage", "AWS::ApiGateway::Method",
}


def test_three_profiles_in_fixed_order() -> None:
    assert [p.id for p in load_profiles()] == ["ARCH-01", "ARCH-02", "ARCH-03"]


def test_resource_types_are_required_types_plus_the_serverless_sub_resources() -> None:
    for profile in load_profiles():
        extra = {"AWS::S3::BucketPolicy"} if "AWS::S3::Bucket" in profile.required_types else set()
        assert set(profile.resource_types) == set(profile.required_types) | ALWAYS_RELEVANT | extra


def test_required_types_match_architecture_table() -> None:
    required = {p.id: set(p.required_types) for p in load_profiles()}
    assert required["ARCH-01"] == {
        "AWS::ApiGateway::RestApi", "AWS::Lambda::Function", "AWS::DynamoDB::Table"
    }
    assert required["ARCH-02"] == {
        "AWS::ApiGateway::RestApi", "AWS::Lambda::Function", "AWS::SQS::Queue", "AWS::S3::Bucket"
    }
    assert required["ARCH-03"] == {
        "AWS::ApiGateway::RestApi", "AWS::Lambda::Function",
        "AWS::KinesisFirehose::DeliveryStream", "AWS::S3::Bucket",
    }


def test_relevant_resource_types_is_the_union_of_all_profiles() -> None:
    types = relevant_resource_types(load_profiles())
    assert "AWS::DynamoDB::Table" in types
    assert "AWS::KinesisFirehose::DeliveryStream" in types
    assert "AWS::EC2::Instance" not in types  # serverless only


def test_every_profile_resource_type_exists_in_cloudformation() -> None:
    from kb_build.cfn_types import load_cfn_types

    known = load_cfn_types()
    for profile in load_profiles():
        assert set(profile.resource_types) <= known, profile.id
