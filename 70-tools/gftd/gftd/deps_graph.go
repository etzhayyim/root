// deps_graph.go — gftd deps graph: layer DAG visualization (tree/mermaid/dot/open).
//
// Source: root deps.toml ([app_layer.*] + [infra_layer.*] sections)
// Layer rules were migrated from DEPS.yaml → deps.toml on 2026-04-11.
// Zero external deps: minimal in-tree TOML subset parser (deps_toml_parse.go).
package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"sort"
	"strings"
)

// depsLayer represents a single layer rule entry from deps.toml.
type depsLayer struct {
	Name        string
	Layer       int
	Tags        []string
	Description string
	DependsOn   []string
	Paths       []string
	Section     string // "packages" (app_layer) or "infra" (infra_layer)
}

// loadLayerRules reads the root deps.toml and extracts [app_layer.*] + [infra_layer.*]
// entries. Returns layer rules in the same shape the renderer expects.
//
// This function ONLY reads <repoRoot>/deps.toml — if the file is missing,
// fail loudly.
func loadLayerRules(repoRoot string) ([]depsLayer, error) {
	depsFile := filepath.Join(repoRoot, "deps.toml")
	data, err := os.ReadFile(depsFile)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", depsFile, err)
	}

	doc, err := depsTOMLParse(string(data))
	if err != nil {
		return nil, fmt.Errorf("parse %s: %w", depsFile, err)
	}

	var layers []depsLayer
	layers = append(layers, extractLayerSection(doc, "app_layer", "packages")...)
	layers = append(layers, extractLayerSection(doc, "infra_layer", "infra")...)

	if len(layers) == 0 {
		return nil, fmt.Errorf("no layer rules found in %s ([app_layer.*] / [infra_layer.*])", depsFile)
	}
	return layers, nil
}

// extractLayerSection walks a parsed TOML document and collects entries under
// `[<section>."<name>"]`. Only the fields used by the DAG renderer are kept.
func extractLayerSection(doc *depsTOMLTable, section, sectionLabel string) []depsLayer {
	if doc == nil {
		return nil
	}
	tbl, ok := doc.table(section)
	if !ok || tbl == nil {
		return nil
	}
	var out []depsLayer
	for _, key := range tbl.sortedKeys() {
		sub, ok := tbl.table(key)
		if !ok || sub == nil {
			continue
		}
		layer := depsLayer{
			Name:    key,
			Section: sectionLabel,
		}
		if v, ok := sub.intVal("layer"); ok {
			layer.Layer = v
		}
		if v, ok := sub.stringVal("description"); ok {
			layer.Description = v
		}
		if v, ok := sub.stringList("tags"); ok {
			layer.Tags = v
		}
		if v, ok := sub.stringList("depends_on"); ok {
			layer.DependsOn = v
		}
		if v, ok := sub.stringList("paths"); ok {
			layer.Paths = v
		}
		out = append(out, layer)
	}
	return out
}

// filterLayers filters by section and optional tag.
func filterLayers(layers []depsLayer, section, tag string) []depsLayer {
	var out []depsLayer
	for _, l := range layers {
		if section != "all" && l.Section != section {
			continue
		}
		if tag != "" {
			found := false
			for _, t := range l.Tags {
				if t == tag {
					found = true
					break
				}
			}
			if !found {
				continue
			}
		}
		out = append(out, l)
	}
	return out
}

// ── ANSI colors ──

var layerColors = []string{
	"\033[38;5;51m",  // L0 cyan
	"\033[38;5;75m",  // L1 blue
	"\033[38;5;114m", // L2 green
	"\033[38;5;220m", // L3 yellow
	"\033[38;5;208m", // L4 orange
	"\033[38;5;204m", // L5 pink
	"\033[38;5;141m", // L6 purple
	"\033[38;5;245m", // L7 gray
}

const (
	cReset = "\033[0m"
	cBold  = "\033[1m"
	cDim   = "\033[2m"
)

