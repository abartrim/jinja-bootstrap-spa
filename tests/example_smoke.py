"""Shared browser smoke flow for the Python and Go example apps."""

from __future__ import annotations

import pytest
from playwright.sync_api import Error as PlaywrightError
from playwright.sync_api import sync_playwright

from tests.browser_assertions import assert_no_browser_errors, capture_browser_errors


def assert_example_smoke_flow(base_url: str) -> None:
    """Run the example-app smoke flow against a live server."""

    with sync_playwright() as playwright:
        try:
            browser = playwright.chromium.launch(headless=True)
        except PlaywrightError as exc:
            pytest.skip(f"Playwright browser is unavailable: {exc}")
        page = browser.new_page()
        console_errors, page_errors = capture_browser_errors(page)
        page.goto(base_url, wait_until="domcontentloaded")
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
            page.wait_for_selector("#foundation-gallery")
            page.wait_for_selector("#foundation-grid")
            page.wait_for_selector("#foundation-searchable-list")
            page.wait_for_selector("#foundation-timeline")
            page.wait_for_selector("#foundation-stacked-list")
            page.wait_for_selector("#foundation-tree-nav")
            page.wait_for_selector("#foundation-code-block")
            page.wait_for_selector("#foundation-facet-bar")
            page.wait_for_selector("#foundation-master-detail")
            page.wait_for_selector("#foundation-result-panel")
            page.wait_for_selector("#foundation-command-bar")
            page.wait_for_selector("#foundation-metric-grid")
            page.wait_for_selector("#foundation-activity-feed")
            page.wait_for_selector("#foundation-property-editor")
            page.wait_for_selector("#foundation-diff-view")
            page.wait_for_selector("#foundation-work-queue")
            page.wait_for_selector("#foundation-filterable-card-list")
            page.wait_for_selector("#foundation-inline-edit-shell")
            page.wait_for_selector("nav.navbar")

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

            page.locator("#orders-table").get_by_role("button", name="Next").click()
            page.wait_for_function(
                "() => document.querySelector('#orders-table')"
                "?.textContent?.includes('Page 2 of')"
            )
            page.locator("#orders-table").get_by_role("button", name="Previous").click()
            page.wait_for_function(
                "() => document.querySelector('#orders-table')"
                "?.textContent?.includes('Page 1 of')"
            )
            page.wait_for_function(
                "() => document.getElementById('orders-table')"
                "?.classList.contains('jbs-demo-cache-hit')"
            )
            page.wait_for_function(
                "() => document.getElementById('orders-table')"
                "?.dataset.jbsDemoLabel?.includes('Cache hit')"
            )

            page.get_by_role("button", name="Theme").click()
            page.locator("[data-bs-theme-value='dark']").click()
            page.wait_for_function(
                "() => document.documentElement"
                ".getAttribute('data-bs-theme') === 'dark'"
            )
            page.wait_for_selector("#orders-table")
            page.get_by_role("button", name="Theme").click()
            page.locator("[data-bs-theme-value='light']").click()
            page.wait_for_function(
                "() => document.documentElement"
                ".getAttribute('data-bs-theme') === 'light'"
            )
            page.wait_for_selector("#orders-table")

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

            page.locator("#foundation-gallery").scroll_into_view_if_needed()
            page.wait_for_selector("#foundation-stream-status")
            page.wait_for_selector("#foundation-toast")
            page.wait_for_selector("#foundation-chart-shell")
            page.wait_for_function(
                "() => document.querySelector('#foundation-facet-bar')"
                "?.textContent?.includes('Queued')"
            )
            page.wait_for_function(
                "() => document.querySelector('#foundation-command-bar')"
                "?.textContent?.includes('quick actions')"
            )
            page.wait_for_function(
                "() => document.querySelector("
                "'#foundation-tree-nav details'"
                ")?.hasAttribute('open')"
            )
            page.wait_for_function(
                "() => document.querySelector('#foundation-code-block')"
                "?.textContent?.includes('orders_component') || "
                "document.querySelector('#foundation-code-block')"
                "?.textContent?.includes('parse_table_state')"
            )
            page.wait_for_function(
                "() => document.querySelector('#foundation-result-panel')"
                "?.textContent?.includes('Query Result')"
            )
            page.wait_for_function(
                "() => document.querySelector('#foundation-filterable-card-list')"
                "?.textContent?.includes('Review Queue')"
            )
            page.wait_for_function(
                "() => document.querySelector('#foundation-diff-view-after')"
                "?.textContent?.includes(\"status = 'open'\")"
            )
            foundation_cards = page.locator(
                "#foundation-filterable-card-list [data-jbs-searchable-list-input]"
            )
            foundation_cards.fill("dashboard")
            page.wait_for_function(
                "() => {"
                "  const items = Array.from(document.querySelectorAll("
                "    '#foundation-filterable-card-list [data-jbs-searchable-item]'"
                "  ));"
                "  const visible = items.filter((item) => !item.hidden);"
                "  return visible.length === 1 && "
                "    visible[0]?.textContent?.includes('Migration Dashboard');"
                "}"
            )
            foundation_cards.fill("")
            page.wait_for_function(
                "() => {"
                "  const items = Array.from(document.querySelectorAll("
                "    '#foundation-filterable-card-list [data-jbs-searchable-item]'"
                "  ));"
                "  return items.filter((item) => !item.hidden).length === 3;"
                "}"
            )
            page.locator("#foundation-work-queue").scroll_into_view_if_needed()
            queue_rows = page.locator(
                "#foundation-work-queue [data-jbs-table-select-row]"
            )
            queue_rows.nth(0).click()
            queue_rows.nth(1).click()
            page.wait_for_function(
                "() => document.querySelector("
                "'#foundation-work-queue [data-jbs-selection-count]'"
                ")"
                "?.textContent?.includes('2 selected')"
            )
            page.locator("#foundation-work-queue").get_by_role(
                "button", name="Next"
            ).click()
            page.wait_for_function(
                "() => document.querySelector('#foundation-work-queue')"
                "?.textContent?.includes('Page 2 of 2')"
            )
            page.wait_for_function(
                "() => document.querySelector("
                "'#foundation-work-queue [data-jbs-selection-count]'"
                ")"
                "?.textContent?.includes('2 selected')"
            )
            page.wait_for_function(
                "() => document.querySelector('#foundation-work-queue')"
                "?.textContent?.includes("
                "'2 selected across refreshes and page changes.'"
                ")"
            )
            foundation_search = page.locator(
                "#foundation-searchable-list [data-jbs-searchable-list-input]"
            )
            foundation_search.fill("workspace")
            page.wait_for_function(
                "() => {"
                "  const items = Array.from(document.querySelectorAll("
                "    '#foundation-searchable-list [data-jbs-searchable-item]'"
                "  ));"
                "  const visible = items.filter((item) => !item.hidden);"
                "  return visible.length === 1 && "
                "    visible[0]?.textContent?.includes('Workspace Layout');"
                "}"
            )
            foundation_search.fill("missing-term")
            page.wait_for_function(
                "() => !document.querySelector("
                "  '#foundation-searchable-list [data-jbs-searchable-list-empty]'"
                ")?.hidden"
            )
            foundation_search.fill("")
            page.wait_for_function(
                "() => {"
                "  const items = Array.from(document.querySelectorAll("
                "    '#foundation-searchable-list [data-jbs-searchable-item]'"
                "  ));"
                "  return items.filter((item) => !item.hidden).length === 3;"
                "}"
            )
            page.get_by_role("button", name="Open Workspace Modal").click()
            page.wait_for_function(
                "() => !document.getElementById('foundation-workspace-modal')?.hidden"
            )
            page.locator("#foundation-workspace-modal").get_by_role(
                "button", name="Apply Layout"
            ).click()
            page.wait_for_function(
                "() => !!document.getElementById('foundation-workspace-modal')?.hidden"
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
                "?.textContent?.trim() == 'fast'"
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
            page.wait_for_function(
                "() => document.getElementById('orders-status-toast')"
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
