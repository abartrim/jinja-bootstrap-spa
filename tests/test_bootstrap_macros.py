"""Tests for the packaged Bootstrap Jinja macros."""

from jinja2 import Environment

from jinja_bootstrap_spa.macros.bootstrap import register_bootstrap_macros
from jinja_bootstrap_spa.runtime.components import (
    action_attrs,
    attrs_to_html,
    table_attrs,
)
from jinja_bootstrap_spa.runtime.contract import (
    JBS_STATE_HEADER,
    conditional_fragment_response,
    etag_matches,
    fragment_etag,
    parse_table_state,
)


def build_environment() -> Environment:
    """Create an environment with the packaged macros registered."""

    environment = Environment(autoescape=True)
    register_bootstrap_macros(environment)
    return environment


def test_button_macro_renders_bootstrap_button_markup() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{ ui.button("Save") }}
        """
    )

    rendered = template.render()

    assert 'class="btn btn-primary"' in rendered
    assert 'type="button"' in rendered
    assert ">Save</button>" in rendered


def test_button_macro_supports_runtime_action_attributes() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.button(
            "Refresh",
            jbs_action="refresh",
            jbs_component_ref="orders-table"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'data-jbs-action="refresh"' in rendered
    assert 'data-jbs-component-ref="orders-table"' in rendered


def test_button_macro_supports_row_actions() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.button(
            "Archive",
            variant="outline-danger",
            size="sm",
            jbs_action="row",
            jbs_row_id="order-42",
            jbs_intent="archive"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'data-jbs-action="row"' in rendered
    assert 'data-jbs-row-id="order-42"' in rendered
    assert 'data-jbs-intent="archive"' in rendered


def test_form_select_macro_supports_selected_value_and_validation_feedback() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.form_select(
            "status",
            [
              {"value": "queued", "label": "Queued"},
              {"value": "open", "label": "Open"},
            ],
            value="open",
            placeholder="All statuses",
            invalid_text="Pick a valid status",
            class_name="form-select-sm"
          )
        }}
        """
    )

    rendered = template.render()
    compact_rendered = " ".join(rendered.split())

    assert 'name="status"' in rendered
    assert 'class="form-select is-invalid form-select-sm"' in rendered
    assert '<option value="">All statuses</option>' in rendered
    assert 'option value="open"' in rendered
    assert 'value="open" selected' in rendered
    assert '<option value="open" selected> Open </option>' in compact_rendered
    assert "Pick a valid status" in rendered


def test_autocomplete_macro_renders_combobox_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.autocomplete(
            "customer",
            "/fragments/customer-options",
            value="Margaret Hamilton",
            display_value="Margaret Hamilton",
            placeholder="Filter customer",
            min_chars=2,
            class_name="mb-0",
            input_class="form-control-sm"
          )
        }}
        """
    )

    rendered = template.render()

    assert "data-jbs-autocomplete" in rendered
    assert 'data-jbs-autocomplete-endpoint="/fragments/customer-options"' in rendered
    assert 'data-jbs-autocomplete-min-chars="2"' in rendered
    assert "data-jbs-autocomplete-input" in rendered
    assert "data-jbs-autocomplete-value" in rendered
    assert 'role="combobox"' in rendered
    assert 'name="customer"' in rendered
    assert 'value="Margaret Hamilton"' in rendered


def test_modal_and_drawer_macros_render_overlay_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{ ui.modal("runtime-modal", title="Runtime Notes", body="<p>Body</p>") }}
        {{ ui.drawer("orders-drawer", title="Workbench", body="<p>Drawer</p>") }}
        """
    )

    rendered = template.render()

    assert 'id="runtime-modal"' in rendered
    assert 'data-jbs-overlay="modal"' in rendered
    assert "data-jbs-overlay-panel" in rendered
    assert "data-jbs-overlay-close" in rendered
    assert 'role="dialog"' in rendered
    assert 'id="orders-drawer"' in rendered
    assert 'data-jbs-overlay="drawer"' in rendered


