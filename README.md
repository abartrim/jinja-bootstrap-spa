# jinja-bootstrap-spa

`jinja-bootstrap-spa` is a small Python framework for AI-assisted web UI generation.
It gives large language models a constrained, consistent surface area for producing
modern server-rendered interfaces:

- Jinja2 templates for familiar composition
- Bootstrap 5 macros for reliable styling without custom CSS
- HTMX or Turbo-friendly attributes for incremental, SPA-like refreshes
- Minimal Python dependencies and no front-end build pipeline

The goal is straightforward: make it easy for humans and AI agents to assemble
polished UI fragments quickly, while keeping the stack inspectable and easy to host.

## Why This Exists

LLMs are good at assembling HTML, but raw HTML generation often drifts into
inconsistent spacing, broken responsiveness, and ad hoc styling. This package
narrows the choices:

- use a shared `base.html`
- import reusable Bootstrap macros
- add partial refresh behavior with `hx-*` attributes
- keep most application state and rendering on the server

That gives generated interfaces a more consistent UX baseline with much less code.

## Installation

```bash
pip install jinja-bootstrap-spa
```

For development:

```bash
pip install -e ".[dev]"
```

## Quickstart

Register the packaged Bootstrap macros with your Jinja environment:

```python
from jinja2 import Environment, FileSystemLoader, select_autoescape

from jinja_bootstrap_spa.macros.bootstrap import register_bootstrap_macros

env = Environment(
    loader=FileSystemLoader("templates"),
    autoescape=select_autoescape(["html", "xml"]),
)
register_bootstrap_macros(env)
```

Then use the macros inside a template:

```jinja
{% extends "base.html" %}
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}

{% block title %}Dashboard{% endblock %}

{% block content %}
  <div class="container py-4">
    {{ ui.navbar("LLM Console", brand_href="/", nav_items=[
      {"label": "Home", "href": "/"},
      {"label": "Jobs", "href": "/jobs"},
    ]) }}

    <section id="stats-card" class="mt-4">
      {{ ui.card(
        title="Build Status",
        body="Everything is green.",
        footer=ui.button(
          "Refresh",
          variant="outline-primary",
          hx_get="/partials/build-status",
          hx_target="#stats-card",
          hx_swap="outerHTML"
        )
      ) }}
    </section>
  </div>
{% endblock %}
```

## HTMX / Partial Refresh Example

`jinja-bootstrap-spa` does not bundle HTMX or Turbo.js. Add them via CDN in your
application template so the JavaScript stays optional and lightweight:

```html
<script
  src="https://unpkg.com/htmx.org@1.9.12"
  integrity="sha384-..."
  crossorigin="anonymous"
></script>
```

A minimal HTMX endpoint can return a fragment rendered with the same macro set:

```python
from flask import Flask, render_template

app = Flask(__name__)


@app.get("/partials/build-status")
def build_status_partial():
    return render_template(
        "partials/build_status.html",
        status="Last updated just now.",
    )
```

In the fragment template, target the same DOM node:

```jinja
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{{ ui.card(
  title="Build Status",
  body=status,
  footer=ui.button(
    "Refresh",
    variant="outline-primary",
    hx_get="/partials/build-status",
    hx_target="#stats-card",
    hx_swap="outerHTML"
  ),
  id="stats-card"
) }}
```

## Included Pieces

- `src/jinja_bootstrap_spa/macros/bootstrap.py`
  Stores the Jinja macro source and exposes environment registration helpers.
- `src/jinja_bootstrap_spa/runtime/htmx.py`
  Small helpers for building `hx-*` attribute dictionaries or HTML-safe attribute strings.
- `src/jinja_bootstrap_spa/templates/base.html`
  A Bootstrap-first base template with extension hooks for additional scripts.

## Customizing Bootstrap

This project intentionally leans on stock Bootstrap 5 so generated UIs remain
predictable. There are two common customization paths:

1. Override blocks in `base.html` to inject a custom stylesheet after Bootstrap.
2. Extend the shipped macros with project-specific variants, icons, or layout rules.

For example, add your own theme file:

```jinja
{% extends "jinja_bootstrap_spa/base.html" %}

{% block head_extra %}
  <link rel="stylesheet" href="{{ url_for('static', filename='theme.css') }}">
{% endblock %}
```

## Extending Macros

The macro set is designed to be copied, wrapped, or expanded. If you need
project-specific primitives:

- keep the Bootstrap class contract stable
- add named arguments rather than positional ones
- prefer explicit accessibility labels and IDs
- expose HTMX/Turbo attributes at the component boundary

## Contributing

Contributions are welcome for new macros, runtime helpers, and documentation.
Suggested areas:

- Turbo-Flask integration helpers
- advanced components such as tables, modals, tabs, and toasts
- accessibility reviews for generated markup
- static site rendering patterns for fragment-first templates

See [`.github/ISSUE_TEMPLATE/roadmap.md`](.github/ISSUE_TEMPLATE/roadmap.md) for
the initial roadmap that can be turned into GitHub issues or a project board.
