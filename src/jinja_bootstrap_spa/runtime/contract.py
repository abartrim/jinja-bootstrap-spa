"""Explicit runtime and table contract helpers.

These constants and parsing helpers define the first opinionated public contract
for server-rendered components in jinja-bootstrap-spa.
"""

from __future__ import annotations

from typing import Any, Iterable, Mapping

JBS_REQUEST_HEADER = "X-JBS-Request"
JBS_COMPONENT_HEADER = "X-JBS-Component"
JBS_ACTION_HEADER = "X-JBS-Action"

JBS_ACTION_REFRESH = "refresh"
JBS_ACTION_FILTER = "filter"
JBS_ACTION_PAGE = "page"
JBS_ACTION_SORT = "sort"
JBS_ACTION_ROW = "row"

JBS_PERSIST_MEMORY = "memory"
JBS_PERSIST_QUERYSTRING = "querystring"
JBS_PERSIST_SESSION = "session"
JBS_SSE_EVENT_REFRESH = "refresh"
JBS_STREAM_MODE_REPLACE = "replace"
JBS_STREAM_MODE_APPEND = "append"
JBS_STREAM_MODE_PREPEND = "prepend"

TABLE_COMPONENT = "table"
TABLE_STATE_KEYS = ("page", "page_size", "sort_by", "sort_dir", "query")
TABLE_DEFAULT_PAGE = 1
TABLE_DEFAULT_PAGE_SIZE = 10
TABLE_DEFAULT_SORT_DIR = "asc"
TABLE_ALLOWED_SORT_DIRS = {"asc", "desc"}


TableState = dict[str, Any]


def _coerce_int(value: Any, default: int, minimum: int = 1) -> int:
    """Parse positive integers from query-like inputs."""

    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default

    return parsed if parsed >= minimum else default


def parse_table_state(
    params: Mapping[str, Any],
    *,
    default_sort_by: str = "",
    default_page_size: int = TABLE_DEFAULT_PAGE_SIZE,
    allowed_page_sizes: Iterable[int] | None = None,
    filter_keys: Iterable[str] = (),
) -> TableState:
    """Normalize table query params into a predictable state dictionary.

    Parameters
    ----------
    params:
        A mapping such as ``request.args``.
    default_sort_by:
        The fallback sort field when ``sort_by`` is missing.
    default_page_size:
        The fallback page size when no valid size is provided.
    allowed_page_sizes:
        Optional allow-list for page sizes.
    filter_keys:
        Additional query keys that should be copied into the returned state.
    """

    allowed_sizes = set(allowed_page_sizes or ())

    page = _coerce_int(params.get("page"), TABLE_DEFAULT_PAGE)
    page_size = _coerce_int(params.get("page_size"), default_page_size)
    if allowed_sizes and page_size not in allowed_sizes:
        page_size = default_page_size

    sort_by = str(params.get("sort_by", default_sort_by) or default_sort_by)
    sort_dir = str(
        params.get("sort_dir", TABLE_DEFAULT_SORT_DIR) or TABLE_DEFAULT_SORT_DIR
    )
    if sort_dir not in TABLE_ALLOWED_SORT_DIRS:
        sort_dir = TABLE_DEFAULT_SORT_DIR

    state: TableState = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }

    query = str(params.get("query", "") or "")
    if query:
        state["query"] = query

    for key in filter_keys:
        value = params.get(key)
        if value not in (None, ""):
            state[key] = str(value)

    return state
