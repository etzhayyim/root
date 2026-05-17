// deps_toml_parse.go — minimal in-tree TOML reader for deps.toml.
//
// Scope (intentionally narrow — zero external dependencies):
//   - [table] and [table.sub."quoted"] headers
//   - scalar assignments: string / int / bool
//   - string-array assignments: key = ["a", "b"]
//   - multi-line string arrays across newlines
//   - comments (#), quoted keys, escaped quotes in strings
//
// NOT supported (by design):
//   - dotted keys (a.b = x) outside headers
//   - inline tables  ({ a = 1, b = 2 })
//   - nested arrays of tables ([[arr]])
//   - datetime / float / hex literals
//
// This subset is enough for the layer-rule schema used in root deps.toml:
//
//	[app_layer."name"]
//	layer = 0
//	tags = ["s", "t"]
//	depends_on = ["other"]
//	description = "..."
//	paths = ["..."]
package main

import (
	"fmt"
	"sort"
	"strings"
)

// depsTOMLValue holds a single scalar value. Only one of the typed fields is set.
type depsTOMLValue struct {
	kind    string // "string" | "int" | "bool" | "strings"
	str     string
	integer int
	boolean bool
	strings []string
}

// depsTOMLTable represents a nested TOML table.
type depsTOMLTable struct {
	values map[string]*depsTOMLValue
	tables map[string]*depsTOMLTable
}

func newDepsTOMLTable() *depsTOMLTable {
	return &depsTOMLTable{
		values: map[string]*depsTOMLValue{},
		tables: map[string]*depsTOMLTable{},
	}
}

// table returns the child table at the given key, if any.
func (t *depsTOMLTable) table(key string) (*depsTOMLTable, bool) {
	if t == nil {
		return nil, false
	}
	sub, ok := t.tables[key]
	return sub, ok
}

// sortedKeys returns the child table keys in sorted order for deterministic iteration.
func (t *depsTOMLTable) sortedKeys() []string {
	if t == nil {
		return nil
	}
	keys := make([]string, 0, len(t.tables))
	for k := range t.tables {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}

func (t *depsTOMLTable) intVal(key string) (int, bool) {
	if t == nil {
		return 0, false
	}
	v, ok := t.values[key]
	if !ok || v.kind != "int" {
		return 0, false
	}
	return v.integer, true
}

func (t *depsTOMLTable) stringVal(key string) (string, bool) {
	if t == nil {
		return "", false
	}
	v, ok := t.values[key]
	if !ok || v.kind != "string" {
		return "", false
	}
	return v.str, true
}

func (t *depsTOMLTable) stringList(key string) ([]string, bool) {
	if t == nil {
		return nil, false
	}
	v, ok := t.values[key]
	if !ok || v.kind != "strings" {
		return nil, false
	}
	out := make([]string, len(v.strings))
	copy(out, v.strings)
	return out, true
}

// ensureTable walks a dotted header path, creating intermediate tables.
func (t *depsTOMLTable) ensureTable(parts []string) *depsTOMLTable {
	cur := t
	for _, part := range parts {
		sub, ok := cur.tables[part]
		if !ok {
			sub = newDepsTOMLTable()
			cur.tables[part] = sub
		}
		cur = sub
	}
	return cur
}

// depsTOMLParse parses the source into a root table.
func depsTOMLParse(src string) (*depsTOMLTable, error) {
	root := newDepsTOMLTable()
	current := root

	lines := strings.Split(src, "\n")
	for i := 0; i < len(lines); i++ {
		raw := lines[i]
		trimmed := strings.TrimSpace(raw)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}

		// Strip trailing comment (only outside strings/arrays — we only call
		// stripComment on header lines where no string spans occur).
		if strings.HasPrefix(trimmed, "[") {
			header := stripTrailingComment(trimmed)
			if !strings.HasSuffix(header, "]") {
				return nil, fmt.Errorf("line %d: unterminated table header: %q", i+1, trimmed)
			}
			header = strings.TrimSuffix(strings.TrimPrefix(header, "["), "]")
			parts, err := splitTOMLKeyPath(header)
			if err != nil {
				return nil, fmt.Errorf("line %d: %w", i+1, err)
			}
			current = root.ensureTable(parts)
			continue
		}

		// Scalar or array assignment. Multi-line arrays are joined until the
		// closing bracket is seen.
		eqIdx := strings.Index(trimmed, "=")
		if eqIdx < 0 {
			return nil, fmt.Errorf("line %d: expected '=' in %q", i+1, trimmed)
		}
		keyPart := strings.TrimSpace(trimmed[:eqIdx])
		valuePart := strings.TrimSpace(trimmed[eqIdx+1:])

		key, err := unquoteTOMLKey(keyPart)
		if err != nil {
			return nil, fmt.Errorf("line %d: %w", i+1, err)
		}

		if strings.HasPrefix(valuePart, "[") && !closesBracket(valuePart) {
			// Multi-line array: accumulate until we see ']'
			var builder strings.Builder
			builder.WriteString(valuePart)
			for j := i + 1; j < len(lines); j++ {
				builder.WriteString("\n")
				builder.WriteString(strings.TrimSpace(lines[j]))
				if closesBracket(lines[j]) {
					i = j
					break
				}
			}
			valuePart = builder.String()
		}

		val, err := parseTOMLValue(valuePart)
		if err != nil {
			return nil, fmt.Errorf("line %d (key %q): %w", i+1, key, err)
		}
		current.values[key] = val
	}

	return root, nil
}