def test_tabs_macro_renders_runtime_tab_actions() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.tabs(
            "orders-tabs",
            items=[
              {
                "label": "All",
                "value": "__all__",
                "jbs_action": "filter",
                "jbs_patch": {"status": none}
              },
              {
                "label": "Queued",
                "value": "queued",
                "jbs_action": "filter",
                "jbs_patch": {"status": "queued"}
              },
            ],
            active="queued"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'id="orders-tabs"' in rendered
    assert 'role="tablist"' in rendered
    assert 'data-jbs-action="filter"' in rendered
    assert "data-jbs-patch=" in rendered
    assert 'class="nav-link active"' in rendered
    assert 'aria-selected="true"' in rendered


def test_segmented_control_macro_renders_pill_tabs_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.segmented_control(
            "orders-segments",
            items=[
              {"label": "All", "value": "__all__", "jbs_action": "filter"},
              {"label": "Queued", "value": "queued", "jbs_action": "filter"},
            ],
            active="queued"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'id="orders-segments"' in rendered
    assert "jbs-segmented-control" in rendered
    assert "nav-pills" in rendered
    assert 'role="tablist"' in rendered


def test_toast_macro_renders_dismissible_status_notice() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.toast(
            "orders-toast",
            title="Live Update",
            message="Order #1005 moved to open.",
            variant="warning"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'id="orders-toast"' in rendered
    assert "data-jbs-status-region" in rendered
    assert "data-jbs-status-dismiss" in rendered
    assert 'class="alert alert-warning shadow-sm mb-0"' in rendered
    assert "Order #1005 moved to open." in rendered


def test_status_region_macro_renders_dismissible_notice() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.status_region(
            "orders-status-region",
            title="Live Update",
            message="Order #1005 moved to open.",
            variant="warning"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'id="orders-status-region"' in rendered
    assert "data-jbs-status-region" in rendered
    assert "data-jbs-status-dismiss" in rendered
    assert 'class="alert alert-warning alert-dismissible"' in rendered
    assert "Order #1005 moved to open." in rendered


def test_filter_accordion_macro_renders_disclosure_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.filter_accordion(
            "orders-filters",
            title="Filters",
            body="<form></form>",
            active_badge=true
          )
        }}
        """
    )

    rendered = template.render()

    assert 'id="orders-filters"' in rendered
    assert "data-jbs-disclosure" in rendered
    assert "data-jbs-disclosure-trigger" in rendered
    assert "data-jbs-disclosure-panel" in rendered
    assert "Active" in rendered


def test_multi_select_filter_macros_render_runtime_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.filter_multi_select(
            "service",
            "Service",
            [
              {"value": "api", "label": "API"},
              {"value": "worker", "label": "Worker"},
            ],
            selected_values=["api"],
            auto_submit=true
          )
        }}
        {{
          ui.filter_single_select(
            "status",
            "Status",
            [
              {"value": "open", "label": "Open"},
              {"value": "queued", "label": "Queued"},
            ],
            selected_value="open"
          )
        }}
        """
    )

    rendered = template.render()

    assert "data-jbs-multi-select" in rendered
    assert 'data-jbs-ms-input-name="service"' in rendered
    assert "data-jbs-ms-toggle" in rendered
    assert "data-jbs-ms-menu" in rendered
    assert "data-jbs-ms-option" in rendered
    assert 'name="service"' in rendered
    assert 'data-jbs-ms-single="true"' in rendered
    assert 'name="status"' in rendered


def test_date_range_and_assist_macros_render_runtime_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.date_range_picker(
            from_value="2026-04-12 09:00",
            to_value="2026-04-12 10:00"
          )
        }}
        {{
          ui.regex_filter_input(
            value="error && !healthcheck",
            validate_endpoint="/api/validate-regex"
          )
        }}
        {{
          ui.sql_filter_input(
            value="service = 'api'",
            hints_endpoint="/api/sql-hints",
            validate_endpoint="/api/sql-validate"
          )
        }}
        """
    )

    rendered = template.render()

    assert "data-jbs-date-range" in rendered
    assert "data-jbs-drp-toggle" in rendered
    assert "data-jbs-drp-preset" in rendered
    assert "data-jbs-drp-custom-from" in rendered
    assert 'data-jbs-assist="regex"' in rendered
    assert 'data-jbs-assist-validate-endpoint="/api/validate-regex"' in rendered
    assert 'data-jbs-assist="sql"' in rendered
    assert 'data-jbs-assist-hints-endpoint="/api/sql-hints"' in rendered
    assert 'data-jbs-assist-validate-endpoint="/api/sql-validate"' in rendered


def test_action_menu_macro_renders_runtime_friendly_dropdown_markup() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.action_menu(
            "order-actions",
            items=[
              {"label": "Inspect", "href": "/orders/42"},
              {"divider": true},
              {
                "label": "Archive Order",
                "jbs_action": "row",
                "jbs_row_id": "order-42",
                "jbs_intent": "archive",
                "variant": "danger"
              },
            ]
          )
        }}
        """
    )

    rendered = template.render()

    assert "data-jbs-menu" in rendered
    assert "data-jbs-menu-trigger" in rendered
    assert "data-jbs-menu-panel" in rendered
    assert 'role="menu"' in rendered
    assert 'href="/orders/42"' in rendered
    assert 'data-jbs-action="row"' in rendered
    assert 'data-jbs-row-id="order-42"' in rendered
    assert 'data-jbs-intent="archive"' in rendered
    assert "text-danger" in rendered


