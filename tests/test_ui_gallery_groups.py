"""Architecture audit on "Audits ansehen": findings grouped by source, via AppTest (#43).

Numbers as in the design artefact of #11: BSI ✕10 ✓8 –16, CIS ✕5 ✓3 –12, FSBP ✕12 ✓14 –80,
C5 ✕2 ✓3 –1.
"""

from streamlit.testing.v1 import AppTest
from streamlit.testing.v1.element_tree import Expander
from test_ui_pages import gallery_script, page, shown_text
from ui_helpers import arch_key, arch_page


def groups(app: AppTest) -> list[Expander]:
    return [e for e in app.expander if " Befunde · " in e.label]


def rows(block: Expander) -> int:
    return sum(1 for button in block.button if "_row_" in button.key)


def test_arch_findings_stand_in_one_group_per_source_with_counts() -> None:
    app = arch_page()

    assert [e.label for e in groups(app)] == [
        "**BSI IT-Grundschutz++** · 34 Befunde · :red-badge[✕ 10] :green-badge[✓ 8] "
        ":gray-badge[– 16]",
        "**CIS AWS Foundations v7.0.0** · 20 Befunde · :red-badge[✕ 5] :green-badge[✓ 3] "
        ":gray-badge[– 12]",
        "**AWS Foundational Security Best Practices** · 106 Befunde · :red-badge[✕ 12] "
        ":green-badge[✓ 14] :gray-badge[– 80]",
        "**BSI C5** · 6 Befunde · :red-badge[✕ 2] :green-badge[✓ 3] :gray-badge[– 1]"]
    assert "166 Befunde in 4 Quellen · je Gruppe FAIL zuerst · N/A eingeklappt" in shown_text(app)


def test_na_of_a_group_stands_collapsed_below_its_findings() -> None:
    bsi = groups(arch_page())[0]
    [na] = [e for e in bsi.expander if e.label.endswith("(nicht anwendbar)")]  # self included

    assert na.label == "16 × N/A einblenden (nicht anwendbar)"
    assert not na.proto.expanded
    assert (rows(bsi), rows(na)) == (10 + 8 + 16, 16)  # rows of bsi include the nested ones


def test_the_first_group_and_the_group_of_the_selected_finding_are_open() -> None:
    app = arch_page()
    assert [e.proto.expanded for e in groups(app)] == [True, False, False, False]

    app.session_state[arch_key("selected")] = "ARCH-CIS-3.1.4"
    app.run()

    assert [e.proto.expanded for e in groups(app)] == [True, True, False, False]


def test_the_arch_audit_has_groups_instead_of_status_and_source_filter() -> None:
    app = arch_page()

    assert not app.pills
    assert not app.segmented_control


def test_gaps_of_an_arch_audit_stand_below_the_groups() -> None:
    app = page(gallery_script)
    app.selectbox(key="gallery_preset").select("arch-fristenwecker").run()

    assert any(e.label == "Was die Eingabe nicht beschreibt · 3 Lücken" for e in app.expander)
