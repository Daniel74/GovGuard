"""Entry point wiring: which LLM provider serves `python -m kb_build select`."""

import pytest
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.groq import GroqModel

from kb_build.__main__ import model_for


def test_bedrock_is_the_default_provider() -> None:
    assert isinstance(model_for("bedrock"), BedrockConverseModel)


def test_the_global_bedrock_profile_is_an_explicit_build_opt_in() -> None:
    # ADR 0012: only when `eu.` lacks capacity; the default and the runtime stay on `eu.`
    assert model_for("bedrock").model_name.startswith("eu.")
    assert model_for("bedrock-global").model_name == (
        "global.anthropic.claude-haiku-4-5-20251001-v1:0")


def test_groq_is_an_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")

    assert isinstance(model_for("groq"), GroqModel)


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="openai"):
        model_for("openai")