def test_table_macro_renders_component_contract() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.table(
            "orders-table",
            "/components/orders",
            columns=[
              {"key": "number", "label": "Order", "sortable": true},
              {"key": "status", "label": "Status", "sortable": false},
            ],
            rows=[
              {"number": "#1001", "status": "Queued"},
            ],
            state={"page": 1, "page_size": 25, "sort_by": "number", "sort_dir": "asc"},
            total_rows=40,
            persist="querystring",
            state_keys=["page", "page_size", "sort_by", "sort_dir", "query", "status"],
            sse_endpoint="/events/orders",
            title="Orders"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'data-jbs-component="table"' in rendered
    assert 'data-jbs-endpoint="/components/orders"' in rendered
    assert 'data-jbs-persist="querystring"' in rendered
    assert (
        'data-jbs-state-keys="page,page_size,sort_by,sort_dir,query,status"' in rendered
    )
    assert 'data-jbs-sse="/events/orders"' in rendered
    assert 'data-jbs-sse-event="refresh"' in rendered
    assert 'data-jbs-stream-mode="replace"' in rendered
    assert 'data-jbs-stream-pause-when-hidden="false"' in rendered
    assert 'data-jbs-stream-buffer-max="100"' in rendered
    assert 'data-jbs-sort-key="number"' in rendered
    assert "Page 1 of 2" in rendered
    assert "Showing 1 of 40 results" in rendered


def test_runtime_helpers_serialize_component_and_action_attrs() -> None:
    component_html = attrs_to_html(
        table_attrs(
            endpoint="/components/orders",
            target="#orders-table",
            key="orders",
            state={"page": 2, "sort_by": "created_at"},
            persist="session",
            state_keys=("page", "page_size", "sort_by"),
            sse_endpoint="/events/orders",
            stream_mode="append",
            stream_max_rows=50,
            stream_pause_when_hidden=True,
            stream_buffer_max=200,
            lazy=True,
        )
    )
    action_html = attrs_to_html(
        action_attrs(
            action="row",
            component_ref="orders-table",
            row_id="order-42",
            intent="archive",
            patch={"status": "archived"},
        )
    )

    assert 'data-jbs-component="table"' in str(component_html)
    assert 'data-jbs-persist="session"' in str(component_html)
    assert 'data-jbs-state-keys="page,page_size,sort_by"' in str(component_html)
    assert 'data-jbs-sse="/events/orders"' in str(component_html)
    assert 'data-jbs-stream-mode="append"' in str(component_html)
    assert 'data-jbs-stream-max-rows="50"' in str(component_html)
    assert 'data-jbs-stream-pause-when-hidden="true"' in str(component_html)
    assert 'data-jbs-stream-buffer-max="200"' in str(component_html)
    assert 'data-jbs-lazy="true"' in str(component_html)
    assert (
        'data-jbs-state="{&#34;page&#34;:2,&#34;sort_by&#34;:&#34;created_at&#34;}"'
        in str(component_html)
    )
    assert 'data-jbs-action="row"' in str(action_html)
    assert 'data-jbs-row-id="order-42"' in str(action_html)
    assert 'data-jbs-intent="archive"' in str(action_html)


def test_parse_table_state_normalizes_paging_sorting_and_filters() -> None:
    state = parse_table_state(
        {
            "page": "0",
            "page_size": "500",
            "sort_by": "created_at",
            "sort_dir": "down",
            "query": "urgent",
            "status": "open",
        },
        default_sort_by="number",
        default_page_size=25,
        allowed_page_sizes=(10, 25, 50),
        filter_keys=("status",),
    )

    assert state == {
        "page": 1,
        "page_size": 25,
        "sort_by": "created_at",
        "sort_dir": "asc",
        "query": "urgent",
        "status": "open",
    }


def test_parse_table_state_prefers_header_state_over_query_params() -> None:
    state = parse_table_state(
        {
            "page": "3",
            "page_size": "10",
            "sort_by": "number",
            "sort_dir": "asc",
            "status": "queued",
        },
        request_headers={
            JBS_STATE_HEADER: (
                '{"page":2,"page_size":25,"sort_by":"customer",'
                '"sort_dir":"desc","status":"open"}'
            )
        },
        default_sort_by="number",
        default_page_size=10,
        allowed_page_sizes=(10, 25),
        filter_keys=("status",),
    )

    assert state == {
        "page": 2,
        "page_size": 25,
        "sort_by": "customer",
        "sort_dir": "desc",
        "status": "open",
    }


def test_fragment_etag_is_stable_for_identical_content() -> None:
    content = "<section id='orders-table'>A</section>"
    assert fragment_etag(content) == fragment_etag(content)


def test_etag_matches_accepts_weak_and_strong_forms() -> None:
    etag = fragment_etag("<section id='orders-table'>A</section>")
    strong = etag[2:]
    assert etag_matches(etag, etag)
    assert etag_matches(strong, etag)
    assert etag_matches(f'{strong}, W/"other"', etag)
    assert not etag_matches('W/"jbs-other"', etag)


def test_conditional_fragment_response_returns_304_on_match() -> None:
    content = "<section id='orders-table'>A</section>"
    first_body, first_status, first_headers = conditional_fragment_response(content, {})
    assert first_status == 200
    assert first_body == content
    assert first_headers["Cache-Control"] == "no-cache"
    etag = first_headers["ETag"]

    second_body, second_status, second_headers = conditional_fragment_response(
        content,
        {"If-None-Match": etag},
    )
    assert second_status == 304
    assert second_body == ""
    assert second_headers["ETag"] == etag
