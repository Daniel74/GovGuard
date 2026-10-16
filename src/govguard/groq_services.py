"""Groq adapter: default LLM at runtime (ADR 0023) and in the build (ADR 0014).

At runtime user input goes to the USA: fictitious data only; real data need `eu.` (ADR 0001).
"""

import os

from groq import AsyncGroq
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

DEFAULT_MODEL = "openai/gpt-oss-120b"  # production model on Groq with tool use, cheap
MAX_RETRIES = 6  # the Groq SDK backs off on HTTP 429 (rate limit) before giving up


class MissingApiKeyError(RuntimeError):
    """No silent switch to Bedrock (ADR 0016): without a key the audit does not start."""


def groq_model() -> GroqModel:
    """Build the Pydantic AI model; the model name can be switched with GROQ_MODEL."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise MissingApiKeyError("GROQ_API_KEY fehlt: im Terminal mit export setzen, nie "
                                 "committen. Für echte Daten: --provider bedrock.")
    provider = GroqProvider(groq_client=AsyncGroq(api_key=api_key, max_retries=MAX_RETRIES))
    return GroqModel(os.getenv("GROQ_MODEL", DEFAULT_MODEL), provider=provider)
