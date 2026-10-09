"""Entry point wiring: which LLM provider serves `python -m kb_build select`."""

import pytest
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.groq import GroqModel

from kb_build.__main__ import model_for


def test_bedrock_is_the_default_provider() -> None:
    assert isinstance(model_for("bedrock"), BedrockConverseModel)


def test_groq_is_an_explicit_opt_in(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")

    assert isinstance(model_for("groq"), GroqModel)


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="openai"):
        model_for("openai")
