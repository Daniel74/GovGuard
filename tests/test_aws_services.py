import boto3
from botocore.client import BaseClient
from botocore.stub import Stubber
from pydantic_ai.models.bedrock import BedrockConverseModel

from govguard.audit_engine import run_audit
from govguard.aws_services import bedrock_model
from govguard.models import RuleCatalog, Trace


def test_bedrock_model_uses_eu_profile_in_frankfurt() -> None:
    model = bedrock_model()

    assert isinstance(model, BedrockConverseModel)
    assert model.model_name == "eu.anthropic.claude-haiku-4-5-20251001-v1:0"  # ADR 0001
    assert model.client.meta.region_name == "eu-central-1"


def stubbed_runtime_client(findings: list[dict]) -> tuple[BaseClient, list[dict]]:
    """A bedrock-runtime client that answers with a submit_audit tool call and records requests."""
    client = boto3.client("bedrock-runtime", region_name="eu-central-1")
    requests: list[dict] = []
    client.meta.events.register(
        "provide-client-params.bedrock-runtime.Converse",
        lambda params, **_: requests.append(dict(params)),
    )
    message = {"role": "assistant", "content": [{"toolUse": {
        "toolUseId": "t-1", "name": "submit_audit", "input": {"findings": findings},
    }}]}
    stubber = Stubber(client)
    stubber.add_response("converse", {
        "output": {"message": message},
        "stopReason": "tool_use",
        "usage": {"inputTokens": 1, "outputTokens": 1, "totalTokens": 2},
        "metrics": {"latencyMs": 1},
    })
    stubber.activate()  # without this the request would really go out
    return client, requests


def test_audit_request_forces_the_submit_audit_tool(
    spec_catalog: RuleCatalog, spec_input: str, trace: Trace
) -> None:
    findings = [
        {"rule_id": rule.id, "status": "WARN", "evidence": None,
         "rationale": "Nicht entscheidbar.", "recommendation": "Prüfen."}
        for rule in spec_catalog.rules
    ]
    client, requests = stubbed_runtime_client(findings)

    report = run_audit(spec_catalog, spec_input, bedrock_model(client), trace)

    assert report.overall_status == "WARN"
    # No silent fallback to toolChoice "auto" (ARCHITECTURE 2.1)
    assert requests[0]["toolConfig"]["toolChoice"] == {"any": {}}
