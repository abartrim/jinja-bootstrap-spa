"""Accessibility assertions shared by browser tests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

AXE_CORE_PATH = (
    Path(__file__).resolve().parents[1] / "node_modules" / "axe-core" / "axe.min.js"
)


def assert_no_critical_accessibility_violations(page: Page) -> None:
    """Run axe-core and fail on serious or critical accessibility violations."""

    if not AXE_CORE_PATH.exists():
        raise AssertionError(
            "axe-core is not installed; run npm install before browser tests"
        )

    page.add_script_tag(path=str(AXE_CORE_PATH))
    results: dict[str, Any] = page.evaluate(
        """async () => await window.axe.run(document, {
          resultTypes: ["violations"],
          runOnly: {
            type: "tag",
            values: ["wcag2a", "wcag2aa", "best-practice"]
          }
        })"""
    )
    violations = [
        violation
        for violation in results.get("violations", [])
        if violation.get("impact") in {"serious", "critical"}
    ]

    if not violations:
        return

    summary = []
    for violation in violations:
        targets = [
            ", ".join(node.get("target", [])) for node in violation.get("nodes", [])[:5]
        ]
        summary.append(
            {
                "id": violation.get("id"),
                "impact": violation.get("impact"),
                "description": violation.get("description"),
                "targets": targets,
            }
        )

    raise AssertionError(
        "Serious accessibility violations found:\n"
        + json.dumps(summary, indent=2, sort_keys=True)
    )
