# Versioning Policy

`jinja-bootstrap-spa` follows Semantic Versioning, with extra caution while the
project is still `0.x`.

## Current Stability

The package is alpha until the first `1.0.0` release. During alpha:

- minor versions may include breaking changes
- patch versions should remain backward-compatible bug fixes
- breaking changes must be documented in `CHANGELOG.md`
- migration notes are required when changing the `data-jbs-*` runtime contract

## Public API

These surfaces are treated as public API:

- Python package imports exported from `jinja_bootstrap_spa`
- packaged Jinja template names
- macro names and named macro parameters documented in `docs/api_reference.md`
- `data-jbs-*` component attributes and `X-JBS-*` request headers
- TypeScript exports from `frontend/src/jinja-bootstrap-spa.ts`
- packaged browser assets in `jinja_bootstrap_spa/static`
- Go helpers exported from the root Go package

## Compatibility Rules

Patch releases:

- fix bugs without changing public macro signatures
- keep existing `data-jbs-*` and `X-JBS-*` behavior compatible
- may add optional macro parameters

Minor alpha releases:

- may add macros, helpers, examples, and runtime features
- may revise public APIs when the current shape blocks real consumers
- must document breaking changes and migration steps

Major releases:

- are reserved for stable compatibility boundaries after `1.0.0`
- may remove deprecated APIs
- must include explicit migration guidance

## Deprecation

When practical, deprecate before removing:

- document the replacement in `CHANGELOG.md`
- keep the old behavior through at least one minor alpha release
- add tests that preserve the compatibility shim until removal
