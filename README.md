# jinja-bootstrap-spa

`jinja-bootstrap-spa` is a Python-first UI framework for building server-rendered
applications with consistent Bootstrap styling and a lightweight SPA-like runtime.

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
npm run build:js
npm run typecheck:js
pytest
```

The browser-level tests use Playwright's Python bindings and expect Chromium to
be installed through `python -m playwright install chromium`.

## Wrapper Dev App

A standalone Flask wrapper app lives in
[examples/table_app](/Users/abartrim/Documents/dev/jinja-bootstrap-spa/examples/table_app).
Use it to iterate on runtime behavior manually while developing new components.

Run it with:

```bash
npm run build:js
.venv/bin/python examples/table_app/app.py
```

Then open [http://127.0.0.1:5000](http://127.0.0.1:5000).

The dev app includes an SSE-backed orders table and row action menus. Click
`Simulate SSE Update` to watch the table refresh in place without a full reload.

## Runtime Model

Each interactive fragment is a server-rendered component root:

- `data-jbs-component`
- `data-jbs-endpoint`
- `data-jbs-target`
- `data-jbs-state`
- `data-jbs-key`

Interactive controls inside the component emit actions such as:

- `data-jbs-action="refresh"`
- `data-jbs-action="sort"`
- `data-jbs-action="page"`
- `data-jbs-patch='{"status":"open"}'`

The browser runtime sends the component state to the endpoint, expects an HTML
fragment back, and replaces the component root in one swap. That keeps the server
as the source of truth while still enabling SPA-like interactions.

## Table Contract

The table component is the first fully specified contract in the framework.

### Request shape

Table requests use normal query params. The reserved keys are:

- `page`
- `page_size`
- `sort_by`
- `sort_dir`
- `query`

Additional filter fields are allowed and should be treated as table-specific state.
For example, a filtered orders table may also send `status=open` and `owner=ops`.

The runtime also sends these headers:

- `X-JBS-Request: true`
- `X-JBS-Component: table`
- `X-JBS-Action: refresh|filter|page|sort|row`

On the Python side, use `parse_table_state(...)` to normalize incoming state
before querying data:

```python
from jinja_bootstrap_spa import parse_table_state


state = parse_table_state(
    request.args,
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
        persist="querystring",
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

<form class="d-flex flex-wrap align-items-end gap-2" data-jbs-form>
  {{
    ui.form_input(
      "query",
      value=table_state.query or "",
      placeholder="Search orders",
      class_name="form-control-sm mb-0"
    )
  }}
  {{
    ui.form_select(
      "status",
      [
        {"value": "queued", "label": "Queued"},
        {"value": "open", "label": "Open"},
        {"value": "archived", "label": "Archived"},
      ],
      value=table_state.status or "",
      placeholder="All statuses",
      class_name="form-select-sm mb-0"
    )
  }}
  {{
    ui.form_select(
      "page_size",
      [
        {"value": "10", "label": "10 rows"},
        {"value": "25", "label": "25 rows"},
        {"value": "50", "label": "50 rows"},
      ],
      value=table_state.page_size or 10,
      class_name="form-select-sm mb-0"
    )
  }}
  <button class="btn btn-sm btn-primary" type="submit">Apply</button>
</form>
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
- optional state persistence through query string or session storage
- click-driven refresh, sort, and page actions
- form-driven state patches through `data-jbs-form`
- row actions through `data-jbs-row-id` and `data-jbs-intent`
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

The table component is the forcing function, not the final scope. Later components
should build on the same runtime contract:

- menus and command surfaces
- filterable card lists
- detail panels and inline edit flows
- modal and drawer components
- richer table features such as row actions, selection, and pinned columns

## Contribution Guidance

When adding macros or runtime features:

- prefer named arguments and explicit state fields
- keep the server as the owner of canonical markup
- treat component replacement as the primitive, not arbitrary DOM patching
- avoid feature growth that turns the runtime into a generic SPA framework
