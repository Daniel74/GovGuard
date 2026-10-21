"""BSI Grundschutz++ adapter: resolved OSCAL catalog -> ExtractedSource (pure, no I/O)."""

import re
from collections.abc import Iterator
from typing import Any

from govguard.text import normalize
from kb_build.extract.models import ExtractedSource, Requirement, mark_prefilter

PRACTICES = frozenset({"DLS", "BER", "DET", "KONF", "BES", "ARCH"})
MODAL_VERBS = frozenset({"MUSS", "SOLLTE"})  # ADR 0007, KANN stays out
CIA = ("confidentiality", "integrity", "availability")
_PLACEHOLDER = re.compile(r"\{\{ insert: param, ([^ }]+) \}\}")


def _controls(node: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """All controls depth-first; sub-controls such as GC.3.1.1 are requirements too."""
    for control in node.get("controls") or []:
        yield control
        yield from _controls(control)
    for group in node.get("groups") or []:
        yield from _controls(group)


def _props(node: dict[str, Any]) -> dict[str, str]:
    return {p["name"]: p["value"] for p in node.get("props") or []}


def _statement(control: dict[str, Any]) -> dict[str, Any]:
    for part in control.get("parts") or []:
        if part.get("name") == "statement":
            return part
    raise ValueError(f"BSI control without statement: {control['id']}")


def _prose(control: dict[str, Any], statement: dict[str, Any]) -> str:
    """Replaces OSCAL placeholders by the parameter label, e.g. "regelmäßig" (gate: quote)."""
    labels = {p["id"]: p["label"] for p in control.get("params") or []}
    return _PLACEHOLDER.sub(lambda m: labels[m.group(1)], statement.get("prose", ""))


def _attributes(control: dict[str, Any], statement: dict[str, Any]) -> dict[str, str | int]:
    props = _props(control)
    facts = {
        "practice": control["id"].split(".", 1)[0],
        "modal_verb": _props(statement).get("modal_verb"),
        "sec_level": props.get("sec_level"),
        "cia_sum": sum(int(props.get(key, 0)) for key in CIA),
    }
    return {key: value for key, value in facts.items() if value is not None}


def _requirement(control: dict[str, Any]) -> Requirement:
    statement = _statement(control)
    return Requirement(
        id=control["id"],
        title=control["title"],
        text=normalize(_prose(control, statement)),
        primary_anchor=f"BSI GS++ {control['id']}",
        attributes=_attributes(control, statement),
        prefilter_passed=False,
    )


def prefilter(requirement: Requirement) -> str | None:
    """Keeps MUSS/SOLLTE at normal-SdT in architecture practices."""
    facts = requirement.attributes
    if facts.get("modal_verb") not in MODAL_VERBS:
        return "Modalverb ist weder MUSS noch SOLLTE."
    if facts.get("sec_level") != "normal-SdT":
        return "Sicherheitsniveau ist nicht normal-SdT."
    if facts.get("practice") not in PRACTICES:
        return f"Praktik gehört nicht zu {', '.join(sorted(PRACTICES))}."
    return None


def extract(origin: str, catalog: dict[str, Any], version: str) -> ExtractedSource:
    """All requirements of the catalog; `version` is the catalog commit SHA."""
    requirements = [_requirement(c) for c in _controls(catalog["catalog"])]
    return ExtractedSource(
        source="BSI", version=version, origin=origin,
        requirements=mark_prefilter(requirements, prefilter),
    )
