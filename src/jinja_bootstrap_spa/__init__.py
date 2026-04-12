"""Public package interface for jinja-bootstrap-spa.

The package intentionally exposes a narrow API:

- macro registration helpers for Jinja environments
- HTML attribute helpers for HTMX-style incremental updates

AI agents can build on top of these primitives without needing to understand a
large framework surface area.
"""

from .macros.bootstrap import (
    BOOTSTRAP_MACROS,
    MACRO_TEMPLATE_NAME,
    register_bootstrap_macros,
)
from .runtime.htmx import attrs_to_html, hx_attrs

__all__ = [
    "BOOTSTRAP_MACROS",
    "MACRO_TEMPLATE_NAME",
    "attrs_to_html",
    "hx_attrs",
    "register_bootstrap_macros",
]

__version__ = "0.1.0"
