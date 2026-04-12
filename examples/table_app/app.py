"""Standalone development app for jinja-bootstrap-spa.

Use this wrapper project to iterate on the runtime and component contracts
manually instead of relying only on tests.
"""

from __future__ import annotations

import json
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

from jinja_bootstrap_spa import parse_table_state, register_bootstrap_macros

app = Flask(__name__, template_folder="templates")
app.jinja_loader = ChoiceLoader(
    [app.jinja_loader, PackageLoader("jinja_bootstrap_spa", "templates")]
)  # type: ignore[list-item]
register_bootstrap_macros(app.jinja_env)

SUBSCRIBERS: list[Queue[dict[str, Any]]] = []
SUBSCRIBERS_LOCK = Lock()
PUSH_COUNTER = 0
LAST_PUSH_MESSAGE = ""


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


def _publish_orders_event(message: str, patch: dict[str, Any] | None = None) -> None:
    payload = {"action": "refresh", "target": "orders-table", "patch": patch or {}}
    with SUBSCRIBERS_LOCK:
        subscribers = list(SUBSCRIBERS)
    for subscriber in subscribers:
        subscriber.put(payload)
    app.logger.info("Published SSE update: %s", message)


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
    rows: list[dict[str, Any]], query: str, status: str, customer: str
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
        default_sort_by="number",
        default_page_size=10,
        allowed_page_sizes=(5, 10, 20, 50),
        filter_keys=("status", "customer", "row_id", "intent"),
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
        "status_summary": _status_summary(filtered_rows),
        "status_notice": status_notice,
    }


@app.get("/")
def index() -> str:
    return render_template("index.html", **build_orders_context())


@app.get("/components/orders")
def orders_component() -> str:
    return render_template("partials/orders_table.html", **build_orders_context())


@app.get("/fragments/customer-options")
def customer_options() -> str:
    query = str(request.args.get("q", "") or "")
    return render_template(
        "partials/customer_autocomplete_options.html",
        matches=_customer_matches(query),
    )


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


if __name__ == "__main__":
    app.run(debug=True)
