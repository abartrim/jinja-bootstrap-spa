package main

import (
	"net/http/httptest"
	"strings"
	"testing"
)

func TestExampleAppRendersIndexTemplate(t *testing.T) {
	t.Parallel()

	app, err := newExampleApp()
	if err != nil {
		t.Fatalf("newExampleApp() error = %v", err)
	}

	request := httptest.NewRequest("GET", "/", nil)
	context, err := app.buildIndexContext(request)
	if err != nil {
		t.Fatalf("buildIndexContext() error = %v", err)
	}

	rendered, err := app.renderTemplate("index.html", context)
	if err != nil {
		t.Fatalf("renderTemplate(index.html) error = %v", err)
	}

	for _, fragment := range []string{
		"Jinja Bootstrap SPA Showcase",
		`id="orders-table"`,
		`id="live-table"`,
		`id="live-append-table"`,
		`id="session-table"`,
		`id="foundation-gallery"`,
		`src="/assets/jinja-bootstrap-spa.js"`,
	} {
		if !strings.Contains(rendered, fragment) {
			t.Fatalf("expected rendered index to contain %q", fragment)
		}
	}
}
