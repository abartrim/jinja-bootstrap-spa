"""Explicit runtime and table contract helpers.

These constants and parsing helpers define the first opinionated public contract
for server-rendered components in jinja-bootstrap-spa.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable, Mapping

JBS_REQUEST_HEADER = "X-JBS-Request"
JBS_COMPONENT_HEADER = "X-JBS-Component"
JBS_ACTION_HEADER = "X-JBS-Action"
JBS_STATE_HEADER = "X-JBS-State"
JBS_CONDITIONAL_HEADER = "If-None-Match"
JBS_ETAG_HEADER = "ETag"

JBS_ACTION_REFRESH = "refresh"
JBS_ACTION_FILTER = "filter"
JBS_ACTION_PAGE = "page"
JBS_ACTION_SORT = "sort"
JBS_ACTION_ROW = "row"

JBS_PERSIST_MEMORY = "memory"
JBS_PERSIST_QUERYSTRING = "querystring"
JBS_PERSIST_SESSION = "session"
JBS_PERSIST_HEADER = "header"
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


def fragment_etag(content: str) -> str:
    """Build a weak ETag for rendered component fragments."""

    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()[:24]
    return f'W/"jbs-{digest}"'


def etag_matches(if_none_match_header: str | None, etag: str) -> bool:
    """Return ``True`` when an ``If-None-Match`` header matches ``etag``."""

    if not if_none_match_header:
        return False

    candidates = [
        token.strip() for token in if_none_match_header.split(",") if token.strip()
    ]
    if "*" in candidates:
        return True

    strong_etag = etag[2:] if etag.startswith("W/") else etag
    weak_etag = f"W/{strong_etag}"

    for candidate in candidates:
        candidate_strong = candidate[2:] if candidate.startswith("W/") else candidate
        if candidate in {etag, strong_etag, weak_etag}:
            return True
        if candidate_strong == strong_etag:
            return True

    return False


def conditional_fragment_response(
    content: str, request_headers: Mapping[str, Any]
) -> tuple[str, int, dict[str, str]]:
    """Return an HTTP tuple with ETag and conditional ``304`` support."""

    etag = fragment_etag(content)
    headers = {
        JBS_ETAG_HEADER: etag,
        "Cache-Control": "no-cache",
    }
    if_none_match = request_headers.get(JBS_CONDITIONAL_HEADER)
    if etag_matches(str(if_none_match or ""), etag):
        return "", 304, headers
    return content, 200, headers


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
    request_headers: Mapping[str, Any] | None = None,
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
    request_headers:
        Optional request headers mapping. When it includes ``X-JBS-State`` JSON,
        those values override query params for state parsing.
    default_sort_by:
        The fallback sort field when ``sort_by`` is missing.
    default_page_size:
        The fallback page size when no valid size is provided.
    allowed_page_sizes:
        Optional allow-list for page sizes.
    filter_keys:
        Additional query keys that should be copied into the returned state.
    """

    header_state: dict[str, Any] = {}
    if request_headers is not None:
        raw_header_state = request_headers.get(JBS_STATE_HEADER)
        if raw_header_state:
            try:
                parsed_header_state = json.loads(str(raw_header_state))
                if isinstance(parsed_header_state, dict):
                    header_state = parsed_header_state
            except json.JSONDecodeError:
                header_state = {}

    def _state_value(key: str, fallback: Any = None) -> Any:
        if key in header_state:
            return header_state.get(key)
        return params.get(key, fallback)

    allowed_sizes = set(allowed_page_sizes or ())

    page = _coerce_int(_state_value("page"), TABLE_DEFAULT_PAGE)
    page_size = _coerce_int(_state_value("page_size"), default_page_size)
    if allowed_sizes and page_size not in allowed_sizes:
        page_size = default_page_size

    sort_by = str(_state_value("sort_by", default_sort_by) or default_sort_by)
    sort_dir = str(
        _state_value("sort_dir", TABLE_DEFAULT_SORT_DIR) or TABLE_DEFAULT_SORT_DIR
    )
    if sort_dir not in TABLE_ALLOWED_SORT_DIRS:
        sort_dir = TABLE_DEFAULT_SORT_DIR

    state: TableState = {
        "page": page,
        "page_size": page_size,
        "sort_by": sort_by,
        "sort_dir": sort_dir,
    }

    query = str(_state_value("query", "") or "")
    if query:
        state["query"] = query

    for key in filter_keys:
        value = _state_value(key)
        if isinstance(value, list):
            values = [str(item) for item in value if item not in (None, "")]
            if values:
                state[key] = values
            continue
        if value not in (None, ""):
            state[key] = str(value)

    return state
