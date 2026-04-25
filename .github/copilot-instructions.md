# Copilot Instructions

This repository is an opinionated server-rendered UI framework.

Before generating code, follow [AGENTS.md](../AGENTS.md) and the detailed authoring guide in [docs/llm_authoring_guide.md](../docs/llm_authoring_guide.md).

## Required approach

- Prefer the packaged Jinja macros over raw Bootstrap markup.
- Preserve the `data-jbs-*` runtime contract for refreshable fragments.
- Keep the server responsible for HTML and state normalization.
- Add app-specific wrappers/macros in the consuming app; keep this framework generic.
- Reuse the example apps before inventing a new interaction pattern.
