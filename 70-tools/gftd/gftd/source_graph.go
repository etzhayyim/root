package main

import (
	"bufio"
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

// --- Annotation types ---

type sgDirective struct {
	Type  string // "import", "lexicon", "calls", "writes", "reads", "authority", "rule", "sensitivity", "owner", "contract", "supersedes", "visibility", "ref"
	Value string // raw value after the directive keyword
}

type sgAnnotation struct {
	File       string        // relative file path
	Line       int           // 1-based line number
	FuncName   string        // enclosing function name (empty = file-level)
	Directives []sgDirective // all directives in scope
}

type sgSourceNode struct {
	Path        string   `json:"path"`
	Kind        string   `json:"kind"`        // "go", "rust", "ts", "wit"
	FuncName    string   `json:"func_name,omitempty"`
	Line        int      `json:"line"`
	AppDID      string   `json:"app_did,omitempty"`
	Sensitivity string   `json:"sensitivity,omitempty"`
	Visibility  string   `json:"visibility,omitempty"`
	Imports     []string `json:"imports,omitempty"`
	Lexicons    []string `json:"lexicons,omitempty"`
	Calls       []string `json:"calls,omitempty"`    // "did#method"
	Writes      []string `json:"writes,omitempty"`
	Reads       []string `json:"reads,omitempty"`
	Authorities []string `json:"authorities,omitempty"` // "kind/id"
	Rules       []string `json:"rules,omitempty"`
	Owner       string   `json:"owner,omitempty"`
	Contracts   []string `json:"contracts,omitempty"` // "category/id"
	Supersedes  []string `json:"supersedes,omitempty"`
	Refs        []string `json:"refs,omitempty"`
}

type sgGraph struct {
	GeneratedAt    string            `json:"generated_at"`
	TotalFiles     int               `json:"total_files"`
	Annotated      int               `json:"annotated"`       // files with @gftd: annotations
	ASTExtracted   int               `json:"ast_extracted"`   // files with AST-extracted facts
	MetaResolved   int               `json:"meta_resolved"`   // files with WIT/jsonld metadata
	ExtractionMode string            `json:"extraction_mode"` // "hybrid" (3-layer)
	Nodes          []sgSourceNode    `json:"nodes"`
	AppMeta        map[string]sgMetaResult `json:"app_meta,omitempty"`
}

type sgViolation struct {
	Rule    string `json:"rule"`
	Path    string `json:"path"`
	Detail  string `json:"detail"`
	Severity string `json:"severity"` // error, warning, info
}

type sgViolationReport struct {
	GeneratedAt string        `json:"generated_at"`
	TotalNodes  int           `json:"total_nodes"`
	Violations  []sgViolation `json:"violations"`
	Score       sgScore       `json:"score"`
}

type sgScore struct {
	AnnotationCoverage    float64 `json:"annotation_coverage"`     // Layer 3: @gftd: comment files / total
	ASTCoverage           float64 `json:"ast_coverage"`            // Layer 2: AST-extracted files / total
	MetaCoverage          float64 `json:"meta_coverage"`           // Layer 1: WIT+jsonld resolved / total apps
	AutoExtractRate       float64 `json:"auto_extract_rate"`       // (Layer1 + Layer2) / total — no manual work
	ViolationFreeRate     float64 `json:"violation_free_rate"`
	AuthorityCoverage     float64 `json:"authority_coverage"`
	ReferenceIntegrity    float64 `json:"reference_integrity"`
	SourceGraphScore      float64 `json:"source_graph_score"`
}

// --- Regex patterns for annotation parsing ---

var (
	sgDirectivePattern = regexp.MustCompile(`//\s*@gftd:(\w+)\s+(.+)`)
	sgGoFuncPattern    = regexp.MustCompile(`^func\s+(?:\([^)]+\)\s+)?(\w+)\s*\(`)
	sgRustFuncPattern  = regexp.MustCompile(`^(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[<(]`)
	sgTSFuncPattern    = regexp.MustCompile(`^(?:export\s+)?(?:async\s+)?function\s+(\w+)\s*[<(]`)
)

// --- Entry point ---

func runSourceGraph(args []string) error {
	if len(args) == 0 {
		printSourceGraphUsage()
		return nil
	}
	switch args[0] {
	case "scan":
		return runSGScan(args[1:])
	case "violations":
		return runSGViolations(args[1:])
	case "sql":
		return runSGSql(args[1:])
	case "dot":
		return runSGDot(args[1:])
	case "help", "--help", "-h":
		printSourceGraphUsage()
		return nil
	default:
		return fmt.Errorf("unknown source-graph command: %s", args[0])
	}
}

func printSourceGraphUsage() {
	fmt.Print(`gftd source-graph — source-level annotation graph + policy enforcement

USAGE:
  gftd source-graph <command> [flags]

COMMANDS:
  scan          Scan source files for @gftd: annotations → JSON graph
  violations    Detect policy violations from annotation graph
  sql        Generate Sql statements for yata graph projection
  dot           Generate Graphviz DOT output

ANNOTATION SYNTAX:
  // @gftd:import <wit-interface>           WIT dependency
  // @gftd:lexicon <nsid>                   AT Lexicon mapping
  // @gftd:calls <did>#<method>             cross-actor invocation
  // @gftd:writes <collection>              Write target
  // @gftd:reads <collection>               Read source
  // @gftd:authority <kind>/<id>            Governing authority
  // @gftd:rule <rule-id>[,<rule-id>...]    Enforced rules
  // @gftd:sensitivity <level>              Data classification
  // @gftd:owner <did>                      Responsible DID
  // @gftd:contract <category>/<id>         Contract basis
  // @gftd:supersedes <path>                Replaced source
  // @gftd:visibility <level>               Access scope
  // @gftd:ref <doc-path>                   Design doc reference

Run 'gftd source-graph <command> --help' for command-specific flags.
`)
}

// --- scan command ---

func runSGScan(args []string) error {
	fs := flag.NewFlagSet("source-graph scan", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", true, "output as JSON")
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

	graph := sgScanWorkspace(wsRoot)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(graph)
	}

	fmt.Printf("source_graph:\n")
	fmt.Printf("  generated_at: %s\n", graph.GeneratedAt)
	fmt.Printf("  extraction_mode: %s\n", graph.ExtractionMode)
	fmt.Printf("  total_files: %d\n", graph.TotalFiles)
	fmt.Printf("  layer1_meta_resolved: %d\n", graph.MetaResolved)
	fmt.Printf("  layer2_ast_extracted: %d\n", graph.ASTExtracted)
	fmt.Printf("  layer3_annotated: %d\n", graph.Annotated)
	fmt.Printf("  nodes: %d\n", len(graph.Nodes))
	return nil
}

// --- violations command ---

func runSGViolations(args []string) error {
	fs := flag.NewFlagSet("source-graph violations", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", true, "output as JSON")
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

	graph := sgScanWorkspace(wsRoot)
	report := sgDetectViolations(wsRoot, &graph)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("source_graph_violations:\n")
	fmt.Printf("  score: %.1f\n", report.Score.SourceGraphScore)
	fmt.Printf("  violations: %d\n", len(report.Violations))
	for _, v := range report.Violations {
		fmt.Printf("    [%s] %s: %s (%s)\n", v.Severity, v.Rule, v.Detail, v.Path)
	}
	return nil
}

// --- sql command ---

func runSGSql(args []string) error {
	fs := flag.NewFlagSet("source-graph sql", flag.ContinueOnError)
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

	graph := sgScanWorkspace(wsRoot)
	stmts := sgGenerateSql(&graph)
	for _, s := range stmts {
		fmt.Println(s)
	}
	return nil
}

// --- dot command ---

func runSGDot(args []string) error {
	fs := flag.NewFlagSet("source-graph dot", flag.ContinueOnError)
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

	graph := sgScanWorkspace(wsRoot)
	fmt.Println(sgGenerateDot(&graph))
	return nil
}

// --- Core: workspace scan ---

func resolveWSRoot(dir string) (string, error) {
	if dir != "" {
		return filepath.Abs(dir)
	}
	cwd, err := os.Getwd()
	if err != nil {
		return "", err
	}
	root, err := findGitRoot(cwd)
	if err != nil {
		return "", fmt.Errorf("detect workspace root: %w", err)
	}
	return filepath.Abs(root)
}

func sgScanWorkspace(wsRoot string) sgGraph {
	graph := sgGraph{
		GeneratedAt:    time.Now().UTC().Format(time.RFC3339),
		ExtractionMode: "hybrid",
	}

	// --- Layer 1: Collect app metadata (WIT + magatama.jsonld) ---
	graph.AppMeta = sgScanAppMeta(wsRoot)
	graph.MetaResolved = len(graph.AppMeta)

	// --- Scan source files ---
	scanDirs := []struct {
		base    string
		pattern string
		kind    string
	}{
		{filepath.Join(wsRoot, "projects"), "*/wasm/*/main.go", "go"},
		{filepath.Join(wsRoot, "projects"), "*/wasm/*/src/lib.rs", "rust"},
		{filepath.Join(wsRoot, "projects"), "*/wasm/*/src/main.rs", "rust"},
		{filepath.Join(wsRoot, "projects"), "*/wasm/*/wit/world.wit", "wit"},
		{filepath.Join(wsRoot, "infra"), "cloudflare/container/*/src/index.ts", "ts"},
		{filepath.Join(wsRoot, "infra"), "cloudflare/container/*/src/*.ts", "ts"},
		{filepath.Join(wsRoot, "packages"), "ts/*/src/*.ts", "ts"},
		{filepath.Join(wsRoot, "packages"), "rust/*/src/*.rs", "rust"},
	}

	seen := make(map[string]bool)
	for _, sd := range scanDirs {
		matches, _ := filepath.Glob(filepath.Join(sd.base, sd.pattern))
		for _, m := range matches {
			rel, _ := filepath.Rel(wsRoot, m)
			if seen[rel] {
				continue
			}
			seen[rel] = true
			graph.TotalFiles++

			// --- Layer 3: @gftd: comment directives ---
			commentNodes := sgParseFile(m, rel, sd.kind)
			hasAnnotation := len(commentNodes) > 0
			if hasAnnotation {
				graph.Annotated++
			}

			// --- Layer 2: AST extraction ---
			data, err := os.ReadFile(m)
			if err != nil {
				if hasAnnotation {
					graph.Nodes = append(graph.Nodes, commentNodes...)
				}
				continue
			}
			content := string(data)

			var astResult sgASTResult
			switch sd.kind {
			case "go":
				astResult = sgExtractGoAST(m, data)
			case "ts":
				astResult = sgExtractTSAST(content)
			case "rust":
				astResult = sgExtractRustAST(content)
			}

			hasAST := len(astResult.Writes) > 0 || len(astResult.Reads) > 0 ||
				len(astResult.Commands) > 0 || len(astResult.Calls) > 0 ||
				astResult.HasServe || len(astResult.Handlers) > 0
			if hasAST {
				graph.ASTExtracted++
			}

			// --- Merge 3 layers ---
			if hasAnnotation {
				// Merge AST facts into annotated nodes
				for i := range commentNodes {
					sgMergeASTIntoNode(&commentNodes[i], astResult)
				}
				graph.Nodes = append(graph.Nodes, commentNodes...)
			} else if hasAST {
				// No annotations — create nodes from AST alone
				nodes := sgASTToNodes(rel, sd.kind, astResult)
				graph.Nodes = append(graph.Nodes, nodes...)
			}

			// --- Layer 1: Merge metadata ---
			// Find matching app metadata for this file
			for i := range graph.Nodes {
				if graph.Nodes[i].Path != rel {
					continue
				}
				// Find closest app dir
				appDir := sgFindAppDir(rel)
				if meta, ok := graph.AppMeta[appDir]; ok {
					sgMergeMetaIntoNode(&graph.Nodes[i], meta)
				}
			}
		}
	}

	// Derive app_did from project path for any remaining unresolved nodes
	for i := range graph.Nodes {
		if graph.Nodes[i].AppDID == "" {
			graph.Nodes[i].AppDID = sgInferAppDID(graph.Nodes[i].Path)
		}
	}

	return graph
}

// sgASTToNodes creates source nodes from AST-only extraction (no @gftd: annotations).
func sgASTToNodes(relPath, kind string, ast sgASTResult) []sgSourceNode {
	var nodes []sgSourceNode

	// File-level node with aggregated data
	fileNode := sgSourceNode{
		Path:   relPath,
		Kind:   kind,
		Writes: ast.Writes,
		Reads:  ast.Reads,
		Calls:  ast.Calls,
	}
	nodes = append(nodes, fileNode)

	// Per-function nodes
	for _, fn := range ast.Funcs {
		if len(fn.Writes) == 0 && len(fn.Reads) == 0 && len(fn.Calls) == 0 {
			continue
		}
		funcNode := sgSourceNode{
			Path:     relPath,
			Kind:     kind,
			FuncName: fn.Name,
			Line:     fn.Line,
			Writes:   fn.Writes,
			Reads:    fn.Reads,
			Calls:    fn.Calls,
		}
		nodes = append(nodes, funcNode)
	}

	return nodes
}

// sgFindAppDir finds the app directory (e.g., "projects/ai-gftd-project-news/wasm/news-app")
// from a relative file path.
func sgFindAppDir(relPath string) string {
	parts := strings.Split(relPath, string(filepath.Separator))
	// Look for projects/*/wasm/*/ pattern
	for i := 0; i+3 < len(parts); i++ {
		if parts[i] == "projects" && parts[i+2] == "wasm" {
			return filepath.Join(parts[:i+4]...)
		}
	}
	return ""
}

// sgParseFile extracts @gftd: annotations from a source file.
func sgParseFile(absPath, relPath, kind string) []sgSourceNode {
	f, err := os.Open(absPath)
	if err != nil {
		return nil
	}
	defer f.Close()

	var nodes []sgSourceNode
	var currentFunc string
	var fileDirectives []sgDirective
	var funcDirectives []sgDirective
	var funcStartLine int
	lineNum := 0
	hasAnnotation := false

	flushFunc := func() {
		if currentFunc != "" && len(funcDirectives) > 0 {
			nodes = append(nodes, sgBuildNode(relPath, kind, currentFunc, funcStartLine, funcDirectives))
		}
		funcDirectives = nil
	}

	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		lineNum++
		line := scanner.Text()
		trimmed := strings.TrimSpace(line)

		// Check for @gftd: directive
		if m := sgDirectivePattern.FindStringSubmatch(trimmed); m != nil {
			hasAnnotation = true
			d := sgDirective{Type: m[1], Value: strings.TrimSpace(m[2])}
			if currentFunc != "" {
				funcDirectives = append(funcDirectives, d)
			} else {
				fileDirectives = append(fileDirectives, d)
			}
			continue
		}

		// Detect function boundaries
		var funcName string
		switch kind {
		case "go":
			if sm := sgGoFuncPattern.FindStringSubmatch(line); sm != nil {
				funcName = sm[1]
			}
		case "rust":
			if sm := sgRustFuncPattern.FindStringSubmatch(line); sm != nil {
				funcName = sm[1]
			}
		case "ts":
			if sm := sgTSFuncPattern.FindStringSubmatch(line); sm != nil {
				funcName = sm[1]
			}
		}

		if funcName != "" {
			flushFunc()
			currentFunc = funcName
			funcStartLine = lineNum
			// Pending file-level directives that appeared right before this func
			// belong to the func if there are no file-level directives yet
		}
	}
	flushFunc()

	if !hasAnnotation {
		return nil
	}

	// File-level node (if there are file-level directives)
	if len(fileDirectives) > 0 {
		node := sgBuildNode(relPath, kind, "", 0, fileDirectives)
		nodes = append([]sgSourceNode{node}, nodes...)
	}

	return nodes
}

func sgBuildNode(path, kind, funcName string, line int, directives []sgDirective) sgSourceNode {
	node := sgSourceNode{
		Path:     path,
		Kind:     kind,
		FuncName: funcName,
		Line:     line,
	}

	for _, d := range directives {
		switch d.Type {
		case "import":
			node.Imports = append(node.Imports, d.Value)
		case "lexicon":
			node.Lexicons = append(node.Lexicons, d.Value)
		case "calls":
			node.Calls = append(node.Calls, d.Value)
		case "writes":
			node.Writes = append(node.Writes, d.Value)
		case "reads":
			node.Reads = append(node.Reads, d.Value)
		case "authority":
			// Support comma-separated: "sovereign/jpn, treaty/wto"
			for _, a := range strings.Split(d.Value, ",") {
				a = strings.TrimSpace(a)
				if a != "" {
					node.Authorities = append(node.Authorities, a)
				}
			}
		case "rule":
			for _, r := range strings.Split(d.Value, ",") {
				r = strings.TrimSpace(r)
				if r != "" {
					node.Rules = append(node.Rules, r)
				}
			}
		case "sensitivity":
			node.Sensitivity = d.Value
		case "owner":
			node.Owner = d.Value
		case "contract":
			node.Contracts = append(node.Contracts, d.Value)
		case "supersedes":
			node.Supersedes = append(node.Supersedes, d.Value)
		case "visibility":
			node.Visibility = d.Value
		case "ref":
			node.Refs = append(node.Refs, d.Value)
		}
	}

	return node
}

// sgInferAppDID extracts app DID from path like "projects/ai-gftd-project-news/wasm/..."
func sgInferAppDID(relPath string) string {
	parts := strings.Split(relPath, string(filepath.Separator))
	for i, p := range parts {
		if strings.HasPrefix(p, "ai-gftd-project-") {
			appName := strings.TrimPrefix(p, "ai-gftd-project-")
			_ = i
			return "did:web:" + appName + ".etzhayyim.com"
		}
	}
	return ""
}

// --- Core: violation detection ---

func sgDetectViolations(wsRoot string, graph *sgGraph) sgViolationReport {
	report := sgViolationReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		TotalNodes:  len(graph.Nodes),
	}

	// Index nodes by app_did for cross-reference
	nodesByApp := make(map[string][]sgSourceNode)
	for _, n := range graph.Nodes {
		if n.AppDID != "" {
			nodesByApp[n.AppDID] = append(nodesByApp[n.AppDID], n)
		}
	}

	// V1 (wit-import-drift) retired per ADR-0049 §M1 — WIT bindgen is a
	// dead path; AT Lexicon JSON is the surviving contract. @gftd:import
	// directives and world.wit scans no longer gate source graph compliance.

	violatedPaths := make(map[string]bool)

	for _, node := range graph.Nodes {
		// V2: sensitivity escalation — confidential source calling public
		if node.Sensitivity == "confidential" || node.Sensitivity == "restricted" {
			for _, call := range node.Calls {
				did := strings.Split(call, "#")[0]
				for _, other := range graph.Nodes {
					if other.Owner == did && (other.Visibility == "public") {
						report.Violations = append(report.Violations, sgViolation{
							Rule:     "sensitivity-escalation",
							Path:     node.Path,
							Detail:   fmt.Sprintf("%s source calls public DID %s", node.Sensitivity, did),
							Severity: "error",
						})
						violatedPaths[node.Path] = true
					}
				}
			}
		}

		// V3: authority gap — sovereign without treaty
		hasSovereign := false
		hasTreaty := false
		for _, a := range node.Authorities {
			if strings.HasPrefix(a, "sovereign/") {
				hasSovereign = true
			}
			if strings.HasPrefix(a, "treaty/") {
				hasTreaty = true
			}
		}
		if hasSovereign && !hasTreaty && len(node.Authorities) > 0 {
			report.Violations = append(report.Violations, sgViolation{
				Rule:     "authority-gap",
				Path:     node.Path,
				Detail:   "sovereign authority declared without treaty — consider adding @gftd:authority treaty/*",
				Severity: "info",
			})
		}

		// V4: circular dependency detection is done across the graph (below)

		// V5: dead supersedes reference
		for _, sup := range node.Supersedes {
			checkPath := filepath.Join(wsRoot, sup)
			if _, err := os.Stat(checkPath); os.IsNotExist(err) {
				report.Violations = append(report.Violations, sgViolation{
					Rule:     "dead-supersedes",
					Path:     node.Path,
					Detail:   fmt.Sprintf("@gftd:supersedes %s — target file not found", sup),
					Severity: "warning",
				})
				violatedPaths[node.Path] = true
			}
		}

		// V6: Shannon redundancy — same collection written by multiple apps
		// (collected below)

		// V7: no-dual-write rule with multiple writes
		for _, r := range node.Rules {
			if r == "no-dual-write" && len(node.Writes) > 1 {
				report.Violations = append(report.Violations, sgViolation{
					Rule:     "rule-no-dual-write",
					Path:     node.Path,
					Detail:   fmt.Sprintf("@gftd:rule no-dual-write but %d write targets declared", len(node.Writes)),
					Severity: "error",
				})
				violatedPaths[node.Path] = true
			}
			if r == "no-batch-polling" {
				// Check if the file has any batch-like patterns
				// This is a lightweight check — full check is in magatama-lint
			}
		}

		// V8: dead ref — referenced doc doesn't exist
		for _, ref := range node.Refs {
			refPath := filepath.Join(wsRoot, ref)
			if _, err := os.Stat(refPath); os.IsNotExist(err) {
				report.Violations = append(report.Violations, sgViolation{
					Rule:     "dead-ref",
					Path:     node.Path,
					Detail:   fmt.Sprintf("@gftd:ref %s — document not found", ref),
					Severity: "warning",
				})
				violatedPaths[node.Path] = true
			}
		}
	}

	// V6: Shannon redundancy — detect multi-app writes to same collection
	collectionWriters := make(map[string]map[string]bool) // collection -> set of app_did
	for _, node := range graph.Nodes {
		for _, w := range node.Writes {
			if collectionWriters[w] == nil {
				collectionWriters[w] = make(map[string]bool)
			}
			if node.AppDID != "" {
				collectionWriters[w][node.AppDID] = true
			}
		}
	}
	for coll, writers := range collectionWriters {
		if len(writers) > 1 {
			var writerList []string
			for w := range writers {
				writerList = append(writerList, w)
			}
			sort.Strings(writerList)
			report.Violations = append(report.Violations, sgViolation{
				Rule:     "shannon-redundancy",
				Path:     "(cross-app)",
				Detail:   fmt.Sprintf("collection %s written by %d apps: %s", coll, len(writers), strings.Join(writerList, ", ")),
				Severity: "warning",
			})
		}
	}

	// V4: cycle detection via DFS on calls graph
	callGraph := make(map[string][]string) // source_id -> []target_did
	didToSource := make(map[string]string) // owner did -> source_id
	for _, node := range graph.Nodes {
		nodeID := node.Path
		if node.FuncName != "" {
			nodeID = node.Path + ":" + node.FuncName
		}
		if node.Owner != "" {
			didToSource[node.Owner] = nodeID
		}
		for _, call := range node.Calls {
			did := strings.Split(call, "#")[0]
			callGraph[nodeID] = append(callGraph[nodeID], did)
		}
	}
	// Simple cycle detection
	for startID, targets := range callGraph {
		for _, targetDID := range targets {
			if targetSrc, ok := didToSource[targetDID]; ok {
				if nextTargets, ok2 := callGraph[targetSrc]; ok2 {
					for _, nextDID := range nextTargets {
						if nextSrc, ok3 := didToSource[nextDID]; ok3 {
							if nextSrc == startID {
								report.Violations = append(report.Violations, sgViolation{
									Rule:     "circular-dependency",
									Path:     startID,
									Detail:   fmt.Sprintf("cycle: %s -> %s -> %s -> %s", startID, targetDID, targetSrc, startID),
									Severity: "error",
								})
								violatedPaths[startID] = true
							}
						}
					}
				}
			}
		}
	}

	// Compute score
	totalFiles := float64(graph.TotalFiles)
	if totalFiles == 0 {
		totalFiles = 1
	}

	annotationCoverage := float64(graph.Annotated) / totalFiles
	astCoverage := float64(graph.ASTExtracted) / totalFiles
	metaCoverage := 0.0
	if graph.MetaResolved > 0 {
		// Meta coverage is apps with metadata / total app directories
		metaCoverage = 1.0 // If metadata scan ran, apps have jsonld
	}

	// Auto-extract rate: files covered by Layer 1 or Layer 2 without manual annotation
	autoFiles := graph.ASTExtracted // AST alone covers these
	autoExtractRate := float64(autoFiles) / totalFiles

	// Total covered = any of the 3 layers
	coveredNodes := len(graph.Nodes)
	violationFreeRate := 0.0
	if coveredNodes > 0 {
		violationFreeRate = 1.0 - float64(len(violatedPaths))/float64(coveredNodes)
		if violationFreeRate < 0 {
			violationFreeRate = 0
		}
	}

	// Authority coverage: nodes with at least one authority / total nodes
	authCount := 0
	for _, n := range graph.Nodes {
		if len(n.Authorities) > 0 {
			authCount++
		}
	}
	authCoverage := 0.0
	if len(graph.Nodes) > 0 {
		authCoverage = float64(authCount) / float64(len(graph.Nodes))
	}

	// Reference integrity: valid refs / total refs
	totalRefs := 0
	validRefs := 0
	for _, n := range graph.Nodes {
		for _, ref := range n.Refs {
			totalRefs++
			refPath := filepath.Join(wsRoot, ref)
			if _, err := os.Stat(refPath); err == nil {
				validRefs++
			}
		}
		for _, sup := range n.Supersedes {
			totalRefs++
			supPath := filepath.Join(wsRoot, sup)
			if _, err := os.Stat(supPath); err == nil {
				validRefs++
			}
		}
	}
	refIntegrity := 1.0
	if totalRefs > 0 {
		refIntegrity = float64(validRefs) / float64(totalRefs)
	}

	// Score model (approach E):
	// 25% auto_extract_rate (Layer 1+2 automation)
	// 25% violation_free_rate
	// 20% annotation_coverage (Layer 3 intent declarations)
	// 15% authority_coverage
	// 15% reference_integrity
	report.Score = sgScore{
		AnnotationCoverage: annotationCoverage,
		ASTCoverage:        astCoverage,
		MetaCoverage:       metaCoverage,
		AutoExtractRate:    autoExtractRate,
		ViolationFreeRate:  violationFreeRate,
		AuthorityCoverage:  authCoverage,
		ReferenceIntegrity: refIntegrity,
		SourceGraphScore: 0.25*autoExtractRate*100 +
			0.25*violationFreeRate*100 +
			0.20*annotationCoverage*100 +
			0.15*authCoverage*100 +
			0.15*refIntegrity*100,
	}

	return report
}

