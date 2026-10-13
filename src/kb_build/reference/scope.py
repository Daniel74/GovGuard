"""The scope (ADR 0011): hand-maintained AWS services of the architecture audit. Pure code."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    services: dict[str, list[str]]  # service name -> CloudFormation resource types (scope.json)

    @property
    def types(self) -> frozenset[str]:
        return frozenset(t for types in self.services.values() for t in types)

    def outside(self, types: Iterable[str]) -> list[str]:
        """The given types the scope lacks, each once, in their order (#19)."""
        inside = self.types
        return [t for t in dict.fromkeys(types) if t not in inside]