// stripTrailingComment removes a trailing `# ...` comment from a header line.
// It assumes the header does not contain quoted `#` characters outside strings;
// for our TOML subset this is sufficient because header strings never contain `#`.
func stripTrailingComment(s string) string {
	inString := false
	for idx := 0; idx < len(s); idx++ {
		c := s[idx]
		if c == '"' {
			// Check escape
			if idx > 0 && s[idx-1] == '\\' {
				continue
			}
			inString = !inString
			continue
		}
		if c == '#' && !inString {
			return strings.TrimSpace(s[:idx])
		}
	}
	return s
}

// closesBracket returns true if the line contains a ']' outside of a string.
func closesBracket(s string) bool {
	inString := false
	for idx := 0; idx < len(s); idx++ {
		c := s[idx]
		if c == '"' {
			if idx > 0 && s[idx-1] == '\\' {
				continue
			}
			inString = !inString
			continue
		}
		if c == ']' && !inString {
			return true
		}
	}
	return false
}

// splitTOMLKeyPath splits a header like `app_layer."some-name"` into ["app_layer", "some-name"].
func splitTOMLKeyPath(header string) ([]string, error) {
	header = strings.TrimSpace(header)
	var parts []string
	pos := 0
	for pos < len(header) {
		// Skip leading whitespace
		for pos < len(header) && (header[pos] == ' ' || header[pos] == '\t') {
			pos++
		}
		if pos >= len(header) {
			break
		}
		if header[pos] == '"' {
			// Quoted key
			end, unquoted, err := readQuotedKey(header, pos)
			if err != nil {
				return nil, err
			}
			parts = append(parts, unquoted)
			pos = end
		} else {
			// Bare key until . or whitespace or end
			start := pos
			for pos < len(header) && header[pos] != '.' && header[pos] != ' ' && header[pos] != '\t' {
				pos++
			}
			parts = append(parts, header[start:pos])
		}
		// Skip whitespace
		for pos < len(header) && (header[pos] == ' ' || header[pos] == '\t') {
			pos++
		}
		if pos >= len(header) {
			break
		}
		if header[pos] == '.' {
			pos++
			continue
		}
		return nil, fmt.Errorf("unexpected character in header at position %d: %q", pos, header)
	}
	if len(parts) == 0 {
		return nil, fmt.Errorf("empty header")
	}
	return parts, nil
}

func readQuotedKey(s string, start int) (int, string, error) {
	if start >= len(s) || s[start] != '"' {
		return 0, "", fmt.Errorf("expected opening quote at %d", start)
	}
	var builder strings.Builder
	i := start + 1
	for i < len(s) {
		c := s[i]
		if c == '\\' && i+1 < len(s) {
			next := s[i+1]
			switch next {
			case '"', '\\':
				builder.WriteByte(next)
			case 'n':
				builder.WriteByte('\n')
			case 't':
				builder.WriteByte('\t')
			default:
				builder.WriteByte(next)
			}
			i += 2
			continue
		}
		if c == '"' {
			return i + 1, builder.String(), nil
		}
		builder.WriteByte(c)
		i++
	}
	return 0, "", fmt.Errorf("unterminated quoted key starting at %d", start)
}

// unquoteTOMLKey accepts either a bare key or a single quoted key segment.
func unquoteTOMLKey(s string) (string, error) {
	s = strings.TrimSpace(s)
	if strings.HasPrefix(s, `"`) {
		_, key, err := readQuotedKey(s, 0)
		return key, err
	}
	return s, nil
}

