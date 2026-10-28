"""Shared AppTest helpers of the demo UI tests: pages, create page and gallery (#11, #44)."""

import json
import re

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel
from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import Block
from test_run_audit_progress import warn_for_every_rule

from govguard.audit_setup import CATALOGS, conditions_for
from govguard.checks.conditions import condition_results, na_drafts
from govguard.condition_models import ConditionDraft, LineRange
from govguard.models import RuleCatalog
from govguard_ui.gallery import GalleryEntry, load_gallery
from govguard_ui.paths import GALLERY, PRESETS
from govguard_ui.report.findings_view import BY_RULE

ARCH = "arch-antragseingang-fehlerhaft"  # 29 FAIL, 28 PASS, 109 N/A, no WARN
SPEC = "spec-meldeportal-gesundheit"  # first in the gallery; numbers in the design of #11
DATA_WARNING = "Keine personenbezogenen oder vertraulichen Daten eingeben."


def start_script() -> None:
    from govguard_ui.screens.start_page import render
    render()


def gallery_script() -> None:
    from govguard_ui.screens.gallery_page import render
    render()


def create_script() -> None:
    from govguard_ui.screens.create_page import render
    render()


def page(script, **secrets: str) -> AppTest:
    app = AppTest.from_function(script, default_timeout=30)
    for name, value in secrets.items():
        app.secrets[name] = value
    return app.run()


def shown_text(app: AppTest) -> str:
    """Headings, markdown, captions, alerts and raw HTML of the page in one string."""
    parts = [*app.title, *app.header, *app.subheader, *app.markdown, *app.caption,
             *app.warning, *app.error, *app.info, *app.success]
    html = [node.proto.body for node in app.get("html")]
    text = "\n".join([str(part.value) for part in parts] + html)
    text = re.sub(r"\\(.)", r"\1", text)  # escaped LLM text reads without backslashes
    return text.replace("**", "").replace("  \n", " ")  # as read, without markdown


def frames(app: AppTest) -> list[str]:
    """Text and widget labels of every bordered container, one string per container."""
    def text(node) -> str:
        return getattr(node.proto, "label", "") or getattr(node.proto, "body", "")

    bordered = [node for node in app.main if node.type == "flex_container"
                and node.proto.flex_container.border]
    return ["\n".join(text(n) for n in frame if n is not frame) for frame in bordered]


def list_items(app: AppTest, start: str) -> list[str]:
    """One sentence per list item: the spacing of the steps on the start page (#51)."""
    text = next(m.value for m in app.markdown if m.value.startswith(f"- {start}"))
    items = text.split("\n")
    assert all(item.startswith("- ") and item.endswith(".") for item in items)
    return items


def create_page() -> AppTest:
    return page(create_script, APP_PASSWORD="geheim", AUDIT_BACKEND="local")


def open_text_tab(app: AppTest) -> AppTest:
    """Opens the second tab; AppTest forgets the open tab on a rerun, so every run sets it."""
    app.session_state["input_mode"] = "Text einfügen"
    return app.run()


def typed_text(text: str) -> AppTest:
    """Create page with the text tab open and the text typed in."""
    app = open_text_tab(create_page())
    app.text_area(key="text").input(text)
    return open_text_tab(app)


def preset_boxes(app: AppTest) -> list[str]:
    return [s.key for s in app.selectbox if s.key.startswith("create_preset_")]


def start(app: AppTest, tab: str = "Musterfall laden") -> AppTest:
    """Types the password and starts; the open tab is set again for this rerun too."""
    app.text_input(key="password").input("geheim")
    app.button(key="start").click()
    app.session_state["input_mode"] = tab
    return app.run()


