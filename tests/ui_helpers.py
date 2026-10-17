"""Shared AppTest helpers of the demo UI tests: create page and gallery (#44)."""

import pytest
from pydantic_ai.messages import ModelMessage, ModelResponse
from pydantic_ai.models.function import AgentInfo, FunctionModel
from streamlit.testing.v1 import AppTest
from test_run_audit_progress import warn_for_every_rule
from test_ui_pages import create_script, gallery_script, page

ARCH = "arch-antragseingang-fehlerhaft"  # 29 FAIL, 28 PASS, 109 N/A, no WARN
SPEC = "spec-meldeportal-gesundheit"  # first in the gallery; numbers in the design of #11


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


def start(app: AppTest, tab: str = "Preset laden") -> AppTest:
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

    monkeypatch.setattr("govguard_ui.create_page.groq_model",
                        lambda: FunctionModel(answer, model_name="fake-groq"))


def arch_page() -> AppTest:
    app = page(gallery_script)
    app.selectbox(key="gallery_preset").select(ARCH).run()
    return app


def spec_page() -> AppTest:
    return page(gallery_script)


def spec_key(suffix: str) -> str:
    return f"gallery_{SPEC}_{suffix}"


def arch_key(suffix: str) -> str:
    """State key of a gallery widget of the ARCH preset, e.g. status -> gallery_<ARCH>_status."""
    return f"gallery_{ARCH}_{suffix}"