// parseTOMLValue parses a single value literal.
func parseTOMLValue(s string) (*depsTOMLValue, error) {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil, fmt.Errorf("empty value")
	}

	// String
	if strings.HasPrefix(s, `"`) {
		// Strip trailing comment before processing closing quote.
		clean, _ := stripValueComment(s)
		if len(clean) < 2 || !strings.HasSuffix(clean, `"`) {
			return nil, fmt.Errorf("unterminated string: %q", s)
		}
		inner, err := unescapeTOMLString(clean[1 : len(clean)-1])
		if err != nil {
			return nil, err
		}
		return &depsTOMLValue{kind: "string", str: inner}, nil
	}

	// Array of strings
	if strings.HasPrefix(s, "[") {
		clean := stripAllValueComments(s)
		if !strings.HasSuffix(clean, "]") {
			return nil, fmt.Errorf("unterminated array: %q", s)
		}
		inner := strings.TrimSpace(clean[1 : len(clean)-1])
		if inner == "" {
			return &depsTOMLValue{kind: "strings", strings: nil}, nil
		}
		items, err := splitTOMLArrayItems(inner)
		if err != nil {
			return nil, err
		}
		return &depsTOMLValue{kind: "strings", strings: items}, nil
	}

	// Strip trailing comment from literals
	literal, _ := stripValueComment(s)
	literal = strings.TrimSpace(literal)

	// Bool
	if literal == "true" {
		return &depsTOMLValue{kind: "bool", boolean: true}, nil
	}
	if literal == "false" {
		return &depsTOMLValue{kind: "bool", boolean: false}, nil
	}

	// Integer (accept leading +/- and underscores)
	normalized := strings.ReplaceAll(literal, "_", "")
	var n int
	_, err := fmt.Sscanf(normalized, "%d", &n)
	if err == nil {
		return &depsTOMLValue{kind: "int", integer: n}, nil
	}

	return nil, fmt.Errorf("unsupported value literal: %q", s)
}

func stripAllValueComments(s string) string {
	var builder strings.Builder
	inString := false
	inComment := false
	for i := 0; i < len(s); i++ {
		c := s[i]
		if inComment {
			if c == '\n' {
				inComment = false
				builder.WriteByte(c)
			}
			continue
		}
		if c == '"' {
			if i > 0 && s[i-1] == '\\' {
				builder.WriteByte(c)
				continue
			}
			inString = !inString
			builder.WriteByte(c)
			continue
		}
		if c == '#' && !inString {
			inComment = true
			continue
		}
		builder.WriteByte(c)
	}
	return strings.TrimSpace(builder.String())
}

// stripValueComment removes a trailing `# ...` comment from a value line,
// respecting quoted strings.
func stripValueComment(s string) (string, bool) {
	inString := false
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c == '"' {
			if i > 0 && s[i-1] == '\\' {
				continue
			}
			inString = !inString
			continue
		}
		if c == '#' && !inString {
			return strings.TrimSpace(s[:i]), true
		}
	}
	return s, false
}

// splitTOMLArrayItems splits the inside of a `["a", "b", "c"]` literal into strings.
func splitTOMLArrayItems(inner string) ([]string, error) {
	var items []string
	pos := 0
	for pos < len(inner) {
		// Skip whitespace and separators
		for pos < len(inner) && (inner[pos] == ' ' || inner[pos] == '\t' || inner[pos] == ',' || inner[pos] == '\n') {
			pos++
		}
		if pos >= len(inner) {
			break
		}
		if inner[pos] != '"' {
			return nil, fmt.Errorf("expected string in array at position %d: %q", pos, inner)
		}
		// Read quoted string
		end := pos + 1
		var builder strings.Builder
		for end < len(inner) {
			c := inner[end]
			if c == '\\' && end+1 < len(inner) {
				next := inner[end+1]
				switch next {
				case '"', '\\':
					builder.WriteByte(next)
				case 'n':
					builder.WriteByte('\n')
				case 't':
					builder.WriteByte('\t')
				default:
					builder.WriteByte(next)
				}
				end += 2
				continue
			}
			if c == '"' {
				items = append(items, builder.String())
				end++
				pos = end
				break
			}
			builder.WriteByte(c)
			end++
		}
		if end > len(inner) {
			return nil, fmt.Errorf("unterminated string in array: %q", inner)
		}
	}
	return items, nil
}

// unescapeTOMLString handles the basic TOML string escapes we use.
func unescapeTOMLString(s string) (string, error) {
	var builder strings.Builder
	for i := 0; i < len(s); i++ {
		c := s[i]
		if c == '\\' && i+1 < len(s) {
			next := s[i+1]
			switch next {
			case '"', '\\':
				builder.WriteByte(next)
			case 'n':
				builder.WriteByte('\n')
			case 't':
				builder.WriteByte('\t')
			default:
				builder.WriteByte(next)
			}
			i++
			continue
		}
		builder.WriteByte(c)
	}
	return builder.String(), nil
}
