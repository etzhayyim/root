package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// --- haisen data model ---

type haisenApp struct {
	Nanoid        string   `json:"nanoid"`
	DID           string   `json:"did"`
	Name          string   `json:"name"`
	PerformerType string   `json:"performer_type"`
	RuntimeType   string   `json:"runtime_type"`
	UIType        string   `json:"ui_type,omitempty"`
	Project       string   `json:"project"`
	Collections   []string `json:"collections,omitempty"`
}

type haisenEdge struct {
	From     string `json:"from"`
	To       string `json:"to"`
	EdgeType string `json:"edge_type"` // invoke, writes, reads, subscribe, follow, service_binding, wasm-import
	Label    string `json:"label,omitempty"`
}

type haisenGraph struct {
	GeneratedAt string       `json:"generated_at"`
	Apps        []haisenApp  `json:"apps"`
	Edges       []haisenEdge `json:"edges"`
	Infra       []haisenApp  `json:"infra"`
	Stats       haisenStats  `json:"stats"`
}

type haisenStats struct {
	TotalApps        int `json:"total_apps"`
	TotalEdges       int `json:"total_edges"`
	InvokeEdges      int `json:"invoke_edges"`
	WriteEdges       int `json:"write_edges"`
	ReadEdges        int `json:"read_edges"`
	SubscribeEdges   int `json:"subscribe_edges"`
	WasmImportEdges  int `json:"wasm_import_edges"`
	Orphans          int `json:"orphans"`
}

type haisenCoupling struct {
	Collection  string   `json:"collection"`
	Writers     []string `json:"writers,omitempty"`
	Readers     []string `json:"readers,omitempty"`
	Subscribers []string `json:"subscribers,omitempty"`
	TotalApps   int      `json:"total_apps"`
}

// --- entry point ---

func runHaisen(args []string) error {
	if len(args) == 0 {
		printHaisenUsage()
		return nil
	}
	switch args[0] {
	case "scan":
		return runHaisenScan(args[1:])
	case "edges":
		return runHaisenEdges(args[1:])
	case "orphans":
		return runHaisenOrphans(args[1:])
	case "coupling":
		return runHaisenCoupling(args[1:])
	case "help", "--help", "-h":
		printHaisenUsage()
		return nil
	default:
		return fmt.Errorf("unknown haisen command: %s", args[0])
	}
}

func printHaisenUsage() {
	fmt.Print(`gftd haisen — app-level wiring diagram (配線図)

USAGE:
  gftd haisen <command> [flags]

COMMANDS:
  scan       Scan all apps and extract inter-app wiring → JSON graph
  edges      List edges (filtered by --type, --from, --to)
  orphans    List apps with zero wiring edges
  coupling   Show collection-mediated coupling between apps

EDGE TYPES:
  invoke       cross-actor Invoke(did, method) calls
  writes       Collection write targets
  reads        Sql graph reads
  subscribe    ComAtprotoSyncSubscribeRepos subscriptions
  follow       Follow(nanoid) relationships
  wasm-import  WIT Component Model import declarations (world.wit → resolved nanoid)

Run 'gftd haisen <command> --help' for command-specific flags.
`)
}

// --- scan command ---

