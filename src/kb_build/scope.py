"""The scope (ADR 0011): hand-maintained AWS services of the architecture audit. Pure code."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scope:
    services: dict[str, list[str]]  # service name -> CloudFormation resource types (scope.json)

    @property
    def types(self) -> frozenset[str]:
        return frozenset(t for types in self.services.values() for t in types)