// Tag labels for display
var tagLabels = map[string]string{
	"e": "Extract",
	"t": "Transform",
	"l": "Load",
	"q": "Query",
	"s": "Schema",
	"r": "Routing",
	"u": "UI",
}

func layerColor(n int) string {
	if n < len(layerColors) {
		return layerColors[n]
	}
	return layerColors[len(layerColors)-1]
}

func formatTags(tags []string) string {
	if len(tags) == 0 {
		return ""
	}
	var parts []string
	for _, t := range tags {
		if label, ok := tagLabels[t]; ok {
			parts = append(parts, t+":"+label)
		} else {
			parts = append(parts, t)
		}
	}
	return "[" + strings.Join(parts, " ") + "]"
}

// ── Tree renderer ──

func renderDepsTree(layers []depsLayer, section string) string {
	byLayer := map[int][]depsLayer{}
	for _, l := range layers {
		byLayer[l.Layer] = append(byLayer[l.Layer], l)
	}

	var keys []int
	for k := range byLayer {
		keys = append(keys, k)
	}
	sort.Ints(keys)

	var b strings.Builder
	b.WriteString(fmt.Sprintf("\n  %s%sDependency Layers (%s)%s\n", cBold, "", section, cReset))
	b.WriteString(fmt.Sprintf("  %s\n", strings.Repeat("─", 62)))
	b.WriteString(fmt.Sprintf("  %sRule: Layer N → depends only on Layer 0..N-1%s\n\n", cDim, cReset))

	for _, n := range keys {
		c := layerColor(n)
		entries := byLayer[n]
		b.WriteString(fmt.Sprintf("  %s%sLayer %d%s\n", c, cBold, n, cReset))

		for i, entry := range entries {
			isLast := i == len(entries)-1
			branch := "├─"
			cont := "│ "
			if isLast {
				branch = "└─"
				cont = "  "
			}

			// Name + deps
			depStr := ""
			if len(entry.DependsOn) > 0 {
				depStr = fmt.Sprintf(" %s→ %s%s", cDim, strings.Join(entry.DependsOn, ", "), cReset)
			}
			b.WriteString(fmt.Sprintf("  %s  %s %s%s%s\n", c, branch, entry.Name, cReset, depStr))

			// Tags + description
			tagStr := formatTags(entry.Tags)
			if tagStr != "" {
				tagStr = " " + tagStr
			}
			b.WriteString(fmt.Sprintf("  %s  %s %s%s%s%s\n", c, cont, cDim, entry.Description, tagStr, cReset))

			// Paths (compact)
			if len(entry.Paths) <= 3 {
				for _, p := range entry.Paths {
					b.WriteString(fmt.Sprintf("  %s  %s %s  %s%s\n", c, cont, cDim, p, cReset))
				}
			} else {
				b.WriteString(fmt.Sprintf("  %s  %s %s  %s  ...+%d more%s\n", c, cont, cDim, entry.Paths[0], len(entry.Paths)-1, cReset))
			}
		}
		b.WriteString("\n")
	}

	return b.String()
}

// ── Mermaid renderer ──

var mermaidColors = map[int]string{
	0: "fill:#e0f7fa,stroke:#00838f",
	1: "fill:#e3f2fd,stroke:#1565c0",
	2: "fill:#e8f5e9,stroke:#2e7d32",
	3: "fill:#fff8e1,stroke:#f9a825",
	4: "fill:#fff3e0,stroke:#ef6c00",
	5: "fill:#fce4ec,stroke:#c62828",
	6: "fill:#f3e5f5,stroke:#6a1b9a",
	7: "fill:#eceff1,stroke:#546e7a",
}

func safeID(name string) string {
	return strings.ReplaceAll(name, "-", "_")
}

