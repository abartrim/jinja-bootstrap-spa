# Release Checklist

Use this checklist before publishing a package release or inviting a new
consumer project to depend on the library.

## Version And Changelog

- Update `version` in `pyproject.toml`.
- Update `__version__` in `src/jinja_bootstrap_spa/__init__.py`.
- Move the current `CHANGELOG.md` entry from `Unreleased` to the release date.
- Confirm the package classifier still reflects stability.
- Review `docs/versioning_policy.md` for any compatibility or deprecation notes.

## Validation

Run:

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

Regenerate the macro API reference and verify it is committed:

```bash
.venv/bin/python scripts/generate_macro_reference.py
git diff --exit-code -- docs/api_reference.md
```

## Package Inspection

- Inspect the generated wheel and confirm it includes:
  - `jinja_bootstrap_spa/templates/base.html`
  - `jinja_bootstrap_spa/static/jinja-bootstrap-spa.js`
  - `jinja_bootstrap_spa/static/jinja-bootstrap-spa.d.ts`
  - `jinja_bootstrap_spa/py.typed`
- Install the wheel into a clean environment.
- Run a minimal Jinja render using `register_bootstrap_macros(...)`.

## Example Apps

- Start the Flask example with `npm run example:python`.
- Start the Go example with `npm run example:go`.
- Confirm table refresh, cache hits, SSE updates, loading states, and disclosure
  persistence in the browser.
- Regenerate visual screenshots when the visual surface changes:

```bash
.venv/bin/python scripts/capture_example_visuals.py
```
