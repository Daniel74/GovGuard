"""Groq adapter: temporary build-only fallback while Bedrock is unavailable (ADR 0010).

Never used at runtime (Lambda); only public norm texts are sent. Delete with ADR 0010.
"""

import os

from groq import AsyncGroq
from pydantic_ai.models.groq import GroqModel
from pydantic_ai.providers.groq import GroqProvider

DEFAULT_MODEL = "openai/gpt-oss-120b"  # production model on Groq with tool use, cheap
MAX_RETRIES = 6  # the Groq SDK backs off on HTTP 429 (rate limit) before giving up


def groq_model() -> GroqModel:
    """Build the Pydantic AI model; the model name can be switched with GROQ_MODEL."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set (export it in your shell, never commit it)")
    provider = GroqProvider(groq_client=AsyncGroq(api_key=api_key, max_retries=MAX_RETRIES))
    return GroqModel(os.getenv("GROQ_MODEL", DEFAULT_MODEL), provider=provider)
