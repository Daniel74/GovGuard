"""The way of every LLM step of the build: from the cache, or ask the model (ADR 0027).

Select and decompose share the cache and "from the cache or ask"; rules share only `paid_call`,
`GateCounts` and `usage_line`. The prompts stay with their step. Pure code.
"""

import hashlib
import logging
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from typing import ClassVar, Self

from pydantic import BaseModel, TypeAdapter
from pydantic_ai.usage import RunUsage

from govguard.models import AuditType
from kb_build.build_log import INVALID_ANSWER, logged_retries, raise_if_no_answer

logger = logging.getLogger("kb_build")


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_version(*request_parts: str) -> str:
    """Hash of everything the model sees besides the text it judges."""
    return _sha("\n".join(request_parts))[:12]


def cache_key(text: str, version: str, model_id: str) -> str:
    """Text hash, prompt version and model_id."""
    return f"{_sha(text)}|{version}|{model_id}"


class LlmCache[T: BaseModel]:
    """Answers of the model, so only new or changed input costs a call (ADR 0011).

    A subclass names the answer type: `class JudgementCache(LlmCache[Classification])`.
    """

    answer_type: ClassVar[type[BaseModel]]

    def __init__(self, entries: dict[str, T] | None = None) -> None:
        self._entries = entries or {}

    @classmethod
    def _adapter(cls) -> TypeAdapter[dict[str, T]]:
        return TypeAdapter(dict[str, cls.answer_type])

    def get(self, key: str) -> T | None:
        return self._entries.get(key)

    def put(self, key: str, answer: T) -> None:
        self._entries[key] = answer

    @classmethod
    def from_json(cls, raw: str) -> Self:
        return cls(cls._adapter().validate_json(raw))

    def to_json(self) -> bytes:
        entries = dict(sorted(self._entries.items()))  # stable order, readable Git diff
        return self._adapter().dump_json(entries, indent=2) + b"\n"


@dataclass
class GateCounts:
    """What a build gate did with the model's answers: the quality report counts it (#27)."""

    retries: int = 0  # answers the model had to redo
    llm_errors: int = 0  # answers that stayed invalid (outcome `llm_error`)

    def __add__(self, other: "GateCounts") -> "GateCounts":
        return GateCounts(self.retries + other.retries, self.llm_errors + other.llm_errors)

    def line(self, audit_type: AuditType, gate: str) -> str:
        return f"{audit_type} quality {gate}: retries={self.retries} llm_error={self.llm_errors}"


def usage_line(audit_type: AuditType, usage: RunUsage) -> str:
    """What a build step paid for one audit type, failed retries included."""
    return (f"{audit_type}: {usage.requests} requests, {usage.input_tokens} input tokens, "
            f"{usage.output_tokens} output tokens")


@contextmanager
def paid_call(total: RunUsage) -> Iterator[RunUsage]:
    """One usage per call: Pydantic AI checks its request limit against it.

    The tokens of a failed call count too, so they reach `total` either way.
    """
    usage = RunUsage()
    try:
        yield usage
    finally:
        total.incr(usage)


class LlmStep[T: BaseModel]:
    """Cache, tokens and counts of one step; the step brings its prompt and its call."""

    def __init__(self, cache: LlmCache[T]) -> None:
        self.cache = cache
        self.usage = RunUsage()  # tokens of the calls the cache could not answer
        self.counts = GateCounts()  # retries and llm_error of those calls (#27)

    def cached_or_ask(self, key: str, ask: Callable[[], T | None]) -> T | None:
        """A known answer comes from the cache; a new valid one goes in, `None` never does."""
        known = self.cache.get(key)
        if known is None:
            known = ask()
            if known is not None:
                self.cache.put(key, known)
        return known

    def ask(
        self, label: str, run: Callable[[RunUsage], T], warning: str, *warning_args: object
    ) -> T | None:
        """An answer that stays invalid gives `None` (outcome `llm_error`) and a warning.

        401, 429 and server errors are no answer at all: they abort the build (ADR 0026).
        `warning` takes `warning_args` and the error as its last argument.
        """
        with paid_call(self.usage) as usage:
            try:
                with logged_retries(label):  # (#30)
                    return run(usage)
            except INVALID_ANSWER as error:
                raise_if_no_answer(error)
                logger.warning(warning, *warning_args, error)
                self.counts.llm_errors += 1
                return None
            finally:
                self.counts.retries += max(usage.requests - 1, 0)  # every request after the first
