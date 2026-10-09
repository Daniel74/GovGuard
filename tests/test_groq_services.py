"""Groq adapter: build-only fallback while Bedrock is unavailable (ADR 0010)."""

import pytest
from pydantic_ai.models.groq import GroqModel

from kb_build.groq_services import DEFAULT_MODEL, groq_model


def test_groq_model_uses_the_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")
    monkeypatch.delenv("GROQ_MODEL", raising=False)

    model = groq_model()

    assert isinstance(model, GroqModel)
    assert model.model_name == DEFAULT_MODEL == "openai/gpt-oss-120b"


def test_groq_model_can_be_switched_by_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")
    monkeypatch.setenv("GROQ_MODEL", "openai/gpt-oss-20b")

    assert groq_model().model_name == "openai/gpt-oss-20b"


def test_missing_api_key_fails_with_a_clear_message(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        groq_model()