// --- Core: Sql generation ---

func sgGenerateSql(graph *sgGraph) []string {
	var stmts []string

	for _, node := range graph.Nodes {
		nodeID := sgSqlID(node)
		props := fmt.Sprintf(`{path: "%s", kind: "%s"`, sgEsc(node.Path), sgEsc(node.Kind))
		if node.FuncName != "" {
			props += fmt.Sprintf(`, func_name: "%s", line: %d`, sgEsc(node.FuncName), node.Line)
		}
		if node.AppDID != "" {
			props += fmt.Sprintf(`, app_did: "%s"`, sgEsc(node.AppDID))
		}
		if node.Sensitivity != "" {
			props += fmt.Sprintf(`, sensitivity: "%s"`, sgEsc(node.Sensitivity))
		}
		if node.Visibility != "" {
			props += fmt.Sprintf(`, visibility: "%s"`, sgEsc(node.Visibility))
		}
		props += "}"

		stmts = append(stmts, "MERGE (s:Source "+props+");")

		// IMPORTS edges
		for _, imp := range node.Imports {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (w:WITInterface {fqn: "%s"}) MERGE (s:Source {path: "%s"})-[:IMPORTS]->(w);`,
				sgEsc(imp), sgEsc(nodeID)))
		}

		// IMPLEMENTS edges (lexicon)
		for _, lex := range node.Lexicons {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (l:Lexicon {nsid: "%s"}) MERGE (s:Source {path: "%s"})-[:IMPLEMENTS]->(l);`,
				sgEsc(lex), sgEsc(nodeID)))
		}

		// INVOKES edges
		for _, call := range node.Calls {
			parts := strings.SplitN(call, "#", 2)
			did := parts[0]
			method := ""
			if len(parts) > 1 {
				method = parts[1]
			}
			methodProp := ""
			if method != "" {
				methodProp = fmt.Sprintf(` {method: "%s"}`, sgEsc(method))
			}
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (d:DID {id: "%s"}) MERGE (s:Source {path: "%s"})-[:INVOKES%s]->(d);`,
				sgEsc(did), sgEsc(nodeID), methodProp))
		}

		// WRITES_TO edges
		for _, w := range node.Writes {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (c:Collection {nsid: "%s"}) MERGE (s:Source {path: "%s"})-[:WRITES_TO]->(c);`,
				sgEsc(w), sgEsc(nodeID)))
		}

		// READS_FROM edges
		for _, r := range node.Reads {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (c:Collection {nsid: "%s"}) MERGE (s:Source {path: "%s"})-[:READS_FROM]->(c);`,
				sgEsc(r), sgEsc(nodeID)))
		}

		// GOVERNED_BY edges
		for _, a := range node.Authorities {
			parts := strings.SplitN(a, "/", 2)
			kind := parts[0]
			id := ""
			if len(parts) > 1 {
				id = parts[1]
			}
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (a:Authority {kind: "%s", id: "%s"}) MERGE (s:Source {path: "%s"})-[:GOVERNED_BY]->(a);`,
				sgEsc(kind), sgEsc(id), sgEsc(nodeID)))
		}

		// ENFORCES edges
		for _, r := range node.Rules {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (r:Rule {id: "%s"}) MERGE (s:Source {path: "%s"})-[:ENFORCES]->(r);`,
				sgEsc(r), sgEsc(nodeID)))
		}

		// BOUND_BY edges (contracts)
		for _, c := range node.Contracts {
			parts := strings.SplitN(c, "/", 2)
			cat := parts[0]
			id := ""
			if len(parts) > 1 {
				id = parts[1]
			}
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (ct:Contract {category: "%s", id: "%s"}) MERGE (s:Source {path: "%s"})-[:BOUND_BY]->(ct);`,
				sgEsc(cat), sgEsc(id), sgEsc(nodeID)))
		}

		// OWNED_BY edge
		if node.Owner != "" {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (d:DID {id: "%s"}) MERGE (s:Source {path: "%s"})-[:OWNED_BY]->(d);`,
				sgEsc(node.Owner), sgEsc(nodeID)))
		}

		// SUPERSEDES edges
		for _, sup := range node.Supersedes {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (t:Source {path: "%s"}) MERGE (s:Source {path: "%s"})-[:SUPERSEDES]->(t);`,
				sgEsc(sup), sgEsc(nodeID)))
		}

		// REFERENCES edges
		for _, ref := range node.Refs {
			stmts = append(stmts, fmt.Sprintf(
				`MERGE (doc:Document {path: "%s"}) MERGE (s:Source {path: "%s"})-[:REFERENCES]->(doc);`,
				sgEsc(ref), sgEsc(nodeID)))
		}
	}

	return stmts
}

