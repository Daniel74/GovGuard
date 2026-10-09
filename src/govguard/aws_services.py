"""AWS adapter: the only module with boto3 and the Bedrock model (ADR 0005). No audit logic."""

from botocore.client import BaseClient
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.providers.bedrock import BedrockProvider

REGION = "eu-central-1"
# `eu.` profile: inference stays in the EU (ADR 0001); Haiku 4.5 supports forced tool use
MODEL_ID = "eu.anthropic.claude-haiku-4-5-20251001-v1:0"


def bedrock_model(client: BaseClient | None = None) -> BedrockConverseModel:
    """Build the Pydantic AI model; tests inject a stubbed `bedrock-runtime` client."""
    provider = (
        BedrockProvider(bedrock_client=client) if client else BedrockProvider(region_name=REGION)
    )
    return BedrockConverseModel(MODEL_ID, provider=provider)
