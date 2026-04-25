package jinjabootstrapspa

import (
	"errors"
	"fmt"
	"io/fs"
	"net/url"
	"path"
	"sort"
	"strings"

	minijinja "github.com/mitsuhiko/minijinja/minijinja-go/v2"
	"github.com/mitsuhiko/minijinja/minijinja-go/v2/value"
)

// URLForFunc is an optional compatibility hook for Flask-style url_for calls.
type URLForFunc func(endpoint string, values map[string]any) (string, error)

// Options configures the MiniJinja environment wrapper.
type Options struct {
	// TemplateFS provides application templates in addition to the packaged
	// shared templates exposed by this repository.
	TemplateFS fs.FS
	// URLFor enables Flask-style {{ url_for(...) }} template calls.
	URLFor URLForFunc
	// Globals are added to the MiniJinja environment as template globals.
	Globals map[string]any
}

// NewEnvironment returns a MiniJinja environment configured to load the
// packaged jinja-bootstrap-spa templates and optional application templates.
func NewEnvironment(opts Options) (*minijinja.Environment, error) {
	env := minijinja.NewEnvironment()
	if err := ConfigureEnvironment(env, opts); err != nil {
		return nil, err
	}
	return env, nil
}

// ConfigureEnvironment mutates an existing MiniJinja environment in place.
func ConfigureEnvironment(env *minijinja.Environment, opts Options) error {
	if env == nil {
		return errors.New("configure environment: nil environment")
	}

	env.SetLoader(func(name string) (string, error) {
		return loadTemplate(opts.TemplateFS, name)
	})
	env.SetPathJoinCallback(joinTemplatePath)
	env.AddFunction("url_for", makeURLForFunction(opts.URLFor))

	for name, global := range opts.Globals {
		env.AddGlobal(name, value.FromAny(global))
	}

	return nil
}

// StaticURLFor returns a small Flask-like url_for implementation for static
// assets. It only accepts endpoint="static" plus a filename keyword.
func StaticURLFor(staticPrefix string) URLForFunc {
	prefix := "/" + strings.Trim(strings.TrimSpace(staticPrefix), "/")
	if prefix == "/" {
		prefix = "/static"
	}

	return func(endpoint string, values map[string]any) (string, error) {
		if endpoint != "static" {
			return "", fmt.Errorf("static url_for only supports endpoint %q", "static")
		}

		filename, ok := values["filename"].(string)
		if !ok || strings.TrimSpace(filename) == "" {
			return "", errors.New("static url_for requires a filename keyword")
		}

		delete(values, "filename")
		target := prefix + "/" + strings.TrimLeft(filename, "/")
		query := encodeQuery(values)
		if query == "" {
			return target, nil
		}
		return target + "?" + query, nil
	}
}

func loadTemplate(templateFS fs.FS, name string) (string, error) {
	cleanName := cleanTemplateName(name)

	if templateFS != nil {
		content, readErr := fs.ReadFile(templateFS, cleanName)
		if readErr == nil {
			return string(content), nil
		}
		if !errors.Is(readErr, fs.ErrNotExist) {
			return "", fmt.Errorf("read template %q: %w", cleanName, readErr)
		}
	}

	source, err := PackagedTemplateSource(cleanName)
	if err == nil {
		return source, nil
	}
	if !errors.Is(err, fs.ErrNotExist) {
		return "", err
	}

	return "", fmt.Errorf("template %q: %w", cleanName, fs.ErrNotExist)
}

func joinTemplatePath(name string, parent string) string {
	trimmed := strings.TrimSpace(name)
	if trimmed == "" {
		return ""
	}
	if strings.HasPrefix(trimmed, "./") || strings.HasPrefix(trimmed, "../") {
		parentDir := path.Dir(cleanTemplateName(parent))
		return cleanTemplateName(path.Join(parentDir, trimmed))
	}
	return cleanTemplateName(trimmed)
}

func cleanTemplateName(name string) string {
	clean := path.Clean(strings.TrimSpace(name))
	clean = strings.TrimPrefix(clean, "./")
	clean = strings.TrimPrefix(clean, "/")
	if clean == "." {
		return ""
	}
	return clean
}

func makeURLForFunction(builder URLForFunc) minijinja.FunctionFunc {
	return func(
		_ *minijinja.State,
		args []value.Value,
		kwargs map[string]value.Value,
	) (value.Value, error) {
		if builder == nil {
			return value.Undefined(), errors.New(
				"url_for is not configured; provide jinjabootstrapspa.Options{URLFor: ...}",
			)
		}
		if len(args) != 1 {
			return value.Undefined(), errors.New(
				"url_for expects exactly one positional argument for the endpoint name",
			)
		}

		endpoint, ok := args[0].AsString()
		if !ok || strings.TrimSpace(endpoint) == "" {
			return value.Undefined(), errors.New(
				"url_for requires the endpoint argument to be a string",
			)
		}

		values := make(map[string]any, len(kwargs))
		for key, raw := range kwargs {
			values[key] = valueToAny(raw)
		}

		target, err := builder(endpoint, values)
		if err != nil {
			return value.Undefined(), err
		}
		return value.FromSafeString(target), nil
	}
}

func valueToAny(v value.Value) any {
	if v.IsUndefined() || v.IsNone() {
		return nil
	}
	if stringValue, ok := v.AsString(); ok {
		return stringValue
	}
	if intValue, ok := v.AsInt(); ok {
		return intValue
	}
	if floatValue, ok := v.AsFloat(); ok {
		return floatValue
	}
	if boolValue, ok := v.AsBool(); ok {
		return boolValue
	}
	if values, ok := v.AsSlice(); ok {
		items := make([]any, 0, len(values))
		for _, item := range values {
			items = append(items, valueToAny(item))
		}
		return items
	}
	if values, ok := v.AsMap(); ok {
		items := make(map[string]any, len(values))
		for key, item := range values {
			items[key] = valueToAny(item)
		}
		return items
	}
	return v.Raw()
}

func encodeQuery(values map[string]any) string {
	if len(values) == 0 {
		return ""
	}

	keys := make([]string, 0, len(values))
	for key := range values {
		keys = append(keys, key)
	}
	sort.Strings(keys)

	query := url.Values{}
	for _, key := range keys {
		appendQueryValue(query, key, values[key])
	}
	return query.Encode()
}

func appendQueryValue(query url.Values, key string, raw any) {
	switch value := raw.(type) {
	case nil:
		return
	case []string:
		for _, item := range value {
			query.Add(key, item)
		}
	case []any:
		for _, item := range value {
			appendQueryValue(query, key, item)
		}
	default:
		query.Add(key, fmt.Sprint(value))
	}
}
