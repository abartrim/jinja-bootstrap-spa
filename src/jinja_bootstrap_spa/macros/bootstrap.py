"""Packaged Jinja macros for Bootstrap 5 UI primitives.

Jinja macros normally live in `.html` files, but keeping the canonical source in
Python makes it easier for AI agents and library authors to inspect, register,
and test them programmatically. The helpers in this module publish a virtual
template called ``jinja_bootstrap_spa/bootstrap_macros.html`` through a
``DictLoader`` so applications can import the macros like any other template.
"""

from __future__ import annotations

from jinja2 import BaseLoader, ChoiceLoader, DictLoader, Environment

MACRO_TEMPLATE_NAME = "jinja_bootstrap_spa/bootstrap_macros.html"

BOOTSTRAP_MACROS = """
{%- macro button(label, href=None, variant="primary", size=None, button_type="button",
                 outline=False, disabled=False, class_name="", id=None,
                 hx_get=None, hx_post=None, hx_target=None, hx_swap=None,
                 attrs="") -%}
  {%- set tag = "a" if href else "button" -%}
  {%- set btn_variant = (
        "outline-" ~ variant
        if outline and not variant.startswith("outline-")
        else variant
      ) -%}
  {%- set classes = "btn btn-" ~ btn_variant -%}
  {%- if size -%}
    {%- set classes = classes ~ " btn-" ~ size -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set classes = classes ~ " " ~ class_name -%}
  {%- endif -%}
  <{{ tag }}
    class="{{ classes }}"
    {%- if id %} id="{{ id }}"{% endif -%}
    {%- if href %} href="{{ href }}"{% else %} type="{{ button_type }}"{% endif -%}
    {%- if disabled %}
      {{ "aria-disabled=\\"true\\" tabindex=\\"-1\\"" if href else "disabled" }}
    {% endif -%}
    {%- if hx_get %} hx-get="{{ hx_get }}"{% endif -%}
    {%- if hx_post %} hx-post="{{ hx_post }}"{% endif -%}
    {%- if hx_target %} hx-target="{{ hx_target }}"{% endif -%}
    {%- if hx_swap %} hx-swap="{{ hx_swap }}"{% endif -%}
    {%- if attrs %} {{ attrs|safe }}{% endif -%}
  >{{ label }}</{{ tag }}>
{%- endmacro -%}

{%- macro card(title=None, body="", footer=None, class_name="", id=None, attrs="") -%}
  <div class="card{% if class_name %} {{ class_name }}{% endif %}"
       {%- if id %} id="{{ id }}"{% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    {%- if title %}
      <div class="card-header">{{ title }}</div>
    {%- endif %}
    <div class="card-body">{{ body }}</div>
    {%- if footer %}
      <div class="card-footer">{{ footer }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro form_input(name, label=None, value="", input_type="text", placeholder=None,
                     variant=None, help_text=None, required=False, class_name="",
                     id=None, attrs="") -%}
  {%- set field_id = id or name -%}
  {%- set input_classes = "form-control" -%}
  {%- if variant -%}
    {%- set input_classes = input_classes ~ " border-" ~ variant -%}
  {%- endif -%}
  {%- if class_name -%}
    {%- set input_classes = input_classes ~ " " ~ class_name -%}
  {%- endif -%}
  <div class="mb-3">
    {%- if label %}
      <label for="{{ field_id }}" class="form-label">{{ label }}</label>
    {%- endif %}
    <input
      type="{{ input_type }}"
      name="{{ name }}"
      id="{{ field_id }}"
      value="{{ value }}"
      class="{{ input_classes }}"
      {%- if placeholder %} placeholder="{{ placeholder }}"{% endif -%}
      {%- if required %} required{% endif -%}
      {%- if attrs %} {{ attrs|safe }}{% endif -%}
    >
    {%- if help_text %}
      <div class="form-text">{{ help_text }}</div>
    {%- endif %}
  </div>
{%- endmacro -%}

{%- macro textarea(name, label=None, value="", rows=4, placeholder=None,
                   class_name="", id=None, attrs="") -%}
  {%- set field_id = id or name -%}
  <div class="mb-3">
    {%- if label %}
      <label for="{{ field_id }}" class="form-label">{{ label }}</label>
    {%- endif %}
    <textarea
      name="{{ name }}"
      id="{{ field_id }}"
      rows="{{ rows }}"
      class="form-control{% if class_name %} {{ class_name }}{% endif %}"
      {%- if placeholder %} placeholder="{{ placeholder }}"{% endif -%}
      {%- if attrs %} {{ attrs|safe }}{% endif -%}
    >{{ value }}</textarea>
  </div>
{%- endmacro -%}

{%- macro navbar(brand, brand_href="/", nav_items=None, expand="lg",
                 theme="light", background="light", class_name="", id=None,
                 attrs="") -%}
  {%- set nav_items = nav_items or [] -%}
  {%- set collapse_id = id ~ "-content" if id else "navbarSupportedContent" -%}
  <nav class="navbar navbar-expand-{{ expand }} navbar-{{ theme }} bg-{{ background }}
              {% if class_name %} {{ class_name }}{% endif %}"
       {%- if id %} id="{{ id }}"{% endif -%}
       {%- if attrs %} {{ attrs|safe }}{% endif -%}>
    <div class="container-fluid">
      <a class="navbar-brand" href="{{ brand_href }}">{{ brand }}</a>
      <button class="navbar-toggler" type="button" data-bs-toggle="collapse"
              data-bs-target="#{{ collapse_id }}" aria-controls="{{ collapse_id }}"
              aria-expanded="false" aria-label="Toggle navigation">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" id="{{ collapse_id }}">
        <ul class="navbar-nav me-auto mb-2 mb-lg-0">
          {%- for item in nav_items %}
            <li class="nav-item">
              <a class="nav-link{% if item.active %} active{% endif %}"
                 href="{{ item.href }}">{{ item.label }}</a>
            </li>
          {%- endfor %}
        </ul>
      </div>
    </div>
  </nav>
{%- endmacro -%}
"""


def bootstrap_loader(template_name: str = MACRO_TEMPLATE_NAME) -> DictLoader:
    """Return a loader that exposes the packaged Bootstrap macros as a template."""

    return DictLoader({template_name: BOOTSTRAP_MACROS})


def register_bootstrap_macros(
    environment: Environment,
    template_name: str = MACRO_TEMPLATE_NAME,
) -> Environment:
    """Register the macro template in an existing Jinja environment.

    Parameters
    ----------
    environment:
        The environment that should be able to import the packaged macros.
    template_name:
        The virtual template path used in ``{% import %}`` statements.

    Returns
    -------
    Environment
        The same environment instance, updated in place for fluent setup code.
    """

    loader: BaseLoader = bootstrap_loader(template_name)
    if environment.loader is None:
        environment.loader = loader
        return environment

    environment.loader = ChoiceLoader([environment.loader, loader])
    return environment
