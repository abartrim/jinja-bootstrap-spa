"""Record a narrated walkthrough video of the wrapper dev app."""

from __future__ import annotations

import argparse
import importlib.util
import shutil
from pathlib import Path
from threading import Thread
from types import ModuleType

from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from playwright.sync_api import Locator, Page, sync_playwright
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


def _install_recording_mode(page: Page) -> None:
    page.evaluate(
        """
        () => {
          const styleId = "jbs-demo-recording-style";
          if (!document.getElementById(styleId)) {
            const style = document.createElement("style");
            style.id = styleId;
            style.textContent = `
              #showcase-journey {
                display: none !important;
              }

              .jbs-hero {
                margin-bottom: 1rem !important;
              }

              .jbs-step {
                padding: 0.7rem 0.9rem !important;
              }

              #jbs-demo-caption {
                pointer-events: none;
              }

              #jbs-demo-pointer,
              #jbs-demo-pointer-ring {
                position: fixed;
                top: 0;
                left: 0;
                z-index: 10000;
                pointer-events: none;
                transform: translate(-50%, -50%);
                transition:
                  left 240ms ease,
                  top 240ms ease,
                  opacity 180ms ease,
                  width 180ms ease,
                  height 180ms ease;
              }

              #jbs-demo-pointer {
                width: 18px;
                height: 18px;
                border-radius: 999px;
                background: rgba(255, 255, 255, 0.96);
                border: 3px solid rgba(13, 110, 253, 0.95);
                box-shadow: 0 0.35rem 1rem rgba(2, 6, 23, 0.28);
              }

              #jbs-demo-pointer-ring {
                width: 42px;
                height: 42px;
                border-radius: 999px;
                border: 2px solid rgba(255, 193, 7, 0.85);
                background: rgba(255, 193, 7, 0.08);
                box-shadow: 0 0 0 0 rgba(255, 193, 7, 0.25);
              }
            `;
            document.head.appendChild(style);
          }

          const ensureNode = (id) => {
            let node = document.getElementById(id);
            if (!node) {
              node = document.createElement("div");
              node.id = id;
              document.body.appendChild(node);
            }
            return node;
          };

          const pointer = ensureNode("jbs-demo-pointer");
          const ring = ensureNode("jbs-demo-pointer-ring");
          pointer.style.opacity = "1";
          ring.style.opacity = "1";

          window.__jbsDemoPointer = {
            move(x, y) {
              pointer.style.left = `${x}px`;
              pointer.style.top = `${y}px`;
              ring.style.left = `${x}px`;
              ring.style.top = `${y}px`;
            },
            click() {
              ring.animate(
                [
                  {
                    transform: "translate(-50%, -50%) scale(0.9)",
                    opacity: 0.95,
                  },
                  {
                    transform: "translate(-50%, -50%) scale(1.35)",
                    opacity: 0.1,
                  },
                ],
                {
                  duration: 450,
                  easing: "ease-out",
                },
              );
            },
          };
        }
        """
    )


def _focus_locator(
    page: Page,
    locator: Locator,
    pace: float,
    hold_ms: int = 650,
    position: str = "center",
) -> None:
    locator.evaluate(
        """
        (element, position) => {
          const rect = element.getBoundingClientRect();
          const absoluteTop = window.scrollY + rect.top;
          const viewportHeight = window.innerHeight;
          const elementHeight = Math.max(rect.height, 1);
          const centeredTop = absoluteTop - ((viewportHeight - elementHeight) / 2);
          const tallElementTop = absoluteTop - Math.max(64, viewportHeight * 0.12);
          const topAnchored = absoluteTop - Math.max(40, viewportHeight * 0.14);
          const bottomAnchored = absoluteTop - Math.max(220, viewportHeight * 0.58);
          let targetTop = elementHeight > viewportHeight * 0.72
            ? tallElementTop
            : centeredTop;

          if (position === "top") {
            targetTop = topAnchored;
          } else if (position === "bottom") {
            targetTop = bottomAnchored;
          }

          window.scrollTo({
            top: Math.max(0, targetTop),
            behavior: "instant",
          });
        }
        """,
        position,
    )
    _pause(page, hold_ms, pace)


def _move_pointer_to(page: Page, locator: Locator, pace: float, hold_ms: int = 420) -> None:
    box = locator.bounding_box()
    if box is None:
        raise RuntimeError("Unable to resolve bounding box for demo pointer movement.")
    x = box["x"] + (box["width"] / 2)
    y = box["y"] + (box["height"] / 2)
    page.mouse.move(x, y, steps=max(24, int(36 * pace)))
    page.evaluate(
        "({ x, y }) => window.__jbsDemoPointer?.move(x, y)",
        {"x": x, "y": y},
    )
    _pause(page, hold_ms, pace)


