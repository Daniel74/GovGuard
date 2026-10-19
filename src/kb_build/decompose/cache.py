"""Cache of decompositions, like the one of the classification (ADR 0011, #53). Pure code."""

import hashlib

from pydantic import TypeAdapter

from kb_build.decompose.models import Decomposition

_ENTRIES = TypeAdapter(dict[str, Decomposition])


def cache_key(prompt: str, version: str, model_id: str) -> str:
    """Hash of the article as the model sees it (marks included), prompt version and model_id."""
    return f"{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}|{version}|{model_id}"


class DecompositionCache:
    def __init__(self, entries: dict[str, Decomposition] | None = None) -> None:
        self._entries = entries or {}

    def get(self, key: str) -> Decomposition | None:
        return self._entries.get(key)

    def put(self, key: str, answer: Decomposition) -> None:
        self._entries[key] = answer

    @classmethod
    def from_json(cls, raw: str) -> "DecompositionCache":
        return cls(_ENTRIES.validate_json(raw))

    def to_json(self) -> bytes:
        return _ENTRIES.dump_json(dict(sorted(self._entries.items())), indent=2) + b"\n"
