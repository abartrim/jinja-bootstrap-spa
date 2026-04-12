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

- [ ] Add Turbo-Flask integration examples and runtime helpers.
- [ ] Support fragment-oriented static site generation workflows.
- [ ] Expand the macro library with tables, modals, tabs, alerts, and pagination.
- [ ] Review generated markup for accessibility defaults and ARIA coverage.
- [ ] Document contribution patterns for new macros and runtime adapters.

## Contribution Notes

- Prefer named macro arguments so generated templates remain readable.
- Keep Bootstrap class defaults conservative and override-friendly.
- Add tests for each new macro or helper.
- Document any HTMX or Turbo attribute conventions in the runtime module.
