"""Browser smoke tests for the real wrapper dev app in examples/table_app."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from threading import Thread
from types import ModuleType

import pytest
from jinja2 import ChoiceLoader, FileSystemLoader, PackageLoader
from werkzeug.serving import make_server

from tests.example_smoke import assert_example_smoke_flow


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
    assert_example_smoke_flow(example_live_server)
