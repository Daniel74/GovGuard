"""The scope (ADR 0011): which AWS resource types the architecture audit keeps rules for."""

import json

import pytest

from kb_build.paths import BuildPaths
from kb_build.reference.archetype_profiles import load_profiles
from kb_build.reference.cfn_types import load_cfn_types
from kb_build.reference.run import read_scope
from kb_build.reference.scope import Scope


@pytest.fixture(scope="module")
def scope() -> Scope:
    return read_scope(BuildPaths().scope)


def test_scope_names_services_with_their_cloudformation_types(scope: Scope) -> None:
    assert "AWS::Lambda::Function" in scope.services["Lambda"]
    assert "AWS::DynamoDB::Table" in scope.services["DynamoDB"]


def test_types_collects_the_types_of_all_services() -> None:
    scope = Scope({"S3": ["AWS::S3::Bucket"], "KMS": ["AWS::KMS::Key", "AWS::KMS::Alias"]})

    assert scope.types == {"AWS::S3::Bucket", "AWS::KMS::Key", "AWS::KMS::Alias"}


def test_scope_names_the_types_it_lacks_once_in_their_order() -> None:
    # One check for stage ②, formulate_rule and check_rules (#19)
    scope = Scope({"S3": ["AWS::S3::Bucket"]})
    named = ["AWS::CloudTrail::Trail", "AWS::S3::Bucket", "AWS::WAF::WebACL",
             "AWS::CloudTrail::Trail"]

    assert scope.outside(named) == ["AWS::CloudTrail::Trail", "AWS::WAF::WebACL"]


def test_scope_contains_only_real_cloudformation_types(scope: Scope) -> None:
    assert scope.types <= load_cfn_types()


def test_scope_includes_what_rds_and_fargate_need(scope: Scope) -> None:
    assert {"AWS::RDS::DBCluster", "AWS::ECS::Service", "AWS::ECR::Repository",
            "AWS::EC2::VPC", "AWS::EC2::SecurityGroup",
            "AWS::ElasticLoadBalancingV2::LoadBalancer"} <= scope.types


def test_scope_excludes_ec2_instances_eks_cloudtrail_cloudfront_and_classic_lb(
    scope: Scope,
) -> None:
    assert not {"AWS::EC2::Instance", "AWS::EKS::Cluster", "AWS::CloudTrail::Trail",
                "AWS::CloudFront::Distribution",
                "AWS::ElasticLoadBalancing::LoadBalancer"} & scope.types


def test_scope_covers_every_resource_type_of_the_archetypes(scope: Scope) -> None:
    archetype_types = {t for p in load_profiles() for t in p.resource_types}

    assert archetype_types <= scope.types


def test_scope_includes_the_companion_types_of_backup_and_auto_scaling(scope: Scope) -> None:
    # Rules like FSBP DynamoDB.4 and RDS.26 name them (#19)
    assert {"AWS::Backup::BackupVault", "AWS::Backup::BackupPlan", "AWS::Backup::BackupSelection",
            "AWS::ApplicationAutoScaling::ScalableTarget",
            "AWS::ApplicationAutoScaling::ScalingPolicy"} <= scope.types


def test_scope_leaves_out_efs_ebs_volumes_and_ssm_parameters(scope: Scope) -> None:
    assert not {"AWS::EFS::FileSystem", "AWS::EC2::Volume", "AWS::SSM::Parameter"} & scope.types


def test_snapshot_has_the_properties_of_every_scope_type(scope: Scope) -> None:
    # The gate of #17 judges only types in the snapshot: scope.json and snapshot move together
    snapshot = json.loads(BuildPaths().cfn_properties.read_text(encoding="utf-8"))

    assert scope.types == snapshot.keys()
