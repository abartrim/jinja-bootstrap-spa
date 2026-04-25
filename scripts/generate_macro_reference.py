"""Generate the public Jinja macro API reference."""

from __future__ import annotations

import re
from pathlib import Path

from jinja_bootstrap_spa.macros.bootstrap import BOOTSTRAP_MACROS

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "docs" / "api_reference.md"
MACRO_RE = re.compile(r"{%-?\s*macro\s+(\w+)\((.*?)\)\s*-?%}", re.DOTALL)


def _normalize_signature(raw_signature: str) -> str:
    """Collapse a Jinja macro signature into one stable Markdown line."""

    return " ".join(raw_signature.replace("\n", " ").split())


def generate_reference() -> str:
    """Return the rendered macro reference document."""

    rows = []
    for name, signature in MACRO_RE.findall(BOOTSTRAP_MACROS):
        rows.append((name, _normalize_signature(signature)))

    lines = [
        "# Macro API Reference",
        "",
        "This file is generated from the canonical macro source in",
        "`src/jinja_bootstrap_spa/macros/bootstrap.py`.",
        "",
        "Regenerate it with:",
        "",
        "```bash",
        ".venv/bin/python scripts/generate_macro_reference.py",
        "```",
        "",
        "| Macro | Signature |",
        "| --- | --- |",
    ]

    for name, signature in rows:
        lines.append(f"| `{name}` | `{name}({signature})` |")

    lines.extend(
        [
            "",
            "## Authoring Notes",
            "",
            "- Prefer these macros before writing raw Bootstrap markup.",
            "- Use app-level macros to compose domain-specific behavior on top "
            "of these primitives.",
            "- Preserve generated `data-jbs-*` attributes when wrapping "
            "interactive components.",
            "- Keep fragment endpoints server-rendered and deterministic.",
            "",
        ]
    )

    return "\n".join(lines)


def main() -> None:
    """Write the generated reference to disk."""

    OUTPUT_PATH.write_text(generate_reference(), encoding="utf-8")


if __name__ == "__main__":
    main()
