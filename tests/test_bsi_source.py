import pytest

from kb_build.sources.bsi import PRACTICES, extract

COMMIT_SHA = "c96d9f575e369df7e392220003b032d731f0e26d"


def control(cid: str, *, modal: str = "SOLLTE", sec_level: str = "normal-SdT", children=()):
    """Minimal OSCAL control as in the resolved Grundschutz++ catalog."""
    return {
        "id": cid,
        "title": f"Titel {cid}",
        "props": [
            {"name": "sec_level", "value": sec_level},
            {"name": "confidentiality", "value": "2"},
            {"name": "integrity", "value": "2"},
            {"name": "availability", "value": "1"},
        ],
        "parts": [
            {
                "name": "statement",
                "props": [{"name": "modal_verb", "value": modal}],
                "prose": f"Detektion  MUSS   Ereignisse zu {cid} protokollieren.",
            }
        ],
        "controls": list(children),
    }


def extract_by_id(*controls) -> dict:
    catalog = {"catalog": {"groups": [{"id": "G", "groups": [{"id": "G2", "controls": controls}]}]}}
    return {r.id: r for r in extract("memory://bsi", catalog, COMMIT_SHA).requirements}


def test_det_3_1_has_facts_anchor_and_passes_prefilter() -> None:
    det = extract_by_id(control("DET.3.1"))["DET.3.1"]
    assert det.attributes == {
        "practice": "DET", "modal_verb": "SOLLTE", "sec_level": "normal-SdT", "cia_sum": 5,
    }
    assert det.primary_anchor == "BSI GS++ DET.3.1"
    assert det.text == "Detektion MUSS Ereignisse zu DET.3.1 protokollieren."
    assert det.prefilter_passed


def test_nested_controls_are_extracted() -> None:
    nested = control("GC.3.1", children=[control("GC.3.1.1", children=[control("GC.3.1.1.1")])])
    assert list(extract_by_id(nested)) == ["GC.3.1", "GC.3.1.1", "GC.3.1.1.1"]


def test_modal_verb_comes_from_statement_prop_not_prose() -> None:
    det = extract_by_id(control("DET.3.2", modal="KANN"))["DET.3.2"]
    assert det.attributes["modal_verb"] == "KANN"


@pytest.mark.parametrize(
    "rejected",
    [control("DET.3.2", modal="KANN"), control("DET.3.3", sec_level="erhöht"), control("SENS.1.1")],
)
def test_prefilter_rejects_kann_erhoeht_and_foreign_practice(rejected: dict) -> None:
    assert not extract_by_id(rejected)[rejected["id"]].prefilter_passed


def test_practices_are_pinned_to_architecture_1_1() -> None:
    # Changing this set changes the rule, not just the code: update ARCHITECTURE 1.1 first.
    assert PRACTICES == {"DLS", "BER", "DET", "KONF", "BES", "ARCH"}


def test_version_is_catalog_commit_sha() -> None:
    catalog = {"catalog": {"groups": [{"id": "DET", "controls": [control("DET.3.1")]}]}}
    assert extract("memory://bsi", catalog, COMMIT_SHA).version == COMMIT_SHA


def test_duplicate_ids_are_rejected() -> None:
    with pytest.raises(ValueError, match="DET.3.1"):
        extract_by_id(control("DET.3.1"), control("DET.3.1"))
