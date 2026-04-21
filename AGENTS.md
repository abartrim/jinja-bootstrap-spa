# Agent Guide

Start here when using `jinja-bootstrap-spa` from Codex or another repository-aware agent.

Read the full guide in [docs/llm_authoring_guide.md](docs/llm_authoring_guide.md).
For migration work in existing Jinja/Bootstrap apps, start from
[docs/copilot_migration_issue_prompt.md](docs/copilot_migration_issue_prompt.md).

## Non-negotiables

- Keep HTML server-rendered. The browser runtime enhances fragments; it does not replace Jinja.
- Import the packaged macros from `jinja_bootstrap_spa/bootstrap_macros.html` before inventing custom markup.
- Extend the packaged base template (`base.html` or `jinja_bootstrap_spa/base.html`) unless the app already owns a base shell.
- Prefer Bootstrap utility classes and the shipped macros over writing custom CSS.
- Use `data-jbs-*` actions and component roots for interactivity. Do not add framework-specific client state unless the repo explicitly opts into it.
- For tables and other refreshable surfaces, preserve component state across swaps and return conditional fragment responses when possible.
- Build app-specific domain macros on top of the generic framework primitives instead of forking the framework macros.

## Local example commands

- Flask example: `npm run example:python`
- Go example: `npm run example:go`
