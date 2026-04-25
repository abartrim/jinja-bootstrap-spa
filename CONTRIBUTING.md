# Contributing

`jinja-bootstrap-spa` is intentionally small and opinionated. Contributions
should preserve the server-rendered Jinja model, Bootstrap defaults, and the
first-party `data-jbs-*` runtime contract.

## Development Setup

```bash
pip install -e ".[dev]"
python -m playwright install chromium
npm ci
```

Run both example apps while developing component behavior:

```bash
npm run example:python
npm run example:go
```

## Validation

Run the same checks as CI before opening a pull request:

```bash
npm run build:js
.venv/bin/flake8 src tests
.venv/bin/black --check src tests
.venv/bin/isort --check-only src tests
.venv/bin/mypy src
.venv/bin/djlint src/jinja_bootstrap_spa/templates --check
test -z "$(gofmt -l assets.go environment.go environment_test.go examples/go_table_app/main.go examples/go_table_app/data.go examples/go_table_app/app.go examples/go_table_app/app_test.go)"
GOSUMDB=off go test ./...
npm run typecheck:js
npm run test:js
.venv/bin/pytest -q
.venv/bin/python -m build
```

## Contribution Rules

- Add generic primitives to the framework; keep product-specific language in
  consuming applications.
- Prefer adding or extending macros before introducing raw Bootstrap markup in
  examples.
- Preserve component state across swaps, reloads, and stream updates.
- Add macro rendering tests for new macros or significant parameters.
- Add Playwright coverage for runtime behavior, especially replacement,
  persistence, SSE, loading, and browser-console failures.
- Add TypeScript unit tests for exported browser-runtime helpers when changing
  parsing, constants, state, or stream payload behavior.
- Keep serious and critical `axe-core` accessibility violations out of the
  example app.
- Keep generated artifacts out of git unless they are packaged public assets,
  such as the compiled browser runtime in `src/jinja_bootstrap_spa/static`.

## Documentation

When adding behavior, update the closest relevant docs:

- `README.md` for user-facing setup and API examples
- `docs/feature_coverage.md` for example/test coverage
- `docs/llm_authoring_guide.md` for agent-facing authoring rules
- `docs/framework_backlog.md` when a backlog item changes status
- `docs/api_reference.md` when macro signatures change

Regenerate the macro API reference after adding or changing macros:

```bash
.venv/bin/python scripts/generate_macro_reference.py
```
