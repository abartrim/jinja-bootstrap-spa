"""Browser smoke tests for the Go MiniJinja example app."""

from __future__ import annotations

import os
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from tests.example_smoke import assert_example_smoke_flow


def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_server(url: str, process: subprocess.Popen[str]) -> None:
    deadline = time.time() + 30
    while time.time() < deadline:
        if process.poll() is not None:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"Go example server exited early:\n{output}")
        try:
            with urllib.request.urlopen(url, timeout=1):
                return
        except (urllib.error.URLError, ConnectionError):
            time.sleep(0.2)
    output = process.stdout.read() if process.stdout else ""
    raise RuntimeError(f"Timed out waiting for Go example server:\n{output}")


def go_example_live_server() -> tuple[subprocess.Popen[str], str]:
    repo_root = Path(__file__).resolve().parents[1]
    port = _pick_free_port()
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["GOCACHE"] = "/tmp/jbs-go-build"
    env["GOSUMDB"] = "off"

    process = subprocess.Popen(
        ["go", "run", "./examples/go_table_app"],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    base_url = f"http://127.0.0.1:{port}"
    _wait_for_server(base_url, process)
    return process, base_url


def test_go_example_app_smoke_flow() -> None:
    process, base_url = go_example_live_server()
    try:
        assert_example_smoke_flow(base_url)
    finally:
        process.terminate()
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)
