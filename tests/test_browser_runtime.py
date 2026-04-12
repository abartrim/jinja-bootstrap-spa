"""End-to-end browser tests for the jinja-bootstrap-spa runtime."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from queue import Empty, Queue
from threading import Lock, Thread
from typing import Any

import pytest
from flask import (
    Flask,
    Response,
    render_template_string,
    request,
    send_file,
    stream_with_context,
)
from jinja2 import ChoiceLoader, PackageLoader
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from jinja_bootstrap_spa import parse_table_state, register_bootstrap_macros


def _seed_orders() -> list[dict[str, Any]]:
    customers = [
        "Ada Lovelace",
        "Linus Torvalds",
        "Grace Hopper",
        "Ken Thompson",
        "Margaret Hamilton",
        "Barbara Liskov",
        "Donald Knuth",
        "Edsger Dijkstra",
        "Radia Perlman",
        "John Carmack",
        "Guido van Rossum",
        "Leslie Lamport",
    ]
    statuses = ["queued", "open", "queued", "open", "archived"]
    return [
        {
            "id": f"order-{1000 + index}",
            "number": f"#{1000 + index}",
            "customer": customer,
            "status": statuses[index % len(statuses)],
        }
        for index, customer in enumerate(customers, start=1)
    ]


ORDERS = _seed_orders()
LAST_PUSH_MESSAGE = ""
PUSH_COUNTER = 0
SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
SUBSCRIBERS_LOCK = Lock()
LIVE_ROWS = [
    {"entry": "boot complete", "source": "runtime"},
    {"entry": "table hydrated", "source": "runtime"},
]
LIVE_SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
LIVE_SUBSCRIBERS_LOCK = Lock()
LIVE_PUSH_COUNTER = 0
APPEND_ROWS = [
    {"entry": "append channel online", "source": "runtime"},
    {"entry": "append stream ready", "source": "runtime"},
]
APPEND_SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
APPEND_SUBSCRIBERS_LOCK = Lock()
APPEND_PUSH_COUNTER = 0
SESSION_ROWS = [
    {"name": "Alerts", "owner": "SRE"},
    {"name": "Incidents", "owner": "On-call"},
    {"name": "Traces", "owner": "Platform"},
    {"name": "Errors", "owner": "Backend"},
]

PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Orders</title>
  </head>
  <body>
    <main class="container py-4">
    <div class="d-flex gap-2 mb-3">
      <button class="btn btn-outline-secondary"
              type="button"
              data-jbs-overlay-open="runtime-modal">
        Open Modal
      </button>
      <button class="btn btn-outline-secondary"
              type="button"
              data-jbs-overlay-open="orders-drawer">
        Open Drawer
      </button>
      <button class="btn btn-outline-secondary"
              type="button"
              id="push-live-row">
        Push Prepend Row
      </button>
      <button class="btn btn-outline-secondary"
              type="button"
              id="push-append-row">
        Push Append Row
      </button>
    </div>
    {{ table_markup|safe }}
    <div class="mt-4">
      {{ live_table_markup|safe }}
    </div>
    <div class="mt-4">
      {{ live_append_table_markup|safe }}
    </div>
    <div class="mt-4">
      {{ session_table_markup|safe }}
    </div>
    <div class="mt-4">
      {{ cancel_demo_markup|safe }}
    </div>
    <div style="height: 1200px;"></div>
    <section id="lazy-summary"
             class="card p-3"
             data-jbs-component="lazy-summary"
             data-jbs-endpoint="/components/lazy-summary"
             data-jbs-target="#lazy-summary"
             data-jbs-key="lazy-summary"
             data-jbs-persist="memory"
             data-jbs-stream-mode="replace"
             data-jbs-stream-pause-when-hidden="false"
             data-jbs-stream-buffer-max="50"
             data-jbs-state="{}"
             data-jbs-lazy="true"
             data-jbs-lazy-fetch="true">
      Loading lazy summary…
    </section>
    {{ overlay_markup|safe }}
    </main>
    <script type="module" src="/static/jinja-bootstrap-spa.js"></script>
    <script type="module">
      const pushLiveRow = document.getElementById("push-live-row");
      pushLiveRow?.addEventListener("click", async () => {
        await fetch("/admin/push-live-row", { method: "POST" });
      });
      const pushAppendRow = document.getElementById("push-append-row");
      pushAppendRow?.addEventListener("click", async () => {
        await fetch("/admin/push-live-append-row", { method: "POST" });
      });
    </script>
  </body>
</html>
"""