def _guided_click(page: Page, locator: Locator, pace: float, hold_ms: int = 420) -> None:
    _move_pointer_to(page, locator, pace, hold_ms=hold_ms)
    locator.click()
    page.evaluate("() => window.__jbsDemoPointer?.click()")
    _pause(page, 320, pace)


def _record_walkthrough(base_url: str, output_path: Path, pace: float) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    record_dir = output_path.parent / "raw"
    if record_dir.exists():
        shutil.rmtree(record_dir)
    record_dir.mkdir(parents=True, exist_ok=True)

    total_steps = 10
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
        _install_recording_mode(page)
        page.mouse.move(120, 120)
        page.evaluate("() => window.__jbsDemoPointer?.move(120, 120)")
        _pause(page, 700, pace)

        _show_step(
            page,
            title="What You Are About To See",
            body=(
                "A guided pass through the jinja-bootstrap-spa runtime:\n"
                "1) table state + filters,\n"
                "2) page caching,\n"
                "3) SSE refresh/append/prepend,\n"
                "4) session persistence,\n"
                "5) stale-request cancellation,\n"
                "6) lazy hydration,\n"
                "7) the new foundation component gallery."
            ),
            hold_ms=3600,
            pace=pace,
        )

        _show_step(
            page,
            title="Step 1: Runtime Overlays and Table State",
            body=(
                "Open modal and drawer, then use segmented controls and row "
                "menus to show the server-driven table surface."
            ),
            hold_ms=1700,
            pace=pace,
            step=1,
            total_steps=total_steps,
        )
        _focus_locator(
            page,
            page.get_by_role("button", name="About Runtime"),
            pace,
            position="top",
        )
        _guided_click(page, page.get_by_role("button", name="About Runtime"), pace)
        _pause(page, 1500, pace)
        page.keyboard.press("Escape")
        _pause(page, 650, pace)
        _guided_click(page, page.get_by_role("button", name="Workbench"), pace)
        _pause(page, 1500, pace)
        _guided_click(
            page,
            page.locator("#orders-drawer").get_by_role("button", name="Close"),
            pace,
        )
        _pause(page, 700, pace)
        _focus_locator(page, page.locator("#orders-status-tabs"), pace)
        _guided_click(page, page.get_by_role("tab", name="Queued"), pace)
        _pause(page, 1200, pace)
        _guided_click(page, page.get_by_role("tab", name="All"), pace)
        _pause(page, 700, pace)
        _focus_locator(
            page,
            page.locator("#orders-table [data-jbs-menu-trigger]").first,
            pace,
        )
        _guided_click(
            page,
            page.locator("#orders-table [data-jbs-menu-trigger]").first,
            pace,
        )
        _pause(page, 1400, pace)
        page.keyboard.press("Escape")
        _pause(page, 500, pace)

        _show_step(
            page,
            title="Step 2: Cached Table Paging",
            body=(
                "Move forward, back, then forward again. Returning to a known "
                "page shows the cache-hit cue instead of a full visible reload."
            ),
            hold_ms=1300,
            pace=pace,
            step=2,
            total_steps=total_steps,
        )
        _focus_locator(page, page.locator("#orders-table .card-footer"), pace)
        next_button = page.locator("#orders-table").get_by_role("button", name="Next")
        previous_button = page.locator("#orders-table").get_by_role(
            "button", name="Previous"
        )
        _guided_click(page, next_button, pace)
        page.wait_for_function(
            "() => document.querySelector('#orders-table')"
            "?.textContent?.includes('Page 2 of')"
        )
        _pause(page, 900, pace)
        _guided_click(page, previous_button, pace)
        page.wait_for_function(
            "() => document.querySelector('#orders-table')"
            "?.textContent?.includes('Page 1 of')"
        )
        _pause(page, 900, pace)
        _guided_click(page, next_button, pace)
        page.wait_for_function(
            "() => document.getElementById('orders-table')"
            "?.dataset.jbsDemoLabel?.includes('Cache hit')"
        )
        _pause(page, 1500, pace)

        _show_step(
            page,
            title="Step 3: SSE Refresh on Main Table",
            body=(
                "A server-side update triggers a targeted table refresh without "
                "reloading the full page."
            ),
            hold_ms=1300,
            pace=pace,
            step=3,
            total_steps=total_steps,
        )
        _focus_locator(
            page,
            page.locator("#orders-table > .card-header"),
            pace,
        )
        _guided_click(page, page.get_by_role("button", name="Simulate SSE Update"), pace)
        _pause(page, 1600, pace)

        _show_step(
            page,
            title="Step 4: Prepend and Append Stream Modes",
            body="Watch new rows animate into place in the live stream tables.",
            hold_ms=1300,
            pace=pace,
            step=4,
            total_steps=total_steps,
        )
        _focus_locator(page, page.locator("#push-live-row"), pace)
        _pause(page, 700, pace)
        _guided_click(page, page.get_by_role("button", name="Push Prepend Row"), pace)
        _pause(page, 1500, pace)
        _focus_locator(page, page.locator("#push-live-append-row"), pace)
        _guided_click(page, page.get_by_role("button", name="Push Append Row"), pace)
        _pause(page, 1500, pace)

        _show_step(
            page,
            title="Step 5: Session Persistence",
            body=(
                "Change table page size and apply. This state survives page "
                "reload via sessionStorage."
            ),
            hold_ms=1200,
            pace=pace,
            step=5,
            total_steps=total_steps,
        )
        _focus_locator(page, page.locator("#session-table"), pace)
        _guided_click(
            page,
            page.locator(
                "#session-table [data-jbs-ms-input-name='page_size'] [data-jbs-ms-toggle]"
            ),
            pace,
        )
        _pause(page, 450, pace)
        _guided_click(
            page,
            page.locator(
                "#session-table [data-jbs-ms-input-name='page_size'] "
                "[data-jbs-ms-option][data-jbs-ms-value='4']"
            ),
            pace,
        )
        _guided_click(page, page.locator("#session-table").get_by_role("button", name="Apply"), pace)
        _pause(page, 1500, pace)

        _show_step(
            page,
            title="Step 6: Request Cancellation Guard",
            body=(
                "Slow request starts first, then fast request wins and stale "
                "response is ignored."
            ),
            hold_ms=1200,
            pace=pace,
            step=6,
            total_steps=total_steps,
        )
        _focus_locator(page, page.locator("#cancel-demo"), pace)
        _guided_click(
            page,
            page.locator("#cancel-demo").get_by_role("button", name="Slow Request"),
            pace,
        )
        _pause(page, 250, pace)
        _guided_click(
            page,
            page.locator("#cancel-demo").get_by_role("button", name="Fast Request"),
            pace,
        )
        _pause(page, 1700, pace)

        page.goto(base_url, wait_until="domcontentloaded")
        page.wait_for_function(
            "() => document.getElementById('orders-table')"
            "?.dataset.jbsHydrated === 'true'"
        )
        page.wait_for_function(
            "() => document.getElementById('lazy-summary')"
            "?.dataset.jbsHydrated !== 'true'"
        )
        _install_recording_mode(page)
        page.evaluate("() => window.__jbsDemoPointer?.move(120, 120)")
        _show_step(
            page,
            title="Step 7: Lazy Hydration",
            body=(
                "On a fresh page state, this component stays dormant until it "
                "enters the viewport for the first time."
            ),
            hold_ms=1200,
            pace=pace,
            step=7,
            total_steps=total_steps,
        )
        _focus_locator(
            page,
            page.locator("#lazy-summary"),
            pace,
            hold_ms=900,
            position="bottom",
        )
        _pause(page, 2200, pace)

        _show_step(
            page,
            title="Step 8: Foundation Component Gallery",
            body=(
                "The wrapper now shows the generic shells: stat cards, stream "
                "status, detail lists, chart shell, data grid, searchable list, "
                "split panels, and workspace modal."
            ),
            hold_ms=2000,
            pace=pace,
            step=8,
            total_steps=total_steps,
        )
        _focus_locator(
            page,
            page.locator("#foundation-gallery"),
            pace,
            hold_ms=900,
            position="top",
        )
        _pause(page, 1200, pace)
        foundation_search = page.locator(
            "#foundation-searchable-list [data-jbs-searchable-list-input]"
        )
        _guided_click(page, foundation_search, pace)
        foundation_search.fill("workspace")
        _pause(page, 1200, pace)
        foundation_search.fill("")
        _pause(page, 700, pace)
        _guided_click(page, page.get_by_role("button", name="Open Workspace Modal"), pace)
        _pause(page, 1800, pace)
        _guided_click(
            page,
            page.locator("#foundation-workspace-modal").get_by_role(
                "button", name="Apply Layout"
            ),
            pace,
        )
        _pause(page, 900, pace)

        _show_step(
            page,
            title="Step 9: Animated Repaint Cues",
            body=(
                "Two quick refreshes show both the swap and the no-change cue, so "
                "watchers can tell whether the component actually repainted."
            ),
            hold_ms=2000,
            pace=pace,
            step=9,
            total_steps=total_steps,
        )
        _focus_locator(
            page,
            page.locator("#orders-table > .card-header"),
            pace,
        )
        refresh_button = page.locator("#orders-table").get_by_role(
            "button", name="Refresh Table"
        )
        _guided_click(page, refresh_button, pace)
        _pause(page, 1400, pace)
        _guided_click(page, refresh_button, pace)
        _pause(page, 1800, pace)

        _show_step(
            page,
            title="What You Just Watched",
            body=(
                "You saw server-rendered components behave like an SPA with "
                "predictable state,\n"
                "incremental updates, cache-aware paging, and explicit UX cues.\n"
                "More info: github.com/abartrim/jinja-bootstrap-spa"
            ),
            hold_ms=4200,
            pace=pace,
            step=10,
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
