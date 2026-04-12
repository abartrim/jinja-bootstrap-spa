# Feature Coverage Matrix

This matrix tracks whether each baseline runtime feature is:

- demonstrated in the local wrapper app (`examples/table_app`)
- covered by Playwright regression tests
- visually sanity-checked in the wrapper app

Last visual check run: April 12, 2026 (desktop + mobile screenshots via
`scripts/capture_example_visuals.py`).

| Feature | Wrapper App Example | Playwright Coverage | Visual Check |
| --- | --- | --- | --- |
| Table contract (sort, page, filter form) | `orders-table` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Querystring persistence | `orders-table` (`persist="querystring"`) | `tests/test_browser_runtime.py` | Yes |
| Session persistence | `session-table` (`persist="session"`) | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| SSE replace mode | `orders-table` (`/events/orders`) | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| SSE prepend mode | `live-table` | `tests/test_browser_runtime.py` | Yes |
| SSE append mode | `live-append-table` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Hidden stream buffering + flush | `live-table` (`stream_pause_when_hidden=true`) | `tests/test_browser_runtime.py` | Yes |
| Lazy hydration/fetch | `lazy-summary` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Action menus | order row menu | `tests/test_browser_runtime.py` | Yes |
| Modal + drawer overlays | `runtime-modal`, `orders-drawer` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Tabs (segmented status control) | `orders-status-tabs` | `tests/test_browser_runtime.py` | Yes |
| Status region (dismissible) | `orders-status-region` | `tests/test_browser_runtime.py` | Yes |
| Multi-select + single-select filters | orders/session toolbars | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Date range picker | orders filters | `tests/test_browser_runtime.py` | Yes |
| SQL assist (hints + validation) | orders filters | `tests/test_browser_runtime.py` | Yes |
| Regex assist validation | orders filters | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Autocomplete input | customer filter | `tests/test_browser_runtime.py` | Yes |
| Request cancellation (stale response protection) | `cancel-demo` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |

## Open Questions

1. Should we add a dedicated `toast(...)` macro and runtime queue, or keep the current
   `status_region(...)` as the only baseline notification primitive?
1. Should we introduce an explicit `segmented_control(...)` macro, or continue using
   `tabs(...)` as the segmented view primitive?
1. For SSE table updates, do we want keyed row `update`/`delete` payload operations in
   v0.2, or keep v0.1 strictly to `replace`/`prepend`/`append`?
1. Should the wrapper app include a dedicated `navbar(...)` showcase section, or keep
   navigation examples out of the initial table-focused vertical?
1. Should querystring persistence support opt-in browser history (`pushState`) mode in
   addition to the current replace-only URL sync?