def fake_groq(monkeypatch: pytest.MonkeyPatch, seen: list[str]) -> None:
    """Groq replaced by a FunctionModel that notes what the audit sent to the model."""
    def answer(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        seen.append(str(messages[0]))
        return warn_for_every_rule(messages, info)

    monkeypatch.setattr("govguard_ui.screens.create_page.groq_model",
                        lambda: FunctionModel(answer, model_name="fake-groq"))


def in_view(app: AppTest, key: str, view: str | None) -> AppTest:
    """"nach Fundstelle" is the default; most tests read the table, so they ask for BY_RULE."""
    return app.segmented_control(key=key).set_value(view).run() if view else app


def arch_page(view: str | None = BY_RULE) -> AppTest:
    app = page(gallery_script)
    app.selectbox(key="gallery_preset").select(ARCH).run()
    return in_view(app, f"gallery_{ARCH}_view", view)


def spec_page(view: str | None = BY_RULE) -> AppTest:
    return in_view(page(gallery_script), f"gallery_{SPEC}_view", view)


def finding_tables(block: AppTest | Block) -> list[dict]:
    """Data of every finding table inside the block; AppTest sees it, but cannot click (#45)."""
    return [json.loads(node.proto.json) for node in block.get("bidi_component")]


def table_rows(block: AppTest | Block) -> list[str]:
    """Rule ids of all rows in the finding tables of the block, nested ones included."""
    return [row["id"] for table in finding_tables(block) for row in table["rows"]]


def gallery_entry(preset_id: str) -> GalleryEntry:
    return next(e for e in load_gallery(PRESETS, GALLERY) if e.preset_id == preset_id)


def spec_key(suffix: str) -> str:
    return f"gallery_{SPEC}_{suffix}"


def arch_key(suffix: str) -> str:
    """State key of a gallery widget of the ARCH preset, e.g. status -> gallery_<ARCH>_status."""
    return f"gallery_{ARCH}_{suffix}"



def report_script(entry_json: str) -> None:
    """Renders one gallery entry with a changed report, e.g. poisoned LLM text."""
    from govguard_ui.gallery import GalleryEntry
    from govguard_ui.report.report_view import render_report

    entry = GalleryEntry.model_validate_json(entry_json)
    render_report(entry.report, entry.preset.title, (entry.source_name, entry.source_text),
                  None, key="report")


def report_page(entry: GalleryEntry, view: str | None = BY_RULE) -> AppTest:
    app = AppTest.from_function(report_script, args=(entry.model_dump_json(),),
                                default_timeout=30).run()
    return in_view(app, "report_view", view)


def lines(start: int, end: int | None = None) -> list[LineRange]:
    return [LineRange(line_start=start, line_end=end or start)]


# What the pre-run found in the portal example (lines of its input.md): a contradiction for the
# processor, a denial of an AI system (which also denies high-risk), a denied consent.
DRAFTS = [
    ConditionDraft(condition_id="ki_system", affirming=[], denying=lines(10)),
    ConditionDraft(condition_id="third_country", affirming=lines(53, 55), denying=[]),
    ConditionDraft(condition_id="processor", affirming=lines(53, 55), denying=lines(20)),
    ConditionDraft(condition_id="consent", affirming=[], denying=lines(47)),
]


def with_conditions(entry: GalleryEntry) -> GalleryEntry:
    """The stored report as if the pre-run had found DRAFTS: the code decides the values and
    makes the denied rules N/A, exactly as the audit does (checks/conditions)."""
    defs = conditions_for("spec")
    results = condition_results(defs, DRAFTS)
    catalog = RuleCatalog.model_validate_json(CATALOGS["spec"].read_text(encoding="utf-8"))
    na = {d.rule_id: d for d in na_drafts(defs, results, catalog.rules)}

    def apply(finding):
        if (draft := na.get(finding.rule_id)) is None:
            return finding
        return finding.model_copy(update={
            "status": "N/A", "line_start": draft.line_start, "line_end": draft.line_end,
            "rationale": draft.rationale, "recommendation": None, "downgraded_from": None,
            "corrections": []})

    report = entry.report.model_copy(update={
        "findings": [apply(f) for f in entry.report.findings], "conditions": results})
    return entry.model_copy(update={"report": report})


def without_conditions(entry: GalleryEntry) -> GalleryEntry:
    """A report as stored before the pre-run (#60): no conditions."""
    return entry.model_copy(update={
        "report": entry.report.model_copy(update={"conditions": {}})})


def conditions_page(view: str | None = BY_RULE) -> AppTest:
    return report_page(with_conditions(gallery_entry(SPEC)), view)
