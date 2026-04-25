"""Public package interface for jinja-bootstrap-spa.

The package intentionally exposes a narrow API:

- macro registration helpers for Jinja environments
- HTML attribute helpers for the first-party component runtime

AI agents can build on top of these primitives without needing to understand a
large framework surface area.
"""

from .macros.bootstrap import (
    BASE_TEMPLATE_NAME,
    BOOTSTRAP_MACROS,
    MACRO_TEMPLATE_NAME,
    register_bootstrap_macros,
)
from .runtime.components import (
    action_attrs,
    attrs_to_html,
    component_attrs,
    table_attrs,
)
from .runtime.contract import (
    JBS_ACTION_FILTER,
    JBS_ACTION_PAGE,
    JBS_ACTION_REFRESH,
    JBS_ACTION_ROW,
    JBS_ACTION_SORT,
    JBS_CONDITIONAL_HEADER,
    JBS_ETAG_HEADER,
    JBS_PERSIST_HEADER,
    JBS_PERSIST_MEMORY,
    JBS_PERSIST_QUERYSTRING,
    JBS_PERSIST_SESSION,
    JBS_SSE_EVENT_REFRESH,
    JBS_STATE_HEADER,
    TABLE_STATE_KEYS,
    conditional_fragment_response,
    etag_matches,
    fragment_etag,
    parse_table_state,
)

__all__ = [
    "BASE_TEMPLATE_NAME",
    "BOOTSTRAP_MACROS",
    "MACRO_TEMPLATE_NAME",
    "JBS_ACTION_FILTER",
    "JBS_ACTION_PAGE",
    "JBS_ACTION_REFRESH",
    "JBS_ACTION_ROW",
    "JBS_ACTION_SORT",
    "JBS_CONDITIONAL_HEADER",
    "JBS_ETAG_HEADER",
    "JBS_PERSIST_HEADER",
    "JBS_PERSIST_MEMORY",
    "JBS_PERSIST_QUERYSTRING",
    "JBS_PERSIST_SESSION",
    "JBS_STATE_HEADER",
    "JBS_SSE_EVENT_REFRESH",
    "TABLE_STATE_KEYS",
    "action_attrs",
    "attrs_to_html",
    "component_attrs",
    "conditional_fragment_response",
    "etag_matches",
    "fragment_etag",
    "parse_table_state",
    "register_bootstrap_macros",
    "table_attrs",
]

__version__ = "0.1.0"