func renderDepsMermaid(layers []depsLayer, section string) string {
	var b strings.Builder
	b.WriteString(fmt.Sprintf("# Dependency Graph (%s)\n\n```mermaid\nflowchart TD\n", section))

	byLayer := map[int][]depsLayer{}
	for _, l := range layers {
		byLayer[l.Layer] = append(byLayer[l.Layer], l)
	}

	var keys []int
	for k := range byLayer {
		keys = append(keys, k)
	}
	sort.Ints(keys)

	// Subgraphs
	for _, n := range keys {
		b.WriteString(fmt.Sprintf("  subgraph L%d[\"Layer %d\"]\n", n, n))
		for _, entry := range byLayer[n] {
			id := safeID(entry.Name)
			tagStr := ""
			if len(entry.Tags) > 0 {
				tagStr = " [" + strings.Join(entry.Tags, ",") + "]"
			}
			b.WriteString(fmt.Sprintf("    %s[\"%s%s\"]\n", id, entry.Name, tagStr))
		}
		b.WriteString("  end\n")
	}

	b.WriteString("\n")

	// Edges
	for _, entry := range layers {
		for _, dep := range entry.DependsOn {
			b.WriteString(fmt.Sprintf("  %s --> %s\n", safeID(dep), safeID(entry.Name)))
		}
	}

	b.WriteString("\n")

	// Styles
	for _, entry := range layers {
		style := mermaidColors[entry.Layer]
		if style == "" {
			style = "fill:#fff,stroke:#333"
		}
		b.WriteString(fmt.Sprintf("  style %s %s\n", safeID(entry.Name), style))
	}

	b.WriteString("```\n")
	return b.String()
}

// ── Graphviz DOT renderer ──

var dotColors = map[int]string{
	0: "#00838f",
	1: "#1565c0",
	2: "#2e7d32",
	3: "#f9a825",
	4: "#ef6c00",
	5: "#c62828",
	6: "#6a1b9a",
	7: "#546e7a",
}

func renderDepsDot(layers []depsLayer, section string) string {
	var b strings.Builder
	b.WriteString("digraph deps {\n")
	b.WriteString("  rankdir=BT;\n")
	b.WriteString("  node [shape=box, style=\"filled,rounded\", fontname=\"Helvetica\", fontsize=11];\n")
	b.WriteString("  edge [color=\"#888888\"];\n\n")

	byLayer := map[int][]depsLayer{}
	for _, l := range layers {
		byLayer[l.Layer] = append(byLayer[l.Layer], l)
	}

	var keys []int
	for k := range byLayer {
		keys = append(keys, k)
	}
	sort.Ints(keys)

	for _, n := range keys {
		c := dotColors[n]
		if c == "" {
			c = "#333333"
		}
		b.WriteString(fmt.Sprintf("  subgraph cluster_L%d {\n", n))
		b.WriteString(fmt.Sprintf("    label=\"Layer %d\"; style=dashed; color=\"%s\"; fontcolor=\"%s\";\n", n, c, c))
		b.WriteString("    rank=same;\n")
		for _, entry := range byLayer[n] {
			id := safeID(entry.Name)
			// Truncate description for node label
			desc := entry.Description
			if len(desc) > 40 {
				desc = desc[:37] + "..."
			}
			tagStr := ""
			if len(entry.Tags) > 0 {
				tagStr = "\\n[" + strings.Join(entry.Tags, ",") + "]"
			}
			b.WriteString(fmt.Sprintf("    %s [label=\"%s\\n%s%s\", fillcolor=\"%s20\", color=\"%s\"];\n",
				id, entry.Name, desc, tagStr, c, c))
		}
		b.WriteString("  }\n")
	}

	b.WriteString("\n")

	for _, entry := range layers {
		for _, dep := range entry.DependsOn {
			b.WriteString(fmt.Sprintf("  %s -> %s;\n", safeID(dep), safeID(entry.Name)))
		}
	}

	b.WriteString("}\n")
	return b.String()
}

// ── Command implementation ──

