import pytest

from kb_build.sources.fsbp import SERVICES, extract

VERSION = "5.44.0"
REASON = "Dienst gehört nicht zum Prüfumfang."


def control(rid: str, service: str) -> dict:
    """Minimal entry as in Prowler `aws_foundational_security_best_practices_aws.json`."""
    return {
        "Id": rid,
        "Name": f"Name  of **{rid}**",
        "Description": f"This control checks  {rid}.",
        "Attributes": [{"ItemId": rid, "Severity": "medium", "Service": service}],
    }


def extract_by_id(*controls: dict) -> dict:
    fsbp = {"Framework": "AWS-Foundational-Security-Best-Practices", "Requirements": list(controls)}
    return {r.id: r for r in extract("memory://fsbp", fsbp, VERSION).requirements}


def test_sns_1_has_facts_anchor_and_clean_text() -> None:
    sns = extract_by_id(control("SNS.1", "SNS"))["SNS.1"]
    assert sns.attributes == {"service": "SNS", "severity": "medium"}
    assert sns.primary_anchor == "AWS FSBP SNS.1"
    assert sns.title == "Name of SNS.1"
    assert sns.text == "This control checks SNS.1."


def test_source_is_fsbp_and_version_comes_from_sources_json() -> None:
    extracted = extract("memory://fsbp", {"Requirements": [control("SNS.1", "SNS")]}, VERSION)
    assert (extracted.source, extracted.version) == ("FSBP", VERSION)


@pytest.mark.parametrize(
    "service", ["Lambda", "API Gateway", "DynamoDB", "SQS", "ECS", "ECR", "ELB", "RDS", "EC2"]
)
def test_prefilter_keeps_services_in_scope_including_fargate_and_aurora(service: str) -> None:
    kept = extract_by_id(control("X.1", service))["X.1"]
    assert kept.prefilter_passed
    assert kept.prefilter_reason is None


@pytest.mark.parametrize("service", ["CloudFront", "EKS", "Redshift", "CloudTrail"])
def test_prefilter_rejects_services_outside_the_scope_with_a_reason(service: str) -> None:
    rejected = extract_by_id(control("X.1", service))["X.1"]
    assert not rejected.prefilter_passed
    assert rejected.prefilter_reason == REASON


def test_services_are_pinned_to_architecture_1_1() -> None:
    # Changing this set changes the rule, not just the code: update ARCHITECTURE 1.1 first.
    # EC2 holds the VPC controls, ELB also ALB/NLB; relevance (#6) drops instances and Classic LB.
    assert {"ECS", "ECR", "ELB", "RDS", "EC2"} <= SERVICES
    assert not {"EKS", "CloudTrail", "CloudFront"} & SERVICES


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="SNS.1"):
        extract_by_id(control("SNS.1", "SNS"), control("SNS.1", "SNS"))
