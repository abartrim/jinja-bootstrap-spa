# Macro API Reference

This file is generated from the canonical macro source in
`src/jinja_bootstrap_spa/macros/bootstrap.py`.

Regenerate it with:

```bash
.venv/bin/python scripts/generate_macro_reference.py
```

| Macro | Signature |
| --- | --- |
| `button` | `button(label, href=None, variant="primary", size=None, button_type="button", outline=False, disabled=False, class_name="", id=None, jbs_action=None, jbs_component_ref=None, jbs_patch=None, jbs_page=None, jbs_sort_key=None, jbs_sort_direction=None, jbs_row_id=None, jbs_intent=None, attrs="")` |
| `action_menu` | `action_menu(menu_id, label="Actions", items=None, variant="outline-secondary", size="sm", align="end", button_class="", menu_class="", class_name="", attrs="")` |
| `tabs` | `tabs(group_id, items, active=None, variant="pills", class_name="", attrs="")` |
| `segmented_control` | `segmented_control(group_id, items, active=None, class_name="", attrs="")` |
| `page_header` | `page_header(title=None, subtitle=None, icon=None, eyebrow=None, title_html=None, meta_html=None, actions_html=None, breadcrumbs=None, class_name="", attrs="")` |
| `toolbar` | `toolbar(toolbar_id=None, title=None, subtitle=None, body="", badges=None, actions_html=None, collapsible=False, expanded=True, class_name="", attrs="")` |
| `card` | `card(title=None, body="", footer=None, class_name="", id=None, attrs="")` |
| `stat_card` | `stat_card(title, value, subtitle=None, icon=None, tone="primary", href=None, trend=None, class_name="", attrs="")` |
| `empty_state` | `empty_state(title, message, icon=None, action_html=None, compact=False, class_name="", attrs="")` |
| `detail_list` | `detail_list(items, columns=1, striped=False, compact=False, class_name="", attrs="")` |
| `key_value_panel` | `key_value_panel(items, columns=1, striped=False, compact=False, class_name="", attrs="")` |
| `callout` | `callout(title=None, message="", message_html=None, tone="info", icon=None, dismissible=False, class_name="", attrs="")` |
| `chart_shell` | `chart_shell(chart_id, title=None, subtitle=None, badges=None, actions_html=None, footer_html=None, empty_html=None, error_html=None, class_name="", attrs="")` |
| `split_panel` | `split_panel(direction="horizontal", ratio="1/1", collapse_on_mobile=True, class_name="", attrs="")` |
| `modal` | `modal(overlay_id, title=None, body="", footer=None, size="lg", close_label="Close", class_name="", attrs="")` |
| `drawer` | `drawer(overlay_id, title=None, body="", footer=None, placement="end", width="420px", close_label="Close", class_name="", attrs="")` |
| `workspace_modal` | `workspace_modal(overlay_id, title=None, body="", footer_html=None, size="xl", sticky_header=True, sticky_footer=True, close_label="Close", class_name="", attrs="")` |
| `status_region` | `status_region(region_id=None, title=None, message="", variant="info", dismissible=True, class_name="", attrs="")` |
| `toast` | `toast(toast_id=None, title=None, message="", variant="info", dismissible=True, class_name="", attrs="")` |
| `stream_status` | `stream_status(status_id=None, state="idle", label=None, buffered_count=0, updated_at=None, controls_html=None, compact=False, class_name="", attrs="")` |
| `filter_accordion` | `filter_accordion(accordion_id, title="Filters", body="", icon_class="bi bi-funnel", open=True, active_badge=False, header_suffix="", class_name="", attrs="")` |
| `filter_multi_select` | `filter_multi_select(name, label, options, selected_values=None, placeholder=None, single_select=False, auto_submit=True, input_name=None, class_name="", attrs="")` |
| `filter_single_select` | `filter_single_select(name, label, options, selected_value="", placeholder=None, auto_submit=True, input_name=None, class_name="", attrs="")` |
| `date_range_picker` | `date_range_picker(from_name="from_ts", to_name="to_ts", from_value="", to_value="", label="Date range", button_label="Range", auto_submit=True, class_name="", attrs="", presets=None)` |
| `regex_filter_input` | `regex_filter_input(name="q", value="", input_id=None, dropdown_id=None, placeholder="Regex filter (&&, !, \\&&)", validate_endpoint=None, hint_text=None, class_name="", attrs="")` |
| `sql_filter_input` | `sql_filter_input(name="sql", value="", input_id=None, dropdown_id=None, placeholder="SQL WHERE expression", hints_endpoint=None, validate_endpoint=None, hint_text=None, class_name="", attrs="")` |
| `form_input` | `form_input(name, label=None, value="", input_type="text", placeholder=None, variant=None, help_text=None, invalid_text=None, valid=False, required=False, class_name="", id=None, attrs="")` |
| `form_select` | `form_select(name, options, label=None, value="", placeholder=None, help_text=None, invalid_text=None, valid=False, required=False, class_name="", id=None, attrs="")` |
| `autocomplete` | `autocomplete(name, endpoint, value="", display_value=None, label=None, placeholder=None, help_text=None, invalid_text=None, valid=False, required=False, min_chars=1, class_name="", input_class="", panel_class="", id=None, attrs="")` |
| `textarea` | `textarea(name, label=None, value="", rows=4, placeholder=None, help_text=None, invalid_text=None, valid=False, class_name="", id=None, attrs="")` |
| `navbar` | `navbar(brand, brand_href="/", nav_items=None, expand="lg", theme="light", background="light", class_name="", id=None, attrs="")` |
| `sort_indicator` | `sort_indicator(active, direction)` |
| `data_grid` | `data_grid(component_id, endpoint, columns, rows, state=None, total_rows=None, caption=None, subtitle=None, count_label=None, empty_html=None, loading_html=None, error_html=None, toolbar_html=None, row_actions_slot=False, selectable=False, selected_ids=None, selection_name="selected_ids", selection_actions_html=None, mobile_labels=True, persist="header", state_keys=None, sse_endpoint=None, sse_event="refresh", stream_mode="replace", stream_max_rows=None, stream_pause_when_hidden=False, stream_buffer_max=100, lazy=False, class_name="", attrs="")` |
| `searchable_expandable_list` | `searchable_expandable_list(list_id, items, search_input=True, search_placeholder="Search items...", empty_title="No matching items", empty_message="Try another search term.", class_name="", attrs="")` |
| `filterable_card_list` | `filterable_card_list(list_id, items, title=None, subtitle=None, search_placeholder="Search cards...", empty_title="No matching cards", empty_message="Try another search term.", column_class="col-12 col-md-6 col-xl-4", class_name="", attrs="")` |
| `stacked_list` | `stacked_list(list_id, items, title=None, subtitle=None, flush=True, class_name="", attrs="")` |
| `timeline` | `timeline(timeline_id, items, title=None, subtitle=None, class_name="", attrs="")` |
| `tree_nav_nodes` | `tree_nav_nodes(nodes, tree_id, level=0)` |
| `tree_nav` | `tree_nav(tree_id, items, title=None, subtitle=None, class_name="", attrs="")` |
| `code_block` | `code_block(block_id=None, code="", language=None, title=None, caption=None, actions_html=None, line_numbers=False, max_height=None, wrap=False, class_name="", attrs="")` |
| `facet_bar` | `facet_bar(facet_id, items, title=None, clear_action_html=None, compact=False, class_name="", attrs="")` |
| `result_panel` | `result_panel(panel_id=None, title=None, subtitle=None, status_badge=None, actions_html=None, body="", empty_html=None, error_html=None, footer=None, class_name="", attrs="")` |
| `master_detail_shell` | `master_detail_shell(shell_id, master_html="", detail_html="", title=None, subtitle=None, header_actions_html=None, master_col_class="col-12 col-lg-4", detail_col_class="col-12 col-lg-8", class_name="", attrs="")` |
| `inline_edit_shell` | `inline_edit_shell(shell_id, title=None, subtitle=None, status_badge=None, actions_html=None, display_title="Current", editor_title="Edit", display_html="", editor_html="", summary_html=None, footer_html=None, display_col_class="col-12 col-xl-5", editor_col_class="col-12 col-xl-7", class_name="", attrs="")` |
| `command_bar` | `command_bar(bar_id=None, title=None, subtitle=None, badges=None, leading_html=None, trailing_html=None, compact=False, class_name="", attrs="")` |
| `metric_grid` | `metric_grid(grid_id, items, title=None, subtitle=None, col_class="col-12 col-md-6 col-xl-3", class_name="", attrs="")` |
| `activity_feed` | `activity_feed(feed_id, items, title=None, subtitle=None, class_name="", attrs="")` |
| `property_editor` | `property_editor(editor_id, title=None, subtitle=None, body="", aside_html=None, footer_html=None, actions_html=None, class_name="", attrs="")` |
| `diff_view` | `diff_view(view_id, left_code="", right_code="", left_title="Before", right_title="After", title=None, subtitle=None, language=None, class_name="", attrs="")` |
| `table` | `table(component_id, endpoint, columns, rows, state=None, total_rows=None, title=None, subtitle=None, toolbar=None, empty_message="No rows found.", persist="memory", selectable=False, selected_ids=None, selection_name="selected_ids", selection_actions_html=None, state_keys=None, sse_endpoint=None, sse_event="refresh", stream_mode="replace", stream_max_rows=None, stream_pause_when_hidden=False, stream_buffer_max=100, lazy=False, class_name="", attrs="")` |

## Authoring Notes

- Prefer these macros before writing raw Bootstrap markup.
- Use app-level macros to compose domain-specific behavior on top of these primitives.
- Preserve generated `data-jbs-*` attributes when wrapping interactive components.
- Keep fragment endpoints server-rendered and deterministic.
