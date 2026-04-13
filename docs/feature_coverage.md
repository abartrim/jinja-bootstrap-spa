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
| Header persistence | `orders-table` (`persist="header"`) | `tests/test_browser_runtime.py` | Yes |
| Session persistence | `session-table` (`persist="session"`) | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| SSE replace mode | `orders-table` (`/events/orders`) | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| SSE prepend mode | `live-table` | `tests/test_browser_runtime.py` | Yes |
| SSE append mode | `live-append-table` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Hidden stream buffering + flush | `live-table` (`stream_pause_when_hidden=true`) | `tests/test_browser_runtime.py` | Yes |
| Lazy hydration/fetch | `lazy-summary` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Action menus | order row menu | `tests/test_browser_runtime.py` | Yes |
| Modal + drawer overlays | `runtime-modal`, `orders-drawer` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Segmented control (status filter) | `orders-status-tabs` | `tests/test_browser_runtime.py` | Yes |
| Status region (dismissible) | `orders-status-region` | `tests/test_browser_runtime.py` | Yes |
| Toast notice (dismissible) | `orders-status-toast` | `tests/test_browser_runtime.py` | Yes |
| Navbar showcase | wrapper app top nav | `tests/test_example_wrapper_app.py` | Yes |
| Multi-select + single-select filters | orders/session toolbars | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Date range picker | orders filters | `tests/test_browser_runtime.py` | Yes |
| SQL assist (hints + validation) | orders filters | `tests/test_browser_runtime.py` | Yes |
| Regex assist validation | orders filters | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |
| Autocomplete input | customer filter | `tests/test_browser_runtime.py` | Yes |
| Request cancellation (stale response protection) | `cancel-demo` | `tests/test_browser_runtime.py`, `tests/test_example_wrapper_app.py` | Yes |

## Decisions

1. Add `toast(...)` as a first-class notification primitive alongside `status_region(...)`.
1. Add explicit `segmented_control(...)` macro for status-style tabs.
1. Extend stream table operations to full CRUD semantics (`create`, `read`, `update`, `delete`) while preserving `upsert` compatibility.
1. Include `navbar(...)` showcase in the wrapper app.
1. Prefer header-based state transport (`persist="header"`) for table state where URL query params could conflict with host application routing.
