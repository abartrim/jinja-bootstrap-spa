package jinjabootstrapspa

import (
	"strings"
	"testing"
	"testing/fstest"
)

func TestBootstrapMacrosSourceExtractsCanonicalTemplate(t *testing.T) {
	t.Parallel()

	source, err := BootstrapMacrosSource()
	if err != nil {
		t.Fatalf("BootstrapMacrosSource() error = %v", err)
	}

	if !strings.Contains(source, `{%- macro button(`) {
		t.Fatalf("expected button macro in source, got %q", source[:120])
	}
	if !strings.Contains(source, `{%- macro table(`) {
		t.Fatal("expected table macro in canonical macro source")
	}
}

func TestNewEnvironmentRendersPackagedBaseAndMacros(t *testing.T) {
	t.Parallel()

	env, err := NewEnvironment(Options{})
	if err != nil {
		t.Fatalf("NewEnvironment() error = %v", err)
	}

	tmpl, err := env.TemplateFromNamedString(
		"orders/page.html",
		`{% extends "jinja_bootstrap_spa/base.html" %}
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{% block title %}Orders{% endblock %}
{% block content %}
<main class="container py-4">{{ ui.button("Save", jbs_action="refresh") }}</main>
{% endblock %}`,
	)
	if err != nil {
		t.Fatalf("TemplateFromNamedString() error = %v", err)
	}

	rendered, err := tmpl.Render(nil)
	if err != nil {
		t.Fatalf("Render() error = %v", err)
	}

	if !strings.Contains(rendered, "<!DOCTYPE html>") {
		t.Fatal("expected packaged base template to render doctype")
	}
	if !strings.Contains(rendered, `class="btn btn-primary"`) {
		t.Fatal("expected packaged button macro to render bootstrap classes")
	}
	if !strings.Contains(rendered, `data-jbs-action="refresh"`) {
		t.Fatal("expected packaged button macro to render runtime attributes")
	}
}

func TestNewEnvironmentAlsoSupportsLegacyBaseTemplateName(t *testing.T) {
	t.Parallel()

	env, err := NewEnvironment(Options{})
	if err != nil {
		t.Fatalf("NewEnvironment() error = %v", err)
	}

	tmpl, err := env.TemplateFromNamedString(
		"legacy/page.html",
		`{% extends "base.html" %}
{% import "jinja_bootstrap_spa/bootstrap_macros.html" as ui %}
{% block content %}{{ ui.button("Legacy Base") }}{% endblock %}`,
	)
	if err != nil {
		t.Fatalf("TemplateFromNamedString() error = %v", err)
	}

	rendered, err := tmpl.Render(nil)
	if err != nil {
		t.Fatalf("Render() error = %v", err)
	}

	if !strings.Contains(rendered, "Legacy Base") {
		t.Fatalf("expected legacy base alias render, got %q", rendered)
	}
}

func TestNewEnvironmentSupportsRelativeIncludes(t *testing.T) {
	t.Parallel()

	env, err := NewEnvironment(Options{
		TemplateFS: fstest.MapFS{
			"pages/orders/index.html": {
				Data: []byte(`{% include "./_panel.html" %}`),
			},
			"pages/orders/_panel.html": {
				Data: []byte(`<section class="panel">Orders Panel</section>`),
			},
		},
	})
	if err != nil {
		t.Fatalf("NewEnvironment() error = %v", err)
	}

	tmpl, err := env.GetTemplate("pages/orders/index.html")
	if err != nil {
		t.Fatalf("GetTemplate() error = %v", err)
	}

	rendered, err := tmpl.Render(nil)
	if err != nil {
		t.Fatalf("Render() error = %v", err)
	}

	if !strings.Contains(rendered, "Orders Panel") {
		t.Fatalf("expected relative include output, got %q", rendered)
	}
}

func TestNewEnvironmentSupportsFlaskStyleURLFor(t *testing.T) {
	t.Parallel()

	env, err := NewEnvironment(Options{
		URLFor: StaticURLFor("/assets"),
	})
	if err != nil {
		t.Fatalf("NewEnvironment() error = %v", err)
	}

	tmpl, err := env.TemplateFromNamedString(
		"demo/page.html",
		`<script src="{{ url_for('static', filename='jinja-bootstrap-spa.js', v='42') }}"></script>`,
	)
	if err != nil {
		t.Fatalf("TemplateFromNamedString() error = %v", err)
	}

	rendered, err := tmpl.Render(nil)
	if err != nil {
		t.Fatalf("Render() error = %v", err)
	}

	expected := `<script src="/assets/jinja-bootstrap-spa.js?v=42"></script>`
	if rendered != expected {
		t.Fatalf("expected %q, got %q", expected, rendered)
	}
}
