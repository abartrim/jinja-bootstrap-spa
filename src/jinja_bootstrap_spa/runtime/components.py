"""Helpers for the first-party jinja-bootstrap-spa browser runtime.

The runtime contract is intentionally opinionated:

- the server renders canonical component HTML
- the browser runtime fetches replacement fragments
- component state is serialized into ``data-jbs-state``
- actions are expressed with ``data-jbs-*`` attributes

This keeps the HTML authoring model simple enough for AI agents while still
supporting SPA-like interactions such as table sorting, filtering, and paging.
"""

from __future__ import annotations

import json
from typing import Any, Mapping, Sequence

from markupsafe import Markup, escape

from .contract import (
    JBS_PERSIST_MEMORY,
    JBS_SSE_EVENT_REFRESH,
    TABLE_COMPONENT,
    TABLE_STATE_KEYS,
)

ComponentState = Mapping[str, Any]


def _json_attr(value: ComponentState | None) -> str | None:
    """Serialize state dictionaries for ``data-jbs-state`` attributes."""

    if value is None:
        return None
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def component_attrs(
    *,
    component: str,
    endpoint: str,
    target: str | None = None,
    state: ComponentState | None = None,
    key: str | None = None,
    swap: str = "outerHTML",
    trigger: str | None = None,
    persist: str = JBS_PERSIST_MEMORY,
    state_keys: Sequence[str] | None = None,
    sse_endpoint: str | None = None,
    sse_event: str = JBS_SSE_EVENT_REFRESH,
    lazy: bool = False,
) -> dict[str, str]:
    """Build attributes for a server-rendered component root element."""

    attrs = {
        "data-jbs-component": component,
        "data-jbs-endpoint": endpoint,
        "data-jbs-swap": swap,
    }
    if target is not None:
        attrs["data-jbs-target"] = target
    if key is not None:
        attrs["data-jbs-key"] = key
    if trigger is not None:
        attrs["data-jbs-trigger"] = trigger
    attrs["data-jbs-persist"] = persist
    if lazy:
        attrs["data-jbs-lazy"] = "true"
    state_json = _json_attr(state)
    if state_json is not None:
        attrs["data-jbs-state"] = state_json
    if state_keys:
        attrs["data-jbs-state-keys"] = ",".join(state_keys)
    if sse_endpoint is not None:
        attrs["data-jbs-sse"] = sse_endpoint
        attrs["data-jbs-sse-event"] = sse_event
    return attrs


def action_attrs(
    *,
    action: str,
    component_ref: str | None = None,
    patch: ComponentState | None = None,
    page: int | None = None,
    sort_key: str | None = None,
    sort_direction: str | None = None,
    row_id: str | None = None,
    intent: str | None = None,
) -> dict[str, str]:
    """Build attributes for an element that triggers a runtime action."""

    attrs = {"data-jbs-action": action}
    if component_ref is not None:
        attrs["data-jbs-component-ref"] = component_ref
    if page is not None:
        attrs["data-jbs-page"] = str(page)
    if sort_key is not None:
        attrs["data-jbs-sort-key"] = sort_key
    if sort_direction is not None:
        attrs["data-jbs-sort-direction"] = sort_direction
    if row_id is not None:
        attrs["data-jbs-row-id"] = row_id
    if intent is not None:
        attrs["data-jbs-intent"] = intent
    patch_json = _json_attr(patch)
    if patch_json is not None:
        attrs["data-jbs-patch"] = patch_json
    return attrs


def table_attrs(
    *,
    endpoint: str,
    state: ComponentState | None = None,
    target: str | None = None,
    key: str | None = None,
    persist: str = JBS_PERSIST_MEMORY,
    state_keys: Sequence[str] = TABLE_STATE_KEYS,
    sse_endpoint: str | None = None,
    sse_event: str = JBS_SSE_EVENT_REFRESH,
) -> dict[str, str]:
    """Build the attribute set for the opinionated table component root."""

    return component_attrs(
        component=TABLE_COMPONENT,
        endpoint=endpoint,
        target=target,
        state=state,
        key=key,
        persist=persist,
        state_keys=state_keys,
        sse_endpoint=sse_endpoint,
        sse_event=sse_event,
    )


def attrs_to_html(attrs: Mapping[str, Any]) -> Markup:
    """Convert a dictionary of HTML attributes into a safe attribute string."""

    parts = [
        f'{escape(str(key))}="{escape(str(value))}"' for key, value in attrs.items()
    ]
    return Markup(" ".join(parts))