TABLE_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{% set selected_statuses = [state.status] if state.status else [] %}
{% set filter_body %}
  <form class="vstack gap-3" data-jbs-form>
    <div class="d-flex flex-wrap align-items-end gap-2">
      {{
        ui.form_input(
          "query",
          value=state.query or "",
          placeholder="Search orders",
          class_name="form-control-sm mb-0"
        )
      }}
      {{
        ui.autocomplete(
          "customer",
          "/fragments/customer-options",
          value=state.customer or "",
          display_value=state.customer or "",
          placeholder="Filter customer",
          class_name="mb-0",
          input_class="form-control-sm"
        )
      }}
      {{
        ui.filter_multi_select(
          "status",
          "Status",
          [
            {"value": "queued", "label": "Queued"},
            {"value": "open", "label": "Open"},
            {"value": "archived", "label": "Archived"},
          ],
          selected_values=selected_statuses,
          class_name="mb-0"
        )
      }}
      {{
        ui.filter_single_select(
          "page_size",
          "Page Size",
          [
            {"value": "4", "label": "4 rows"},
            {"value": "8", "label": "8 rows"},
          ],
          selected_value=state.page_size or 4,
          class_name="mb-0"
        )
      }}
      {{
        ui.date_range_picker(
          from_name="from_ts",
          to_name="to_ts",
          from_value=state.from_ts or "",
          to_value=state.to_ts or "",
          class_name="mb-0"
        )
      }}
    </div>
    {{
      ui.sql_filter_input(
        name="sql",
        value=state.sql or "",
        hints_endpoint="/api/sql-hints",
        validate_endpoint="/api/sql-validate"
      )
    }}
    {{
      ui.regex_filter_input(
        name="regex",
        value=state.regex or "",
        validate_endpoint="/api/validate-regex"
      )
    }}
    <button class="btn btn-sm btn-primary align-self-start" type="submit">Apply</button>
  </form>
{% endset %}

{% set toolbar %}
  <div class="vstack gap-3">
    {% if status_notice %}
      {{
        ui.status_region(
          "orders-status-region",
          title=status_notice.title,
          message=status_notice.message,
          variant=status_notice.variant,
          class_name="mb-0"
        )
      }}
    {% endif %}
    {{
      ui.tabs(
        "orders-status-tabs",
        [
          {
            "label": "All",
            "value": "__all__",
            "jbs_action": "filter",
            "jbs_patch": {"status": none, "page": 1}
          },
          {
            "label": "Queued",
            "value": "queued",
            "jbs_action": "filter",
            "jbs_patch": {"status": "queued", "page": 1}
          },
          {
            "label": "Open",
            "value": "open",
            "jbs_action": "filter",
            "jbs_patch": {"status": "open", "page": 1}
          },
          {
            "label": "Archived",
            "value": "archived",
            "jbs_action": "filter",
            "jbs_patch": {"status": "archived", "page": 1}
          },
        ],
        active=state.status or "__all__",
        class_name="small"
      )
    }}
    {{
      ui.filter_accordion(
        "orders-filters",
        body=filter_body,
        active_badge=(
          state.status or state.query or state.customer or state.sql or state.regex
        )
      )
    }}
  </div>
{% endset %}

{{
  ui.table(
    "orders-table",
    "/components/orders",
    columns=[
      {"key": "number", "label": "Order", "sortable": true},
      {"key": "customer", "label": "Customer", "sortable": true},
      {"key": "status", "label": "Status", "sortable": false},
      {
        "key": "actions",
        "label": "Actions",
        "sortable": false,
        "html": true,
        "cell_class": "text-end"
      },
    ],
    rows=rows,
    state=state,
    total_rows=total_rows,
    persist="querystring",
    state_keys=[
      "page",
      "page_size",
      "sort_by",
      "sort_dir",
      "query",
      "customer",
      "status",
      "from_ts",
      "to_ts",
      "sql",
      "regex"
    ],
    title="Orders",
    subtitle=subtitle,
    toolbar=toolbar,
    sse_endpoint="/events/orders"
  )
}}
"""

ACTION_MENU_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{{
  ui.action_menu(
    menu_id,
    label="Actions",
    items=items,
    variant="outline-secondary",
    size="sm",
    align="end"
  )
}}
"""

LIVE_TABLE_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{{
  ui.table(
    "live-table",
    "/components/live-table",
    columns=[
      {"key": "entry", "label": "Entry", "sortable": false},
      {"key": "source", "label": "Source", "sortable": false},
    ],
    rows=rows,
    state={"page": 1, "page_size": 3, "sort_by": "", "sort_dir": "asc"},
    total_rows=rows|length,
    title="Live Stream Table",
    subtitle="SSE prepend mode keeps newest events on top.",
    stream_mode="prepend",
    stream_max_rows=3,
    stream_pause_when_hidden=true,
    stream_buffer_max=20,
    sse_endpoint="/events/live-table",
    sse_event="refresh"
  )
}}
"""

LIVE_APPEND_TABLE_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{{
  ui.table(
    "live-append-table",
    "/components/live-append-table",
    columns=[
      {"key": "entry", "label": "Entry", "sortable": false},
      {"key": "source", "label": "Source", "sortable": false},
    ],
    rows=rows,
    state={"page": 1, "page_size": 3, "sort_by": "", "sort_dir": "asc"},
    total_rows=rows|length,
    title="Append Stream Table",
    subtitle="SSE append mode keeps newest events at the bottom.",
    stream_mode="append",
    stream_max_rows=3,
    stream_pause_when_hidden=false,
    stream_buffer_max=20,
    sse_endpoint="/events/live-append-table",
    sse_event="refresh"
  )
}}
"""

