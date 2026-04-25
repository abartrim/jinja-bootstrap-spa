---
name: Framework Roadmap
about: Track early roadmap items for jinja-bootstrap-spa
title: "Roadmap: initial framework enhancements"
labels: roadmap
assignees: ""
---

## Scope

Use this issue to track the first wave of framework enhancements after the
initial scaffold lands.

## Planned Enhancements

- [ ] Expand first-party runtime examples for fragment replacement, SSE, and state persistence.
- [ ] Support fragment-oriented static site generation workflows.
- [ ] Expand the macro library with additional generic app shells and form workflows.
- [ ] Review generated markup for accessibility defaults and ARIA coverage.
- [ ] Document contribution patterns for new macros and runtime adapters.

## Contribution Notes

- Prefer named macro arguments so generated templates remain readable.
- Keep Bootstrap class defaults conservative and override-friendly.
- Add tests for each new macro or helper.
- Preserve the `data-jbs-*` runtime contract for all interactive primitives.
