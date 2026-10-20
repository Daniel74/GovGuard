"""Cache of LLM verdicts, so only new or changed requirements cost a call (ADR 0011). Pure code."""

from kb_build.extract.models import Requirement
from kb_build.llm_step import LlmCache
from kb_build.llm_step import cache_key as text_key
from kb_build.select.models import Classification


def cache_key(requirement: Requirement, version: str, model_id: str) -> str:
    """Text hash, prompt version and model_id."""
    return text_key(f"{requirement.title}\n{requirement.text}", version, model_id)


class JudgementCache(LlmCache[Classification]):
    answer_type = Classification
