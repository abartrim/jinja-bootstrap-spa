# jinja-bootstrap-spa

`jinja-bootstrap-spa` is a Python-first UI framework for building server-rendered
applications with consistent Bootstrap styling and a lightweight SPA-like runtime.
It also includes an experimental Go companion built on
[`minijinja-go`](https://github.com/mitsuhiko/minijinja/tree/main/minijinja-go)
for teams that want to reuse the same packaged Jinja templates outside Python.

The framework is opinionated on purpose:

- Jinja2 renders the canonical HTML.
- Bootstrap 5 provides the visual system.
- A small first-party browser runtime handles component refresh, state, and DOM replacement.
- Components communicate through `data-jbs-*` attributes instead of a heavy front-end framework.
- Form primitives cover the common server-driven cases without custom CSS.

The first vertical is a stateful table component with row action menus, because
tables force the runtime to solve the hard problems early: sorting, filtering,
paging, refresh, and state preservation across fragment swaps.

## Design Goals

- Give humans and AI agents a constrained component authoring model.
- Keep layout and styling consistent without requiring custom CSS.
- Support SPA-like interactions while keeping the server responsible for HTML.
- Ship a real typed browser runtime for consumers once client-side behavior becomes public API.

## Installation

```bash
pip install jinja-bootstrap-spa
```

For the Go companion:

```bash
go get github.com/abartrim/jinja-bootstrap-spa
```

For framework development:

```bash
pip install -e ".[dev]"
python -m playwright install chromium
npm ci
```

Run the full validation suite with:

```bash
flake8 src tests
black --check src tests
isort --check-only src tests
mypy src
djlint src/jinja_bootstrap_spa/templates --check
test -z "$(gofmt -l assets.go environment.go environment_test.go)"
GOSUMDB=off go test ./...
npm run build:js
npm run typecheck:js
pytest
```

To enforce linting automatically before each commit, enable pre-commit hooks:

```bash
pip install -e ".[dev]"
pre-commit install
```

Run all hooks manually at any time with:

```bash
pre-commit run --all-files
```

The browser-level tests use Playwright's Python bindings and expect Chromium to
be installed through `python -m playwright install chromium`.

Two Playwright suites are included:

- `tests/test_browser_runtime.py`: runtime contract tests against an in-test Flask app.
- `tests/test_example_wrapper_app.py`: smoke/regression tests against the real wrapper app.
- `tests/test_go_example_app.py`: the same wrapper smoke flow against the Go MiniJinja example app.

## Wrapper Dev App

A standalone Flask wrapper app lives in
[examples/table_app](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/examples/table_app).
Use it to iterate on runtime behavior manually while developing new components.

Run it with:

```bash
npm run example:python
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

A matching Go wrapper app lives in
[examples/go_table_app](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/examples/go_table_app).
It renders the same example templates without modification through MiniJinja-Go.

Run it with:

```bash
npm run example:go
```

Then open [http://127.0.0.1:5001](http://127.0.0.1:5001).

AI authoring guidance for Codex, Copilot, and Claude lives in
[AGENTS.md](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/AGENTS.md) and
[docs/llm_authoring_guide.md](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/docs/llm_authoring_guide.md).

The dev app includes:

- an SSE-backed orders table with stateful filters
- a prepend-stream live table (row-level SSE patches)
- an append-stream live table (row-level SSE patches)
- a session-persisted table (`sessionStorage`)
- a stale-request cancellation demo
- a lazy-hydrated component loaded on first viewport entry
- a foundation gallery covering generic shells such as data grids, timelines,
  stacked lists, tree navigation, code blocks, workspace modals, and explorer surfaces

Use `Simulate SSE Update`, `Push Prepend Row`, and `Push Append Row` to exercise
all stream modes.

The feature-to-example coverage map lives in
[docs/feature_coverage.md](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/docs/feature_coverage.md).

The generic framework implementation backlog lives in
[docs/framework_backlog.md](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/docs/framework_backlog.md).

The current macro surface now includes:

- stateful table and richer `data_grid(...)` shells
- page framing via `page_header(...)` and `toolbar(...)`
- overlays via `modal(...)`, `drawer(...)`, and `workspace_modal(...)`
- form primitives including autocomplete, multi-select, regex/sql assist, and date-range inputs
- presentation primitives such as `stat_card(...)`, `detail_list(...)`, `callout(...)`, `chart_shell(...)`, `timeline(...)`, `stacked_list(...)`, `tree_nav(...)`, and `code_block(...)`
- workflow/presentation shells such as `facet_bar(...)`, `master_detail_shell(...)`, and `result_panel(...)`
- inspector/review primitives such as `command_bar(...)`, `metric_grid(...)`, `activity_feed(...)`, `property_editor(...)`, and `diff_view(...)`
- collection/edit primitives such as `filterable_card_list(...)` and `inline_edit_shell(...)`
- dense-grid enhancements including row selection and pinned columns in `table(...)` and `data_grid(...)`

For manual visual inspection snapshots:

```bash
.venv/bin/python scripts/capture_example_visuals.py
```

This writes desktop/mobile screenshots to `tmp/visual/`.

For a short guided walkthrough video:

```bash
.venv/bin/python scripts/record_example_walkthrough.py
```

This writes `tmp/demo/wrapper-walkthrough.webm` (playable in browsers and suitable
for docs/tutorial sharing). The recorder includes on-screen captions (intro,
feature-by-feature narration, and summary) and supports pacing controls:

```bash
.venv/bin/python scripts/record_example_walkthrough.py --pace 2.2
```

For stream protocol benchmark trend summaries (from Playwright metrics artifacts):

```bash
.venv/bin/python scripts/summarize_stream_metrics.py
```

This reads `tmp/metrics/stream_protocol_metrics_history.csv` and reports latest
metrics, rolling medians, and deltas versus previous/baseline runs.

## Runtime Model

Each interactive fragment is a server-rendered component root:

- `data-jbs-component`
- `data-jbs-endpoint`
- `data-jbs-target`
- `data-jbs-state`
- `data-jbs-key`
- `data-jbs-stream-mode`
- `data-jbs-lazy`

Interactive controls inside the component emit actions such as:

- `data-jbs-action="refresh"`
- `data-jbs-action="sort"`
- `data-jbs-action="page"`
- `data-jbs-patch='{"status":"open"}'`

The browser runtime sends component state to the endpoint and, by default,
replaces the component root in one swap. For stream-heavy tables it can also
apply row-level append/prepend patches from SSE payloads.

## Table Contract

The table component is the first fully specified contract in the framework.

### Request shape

Table state can be transported either via query params or the state header.
The reserved table keys are:

- `page`
- `page_size`
- `sort_by`
- `sort_dir`
- `query`

Additional filter fields are allowed and should be treated as table-specific state.
For example, a filtered orders table may also send `status=open` and `owner=ops`.

When `persist="header"` is enabled, the runtime sends state as JSON in
`X-JBS-State` and the server should prefer that over query params.

The runtime also sends these headers:

- `X-JBS-Request: true`
- `X-JBS-Component: table`
- `X-JBS-Action: refresh|filter|page|sort|row`
- `X-JBS-State: { ... }` (when using `persist="header"`)
- `If-None-Match: W/"jbs-..."` (when the runtime already has an ETag for the component)

On the Python side, use `parse_table_state(...)` to normalize incoming state
before querying data:

```python
from jinja_bootstrap_spa import parse_table_state


state = parse_table_state(
    request.args,
    request_headers=request.headers,
    default_sort_by="created_at",
    default_page_size=25,
    allowed_page_sizes=(10, 25, 50, 100),
    filter_keys=("status", "owner"),
)
```

### Response shape

A component endpoint must return HTML with a single root element. For tables,
that root should remain the same logical component:

- keep the same root `id`
- keep `data-jbs-component="table"`
- keep or allow the runtime to preserve `data-jbs-endpoint`
- return a fully rendered replacement fragment, not partial row patches

The runtime will reject a swapped fragment if the component type changes, and it
expects the root identity to stay stable across requests.

To reduce payload when content is unchanged, you can return conditional responses
using helper utilities:

```python
from flask import request
from jinja_bootstrap_spa import conditional_fragment_response


@app.get("/components/orders")
def orders_component():
    html = render_template("partials/orders_table.html", **build_orders_context())
    return conditional_fragment_response(html, request.headers)
```

When `If-None-Match` matches, the helper returns `304` with no HTML body.
The runtime treats that as "no visual change", skips swap, and keeps current DOM.

## Visual Cues

The runtime emits visible update cues by default:

- `jbs-swap-pulse` on full component replacement (orange border/glow flash)
- `jbs-not-modified-pulse` on `304 Not Modified` refresh attempts (cyan border/glow flash)
- `jbs-stream-row-pulse` on stream append/prepend row insert

What you should see in the example app:

- Clicking `Refresh Table` with changed content flashes the table boundary.
- Clicking `Refresh Table` with no server-side changes flashes cyan to show the request was handled but no replacement was needed.
- Stream buttons (`Push Prepend Row` / `Push Append Row`) flash inserted rows.
- If a response is `304 Not Modified`, there is no swap flash; you should see the cyan not-modified flash instead.

### Stream shape

When using SSE (`data-jbs-sse`), table components support three stream modes:

- `replace`: fetch and replace the whole fragment (default)
- `prepend`: prepend incoming row payloads into `<tbody>`
- `append`: append incoming row payloads into `<tbody>`

Use these attributes on the component root:

- `data-jbs-stream-mode="replace|prepend|append"`
- `data-jbs-stream-max-rows="N"` (optional row cap for append/prepend)
- `data-jbs-stream-pause-when-hidden="true|false"` (buffer when off-screen)
- `data-jbs-stream-buffer-max="N"` (max buffered stream events)

The runtime supports a v1 delta payload for stream patches:

```json
{
  "v": 1,
  "target": "orders-table",
  "seq": 42,
  "snapshot": "orders-42",
  "cache_scope": "orders:tenant-a",
  "mode": "replace",
  "ops": [
    {"op": "update", "id": "order-1001", "html": "<tr data-jbs-row-id=\"order-1001\">...</tr>"},
    {"op": "move", "id": "order-1004", "before_id": "order-1002"},
    {"op": "delete", "id": "order-1007"}
  ],
  "meta": {
    "subtitle": "Filtered to queued",
    "total_rows": 17,
    "page": 1,
    "page_count": 2
  }
}
```

Supported row operations in `ops`:

- `create`
- `read` (position-only move with no HTML change)
- `update`
- `delete`
- `upsert`
- `move`

Ordering and safety behavior:

- `seq` deduplicates stale events.
- Sequence gaps trigger automatic refresh/resync.
- `resync: true` forces refresh.
- `cache_scope` changes trigger refresh and snapshot reset.
- Invalid ops/fragments fall back to full refresh instead of partial corruption.

Legacy append/prepend payloads with `row` or `rows` HTML are still supported:

```json
{
  "target": "live-table",
  "mode": "prepend",
  "row": "<tr><td>event-42</td><td>sse</td></tr>",
  "max_rows": 50
}
```

### Filter forms

Forms inside a component become table filters when marked with `data-jbs-form`.
On submit, the runtime:

- serializes the form fields into component state
- merges them onto the current state
- resets `page` back to `1`
- requests a full fragment replacement

That means filters preserve current sort and page size unless the form explicitly
changes them.

### Row actions

Row actions use the same action channel as paging and sorting. A row-level button
should use `data-jbs-action="row"` and can include:

- `data-jbs-row-id`
- `data-jbs-intent`
- `data-jbs-patch`

The runtime merges those fields into the current component state before issuing
the request. That gives the server one consistent request model for paging,
sorting, filtering, and row-level intents like archive, approve, retry, or open.

Transient row-action fields such as `row_id` and `intent` should be treated as
one-shot request data by the server and should not be persisted back into the
component state after rendering the replacement fragment.

### Action menus

`action_menu(...)` is the next opinionated primitive after `table(...)`. It
renders a Bootstrap-styled dropdown surface without relying on Bootstrap's JS.

- Menus open and close through the first-party runtime.
- Clicking outside the menu or pressing `Escape` dismisses it.
- Menu items can be normal links or runtime actions such as `row` intents.
- Menus are designed for per-row actions, overflow actions, and compact command surfaces.

### Persistence

The root component declares persistence with `data-jbs-persist`:

- `memory`: keep state only in the in-page runtime store
- `querystring`: mirror declared state keys into the URL query string
- `session`: persist state in `sessionStorage`
- `header`: send/read state via `X-JBS-State` request header

Use `data-jbs-state-keys` to define which keys are synchronized when using
querystring or session persistence. For tables, the macro defaults to:

- `page`
- `page_size`
- `sort_by`
- `sort_dir`
- `query`

## Quickstart

Register the packaged macros with your Jinja environment:

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

from jinja_bootstrap_spa.macros.bootstrap import register_bootstrap_macros

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)
register_bootstrap_macros(env)
```

Render a server-driven table component:

```jinja
{% extends "jinja_bootstrap_spa/base.html" %}
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}

{% block title %}Orders{% endblock %}

{% block content %}
  <main class="container py-4">
    {{
      ui.table(
        "orders-table",
        "/components/orders",
        columns=[
          {"key": "number", "label": "Order", "sortable": true},
          {"key": "customer", "label": "Customer", "sortable": true},
          {"key": "status", "label": "Status", "sortable": false},
          {"key": "total", "label": "Total", "sortable": true, "cell_class": "text-end"},
        ],
        rows=rows,
        state=table_state,
        total_rows=total_rows,
        persist="header",
        state_keys=["page", "page_size", "sort_by", "sort_dir", "query", "status"],
        title="Orders",
        subtitle="Server-rendered table with client-side component replacement.",
        toolbar='
          <form class="d-flex gap-2" data-jbs-form>
            <input class="form-control form-control-sm" name="query" placeholder="Search orders">
            <button class="btn btn-sm btn-primary" type="submit">Apply</button>
          </form>
        '
      )
    }}
  </main>
{% endblock %}

{% block spa_runtime %}
  <script
    type="module"
    src="{{ url_for('static', filename='jinja-bootstrap-spa.js') }}"
  ></script>
{% endblock %}
```

### Go MiniJinja Quickstart

The Go companion exposes the same packaged template names:

- `jinja_bootstrap_spa/bootstrap_macros.html`
- `jinja_bootstrap_spa/base.html`

```go
package main

import (
	"fmt"
	"log"
	"testing/fstest"

	jbs "github.com/abartrim/jinja-bootstrap-spa"
)

func main() {
	env, err := jbs.NewEnvironment(jbs.Options{
		TemplateFS: fstest.MapFS{
			"pages/orders.html": {
				Data: []byte(`{% extends "jinja_bootstrap_spa/base.html" %}
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{% block title %}Orders{% endblock %}
{% block content %}
  <main class="container py-4">
    {{ ui.button("Refresh", jbs_action="refresh", jbs_component_ref="orders-table") }}
  </main>
{% endblock %}`),
			},
		},
		URLFor: jbs.StaticURLFor("/static"),
	})
	if err != nil {
		log.Fatal(err)
	}

	tmpl, err := env.GetTemplate("pages/orders.html")
	if err != nil {
		log.Fatal(err)
	}

	html, err := tmpl.Render(nil)
	if err != nil {
		log.Fatal(err)
	}

	fmt.Println(html)
}
```

The Go layer is intentionally small:

- Python remains the canonical macro source.
- Go extracts `BOOTSTRAP_MACROS` directly from
  `src/jinja_bootstrap_spa/macros/bootstrap.py` so the packaged macro surface stays aligned.
- `url_for(...)` is opt-in through `Options.URLFor`; `StaticURLFor(...)` covers the common
  `url_for("static", filename=...)` case.
- Flask globals beyond `url_for` are not emulated by default. Add them through
  `Options.Globals` or your own MiniJinja environment setup when specific templates need them.

Render a row action menu inside a table cell:

```jinja
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}

{{
  ui.action_menu(
    order.id ~ "-actions",
    items=[
      {"label": "Inspect Order", "href": "/orders/" ~ order.id},
      {"divider": true},
      {
        "label": "Archive Order",
        "jbs_action": "row",
        "jbs_row_id": order.id,
        "jbs_intent": "archive",
        "variant": "danger"
      }
    ]
  )
}}
```

Build a filter form with the packaged primitives:

```jinja
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}

{% set filter_body %}
  <form class="vstack gap-3" data-jbs-form>
    <div class="d-flex flex-wrap align-items-end gap-2">
      {{ ui.form_input("query", value=table_state.query or "", placeholder="Search orders", class_name="form-control-sm mb-0") }}
      {{ ui.filter_multi_select("status", "Status", [{"value":"queued","label":"Queued"},{"value":"open","label":"Open"},{"value":"archived","label":"Archived"}], selected_values=[table_state.status] if table_state.status else []) }}
      {{ ui.filter_single_select("page_size", "Page Size", [{"value":"10","label":"10 rows"},{"value":"25","label":"25 rows"},{"value":"50","label":"50 rows"}], selected_value=table_state.page_size or 10) }}
      {{ ui.date_range_picker(from_name="from_ts", to_name="to_ts", from_value=table_state.from_ts or "", to_value=table_state.to_ts or "") }}
    </div>
    {{ ui.sql_filter_input(name="sql", value=table_state.sql or "", hints_endpoint="/api/sql-hints", validate_endpoint="/api/sql-validate") }}
    <button class="btn btn-sm btn-primary align-self-start" type="submit">Apply</button>
  </form>
{% endset %}

{{ ui.filter_accordion("orders-filters", body=filter_body, active_badge=true) }}
```

A matching Flask endpoint returns the replacement fragment:

```python
from flask import Flask, render_template, request

app = Flask(__name__)


@app.get("/components/orders")
def orders_table() -> str:
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 10))
    sort_by = request.args.get("sort_by", "number")
    sort_dir = request.args.get("sort_dir", "asc")
    query = request.args.get("query", "")

    rows, total_rows = load_orders(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_dir=sort_dir,
        query=query,
    )

    return render_template(
        "partials/orders_table.html",
        rows=rows,
        total_rows=total_rows,
        table_state={
            "page": page,
            "page_size": page_size,
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "query": query,
        },
    )
```

## Browser Runtime

The browser runtime is authored in TypeScript and compiled into:

- `src/jinja_bootstrap_spa/static/jinja-bootstrap-spa.js`
- `src/jinja_bootstrap_spa/static/jinja-bootstrap-spa.d.ts`

That choice is deliberate. Once the library owns client-side state and component
replacement semantics, the runtime is a public API and should be typed as one.

Load the generated runtime as an ES module in the browser:

```html
<script type="module" src="/static/jinja-bootstrap-spa.js"></script>
```

The initial runtime supports:

- hydrating component state from `data-jbs-state`
- lazy hydration via `data-jbs-lazy`
- optional state persistence through query string or session storage
- history back/forward re-sync for querystring-persisted components
- click-driven refresh, sort, and page actions
- form-driven state patches through `data-jbs-form`
- row actions through `data-jbs-row-id` and `data-jbs-intent`
- multi-select, disclosure, and date-range picker primitives
- SQL/regex assist inputs with hint + validation endpoints
- SSE stream modes (`replace`, `append`, `prepend`) with hidden-state buffering
- HTML fragment fetching with `X-JBS-*` headers
- root component replacement with lifecycle events

## Current Surface Area

- [src/jinja_bootstrap_spa/macros/bootstrap.py](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/src/jinja_bootstrap_spa/macros/bootstrap.py)
  Bootstrap macros, including the first opinionated `table()` component.
- [src/jinja_bootstrap_spa/runtime/components.py](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/src/jinja_bootstrap_spa/runtime/components.py)
  Python helpers for `data-jbs-*` attributes.
- [frontend/src/jinja-bootstrap-spa.ts](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/frontend/src/jinja-bootstrap-spa.ts)
  The TypeScript browser runtime source.
- [src/jinja_bootstrap_spa/templates/base.html](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/src/jinja_bootstrap_spa/templates/base.html)
  Bootstrap base template with a dedicated runtime block.

## What Comes Next

The table component is the forcing function, not the final scope. The next
generic work should continue building on the same runtime contract without
becoming app-specific:

- chart/dashboard composition helpers that stay data-library agnostic
- upload and file-management surfaces for server-driven workflows
- more opinionated batch-review shells built on the current selection contract
- additional explorer patterns once a second consumer proves the need

## Contribution Guidance

When adding macros or runtime features:

- prefer named arguments and explicit state fields
- keep the server as the owner of canonical markup
- treat component replacement as the primitive, not arbitrary DOM patching
- avoid feature growth that turns the runtime into a generic SPA framework
