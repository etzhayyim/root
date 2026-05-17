// gftd docs-gen — auto-generate factual schema docs from Parquet/local sources.
//
// Reads magatama.jsonld + wrangler.jsonc + src/*.ts to produce schema.auto.md or JSON.
// Shannon principle: factual content only (labels/collections/deps).
// Behavioral rules remain human-authored in CLAUDE.md.
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

// AppSchema is the auto-generated factual schema for one App.
type AppSchema struct {
	App             string   `json:"app"`
	Nanoid          string   `json:"nanoid,omitempty"`
	DID             string   `json:"did,omitempty"`
	Project         string   `json:"project,omitempty"`
	PerformerType   string   `json:"performerType,omitempty"`
	Collections     []string `json:"collections,omitempty"`
	GraphLabels     []string `json:"graphLabels,omitempty"`
	ServiceBindings []string `json:"serviceBindings,omitempty"`
	WitImports      []string `json:"witImports,omitempty"`
	ScannedAt       string   `json:"scannedAt"`
}

var (
	docsGenGLabelRe    = regexp.MustCompile(`G\(\s*["']([A-Z][a-zA-Z0-9]*)["']`)
	docsGenBindingRe   = regexp.MustCompile(`"binding"\s*:\s*"([^"]+)"`)
	docsGenWitImportRe = regexp.MustCompile(`(?m)^\s*import\s+([^\s{]+)\s+from\s+"([^"]+)"`)
)

// runDocsGen is the entry point for `gftd docs-gen`.
func runDocsGen(args []string) error {
	if len(args) == 0 {
		printDocsGenUsage()
		return nil
	}
	switch args[0] {
	case "schema":
		return runDocsGenSchema(args[1:])
	case "help", "--help", "-h":
		printDocsGenUsage()
		return nil
	default:
		return fmt.Errorf("unknown docs-gen subcommand: %s\nRun 'gftd docs-gen --help' for usage", args[0])
	}
}

func printDocsGenUsage() {
	fmt.Print(`gftd docs-gen — auto-generate factual schema docs from local sources

USAGE:
  gftd docs-gen <subcommand> [flags]

SUBCOMMANDS:
  schema   Generate schema.auto.md / JSON from magatama.jsonld + src scan

DESCRIPTION:
  Reads magatama.jsonld (collections, performerType), wrangler.jsonc (service
  bindings), and src/*.ts (G("Label") graph patterns) to produce factual content.
  Output is always derivable from ground truth — never hand-edit the output.

  --format md + --all writes schema.auto.md into each project directory.
  These files can be @imported or injected into Claude context on demand.

Run 'gftd docs-gen schema --help' for flags.
`)
}