func runHaisenScan(args []string) error {
	fs := flag.NewFlagSet("haisen scan", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	includeInfra := fs.Bool("include-infra", false, "include infra nodes in output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	graph := haisenScanWorkspace(wsRoot, *includeInfra)

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(graph)
}

// --- edges command ---

func runHaisenEdges(args []string) error {
	fs := flag.NewFlagSet("haisen edges", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	edgeType := fs.String("type", "", "filter by edge type (invoke, writes, reads, subscribe)")
	from := fs.String("from", "", "filter by source app nanoid/name")
	to := fs.String("to", "", "filter by target")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	graph := haisenScanWorkspace(wsRoot, false)

	var filtered []haisenEdge
	for _, e := range graph.Edges {
		if *edgeType != "" && e.EdgeType != *edgeType {
			continue
		}
		if *from != "" && !strings.Contains(e.From, *from) {
			continue
		}
		if *to != "" && !strings.Contains(e.To, *to) {
			continue
		}
		filtered = append(filtered, e)
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(filtered)
}

// --- orphans command ---

func runHaisenOrphans(args []string) error {
	fs := flag.NewFlagSet("haisen orphans", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	graph := haisenScanWorkspace(wsRoot, false)

	connected := make(map[string]bool)
	for _, e := range graph.Edges {
		connected[e.From] = true
		connected[e.To] = true
	}

	var orphans []haisenApp
	for _, app := range graph.Apps {
		id := app.Nanoid
		if id == "" {
			id = app.DID
		}
		if !connected[id] && !connected[app.Name] && !connected[app.DID] {
			orphans = append(orphans, app)
		}
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(orphans)
}

// --- coupling command ---

func runHaisenCoupling(args []string) error {
	fs := flag.NewFlagSet("haisen coupling", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	minApps := fs.Int("min", 2, "minimum apps sharing a collection to report")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	graph := haisenScanWorkspace(wsRoot, false)

	type collInfo struct {
		writers     map[string]bool
		readers     map[string]bool
		subscribers map[string]bool
	}

	colls := make(map[string]*collInfo)
	ensureColl := func(c string) *collInfo {
		if colls[c] == nil {
			colls[c] = &collInfo{
				writers:     make(map[string]bool),
				readers:     make(map[string]bool),
				subscribers: make(map[string]bool),
			}
		}
		return colls[c]
	}

	for _, e := range graph.Edges {
		switch e.EdgeType {
		case "writes":
			ensureColl(e.To).writers[e.From] = true
		case "reads":
			ensureColl(e.To).readers[e.From] = true
		case "subscribe":
			ensureColl(e.To).subscribers[e.From] = true
		}
	}

	var couplings []haisenCoupling
	for coll, info := range colls {
		allApps := make(map[string]bool)
		for a := range info.writers {
			allApps[a] = true
		}
		for a := range info.readers {
			allApps[a] = true
		}
		for a := range info.subscribers {
			allApps[a] = true
		}
		if len(allApps) < *minApps {
			continue
		}
		c := haisenCoupling{
			Collection: coll,
			TotalApps:  len(allApps),
		}
		for a := range info.writers {
			c.Writers = append(c.Writers, a)
		}
		for a := range info.readers {
			c.Readers = append(c.Readers, a)
		}
		for a := range info.subscribers {
			c.Subscribers = append(c.Subscribers, a)
		}
		sort.Strings(c.Writers)
		sort.Strings(c.Readers)
		sort.Strings(c.Subscribers)
		couplings = append(couplings, c)
	}

	sort.Slice(couplings, func(i, j int) bool {
		return couplings[i].TotalApps > couplings[j].TotalApps
	})

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(couplings)
}

// --- core scan logic ---

func haisenScanWorkspace(wsRoot string, includeInfra bool) haisenGraph {
	graph := haisenGraph{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
	}

	// 1. Discover apps from magatama.jsonld (reuse sgScanAppMeta)
	appMeta := sgScanAppMeta(wsRoot)

	// Build app list and nanoid→app index
	nanoidToApp := make(map[string]*haisenApp)
	didToNanoid := make(map[string]string)

	// Sort app paths for deterministic layout
	var appPaths []string
	for relPath := range appMeta {
		appPaths = append(appPaths, relPath)
	}
	sort.Strings(appPaths)

	for _, relPath := range appPaths {
		meta := appMeta[relPath]
		// Skip apps without nanoid or DID (WIT-only, no magatama.jsonld)
		if meta.NanoID == "" && meta.DID == "" {
			continue
		}
		project := haisenExtractProject(relPath)
		app := haisenApp{
			Nanoid:        meta.NanoID,
			DID:           meta.DID,
			Name:          meta.Name,
			PerformerType: meta.PerformerType,
			RuntimeType:   meta.RuntimeType,
			UIType:        meta.UIType,
			Project:       project,
			Collections:   meta.Collections,
		}
		graph.Apps = append(graph.Apps, app)
		if meta.NanoID != "" {
			nanoidToApp[meta.NanoID] = &graph.Apps[len(graph.Apps)-1]
			didToNanoid[meta.DID] = meta.NanoID
		}
	}

	sort.Slice(graph.Apps, func(i, j int) bool {
		return graph.Apps[i].Name < graph.Apps[j].Name
	})

	// 2. Extract edges from source-graph AST
	sgGraph := sgScanWorkspace(wsRoot)

	// Map source-graph nodes to their app (by AppDID → nanoid)
	for _, node := range sgGraph.Nodes {
		fromNanoid := didToNanoid[node.AppDID]
		if fromNanoid == "" {
			continue
		}

		// Invoke edges
		for _, call := range node.Calls {
			graph.Edges = append(graph.Edges, haisenEdge{
				From:     fromNanoid,
				To:       call,
				EdgeType: "invoke",
				Label:    call,
			})
		}

		// Write edges
		for _, w := range node.Writes {
			graph.Edges = append(graph.Edges, haisenEdge{
				From:     fromNanoid,
				To:       w,
				EdgeType: "writes",
				Label:    w,
			})
		}

		// Read edges
		for _, r := range node.Reads {
			if strings.HasPrefix(r, "subscribeRepos:") {
				continue // handled separately
			}
			graph.Edges = append(graph.Edges, haisenEdge{
				From:     fromNanoid,
				To:       r,
				EdgeType: "reads",
				Label:    r,
			})
		}
	}

	// 3. Extract subscribe edges from magatama.jsonld collections
	for _, app := range graph.Apps {
		for _, coll := range app.Collections {
			graph.Edges = append(graph.Edges, haisenEdge{
				From:     app.Nanoid,
				To:       coll,
				EdgeType: "subscribe",
				Label:    coll,
			})
		}
	}

	// 4a. Extract wasm-import edges from world.wit import declarations.
	// Resolves WIT imports to exporting app nanoids via WITExports cross-reference.
	// Only emits edges where both From and To are known app nanoids (DSM-compatible).
	witExportToNanoid := make(map[string]string)
	for _, meta := range appMeta {
		if meta.NanoID == "" {
			continue
		}
		for _, exp := range meta.WITExports {
			witExportToNanoid[exp] = meta.NanoID
		}
	}
	for _, meta := range appMeta {
		fromNanoid := meta.NanoID
		if fromNanoid == "" {
			continue
		}
		for _, imp := range meta.WITImports {
			toNanoid := witExportToNanoid[imp]
			if toNanoid == "" || toNanoid == fromNanoid {
				continue
			}
			graph.Edges = append(graph.Edges, haisenEdge{
				From:     fromNanoid,
				To:       toNanoid,
				EdgeType: "wasm-import",
				Label:    imp,
			})
		}
	}

	// 4. Deduplicate and sort edges (deterministic order for layout)
	graph.Edges = haisenDeduplicateEdges(graph.Edges)
	sort.Slice(graph.Edges, func(i, j int) bool {
		if graph.Edges[i].From != graph.Edges[j].From {
			return graph.Edges[i].From < graph.Edges[j].From
		}
		if graph.Edges[i].To != graph.Edges[j].To {
			return graph.Edges[i].To < graph.Edges[j].To
		}
		return graph.Edges[i].EdgeType < graph.Edges[j].EdgeType
	})

	// 5. Infra nodes
	if includeInfra {
		graph.Infra = haisenInfraNodes()
	}

	// 6. Stats
	connected := make(map[string]bool)
	for _, e := range graph.Edges {
		connected[e.From] = true
		graph.Stats.TotalEdges++
		switch e.EdgeType {
		case "invoke":
			graph.Stats.InvokeEdges++
		case "writes":
			graph.Stats.WriteEdges++
		case "reads":
			graph.Stats.ReadEdges++
		case "subscribe":
			graph.Stats.SubscribeEdges++
		case "wasm-import":
			graph.Stats.WasmImportEdges++
		}
	}
	graph.Stats.TotalApps = len(graph.Apps)
	for _, app := range graph.Apps {
		if !connected[app.Nanoid] {
			graph.Stats.Orphans++
		}
	}

	return graph
}

func haisenExtractProject(relPath string) string {
	// relPath: projects/ai-gftd-project-{name}/wasm/{app}/...
	parts := strings.Split(relPath, string(filepath.Separator))
	for _, p := range parts {
		if strings.HasPrefix(p, "ai-gftd-project-") {
			return strings.TrimPrefix(p, "ai-gftd-project-")
		}
	}
	return ""
}

func haisenDeduplicateEdges(edges []haisenEdge) []haisenEdge {
	seen := make(map[string]bool)
	var result []haisenEdge
	for _, e := range edges {
		key := e.From + "|" + e.To + "|" + e.EdgeType
		if seen[key] {
			continue
		}
		seen[key] = true
		result = append(result, e)
	}
	return result
}

func haisenInfraNodes() []haisenApp {
	return []haisenApp{
		{Name: "pds", DID: "did:web:mod.etzhayyim.com", RuntimeType: "worker", PerformerType: "system"},
		{Name: "yoro", DID: "did:web:yoro.etzhayyim.com", RuntimeType: "worker", PerformerType: "system"},
		{Name: "repo", DID: "did:web:repo.etzhayyim.com", RuntimeType: "worker", PerformerType: "system"},
		{Name: "maps", DID: "did:web:maps.etzhayyim.com", RuntimeType: "worker", PerformerType: "system"},
	}
}

// Layout is computed by kami-graph Rust crate (kami-web WASM).
// Go CLI outputs data only. kami-web run_with_graph() handles layout + rendering.
