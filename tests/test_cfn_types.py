"""The list of real CloudFormation resource types (SPEC: no invented types)."""

from kb_build.cfn_types import load_cfn_types


def test_known_types_include_real_ones_and_exclude_invented_ones() -> None:
    known = load_cfn_types()

    assert {"AWS::S3::Bucket", "AWS::IAM::Policy", "AWS::ApiGateway::Method"} <= known
    assert "AWS::S3::BucketPublicAccessBlock" not in known  # invented by the LLM in the first run