func runDocsGenSchema(args []string) error {
	fs := flag.NewFlagSet("docs-gen schema", flag.ContinueOnError)
	dir := fs.String("dir", ".", "project directory containing magatama.jsonld")
	all := fs.Bool("all", false, "scan all projects under 60-apps/ and write schema.auto.md per project")
	format := fs.String("format", "json", "output format: json or md")
	out := fs.String("out", "", "output file path (default: stdout; ignored with --all)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*dir)
	if err != nil {
		return err
	}

	if *all {
		return runDocsGenSchemaAll(wsRoot)
	}

	absDir := *dir
	if !filepath.IsAbs(absDir) {
		if cwd, e := os.Getwd(); e == nil {
			absDir = filepath.Join(cwd, absDir)
		}
	}

	schema, err := scanAppSchema(absDir, wsRoot)
	if err != nil {
		return err
	}

	var rendered string
	if *format == "md" {
		rendered = renderSchemaMarkdown(schema)
	} else {
		b, _ := json.MarshalIndent(schema, "", "  ")
		rendered = string(b)
	}

	if *out != "" {
		return os.WriteFile(*out, []byte(rendered+"\n"), 0o644)
	}
	fmt.Println(rendered)
	return nil
}

// runDocsGenSchemaAll scans every 60-apps/ai-gftd-project-*/wasm/*/magatama.jsonld and writes schema.auto.md.
func runDocsGenSchemaAll(wsRoot string) error {
	// Collect all wasm component directories via glob
	pattern := filepath.Join(wsRoot, "60-apps", "ai-gftd-project-*", "wasm", "*", "magatama.jsonld")
	matches, err := filepath.Glob(pattern)
	if err != nil {
		return fmt.Errorf("glob: %w", err)
	}

	var wrote, skipped int
	for _, jsonldPath := range matches {
		// Skip .gftd-deploy copies
		if strings.Contains(jsonldPath, ".gftd-deploy") {
			continue
		}
		componentDir := filepath.Dir(jsonldPath)

		schema, err := scanAppSchema(componentDir, wsRoot)
		if err != nil {
			fmt.Fprintf(os.Stderr, "docs-gen: skip %s: %v\n", componentDir, err)
			skipped++
			continue
		}

		outPath := filepath.Join(componentDir, "schema.auto.md")
		content := renderSchemaMarkdown(schema)
		if err := os.WriteFile(outPath, []byte(content+"\n"), 0o644); err != nil {
			fmt.Fprintf(os.Stderr, "docs-gen: write %s: %v\n", outPath, err)
			skipped++
			continue
		}
		wrote++
	}

	fmt.Fprintf(os.Stderr, "docs-gen schema --all: wrote %d, skipped %d\n", wrote, skipped)
	return nil
}

// scanAppSchema reads magatama.jsonld, wrangler.jsonc, and src/*.ts to build AppSchema.
func scanAppSchema(projectDir, wsRoot string) (*AppSchema, error) {
	cfg, err := readMagatamaJSONLD(projectDir)
	if err != nil {
		return nil, fmt.Errorf("magatama.jsonld: %w", err)
	}

	schema := &AppSchema{
		App:           cfg.Name,
		Nanoid:        cfg.Nanoid,
		DID:           cfg.ID,
		Project:       cfg.Project,
		PerformerType: cfg.PerformerType,
		ScannedAt:     time.Now().UTC().Format(time.RFC3339),
	}

	// Collections from triggers.subscribeRepos
	if cfg.Triggers != nil && cfg.Triggers.SubscribeRepos != nil {
		schema.Collections = cfg.Triggers.SubscribeRepos.Collections
	}

	// Service bindings from wrangler.jsonc (generated at deploy time)
	if bindings := scanWranglerBindings(projectDir); len(bindings) > 0 {
		schema.ServiceBindings = bindings
	} else {
		// Default: all apps use PDS_SERVICE and HYPERDRIVE
		schema.ServiceBindings = []string{"PDS_SERVICE", "HYPERDRIVE"}
	}

	// Graph labels from src/*.ts G("Label") scan
	schema.GraphLabels = scanTSGraphLabels(projectDir)

	// WIT imports — retired per ADR-0049. AT Lexicon JSON under
	// 00-contracts/lexicons/ is the surviving contract. The schema.WitImports
	// field is retained (empty slice) so any external JSON consumer keeps
	// its shape stable.

	return schema, nil
}

// scanWranglerBindings reads wrangler.jsonc and extracts "binding" values from services[].
func scanWranglerBindings(projectDir string) []string {
	data, err := os.ReadFile(filepath.Join(projectDir, "wrangler.jsonc"))
	if err != nil {
		return nil
	}
	// Strip single-line // comments (simple JSONC handling)
	stripped := stripJSONComments(string(data))

	// Extract all "binding": "..." values
	matches := docsGenBindingRe.FindAllStringSubmatch(stripped, -1)
	seen := make(map[string]bool)
	var bindings []string
	for _, m := range matches {
		b := m[1]
		if !seen[b] {
			seen[b] = true
			bindings = append(bindings, b)
		}
	}
	sort.Strings(bindings)
	return bindings
}

// stripJSONComments removes // single-line comments from JSON-with-comments text.
func stripJSONComments(src string) string {
	var sb strings.Builder
	inString := false
	i := 0
	for i < len(src) {
		c := src[i]
		if inString {
			if c == '\\' && i+1 < len(src) {
				sb.WriteByte(c)
				sb.WriteByte(src[i+1])
				i += 2
				continue
			}
			if c == '"' {
				inString = false
			}
			sb.WriteByte(c)
			i++
			continue
		}
		if c == '"' {
			inString = true
			sb.WriteByte(c)
			i++
			continue
		}
		if c == '/' && i+1 < len(src) && src[i+1] == '/' {
			// Skip until end of line
			for i < len(src) && src[i] != '\n' {
				i++
			}
			continue
		}
		sb.WriteByte(c)
		i++
	}
	return sb.String()
}

// scanTSGraphLabels scans src/*.ts for G("Label") patterns and returns unique labels.
func scanTSGraphLabels(projectDir string) []string {
	srcDir := filepath.Join(projectDir, "src")
	entries, err := os.ReadDir(srcDir)
	if err != nil {
		return nil
	}

	seen := make(map[string]bool)
	var labels []string
	for _, e := range entries {
		if e.IsDir() || !strings.HasSuffix(e.Name(), ".ts") {
			continue
		}
		data, err := os.ReadFile(filepath.Join(srcDir, e.Name()))
		if err != nil {
			continue
		}
		for _, m := range docsGenGLabelRe.FindAllStringSubmatch(string(data), -1) {
			lbl := m[1]
			if !seen[lbl] {
				seen[lbl] = true
				labels = append(labels, lbl)
			}
		}
	}
	sort.Strings(labels)
	return labels
}

// scanWitImports was the pre-ADR-0049 WIT bindgen scanner. Retired — all
// callers read AT Lexicon JSON at 00-contracts/lexicons/ instead. Function
// removed; the `WitImports` field on AppSchema stays for JSON shape
// compatibility but is never populated.

// renderSchemaMarkdown renders AppSchema as Markdown with auto-generated header.
func renderSchemaMarkdown(s *AppSchema) string {
	var sb strings.Builder
	sb.WriteString(fmt.Sprintf("<!-- AUTO-GENERATED by gftd docs-gen schema. Regenerate: gftd docs-gen schema --dir . --format md --out schema.auto.md -->\n"))
	sb.WriteString(fmt.Sprintf("<!-- scannedAt: %s -->\n\n", s.ScannedAt))
	sb.WriteString(fmt.Sprintf("## Schema: %s\n\n", s.App))

	sb.WriteString("### App\n\n")
	if s.Nanoid != "" {
		sb.WriteString(fmt.Sprintf("| Key | Value |\n|---|---|\n"))
		sb.WriteString(fmt.Sprintf("| **name** | `%s` |\n", s.App))
		if s.Nanoid != "" {
			sb.WriteString(fmt.Sprintf("| **nanoid** | `%s` |\n", s.Nanoid))
		}
		if s.DID != "" {
			sb.WriteString(fmt.Sprintf("| **did** | `%s` |\n", s.DID))
		}
		if s.Project != "" {
			sb.WriteString(fmt.Sprintf("| **project** | `%s` |\n", s.Project))
		}
		if s.PerformerType != "" {
			sb.WriteString(fmt.Sprintf("| **performerType** | `%s` |\n", s.PerformerType))
		}
		sb.WriteString("\n")
	}

	if len(s.Collections) > 0 {
		sb.WriteString("### Collections\n\n")
		for _, c := range s.Collections {
			sb.WriteString(fmt.Sprintf("- `%s`\n", c))
		}
		sb.WriteString("\n")
	}

	if len(s.GraphLabels) > 0 {
		sb.WriteString("### Graph Labels (G() scan)\n\n")
		for _, l := range s.GraphLabels {
			sb.WriteString(fmt.Sprintf("- `:%s`\n", l))
		}
		sb.WriteString("\n")
	}

	if len(s.ServiceBindings) > 0 {
		sb.WriteString("### Service Bindings\n\n")
		for _, b := range s.ServiceBindings {
			sb.WriteString(fmt.Sprintf("- `%s`\n", b))
		}
		sb.WriteString("\n")
	}

	// WIT Imports section retired per ADR-0049 (WIT bindgen dead path).

	return strings.TrimRight(sb.String(), "\n")
}
