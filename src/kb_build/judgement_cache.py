"""Cache of LLM verdicts, so only new or changed requirements cost a call (ADR 0011)."""

import hashlib
from pathlib import Path

from pydantic import TypeAdapter

from kb_build.extracted_models import Requirement
from kb_build.selection_models import Classification

CACHE_FILE = Path("data/knowledge_base/judgement_cache.json")
_ENTRIES = TypeAdapter(dict[str, Classification])


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_key(requirement: Requirement, instructions: str, model_id: str) -> str:
    """Text hash, prompt version (hash of the full prompt) and model_id."""
    text_hash = _sha(f"{requirement.title}\n{requirement.text}")
    return f"{text_hash}|{_sha(instructions)[:12]}|{model_id}"


class JudgementCache:
    def __init__(self, entries: dict[str, Classification] | None = None) -> None:
        self._entries = entries or {}

    @property
    def size(self) -> int:
        return len(self._entries)

    def get(self, key: str) -> Classification | None:
        return self._entries.get(key)

    def put(self, key: str, answer: Classification) -> None:
        self._entries[key] = answer

    @classmethod
    def load(cls, path: Path = CACHE_FILE) -> "JudgementCache":
        if not path.exists():
            return cls()
        return cls(_ENTRIES.validate_json(path.read_text(encoding="utf-8")))

    def save(self, path: Path = CACHE_FILE) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        entries = dict(sorted(self._entries.items()))  # stable order, readable Git diff
        path.write_bytes(_ENTRIES.dump_json(entries, indent=2) + b"\n")
