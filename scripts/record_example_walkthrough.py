"""Record a narrated walkthrough video of the wrapper dev app."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path
from threading import Thread
from types import ModuleType

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from playwright.sync_api import Page, sync_playwright
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


def _pause(page: Page, milliseconds: int, pace: float) -> None:
    page.wait_for_timeout(max(1, int(milliseconds * pace)))


def _set_caption(
    page: Page,
    *,
    title: str,
    body: str,
    step: int | None = None,
    total_steps: int | None = None,
) -> None:
    page.evaluate(
        """
        ({ title, body, step, total_steps }) => {
          let root = document.getElementById("jbs-demo-caption");
          if (!root) {
            root = document.createElement("aside");
            root.id = "jbs-demo-caption";
            root.style.position = "fixed";
            root.style.right = "16px";
            root.style.bottom = "16px";
            root.style.zIndex = "9999";
            root.style.maxWidth = "420px";
            root.style.padding = "12px 14px";
            root.style.borderRadius = "10px";
            root.style.background = "rgba(15, 23, 42, 0.92)";
            root.style.color = "#f8fafc";
            root.style.boxShadow = "0 10px 32px rgba(2, 6, 23, 0.35)";
            root.style.backdropFilter = "blur(2px)";
            root.style.fontFamily = (
              "system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial, sans-serif"
            );
            root.innerHTML = `
              <div id="jbs-demo-caption-step"
                   style="font-size:12px;opacity:0.8;margin-bottom:4px;"></div>
              <h2 id="jbs-demo-caption-title"
                  style="font-size:16px;line-height:1.25;margin:0 0 6px 0;"></h2>
              <p id="jbs-demo-caption-body"
                 style="font-size:13px;line-height:1.45;margin:0;white-space:pre-line;"></p>
            `;
            document.body.appendChild(root);
          }

          const stepNode = document.getElementById("jbs-demo-caption-step");
          const titleNode = document.getElementById("jbs-demo-caption-title");
          const bodyNode = document.getElementById("jbs-demo-caption-body");
          if (!stepNode || !titleNode || !bodyNode) {
            return;
          }

          if (step !== null && total_steps !== null) {
            stepNode.textContent = `Step ${step} / ${total_steps}`;
            stepNode.style.display = "block";
          } else {
            stepNode.textContent = "";
            stepNode.style.display = "none";
          }
          titleNode.textContent = title;
          bodyNode.textContent = body;
        }
        """,
        {
            "title": title,
            "body": body,
            "step": step,
            "total_steps": total_steps,
        },
    )


def _show_step(
    page: Page,
    *,
    title: str,
    body: str,
    hold_ms: int,
    pace: float,
    step: int | None = None,
    total_steps: int | None = None,
) -> None:
    _set_caption(page, title=title, body=body, step=step, total_steps=total_steps)
    _pause(page, hold_ms, pace)


def _record_walkthrough(base_url: str, output_path: Path, pace: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record_dir = output_path.parent / "raw"
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True, exist_ok=True)

    total_steps = 8
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
        _pause(page, 700, pace)

        _show_step(
            page,
            title="What You Are About To See",
            body=(
                "A guided pass through the jinja-bootstrap-spa runtime:\n"
                "1) table state + filters,\n"
                "2) SSE refresh/append/prepend,\n"
                "3) session persistence,\n"
                "4) stale-request cancellation,\n"
                "5) lazy hydration."
            ),
            hold_ms=3600,
            pace=pace,
        )

        _show_step(
            page,
            title="Step 1: Runtime Overlays and Table State",
            body=(
                "Open modal/drawer, then use tabs and filters to trigger "
                "component swaps."
            ),
            hold_ms=1700,
            pace=pace,
            step=1,
            total_steps=total_steps,
        )
        page.get_by_role("button", name="About Runtime").click()
        _pause(page, 1500, pace)
        page.keyboard.press("Escape")
        _pause(page, 650, pace)
        page.get_by_role("button", name="Workbench").click()
        _pause(page, 1500, pace)
        page.locator("#orders-drawer").get_by_role("button", name="Close").click()
        _pause(page, 700, pace)
        page.get_by_role("tab", name="Queued").click()
        _pause(page, 1200, pace)
        page.get_by_role("tab", name="All").click()
        _pause(page, 900, pace)
        regex_input = page.locator("#orders-table input[name='regex']")
        regex_input.fill("Ada")
        _pause(page, 650, pace)
        page.locator("#orders-table").get_by_role("button", name="Apply").click()
        _pause(page, 1400, pace)

        _show_step(
            page,
            title="Step 2: SSE Refresh on Main Table",
            body=(
                "A server-side update triggers a targeted table refresh without "
                "full-page reload."
            ),
            hold_ms=1300,
            pace=pace,
            step=2,
            total_steps=total_steps,
        )
        page.get_by_role("button", name="Simulate SSE Update").click()
        _pause(page, 1600, pace)

        _show_step(
            page,
            title="Step 3: Prepend and Append Stream Modes",
            body="Watch new rows animate into place in the live stream tables.",
            hold_ms=1300,
            pace=pace,
            step=3,
            total_steps=total_steps,
        )
        page.locator("#live-table").scroll_into_view_if_needed()
        _pause(page, 700, pace)
        page.get_by_role("button", name="Push Prepend Row").click()
        _pause(page, 1500, pace)
        page.get_by_role("button", name="Push Append Row").click()
        _pause(page, 1500, pace)

        _show_step(
            page,
            title="Step 4: Session Persistence",
            body=(
                "Change table page size and apply. This state survives page "
                "reload via sessionStorage."
            ),
            hold_ms=1200,
            pace=pace,
            step=4,
            total_steps=total_steps,
        )
        page.locator(
            "#session-table [data-jbs-ms-input-name='page_size'] [data-jbs-ms-toggle]"
        ).click()
        _pause(page, 450, pace)
        page.locator(
            "#session-table [data-jbs-ms-input-name='page_size'] "
            "[data-jbs-ms-option][data-jbs-ms-value='4']"
        ).click()
        page.locator("#session-table").get_by_role("button", name="Apply").click()
        _pause(page, 1500, pace)

        _show_step(
            page,
            title="Step 5: Request Cancellation Guard",
            body=(
                "Slow request starts first, then fast request wins and stale "
                "response is ignored."
            ),
            hold_ms=1200,
            pace=pace,
            step=5,
            total_steps=total_steps,
        )
        page.locator("#cancel-demo").get_by_role("button", name="Slow Request").click()
        _pause(page, 250, pace)
        page.locator("#cancel-demo").get_by_role("button", name="Fast Request").click()
        _pause(page, 1700, pace)

        _show_step(
            page,
            title="Step 6: Lazy Hydration",
            body=(
                "Scroll to the lazy component. The server fetch happens on first "
                "viewport entry."
            ),
            hold_ms=1200,
            pace=pace,
            step=6,
            total_steps=total_steps,
        )
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        _pause(page, 2200, pace)

        _show_step(
            page,
            title="Step 7: Animated Repaint Cues",
            body=(
                "Updated components and incoming stream rows pulse briefly to make "
                "repainted areas obvious during demos and debugging."
            ),
            hold_ms=2000,
            pace=pace,
            step=7,
            total_steps=total_steps,
        )

        _show_step(
            page,
            title="What You Just Watched",
            body=(
                "You saw server-rendered components behave like an SPA with "
                "predictable state,\n"
                "incremental updates, and explicit UX cues.\n"
                "More info: github.com/abartrim/jinja-bootstrap-spa"
            ),
            hold_ms=4200,
            pace=pace,
            step=8,
            total_steps=total_steps,
        )

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
    parser.add_argument(
        "--pace",
        type=float,
        default=1.8,
        help="Timing multiplier for pauses/captions (default: 1.8).",
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
        _record_walkthrough(base_url, output_path, max(0.1, args.pace))
        print(output_path)
    finally:
        server.shutdown()
        thread.join(timeout=5)


if __name__ == "__main__":
    main()
