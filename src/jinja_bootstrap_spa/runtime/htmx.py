"""Helpers for HTMX-style incremental updates.

The functions here stay intentionally small. They do not depend on a specific web
framework and only help assemble HTML attributes that can be passed into Jinja
macros or templates.
"""

from __future__ import annotations

from typing import Any

from markupsafe import Markup, escape


def hx_attrs(
    *,
    get: str | None = None,
    post: str | None = None,
    target: str | None = None,
    swap: str | None = None,
    trigger: str | None = None,
    select: str | None = None,
    push_url: bool | None = None,
    include: str | None = None,
) -> dict[str, str]:
    """Build a dictionary of ``hx-*`` attributes.

    This helper is convenient when Python code needs to hand structured HTMX
    attributes to a template or macro without manually spelling each attribute.
    Only keys with non-``None`` values are returned.
    """

    attrs: dict[str, str] = {}
    if get is not None:
        attrs["hx-get"] = get
    if post is not None:
        attrs["hx-post"] = post
    if target is not None:
        attrs["hx-target"] = target
    if swap is not None:
        attrs["hx-swap"] = swap
    if trigger is not None:
        attrs["hx-trigger"] = trigger
    if select is not None:
        attrs["hx-select"] = select
    if push_url is not None:
        attrs["hx-push-url"] = str(push_url).lower()
    if include is not None:
        attrs["hx-include"] = include
    return attrs


def attrs_to_html(attrs: dict[str, Any]) -> Markup:
    """Convert a dictionary of HTML attributes into a safe attribute string.

    Example
    -------
    >>> attrs_to_html({"hx-get": "/partial", "hx-target": "#card"})
    Markup('hx-get="/partial" hx-target="#card"')
    """

    parts = [
        f'{escape(str(key))}="{escape(str(value))}"'
        for key, value in attrs.items()
    ]
    return Markup(" ".join(parts))