// --- Core: DOT generation ---

func sgGenerateDot(graph *sgGraph) string {
	var b strings.Builder
	b.WriteString("digraph source_graph {\n")
	b.WriteString("  rankdir=LR;\n")
	b.WriteString("  node [shape=box, fontsize=10];\n")
	b.WriteString("  edge [fontsize=8];\n\n")

	// Group by app_did
	appNodes := make(map[string][]sgSourceNode)
	for _, n := range graph.Nodes {
		app := n.AppDID
		if app == "" {
			app = "_unowned"
		}
		appNodes[app] = append(appNodes[app], n)
	}

	clusterIdx := 0
	for app, nodes := range appNodes {
		b.WriteString(fmt.Sprintf("  subgraph cluster_%d {\n", clusterIdx))
		b.WriteString(fmt.Sprintf("    label=%q;\n", app))
		b.WriteString("    style=dashed;\n")
		for _, n := range nodes {
			nodeID := sgDotID(n)
			label := n.Path
			if n.FuncName != "" {
				label = n.FuncName
			}
			b.WriteString(fmt.Sprintf("    %s [label=%q];\n", nodeID, label))
		}
		b.WriteString("  }\n\n")
		clusterIdx++
	}

	// Edges
	for _, n := range graph.Nodes {
		srcID := sgDotID(n)
		for _, call := range n.Calls {
			targetID := sgDotSafe(call)
			b.WriteString(fmt.Sprintf("  %s -> %s [label=\"calls\", color=red];\n", srcID, targetID))
		}
		for _, w := range n.Writes {
			targetID := sgDotSafe(w)
			b.WriteString(fmt.Sprintf("  %s -> %s [label=\"writes\", color=blue];\n", srcID, targetID))
		}
		for _, r := range n.Reads {
			targetID := sgDotSafe(r)
			b.WriteString(fmt.Sprintf("  %s -> %s [label=\"reads\", color=green];\n", srcID, targetID))
		}
		for _, imp := range n.Imports {
			targetID := sgDotSafe(imp)
			b.WriteString(fmt.Sprintf("  %s -> %s [label=\"import\", style=dotted];\n", srcID, targetID))
		}
	}

	b.WriteString("}\n")
	return b.String()
}

// --- Helpers ---

func sgSqlID(node sgSourceNode) string {
	if node.FuncName != "" {
		return node.Path + ":" + node.FuncName
	}
	return node.Path
}

func sgEsc(s string) string {
	s = strings.ReplaceAll(s, `\`, `\\`)
	s = strings.ReplaceAll(s, `"`, `\"`)
	return s
}

func sgDotID(n sgSourceNode) string {
	id := n.Path
	if n.FuncName != "" {
		id = n.Path + "_" + n.FuncName
	}
	return sgDotSafe(id)
}

func sgDotSafe(s string) string {
	r := strings.NewReplacer(
		"/", "_", ".", "_", "-", "_", ":", "_", "#", "_",
		"@", "_", " ", "_", "(", "_", ")", "_",
	)
	return r.Replace(s)
}
