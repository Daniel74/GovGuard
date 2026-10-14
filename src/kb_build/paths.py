"""Every data path of the build (#20): data/ is split by origin, not by build step.

input/          maintained by hand
intermediate/   build results, checked in for the review (sources/ stays local, ADR 0008)
                logs/ explains how a result came about: retries, judge, tokens (#29)
knowledge_base/ only rules_*.json: read at runtime, deployed to S3
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from govguard.models import AuditType

_FILE_SUFFIX: dict[AuditType, str] = {"architecture": "arch", "spec": "spec"}
OutputKind = Literal["selection", "verdicts", "rules"]


@dataclass(frozen=True)
class BuildPaths:
    input: Path = Path("data/input")
    intermediate: Path = Path("data/intermediate")
    knowledge_base: Path = Path("data/knowledge_base")

    @property
    def sources_json(self) -> Path:
        return self.input / "sources.json"

    @property
    def scope(self) -> Path:
        return self.input / "scope.json"

    @property
    def archetype_profiles(self) -> Path:
        return self.input / "archetype_profiles.json"

    @property
    def cfn_types(self) -> Path:
        return self.input / "cfn_resource_types.json"  # aws cloudformation list-types, AWS_TYPES

    @property
    def cfn_properties(self) -> Path:
        return self.input / "cfn_properties.json"  # snapshot of describe-type, see README

    @property
    def presets(self) -> Path:
        return self.input / "presets"

    @property
    def source_cache(self) -> Path:
        return self.intermediate / "sources"

    @property
    def extracted(self) -> Path:
        return self.intermediate / "extracted"

    @property
    def judgement_cache(self) -> Path:
        return self.intermediate / "judgement_cache.json"

    def out_file(self, kind: OutputKind, audit_type: AuditType) -> Path:
        """E.g. selection_arch.json, verdicts_spec.json; only rules_*.json is deployed."""
        folder = self.knowledge_base if kind == "rules" else self.intermediate
        return folder / f"{kind}_{_FILE_SUFFIX[audit_type]}.json"

    def build_log(self, command: str, audit_type: AuditType | None) -> Path:
        """E.g. logs/rules_spec.log; each run overwrites it, git keeps the older runs (#29)."""
        suffix = f"_{_FILE_SUFFIX[audit_type]}" if audit_type else ""
        return self.intermediate / "logs" / f"{command}{suffix}.log"