func runDepsGraph(args []string) error {
	fs := flag.NewFlagSet("deps graph", flag.ContinueOnError)
	format := fs.String("format", "tree", "output format: tree, mermaid, dot, open")
	section := fs.String("section", "all", "section: packages, infra, all")
	tag := fs.String("tag", "", "filter by ETL tag: e, t, l, q, s, r, u")
	output := fs.String("output", "", "output file path (default: stdout for tree, reports/ for mermaid/dot)")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	root, err := findGitRoot(".")
	if err != nil {
		return fmt.Errorf("find git root: %w", err)
	}

	// Layer rules live in root deps.toml ([app_layer.*] + [infra_layer.*]).
	layers, err := loadLayerRules(root)
	if err != nil {
		return err
	}

	layers = filterLayers(layers, *section, *tag)
	if len(layers) == 0 {
		return fmt.Errorf("no layers matched (section=%s, tag=%s)", *section, *tag)
	}

	switch *format {
	case "tree":
		fmt.Print(renderDepsTree(layers, *section))

	case "mermaid":
		content := renderDepsMermaid(layers, *section)
		out := *output
		if out == "" {
			out = filepath.Join(root, "reports", "deps-graph.md")
		}
		if err := os.MkdirAll(filepath.Dir(out), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(out, []byte(content), 0o644); err != nil {
			return err
		}
		fmt.Printf("Mermaid written to %s\n", out)

	case "dot":
		dotSrc := renderDepsDot(layers, *section)
		svgOut := *output
		if svgOut == "" {
			svgOut = filepath.Join(root, "reports", "deps-graph.svg")
		}
		dotFile := strings.TrimSuffix(svgOut, ".svg") + ".dot"
		if err := os.MkdirAll(filepath.Dir(svgOut), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(dotFile, []byte(dotSrc), 0o644); err != nil {
			return err
		}
		fmt.Printf("DOT written to %s\n", dotFile)

		// Generate SVG if graphviz is available
		if dotBin, lookErr := exec.LookPath("dot"); lookErr == nil {
			cmd := exec.Command(dotBin, "-Tsvg", "-o", svgOut, dotFile)
			if out, runErr := cmd.CombinedOutput(); runErr != nil {
				fmt.Fprintf(os.Stderr, "dot warning: %s\n", string(out))
			} else {
				fmt.Printf("SVG written to %s\n", svgOut)
			}
		} else {
			fmt.Fprintf(os.Stderr, "Install graphviz for SVG: brew install graphviz\n")
		}

	case "open":
		// Generate mermaid + dot, then open SVG
		mermaidOut := filepath.Join(root, "reports", "deps-graph.md")
		svgOut := filepath.Join(root, "reports", "deps-graph.svg")
		dotFile := filepath.Join(root, "reports", "deps-graph.dot")

		if err := os.MkdirAll(filepath.Dir(mermaidOut), 0o755); err != nil {
			return err
		}

		// Write mermaid
		if err := os.WriteFile(mermaidOut, []byte(renderDepsMermaid(layers, *section)), 0o644); err != nil {
			return err
		}
		fmt.Printf("Mermaid: %s\n", mermaidOut)

		// Write dot + SVG
		dotSrc := renderDepsDot(layers, *section)
		if err := os.WriteFile(dotFile, []byte(dotSrc), 0o644); err != nil {
			return err
		}

		openTarget := mermaidOut // fallback
		if dotBin, lookErr := exec.LookPath("dot"); lookErr == nil {
			cmd := exec.Command(dotBin, "-Tsvg", "-o", svgOut, dotFile)
			if _, runErr := cmd.CombinedOutput(); runErr == nil {
				openTarget = svgOut
				fmt.Printf("SVG: %s\n", svgOut)
			}
		}

		// Open in default viewer
		openCmd := "xdg-open"
		if runtime.GOOS == "darwin" {
			openCmd = "open"
		}
		fmt.Printf("Opening %s ...\n", openTarget)
		return exec.Command(openCmd, openTarget).Start()

	default:
		return fmt.Errorf("unknown format: %s (use tree, mermaid, dot, open)", *format)
	}

	return nil
}
