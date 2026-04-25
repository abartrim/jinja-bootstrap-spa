package jinjabootstrapspa

import (
	"embed"
	"fmt"
	"io/fs"
	"regexp"
	"strings"
)

const (
	// MacroTemplateName is the virtual template path shared by Python and Go.
	MacroTemplateName = "jinja_bootstrap_spa/bootstrap_macros.html"
	// BaseTemplateName is the packaged base template path shared by Python and Go.
	BaseTemplateName = "jinja_bootstrap_spa/base.html"
	// LegacyBaseTemplateName keeps parity with PackageLoader("jinja_bootstrap_spa", "templates").
	LegacyBaseTemplateName = "base.html"
)

var bootstrapMacroPattern = regexp.MustCompile(`(?s)BOOTSTRAP_MACROS = """\n(.*?)\n"""`)

//go:embed src/jinja_bootstrap_spa/macros/bootstrap.py src/jinja_bootstrap_spa/templates/base.html
var packagedAssets embed.FS

// BootstrapMacrosSource extracts the canonical macro template source from the
// Python package so Go renders the same macro definitions without maintaining a
// second copy.
func BootstrapMacrosSource() (string, error) {
	source, err := packagedAssets.ReadFile("src/jinja_bootstrap_spa/macros/bootstrap.py")
	if err != nil {
		return "", fmt.Errorf("read canonical macro source: %w", err)
	}

	match := bootstrapMacroPattern.FindSubmatch(source)
	if len(match) != 2 {
		return "", fmt.Errorf("extract canonical macro source: %w", fs.ErrInvalid)
	}
	return decodePythonString(string(match[1]))
}

// PackagedTemplateSource returns the shared template source for a packaged
// virtual template name.
func PackagedTemplateSource(name string) (string, error) {
	switch cleanTemplateName(name) {
	case MacroTemplateName:
		return BootstrapMacrosSource()
	case BaseTemplateName, LegacyBaseTemplateName:
		source, err := packagedAssets.ReadFile("src/jinja_bootstrap_spa/templates/base.html")
		if err != nil {
			return "", fmt.Errorf("read packaged base template: %w", err)
		}
		return string(source), nil
	default:
		return "", fmt.Errorf("template %q: %w", name, fs.ErrNotExist)
	}
}

func decodePythonString(raw string) (string, error) {
	var builder strings.Builder

	for index := 0; index < len(raw); index++ {
		current := raw[index]
		if current != '\\' {
			builder.WriteByte(current)
			continue
		}

		index++
		if index >= len(raw) {
			return "", fmt.Errorf("decode python string: %w", fs.ErrInvalid)
		}

		switch raw[index] {
		case '\\':
			builder.WriteByte('\\')
		case '"':
			builder.WriteByte('"')
		case '\'':
			builder.WriteByte('\'')
		case 'n':
			builder.WriteByte('\n')
		case 'r':
			builder.WriteByte('\r')
		case 't':
			builder.WriteByte('\t')
		default:
			builder.WriteByte('\\')
			builder.WriteByte(raw[index])
		}
	}

	return builder.String(), nil
}
