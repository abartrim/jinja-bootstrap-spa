"""Standalone development app for jinja-bootstrap-spa.

Use this wrapper project to iterate on the runtime and component contracts
manually instead of relying only on tests.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from queue import Empty, Queue
from threading import Lock
from typing import Any

from flask import (
    Flask,
    Response,
    render_template,
    request,
    send_file,
    stream_with_context,
    url_for,
)
from jinja2 import ChoiceLoader, PackageLoader

from jinja_bootstrap_spa import conditional_fragment_response
from jinja_bootstrap_spa import parse_table_state
from jinja_bootstrap_spa import register_bootstrap_macros

app = Flask(__name__, template_folder="templates")
app.jinja_loader = ChoiceLoader(
    [app.jinja_loader, PackageLoader("jinja_bootstrap_spa", "templates")]
)  # type: ignore[list-item]
register_bootstrap_macros(app.jinja_env)

SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
SUBSCRIBERS_LOCK = Lock()
PUSH_COUNTER = 0
LAST_PUSH_MESSAGE = ""
ORDERS_STREAM_SEQ = 0
LIVE_SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
LIVE_SUBSCRIBERS_LOCK = Lock()
LIVE_PUSH_COUNTER = 0
LIVE_ROWS = [
    {"id": "live-boot", "entry": "boot complete", "source": "runtime"},
    {"id": "live-hydrated", "entry": "table hydrated", "source": "runtime"},
]
APPEND_SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
APPEND_SUBSCRIBERS_LOCK = Lock()
APPEND_PUSH_COUNTER = 0
APPEND_ROWS = [
    {"id": "append-boot", "entry": "append channel online", "source": "runtime"},
    {"id": "append-ready", "entry": "append stream ready", "source": "runtime"},
]
SESSION_ROWS = [
    {"name": "Alerts", "owner": "SRE"},
    {"name": "Incidents", "owner": "On-call"},
    {"name": "Traces", "owner": "Platform"},
    {"name": "Errors", "owner": "Backend"},
    {"name": "Web Traffic", "owner": "Growth"},
    {"name": "AI Calls", "owner": "Infra"},
]


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
        "Sophie Wilson",
        "Anders Hejlsberg",
        "Brendan Eich",
        "Yukihiro Matsumoto",
        "Bjarne Stroustrup",
        "Katie Bouman",
        "Fei-Fei Li",
        "Tim Berners-Lee",
        "Cynthia Dwork",
        "Adele Goldberg",
        "James Gosling",
        "Frances Allen",
        "Carol Shaw",
        "Brian Kernighan",
        "Whitfield Diffie",
        "Martin Fowler",
        "Ward Cunningham",
        "Alan Kay",
    ]
    statuses = ["queued", "open", "archived", "open", "queued"]
    base_total = 42.50
    orders: list[dict[str, Any]] = []

    for index, customer in enumerate(customers, start=1):
        orders.append(
            {
                "id": f"order-{1000 + index}",
                "number": f"#{1000 + index}",
                "customer": customer,
                "status": statuses[index % len(statuses)],
                "total": round(base_total + (index * 17.35), 2),
            }
        )

    return orders


ORDERS = _seed_orders()


def _runtime_asset_path() -> Path:
    return (
        Path(__file__).resolve().parents[2]
        / "src"
        / "jinja_bootstrap_spa"
        / "static"
        / "jinja-bootstrap-spa.js"
    )


def _fragment_response(content: str) -> tuple[str, int, dict[str, str]]:
    return conditional_fragment_response(content, request.headers)


def _publish_orders_event(message: str, patch: dict[str, Any] | None = None) -> None:
    global ORDERS_STREAM_SEQ

    with SUBSCRIBERS_LOCK:
        ORDERS_STREAM_SEQ += 1
        payload = {
            "v": 1,
            "seq": ORDERS_STREAM_SEQ,
            "action": "refresh",
            "target": "orders-table",
            "patch": patch or {},
            "snapshot": f"orders-{ORDERS_STREAM_SEQ}",
        }
        subscribers = list(SUBSCRIBERS)
    for subscriber in subscribers:
        subscriber.put(payload)
    app.logger.info("Published SSE update: %s", message)


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


def _render_live_row(row_id: str, entry: str, source: str) -> str:
    safe_id = row_id.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_entry = entry.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    safe_source = source.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return (
        f'<tr data-jbs-row-id="{safe_id}"><td>{safe_entry}</td><td>{safe_source}</td></tr>'
    )


def _action_menu(order: dict[str, Any]) -> str:
    destructive_label = (
        "Restore Order" if order["status"] == "archived" else "Archive Order"
    )
    destructive_intent = "restore" if order["status"] == "archived" else "archive"
    return render_template(
        "partials/order_action_menu.html",
        menu_id=f"{order['id']}-actions",
        order=order,
        items=[
            {
                "label": "Inspect Order",
                "href": f"/?query={order['number']}",
            },
            {"divider": True},
            {
                "label": destructive_label,
                "jbs_action": "row",
                "jbs_row_id": order["id"],
                "jbs_intent": destructive_intent,
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

        message = f"{intent.title()}d {order['number']}"
        _publish_orders_event(message)
        return message
    return None


def _filter_orders(
    rows: list[dict[str, Any]],
    query: str,
    status: str,
    customer: str,
    regex_filter: str,
) -> list[dict[str, Any]]:
    filtered = rows
    if query:
        query_lower = query.lower()
        filtered = [
            row
            for row in filtered
            if query_lower in row["number"].lower()
            or query_lower in row["customer"].lower()
        ]
    if status:
        filtered = [row for row in filtered if row["status"] == status]
    if customer:
        filtered = [
            row for row in filtered if row["customer"].lower() == customer.lower()
        ]
    if regex_filter:
        try:
            pattern = re.compile(regex_filter, re.IGNORECASE)
        except re.error:
            return filtered
        filtered = [
            row
            for row in filtered
            if pattern.search(row["number"]) or pattern.search(row["customer"])
        ]
    return filtered


def _customer_matches(query: str) -> list[str]:
    query_lower = query.strip().lower()
    customers = sorted({str(order["customer"]) for order in ORDERS})
    if not query_lower:
        return customers[:8]
    return [customer for customer in customers if query_lower in customer.lower()][:8]


def _sort_orders(
    rows: list[dict[str, Any]], sort_by: str, sort_dir: str
) -> list[dict[str, Any]]:
    reverse = sort_dir == "desc"
    if sort_by not in {"number", "customer", "status", "total"}:
        sort_by = "number"
    return sorted(rows, key=lambda row: row[sort_by], reverse=reverse)


def _status_summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts = {
        "Queued": sum(1 for row in rows if row["status"] == "queued"),
        "Open": sum(1 for row in rows if row["status"] == "open"),
        "Archived": sum(1 for row in rows if row["status"] == "archived"),
    }
    return [{"label": label, "count": count} for label, count in counts.items()]


def build_orders_context() -> dict[str, Any]:
    state = parse_table_state(
        request.args,
        request_headers=request.headers,
        default_sort_by="number",
        default_page_size=8,
        allowed_page_sizes=(4, 8, 12, 20),
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
            "id": order["id"],
            "number": order["number"],
            "customer": order["customer"],
            "status": order["status"].title(),
            "total": f"${order['total']:.2f}",
            "actions": _action_menu(order),
        }
        for order in page_rows
    ]

    subtitle = "Exercise sort, paging, filters, row actions, and SSE-driven refreshes."
    status_notice = None
    if LAST_PUSH_MESSAGE:
        subtitle = LAST_PUSH_MESSAGE
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

    return {
        "rows": rows,
        "total_rows": len(sorted_rows),
        "table_state": state,
        "subtitle": subtitle,
        "runtime_url": url_for("runtime_js"),
        "push_url": url_for("simulate_push"),
        "live_push_url": url_for("push_live_row"),
        "append_push_url": url_for("push_live_append_row"),
        "live_rows": list(LIVE_ROWS),
        "append_rows": list(APPEND_ROWS),
        "status_summary": _status_summary(filtered_rows),
        "status_notice": status_notice,
    }


def build_session_context() -> dict[str, Any]:
    state = parse_table_state(
        request.args,
        request_headers=request.headers,
        default_sort_by="name",
        default_page_size=2,
        allowed_page_sizes=(2, 4),
        filter_keys=(),
    )
    rows_sorted = sorted(SESSION_ROWS, key=lambda row: row["name"])
    page = int(state["page"])
    page_size = int(state["page_size"])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "session_rows": rows_sorted[start:end],
        "session_total_rows": len(rows_sorted),
        "session_state": state,
    }


def build_live_table_context() -> dict[str, Any]:
    state = parse_table_state(
        request.args,
        request_headers=request.headers,
        default_sort_by="",
        default_page_size=5,
        allowed_page_sizes=(5,),
        filter_keys=(),
    )
    page = int(state["page"])
    page_size = int(state["page_size"])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "live_rows": list(LIVE_ROWS[start:end]),
        "live_total_rows": len(LIVE_ROWS),
        "live_state": state,
    }


def build_live_append_context() -> dict[str, Any]:
    state = parse_table_state(
        request.args,
        request_headers=request.headers,
        default_sort_by="",
        default_page_size=5,
        allowed_page_sizes=(5,),
        filter_keys=(),
    )
    page = int(state["page"])
    page_size = int(state["page_size"])
    start = (page - 1) * page_size
    end = start + page_size
    return {
        "append_rows": list(APPEND_ROWS[start:end]),
        "append_total_rows": len(APPEND_ROWS),
        "append_state": state,
    }


def build_foundation_grid_context() -> dict[str, Any]:
    return {
        "foundation_grid_rows": [
            {
                "primitive": "data_grid",
                "purpose": "Reusable CRUD and operator shell for table-driven pages.",
                "status": '<span class="badge text-bg-success">Implemented</span>',
            },
            {
                "primitive": "searchable_expandable_list",
                "purpose": "Explorer shell for drill-down lists and schema browsers.",
                "status": '<span class="badge text-bg-success">Implemented</span>',
            },
            {
                "primitive": "workspace_modal",
                "purpose": "Large overlay for editors, inspectors, and multi-pane flows.",
                "status": '<span class="badge text-bg-primary">Ready to compose</span>',
            },
            {
                "primitive": "timeline",
                "purpose": "Ordered event/history surface for audit trails and stream summaries.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "stacked_list",
                "purpose": "Compact stacked rows for queues, review surfaces, and result summaries.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "tree_nav",
                "purpose": "Hierarchical explorer navigation without a separate JS tree widget.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "code_block",
                "purpose": "Structured snippet/config surface for docs, query output, and operator hints.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "facet_bar",
                "purpose": "Active-filter chip row with clear/remove affordances for tables and explorers.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "master_detail_shell",
                "purpose": "Generic master/detail layout for inspector, review, and explorer pages.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "result_panel",
                "purpose": "Consistent output surface for generated results, previews, and validation summaries.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "command_bar",
                "purpose": "Reusable action strip for search, quick actions, and overflow commands.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "metric_grid",
                "purpose": "Structured summary band for grouped stat cards and KPI rows.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "activity_feed",
                "purpose": "Dense event stream surface for audits, comments, and runtime activity.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "property_editor",
                "purpose": "Inspector-style form shell for settings, metadata, and builder properties.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
            {
                "primitive": "diff_view",
                "purpose": "Before/after comparison shell for config reviews and change inspection.",
                "status": '<span class="badge text-bg-success">New</span>',
            },
        ],
        "foundation_grid_state": {
            "page": 1,
            "page_size": 10,
            "sort_by": "",
            "sort_dir": "asc",
        },
    }


@app.get("/")
def index() -> str:
    context = build_orders_context()
    context.update(build_session_context())
    context.update(build_live_table_context())
    context.update(build_live_append_context())
    context.update(build_foundation_grid_context())
    return render_template("index.html", **context)


@app.get("/components/orders")
def orders_component() -> tuple[str, int, dict[str, str]]:
    html = render_template("partials/orders_table.html", **build_orders_context())
    return _fragment_response(html)


@app.get("/components/live-table")
def live_table_component() -> tuple[str, int, dict[str, str]]:
    context = build_live_table_context()
    html = render_template("partials/live_table.html", **context)
    return _fragment_response(html)


@app.get("/components/live-append-table")
def live_append_table_component() -> tuple[str, int, dict[str, str]]:
    context = build_live_append_context()
    html = render_template("partials/live_append_table.html", **context)
    return _fragment_response(html)


@app.get("/components/session-table")
def session_table_component() -> tuple[str, int, dict[str, str]]:
    context = build_orders_context()
    context.update(build_session_context())
    html = render_template("partials/session_table.html", **context)
    return _fragment_response(html)


@app.get("/components/foundation-grid")
def foundation_grid_component() -> tuple[str, int, dict[str, str]]:
    html = render_template(
        "partials/foundation_grid.html",
        **build_foundation_grid_context(),
    )
    return _fragment_response(html)


@app.get("/components/cancel-demo")
def cancel_demo_component() -> tuple[str, int, dict[str, str]]:
    value = str(request.args.get("value", "idle"))
    delay_ms = int(request.args.get("delay_ms", 0) or 0)
    delay_ms = max(0, min(delay_ms, 1000))
    if delay_ms:
        time.sleep(delay_ms / 1000)
    html = render_template("partials/cancel_demo.html", value=value, delay_ms=delay_ms)
    return _fragment_response(html)


@app.get("/components/lazy-summary")
def lazy_summary_component() -> tuple[str, int, dict[str, str]]:
    html = (
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
    return _fragment_response(html)


@app.get("/fragments/customer-options")
def customer_options() -> tuple[str, int, dict[str, str]]:
    query = str(request.args.get("q", "") or "")
    html = render_template(
        "partials/customer_autocomplete_options.html",
        matches=_customer_matches(query),
    )
    return _fragment_response(html)


@app.get("/assets/jinja-bootstrap-spa.js")
def runtime_js() -> Any:
    return send_file(_runtime_asset_path(), mimetype="text/javascript")


@app.get("/events/orders")
def orders_events() -> Response:
    queue: Queue[dict[str, Any]] = Queue()
    with SUBSCRIBERS_LOCK:
        SUBSCRIBERS.append(queue)

    @stream_with_context
    def event_stream() -> Any:
        try:
            yield "retry: 3000\n\n"
            while True:
                try:
                    payload = queue.get(timeout=15)
                    yield ("event: refresh\n" f"data: {json.dumps(payload)}\n\n")
                except Empty:
                    yield ": keep-alive\n\n"
        finally:
            with SUBSCRIBERS_LOCK:
                if queue in SUBSCRIBERS:
                    SUBSCRIBERS.remove(queue)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/events/live-table")
def live_table_events() -> Response:
    queue: Queue[dict[str, Any]] = Queue()
    with LIVE_SUBSCRIBERS_LOCK:
        LIVE_SUBSCRIBERS.append(queue)

    @stream_with_context
    def event_stream() -> Any:
        try:
            yield "retry: 3000\n\n"
            while True:
                try:
                    payload = queue.get(timeout=15)
                    yield ("event: refresh\n" f"data: {json.dumps(payload)}\n\n")
                except Empty:
                    yield ": keep-alive\n\n"
        finally:
            with LIVE_SUBSCRIBERS_LOCK:
                if queue in LIVE_SUBSCRIBERS:
                    LIVE_SUBSCRIBERS.remove(queue)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/events/live-append-table")
def live_append_table_events() -> Response:
    queue: Queue[dict[str, Any]] = Queue()
    with APPEND_SUBSCRIBERS_LOCK:
        APPEND_SUBSCRIBERS.append(queue)

    @stream_with_context
    def event_stream() -> Any:
        try:
            yield "retry: 3000\n\n"
            while True:
                try:
                    payload = queue.get(timeout=15)
                    yield ("event: refresh\n" f"data: {json.dumps(payload)}\n\n")
                except Empty:
                    yield ": keep-alive\n\n"
        finally:
            with APPEND_SUBSCRIBERS_LOCK:
                if queue in APPEND_SUBSCRIBERS:
                    APPEND_SUBSCRIBERS.remove(queue)

    return Response(
        event_stream(),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/admin/simulate-update")
def simulate_push() -> Any:
    global PUSH_COUNTER, LAST_PUSH_MESSAGE

    PUSH_COUNTER += 1
    order = ORDERS[PUSH_COUNTER % len(ORDERS)]
    order["status"] = "open" if order["status"] != "open" else "queued"
    LAST_PUSH_MESSAGE = (
        f"SSE update #{PUSH_COUNTER}: {order['number']} is now {order['status']}."
    )
    _publish_orders_event(LAST_PUSH_MESSAGE)
    return {"ok": True, "message": LAST_PUSH_MESSAGE}


@app.post("/admin/push-live-row")
def push_live_row() -> Any:
    global LIVE_PUSH_COUNTER

    LIVE_PUSH_COUNTER += 1
    row = {
        "id": f"live-{LIVE_PUSH_COUNTER}",
        "entry": f"event-{LIVE_PUSH_COUNTER}",
        "source": "sse",
    }
    LIVE_ROWS.insert(0, row)
    _publish_live_event(
        {
            "v": 1,
            "seq": LIVE_PUSH_COUNTER,
            "target": "live-table",
            "ops": [
                {
                    "op": "upsert",
                    "id": row["id"],
                    "position": "prepend",
                    "html": _render_live_row(row["id"], row["entry"], row["source"]),
                }
            ],
        }
    )
    return {"ok": True, "entry": row["entry"]}


@app.post("/admin/push-live-append-row")
def push_live_append_row() -> Any:
    global APPEND_PUSH_COUNTER

    APPEND_PUSH_COUNTER += 1
    row = {
        "id": f"append-{APPEND_PUSH_COUNTER}",
        "entry": f"append-{APPEND_PUSH_COUNTER}",
        "source": "sse",
    }
    APPEND_ROWS.append(row)
    page_size = 5
    page_count = max(1, (len(APPEND_ROWS) + page_size - 1) // page_size)
    _publish_append_event(
        {
            "v": 1,
            "seq": APPEND_PUSH_COUNTER,
            "target": "live-append-table",
            "ops": [
                {
                    "op": "upsert",
                    "id": row["id"],
                    "position": "append",
                    "html": _render_live_row(row["id"], row["entry"], row["source"]),
                }
            ],
            "meta": {
                "total_rows": len(APPEND_ROWS),
                "page_count": page_count,
                "showing_rows": min(page_size, len(APPEND_ROWS)),
                "subtitle": "SSE stream appends rows while table metadata stays in sync.",
            },
        }
    )
    return {"ok": True, "entry": row["entry"]}


@app.get("/api/sql-hints")
def sql_hints() -> Any:
    return {"hints": ["service", "status", "duration_ms", "AND", "OR", "ILIKE"]}


@app.post("/api/sql-validate")
def sql_validate() -> Any:
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
def validate_regex() -> Any:
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


if __name__ == "__main__":
    app.run(debug=True)