SESSION_TABLE_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{% set toolbar %}
  <form class="d-flex flex-wrap align-items-end gap-2" data-jbs-form>
    {{
      ui.filter_single_select(
        "page_size",
        "Rows",
        [
          {"value": "2", "label": "2 rows"},
          {"value": "4", "label": "4 rows"},
        ],
        selected_value=state.page_size or 2,
        auto_submit=false
      )
    }}
    <button class="btn btn-sm btn-primary" type="submit">Apply</button>
  </form>
{% endset %}
{{
  ui.table(
    "session-table",
    "/components/session-table",
    columns=[
      {"key": "name", "label": "View", "sortable": false},
      {"key": "owner", "label": "Owner", "sortable": false},
    ],
    rows=rows,
    state=state,
    total_rows=total_rows,
    title="Session Persistence Table",
    subtitle="State should survive full page reloads via sessionStorage.",
    toolbar=toolbar,
    persist="session",
    state_keys=["page", "page_size"]
  )
}}
"""

CANCEL_DEMO_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{% set controls %}
  <div class="d-flex gap-2">
    {{
      ui.button(
        "Slow Request",
        variant="outline-secondary",
        size="sm",
        jbs_action="refresh",
        jbs_component_ref="cancel-demo",
        jbs_patch={"value": "slow", "delay_ms": 350}
      )
    }}
    {{
      ui.button(
        "Fast Request",
        variant="outline-primary",
        size="sm",
        jbs_action="refresh",
        jbs_component_ref="cancel-demo",
        jbs_patch={"value": "fast", "delay_ms": 20}
      )
    }}
  </div>
{% endset %}
{% set body %}
  <p class="mb-2">
    Trigger a slow request then a fast request. The runtime should keep fast state.
  </p>
  <dl class="row mb-0">
    <dt class="col-sm-3 text-body-secondary">Value</dt>
    <dd class="col-sm-9" id="cancel-demo-value">{{ value }}</dd>
    <dt class="col-sm-3 text-body-secondary">Delay</dt>
    <dd class="col-sm-9">{{ delay_ms }} ms</dd>
  </dl>
{% endset %}
<section id="cancel-demo"
         data-jbs-component="cancel-demo"
         data-jbs-endpoint="/components/cancel-demo"
         data-jbs-target="#cancel-demo"
         data-jbs-key="cancel-demo"
         data-jbs-swap="outerHTML"
         data-jbs-persist="memory"
         data-jbs-stream-mode="replace"
         data-jbs-stream-pause-when-hidden="false"
         data-jbs-stream-buffer-max="50"
         data-jbs-state='{{ {"value": value, "delay_ms": delay_ms}|tojson }}'>
  {{
    ui.card(
      title="Request Cancellation Demo",
      body=(controls ~ body)|safe,
      class_name="shadow-sm"
    )
  }}
</section>
"""

AUTOCOMPLETE_OPTIONS_TEMPLATE = """
{% if matches %}
  {% for customer in matches %}
    <button
      class="dropdown-item"
      type="button"
      role="option"
      data-jbs-autocomplete-option
      data-jbs-autocomplete-value="{{ customer }}"
      data-jbs-autocomplete-label="{{ customer }}">
      {{ customer }}
    </button>
  {% endfor %}
{% else %}
  <div class="dropdown-item-text text-body-secondary small">
    No matching customers.
  </div>
{% endif %}
"""

