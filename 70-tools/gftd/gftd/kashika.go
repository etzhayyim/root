package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"sort"
	"strings"
)

// --- entry point ---

func runKashika(args []string) error {
	if len(args) == 0 {
		printKashikaUsage()
		return nil
	}
	switch args[0] {
	case "terminal":
		return runKashikaTerminal(args[1:])
	case "dot":
		return runKashikaDot(args[1:])
	case "mermaid":
		return runKashikaMermaid(args[1:])
	case "html":
		return runKashikaHTML(args[1:])
	case "sla":
		return runKashikaSLA(args[1:])
	case "shinka":
		return runKashikaShinka(args[1:])
	case "hyoka":
		return runKashikaHyoka(args[1:])
	case "help", "--help", "-h":
		printKashikaUsage()
		return nil
	default:
		return fmt.Errorf("unknown kashika command: %s", args[0])
	}
}

func printKashikaUsage() {
	fmt.Print(`gftd kashika — visualization renderer (可視化)

USAGE:
  gftd kashika <format> [flags]

FORMATS:
  terminal    ANSI terminal table summary
  dot         Graphviz DOT digraph
  mermaid     Mermaid diagram (Markdown-embeddable)
  html        Self-contained HTML with D3.js force-directed graph
  sla         99.999% SLA design analysis (PDS/Worker/Infra)
  shinka      Shinka/Kyumei-Koji health visualization (monitor shinka JSON)
  hyoka       Actor self-organization evaluation visualization (hyoka score)

INPUT:
  --source haisen       (default) read haisen JSON from stdin or --input
  --source sos          read systemofsystem JSON from stdin or --input
  --input <file>        read from file instead of stdin

EXAMPLES:
  gftd haisen scan | gftd kashika terminal
  gftd haisen scan | gftd kashika dot | dot -Tpng -o wiring.png
  gftd haisen scan | gftd kashika mermaid > wiring.md
  gftd haisen scan | gftd kashika html > wiring.html && open wiring.html
  gftd systemofsystem scan | gftd kashika terminal --source sos
  gftd monitor shinka --json | gftd kashika shinka > shinka.svg
  gftd kashika shinka --input reports/260402-monitor-shinka.json --format terminal
  gftd monitor shinka --hyoka --json | gftd kashika hyoka --format html > hyoka.html

Run 'gftd kashika <format> --help' for format-specific flags.
`)
}

// --- common input parsing ---

func kashikaParseInput(args []string) (*flag.FlagSet, *string, *string, error) {
	fs := flag.NewFlagSet("kashika", flag.ContinueOnError)
	source := fs.String("source", "haisen", "input source type: haisen, sos")
	input := fs.String("input", "", "input file (default: stdin)")
	if err := fs.Parse(args); err != nil {
		return fs, source, input, err
	}
	return fs, source, input, nil
}

func kashikaReadInput(inputFile string) ([]byte, error) {
	if inputFile != "" {
		return os.ReadFile(inputFile)
	}
	return io.ReadAll(os.Stdin)
}

func kashikaParseHaisen(data []byte) (haisenGraph, error) {
	var g haisenGraph
	err := json.Unmarshal(data, &g)
	return g, err
}

func kashikaParseSoS(data []byte) (sosReport, error) {
	var r sosReport
	err := json.Unmarshal(data, &r)
	return r, err
}

// --- shinka format ---

type kashikaShinkaSummary struct {
	Total     int
	Joucho    int
	Inbox     int
	Cadence   int
	Drill     int
	Validate  int
	Analyze   int
	Engage    int
	OldTimer  int
	AvgShinka float64
	AvgHyoka  float64
	MaxHyoka  int
	TopActor  string
}

func runKashikaShinka(args []string) error {
	fs := flag.NewFlagSet("kashika shinka", flag.ContinueOnError)
	input := fs.String("input", "", "input JSON file from `gftd monitor shinka --json` (default: stdin)")
	format := fs.String("format", "svg", "output format: terminal|dot|svg|png|html|json")
	output := fs.String("output", "", "output file path (default: stdout)")
	top := fs.Int("top", 20, "max old-timer apps listed in graph/table")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	data, err := kashikaReadInput(*input)
	if err != nil {
		return fmt.Errorf("read input: %w", err)
	}

	var rows []shinkaStatus
	if err := json.Unmarshal(data, &rows); err != nil {
		return fmt.Errorf("parse shinka JSON: %w", err)
	}

	summary := kashikaSummarizeShinka(rows)
	switch strings.ToLower(strings.TrimSpace(*format)) {
	case "terminal":
		return kashikaWriteOutput(*output, []byte(kashikaShinkaTerminal(summary, rows, *top)))
	case "dot":
		return kashikaWriteOutput(*output, []byte(kashikaShinkaDot(summary, rows, *top)))
	case "svg", "png":
		dot := kashikaShinkaDot(summary, rows, *top)
		graph, err := kashikaGraphviz(strings.ToLower(*format), dot)
		if err != nil {
			return err
		}
		return kashikaWriteOutput(*output, graph)
	case "html":
		dot := kashikaShinkaDot(summary, rows, *top)
		svg, err := kashikaGraphviz("svg", dot)
		if err != nil {
			return err
		}
		return kashikaWriteOutput(*output, []byte(kashikaShinkaHTML(summary, string(svg))))
	case "json":
		type out struct {
			Summary kashikaShinkaSummary `json:"summary"`
			Apps    []shinkaStatus       `json:"apps"`
		}
		buf, err := json.MarshalIndent(out{Summary: summary, Apps: rows}, "", "  ")
		if err != nil {
			return err
		}
		return kashikaWriteOutput(*output, append(buf, '\n'))
	default:
		return fmt.Errorf("unknown shinka format: %s", *format)
	}
}

