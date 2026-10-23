"""Interaction inventory of the demo UI: control -> the test that uses it (ADR 0024, #44).

Key: <widget>:<key as written in src/govguard_ui>, an f-string part shows as {}, no key as -.
Value: <file>::<test>. Each control is tested on the cheapest level that sees it: AppTest for
Streamlit widgets, Playwright (tests/visual) for what only the browser shows. The guard is
tests/test_ui_inventory.py; a new control needs its entry here and its test.
"""

INVENTORY: dict[str, str] = {
    # Sidebar: one link per page
    "page_link:-": "tests/visual/test_browser.py::test_the_sidebar_links_open_all_three_pages",
    # Audits ansehen: filters, finding list, document, download
    "selectbox:gallery_preset": "tests/test_ui_pages.py::"
                                "test_gallery_shows_the_deviation_of_the_arch_preset",
    "pills:{}_status": "tests/test_ui_gallery_filters.py::"
                       "test_switching_a_status_on_or_off_changes_the_list_and_its_count",
    "segmented_control:{}_source": "tests/test_ui_gallery_filters.py::"
                                   "test_the_source_filter_keeps_only_findings_of_that_source",
    "finding_table:{}": "tests/visual/test_browser_findings.py::"
                        "test_a_click_on_a_row_selects_the_finding_and_marks_only_this_row",
    "button:{}_required_{}": "tests/test_ui_report_header.py::"
                             "test_a_click_on_a_required_finding_shows_it_in_the_detail",
    "expander:{}_gaps": "tests/visual/test_browser_findings.py::"
                        "test_the_gap_list_stays_open_when_the_source_changes_and_scrolls",
    "popover:{}": "tests/test_ui_conditions.py::"
                  "test_the_popover_closes_when_the_jump_button_is_clicked",
    "button:{}_condition_go_{}_{}": "tests/test_ui_conditions.py::"
                                    "test_the_jump_button_marks_the_evidence_lines_in_the_document",
    "button:{}_condition_close": "tests/test_ui_conditions.py::"
                                "test_back_to_the_finding_shows_the_finding_again",
    "expander:{}_gaps_common": "tests/test_ui_gaps.py::"
                               "test_common_gaps_come_first_then_one_expander_per_open_condition",
    "expander:{}_gaps_{}": "tests/test_ui_gaps.py::"
                           "test_every_gap_stands_exactly_once_in_the_sections",
    "toggle:{}_full": "tests/test_ui_gallery_selection.py::"
                      "test_whole_document_shows_every_line_and_marks_the_evidence_still",
    "download_button:{}_download": "tests/test_ui_report_header.py::"
                                   "test_the_json_download_keeps_the_trace",
    # Audit erstellen: audit type, input, model, start, new audit
    "radio:audit_type": "tests/test_ui_create_input.py::"
                        "test_the_audit_type_decides_which_presets_can_be_chosen",
    "tabs:input_mode": "tests/test_ui_create_input.py::test_the_text_tab_hides_the_preset_choice",
    "selectbox:create_preset_{}": "tests/test_ui_create_input.py::"
                                  "test_another_preset_changes_file_format_size_and_expected_status",
    "text_area:text": "tests/test_ui_create_input.py::"
                      "test_an_audit_of_pasted_text_checks_exactly_this_text",
    "radio:model": "tests/test_ui_create_page.py::"
                   "test_create_page_shows_the_input_limit_and_the_model",
    "radio:model_bedrock": "tests/test_ui_create_page.py::"
                           "test_bedrock_is_shown_as_a_model_that_is_not_available_in_the_ui",
    "text_input:password": "tests/test_ui_create_page.py::"
                           "test_create_page_without_the_password_starts_no_audit",
    "button:start": "tests/test_ui_create_page.py::"
                    "test_with_the_password_the_audit_runs_and_stays_only_in_the_session",
    "button:new_audit": "tests/test_ui_create_session.py::"
                        "test_new_audit_clears_the_result_and_shows_the_form_again",
    "guard:navigation_guard": "tests/visual/test_browser_guard.py::"
                              "test_stay_keeps_the_audit_running_and_afterwards_links_switch_freely",
}