OVERLAYS_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{{
  ui.modal(
    "runtime-modal",
    title="Runtime Notes",
    body="<p>Server-rendered modal content.</p>"
  )
}}
{{
  ui.drawer(
    "orders-drawer",
    title="Orders Drawer",
    body="<p>Server-rendered drawer content.</p>"
  )
}}
"""


def _publish_orders_event(message: str, patch: dict[str, Any] | None = None) -> None:
    payload = {"action": "refresh", "target": "orders-table", "patch": patch or {}}
    with SUBSCRIBERS_LOCK:
        subscribers = list(SUBSCRIBERS)
    for subscriber in subscribers:
        subscriber.put(payload)


def _publish_live_event(payload: dict[str, Any]) -> None:
    with LIVE_SUBSCRIBERS_LOCK:
        subscribers = list(LIVE_SUBSCRIBERS)
    for subscriber in subscribers:
        subscriber.put(payload)


def _publish_append_event(payload: dict[str, Any]) -> None:
    with APPEND_SUBSCRIBERS_LOCK:
        subscribers = list(APPEND_SUBSCRIBERS)
    for subscriber in subscribers:
        subscriber.put(payload)


def _render_live_row(entry: str, source: str) -> str:
    safe_entry = entry.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_source = source.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return f"<tr><td>{safe_entry}</td><td>{safe_source}</td></tr>"


def _build_live_table(app: Flask) -> str:
    template = app.jinja_env.from_string(LIVE_TABLE_TEMPLATE)
    return template.render(rows=list(LIVE_ROWS))


def _build_live_append_table(app: Flask) -> str:
    template = app.jinja_env.from_string(LIVE_APPEND_TABLE_TEMPLATE)
    return template.render(rows=list(APPEND_ROWS))


def _build_session_table(app: Flask) -> str:
    state = parse_table_state(
        request.args,
        default_sort_by="name",
        default_page_size=2,
        allowed_page_sizes=(2, 4),
        filter_keys=(),
    )
    sorted_rows = sorted(SESSION_ROWS, key=lambda row: row["name"])
    page = int(state["page"])
    page_size = int(state["page_size"])
    start = (page - 1) * page_size
    end = start + page_size
    template = app.jinja_env.from_string(SESSION_TABLE_TEMPLATE)
    return template.render(
        rows=sorted_rows[start:end],
        total_rows=len(sorted_rows),
        state=state,
    )


def _build_cancel_demo(app: Flask) -> str:
    value = str(request.args.get("value", "idle"))
    delay_ms = int(request.args.get("delay_ms", 0) or 0)
    delay_ms = max(0, min(delay_ms, 1000))
    if delay_ms > 0:
        time.sleep(delay_ms / 1000)
    template = app.jinja_env.from_string(CANCEL_DEMO_TEMPLATE)
    return template.render(value=value, delay_ms=delay_ms)


def _sort_orders(
    rows: list[dict[str, Any]], sort_by: str, sort_dir: str
) -> list[dict[str, Any]]:
    reverse = sort_dir == "desc"
    if sort_by not in {"number", "customer", "status"}:
        sort_by = "number"
    return sorted(rows, key=lambda row: str(row[sort_by]), reverse=reverse)


def _filter_orders(
    rows: list[dict[str, Any]],
    query: str,
    status: str,
    customer: str,
    regex_filter: str,
) -> list[dict[str, Any]]:
    next_rows = rows
    if query:
        query_lower = query.lower()
        next_rows = [
            row
            for row in next_rows
            if query_lower in row["number"].lower()
            or query_lower in row["customer"].lower()
        ]
    if status:
        next_rows = [row for row in next_rows if row["status"] == status]
    if customer:
        next_rows = [
            row for row in next_rows if row["customer"].lower() == customer.lower()
        ]
    if regex_filter:
        try:
            pattern = re.compile(regex_filter, re.IGNORECASE)
        except re.error:
            return next_rows
        next_rows = [
            row
            for row in next_rows
            if pattern.search(row["number"]) or pattern.search(row["customer"])
        ]
    return next_rows


def _customer_matches(query: str) -> list[str]:
    query_lower = query.strip().lower()
    customers = sorted({str(order["customer"]) for order in ORDERS})
    if not query_lower:
        return customers[:8]
    return [customer for customer in customers if query_lower in customer.lower()][:8]


def _render_actions(app: Flask, order_id: str, status: str) -> str:
    intent = "restore" if status == "archived" else "archive"
    label = "Restore Order" if status == "archived" else "Archive Order"
    return render_template_string(
        ACTION_MENU_TEMPLATE,
        menu_id=f"{order_id}-actions",
        items=[
            {
                "label": "Inspect Order",
                "href": f"/?query=%23{order_id.split('-')[-1]}",
            },
            {"divider": True},
            {
                "label": label,
                "jbs_action": "row",
                "jbs_row_id": order_id,
                "jbs_intent": intent,
                "variant": "danger",
            },
        ],
    )


def _apply_row_action(row_id: str, intent: str) -> str | None:
    for order in ORDERS:
        if order["id"] != row_id:
            continue
        if intent == "archive":
            order["status"] = "archived"
        elif intent == "restore":
            order["status"] = "queued"
        else:
            return None

        message = f"Last action: {intent} {row_id}"
        _publish_orders_event(message)
        return message
    return None


def _build_table(app: Flask) -> str:
    state = parse_table_state(
        request.args,
        default_sort_by="number",
        default_page_size=4,
        allowed_page_sizes=(4, 8),
        filter_keys=(
            "status",
            "customer",
            "row_id",
            "intent",
            "from_ts",
            "to_ts",
            "sql",
            "regex",
        ),
    )

    action_message = None
    row_id = str(state.get("row_id", "") or "")
    intent = str(state.get("intent", "") or "")
    if row_id and intent:
        action_message = _apply_row_action(row_id, intent)
        state.pop("row_id", None)
        state.pop("intent", None)

    filtered_rows = _filter_orders(
        ORDERS,
        query=str(state.get("query", "")),
        status=str(state.get("status", "")),
        customer=str(state.get("customer", "")),
        regex_filter=str(state.get("regex", "")),
    )
    sorted_rows = _sort_orders(
        filtered_rows,
        sort_by=str(state.get("sort_by", "number")),
        sort_dir=str(state.get("sort_dir", "asc")),
    )

    page = int(state["page"])
    page_size = int(state["page_size"])
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = sorted_rows[start:end]

    rows = [
        {
            **row,
            "actions": _render_actions(app, row["id"], row["status"]),
        }
        for row in page_rows
    ]

    subtitle = LAST_PUSH_MESSAGE or "Server-driven component contract."
    status_notice = None
    if LAST_PUSH_MESSAGE:
        status_notice = {
            "title": "Live Update",
            "message": LAST_PUSH_MESSAGE,
            "variant": "info",
        }
    if action_message:
        subtitle = action_message
        status_notice = {
            "title": "Row Action",
            "message": action_message,
            "variant": "success",
        }

    template = app.jinja_env.from_string(TABLE_TEMPLATE)
    return template.render(
        rows=rows,
        total_rows=len(sorted_rows),
        state=state,
        subtitle=subtitle,
        status_notice=status_notice,
    )


def create_test_app() -> Flask:
    app = Flask(__name__)
    app.jinja_loader = ChoiceLoader([PackageLoader("jinja_bootstrap_spa", "templates")])
    register_bootstrap_macros(app.jinja_env)

    @app.get("/")
    def index() -> str:
        table_markup = _build_table(app)
        live_table_markup = _build_live_table(app)
        live_append_table_markup = _build_live_append_table(app)
        session_table_markup = _build_session_table(app)
        cancel_demo_markup = _build_cancel_demo(app)
        overlay_markup = render_template_string(OVERLAYS_TEMPLATE)
        return render_template_string(
            PAGE_TEMPLATE,
            table_markup=table_markup,
            live_table_markup=live_table_markup,
            live_append_table_markup=live_append_table_markup,
            session_table_markup=session_table_markup,
            cancel_demo_markup=cancel_demo_markup,
            overlay_markup=overlay_markup,
        )

    @app.get("/components/orders")
    def orders_component() -> str:
        return _build_table(app)

    @app.get("/components/live-table")
    def live_table_component() -> str:
        return _build_live_table(app)

    @app.get("/components/live-append-table")
    def live_append_table_component() -> str:
        return _build_live_append_table(app)

    @app.get("/components/session-table")
    def session_table_component() -> str:
        return _build_session_table(app)

    @app.get("/components/cancel-demo")
    def cancel_demo_component() -> str:
        return _build_cancel_demo(app)

    @app.get("/components/lazy-summary")
    def lazy_summary_component() -> str:
        return (
            '<section id="lazy-summary" '
            'class="card p-3 border-success-subtle" '
            'data-jbs-component="lazy-summary" '
            'data-jbs-endpoint="/components/lazy-summary" '
            'data-jbs-target="#lazy-summary" '
            'data-jbs-key="lazy-summary" '
            'data-jbs-persist="memory" '
            'data-jbs-stream-mode="replace" '
            'data-jbs-stream-pause-when-hidden="false" '
            'data-jbs-stream-buffer-max="50" '
            "data-jbs-state='{}'>"
            '<strong class="text-success">Lazy summary ready.</strong> '
            '<span class="text-body-secondary">Loaded on first viewport entry.</span>'
            "</section>"
        )

    @app.get("/events/orders")
    def orders_events() -> Response:
        queue: Queue[dict[str, Any]] = Queue()
        with SUBSCRIBERS_LOCK:
            SUBSCRIBERS.append(queue)

        @stream_with_context
        def event_stream() -> Any:
            try:
                yield "retry: 1000\n\n"
                while True:
                    try:
                        payload = queue.get(timeout=10)
                        yield f"event: refresh\ndata: {json.dumps(payload)}\n\n"
                    except Empty:
                        yield ": keep-alive\n\n"
            finally:
                with SUBSCRIBERS_LOCK:
                    if queue in SUBSCRIBERS:
                        SUBSCRIBERS.remove(queue)

        return Response(
            event_stream(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.get("/events/live-table")
    def live_table_events() -> Response:
        queue: Queue[dict[str, Any]] = Queue()
        with LIVE_SUBSCRIBERS_LOCK:
            LIVE_SUBSCRIBERS.append(queue)

        @stream_with_context
        def event_stream() -> Any:
            try:
                yield "retry: 1000\n\n"
                while True:
                    try:
                        payload = queue.get(timeout=10)
                        yield f"event: refresh\ndata: {json.dumps(payload)}\n\n"
                    except Empty:
                        yield ": keep-alive\n\n"
            finally:
                with LIVE_SUBSCRIBERS_LOCK:
                    if queue in LIVE_SUBSCRIBERS:
                        LIVE_SUBSCRIBERS.remove(queue)

        return Response(
            event_stream(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.get("/events/live-append-table")
    def live_append_table_events() -> Response:
        queue: Queue[dict[str, Any]] = Queue()
        with APPEND_SUBSCRIBERS_LOCK:
            APPEND_SUBSCRIBERS.append(queue)

        @stream_with_context
        def event_stream() -> Any:
            try:
                yield "retry: 1000\n\n"
                while True:
                    try:
                        payload = queue.get(timeout=10)
                        yield f"event: refresh\ndata: {json.dumps(payload)}\n\n"
                    except Empty:
                        yield ": keep-alive\n\n"
            finally:
                with APPEND_SUBSCRIBERS_LOCK:
                    if queue in APPEND_SUBSCRIBERS:
                        APPEND_SUBSCRIBERS.remove(queue)

        return Response(
            event_stream(),
            mimetype="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
        )

    @app.get("/fragments/customer-options")
    def customer_options() -> str:
        query = str(request.args.get("q", "") or "")
        return render_template_string(
            AUTOCOMPLETE_OPTIONS_TEMPLATE, matches=_customer_matches(query)
        )

    @app.post("/admin/push-update")
    def push_update() -> dict[str, Any]:
        global LAST_PUSH_MESSAGE, PUSH_COUNTER

        PUSH_COUNTER += 1
        order = ORDERS[PUSH_COUNTER % len(ORDERS)]
        order["status"] = "open" if order["status"] != "open" else "queued"
        LAST_PUSH_MESSAGE = (
            f"SSE update #{PUSH_COUNTER}: {order['number']} is now {order['status']}."
        )
        _publish_orders_event(LAST_PUSH_MESSAGE)
        return {"ok": True, "message": LAST_PUSH_MESSAGE}

    @app.post("/admin/push-live-row")
    def push_live_row() -> dict[str, Any]:
        global LIVE_PUSH_COUNTER

        LIVE_PUSH_COUNTER += 1
        row = {
            "entry": f"event-{LIVE_PUSH_COUNTER}",
            "source": "sse",
        }
        LIVE_ROWS.insert(0, row)
        payload = {
            "target": "live-table",
            "mode": "prepend",
            "row": _render_live_row(row["entry"], row["source"]),
            "max_rows": 3,
        }
        _publish_live_event(payload)
        return {"ok": True, "entry": row["entry"]}

    @app.post("/admin/push-live-append-row")
    def push_live_append_row() -> dict[str, Any]:
        global APPEND_PUSH_COUNTER

        APPEND_PUSH_COUNTER += 1
        row = {"entry": f"append-{APPEND_PUSH_COUNTER}", "source": "sse"}
        APPEND_ROWS.append(row)
        payload = {
            "target": "live-append-table",
            "mode": "append",
            "row": _render_live_row(row["entry"], row["source"]),
            "max_rows": 3,
        }
        _publish_append_event(payload)
        return {"ok": True, "entry": row["entry"]}

    @app.get("/api/sql-hints")
    def sql_hints() -> dict[str, Any]:
        return {
            "hints": [
                "service",
                "status",
                "duration_ms",
                "AND",
                "OR",
                "ILIKE",
            ]
        }

    @app.post("/api/sql-validate")
    def sql_validate() -> dict[str, Any]:
        payload = request.get_json(silent=True) or {}
        sql = str(payload.get("sql", "")).strip()
        if not sql:
            return {"ok": True, "message": "SQL filter is empty."}
        if "drop " in sql.lower():
            return {
                "ok": False,
                "issues": [{"level": "error", "message": "Forbidden keyword."}],
            }
        if sql.endswith(("AND", "OR")):
            return {
                "ok": False,
                "issues": [
                    {"level": "warning", "message": "Expression ends with an operator."}
                ],
            }
        return {"ok": True, "message": "SQL filter validated."}

    @app.post("/api/validate-regex")
    def validate_regex() -> dict[str, Any]:
        payload = request.get_json(silent=True) or {}
        regex_value = str(payload.get("query", "")).strip()
        if not regex_value:
            return {"ok": True, "message": "Regex filter is empty."}
        try:
            re.compile(regex_value)
        except re.error as exc:
            return {
                "ok": False,
                "issues": [{"level": "error", "message": f"Invalid regex: {exc}"}],
            }
        return {"ok": True, "message": "Regex filter validated."}

    @app.get("/static/jinja-bootstrap-spa.js")
    def runtime_js() -> Any:
        runtime_path = (
            Path(__file__).resolve().parents[1]
            / "src"
            / "jinja_bootstrap_spa"
            / "static"
            / "jinja-bootstrap-spa.js"
        )
        return send_file(runtime_path, mimetype="text/javascript")

    return app


@pytest.fixture()
def live_server() -> str:
    global LAST_PUSH_MESSAGE, PUSH_COUNTER
    global LIVE_PUSH_COUNTER, LIVE_ROWS
    global APPEND_PUSH_COUNTER, APPEND_ROWS

    LAST_PUSH_MESSAGE = ""
    PUSH_COUNTER = 0
    LIVE_PUSH_COUNTER = 0
    LIVE_ROWS = [
        {"entry": "boot complete", "source": "runtime"},
        {"entry": "table hydrated", "source": "runtime"},
    ]
    APPEND_PUSH_COUNTER = 0
    APPEND_ROWS = [
        {"entry": "append channel online", "source": "runtime"},
        {"entry": "append stream ready", "source": "runtime"},
    ]

    app = create_test_app()
    server = make_server("127.0.0.1", 0, app, threaded=True)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def _table_contains(text: str) -> str:
    return (
        "() => document.querySelector('#orders-table')"
        f"?.textContent?.includes({text!r})"
    )


def test_browser_runtime_handles_overlays_autocomplete_and_table_contract(
    live_server: str,
) -> None:
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.skip(f"Playwright browser is unavailable: {exc}")
        page = browser.new_page()
        page.goto(live_server, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.getElementById('orders-table')"
            "?.dataset.jbsHydrated === 'true'"
        )
        try:

            page.get_by_role("button", name="Open Modal").click()
            expect_modal = page.locator("#runtime-modal")
            page.wait_for_function(
                "() => !document.getElementById('runtime-modal')?.hidden"
            )
            assert expect_modal.is_visible()
            page.keyboard.press("Escape")
            page.wait_for_function(
                "() => !!document.getElementById('runtime-modal')?.hidden"
            )

            page.get_by_role("button", name="Open Drawer").click()
            expect_drawer = page.locator("#orders-drawer")
            page.wait_for_function(
                "() => !document.getElementById('orders-drawer')?.hidden"
            )
            assert expect_drawer.is_visible()
            page.locator("#orders-drawer [data-jbs-overlay-close]").click()
            page.wait_for_function(
                "() => !!document.getElementById('orders-drawer')?.hidden"
            )

            assert "Page 1 of 3" in page.locator("#orders-table").text_content()
            assert (
                "#1001" in page.locator("#orders-table tbody tr").first.text_content()
            )

            page.locator("#orders-filters [data-jbs-disclosure-trigger]").click()
            page.wait_for_function(
                "() => !!document.querySelector("
                "'#orders-filters [data-jbs-disclosure-panel]'"
                ")?.hidden"
            )
            page.locator("#orders-filters [data-jbs-disclosure-trigger]").click()
            page.wait_for_function(
                "() => !document.querySelector("
                "'#orders-filters [data-jbs-disclosure-panel]'"
                ")?.hidden"
            )

            page.get_by_role("tab", name="Queued").click()
            page.wait_for_function(_table_contains("Queued"))
            assert "status=queued" in page.url
            page.get_by_role("tab", name="All").click()
            page.wait_for_function(_table_contains("Page 1 of 3"))
            assert "status=queued" not in page.url

            page.get_by_role("button", name="Order").click()
            page.wait_for_function(_table_contains("#1012"))
            assert "sort_dir=desc" in page.url
            assert "sort_by=number" in page.url

            page.locator("#orders-table").get_by_role("button", name="Next").click()
            page.wait_for_function(_table_contains("Page 2 of 3"))
            assert "page=2" in page.url

            page.locator("[data-jbs-autocomplete-input]").fill("Marg")
            page.wait_for_selector("[data-jbs-autocomplete-option]")
            page.get_by_role("option", name="Margaret Hamilton").click()

            page.locator(
                "[data-jbs-ms-input-name='status'] [data-jbs-ms-toggle]"
            ).click()
            page.locator(
                "[data-jbs-ms-input-name='status'] "
                "[data-jbs-ms-option][data-jbs-ms-value='queued']"
            ).click()

            page.locator(
                "#orders-table [data-jbs-ms-input-name='page_size'] "
                "[data-jbs-ms-toggle]"
            ).click()
            page.locator(
                "#orders-table [data-jbs-ms-input-name='page_size'] "
                "[data-jbs-ms-option][data-jbs-ms-value='8']"
            ).click()

            page.locator("[data-jbs-date-range] [data-jbs-drp-toggle]").click()
            page.locator(
                "[data-jbs-date-range] [data-jbs-drp-preset][data-jbs-minutes='60']"
            ).click()
            assert page.locator(
                "[data-jbs-date-range] [data-jbs-drp-from]"
            ).input_value()

            sql_input = page.locator("input[name='sql']")
            sql_input.click()
            page.wait_for_selector("[data-jbs-assist-option='service']")
            sql_input.fill("status = 'queued' AND")
            page.wait_for_function(
                "() => document.querySelector("
                "'[data-jbs-assist=\"sql\"] [data-jbs-assist-status]'"
                ")?.textContent?.includes('operator')"
            )
            sql_input.fill("status = 'queued'")
            page.wait_for_function(
                "() => document.querySelector("
                "'[data-jbs-assist=\"sql\"] [data-jbs-assist-status]'"
                ")?.textContent?.includes('validated')"
            )

            regex_input = page.locator("input[name='regex']")
            regex_input.fill("(")
            page.wait_for_function(
                "() => document.querySelector("
                "'[data-jbs-assist=\"regex\"] [data-jbs-assist-status]'"
                ")?.textContent?.includes('Invalid regex')"
            )
            regex_input.fill("Margaret")
            page.wait_for_function(
                "() => document.querySelector("
                "'[data-jbs-assist=\"regex\"] [data-jbs-assist-status]'"
                ")?.textContent?.includes('validated')"
            )

            page.locator("#orders-table").get_by_role("button", name="Apply").click()
            page.wait_for_function(_table_contains("Page 1 of 1"))
            assert "status=queued" in page.url
            assert "page=1" in page.url
            assert "page_size=8" in page.url
            assert "customer=Margaret+Hamilton" in page.url
            assert "Margaret" in page.locator("#orders-table tbody").text_content()

            page.get_by_role("tab", name="All").click()
            page.wait_for_function(_table_contains("Page 1 of 1"))
            assert "status=queued" not in page.url

            first_menu = page.locator("#orders-table tbody tr").first.locator(
                "[data-jbs-menu]"
            )
            first_menu.get_by_role("button", name="Actions").click()
            expect_panel = first_menu.locator("[data-jbs-menu-panel]")
            page.wait_for_function(
                "() => !!document.querySelector("
                "'#orders-table [data-jbs-menu-panel].show'"
                ")"
            )
            assert expect_panel.is_visible()

            page.locator("body").click(position={"x": 5, "y": 5})
            page.wait_for_function(
                "() => !document.querySelector("
                "'#orders-table [data-jbs-menu-panel].show'"
                ")"
            )

            first_menu.get_by_role("button", name="Actions").click()
            first_menu.locator("[data-jbs-menu-panel] [role='menuitem']").get_by_text(
                "Archive Order"
            ).click(force=True)
            page.wait_for_function(_table_contains("Restore Order"))

            page.evaluate(
                """
                async () => {
                  await fetch('/admin/push-update', { method: 'POST' });
                }
                """
            )
            page.wait_for_function(_table_contains("SSE update #1:"))
            assert "SSE update #1:" in page.locator("#orders-table").text_content()
            page.locator("#orders-status-region [data-jbs-status-dismiss]").click()
            page.wait_for_function(
                "() => !document.getElementById('orders-status-region')"
            )

            assert "table hydrated" in page.locator("#live-table").text_content()
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.evaluate(
                """
                async () => {
                  await fetch('/admin/push-live-row', { method: 'POST' });
                }
                """
            )
            page.wait_for_timeout(300)
            assert (
                "event-1"
                not in page.locator("#live-table tbody tr:first-child").text_content()
            )
            page.evaluate("() => window.scrollTo(0, 0)")
            page.wait_for_function(
                "() => document.querySelector("
                "'#live-table tbody tr:first-child'"
                ")?.textContent?.includes('event-1')"
            )
            page.get_by_role("button", name="Push Prepend Row").click()
            page.get_by_role("button", name="Push Prepend Row").click()
            page.wait_for_function(
                "() => document.querySelector("
                "'#live-table tbody tr:first-child'"
                ")?.textContent?.includes('event-3')"
            )
            row_count = page.evaluate(
                "() => document.querySelectorAll('#live-table tbody tr').length"
            )
            assert row_count == 3

            assert (
                "append stream ready"
                in page.locator("#live-append-table").text_content()
            )
            page.get_by_role("button", name="Push Append Row").click()
            page.get_by_role("button", name="Push Append Row").click()
            page.get_by_role("button", name="Push Append Row").click()
            page.wait_for_function(
                "() => document.querySelector("
                "'#live-append-table tbody tr:last-child'"
                ")?.textContent?.includes('append-3')"
            )
            append_count = page.evaluate(
                "() => document.querySelectorAll('#live-append-table tbody tr').length"
            )
            assert append_count == 3

            page.locator(
                "#session-table [data-jbs-ms-input-name='page_size'] "
                "[data-jbs-ms-toggle]"
            ).click()
            page.locator(
                "#session-table [data-jbs-ms-input-name='page_size'] "
                "[data-jbs-ms-option][data-jbs-ms-value='4']"
            ).click()
            page.locator("#session-table").get_by_role("button", name="Apply").click()
            page.wait_for_function(
                "() => document.querySelector('#session-table')"
                "?.textContent?.includes('Showing 4 of 4')"
            )
            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelector('#session-table')"
                "?.textContent?.includes('Showing 4 of 4')"
            )

            page.locator("#cancel-demo").get_by_role(
                "button", name="Slow Request"
            ).click()
            page.locator("#cancel-demo").get_by_role(
                "button", name="Fast Request"
            ).click()
            page.wait_for_function(
                "() => document.getElementById('cancel-demo-value')"
                "?.textContent?.trim() === 'fast'"
            )
            assert page.locator("#cancel-demo-value").text_content().strip() == "fast"

            assert (
                "Loading lazy summary" in page.locator("#lazy-summary").text_content()
            )
            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function(
                "() => document.getElementById('lazy-summary')"
                "?.textContent?.includes('Lazy summary ready.')"
            )
            assert "Lazy summary ready." in page.locator("#lazy-summary").text_content()

        finally:
            browser.close()
