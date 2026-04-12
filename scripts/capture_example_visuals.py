"""Capture wrapper app screenshots for manual visual inspection."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from threading import Thread
from types import ModuleType

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server


def load_example_app_module() -> ModuleType:
    """Load the example wrapper app module from examples/table_app/app.py."""

    app_path = Path(__file__).resolve().parents[1] / "examples" / "table_app" / "app.py"
    spec = importlib.util.spec_from_file_location(
        "jbs_example_table_app_visual", app_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load example app module from {app_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def reset_example_state(module: ModuleType) -> None:
    """Reset module-level mutable state for repeatable screenshots."""

    module.LAST_PUSH_MESSAGE = ""
    module.PUSH_COUNTER = 0
    module.LIVE_PUSH_COUNTER = 0
    module.LIVE_ROWS = [
        {"entry": "boot complete", "source": "runtime"},
        {"entry": "table hydrated", "source": "runtime"},
    ]
    module.APPEND_PUSH_COUNTER = 0
    module.APPEND_ROWS = [
        {"entry": "append channel online", "source": "runtime"},
        {"entry": "append stream ready", "source": "runtime"},
    ]
    template_dir = (
        Path(__file__).resolve().parents[1] / "examples" / "table_app" / "templates"
    )
    module.app.jinja_loader = ChoiceLoader(
        [
            FileSystemLoader(str(template_dir)),
            PackageLoader("jinja_bootstrap_spa", "templates"),
        ]
    )


def run() -> None:
    """Start the example app and capture desktop/mobile screenshots."""

    module = load_example_app_module()
    reset_example_state(module)

    output_dir = Path(__file__).resolve().parents[1] / "tmp" / "visual"
    output_dir.mkdir(parents=True, exist_ok=True)

    server = make_server("127.0.0.1", 0, module.app, threaded=True)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    base_url = f"http://127.0.0.1:{server.server_port}"

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)

            desktop = browser.new_page(viewport={"width": 1600, "height": 1600})
            desktop.goto(base_url, wait_until="domcontentloaded")
            desktop.wait_for_selector("#orders-table")
            desktop.wait_for_function(
                "() => document.getElementById('orders-table')"
                "?.dataset.jbsHydrated === 'true'"
            )
            desktop.screenshot(
                path=str(output_dir / "desktop_full.png"), full_page=True
            )

            mobile = browser.new_page(
                viewport={"width": 430, "height": 1800},
                user_agent=(
                    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 "
                    "Mobile/15E148 Safari/604.1"
                ),
            )
            mobile.goto(base_url, wait_until="domcontentloaded")
            mobile.wait_for_selector("#orders-table")
            mobile.wait_for_function(
                "() => document.getElementById('orders-table')"
                "?.dataset.jbsHydrated === 'true'"
            )
            mobile.screenshot(path=str(output_dir / "mobile_full.png"), full_page=True)

            browser.close()
    finally:
        server.shutdown()
        thread.join(timeout=5)


if __name__ == "__main__":
    run()
