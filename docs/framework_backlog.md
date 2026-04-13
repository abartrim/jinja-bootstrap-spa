# Framework Backlog

This backlog tracks the next generic primitives `jinja-bootstrap-spa` should
add so consuming Jinja applications can compose richer product-specific UI on
top of the framework.

The boundary is intentional:

- The framework owns generic server-rendered UI primitives and the SPA-like
  replacement/runtime contract.
- Consuming apps own domain-specific compositions, workflows, and business
  language.

## Non-Goals

These should stay in consuming apps, not in this framework:

- saved reports workflows
- logs-specific live tail behavior
- AI trace grouping views
- dashboard/chart-builder product flows
- work-item specific modal content
- query-builder product UX

## Prioritization Rules

Prioritize primitives that:

1. Repeat across many pages.
2. Are useful outside Sobs.
3. Reduce bespoke template and JavaScript in consuming apps.
4. Fit the current runtime model of full component replacement plus optional
   stream updates.

## Proposed Backlog

### P0: Page Framing

#### `page_header(...)`

Status: missing

Why:

- Repeated across many server-rendered apps.
- Needed for title, subtitle, metadata chips, breadcrumbs, and action groups.

Proposed API:

```jinja
{{ ui.page_header(
    title="Orders",
    subtitle="Monitor order health and recent changes.",
    icon="bi bi-box-seam",
    eyebrow=None,
    meta_html=None,
    actions_html=None,
    breadcrumbs=None,
    class_name="",
    attrs=""
) }}
```

Notes:

- Keep `meta_html` and `actions_html` as escape hatches.
- Accept either `title` or `title_html`.
- Breadcrumbs should be generic link dictionaries.

Sobs pages unblocked:

- `logs.html`
- `work_items.html`
- `ai.html`
- `reports.html`
- `query.html`
- `table_explorer.html`
- `custom_dashboard_view.html`

#### `toolbar(...)` / `filter_bar_shell(...)`

Status: missing

Why:

- Repeated page-level shell for filters, status badges, action buttons, and
  secondary controls.
- Should not know about reports, timezones, or app-specific actions.

Proposed API:

```jinja
{% call ui.toolbar(
    toolbar_id="orders-toolbar",
    title=None,
    subtitle=None,
    badges=None,
    actions_html=None,
    collapsible=True,
    expanded=True,
    class_name="",
    attrs=""
) %}
  {{ filters_html | safe }}
{% endcall %}
```

Notes:

- This should be a shell, not a domain-specific filter system.
- Works well with existing filter macros and future app-specific composites.

Sobs pages unblocked:

- `logs.html`
- `work_items.html`
- `ai.html`

### P1: Stateful Data Presentation

#### `data_grid(...)`

Status: partial, table base exists

Why:

- The current `table(...)` covers the contract, but apps still need a richer
  grid shell around it.
- This is the biggest generic unlock for CRUD/admin/ops apps.

Proposed API:

```jinja
{{ ui.data_grid(
    component_id="orders-grid",
    endpoint="/components/orders",
    columns=columns,
    rows=rows,
    state=state,
    caption=None,
    subtitle=None,
    count_label=None,
    empty_html=None,
    loading_html=None,
    error_html=None,
    toolbar_html=None,
    row_actions_slot=True,
    mobile_labels=True,
    persist="header",
    sse_endpoint=None,
    stream_mode="replace",
    class_name="",
    attrs=""
) }}
```

Notes:

- Build on top of the existing table runtime contract.
- Support richer empty/loading/error slots without changing the transport model.
- Support mobile card metadata and action-cell layout.

Sobs pages unblocked:

- `logs.html`
- `work_items.html`
- portions of `query.html`

#### `stream_status(...)`

Status: missing

Why:

- The runtime supports streaming, buffering, and refresh semantics already.
- Apps still need a generic status strip to present connection state cleanly.

Proposed API:

```jinja
{{ ui.stream_status(
    status_id="orders-stream-status",
    state="idle",
    label="Live off",
    buffered_count=0,
    updated_at=None,
    controls_html=None,
    compact=False,
    class_name="",
    attrs=""
) }}
```

Notes:

- Generic states should include `idle`, `connecting`, `live`, `paused`,
  `buffered`, `error`, and `stale`.
- Leave behavior wiring to consuming apps or light runtime helpers.

Sobs pages unblocked:

- `logs.html`
- `ai.html`

#### `stat_card(...)`

Status: missing

Why:

- Summary metrics appear in analytics, admin, and dashboard pages.
- Highly reusable and cheap to implement.

Proposed API:

```jinja
{{ ui.stat_card(
    title="Total Calls",
    value="12.4K",
    subtitle=None,
    icon="bi bi-cpu",
    tone="primary",
    href=None,
    trend=None,
    class_name="",
    attrs=""
) }}
```

Sobs pages unblocked:

- `ai.html`
- dashboard pages in `custom_dashboard_view.html`

#### `empty_state(...)`

Status: missing

Why:

- Repeated everywhere and easy to standardize.

Proposed API:

```jinja
{{ ui.empty_state(
    title="No charts yet",
    message="Add your first chart to this dashboard.",
    icon="bi bi-bar-chart",
    action_html=None,
    compact=False,
    class_name="",
    attrs=""
) }}
```

Sobs pages unblocked:

- `reports.html`
- `work_items.html`
- `table_explorer.html`
- `custom_dashboard_view.html`

### P2: Structured Detail Views

#### `detail_list(...)` / `key_value_panel(...)`

Status: missing

Why:

- Reusable for detail modals, inspection panels, and metadata sidebars.

Proposed API:

```jinja
{{ ui.detail_list(
    items=[
      {"label": "Service", "value": "api"},
      {"label": "Status", "value_html": "<span class='badge bg-success'>OK</span>"},
    ],
    columns=1,
    striped=False,
    compact=False,
    class_name="",
    attrs=""
) }}
```

Sobs pages unblocked:

- `work_items.html`
- parts of `reports.html`

#### `callout(...)`

Status: missing

Why:

- Reusable for beta notices, help blocks, migration hints, and warnings.

Proposed API:

```jinja
{{ ui.callout(
    title=None,
    message="This feature is beta.",
    tone="info",
    icon=None,
    dismissible=False,
    class_name="",
    attrs=""
) }}
```

Sobs pages unblocked:

- `query.html`
- `reports.html`
- help/instructional sections across pages

### P3: Explorers, Editors, and Rich Layout

#### `searchable_expandable_list(...)`

Status: missing

Why:

- Generic pattern for explorer-style pages and grouped drill-down lists.

Proposed API:

```jinja
{% call(item) ui.searchable_expandable_list(
    list_id="schema-list",
    items=tables,
    search_input=True,
    search_placeholder="Search items...",
    empty_title="No matching items",
    empty_message="Try another search term.",
    class_name="",
    attrs=""
) %}
  {{ caller(item) }}
{% endcall %}
```

Notes:

- The generic primitive should own shell/search/expand behavior.
- Consuming apps should supply item body/detail markup.

Sobs pages unblocked:

- `table_explorer.html`

#### `chart_shell(...)`

Status: missing

Why:

- Many apps need a consistent chart card, even when the chart library differs.

Proposed API:

```jinja
{% call ui.chart_shell(
    chart_id="requests-chart",
    title="Request Volume",
    subtitle=None,
    badges=None,
    actions_html=None,
    footer_html=None,
    empty_html=None,
    error_html=None,
    class_name="",
    attrs=""
) %}
  <div id="requests-chart-canvas"></div>
{% endcall %}
```

Notes:

- This should not embed ECharts-specific logic.
- It is a shell around the render target and surrounding actions/status.

Sobs pages unblocked:

- `query.html`
- `custom_dashboard_view.html`

#### `workspace_modal(...)`

Status: missing

Why:

- Consuming apps need large, scrollable, editing-oriented overlays that go
  beyond a simple confirm modal.

Proposed API:

```jinja
{% call ui.workspace_modal(
    overlay_id="chart-editor",
    title="Edit Chart",
    size="xl",
    footer_html=None,
    sticky_header=True,
    sticky_footer=True,
    class_name="",
    attrs=""
) %}
  {{ editor_html | safe }}
{% endcall %}
```

Sobs pages unblocked:

- `custom_dashboard_view.html`
- parts of `query.html`

#### `split_panel(...)`

Status: missing

Why:

- Generic layout primitive for builder/preview, inspector/content, and
  editor/results views.

Proposed API:

```jinja
{% call ui.split_panel(
    direction="horizontal",
    ratio="50/50",
    collapse_on_mobile=True,
    class_name="",
    attrs=""
) %}
  <section data-jbs-pane="primary">...</section>
  <section data-jbs-pane="secondary">...</section>
{% endcall %}
```

Sobs pages unblocked:

- `query.html`
- `custom_dashboard_view.html`

## Suggested Delivery Order

1. `page_header`
2. `toolbar`
3. `data_grid`
4. `empty_state`
5. `stat_card`
6. `detail_list`
7. `stream_status`
8. `callout`
9. `searchable_expandable_list`
10. `chart_shell`
11. `workspace_modal`
12. `split_panel`

## Framework vs App Composition

Examples of what the framework should enable, but not own:

- Sobs can build `saved_reports_filter_bar(...)` on top of `toolbar(...)`.
- Sobs can build `logs_live_panel(...)` on top of `stream_status(...)`.
- Sobs can build `ai_trace_group(...)` on top of `card(...)`,
  `detail_list(...)`, and `page_header(...)`.
- Sobs can build `dashboard_chart_editor(...)` on top of
  `workspace_modal(...)`, `split_panel(...)`, `form_*` macros, and
  `chart_shell(...)`.

## Implementation Notes

- Prefer macro names that describe structure rather than app semantics.
- Keep `*_html` escape hatches for advanced composition.
- Do not add framework JS unless the behavior is truly generic and repeated.
- Reuse the existing `data-jbs-*` runtime model instead of inventing separate
  interaction channels for each new primitive.