func runKashikaHyoka(args []string) error {
	fs := flag.NewFlagSet("kashika hyoka", flag.ContinueOnError)
	input := fs.String("input", "", "input JSON file from `gftd monitor shinka --hyoka --json` (default: stdin)")
	format := fs.String("format", "html", "output format: terminal|dot|svg|png|html|json")
	output := fs.String("output", "", "output file path (default: stdout)")
	top := fs.Int("top", 30, "top actors in terminal output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	data, err := kashikaReadInput(*input)
	if err != nil {
		return fmt.Errorf("read input: %w", err)
	}
	var rows []shinkaStatus
	if err := json.Unmarshal(data, &rows); err != nil {
		return fmt.Errorf("parse hyoka JSON: %w", err)
	}
	summary := kashikaSummarizeShinka(rows)

	sort.Slice(rows, func(i, j int) bool {
		if rows[i].HyokaScore != rows[j].HyokaScore {
			return rows[i].HyokaScore > rows[j].HyokaScore
		}
		return rows[i].Nanoid < rows[j].Nanoid
	})

	switch strings.ToLower(strings.TrimSpace(*format)) {
	case "terminal":
		var b strings.Builder
		fmt.Fprintf(&b, "Hyoka Ranking (%d actors)\n", len(rows))
		fmt.Fprintf(&b, "Average Hyoka: %.1f / Average Shinka: %.1f\n\n", summary.AvgHyoka, summary.AvgShinka)
		limit := *top
		if limit > len(rows) {
			limit = len(rows)
		}
		for i := 0; i < limit; i++ {
			r := rows[i]
			fmt.Fprintf(&b, "%3d. %3d (%s)  %s  domain=%d kg=%d shinka=%d\n",
				i+1, r.HyokaScore, r.HyokaGrade, r.Nanoid, r.DomainScore, r.KGScore, r.ShinkaScore)
		}
		return kashikaWriteOutput(*output, []byte(b.String()))
	case "html":
		hyokaJSON, _ := json.Marshal(rows)
		return kashikaWriteOutput(*output, []byte(kashikaHyokaHTML(summary, string(hyokaJSON))))
	default:
		// Reuse shinka renderer for non-HTML formats
		return runKashikaShinka(append([]string{"--input", *input, "--format", *format, "--output", *output}, fmt.Sprintf("--top=%d", *top)))
	}
}

func kashikaSummarizeShinka(rows []shinkaStatus) kashikaShinkaSummary {
	s := kashikaShinkaSummary{Total: len(rows)}
	shinkaSum := 0
	hyokaSum := 0
	for _, r := range rows {
		if r.HasJoucho {
			s.Joucho++
		}
		if r.HasInbox {
			s.Inbox++
		}
		if r.HasCadence {
			s.Cadence++
		}
		if r.HasDrill {
			s.Drill++
		}
		if r.HasValidate {
			s.Validate++
		}
		if r.HasAnalyze {
			s.Analyze++
		}
		if r.HasEngage {
			s.Engage++
		}
		if r.HasOldTimer {
			s.OldTimer++
		}
		shinkaSum += r.ShinkaScore
		hyokaSum += r.HyokaScore
		if r.HyokaScore > s.MaxHyoka {
			s.MaxHyoka = r.HyokaScore
			s.TopActor = r.Nanoid
		}
	}
	if s.Total > 0 {
		s.AvgShinka = float64(shinkaSum) / float64(s.Total)
		s.AvgHyoka = float64(hyokaSum) / float64(s.Total)
	}
	return s
}

func kashikaShinkaTerminal(summary kashikaShinkaSummary, rows []shinkaStatus, top int) string {
	var b strings.Builder
	fmt.Fprintf(&b, "Shinka/Kyumei-Koji Health (%d apps)\n", summary.Total)
	fmt.Fprintf(&b, "  AvgShinka:%5.1f\n", summary.AvgShinka)
	fmt.Fprintf(&b, "  AvgHyoka: %5.1f\n", summary.AvgHyoka)
	fmt.Fprintf(&b, "  Joucho:   %4d (%.1f%%)\n", summary.Joucho, kashikaPct(summary.Joucho, summary.Total))
	fmt.Fprintf(&b, "  Inbox:    %4d (%.1f%%)\n", summary.Inbox, kashikaPct(summary.Inbox, summary.Total))
	fmt.Fprintf(&b, "  Cadence:  %4d (%.1f%%)\n", summary.Cadence, kashikaPct(summary.Cadence, summary.Total))
	fmt.Fprintf(&b, "  Drill:    %4d (%.1f%%)\n", summary.Drill, kashikaPct(summary.Drill, summary.Total))
	fmt.Fprintf(&b, "  Validate: %4d (%.1f%%)\n", summary.Validate, kashikaPct(summary.Validate, summary.Total))
	fmt.Fprintf(&b, "  Analyze:  %4d (%.1f%%)\n", summary.Analyze, kashikaPct(summary.Analyze, summary.Total))
	fmt.Fprintf(&b, "  Engage:   %4d (%.1f%%)\n", summary.Engage, kashikaPct(summary.Engage, summary.Total))
	fmt.Fprintf(&b, "  OldTimer: %4d (%.1f%%)\n", summary.OldTimer, kashikaPct(summary.OldTimer, summary.Total))

	old := make([]shinkaStatus, 0, len(rows))
	for _, r := range rows {
		if r.HasOldTimer {
			old = append(old, r)
		}
	}
	sort.Slice(old, func(i, j int) bool { return old[i].Nanoid < old[j].Nanoid })
	if len(old) > top {
		old = old[:top]
	}

	if len(old) > 0 {
		b.WriteString("\nTop old-timer violations:\n")
		for _, r := range old {
			fmt.Fprintf(&b, "  - %s (%s)\n", r.Nanoid, r.Name)
		}
	}
	return b.String()
}

func kashikaShinkaDot(summary kashikaShinkaSummary, rows []shinkaStatus, top int) string {
	old := make([]shinkaStatus, 0, len(rows))
	for _, r := range rows {
		if r.HasOldTimer {
			old = append(old, r)
		}
	}
	sort.Slice(old, func(i, j int) bool { return old[i].Nanoid < old[j].Nanoid })
	if len(old) > top {
		old = old[:top]
	}

	var b strings.Builder
	b.WriteString("digraph shinka {\n")
	b.WriteString("  rankdir=TB;\n")
	b.WriteString("  graph [bgcolor=\"#0b1020\", fontname=\"Helvetica\", labelloc=t, label=\"GFTD Shinka/Kyumei-Koji Health\", fontcolor=white];\n")
	b.WriteString("  node [shape=box, style=\"rounded,filled\", fillcolor=\"#111932\", color=\"#2a3b70\", fontname=\"Helvetica\", fontcolor=white];\n")
	b.WriteString("  edge [color=\"#4a5f9f\"];\n")
	fmt.Fprintf(&b, "  summary [label=\"Total Apps: %d\\nAvgShinka: %.1f\\nAvgHyoka: %.1f\\nTopActor: %s (%d)\\nJoucho: %d (%.1f%%)\\nInbox: %d (%.1f%%)\\nCadence: %d (%.1f%%)\\nDrill: %d (%.1f%%)\\nValidate: %d (%.1f%%)\\nAnalyze: %d (%.1f%%)\\nEngage: %d (%.1f%%)\\nOldTimer Violations: %d (%.1f%%)\"];\n",
		summary.Total,
		summary.AvgShinka,
		summary.AvgHyoka,
		summary.TopActor,
		summary.MaxHyoka,
		summary.Joucho, kashikaPct(summary.Joucho, summary.Total),
		summary.Inbox, kashikaPct(summary.Inbox, summary.Total),
		summary.Cadence, kashikaPct(summary.Cadence, summary.Total),
		summary.Drill, kashikaPct(summary.Drill, summary.Total),
		summary.Validate, kashikaPct(summary.Validate, summary.Total),
		summary.Analyze, kashikaPct(summary.Analyze, summary.Total),
		summary.Engage, kashikaPct(summary.Engage, summary.Total),
		summary.OldTimer, kashikaPct(summary.OldTimer, summary.Total),
	)
	if len(old) > 0 {
		var lines []string
		lines = append(lines, "Top OldTimer Violations")
		for _, r := range old {
			name := strings.TrimSpace(r.Name)
			if name == "" {
				lines = append(lines, r.Nanoid)
				continue
			}
			lines = append(lines, fmt.Sprintf("%s (%s)", r.Nanoid, name))
		}
		fmt.Fprintf(&b, "  note [shape=note, fillcolor=\"#1a1430\", color=\"#6f5ca8\", label=%q];\n", strings.Join(lines, "\\n"))
	} else {
		b.WriteString("  note [shape=note, fillcolor=\"#1a1430\", color=\"#6f5ca8\", label=\"Top OldTimer Violations\\n(none)\"];\n")
	}
	b.WriteString("  summary -> note;\n")
	b.WriteString("}\n")
	return b.String()
}

func kashikaShinkaHTML(summary kashikaShinkaSummary, svg string) string {
	return fmt.Sprintf(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GFTD Shinka/Kyumei-Koji Health</title>
<style>
body{margin:0;background:#0b1020;color:#fff;font:14px/1.5 system-ui,sans-serif}
.wrap{max-width:1200px;margin:24px auto;padding:0 16px}
.meta{color:#b8c0df;margin-bottom:14px}
.card{background:#111932;border:1px solid #2a3b70;border-radius:12px;padding:10px 14px;margin-bottom:14px}
.svg{background:#0b1020;border:1px solid #2a3b70;border-radius:12px;padding:12px;overflow:auto}
svg{max-width:100%%;height:auto}
</style></head><body>
<div class="wrap">
  <div class="card">
    <strong>Shinka/Kyumei-Koji Health</strong>
    <div class="meta">Apps=%d / AvgShinka=%.1f / AvgHyoka=%.1f / Joucho=%.1f%% / OldTimer=%.1f%%</div>
  </div>
  <div class="svg">%s</div>
</div>
</body></html>`,
		summary.Total,
		summary.AvgShinka,
		summary.AvgHyoka,
		kashikaPct(summary.Joucho, summary.Total),
		kashikaPct(summary.OldTimer, summary.Total),
		svg,
	)
}

func kashikaHyokaHTML(summary kashikaShinkaSummary, rowsJSON string) string {
	return fmt.Sprintf(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GFTD Hyoka Dashboard</title>
<style>
body{margin:0;background:#0b1020;color:#fff;font:14px/1.5 system-ui,sans-serif}
.wrap{max-width:1280px;margin:20px auto;padding:0 16px}
.card{background:#111932;border:1px solid #2a3b70;border-radius:12px;padding:12px 14px;margin-bottom:14px}
table{width:100%%;border-collapse:collapse;background:#111932;border:1px solid #2a3b70;border-radius:12px;overflow:hidden}
th,td{padding:8px 10px;border-bottom:1px solid #1d2a52;text-align:left}
th{background:#0e1733}
.gradeS{color:#00ff88}.gradeA{color:#88ff00}.gradeB{color:#ffcc00}.gradeC{color:#ff8844}.gradeD{color:#ff4444}
</style></head><body>
<div class="wrap">
  <div class="card">
    <strong>Hyoka Dashboard</strong><br>
    Actors=%d / AvgShinka=%.1f / AvgHyoka=%.1f / Top=%s (%d)
  </div>
  <table>
    <thead><tr><th>#</th><th>Nanoid</th><th>Hyoka</th><th>Domain</th><th>KG</th><th>Shinka</th><th>Mood</th></tr></thead>
    <tbody id="rows"></tbody>
  </table>
</div>
<script>
const rows=%s;
const g=(r,k)=> (r && r[k]!==undefined) ? r[k] : (r ? r[k.charAt(0).toUpperCase()+k.slice(1)] : undefined);
rows.sort((a,b)=> (Number(g(b,'hyokaScore')||0))-(Number(g(a,'hyokaScore')||0)) || String(g(a,'nanoid')||'').localeCompare(String(g(b,'nanoid')||'')));
const tbody=document.getElementById('rows');
rows.slice(0,300).forEach((r,i)=>{
  const tr=document.createElement('tr');
  const grade=String(g(r,'hyokaGrade')||'');
  tr.innerHTML='<td>'+ (i+1) +'</td><td>'+ (g(r,'nanoid')||'') +'</td><td class="grade'+grade+'">'+ (g(r,'hyokaScore')||0) +' ('+grade+')</td><td>'+ (g(r,'domainScore')||0) +'</td><td>'+ (g(r,'kgScore')||0) +' [n='+(g(r,'kgNodes')||0)+', l='+(g(r,'kgLabels')||0)+']</td><td>'+ (g(r,'shinkaScore')||0) +'</td><td>'+ (g(r,'hbMood')||'') +'</td>';
  tbody.appendChild(tr);
});
</script>
</body></html>`,
		summary.Total, summary.AvgShinka, summary.AvgHyoka, summary.TopActor, summary.MaxHyoka, rowsJSON)
}

func kashikaPct(n, total int) float64 {
	if total == 0 {
		return 0
	}
	return float64(n) * 100 / float64(total)
}

func kashikaGraphviz(format, dotSrc string) ([]byte, error) {
	if _, err := exec.LookPath("dot"); err != nil {
		return nil, fmt.Errorf("graphviz 'dot' not found in PATH")
	}
	cmd := exec.Command("dot", "-T"+format)
	cmd.Stdin = strings.NewReader(dotSrc)
	out, err := cmd.Output()
	if err != nil {
		if ee, ok := err.(*exec.ExitError); ok {
			return nil, fmt.Errorf("dot -T%s failed: %s", format, strings.TrimSpace(string(ee.Stderr)))
		}
		return nil, fmt.Errorf("dot -T%s failed: %w", format, err)
	}
	return out, nil
}

func kashikaWriteOutput(path string, data []byte) error {
	if path == "" {
		_, err := os.Stdout.Write(data)
		return err
	}
	return os.WriteFile(path, data, 0644)
}

// --- terminal format ---

func runKashikaTerminal(args []string) error {
	_, source, input, err := kashikaParseInput(args)
	if err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	data, err := kashikaReadInput(*input)
	if err != nil {
		return fmt.Errorf("read input: %w", err)
	}

	switch *source {
	case "haisen":
		g, err := kashikaParseHaisen(data)
		if err != nil {
			return fmt.Errorf("parse haisen: %w", err)
		}
		kashikaTerminalHaisen(g)
	case "sos":
		r, err := kashikaParseSoS(data)
		if err != nil {
			return fmt.Errorf("parse sos: %w", err)
		}
		kashikaTerminalSoS(r)
	default:
		return fmt.Errorf("unknown source: %s", *source)
	}
	return nil
}

func kashikaTerminalHaisen(g haisenGraph) {
	w := 60
	line := strings.Repeat("─", w-2)
	fmt.Printf("┌%s┐\n", line)
	fmt.Printf("│ %-*s│\n", w-3, fmt.Sprintf("GFTD Wiring (配線図) — %d apps, %d edges", g.Stats.TotalApps, g.Stats.TotalEdges))
	fmt.Printf("├%s┤\n", line)

	fmt.Printf("│ %-*s│\n", w-3, fmt.Sprintf("invoke: %d  writes: %d  reads: %d  subscribe: %d",
		g.Stats.InvokeEdges, g.Stats.WriteEdges, g.Stats.ReadEdges, g.Stats.SubscribeEdges))
	fmt.Printf("│ %-*s│\n", w-3, fmt.Sprintf("orphans: %d", g.Stats.Orphans))
	fmt.Printf("├%s┤\n", line)

	// Group edges by from
	byFrom := make(map[string][]haisenEdge)
	for _, e := range g.Edges {
		byFrom[e.From] = append(byFrom[e.From], e)
	}

	// Show top 20 most connected apps
	type appEdges struct {
		nanoid string
		count  int
	}
	var ranked []appEdges
	for k, v := range byFrom {
		ranked = append(ranked, appEdges{k, len(v)})
	}
	sort.Slice(ranked, func(i, j int) bool { return ranked[i].count > ranked[j].count })
	if len(ranked) > 20 {
		ranked = ranked[:20]
	}

	for _, ae := range ranked {
		edges := byFrom[ae.nanoid]
		first := edges[0]
		fmt.Printf("│ %-8s ──%s──> %-*s│\n", ae.nanoid, first.EdgeType, w-26-len(first.EdgeType), first.To)
		for i := 1; i < len(edges) && i < 3; i++ {
			fmt.Printf("│ %8s ──%s──> %-*s│\n", "", edges[i].EdgeType, w-26-len(edges[i].EdgeType), edges[i].To)
		}
		if len(edges) > 3 {
			fmt.Printf("│ %8s   ... +%d more %-*s│\n", "", len(edges)-3, w-28, "")
		}
	}

	fmt.Printf("└%s┘\n", line)
}

func kashikaTerminalSoS(r sosReport) {
	w := 64
	line := strings.Repeat("─", w-2)
	fmt.Printf("┌%s┐\n", line)
	fmt.Printf("│ %-*s│\n", w-3, kashikaFit(fmt.Sprintf("GFTD System-of-Systems — %d systems, %d interfaces",
		r.Stats.TotalSystems, r.Stats.TotalInterfaces), w-3))
	fmt.Printf("├%s┤\n", line)
	fmt.Printf("│ %-*s│\n", w-3, kashikaFit(fmt.Sprintf("apps: %d  deployed: %d  orphans: %d",
		r.Stats.TotalApps, r.Stats.DeployedApps, r.Stats.OrphanApps), w-3))
	fmt.Printf("│ %-*s│\n", w-3, kashikaFit(fmt.Sprintf("projects: %d  repo-systems: %d",
		r.Stats.ProjectSystems, r.Stats.RepoSystems), w-3))
	fmt.Printf("│ %-*s│\n", w-3, kashikaFit(fmt.Sprintf("pkg.json: %d  workflows: %d  dockerfiles: %d",
		r.Stats.PackageJSONCount, r.Stats.WorkflowCount, r.Stats.DockerfileCount), w-3))
	fmt.Printf("│ %-*s│\n", w-3, kashikaFit(fmt.Sprintf("coupling: %.1f  cohesion: %.1f",
		r.Stats.CouplingScore, r.Stats.CohesionScore), w-3))
	fmt.Printf("├%s┤\n", line)

	for _, layer := range r.Layers {
		names := layer.Systems
		if len(names) > 6 {
			names = append(append([]string{}, names[:6]...), fmt.Sprintf("...+%d more", len(layer.Systems)-6))
		}
		text := fmt.Sprintf("[%s] %s", layer.Name, strings.Join(names, ", "))
		fmt.Printf("│ %-*s│\n", w-3, kashikaFit(text, w-3))
	}
	fmt.Printf("├%s┤\n", line)

	for i, iface := range r.Interfaces {
		if i >= 24 {
			fmt.Printf("│ %-*s│\n", w-3, kashikaFit(fmt.Sprintf("... +%d more interfaces", len(r.Interfaces)-i), w-3))
			break
		}
		text := fmt.Sprintf("%s ──%s──> %s", iface.From, iface.Protocol, iface.To)
		fmt.Printf("│ %-*s│\n", w-3, kashikaFit(text, w-3))
	}

	fmt.Printf("└%s┘\n", line)
}

// --- dot format ---

func runKashikaDot(args []string) error {
	_, source, input, err := kashikaParseInput(args)
	if err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	data, err := kashikaReadInput(*input)
	if err != nil {
		return fmt.Errorf("read input: %w", err)
	}

	switch *source {
	case "haisen":
		g, err := kashikaParseHaisen(data)
		if err != nil {
			return fmt.Errorf("parse haisen: %w", err)
		}
		fmt.Print(kashikaDotHaisen(g))
	case "sos":
		r, err := kashikaParseSoS(data)
		if err != nil {
			return fmt.Errorf("parse sos: %w", err)
		}
		fmt.Print(kashikaDotSoS(r))
	default:
		return fmt.Errorf("unknown source: %s", *source)
	}
	return nil
}

func kashikaDotHaisen(g haisenGraph) string {
	var b strings.Builder
	b.WriteString("digraph haisen {\n")
	b.WriteString("  rankdir=LR;\n")
	b.WriteString("  node [shape=box, fontsize=10, style=rounded];\n")
	b.WriteString("  edge [fontsize=8];\n\n")

	// Group apps by project
	byProject := make(map[string][]haisenApp)
	for _, app := range g.Apps {
		p := app.Project
		if p == "" {
			p = "_unowned"
		}
		byProject[p] = append(byProject[p], app)
	}

	idx := 0
	for project, apps := range byProject {
		b.WriteString(fmt.Sprintf("  subgraph cluster_%d {\n", idx))
		b.WriteString(fmt.Sprintf("    label=%q;\n", project))
		b.WriteString("    style=dashed; color=gray;\n")
		for _, app := range apps {
			id := sgDotSafe(app.Nanoid)
			label := app.Name
			if label == "" {
				label = app.Nanoid
			}
			b.WriteString(fmt.Sprintf("    %s [label=%q];\n", id, label))
		}
		b.WriteString("  }\n\n")
		idx++
	}

	// Infra nodes
	if len(g.Infra) > 0 {
		b.WriteString(fmt.Sprintf("  subgraph cluster_%d {\n", idx))
		b.WriteString("    label=\"infra\";\n")
		b.WriteString("    style=filled; fillcolor=\"#f0f0f0\";\n")
		for _, infra := range g.Infra {
			id := sgDotSafe(infra.Name)
			b.WriteString(fmt.Sprintf("    %s [label=%q, shape=component];\n", id, infra.Name))
		}
		b.WriteString("  }\n\n")
	}

	// Edge colors by type
	edgeColors := map[string]string{
		"invoke":    "red",
		"writes":    "blue",
		"reads":     "green",
		"subscribe": "orange",
		"follow":    "purple",
	}

	for _, e := range g.Edges {
		fromID := sgDotSafe(e.From)
		toID := sgDotSafe(e.To)
		color := edgeColors[e.EdgeType]
		if color == "" {
			color = "black"
		}
		b.WriteString(fmt.Sprintf("  %s -> %s [label=%q, color=%s];\n", fromID, toID, e.EdgeType, color))
	}

	b.WriteString("}\n")
	return b.String()
}

func kashikaDotSoS(r sosReport) string {
	var b strings.Builder
	b.WriteString("digraph sos {\n")
	b.WriteString("  rankdir=TB;\n")
	b.WriteString("  node [shape=box3d, fontsize=11, style=filled];\n")
	b.WriteString("  edge [fontsize=9];\n\n")

	layerColors := map[string]string{
		"control":    "#FFE6CC",
		"runtime":    "#D9EAF7",
		"infra":      "#E0E0FF",
		"app":        "#E0FFE0",
		"operations": "#F5E0FF",
		"data":       "#FFFFC0",
	}
	systemByID := make(map[string]sosSystem)
	for _, system := range r.Systems {
		systemByID[system.ID] = system
	}

	for i, layer := range r.Layers {
		b.WriteString(fmt.Sprintf("  subgraph cluster_%d {\n", i))
		b.WriteString(fmt.Sprintf("    label=%q;\n", "Layer: "+layer.Name))
		color := layerColors[layer.Name]
		if color == "" {
			color = "#F0F0F0"
		}
		b.WriteString(fmt.Sprintf("    style=filled; fillcolor=%q;\n", color))
		for _, sys := range layer.Systems {
			id := sgDotSafe(sys)
			label := sys
			if system, ok := systemByID[sys]; ok {
				label = kashikaSoSLabel(system)
			}
			b.WriteString(fmt.Sprintf("    %s [label=%q];\n", id, label))
		}
		b.WriteString("  }\n\n")
	}

	for _, iface := range r.Interfaces {
		fromID := sgDotSafe(iface.From)
		toID := sgDotSafe(iface.To)
		label := fmt.Sprintf("%s (%d)", iface.Protocol, iface.EdgeCount)
		b.WriteString(fmt.Sprintf("  %s -> %s [label=%q];\n", fromID, toID, label))
	}

	b.WriteString("}\n")
	return b.String()
}

// --- mermaid format ---

func runKashikaMermaid(args []string) error {
	_, source, input, err := kashikaParseInput(args)
	if err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	data, err := kashikaReadInput(*input)
	if err != nil {
		return fmt.Errorf("read input: %w", err)
	}

	switch *source {
	case "haisen":
		g, err := kashikaParseHaisen(data)
		if err != nil {
			return fmt.Errorf("parse haisen: %w", err)
		}
		fmt.Print(kashikaMermaidHaisen(g))
	case "sos":
		r, err := kashikaParseSoS(data)
		if err != nil {
			return fmt.Errorf("parse sos: %w", err)
		}
		fmt.Print(kashikaMermaidSoS(r))
	default:
		return fmt.Errorf("unknown source: %s", *source)
	}
	return nil
}

func mermaidSafe(s string) string {
	r := strings.NewReplacer(
		" ", "_", ".", "_", ":", "_", "#", "_", "-", "_",
		"/", "_", "@", "_", "(", "", ")", "",
	)
	return r.Replace(s)
}

func kashikaMermaidHaisen(g haisenGraph) string {
	var b strings.Builder
	b.WriteString("graph LR\n")

	// Group by project
	byProject := make(map[string][]haisenApp)
	for _, app := range g.Apps {
		p := app.Project
		if p == "" {
			p = "unowned"
		}
		byProject[p] = append(byProject[p], app)
	}

	for project, apps := range byProject {
		b.WriteString(fmt.Sprintf("  subgraph %s\n", mermaidSafe(project)))
		for _, app := range apps {
			label := app.Name
			if label == "" {
				label = app.Nanoid
			}
			b.WriteString(fmt.Sprintf("    %s[\"%s\"]\n", mermaidSafe(app.Nanoid), label))
		}
		b.WriteString("  end\n")
	}

	// Limit edges for readability (top 100)
	edges := g.Edges
	if len(edges) > 100 {
		edges = edges[:100]
	}

	for _, e := range edges {
		from := mermaidSafe(e.From)
		to := mermaidSafe(e.To)
		b.WriteString(fmt.Sprintf("  %s -->|%s| %s\n", from, e.EdgeType, to))
	}

	return b.String()
}

func kashikaMermaidSoS(r sosReport) string {
	var b strings.Builder
	b.WriteString("graph TB\n")
	systemByID := make(map[string]sosSystem)
	for _, system := range r.Systems {
		systemByID[system.ID] = system
	}

	for _, layer := range r.Layers {
		b.WriteString(fmt.Sprintf("  subgraph %s\n", mermaidSafe(layer.Name)))
		for _, sys := range layer.Systems {
			label := sys
			if system, ok := systemByID[sys]; ok {
				label = kashikaSoSLabel(system)
			}
			b.WriteString(fmt.Sprintf("    %s[\"%s\"]\n", mermaidSafe(sys), label))
		}
		b.WriteString("  end\n")
	}

	for _, iface := range r.Interfaces {
		from := mermaidSafe(iface.From)
		to := mermaidSafe(iface.To)
		b.WriteString(fmt.Sprintf("  %s -->|%s| %s\n", from, iface.Protocol, to))
	}

	return b.String()
}

func kashikaSoSLabel(system sosSystem) string {
	label := system.ID
	if system.Name != "" && system.Name != system.ID {
		label = system.Name
	}
	var lines []string
	lines = append(lines, label)
	meta := system.SystemType
	if system.Layer != "" && system.Layer != system.SystemType {
		meta = system.Layer + " / " + system.SystemType
	}
	if meta != "" {
		lines = append(lines, meta)
	}
	if system.AppCount > 0 || system.Deployed > 0 {
		lines = append(lines, fmt.Sprintf("apps=%d deployed=%d", system.AppCount, system.Deployed))
	}
	return strings.Join(lines, "\n")
}

func kashikaFit(s string, width int) string {
	if len(s) <= width {
		return s
	}
	if width <= 3 {
		return s[:width]
	}
	return s[:width-3] + "..."
}

// --- html format ---

func runKashikaHTML(args []string) error {
	_, source, input, err := kashikaParseInput(args)
	if err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	data, err := kashikaReadInput(*input)
	if err != nil {
		return fmt.Errorf("read input: %w", err)
	}

	switch *source {
	case "haisen":
		g, err := kashikaParseHaisen(data)
		if err != nil {
			return fmt.Errorf("parse haisen: %w", err)
		}
		fmt.Print(kashikaHTMLForceGraph(g))
	case "sos":
		r, err := kashikaParseSoS(data)
		if err != nil {
			return fmt.Errorf("parse sos: %w", err)
		}
		fmt.Print(kashikaHTMLSoS(r))
	default:
		return fmt.Errorf("unknown source: %s", *source)
	}
	return nil
}

func kashikaHTMLForceGraph(g haisenGraph) string {
	dataJSON, _ := json.Marshal(g)

	// kami-web WASM (WebGPU → WebGL2 fallback) renders graph.
	// Requires kami_web.js + kami_web_bg.wasm in same directory.
	return fmt.Sprintf(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GFTD Wiring (配線図)</title>
<style>body{margin:0;overflow:hidden;background:#0d1117}canvas{display:block;width:100vw;height:100vh}
#s{position:fixed;top:8px;left:8px;color:#eee;font:13px system-ui;background:rgba(0,0,0,0.7);padding:8px 14px;border-radius:6px;z-index:10}</style>
</head><body>
<div id="s">Loading kami-engine WASM...</div>
<canvas id="gc"></canvas>
<script type="module">
import init,{run_with_graph} from "./kami_web.js";
const s=document.getElementById("s");
try{
  s.textContent="Initializing WebGPU...";
  await init();
  s.textContent="Rendering...";
  await run_with_graph("gc",JSON.stringify(%s),"haisen");
  s.textContent="GFTD Wiring — kami-engine | WASD: pan | Space/Shift: zoom";
}catch(e){s.textContent="Error: "+e.message;console.error(e)}
</script></body></html>`, string(dataJSON))
}

func kashikaHTMLSoS(r sosReport) string {
	dataJSON, _ := json.Marshal(r)

	return fmt.Sprintf(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>GFTD System-of-Systems</title>
<style>
:root{
  --bg:#0b1020;
  --panel:#111932;
  --panel2:#0f1730;
  --text:#e6ecff;
  --muted:#91a0c7;
  --line:#26345f;
  --control:#ffb86b;
  --runtime:#78c7ff;
  --infra:#9ea8ff;
  --app:#7ae7a1;
  --operations:#df9cff;
  --data:#f0dc78;
}
*{box-sizing:border-box}
body{margin:0;background:radial-gradient(circle at top,#162349 0,#0b1020 50%%,#070b15 100%%);color:var(--text);font:14px/1.4 system-ui,sans-serif}
.shell{display:grid;grid-template-columns:320px 1fr;min-height:100vh}
.sidebar{padding:18px;border-right:1px solid var(--line);background:linear-gradient(180deg,rgba(17,25,50,.96),rgba(10,16,31,.96))}
.content{position:relative;overflow:auto}
h1{font-size:20px;margin:0 0 8px}
h2{font-size:13px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin:22px 0 10px}
.meta,.legend,.layers,.toplist{display:grid;gap:8px}
.card{background:rgba(255,255,255,.03);border:1px solid var(--line);border-radius:12px;padding:10px 12px}
.stat{display:flex;justify-content:space-between;gap:12px}
.stat b{font-size:18px}
.legend-item{display:flex;align-items:center;gap:10px}
.swatch{width:12px;height:12px;border-radius:999px;display:inline-block}
.layer-pill{display:inline-flex;align-items:center;gap:8px;border:1px solid var(--line);border-radius:999px;padding:5px 10px;background:rgba(255,255,255,.02)}
.topitem{display:flex;justify-content:space-between;gap:8px;font-size:13px}
.canvas-wrap{padding:18px}
.toolbar{position:sticky;top:0;z-index:5;display:flex;gap:12px;align-items:center;justify-content:space-between;margin-bottom:12px;padding:12px 14px;background:rgba(11,16,32,.88);backdrop-filter:blur(10px);border:1px solid var(--line);border-radius:14px}
.toolbar input{width:280px;max-width:100%%;padding:10px 12px;border-radius:10px;border:1px solid var(--line);background:var(--panel2);color:var(--text)}
.graph{display:grid;gap:14px}
.system{border:1px solid var(--line);border-radius:16px;padding:14px;background:linear-gradient(180deg,rgba(255,255,255,.03),rgba(255,255,255,.01))}
.system header{display:flex;justify-content:space-between;gap:12px;align-items:flex-start;margin-bottom:10px}
.system h3{margin:0;font-size:17px}
.system small{color:var(--muted)}
.badge{display:inline-block;border-radius:999px;padding:4px 8px;font-size:12px;font-weight:600}
.meta-line{color:var(--muted);font-size:12px;margin-top:6px}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}
.chip{padding:4px 8px;border-radius:999px;background:rgba(255,255,255,.04);border:1px solid var(--line);font-size:12px}
.ifaces{margin-top:12px;border-top:1px solid var(--line);padding-top:12px;display:grid;gap:8px}
.iface{display:flex;justify-content:space-between;gap:10px;font-size:13px}
.iface span:last-child{color:var(--muted);text-align:right}
.empty{padding:24px;border:1px dashed var(--line);border-radius:16px;color:var(--muted);text-align:center}
@media (max-width: 960px){
  .shell{grid-template-columns:1fr}
  .sidebar{border-right:0;border-bottom:1px solid var(--line)}
  .toolbar{position:static}
}
</style>
</head><body>
<div class="shell">
  <aside class="sidebar">
    <h1>GFTD System-of-Systems</h1>
    <div class="meta">
      <div class="card stat"><span>Systems</span><b id="stat-systems">0</b></div>
      <div class="card stat"><span>Interfaces</span><b id="stat-interfaces">0</b></div>
      <div class="card stat"><span>Apps</span><b id="stat-apps">0</b></div>
      <div class="card stat"><span>Workflows</span><b id="stat-workflows">0</b></div>
    </div>
    <h2>Layers</h2>
    <div class="layers" id="layers"></div>
    <h2>Legend</h2>
    <div class="legend">
      <div class="legend-item"><span class="swatch" style="background:var(--control)"></span><span>Control</span></div>
      <div class="legend-item"><span class="swatch" style="background:var(--runtime)"></span><span>Runtime</span></div>
      <div class="legend-item"><span class="swatch" style="background:var(--infra)"></span><span>Infra</span></div>
      <div class="legend-item"><span class="swatch" style="background:var(--app)"></span><span>App</span></div>
      <div class="legend-item"><span class="swatch" style="background:var(--operations)"></span><span>Operations</span></div>
      <div class="legend-item"><span class="swatch" style="background:var(--data)"></span><span>Data</span></div>
    </div>
    <h2>Top Interfaces</h2>
    <div class="toplist card" id="top-interfaces"></div>
  </aside>
  <main class="content">
    <div class="canvas-wrap">
      <div class="toolbar">
        <div>
          <div><strong>Generated:</strong> <span id="generated-at"></span></div>
          <div class="meta-line">repo-wide infra / runtime / deps / ops / project systems</div>
        </div>
        <input id="search" type="search" placeholder="Filter by system id, path, technology, protocol">
      </div>
      <div class="graph" id="graph"></div>
    </div>
  </main>
</div>
<script>
const report = %s;
const colorMap = {
  control: "var(--control)",
  runtime: "var(--runtime)",
  infra: "var(--infra)",
  app: "var(--app)",
  operations: "var(--operations)",
  data: "var(--data)"
};
const systems = report.systems || [];
const interfaces = report.interfaces || [];
const byFrom = new Map();
for (const iface of interfaces) {
  if (!byFrom.has(iface.from)) byFrom.set(iface.from, []);
  byFrom.get(iface.from).push(iface);
}
for (const list of byFrom.values()) list.sort((a,b) => b.edge_count - a.edge_count);

document.getElementById("generated-at").textContent = report.generated_at || "";
document.getElementById("stat-systems").textContent = report.stats.total_systems;
document.getElementById("stat-interfaces").textContent = report.stats.total_interfaces;
document.getElementById("stat-apps").textContent = report.stats.total_apps;
document.getElementById("stat-workflows").textContent = report.stats.workflow_count;

const layersEl = document.getElementById("layers");
for (const layer of report.layers || []) {
  const div = document.createElement("div");
  div.className = "layer-pill";
  div.innerHTML = '<span class="swatch" style="background:'+ (colorMap[layer.name] || "var(--muted)") +'"></span><span>'+layer.name+'</span><small>'+layer.systems.length+'</small>';
  layersEl.appendChild(div);
}

const topIfaces = document.getElementById("top-interfaces");
for (const iface of interfaces.slice(0, 12)) {
  const row = document.createElement("div");
  row.className = "topitem";
  row.innerHTML = '<span>'+iface.from+' → '+iface.to+'</span><span>'+iface.protocol+' · '+iface.edge_count+'</span>';
  topIfaces.appendChild(row);
}

const graphEl = document.getElementById("graph");
const searchEl = document.getElementById("search");

function systemMatches(system, q) {
  if (!q) return true;
  const hay = [
    system.id, system.name, system.path, system.system_type, system.layer,
    ...(system.technologies || []),
    ...(system.signals || []),
    ...(Object.keys(system.version_hints || {})),
    ...(Object.values(system.version_hints || {}))
  ].filter(Boolean).join(" ").toLowerCase();
  const ifaceHay = (byFrom.get(system.id) || []).slice(0, 8).map(iface => [iface.to, iface.protocol, iface.description].filter(Boolean).join(" ")).join(" ").toLowerCase();
  return hay.includes(q) || ifaceHay.includes(q);
}

function render() {
  const q = searchEl.value.trim().toLowerCase();
  graphEl.textContent = "";
  const filtered = systems.filter(system => systemMatches(system, q));
  if (filtered.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No systems matched the current filter.";
    graphEl.appendChild(empty);
    return;
  }
  for (const system of filtered) {
    const card = document.createElement("section");
    card.className = "system";
    const color = colorMap[system.layer] || "var(--muted)";
    const outgoing = (byFrom.get(system.id) || []).slice(0, 10);
    const techs = system.technologies || [];
    const versions = system.version_hints ? Object.entries(system.version_hints) : [];
    const title = system.name || system.id;
    const metaPath = system.path ? " · " + system.path : "";
    const badge = system.layer || system.system_type;
    const techHTML = techs.length ? '<div class="chips">'+techs.map(t => '<span class="chip">'+t+'</span>').join("")+'</div>' : "";
    const versionHTML = versions.length ? '<div class="chips">'+versions.map(([k,v]) => '<span class="chip">'+k+': '+v+'</span>').join("")+'</div>' : "";
    const ifaceHTML = outgoing.length ? outgoing.map(iface => '<div class="iface"><span>'+iface.from+' → '+iface.to+'</span><span>'+iface.protocol+' · '+iface.edge_count+(iface.description ? '<br>'+iface.description : '')+'</span></div>').join("") : '<div class="meta-line">No outgoing interfaces recorded.</div>';
    card.innerHTML =
      '<header>' +
        '<div>' +
          '<h3>' + title + '</h3>' +
          '<div class="meta-line">' + system.id + metaPath + '</div>' +
        '</div>' +
        '<span class="badge" style="background:' + color + ';color:#08111f">' + badge + '</span>' +
      '</header>' +
      '<div class="meta-line">type=' + system.system_type + ' · apps=' + system.app_count + ' · deployed=' + system.deployed + ' · edges=' + system.edge_count + '</div>' +
      techHTML +
      versionHTML +
      '<div class="ifaces">' + ifaceHTML + '</div>';
    graphEl.appendChild(card);
  }
}

searchEl.addEventListener("input", render);
render();
</script></body></html>`, string(dataJSON))
}

// ════════════════════════════════════════════════════════════════════════════
// kashika sla — 99.999% SLA Design Analysis
// ════════════════════════════════════════════════════════════════════════════

// slaComponent models one infrastructure component for SLA analysis.
type slaComponent struct {
	Name          string   `json:"name"`
	Layer         string   `json:"layer"`          // edge / gateway / data / compute / storage
	AvailSLA      float64  `json:"avail_sla"`      // provider SLA (e.g. 0.9999)
	DurabilitySLA float64  `json:"durability_sla"` // data durability (e.g. 0.99999999999)
	Redundancy    int      `json:"redundancy"`     // N replicas (1 = no redundancy)
	FailoverSec   float64  `json:"failover_sec"`   // failover time in seconds
	ColdStartSec  float64  `json:"cold_start_sec"` // cold start latency
	SinglePoint   bool     `json:"single_point"`   // true = SPOF
	WriteAuth     bool     `json:"write_auth"`     // participates in write path
	ReadAuth      bool     `json:"read_auth"`      // participates in read path
	Issues        []string `json:"issues"`
	Mitigations   []string `json:"mitigations"`
}

// slaPath models one request path (write or read) as a chain of components.
type slaPath struct {
	Name       string   `json:"name"`
	Components []string `json:"components"` // component names in order
	Composite  float64  `json:"composite"`  // computed composite availability
}

// slaReport is the full SLA analysis output.
type slaReport struct {
	Target          float64        `json:"target_sla"`
	TargetLabel     string         `json:"target_label"`
	DowntimePerYear string         `json:"downtime_per_year"`
	Components      []slaComponent `json:"components"`
	WritePath       slaPath        `json:"write_path"`
	ReadPathKV      slaPath        `json:"read_path_kv"`
	ReadPathSql  slaPath        `json:"read_path_sql"`
	TimelinePath    slaPath        `json:"timeline_path"`
	OverallWrite    float64        `json:"overall_write"`
	OverallRead     float64        `json:"overall_read"`
	NSIDs           []slaNSID      `json:"nsids"`
	Issues          []slaIssue     `json:"issues"`
	Phases          []slaPhase     `json:"phases"`
}

type slaIssue struct {
	Severity  string `json:"severity"` // critical / high / medium / low
	Component string `json:"component"`
	Issue     string `json:"issue"`
	Impact    string `json:"impact"`
	Fix       string `json:"fix"`
	Phase     string `json:"phase"` // P0/P1/P2/P3
}

type slaPhase struct {
	Phase    string   `json:"phase"`
	Target   string   `json:"target"`
	Downtime string   `json:"downtime"`
	Changes  []string `json:"changes"`
	Cost     string   `json:"cost"`
	Timeline string   `json:"timeline"`
}

type slaNSID struct {
	NSID      string  `json:"nsid"`
	Category  string  `json:"category"`
	DataPath  string  `json:"data_path"`
	Tier      string  `json:"tier"`       // instant/interactive/tolerable/background
	P50Target float64 `json:"p50_target"` // ms
	P99Target float64 `json:"p99_target"` // ms
	P50Actual float64 `json:"p50_actual"` // ms (measured, 0=unknown)
	Status    string  `json:"status"`     // met/gap/unknown
}

func runKashikaSLA(args []string) error {
	fs := flag.NewFlagSet("kashika sla", flag.ContinueOnError)
	asJSON := fs.Bool("json", false, "emit JSON")
	asSVG := fs.Bool("svg", false, "generate SVG and open")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	report := buildSLAReport()

	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	if *asSVG {
		return generateAndOpenSLASVG(report)
	}

	printSLAReport(report)
	return nil
}

func generateAndOpenSLASVG(r slaReport) error {
	svg := buildSLASVG(r)
	tmpFile := os.TempDir() + "/gftd-sla-analysis.svg"
	if err := os.WriteFile(tmpFile, []byte(svg), 0644); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "SVG written to %s\n", tmpFile)
	cmd := exec.Command("open", tmpFile)
	return cmd.Run()
}

func buildSLASVG(r slaReport) string {
	var b strings.Builder

	w := 1200
	h := 2600

	b.WriteString(fmt.Sprintf(`<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 %d %d" width="%d" height="%d">
<defs>
  <style>
    text { font-family: 'SF Mono', 'Menlo', 'Consolas', monospace; }
    .title { font-size: 22px; font-weight: bold; fill: #e0e0ff; }
    .subtitle { font-size: 14px; fill: #a0a0c0; }
    .header { font-size: 13px; font-weight: bold; fill: #c0c0e0; }
    .label { font-size: 11px; fill: #b0b0d0; }
    .value { font-size: 11px; fill: #e0e0ff; }
    .grade-s { fill: #00ff88; font-weight: bold; }
    .grade-a { fill: #88ff00; }
    .grade-b { fill: #ffcc00; }
    .grade-c { fill: #ff8800; }
    .grade-d { fill: #ff4444; }
    .critical { fill: #ff4444; font-weight: bold; }
    .high { fill: #ff8844; }
    .medium { fill: #ffcc44; }
    .low { fill: #88aacc; }
    .spof { fill: #ff4444; font-size: 12px; font-weight: bold; }
    .bar-fill { fill: #4488ff; }
    .bar-bg { fill: #1a1a3a; }
    .bar-target { fill: #00ff88; opacity: 0.3; }
    .phase-box { rx: 6; ry: 6; }
    .path-line { stroke: #4488ff; stroke-width: 2; fill: none; marker-end: url(#arrow); }
    .path-line-degraded { stroke: #ff8844; stroke-width: 2; fill: none; stroke-dasharray: 6,3; marker-end: url(#arrow-warn); }
  </style>
  <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#4488ff"/>
  </marker>
  <marker id="arrow-warn" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="#ff8844"/>
  </marker>
</defs>
<rect width="%d" height="%d" fill="#0b1020" rx="12"/>
`, w, h, w, h, w, h))

	y := 50
	// Title
	b.WriteString(fmt.Sprintf(`<text x="600" y="%d" text-anchor="middle" class="title">GFTD Platform SLA Analysis</text>`, y))
	y += 28
	b.WriteString(fmt.Sprintf(`<text x="600" y="%d" text-anchor="middle" class="subtitle">Target: %s — Max downtime: %s/year</text>`, y, r.TargetLabel, r.DowntimePerYear))
	y += 40

	// ── Component boxes ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">Infrastructure Components</text>`, y))
	y += 20

	for _, c := range r.Components {
		effectiveAvail := c.AvailSLA
		if c.Redundancy > 1 {
			fail := 1.0
			for i := 0; i < c.Redundancy; i++ {
				fail *= (1 - c.AvailSLA)
			}
			effectiveAvail = 1 - fail
		}
		grade := slaGrade(effectiveAvail)
		gradeClass := "grade-" + strings.ToLower(grade)

		// Box
		boxColor := "#1a2040"
		borderColor := "#2a3060"
		if c.SinglePoint {
			borderColor = "#ff4444"
		}
		b.WriteString(fmt.Sprintf(`<rect x="40" y="%d" width="1120" height="36" fill="%s" stroke="%s" rx="4"/>`, y, boxColor, borderColor))

		// Name
		b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="value">%s</text>`, y+23, escSVG(c.Name)))
		// SLA
		b.WriteString(fmt.Sprintf(`<text x="380" y="%d" class="value">%s</text>`, y+23, slaPercent(effectiveAvail)))
		// Grade
		b.WriteString(fmt.Sprintf(`<text x="520" y="%d" class="%s">%s</text>`, y+23, gradeClass, grade))
		// Redundancy
		b.WriteString(fmt.Sprintf(`<text x="580" y="%d" class="value">%dx</text>`, y+23, c.Redundancy))
		// SPOF
		if c.SinglePoint {
			b.WriteString(fmt.Sprintf(`<text x="640" y="%d" class="spof">SPOF</text>`, y+23))
		}
		// Downtime
		b.WriteString(fmt.Sprintf(`<text x="710" y="%d" class="label">%s</text>`, y+23, slaDowntime(effectiveAvail)))
		// Layer
		b.WriteString(fmt.Sprintf(`<text x="880" y="%d" class="label">%s</text>`, y+23, c.Layer))
		// Role
		role := ""
		if c.WriteAuth {
			role += "W"
		}
		if c.ReadAuth {
			role += "R"
		}
		if role == "" {
			role = "—"
		}
		b.WriteString(fmt.Sprintf(`<text x="960" y="%d" class="label">%s</text>`, y+23, role))

		y += 40
	}
	y += 20

	// ── Request Path Diagram ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">Request Path Composite Availability</text>`, y))
	y += 25

	paths := []slaPath{r.WritePath, r.ReadPathKV, r.ReadPathSql, r.TimelinePath}
	for _, p := range paths {
		grade := slaGrade(p.Composite)
		gradeClass := "grade-" + strings.ToLower(grade)
		b.WriteString(fmt.Sprintf(`<rect x="40" y="%d" width="1120" height="32" fill="#1a2040" stroke="#2a3060" rx="4"/>`, y))
		b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="value">%s</text>`, y+21, escSVG(p.Name)))
		b.WriteString(fmt.Sprintf(`<text x="520" y="%d" class="%s">%s  %s</text>`, y+21, gradeClass, slaPercent(p.Composite), grade))
		b.WriteString(fmt.Sprintf(`<text x="710" y="%d" class="label">%s</text>`, y+21, slaDowntime(p.Composite)))

		// Availability bar (99.90% → 100% scaled to 200px)
		pct := p.Composite * 100
		barW := (pct - 99.90) / (100.0 - 99.90) * 200
		if barW < 0 {
			barW = 0
		}
		if barW > 200 {
			barW = 200
		}
		b.WriteString(fmt.Sprintf(`<rect x="900" y="%d" width="200" height="14" class="bar-bg" rx="3"/>`, y+8))
		b.WriteString(fmt.Sprintf(`<rect x="900" y="%d" width="%.0f" height="14" class="bar-fill" rx="3"/>`, y+8, barW))
		// Target line
		targetW := (99.999 - 99.90) / (100.0 - 99.90) * 200
		b.WriteString(fmt.Sprintf(`<line x1="%.0f" y1="%d" x2="%.0f" y2="%d" stroke="#00ff88" stroke-width="2" stroke-dasharray="3,2"/>`, 900+targetW, y+6, 900+targetW, y+24))

		y += 36
	}
	y += 20

	// ── Write Path Flow ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">Write Path Flow</text>`, y))
	y += 30
	writeNodes := []struct {
		name string
		x    int
	}{
		{"Client", 80}, {"Dispatcher", 270}, {"PDS Worker", 480}, {"KV (await)", 690}, {"yata (async)", 920},
	}
	for _, n := range writeNodes {
		fill := "#1a3050"
		if n.name == "yata (async)" {
			fill = "#2a2040"
		}
		b.WriteString(fmt.Sprintf(`<rect x="%d" y="%d" width="150" height="36" fill="%s" stroke="#4488ff" rx="6"/>`, n.x, y, fill))
		b.WriteString(fmt.Sprintf(`<text x="%d" y="%d" text-anchor="middle" class="value">%s</text>`, n.x+75, y+23, n.name))
	}
	// Arrows
	for i := 0; i < len(writeNodes)-1; i++ {
		x1 := writeNodes[i].x + 150
		x2 := writeNodes[i+1].x
		cls := "path-line"
		if writeNodes[i+1].name == "yata (async)" {
			cls = "path-line-degraded"
		}
		b.WriteString(fmt.Sprintf(`<line x1="%d" y1="%d" x2="%d" y2="%d" class="%s"/>`, x1, y+18, x2, y+18, cls))
	}
	y += 55

	// ── NSID p99 SLA ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">NSID-Level p99 SLA (%d endpoints)</text>`, y, len(r.NSIDs)))
	y += 18
	// Column headers
	b.WriteString(fmt.Sprintf(`<rect x="40" y="%d" width="1120" height="20" fill="#1a2040"/>`, y))
	b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="label" font-size="9">NSID</text>`, y+14))
	b.WriteString(fmt.Sprintf(`<text x="480" y="%d" class="label" font-size="9">Tier</text>`, y+14))
	b.WriteString(fmt.Sprintf(`<text x="580" y="%d" class="label" font-size="9">p50 Target</text>`, y+14))
	b.WriteString(fmt.Sprintf(`<text x="670" y="%d" class="label" font-size="9">p99 Target</text>`, y+14))
	b.WriteString(fmt.Sprintf(`<text x="760" y="%d" class="label" font-size="9">p50 Actual</text>`, y+14))
	b.WriteString(fmt.Sprintf(`<text x="860" y="%d" class="label" font-size="9">Status</text>`, y+14))
	y += 22
	for _, n := range r.NSIDs {
		bgColor := "#0d1225"
		if n.Status == "gap" {
			bgColor = "#2a1020"
		}
		b.WriteString(fmt.Sprintf(`<rect x="40" y="%d" width="1120" height="18" fill="%s"/>`, y, bgColor))
		b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="value" font-size="9">%s</text>`, y+13, escSVG(n.NSID)))
		tierColor := map[string]string{"instant": "#00ff88", "interactive": "#88ff00", "tolerable": "#ffcc00", "background": "#888888"}
		tc := tierColor[n.Tier]
		if tc == "" {
			tc = "#888888"
		}
		b.WriteString(fmt.Sprintf(`<text x="480" y="%d" font-size="9" fill="%s">%s</text>`, y+13, tc, n.Tier))
		b.WriteString(fmt.Sprintf(`<text x="580" y="%d" class="label" font-size="9">%.0fms</text>`, y+13, n.P50Target))
		b.WriteString(fmt.Sprintf(`<text x="670" y="%d" class="label" font-size="9">%.0fms</text>`, y+13, n.P99Target))
		actualColor := "#00ff88"
		if n.P50Actual > n.P50Target {
			actualColor = "#ff4444"
		}
		b.WriteString(fmt.Sprintf(`<text x="760" y="%d" font-size="9" fill="%s">%.0fms</text>`, y+13, actualColor, n.P50Actual))
		stColor := "#00ff88"
		stText := "OK"
		if n.Status == "gap" {
			stColor = "#ff4444"
			stText = "GAP"
		}
		b.WriteString(fmt.Sprintf(`<text x="860" y="%d" font-size="10" font-weight="bold" fill="%s">%s</text>`, y+13, stColor, stText))
		y += 20
	}
	y += 25

	// ── Issues ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">Issues (%d total: %d critical, %d high)</text>`, y,
		len(r.Issues),
		countIssueSev(r.Issues, "critical"),
		countIssueSev(r.Issues, "high")))
	y += 20

	for _, issue := range r.Issues {
		sevClass := issue.Severity
		b.WriteString(fmt.Sprintf(`<rect x="40" y="%d" width="1120" height="28" fill="#12162a" stroke="#1a2040" rx="3"/>`, y))
		b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="%s">%-8s</text>`, y+19, sevClass, strings.ToUpper(issue.Severity)))
		comp := issue.Component
		if len(comp) > 24 {
			comp = comp[:24]
		}
		b.WriteString(fmt.Sprintf(`<text x="160" y="%d" class="label">%s</text>`, y+19, escSVG(comp)))
		desc := issue.Issue
		if len(desc) > 50 {
			desc = desc[:50]
		}
		b.WriteString(fmt.Sprintf(`<text x="400" y="%d" class="value">%s</text>`, y+19, escSVG(desc)))
		b.WriteString(fmt.Sprintf(`<text x="900" y="%d" class="label">%s → %s</text>`, y+19, issue.Phase, escSVG(slaTruncStr(issue.Fix, 30))))
		y += 30
	}
	y += 25

	// ── Phase Roadmap ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">Roadmap to 99.999%%</text>`, y))
	y += 25

	phaseColors := map[string]string{"P0": "#ff4444", "P1": "#ff8844", "P2": "#ffcc44", "P3": "#00ff88"}
	for _, p := range r.Phases {
		color := phaseColors[p.Phase]
		if color == "" {
			color = "#4488ff"
		}
		b.WriteString(fmt.Sprintf(`<rect x="40" y="%d" width="1120" height="%d" fill="#12162a" stroke="%s" class="phase-box"/>`,
			y, 28+len(p.Changes)*18, color))
		b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="value" fill="%s">%s — %s (%s, %s)</text>`,
			y+20, color, p.Phase, p.Target, p.Timeline, p.Cost))
		for i, c := range p.Changes {
			b.WriteString(fmt.Sprintf(`<text x="75" y="%d" class="label">• %s</text>`, y+38+i*18, escSVG(c)))
		}
		y += 32 + len(p.Changes)*18
	}
	y += 30

	// ── Gap meter ──
	b.WriteString(fmt.Sprintf(`<text x="40" y="%d" class="header">Gap to 99.999%%</text>`, y))
	y += 25
	meters := []struct {
		name string
		val  float64
	}{
		{"Write Path", r.WritePath.Composite},
		{"Read Path ", r.TimelinePath.Composite},
	}
	for _, m := range meters {
		pct := m.val * 100
		barW := (pct - 99.0) / (100.0 - 99.0) * 800
		if barW < 0 {
			barW = 0
		}
		if barW > 800 {
			barW = 800
		}
		targetW := (99.999 - 99.0) / (100.0 - 99.0) * 800
		b.WriteString(fmt.Sprintf(`<text x="55" y="%d" class="label">%s</text>`, y+16, m.name))
		b.WriteString(fmt.Sprintf(`<rect x="200" y="%d" width="800" height="20" class="bar-bg" rx="4"/>`, y+2))
		b.WriteString(fmt.Sprintf(`<rect x="200" y="%d" width="%.0f" height="20" class="bar-fill" rx="4"/>`, y+2, barW))
		b.WriteString(fmt.Sprintf(`<line x1="%.0f" y1="%d" x2="%.0f" y2="%d" stroke="#00ff88" stroke-width="2"/>`, 200+targetW, y, 200+targetW, y+24))
		b.WriteString(fmt.Sprintf(`<text x="%.0f" y="%d" class="grade-s" font-size="9" text-anchor="middle">99.999%%</text>`, 200+targetW, y-2))
		b.WriteString(fmt.Sprintf(`<text x="1020" y="%d" class="value">%s</text>`, y+16, slaPercent(m.val)))
		y += 30
	}

	b.WriteString("</svg>")
	return b.String()
}

func escSVG(s string) string {
	s = strings.ReplaceAll(s, "&", "&amp;")
	s = strings.ReplaceAll(s, "<", "&lt;")
	s = strings.ReplaceAll(s, ">", "&gt;")
	s = strings.ReplaceAll(s, "\"", "&quot;")
	return s
}

func slaTruncStr(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n-3] + "..."
}

func countIssueSev(issues []slaIssue, sev string) int {
	n := 0
	for _, i := range issues {
		if i.Severity == sev {
			n++
		}
	}
	return n
}

func buildSLAReport() slaReport {
	components := []slaComponent{
		{
			Name: "CF Workers (Dispatcher)", Layer: "edge",
			AvailSLA: 0.9999, Redundancy: 1, FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: false, WriteAuth: false, ReadAuth: true,
			Issues:      nil,
			Mitigations: []string{"Anycast global, auto-failover across 300+ PoP"},
		},
		{
			Name: "CF Workers (PDS)", Layer: "gateway",
			AvailSLA: 0.9999, Redundancy: 1, FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: true, WriteAuth: true, ReadAuth: true,
			Issues:      []string{"Single Worker, no multi-region active-active"},
			Mitigations: []string{"Circuit breaker (10s cooldown)", "Rate limiter 600/min", "KV-authoritative write"},
		},
		{
			Name: "CF KV (PDS_KV)", Layer: "storage",
			AvailSLA: 0.9999, DurabilitySLA: 0.99999999999, Redundancy: 1,
			FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: false, WriteAuth: true, ReadAuth: true,
			Issues:      nil,
			Mitigations: []string{"11 nines durability", "Global replication", "Authoritative write store"},
		},
		{
			Name: "CF R2 (Lance snapshots)", Layer: "storage",
			AvailSLA: 0.9999, DurabilitySLA: 0.99999999999, Redundancy: 1,
			FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: false, WriteAuth: false, ReadAuth: true,
			Issues:      []string{"Snapshot metadata.json write not atomic"},
			Mitigations: []string{"Lance append-only fragments", "KV authoritative fallback"},
		},
		{
			Name: "yata Container", Layer: "compute",
			AvailSLA: 0.9995, Redundancy: 1, FailoverSec: 3,
			ColdStartSec: 3, SinglePoint: true, WriteAuth: false, ReadAuth: true,
			Issues: []string{
				"Single instance (min_instances=1)",
				"CSR data lost on restart",
				"OOM risk from base64 snapshot encoding",
				"Cold start 2-3s blocks queries",
			},
			Mitigations: []string{"Fire-and-forget write (KV authoritative)", "Sql retry with 150ms delay"},
		},
		{
			Name: "CF Workers (App)", Layer: "compute",
			AvailSLA: 0.9999, Redundancy: 1, FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: false, WriteAuth: true, ReadAuth: true,
			Issues:      nil,
			Mitigations: []string{"V8 isolate per request", "Unlimited scripts in namespace"},
		},
		{
			Name: "CF Workers (Auth)", Layer: "gateway",
			AvailSLA: 0.9999, Redundancy: 1, FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: true, WriteAuth: false, ReadAuth: false,
			Issues:      []string{"Auth down = no new sessions (existing JWT still valid)"},
			Mitigations: []string{"JWT cached client-side (2h TTL)", "Service auth bypass for internal"},
		},
		{
			Name: "Murakumo Fleet (9x M4)", Layer: "compute",
			AvailSLA: 0.99, Redundancy: 9, FailoverSec: 0, ColdStartSec: 15,
			SinglePoint: false, WriteAuth: false, ReadAuth: false,
			Issues: []string{
				"No auto-failover between nodes",
				"MLX server OOM on concurrent large requests",
				"Model routing static (no health-based LB)",
			},
			Mitigations: []string{"9-node redundancy", "Murakumo Worker round-robin"},
		},
		{
			Name: "LanceDB (local /Volumes)", Layer: "storage",
			AvailSLA: 0.999, DurabilitySLA: 0.9999, Redundancy: 1,
			FailoverSec: 0, ColdStartSec: 0,
			SinglePoint: true, WriteAuth: true, ReadAuth: true,
			Issues:      []string{"Single disk, no replication", "USB volume failure = data loss"},
			Mitigations: []string{"R2 snapshot backup (manual)", "graph_results Sql file as replay log"},
		},
	}

	// Compute composite availability for paths
	writePath := slaPath{
		Name:       "Write (createRecord)",
		Components: []string{"CF Workers (App)", "CF Workers (PDS)", "CF KV (PDS_KV)"},
	}
	writePath.Composite = compositeAvail(components, writePath.Components)

	readPathKV := slaPath{
		Name:       "Read KV (getRecord)",
		Components: []string{"CF Workers (App)", "CF Workers (PDS)", "CF KV (PDS_KV)"},
	}
	readPathKV.Composite = compositeAvail(components, readPathKV.Components)

	readPathSql := slaPath{
		Name:       "Read Sql (search/list)",
		Components: []string{"CF Workers (App)", "CF Workers (PDS)", "yata Container"},
	}
	readPathSql.Composite = compositeAvail(components, readPathSql.Components)

	timelinePath := slaPath{
		Name:       "Timeline (KV fast → Sql fallback)",
		Components: []string{"CF Workers (App)", "CF Workers (PDS)", "CF KV (PDS_KV)", "yata Container"},
	}
	// Timeline: KV fast path OR Sql fallback = 1 - (1-KV)*(1-Sql)
	kvAvail := compositeAvail(components, []string{"CF Workers (App)", "CF Workers (PDS)", "CF KV (PDS_KV)"})
	sqlAvail := compositeAvail(components, []string{"CF Workers (App)", "CF Workers (PDS)", "yata Container"})
	timelinePath.Composite = 1 - (1-kvAvail)*(1-sqlAvail)

	// Issues
	issues := []slaIssue{
		{"critical", "yata Container", "Single instance — restart loses CSR", "Read queries fail 2-3s, stale data after recovery", "min_instances=2 + read replicas", "P1"},
		{"critical", "yata Container", "Snapshot metadata.json not atomic", "Container restart → empty CSR → all graph queries return 0 rows", "R2 atomic upload (multipart + ETag)", "P2"},
		{"critical", "yata Container", "OOM from base64 snapshot encoding", "Snapshot fails → restart → data loss cycle", "Streaming 32MB chunk upload to R2", "P0"},
		{"high", "CF Workers (PDS)", "Single-region Worker", "Region outage = full downtime", "Active-active 3-region deployment", "P3"},
		{"high", "yata Container", "Cold start 2-3s", "First query after sleep takes 2-3s", "min_instances=2, cron keep-alive", "P1"},
		{"high", "Murakumo Fleet", "No health-based load balancing", "Requests routed to OOM/busy nodes → 503", "Health check + weighted routing in Murakumo Worker", "P2"},
		{"medium", "CF Workers (PDS)", "Circuit breaker 10s fixed cooldown", "Premature recovery or too-long open", "Exponential backoff + jitter", "P2"},
		{"medium", "LanceDB (local)", "Single disk, no replication", "Disk failure = training data loss", "R2 periodic sync + RAID-1 on fleet", "P2"},
		{"medium", "CF KV (PDS_KV)", "Timeline KV list unbounded growth risk", "Large timeline JSON parse latency", "Cap at 1000 entries (implemented), shard by time window", "P1"},
		{"low", "CF Workers (Auth)", "Auth down blocks new sessions", "No new login for duration of outage", "JWT 2h TTL + refresh token chain", "P3"},
		{"low", "CF Workers (App)", "No per-app circuit breaker", "One bad app timeout", "Per-nanoid timeout + kill switch", "P2"},
	}

	phases := []slaPhase{
		{
			Phase: "P0", Target: "Data Durability", Downtime: "—",
			Changes: []string{
				"Streaming base64 snapshot export (32MB chunks)",
				"First-write snapshot forcing on Container start",
				"Empty CSR guard (reject queries until snapshot loaded)",
				"KV getRecord fallback (implemented)",
			},
			Cost: "~$3/mo", Timeline: "Immediate",
		},
		{
			Phase: "P1", Target: "99.95%", Downtime: "4.4h/year",
			Changes: []string{
				"yata min_instances=2 (read replicas)",
				"Cron snapshot every 1min (reliable)",
				"WAL replay automation on Container start",
				"RTO < 30s (snapshot load + CSR build)",
			},
			Cost: "~$9/mo", Timeline: "1 week",
		},
		{
			Phase: "P2", Target: "99.99%", Downtime: "52min/year",
			Changes: []string{
				"3-partition write (N=3, hash-based label routing)",
				"R2 atomic upload (multipart + ETag verification)",
				"QueryCache max_capacity guard (OOM prevention)",
				"Monitoring + alerting (Grafana / CF Analytics)",
				"Murakumo health-based LB",
				"Per-app circuit breaker in PDS",
			},
			Cost: "~$12/mo", Timeline: "3 weeks",
		},
		{
			Phase: "P3", Target: "99.999%", Downtime: "5.3min/year",
			Changes: []string{
				"Active-active 3-region PDS Workers (CF Smart Placement)",
				"yata 3-region × 3-partition (9 instances)",
				"Cross-region KV replication (automatic with CF KV)",
				"Circuit breaker with exponential backoff + jitter",
				"Streaming snapshot upload (32MB chunks, parallel)",
				"Chaos engineering: random Container kill + recovery test",
			},
			Cost: "~$36/mo", Timeline: "8 weeks",
		},
	}

	nsids := []slaNSID{
		{"health", "infra", "edge", "instant", 10, 20, 12, "met"},
		{"com.atproto.repo.createRecord", "write", "KV await", "interactive", 30, 100, 13, "met"},
		{"com.atproto.repo.getRecord", "read", "KV first", "instant", 10, 20, 5, "met"},
		{"com.atproto.repo.listRecords", "read", "Sql", "tolerable", 150, 500, 16, "met"},
		{"com.atproto.repo.deleteRecord", "write", "KV+yata", "interactive", 30, 100, 15, "met"},
		{"app.bsky.feed.getTimeline", "feed", "KV||Sql", "interactive", 30, 100, 176, "gap"},
		{"app.bsky.feed.getAuthorFeed", "feed", "KV||Sql", "interactive", 30, 100, 12, "met"},
		{"app.bsky.feed.getDiscoverFeed", "feed", "KV||Sql", "tolerable", 150, 500, 173, "met"},
		{"app.bsky.feed.getPostThread", "feed", "Sql 4x", "tolerable", 150, 500, 163, "met"},
		{"app.bsky.feed.searchPosts", "search", "Sql", "tolerable", 150, 500, 14, "met"},
		{"app.bsky.actor.getProfile", "profile", "KV first", "instant", 10, 20, 13, "met"},
		{"app.bsky.actor.searchActors", "search", "Sql 3x", "tolerable", 150, 500, 169, "met"},
		{"app.bsky.actor.getSuggestions", "profile", "Sql cached", "interactive", 30, 100, 12, "met"},
		{"app.bsky.graph.getFollowers", "social", "Sql", "interactive", 30, 100, 12, "met"},
		{"app.bsky.graph.getFollows", "social", "Sql", "interactive", 30, 100, 12, "met"},
		{"app.bsky.notification.listNotifications", "notif", "Sql", "interactive", 30, 100, 12, "met"},
		{"app.bsky.notification.getUnreadCount", "notif", "KV counter", "instant", 10, 20, 14, "met"},
		{"ai.gftd.kagami.sql", "graph", "Sql", "tolerable", 150, 500, 170, "met"},
		{"ai.gftd.kagami.sqlBatch", "graph", "Sql batch", "background", 500, 2000, 800, "met"},
		{"com.atproto.sync.subscribeRepos", "stream", "SSE", "background", 500, 2000, 100, "met"},
		{"ai.gftd.convo.sendMessage", "convo", "KV await", "interactive", 30, 100, 20, "met"},
		{"ai.gftd.convo.listMessages", "convo", "KV||Sql", "interactive", 30, 100, 25, "met"},
	}

	return slaReport{
		Target:          0.99999,
		TargetLabel:     "99.999% (Five Nines)",
		DowntimePerYear: "5 min 15 sec",
		Components:      components,
		WritePath:       writePath,
		ReadPathKV:      readPathKV,
		ReadPathSql:  readPathSql,
		TimelinePath:    timelinePath,
		OverallWrite:    writePath.Composite,
		OverallRead:     timelinePath.Composite,
		NSIDs:           nsids,
		Issues:          issues,
		Phases:          phases,
	}
}

func compositeAvail(components []slaComponent, names []string) float64 {
	avail := 1.0
	for _, name := range names {
		for _, c := range components {
			if c.Name == name {
				a := c.AvailSLA
				if c.Redundancy > 1 {
					// Parallel redundancy: 1 - (1-a)^N
					fail := 1.0
					for i := 0; i < c.Redundancy; i++ {
						fail *= (1 - a)
					}
					a = 1 - fail
				}
				avail *= a
				break
			}
		}
	}
	return avail
}

func slaPercent(v float64) string {
	if v >= 0.99999 {
		return fmt.Sprintf("%.5f%%", v*100)
	}
	if v >= 0.9999 {
		return fmt.Sprintf("%.4f%%", v*100)
	}
	if v >= 0.999 {
		return fmt.Sprintf("%.3f%%", v*100)
	}
	return fmt.Sprintf("%.2f%%", v*100)
}

func slaDowntime(avail float64) string {
	minutesPerYear := 525960.0
	down := (1 - avail) * minutesPerYear
	if down < 1 {
		return fmt.Sprintf("%.0fs/year", down*60)
	}
	if down < 60 {
		return fmt.Sprintf("%.1fmin/year", down)
	}
	return fmt.Sprintf("%.1fh/year", down/60)
}

func slaGrade(avail float64) string {
	if avail >= 0.99999 {
		return "S"
	}
	if avail >= 0.9999 {
		return "A"
	}
	if avail >= 0.999 {
		return "B"
	}
	if avail >= 0.99 {
		return "C"
	}
	return "D"
}

func printSLAReport(r slaReport) {
	fmt.Println()
	fmt.Println("╔══════════════════════════════════════════════════════════════════════════════════╗")
	fmt.Println("║              GFTD Platform SLA Analysis (可視化 SLA)                            ║")
	fmt.Printf("║              Target: %s — Max downtime: %s/year        ║\n", r.TargetLabel, r.DowntimePerYear)
	fmt.Println("╠══════════════════════════════════════════════════════════════════════════════════╣")
	fmt.Println()

	// Component table
	fmt.Println("  ┌─────────────────────────────┬─────────┬───────┬──────────┬──────┬───────────────────┐")
	fmt.Println("  │ Component                   │ SLA     │ Grade │ Redund.  │ SPOF │ Downtime/year     │")
	fmt.Println("  ├─────────────────────────────┼─────────┼───────┼──────────┼──────┼───────────────────┤")
	for _, c := range r.Components {
		effectiveAvail := c.AvailSLA
		if c.Redundancy > 1 {
			fail := 1.0
			for i := 0; i < c.Redundancy; i++ {
				fail *= (1 - c.AvailSLA)
			}
			effectiveAvail = 1 - fail
		}
		spof := "  "
		if c.SinglePoint {
			spof = "!!"
		}
		name := c.Name
		if len(name) > 27 {
			name = name[:27]
		}
		redStr := fmt.Sprintf("%dx", c.Redundancy)
		fmt.Printf("  │ %-27s │ %s │   %s   │ %-8s │  %s  │ %-17s │\n",
			name, slaPercent(effectiveAvail), slaGrade(effectiveAvail), redStr, spof, slaDowntime(effectiveAvail))
	}
	fmt.Println("  └─────────────────────────────┴─────────┴───────┴──────────┴──────┴───────────────────┘")
	fmt.Println()

	// Request paths
	fmt.Println("  Request Path Composite Availability:")
	fmt.Println("  ┌─────────────────────────────────────────┬───────────┬───────┬───────────────────┐")
	fmt.Println("  │ Path                                    │ Composite │ Grade │ Downtime/year     │")
	fmt.Println("  ├─────────────────────────────────────────┼───────────┼───────┼───────────────────┤")
	paths := []slaPath{r.WritePath, r.ReadPathKV, r.ReadPathSql, r.TimelinePath}
	for _, p := range paths {
		name := p.Name
		if len(name) > 39 {
			name = name[:39]
		}
		fmt.Printf("  │ %-39s │ %s │   %s   │ %-17s │\n",
			name, slaPercent(p.Composite), slaGrade(p.Composite), slaDowntime(p.Composite))
	}
	fmt.Println("  └─────────────────────────────────────────┴───────────┴───────┴───────────────────┘")
	fmt.Println()

	// Path chain visualization
	fmt.Println("  Write Path:    App Worker → PDS Worker → KV (await)")
	fmt.Printf("                 %s (%s)\n", slaPercent(r.WritePath.Composite), slaDowntime(r.WritePath.Composite))
	fmt.Println()
	fmt.Println("  Read KV:       App Worker → PDS Worker → KV get")
	fmt.Printf("                 %s (%s)\n", slaPercent(r.ReadPathKV.Composite), slaDowntime(r.ReadPathKV.Composite))
	fmt.Println()
	fmt.Println("  Read Sql:   App Worker → PDS Worker → yata Container")
	fmt.Printf("                 %s (%s)\n", slaPercent(r.ReadPathSql.Composite), slaDowntime(r.ReadPathSql.Composite))
	fmt.Println()
	fmt.Println("  Timeline:      KV fast path OR Sql fallback")
	fmt.Printf("                 %s (%s)\n", slaPercent(r.TimelinePath.Composite), slaDowntime(r.TimelinePath.Composite))
	fmt.Println()

	// NSID p99 SLA table
	fmt.Println("  NSID-Level p99 SLA Targets:")
	fmt.Println("  ┌─────────────────────────────────────────────┬─────────────┬────────┬────────┬────────┬────────┐")
	fmt.Println("  │ NSID                                        │ Tier        │ p50 T  │ p99 T  │ p50 A  │ Status │")
	fmt.Println("  ├─────────────────────────────────────────────┼─────────────┼────────┼────────┼────────┼────────┤")
	gapCount := 0
	for _, n := range r.NSIDs {
		nsid := n.NSID
		if len(nsid) > 43 {
			nsid = nsid[:43]
		}
		tier := n.Tier
		if len(tier) > 11 {
			tier = tier[:11]
		}
		status := n.Status
		statusMark := "  OK  "
		if status == "gap" {
			statusMark = " GAP  "
			gapCount++
		} else if status == "unknown" {
			statusMark = "  ?   "
		}
		fmt.Printf("  │ %-43s │ %-11s │ %4.0fms │ %4.0fms │ %4.0fms │ %s │\n",
			nsid, tier, n.P50Target, n.P99Target, n.P50Actual, statusMark)
	}
	fmt.Println("  └─────────────────────────────────────────────┴─────────────┴────────┴────────┴────────┴────────┘")
	fmt.Printf("  Coverage: %d/%d NSIDs within target (%d gaps)\n", len(r.NSIDs)-gapCount, len(r.NSIDs), gapCount)
	fmt.Println()

	// Gap analysis
	targetPct := r.Target * 100
	writePct := r.WritePath.Composite * 100
	readPct := r.TimelinePath.Composite * 100
	fmt.Println("  Gap to Target (99.999%):")
	writeGap := targetPct - writePct
	readGap := targetPct - readPct
	if writeGap > 0 {
		fmt.Printf("    Write:   %.4f%% → need +%.4f%%\n", writePct, writeGap)
	} else {
		fmt.Printf("    Write:   %.5f%% — TARGET MET\n", writePct)
	}
	if readGap > 0 {
		fmt.Printf("    Read:    %.4f%% → need +%.4f%%\n", readPct, readGap)
	} else {
		fmt.Printf("    Read:    %.5f%% — TARGET MET\n", readPct)
	}
	fmt.Println()

	// Issues
	fmt.Println("  ┌──────────┬─────────────────────────────┬─────────────────────────────────────────────┐")
	fmt.Println("  │ Severity │ Component                   │ Issue                                       │")
	fmt.Println("  ├──────────┼─────────────────────────────┼─────────────────────────────────────────────┤")
	for _, issue := range r.Issues {
		sev := issue.Severity
		if len(sev) > 8 {
			sev = sev[:8]
		}
		comp := issue.Component
		if len(comp) > 27 {
			comp = comp[:27]
		}
		desc := issue.Issue
		if len(desc) > 43 {
			desc = desc[:43]
		}
		fmt.Printf("  │ %-8s │ %-27s │ %-43s │\n", sev, comp, desc)
	}
	fmt.Println("  └──────────┴─────────────────────────────┴─────────────────────────────────────────────┘")
	fmt.Println()

	// Issue details with fix
	fmt.Println("  Issue Details:")
	for i, issue := range r.Issues {
		fmt.Printf("    %d. [%s] %s — %s\n", i+1, strings.ToUpper(issue.Severity), issue.Component, issue.Issue)
		fmt.Printf("       Impact: %s\n", issue.Impact)
		fmt.Printf("       Fix:    %s (Phase %s)\n", issue.Fix, issue.Phase)
	}
	fmt.Println()

	// Phases roadmap
	fmt.Println("  ┌───────┬──────────┬───────────────┬───────────┬──────────┐")
	fmt.Println("  │ Phase │ Target   │ Downtime/year │ Cost/mo   │ Timeline │")
	fmt.Println("  ├───────┼──────────┼───────────────┼───────────┼──────────┤")
	for _, p := range r.Phases {
		fmt.Printf("  │ %-5s │ %-8s │ %-13s │ %-9s │ %-8s │\n",
			p.Phase, p.Target, p.Downtime, p.Cost, p.Timeline)
	}
	fmt.Println("  └───────┴──────────┴───────────────┴───────────┴──────────┘")
	fmt.Println()

	for _, p := range r.Phases {
		fmt.Printf("  %s (%s, %s):\n", p.Phase, p.Target, p.Timeline)
		for _, c := range p.Changes {
			fmt.Printf("    - %s\n", c)
		}
		fmt.Println()
	}

	// Availability bar
	fmt.Println("  Current → Target:")
	bars := []struct {
		name string
		val  float64
	}{
		{"Write ", r.WritePath.Composite},
		{"Read  ", r.TimelinePath.Composite},
		{"Target", r.Target},
	}
	for _, b := range bars {
		// Scale: 99.90% = 0, 100% = 50 chars
		pct := b.val * 100
		barPos := int((pct - 99.90) / (100.0 - 99.90) * 50)
		if barPos < 0 {
			barPos = 0
		}
		if barPos > 50 {
			barPos = 50
		}
		bar := strings.Repeat("█", barPos) + strings.Repeat("░", 50-barPos)
		fmt.Printf("    %s [%s] %s\n", b.name, bar, slaPercent(b.val))
	}
	fmt.Println()
	fmt.Println("╚══════════════════════════════════════════════════════════════════════════════════╝")
}
