"""End-to-end browser tests for the jinja-bootstrap-spa runtime."""

from __future__ import annotations

import json
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
    </div>
    {{ table_markup|safe }}
    {{ overlay_markup|safe }}
    </main>
    <script type="module" src="/static/jinja-bootstrap-spa.js"></script>
  </body>
</html>
"""

TABLE_TEMPLATE = """
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
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
      "status"
    ],
    title="Orders",
    subtitle=subtitle,
    toolbar='
      <div class="vstack gap-3">
        '
        ~ (
          ui.status_region(
            "orders-status-region",
            title=status_notice.title,
            message=status_notice.message,
            variant=status_notice.variant,
            class_name="mb-0"
          )
          if status_notice
          else ""
        )
        ~ '
        '
        ~ ui.tabs(
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
        ~ '
        <form class="d-flex flex-wrap align-items-end gap-2" data-jbs-form>
          '
          ~ ui.form_input(
            "query",
            value=state.query or "",
            placeholder="Search orders",
            class_name="form-control-sm mb-0"
          )
          ~ '
          ~ ui.autocomplete(
            "customer",
            "/fragments/customer-options",
            value=state.customer or "",
            display_value=state.customer or "",
            placeholder="Filter customer",
            class_name="mb-0",
            input_class="form-control-sm"
          )
          ~ '
          ~ ui.form_select(
            "status",
            [
              {"value": "queued", "label": "Queued"},
              {"value": "open", "label": "Open"},
              {"value": "archived", "label": "Archived"},
            ],
            value=state.status or "",
            placeholder="All",
            class_name="form-select-sm mb-0"
          )
          ~ '
          ~ ui.form_select(
            "page_size",
            [
              {"value": "4", "label": "4 rows"},
              {"value": "8", "label": "8 rows"},
            ],
            value=state.page_size or 4,
            class_name="form-select-sm mb-0"
          )
          ~ '
          <button class="btn btn-sm btn-primary" type="submit">Apply</button>
        </form>
      </div>
    ',
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


def _sort_orders(
    rows: list[dict[str, Any]], sort_by: str, sort_dir: str
) -> list[dict[str, Any]]:
    reverse = sort_dir == "desc"
    if sort_by not in {"number", "customer", "status"}:
        sort_by = "number"
    return sorted(rows, key=lambda row: str(row[sort_by]), reverse=reverse)


def _filter_orders(
    rows: list[dict[str, Any]], query: str, status: str, customer: str
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
        overlay_markup = render_template_string(OVERLAYS_TEMPLATE)
        return render_template_string(
            PAGE_TEMPLATE, table_markup=table_markup, overlay_markup=overlay_markup
        )

    @app.get("/components/orders")
    def orders_component() -> str:
        return _build_table(app)

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
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(live_server, wait_until="domcontentloaded")

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

            page.get_by_role("tab", name="Queued").click()
            page.wait_for_function(_table_contains("Queued"))
            assert "status=queued" in page.url
            page.get_by_role("tab", name="All").click()
            page.wait_for_function(_table_contains("Page 1 of 3"))

            page.get_by_role("button", name="Order").click()
            page.wait_for_function(_table_contains("#1012"))
            assert "sort_dir=desc" in page.url
            assert "sort_by=number" in page.url

            page.get_by_role("button", name="Next").click()
            page.wait_for_function(_table_contains("Page 2 of 3"))
            assert "page=2" in page.url

            page.locator("[data-jbs-autocomplete-input]").fill("Marg")
            page.wait_for_selector("[data-jbs-autocomplete-option]")
            page.get_by_role("option", name="Margaret Hamilton").click()
            page.locator("select[name='status']").select_option("queued")
            page.locator("select[name='page_size']").select_option("8")
            page.get_by_role("button", name="Apply").click()
            page.wait_for_function(_table_contains("Page 1 of 1"))
            assert "status=queued" in page.url
            assert "page=1" in page.url
            assert "page_size=8" in page.url
            assert "customer=Margaret+Hamilton" in page.url
            assert "Margaret" in page.locator("#orders-table tbody").text_content()

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
            page.locator(
                "#orders-table [data-jbs-menu-panel].show [role='menuitem']"
            ).get_by_text("Archive Order").click()
            page.wait_for_function(_table_contains("Last action: archive"))
            assert (
                "Last action: archive" in page.locator("#orders-table").text_content()
            )
            page.locator("#orders-status-region [data-jbs-status-dismiss]").click()
            page.wait_for_function(
                "() => !document.getElementById('orders-status-region')"
            )

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

            browser.close()
    except PlaywrightError as exc:
        pytest.skip(f"Playwright browser is unavailable: {exc}")
