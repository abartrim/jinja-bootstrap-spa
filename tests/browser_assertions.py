"""Helpers for asserting clean browser runtime execution in Playwright tests."""

from __future__ import annotations

from collections.abc import Sequence

from playwright.sync_api import ConsoleMessage
from playwright.sync_api import Page


def capture_browser_errors(page: Page) -> tuple[list[str], list[str]]:
    """Attach listeners for console errors and page-level uncaught exceptions."""

    console_errors: list[str] = []
    page_errors: list[str] = []

    def on_console(message: ConsoleMessage) -> None:
        if message.type != "error":
            return
        text = message.text.strip()
        if not text or "favicon.ico" in text:
            return
        console_errors.append(text)

    def on_pageerror(error: object) -> None:
        page_errors.append(str(error))

    page.on("console", on_console)
    page.on("pageerror", on_pageerror)
    return console_errors, page_errors


def assert_no_browser_errors(
    console_errors: Sequence[str], page_errors: Sequence[str]
) -> None:
    """Fail the test when browser console/page errors were emitted."""

    issues = [f"console: {entry}" for entry in console_errors]
    issues.extend(f"pageerror: {entry}" for entry in page_errors)
    assert not issues, "Unexpected browser errors:\n" + "\n".join(issues)
