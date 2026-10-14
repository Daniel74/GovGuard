"""Entry point wiring: which LLM provider serves `python -m kb_build select`, where the log goes."""

import logging
from collections.abc import Iterator
from pathlib import Path

import pytest
from pydantic_ai.models.bedrock import BedrockConverseModel
from pydantic_ai.models.groq import GroqModel

from kb_build.__main__ import configure_logging, model_for, parse_args


def test_groq_is_the_default_provider() -> None:
    # ADR 0014: public norm texts only; Bedrock stays an explicit option
    assert parse_args([]).provider == "groq"
    assert parse_args(["--provider", "bedrock"]).provider == "bedrock"
    assert parse_args(["--provider", "bedrock-global"]).provider == "bedrock-global"


def test_missing_groq_key_aborts_without_falling_back_to_bedrock(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("GROQ_API_KEY", raising=False)

    def bedrock_must_not_be_called(**_: object) -> None:
        raise AssertionError("silent fallback to Bedrock")

    monkeypatch.setattr("kb_build.__main__.bedrock_model", bedrock_must_not_be_called)

    with pytest.raises(RuntimeError, match="GROQ_API_KEY"):
        model_for(parse_args([]).provider)


def test_bedrock_is_an_explicit_provider() -> None:
    assert isinstance(model_for("bedrock"), BedrockConverseModel)


def test_the_global_bedrock_profile_is_an_explicit_build_opt_in() -> None:
    # ADR 0012: only when `eu.` lacks capacity; the default and the runtime stay on `eu.`
    assert model_for("bedrock").model_name.startswith("eu.")
    assert model_for("bedrock-global").model_name == (
        "global.anthropic.claude-haiku-4-5-20251001-v1:0")


def test_groq_provider_builds_a_groq_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("GROQ_API_KEY", "test")

    assert isinstance(model_for("groq"), GroqModel)


def test_unknown_provider_is_rejected() -> None:
    with pytest.raises(ValueError, match="openai"):
        model_for("openai")


@pytest.fixture
def build_logger() -> Iterator[logging.Logger]:
    """configure_logging() adds a file handler; take it off again after the test."""
    logger = logging.getLogger("kb_build")
    before = list(logger.handlers)
    yield logger
    for handler in [h for h in logger.handlers if h not in before]:
        handler.close()
        logger.removeHandler(handler)


def test_the_build_log_goes_to_a_file_too_without_http_noise(
    tmp_path: Path, build_logger: logging.Logger
) -> None:
    log_file = tmp_path / "logs" / "rules_spec.log"

    configure_logging(log_file)
    build_logger.info("spec DSGVO Art. 16 retry 1: Grund")
    logging.getLogger("httpx").warning("HTTP Request: POST https://api.groq.com")

    text = log_file.read_text("utf-8")
    assert "spec DSGVO Art. 16 retry 1: Grund" in text
    assert "api.groq.com" not in text


def test_each_run_overwrites_the_log_of_the_last_run(
    tmp_path: Path, build_logger: logging.Logger
) -> None:
    log_file = tmp_path / "rules_spec.log"
    log_file.write_text("old run\n", encoding="utf-8")

    configure_logging(log_file)
    build_logger.info("new run")

    assert "old run" not in log_file.read_text("utf-8")
