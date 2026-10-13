"""AWS FSBP adapter: Prowler `aws_foundational_security_best_practices_aws.json` (pure, no I/O)."""

from typing import Any

from kb_build.extract import prowler
from kb_build.extract.models import ExtractedSource, Requirement
from kb_build.extract.prowler import ProwlerFormat, strip_markdown

# Prowler `Attributes.Service` in the scope; ECS/ECR/ELB (Fargate) and RDS (Aurora) included.
# EC2 holds the VPC controls (security groups, flow logs); relevance (#6) drops EC2 instances
# and the Classic Load Balancer by resource type (ADR 0011).
SERVICES = frozenset({
    "API Gateway", "Lambda", "DynamoDB", "SQS", "SNS", "S3", "KMS", "Kinesis", "Secrets Manager",
    "EventBridge", "Step Functions", "Cognito", "AppSync", "IAM", "ECS", "ECR", "ELB", "RDS", "EC2",
})


def _attributes(entry: dict[str, Any]) -> dict[str, str]:
    details = entry["Attributes"][0]
    return {"service": details["Service"], "severity": details["Severity"]}


def prefilter(requirement: Requirement) -> str | None:
    """Keeps controls of the services in the scope (ARCHITECTURE 1.1)."""
    if requirement.attributes.get("service") in SERVICES:
        return None
    return "Dienst gehört nicht zum Prüfumfang."


FORMAT = ProwlerFormat(
    source="FSBP",
    anchor=lambda rid, version: f"AWS FSBP {rid}",
    title=lambda entry: strip_markdown(entry["Name"]),
    text=lambda entry: strip_markdown(entry["Description"]),
    attributes=_attributes,
    prefilter=prefilter,
)


def extract(origin: str, data: dict[str, Any], version: str) -> ExtractedSource:
    """All controls; `version` is the Prowler tag from data/input/sources.json."""
    return prowler.extract(FORMAT, origin, data, version)
