"""Record a short Playwright walkthrough video of the wrapper dev app."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path
from threading import Thread
from types import ModuleType

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server


def _load_example_app_module() -> ModuleType:
    app_path = Path(__file__).resolve().parents[1] / "examples" / "table_app" / "app.py"
    spec = importlib.util.spec_from_file_location("jbs_example_walkthrough", app_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load example app module from {app_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _prepare_example_app(module: ModuleType) -> None:
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


def _record_walkthrough(base_url: str, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record_dir = output_path.parent / "raw"
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True, exist_ok=True)

    video_path: Path | None = None

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1366, "height": 768},
            record_video_dir=str(record_dir),
            record_video_size={"width": 1366, "height": 768},
        )
        page = context.new_page()

        page.goto(base_url, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.getElementById('orders-table')"
            "?.dataset.jbsHydrated === 'true'"
        )
        page.wait_for_timeout(600)

        page.get_by_role("button", name="About Runtime").click()
        page.wait_for_timeout(900)
        page.keyboard.press("Escape")
        page.wait_for_timeout(400)

        page.get_by_role("button", name="Workbench").click()
        page.wait_for_timeout(900)
        page.locator("#orders-drawer").get_by_role("button", name="Close").click()
        page.wait_for_timeout(400)

        page.get_by_role("tab", name="Queued").click()
        page.wait_for_timeout(700)
        page.get_by_role("tab", name="All").click()
        page.wait_for_timeout(500)

        regex_input = page.locator("#orders-table input[name='regex']")
        regex_input.fill("Ada")
        page.wait_for_timeout(300)
        page.locator("#orders-table").get_by_role("button", name="Apply").click()
        page.wait_for_timeout(700)

        page.get_by_role("button", name="Simulate SSE Update").click()
        page.wait_for_timeout(700)

        page.locator("#live-table").scroll_into_view_if_needed()
        page.wait_for_timeout(250)
        page.get_by_role("button", name="Push Prepend Row").click()
        page.wait_for_timeout(500)
        page.get_by_role("button", name="Push Append Row").click()
        page.wait_for_timeout(500)

        page.locator(
            "#session-table [data-jbs-ms-input-name='page_size'] [data-jbs-ms-toggle]"
        ).click()
        page.wait_for_timeout(250)
        page.locator(
            "#session-table [data-jbs-ms-input-name='page_size'] "
            "[data-jbs-ms-option][data-jbs-ms-value='4']"
        ).click()
        page.locator("#session-table").get_by_role("button", name="Apply").click()
        page.wait_for_timeout(700)

        page.locator("#cancel-demo").get_by_role("button", name="Slow Request").click()
        page.wait_for_timeout(100)
        page.locator("#cancel-demo").get_by_role("button", name="Fast Request").click()
        page.wait_for_timeout(700)

        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1300)

        video = page.video
        context.close()
        if video is not None:
            video_path = Path(video.path())
        browser.close()

    if video_path is None:
        raise RuntimeError("Playwright did not produce a video artifact.")

    if output_path.exists():
        output_path.unlink()
    shutil.move(str(video_path), str(output_path))
    shutil.rmtree(record_dir, ignore_errors=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Record a walkthrough video of the wrapper dev app."
    )
    parser.add_argument(
        "--output",
        default=str(
            Path(__file__).resolve().parents[1]
            / "tmp"
            / "demo"
            / "wrapper-walkthrough.webm"
        ),
        help="Output video path (default: tmp/demo/wrapper-walkthrough.webm).",
    )
    args = parser.parse_args()

    output_path = Path(args.output).expanduser().resolve()

    module = _load_example_app_module()
    _prepare_example_app(module)

    server = make_server("127.0.0.1", 0, module.app, threaded=True)
    thread = Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()

    try:
        base_url = f"http://127.0.0.1:{server.server_port}"
        _record_walkthrough(base_url, output_path)
        print(output_path)
    finally:
        server.shutdown()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
