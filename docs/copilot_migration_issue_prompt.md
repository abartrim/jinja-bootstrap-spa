# Copilot Migration Issue Prompt

Use this document as a ready-to-paste GitHub issue for Copilot or another
repository-aware coding agent. It is written for migrating an existing
Jinja/Bootstrap application onto `jinja-bootstrap-spa` without rewriting the
entire app at once.

## Intended Outcome

The agent should:

- inspect both templates and backend routes
- identify the highest-value UI surfaces for `jinja-bootstrap-spa`
- introduce the framework incrementally
- preserve existing behavior while improving stateful partial refresh,
  conditional fragment rendering, and live updates where they make sense

## Ready-To-Paste Issue

```md
## Goal

Migrate this repository's existing Jinja/Bootstrap UI toward
`jinja-bootstrap-spa` in a safe, incremental way.

The objective is not a full rewrite. The objective is to identify the best
targets for server-rendered component replacement, streaming updates, and
shared framework macros, then implement the first migration slice end to end.

## Context

This project should use `jinja-bootstrap-spa` as the generic UI/runtime layer:

- Jinja remains the canonical HTML renderer.
- Bootstrap remains the styling system.
- `jinja-bootstrap-spa` macros should replace repeated raw Bootstrap markup.
- The `data-jbs-*` runtime should drive partial updates, state persistence,
  loading behavior, and SSE where appropriate.

Do not introduce a heavy client framework. Do not convert views into JSON APIs
unless required by an existing backend contract.

## Required Reading

Before changing code, read these files from the framework repository:

- `AGENTS.md`
- `docs/llm_authoring_guide.md`
- `docs/feature_coverage.md`
- `docs/framework_backlog.md`

If this repository vendors or references the framework locally, inspect the
current macro surface before inventing custom markup.

## Your Tasks

### 1. Audit the current app

Inspect:

- all Jinja templates and partials
- base layouts and repeated Bootstrap markup
- route handlers, view functions, controllers, and server-rendered endpoints
- forms, filters, tables, search pages, list pages, detail pages, menus, modals,
  drawers, status areas, and notification patterns
- existing JavaScript that performs fetches, polling, DOM replacement,
  accordions, tab state, or ad hoc state management

### 2. Produce a migration map

Create a migration summary in a Markdown document that identifies:

- repeated template patterns that should become framework macros or app-level
  macros built on top of framework macros
- current pages/components that are the strongest candidates for
  `data-jbs-*` componentization
- routes that already return HTML fragments and can be upgraded quickly
- routes that should be split into page endpoints plus fragment endpoints
- places where SSE would improve the UX
- places where conditional `ETag`/`304` responses would reduce unnecessary
  traffic
- places where state persistence is currently broken or missing and should be
  standardized

For each candidate, include:

- component/page name
- current template path
- backend route or handler
- recommended framework primitive or macro
- whether it should use full replace, append, prepend, or no streaming
- migration priority: high, medium, or low
- migration risk: low, medium, or high

### 3. Infer likely framework targets from backend code

Do not limit the analysis to template files alone. Use the backend to infer
where the framework should be applied.

Look for:

- handlers that paginate, sort, or filter data
- handlers returning tabular/list results
- repeated form validation and submit/re-render flows
- endpoints used for dashboards, work queues, job lists, audit logs, activity
  feeds, timelines, or detail inspectors
- polling endpoints or refresh buttons that should become in-place refreshable
  components
- places where the backend already computes view state that should remain
  server-owned rather than moving into client state

Call out likely future framework component needs if the project depends on them.

### 4. Implement the first migration slice

Choose the highest-value low-to-medium-risk slice and implement it.

Prefer this order:

1. stateful tables or data grids
2. search/filter/list surfaces
3. form workflows
4. menus/action menus
5. modals/drawers
6. status/toast/feedback regions

For the first slice:

- replace repeated markup with framework macros
- preserve or improve the current Bootstrap appearance
- introduce `data-jbs-*` component refresh behavior where useful
- preserve state across swaps and reloads
- add loading behavior using the framework's loading phase conventions
- add `ETag`/`304` support if the slice is refresh-driven
- add SSE if the slice is live-updating and the backend already supports or can
  safely support it

### 5. Add tests

Add or update:

- unit tests for macro or template rendering where appropriate
- server tests for fragment endpoints
- Playwright tests for the migrated user flow
- browser-console assertions so runtime errors fail tests

The browser tests should confirm:

- component refresh works
- visual state is preserved across swaps
- loading indicators appear and clear
- SSE updates do not break pagination/filter state
- unchanged content can avoid unnecessary replacement when the framework
  supports it

### 6. Document the migration path

Add developer-facing documentation that explains:

- what was migrated
- which remaining pages/components should migrate next
- which app-specific macros should be created on top of the framework
- any backend conventions required for fragment endpoints, persisted state,
  `ETag`, or SSE

## Implementation Rules

- Keep HTML server-rendered.
- Prefer framework macros before raw Bootstrap markup.
- Keep the framework generic; app-specific semantics belong in app templates or
  app-level macros.
- Do not fork framework internals unless absolutely necessary.
- Preserve accessibility and keyboard behavior.
- Preserve visual state across partial updates.
- Prefer incremental migration over page rewrites.

## Deliverables

Provide:

1. the migration audit document
2. the first implementation slice
3. tests covering the migrated flow
4. a short follow-up backlog ordered by value and risk

## Suggested Output Format

In your final summary, include:

- **Audit Findings**
- **Implemented Slice**
- **Remaining Migration Backlog**
- **Open Risks / Follow-Ups**
```

## Notes For Humans

Recommended first targets in most Jinja/Bootstrap apps:

- admin/work-queue tables with pagination, filters, and row actions
- dashboard panels that currently rely on polling or manual refresh
- search/list/detail screens with repeated filter forms
- modal or drawer driven edit/view flows
- toast/status surfaces with inconsistent feedback handling

Lower-value early targets:

- purely static marketing pages
- pages with minimal interactivity and no repeated component structure
- one-off legacy templates that are close to retirement
