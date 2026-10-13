"""Cache of LLM verdicts, so only new or changed requirements cost a call (ADR 0011). Pure code."""

import hashlib

from pydantic import TypeAdapter

from kb_build.extract.models import Requirement
from kb_build.select.models import Classification

_ENTRIES = TypeAdapter(dict[str, Classification])


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompt_version(*request_parts: str) -> str:
    """Hash of everything the model sees besides the requirement itself."""
    return _sha("\n".join(request_parts))[:12]


def cache_key(requirement: Requirement, version: str, model_id: str) -> str:
    """Text hash, prompt version and model_id."""
    text_hash = _sha(f"{requirement.title}\n{requirement.text}")
    return f"{text_hash}|{version}|{model_id}"


class JudgementCache:
    def __init__(self, entries: dict[str, Classification] | None = None) -> None:
        self._entries = entries or {}

    def get(self, key: str) -> Classification | None:
        return self._entries.get(key)

    def put(self, key: str, answer: Classification) -> None:
        self._entries[key] = answer

    @classmethod
    def from_json(cls, raw: str) -> "JudgementCache":
        return cls(_ENTRIES.validate_json(raw))

    def to_json(self) -> bytes:
        entries = dict(sorted(self._entries.items()))  # stable order, readable Git diff
        return _ENTRIES.dump_json(entries, indent=2) + b"\n"
