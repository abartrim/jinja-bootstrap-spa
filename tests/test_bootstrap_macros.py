"""Tests for the packaged Bootstrap Jinja macros."""

from jinja2 import Environment

from jinja_bootstrap_spa.macros.bootstrap import register_bootstrap_macros


def build_environment() -> Environment:
    """Create an environment with the packaged macros registered."""

    environment = Environment(autoescape=True)
    register_bootstrap_macros(environment)
    return environment


def test_button_macro_renders_bootstrap_button_markup() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{ ui.button("Save") }}
        """
    )

    rendered = template.render()

    assert 'class="btn btn-primary"' in rendered
    assert 'type="button"' in rendered
    assert ">Save</button>" in rendered


def test_button_macro_supports_htmx_attributes() -> None:
    environment = build_environment()
    template = environment.from_string(
        """
        {% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
        {{
          ui.button(
            "Refresh",
            hx_get="/partial",
            hx_target="#card",
            hx_swap="outerHTML"
          )
        }}
        """
    )

    rendered = template.render()

    assert 'hx-get="/partial"' in rendered
    assert 'hx-target="#card"' in rendered
    assert 'hx-swap="outerHTML"' in rendered
