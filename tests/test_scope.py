"""The Prüfumfang (ADR 0011): which AWS resource types the architecture audit keeps rules for."""

from kb_build.archetype_profiles import load_profiles
from kb_build.cfn_types import load_cfn_types
from kb_build.scope import load_scope, scope_types


def test_scope_names_services_with_their_cloudformation_types() -> None:
    scope = load_scope()

    assert "AWS::Lambda::Function" in scope["Lambda"]
    assert "AWS::DynamoDB::Table" in scope["DynamoDB"]


def test_scope_contains_only_real_cloudformation_types() -> None:
    assert scope_types() <= load_cfn_types()


def test_scope_includes_what_rds_and_fargate_need() -> None:
    types = scope_types()

    assert {"AWS::RDS::DBCluster", "AWS::ECS::Service", "AWS::ECR::Repository",
            "AWS::EC2::VPC", "AWS::EC2::SecurityGroup",
            "AWS::ElasticLoadBalancingV2::LoadBalancer"} <= types


def test_scope_excludes_ec2_instances_eks_cloudtrail_cloudfront_and_classic_lb() -> None:
    types = scope_types()

    assert not {"AWS::EC2::Instance", "AWS::EKS::Cluster", "AWS::CloudTrail::Trail",
                "AWS::CloudFront::Distribution", "AWS::ElasticLoadBalancing::LoadBalancer"} & types


def test_scope_covers_every_resource_type_of_the_archetypes() -> None:
    archetype_types = {t for p in load_profiles() for t in p.resource_types}

    assert archetype_types <= scope_types()
