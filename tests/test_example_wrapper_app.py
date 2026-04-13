"""Browser smoke tests for the real wrapper dev app in examples/table_app."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from threading import Thread
from types import ModuleType

import pytest
from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from tests.browser_assertions import assert_no_browser_errors
from tests.browser_assertions import capture_browser_errors


def _load_example_app_module() -> ModuleType:
    app_path = Path(__file__).resolve().parents[1] / "examples" / "table_app" / "app.py"
    spec = importlib.util.spec_from_file_location("jbs_example_table_app", app_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load example app module from {app_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture()
def example_live_server() -> str:
    module = _load_example_app_module()
    template_dir = (
        Path(__file__).resolve().parents[1] / "examples" / "table_app" / "templates"
    )
    module.app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(template_dir)),
            PackageLoader("jinja_bootstrap_spa", "templates"),
        ]
    )

    module.LAST_PUSH_MESSAGE = ""
    module.PUSH_COUNTER = 0
    module.ORDERS_STREAM_SEQ = 0
    module.LIVE_PUSH_COUNTER = 0
    module.LIVE_ROWS = [
        {"id": "live-boot", "entry": "boot complete", "source": "runtime"},
        {"id": "live-hydrated", "entry": "table hydrated", "source": "runtime"},
    ]
    module.APPEND_PUSH_COUNTER = 0
    module.APPEND_ROWS = [
        {"id": "append-boot", "entry": "append channel online", "source": "runtime"},
        {"id": "append-ready", "entry": "append stream ready", "source": "runtime"},
    ]

    server = make_server("127.0.0.1", 0, module.app, threaded=True)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def test_wrapper_app_smoke_flow(example_live_server: str) -> None:
    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.skip(f"Playwright browser is unavailable: {exc}")
        page = browser.new_page()
        console_errors, page_errors = capture_browser_errors(page)
        page.goto(example_live_server, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.getElementById('orders-table')"
            "?.dataset.jbsHydrated === 'true'"
        )
        try:

            page.wait_for_selector("#orders-table")
            page.wait_for_selector("#live-table")
            page.wait_for_selector("#live-append-table")
            page.wait_for_selector("#session-table")
            page.wait_for_selector("#cancel-demo")
            page.wait_for_selector("#lazy-summary")

            page.get_by_role("button", name="About Runtime").click()
            page.wait_for_function(
                "() => !document.getElementById('runtime-modal')?.hidden"
            )
            page.keyboard.press("Escape")
            page.wait_for_function(
                "() => !!document.getElementById('runtime-modal')?.hidden"
            )

            page.get_by_role("button", name="Workbench").click()
            page.wait_for_function(
                "() => !document.getElementById('orders-drawer')?.hidden"
            )
            page.locator("#orders-drawer").get_by_role("button", name="Close").click()
            page.wait_for_function(
                "() => !!document.getElementById('orders-drawer')?.hidden"
            )

            page.locator("#orders-filters [data-jbs-disclosure-trigger]").click()
            page.wait_for_function(
                "() => !!document.querySelector("
                "'#orders-filters [data-jbs-disclosure-panel]'"
                ")?.hidden"
            )
            with page.expect_response("**/components/orders*") as first_refresh:
                page.get_by_role("button", name="Refresh Table").click()
            assert first_refresh.value.status in (200, 304)
            with page.expect_response("**/components/orders*") as second_refresh:
                page.get_by_role("button", name="Refresh Table").click()
            assert second_refresh.value.status == 304
            page.wait_for_function(
                "() => document.getElementById('orders-table')"
                "?.dataset.jbsPhase === 'unchanged'"
            )
            page.wait_for_function(
                "() => !!document.getElementById('orders-table')"
                "?.classList.contains('jbs-not-modified-pulse')"
            )
            page.wait_for_function(
                "() => !!document.getElementById('orders-table')"
                "?.classList.contains('jbs-swap-pulse')"
            )
            page.wait_for_function(
                "() => !!document.querySelector("
                "'#orders-filters [data-jbs-disclosure-panel]'"
                ")?.hidden"
            )
            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.getElementById('orders-table')"
                "?.dataset.jbsHydrated === 'true'"
            )
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

            regex_input = page.locator("#orders-table input[name='regex']")
            regex_input.fill("(")
            page.wait_for_function(
                "() => document.querySelector("
                "'[data-jbs-assist=\"regex\"] [data-jbs-assist-status]'"
                ")?.textContent?.includes('Invalid regex')"
            )
            regex_input.fill("Ada")
            page.wait_for_function(
                "() => document.querySelector("
                "'[data-jbs-assist=\"regex\"] [data-jbs-assist-status]'"
                ")?.textContent?.includes('validated')"
            )

            page.locator("#orders-table").get_by_role("button", name="Apply").click()
            page.wait_for_function(
                "() => document.querySelector('#orders-table tbody')"
                "?.textContent?.includes('Ada Lovelace')"
            )

            page.locator("#live-table").scroll_into_view_if_needed()
            with page.expect_response("**/admin/push-live-row") as prepend_response:
                page.get_by_role("button", name="Push Prepend Row").click()
            assert prepend_response.value.ok

            page.get_by_role("button", name="Push Append Row").click()
            page.wait_for_function(
                "() => document.querySelector('#live-append-table tbody tr:last-child')"
                "?.textContent?.includes('append-1')"
            )
            page.get_by_role("button", name="Push Append Row").click()
            page.get_by_role("button", name="Push Append Row").click()
            page.get_by_role("button", name="Push Append Row").click()
            page.wait_for_function(
                "() => document.querySelector('#live-append-table')"
                "?.textContent?.includes('Page 1 of 2')"
            )
            append_pager = page.locator("#live-append-table")
            append_pager.get_by_role("button", name="Next").click()
            page.wait_for_function(
                "() => document.querySelector('#live-append-table')"
                "?.textContent?.includes('Page 2 of 2')"
            )
            page.get_by_role("button", name="Push Append Row").click()
            page.wait_for_function(
                "() => document.querySelector('#live-append-table tbody tr:last-child')"
                "?.textContent?.includes('append-5')"
            )
            page.wait_for_function(
                "() => document.getElementById('live-append-table')"
                "?.classList.contains('jbs-demo-replaced')"
            )
            page.wait_for_function(
                "() => document.querySelector('#live-append-table')"
                "?.textContent?.includes('Page 2 of 2')"
            )

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
                "?.textContent?.includes('Showing 4 of 6')"
            )
            page.reload(wait_until="domcontentloaded")
            page.wait_for_function(
                "() => document.querySelector('#session-table')"
                "?.textContent?.includes('Showing 4 of 6')"
            )

            page.locator("#cancel-demo").get_by_role(
                "button", name="Slow Request"
            ).click()
            page.wait_for_function(
                "() => document.getElementById('cancel-demo')"
                "?.dataset.jbsPhase === 'loading'"
            )
            page.wait_for_function(
                "() => document.getElementById('cancel-demo')"
                "?.classList.contains('jbs-is-loading')"
            )
            page.wait_for_function(
                "() => document.getElementById('cancel-demo')"
                "?.getAttribute('aria-busy') === 'true'"
            )
            page.locator("#cancel-demo").get_by_role(
                "button", name="Fast Request"
            ).click()
            page.wait_for_function(
                "() => document.getElementById('cancel-demo-value')"
                "?.textContent?.trim() === 'fast'"
            )
            page.wait_for_function(
                "() => document.getElementById('cancel-demo')"
                "?.dataset.jbsPhase === 'success'"
            )
            page.wait_for_function(
                "() => document.getElementById('cancel-demo')"
                "?.getAttribute('aria-busy') === 'false'"
            )

            page.get_by_role("button", name="Simulate SSE Update").click()
            page.wait_for_function(
                "() => document.querySelector('#orders-table')"
                "?.textContent?.includes('SSE update #1:')"
            )

            page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_function(
                "() => document.getElementById('lazy-summary')"
                "?.textContent?.includes('Lazy summary ready.')"
            )
            assert_no_browser_errors(console_errors, page_errors)
        finally:
            browser.close()
