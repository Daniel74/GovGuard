"""Selected finding and "Ganzes Dokument" on "Audits ansehen", via AppTest (#44).

The finding table is an own component (#45): AppTest cannot click it, so these tests set the
selection in the session state, as a click does; tests/visual clicks the rows.
"""

from streamlit.testing.v1 import AppTest
from test_ui_pages import shown_text
from ui_helpers import arch_key, arch_page

SELECTED = arch_key("selected")
S3_PUBLIC_ACCESS = "ARCH-CIS-3.1.4"  # template.json lines 120–125 of 485
FULL_ACCESS_POLICY = "ARCH-BSI-BER.4.1"  # template.json lines 265–268


def select(app: AppTest, rule_id: str) -> None:
    app.session_state[SELECTED] = rule_id
    app.run()


def document(app: AppTest) -> str:
    return next(n.proto.body for n in app.get("html") if "gg-doc" in n.proto.body)


def test_the_detail_shows_the_selected_finding_and_its_evidence_lines() -> None:
    app = arch_page()

    select(app, S3_PUBLIC_ACCESS)

    assert not app.exception
    assert "#### Block Public Access für S3\\-Buckets" in [m.value for m in app.markdown]
    assert "CIS AWS v7.0.0 3.1.4 · ARCH-CIS-3.1.4 · Beleg: Zeilen 120–125" in shown_text(app)
    assert document(app).count("gg-mark") == 6


def test_selecting_another_finding_moves_the_document_to_its_lines() -> None:
    app = arch_page()
    select(app, S3_PUBLIC_ACCESS)

    select(app, FULL_ACCESS_POLICY)

    assert "ARCH-BSI-BER.4.1 · Beleg: Zeilen 265–268" in shown_text(app)
    assert document(app).count("gg-mark") == 4
    assert "▲ Zeilen 1–260 ausgeblendet" in shown_text(app)


def test_the_document_starts_a_few_lines_above_the_evidence() -> None:
    app = arch_page()

    select(app, S3_PUBLIC_ACCESS)

    assert "▲ Zeilen 1–115 ausgeblendet" in shown_text(app)
    assert document(app).count('class="gg-line') == 485 - 115


def test_whole_document_shows_every_line_and_marks_the_evidence_still() -> None:
    app = arch_page()
    select(app, S3_PUBLIC_ACCESS)

    app.toggle(key=arch_key("full")).set_value(True).run()

    assert document(app).count('class="gg-line') == 485
    assert document(app).count("gg-mark") == 6
    assert "ausgeblendet" not in shown_text(app)


def test_switching_whole_document_off_returns_to_the_window() -> None:
    app = arch_page()
    select(app, S3_PUBLIC_ACCESS)
    app.toggle(key=arch_key("full")).set_value(True).run()

    app.toggle(key=arch_key("full")).set_value(False).run()

    assert "▲ Zeilen 1–115 ausgeblendet" in shown_text(app)
