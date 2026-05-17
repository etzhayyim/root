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

// ── Process Mining Command ──

func runProcessMining(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "scan":
			return runPMScan(args[1:])
		case "bottlenecks":
			return runPMBottlenecks(args[1:])
		case "flow":
			return runPMFlow(args[1:])
		case "help", "--help", "-h":
			printProcessMiningUsage()
			return nil
		default:
			return runPMScan(args)
		}
	}
	return runPMScan(args)
}

func printProcessMiningUsage() {
	fmt.Print(`gftd process-mining — PDS XRPC handler static analysis + performance bottleneck detection

USAGE:
  gftd process-mining <command> [flags]

COMMANDS:
  scan          Full analysis of all PDS handler files → JSON/text report
  bottlenecks   List critical performance bottlenecks only
  flow          Show request flow diagram for a specific NSID

FLAGS:
  --workspace-dir   Workspace root (default: git root)
  --json            Output as JSON
  --severity        Filter by severity: critical,high,medium (default: all)
  --handler         Filter by handler file: feed,repo,infra,gftd (default: all)

ANALYSIS:
  - Unfiltered full scans (buildLabelSql without WHERE filter)
  - Sequential waterfalls (await inside for-loop)
  - Missing cache (aiGftdYataSql instead of aiGftdYataSqlCached)
  - Missing time filters on engagement queries
  - N+1 query patterns
  - Cross-label fan-out risk
`)
}

// ── Data Model ──

type pmHandler struct {
	Name     string `json:"name"`
	NSID     string `json:"nsid"`
	File     string `json:"file"`
	Line     int    `json:"line"`
	Category string `json:"category"`
}

type pmQueryCall struct {
	Function string `json:"function"`
	Label    string `json:"label"`
	Cached   bool   `json:"cached"`
	Filtered bool   `json:"filtered"`
	Filter   string `json:"filter,omitempty"`
	Line     int    `json:"line"`
}

type pmBottleneck struct {
	Handler  string `json:"handler"`
	NSID     string `json:"nsid"`
	Type     string `json:"type"`
	Severity string `json:"severity"`
	Message  string `json:"message"`
	File     string `json:"file"`
	Line     int    `json:"line"`
	Fix      string `json:"fix"`
}

type pmFlowStep struct {
	Step     int    `json:"step"`
	Type     string `json:"type"`
	Function string `json:"function"`
	Label    string `json:"label,omitempty"`
	Parallel bool   `json:"parallel"`
	Cached   bool   `json:"cached"`
	Filtered bool   `json:"filtered"`
}

type pmHandlerAnalysis struct {
	Handler       pmHandler      `json:"handler"`
	Queries       []pmQueryCall  `json:"queries"`
	QueryCount    int            `json:"query_count"`
	CachedCount   int            `json:"cached_count"`
	FilteredCount int            `json:"filtered_count"`
	Sequential    bool           `json:"sequential"`
	Bottlenecks   []pmBottleneck `json:"bottlenecks"`
	Score         float64        `json:"score"`
	Grade         string         `json:"grade"`
	Flow          []pmFlowStep   `json:"flow"`
}

type pmReport struct {
	AnalyzedAt   string              `json:"analyzed_at"`
	HandlerFiles []string            `json:"handler_files"`
	Handlers     []pmHandlerAnalysis `json:"handlers"`
	Summary      pmSummary           `json:"summary"`
}

type pmSummary struct {
	TotalHandlers    int            `json:"total_handlers"`
	TotalQueries     int            `json:"total_queries"`
	UnfilteredScans  int            `json:"unfiltered_scans"`
	UncachedQueries  int            `json:"uncached_queries"`
	SequentialChains int            `json:"sequential_chains"`
	CriticalCount    int            `json:"critical_count"`
	HighCount        int            `json:"high_count"`
	MediumCount      int            `json:"medium_count"`
	OverallScore     float64        `json:"overall_score"`
	OverallGrade     string         `json:"overall_grade"`
	TopBottlenecks   []pmBottleneck `json:"top_bottlenecks"`
}

type pmMethodBlock struct {
	name      string
	startLine int
	endLine   int
	content   string
}

// ── Source Analysis Patterns ──

var (
	// Match buildLabelSql calls: ctx.aiGftdYataSqlCached({ sql: buildLabelSql("Label", limit, "filter"), ... })
	reQueryLabel       = regexp.MustCompile(`buildLabelSql\("([^"]*)"`)
	reQueryLabelFilter = regexp.MustCompile(`buildLabelSql\("([^"]*)",\s*\d+,\s*"([^"]*)"`)
	// Match aiGftdYataSql/aiGftdYataSqlCached calls (named params: ctx.aiGftdYataSql({ ... }))
	reCyCall  = regexp.MustCompile(`ctx\.aiGftdYataSql(Cached)?\(\{`)
	reCyMatch = regexp.MustCompile(`MATCH\s*\((\w+):(\w+)`)
	reCyWhere = regexp.MustCompile(`WHERE\s+`)
	reCyLimit = regexp.MustCompile(`LIMIT\s+(\d+)`)
	// Match Promise.all
	rePromiseAll = regexp.MustCompile(`Promise\.all\(\[`)
	// Match await inside loop
	reAwaitInLoop = regexp.MustCompile(`for\s*\([^)]*\)\s*\{[^}]*await\s`)
	// Match method/handler function
	reMethodCheck = regexp.MustCompile(`method\s*===?\s*"(\w+)"`)
	reIfMethod    = regexp.MustCompile(`if\s*\(\s*method\s*===?\s*"(\w+)"`)
	reCaseMethod  = regexp.MustCompile(`^\s*case\s+([^:]+):`)
	// Handler categories
	reHandlerFile = regexp.MustCompile(`pds-handlers-(\w+)\.ts`)
)

type pmHandlerSource struct {
	Path     string
	Category string
}

// ── Scanner ──

func runPMScan(args []string) error {
	fs := flag.NewFlagSet("process-mining scan", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	jsonOut := fs.Bool("json", false, "output as JSON")
	severity := fs.String("severity", "", "filter by severity")
	handler := fs.String("handler", "", "filter by handler file")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot := *workspaceDir
	if wsRoot == "" {
		cwd, _ := os.Getwd()
		wsRoot, _ = findGitRoot(cwd)
	}

	handlerFiles := resolvePMHandlerSources(wsRoot)

	// Handler filter
	if *handler != "" {
		filterSet := make(map[string]bool)
		for _, h := range strings.Split(*handler, ",") {
			filterSet[strings.TrimSpace(h)] = true
		}
		var filtered []pmHandlerSource
		for _, src := range handlerFiles {
			if filterSet[src.Category] {
				filtered = append(filtered, src)
			}
		}
		handlerFiles = filtered
	}

	report := pmReport{
		AnalyzedAt: time.Now().UTC().Format(time.RFC3339),
	}
	for _, src := range handlerFiles {
		report.HandlerFiles = append(report.HandlerFiles, src.Path)
	}

	for _, src := range handlerFiles {
		data, err := os.ReadFile(src.Path)
		if err != nil {
			fmt.Fprintf(os.Stderr, "warning: %s: %v\n", src.Path, err)
			continue
		}
		analyses := analyzeHandlerFile(src, string(data))
		report.Handlers = append(report.Handlers, analyses...)
	}

	// Severity filter
	if *severity != "" {
		sevSet := make(map[string]bool)
		for _, s := range strings.Split(*severity, ",") {
			sevSet[strings.TrimSpace(s)] = true
		}
		for i := range report.Handlers {
			var filtered []pmBottleneck
			for _, b := range report.Handlers[i].Bottlenecks {
				if sevSet[b.Severity] {
					filtered = append(filtered, b)
				}
			}
			report.Handlers[i].Bottlenecks = filtered
		}
	}

	// Compute summary
	report.Summary = computePMSummary(report.Handlers)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printPMText(&report)
	return nil
}

func runPMBottlenecks(args []string) error {
	fs := flag.NewFlagSet("process-mining bottlenecks", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	jsonOut := fs.Bool("json", false, "output as JSON")
	severity := fs.String("severity", "critical,high", "filter by severity")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot := *workspaceDir
	if wsRoot == "" {
		cwd, _ := os.Getwd()
		wsRoot, _ = findGitRoot(cwd)
	}

	handlerFiles := resolvePMHandlerSources(wsRoot)

	sevSet := make(map[string]bool)
	for _, s := range strings.Split(*severity, ",") {
		sevSet[strings.TrimSpace(s)] = true
	}

	var bottlenecks []pmBottleneck
	for _, src := range handlerFiles {
		data, err := os.ReadFile(src.Path)
		if err != nil {
			continue
		}
		analyses := analyzeHandlerFile(src, string(data))
		for _, a := range analyses {
			for _, b := range a.Bottlenecks {
				if sevSet[b.Severity] {
					bottlenecks = append(bottlenecks, b)
				}
			}
		}
	}

	sort.Slice(bottlenecks, func(i, j int) bool {
		sevOrder := map[string]int{"critical": 0, "high": 1, "medium": 2}
		return sevOrder[bottlenecks[i].Severity] < sevOrder[bottlenecks[j].Severity]
	})

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(bottlenecks)
	}

	fmt.Printf("Process Mining: %d bottlenecks found\n\n", len(bottlenecks))
	for _, b := range bottlenecks {
		sev := strings.ToUpper(b.Severity)
		fmt.Printf("[%s] %s (%s)\n", sev, b.Handler, b.NSID)
		fmt.Printf("  type: %s\n", b.Type)
		fmt.Printf("  message: %s\n", b.Message)
		fmt.Printf("  fix: %s\n", b.Fix)
		fmt.Printf("  location: %s:%d\n\n", b.File, b.Line)
	}
	return nil
}

func runPMFlow(args []string) error {
	fs := flag.NewFlagSet("process-mining flow", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	nsid := fs.String("nsid", "", "NSID or method name to trace")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if *nsid == "" && fs.NArg() > 0 {
		*nsid = fs.Arg(0)
	}
	if *nsid == "" {
		return fmt.Errorf("usage: gftd process-mining flow <nsid>")
	}

	wsRoot := *workspaceDir
	if wsRoot == "" {
		cwd, _ := os.Getwd()
		wsRoot, _ = findGitRoot(cwd)
	}

	handlerFiles := resolvePMHandlerSources(wsRoot)

	target := strings.ToLower(*nsid)
	for _, src := range handlerFiles {
		data, err := os.ReadFile(src.Path)
		if err != nil {
			continue
		}
		analyses := analyzeHandlerFile(src, string(data))
		for _, a := range analyses {
			if strings.ToLower(a.Handler.Name) == target || strings.ToLower(a.Handler.NSID) == target {
				printFlowDiagram(&a)
				return nil
			}
		}
	}
	return fmt.Errorf("handler not found: %s", *nsid)
}

func resolvePMHandlerDir(wsRoot string) string {
	candidates := []string{
		filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers"),
		filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src"),
		filepath.Join(wsRoot, "..", "..", "..", "50-infra", "cloudflare", "workers", "atproto", "src", "handlers"),
		filepath.Join(wsRoot, "..", "..", "..", "50-infra", "cloudflare", "workers", "atproto", "src"),
		filepath.Join(wsRoot, "infra", "cloudflare", "workers", "pds", "src"),
		filepath.Join(wsRoot, "packages", "server", "wproto", "src"),
	}
	for _, dir := range candidates {
		clean := filepath.Clean(dir)
		if st, err := os.Stat(clean); err == nil && st.IsDir() {
			return clean
		}
	}
	return ""
}

func resolvePMHandlerSources(wsRoot string) []pmHandlerSource {
	currentRoot := filepath.Join(wsRoot, "50-infra", "cloudflare", "workers", "atproto", "src", "handlers")
	current := []pmHandlerSource{
		{Path: filepath.Join(currentRoot, "appview", "feed.ts"), Category: "feed"},
		{Path: filepath.Join(currentRoot, "pds", "repo.ts"), Category: "repo"},
		{Path: filepath.Join(currentRoot, "pds", "server.ts"), Category: "infra"},
		{Path: filepath.Join(currentRoot, "gftd", "index.ts"), Category: "gftd"},
	}
	if allPMHandlerSourcesExist(current) {
		return current
	}

	legacyDir := resolvePMHandlerDir(wsRoot)
	legacy := []pmHandlerSource{
		{Path: filepath.Join(legacyDir, "pds-handlers-feed.ts"), Category: "feed"},
		{Path: filepath.Join(legacyDir, "pds-handlers-repo.ts"), Category: "repo"},
		{Path: filepath.Join(legacyDir, "pds-handlers-infra.ts"), Category: "infra"},
		{Path: filepath.Join(legacyDir, "pds-handlers-gftd.ts"), Category: "gftd"},
	}
	if allPMHandlerSourcesExist(legacy) {
		return legacy
	}

	var existing []pmHandlerSource
	for _, src := range append(current, legacy...) {
		if st, err := os.Stat(src.Path); err == nil && !st.IsDir() {
			existing = append(existing, src)
		}
	}
	return existing
}

func allPMHandlerSourcesExist(sources []pmHandlerSource) bool {
	if len(sources) == 0 {
		return false
	}
	for _, src := range sources {
		st, err := os.Stat(src.Path)
		if err != nil || st.IsDir() {
			return false
		}
	}
	return true
}

// ── Analysis Engine ──

func analyzeHandlerFile(src pmHandlerSource, content string) []pmHandlerAnalysis {
	lines := strings.Split(content, "\n")
	category := src.Category
	if category == "" {
		category = pmCategoryFromPath(src.Path)
	}
	if category == "" {
		category = "unknown"
	}

	var analyses []pmHandlerAnalysis

	// Find method blocks
	var blocks []pmMethodBlock
	for i, line := range lines {
		if m := reIfMethod.FindStringSubmatch(line); m != nil {
			methodName := m[1]
			// Find the block extent (simplified: next method check or 200 lines)
			endLine := i + 200
			if endLine > len(lines) {
				endLine = len(lines)
			}
			for j := i + 1; j < len(lines) && j < i+300; j++ {
				if reIfMethod.MatchString(lines[j]) || strings.Contains(lines[j], "// ── ") {
					endLine = j
					break
				}
			}
			blockContent := strings.Join(lines[i:endLine], "\n")
			blocks = append(blocks, pmMethodBlock{
				name:      methodName,
				startLine: i + 1,
				endLine:   endLine,
				content:   blockContent,
			})
		}
	}
	consts := parsePMConsts(lines)
	blocks = append(blocks, extractCaseMethodBlocks(lines, consts)...)
	if len(blocks) > 1 {
		seen := map[string]bool{}
		dedup := make([]pmMethodBlock, 0, len(blocks))
		for _, b := range blocks {
			key := fmt.Sprintf("%s:%d", b.name, b.startLine)
			if seen[key] {
				continue
			}
			seen[key] = true
			dedup = append(dedup, b)
		}
		blocks = dedup
	}

	for _, block := range blocks {
		handler := pmHandler{
			Name:     block.name,
			NSID:     normalizePMNSID(block.name),
			File:     src.Path,
			Line:     block.startLine,
			Category: category,
		}

		queries, bottlenecks, flow := analyzeBlock(block.content, block.startLine, handler, src.Path)

		cachedCount := 0
		filteredCount := 0
		for _, q := range queries {
			if q.Cached {
				cachedCount++
			}
			if q.Filtered {
				filteredCount++
			}
		}

		sequential := !strings.Contains(block.content, "Promise.all")
		if sequential && len(queries) > 1 {
			bottlenecks = append(bottlenecks, pmBottleneck{
				Handler:  handler.Name,
				NSID:     handler.NSID,
				Type:     "sequential_waterfall",
				Severity: "high",
				Message:  fmt.Sprintf("%d queries executed sequentially without Promise.all", len(queries)),
				File:     src.Path,
				Line:     block.startLine,
				Fix:      "Wrap independent queries in Promise.all([])",
			})
		}

		score := computeHandlerScore(queries, bottlenecks)
		grade := gradeScore(score)

		analyses = append(analyses, pmHandlerAnalysis{
			Handler:       handler,
			Queries:       queries,
			QueryCount:    len(queries),
			CachedCount:   cachedCount,
			FilteredCount: filteredCount,
			Sequential:    sequential && len(queries) > 1,
			Bottlenecks:   bottlenecks,
			Score:         score,
			Grade:         grade,
			Flow:          flow,
		})
	}

	return analyses
}

func pmCategoryFromPath(path string) string {
	base := filepath.Base(path)
	if m := reHandlerFile.FindStringSubmatch(base); m != nil {
		return m[1]
	}
	switch {
	case strings.HasSuffix(path, "/appview/feed.ts"):
		return "feed"
	case strings.HasSuffix(path, "/pds/repo.ts"):
		return "repo"
	case strings.HasSuffix(path, "/pds/server.ts"):
		return "infra"
	case strings.HasSuffix(path, "/gftd/index.ts"):
		return "gftd"
	default:
		return ""
	}
}

func parsePMConsts(lines []string) map[string]string {
	consts := map[string]string{}
	for _, line := range lines {
		s := strings.TrimSpace(line)
		if !strings.HasPrefix(s, "const ") || !strings.Contains(s, "=") {
			continue
		}
		parts := strings.SplitN(strings.TrimPrefix(s, "const "), "=", 2)
		if len(parts) != 2 {
			continue
		}
		name := strings.TrimSpace(parts[0])
		rhs := strings.TrimSpace(strings.TrimSuffix(parts[1], ";"))
		if strings.HasPrefix(rhs, "[") && strings.Contains(rhs, "].join(\".\")") {
			vals := regexp.MustCompile(`"([^"]+)"`).FindAllStringSubmatch(rhs, -1)
			if len(vals) == 0 {
				continue
			}
			parts := make([]string, 0, len(vals))
			for _, v := range vals {
				parts = append(parts, v[1])
			}
			consts[name] = strings.Join(parts, ".")
			continue
		}
		if strings.HasPrefix(rhs, `"`) && strings.HasSuffix(rhs, `"`) && len(rhs) >= 2 {
			consts[name] = strings.Trim(rhs, `"`)
			continue
		}
		if strings.HasPrefix(rhs, "`") && strings.HasSuffix(rhs, "`") && len(rhs) >= 2 {
			v := strings.TrimSuffix(strings.TrimPrefix(rhs, "`"), "`")
			replaced := regexp.MustCompile(`\$\{([A-Za-z0-9_]+)\}`).ReplaceAllStringFunc(v, func(seg string) string {
				m := regexp.MustCompile(`\$\{([A-Za-z0-9_]+)\}`).FindStringSubmatch(seg)
				if len(m) == 2 {
					if cv, ok := consts[m[1]]; ok {
						return cv
					}
				}
				return seg
			})
			consts[name] = replaced
		}
	}
	return consts
}

func extractCaseMethodBlocks(lines []string, consts map[string]string) []pmMethodBlock {
	var out []pmMethodBlock
	resolveCaseExpr := func(raw string) string {
		expr := strings.TrimSpace(raw)
		if strings.HasPrefix(expr, `"`) && strings.HasSuffix(expr, `"`) {
			return strings.Trim(expr, `"`)
		}
		if strings.HasPrefix(expr, `'`) && strings.HasSuffix(expr, `'`) {
			return strings.Trim(expr, `'`)
		}
		if v, ok := consts[expr]; ok {
			return v
		}
		return expr
	}
	for i := 0; i < len(lines); i++ {
		m := reCaseMethod.FindStringSubmatch(lines[i])
		if m == nil {
			continue
		}
		name := resolveCaseExpr(m[1])
		end := len(lines)
		for j := i + 1; j < len(lines); j++ {
			if reCaseMethod.MatchString(lines[j]) || strings.HasPrefix(strings.TrimSpace(lines[j]), "default:") {
				end = j
				break
			}
		}
		out = append(out, pmMethodBlock{
			name:      name,
			startLine: i + 1,
			endLine:   end,
			content:   strings.Join(lines[i:end], "\n"),
		})
	}
	return out
}

func analyzeBlock(content string, baseLineNo int, handler pmHandler, fname string) ([]pmQueryCall, []pmBottleneck, []pmFlowStep) {
	var queries []pmQueryCall
	var bottlenecks []pmBottleneck
	var flow []pmFlowStep

	blockLines := strings.Split(content, "\n")
	inPromiseAll := false
	stepNo := 0

	for i, line := range blockLines {
		lineNo := baseLineNo + i

		if rePromiseAll.MatchString(line) {
			inPromiseAll = true
		}
		if inPromiseAll && strings.Contains(line, "])") {
			inPromiseAll = false
		}

		// buildLabelSql + aiGftdYataSql/Cached
		if m := reQueryLabel.FindStringSubmatch(line); m != nil {
			label := m[1]
			cached := strings.Contains(line, "aiGftdYataSqlCached")

			// Check filter
			filtered := false
			filterStr := ""
			if fm := reQueryLabelFilter.FindStringSubmatch(line); fm != nil {
				filterStr = fm[2]
				filtered = filterStr != ""
			}

			fn := "buildLabelSql"
			if cached {
				fn = "aiGftdYataSqlCached"
			} else {
				fn = "aiGftdYataSql"
			}
			q := pmQueryCall{
				Function: fn,
				Label:    label,
				Cached:   cached,
				Filtered: filtered,
				Filter:   filterStr,
				Line:     lineNo,
			}
			queries = append(queries, q)

			stepNo++
			flow = append(flow, pmFlowStep{
				Step:     stepNo,
				Type:     "sql",
				Function: fn,
				Label:    label,
				Parallel: inPromiseAll,
				Cached:   cached,
				Filtered: filtered,
			})

			// Detect bottlenecks
			if !filtered {
				bottlenecks = append(bottlenecks, pmBottleneck{
					Handler:  handler.Name,
					NSID:     handler.NSID,
					Type:     "unfiltered_scan",
					Severity: "critical",
					Message:  fmt.Sprintf("buildLabelSql(\"%s\") without WHERE filter — full node scan", label),
					File:     fname,
					Line:     lineNo,
					Fix:      fmt.Sprintf("Add filter: buildLabelSql(\"%s\", limit, \"r.updated_at >= ...\")", label),
				})
			}

			if !cached {
				bottlenecks = append(bottlenecks, pmBottleneck{
					Handler:  handler.Name,
					NSID:     handler.NSID,
					Type:     "uncached_query",
					Severity: "medium",
					Message:  fmt.Sprintf("buildLabelSql(\"%s\") not cached — hits yata on every request", label),
					File:     fname,
					Line:     lineNo,
					Fix:      fmt.Sprintf("Use aiGftdYataSqlCached({ sql: buildLabelSql(\"%s\", ...), ttlS: 60 })", label),
				})
			}
		}

		// aiGftdYataSql / aiGftdYataSqlCached with MATCH
		if reCyCall.MatchString(line) || strings.Contains(line, "aiGftdKagamiSql(") || strings.Contains(line, "aiGftdKagamiSqlCached(") {
			cached := strings.Contains(line, "aiGftdYataSqlCached") || strings.Contains(line, "aiGftdKagamiSqlCached")
			filtered := reCyWhere.MatchString(line)
			label := ""
			if m := reCyMatch.FindStringSubmatch(line); m != nil {
				label = m[2]
			}

			stepNo++
			flow = append(flow, pmFlowStep{
				Step:     stepNo,
				Type:     "sql_raw",
				Function: "sql",
				Label:    label,
				Parallel: inPromiseAll,
				Cached:   cached,
				Filtered: filtered,
			})

			if !filtered && label != "" {
				bottlenecks = append(bottlenecks, pmBottleneck{
					Handler:  handler.Name,
					NSID:     handler.NSID,
					Type:     "unfiltered_sql",
					Severity: "high",
					Message:  fmt.Sprintf("MATCH (:%s) without WHERE clause", label),
					File:     fname,
					Line:     lineNo,
					Fix:      "Add WHERE clause with property filter or time range",
				})
			}
		}

		// Raw MATCH without WHERE in direct Sql literals (common timeout trigger).
		if strings.Contains(line, "MATCH (") && !strings.Contains(line, "WHERE") {
			bottlenecks = append(bottlenecks, pmBottleneck{
				Handler:  handler.Name,
				NSID:     handler.NSID,
				Type:     "unfiltered_sql",
				Severity: "high",
				Message:  "MATCH without WHERE in handler query path",
				File:     fname,
				Line:     lineNo,
				Fix:      "Add WHERE predicate or stronger paging constraints",
			})
		}

		// N+1 pattern: await inside for loop
		if strings.Contains(line, "for ") && strings.Contains(line, "{") {
			// Look ahead for await in next 10 lines
			for j := i + 1; j < i+10 && j < len(blockLines); j++ {
				if strings.Contains(blockLines[j], "await ") && (strings.Contains(blockLines[j], "ctx.aiGftdYataSql") || strings.Contains(blockLines[j], "buildLabelSql")) {
					bottlenecks = append(bottlenecks, pmBottleneck{
						Handler:  handler.Name,
						NSID:     handler.NSID,
						Type:     "n_plus_1",
						Severity: "critical",
						Message:  "Sequential await inside for-loop — N+1 query pattern",
						File:     fname,
						Line:     baseLineNo + j,
						Fix:      "Batch into single Sql with WHERE ... IN [...] or use Promise.all",
					})
					break
				}
			}
		}
	}

	return queries, bottlenecks, flow
}

func methodToNSID(method string) string {
	// AppBskyFeedGetTimeline → app.bsky.feed.getTimeline
	if len(method) < 3 {
		return method
	}

	// Known prefixes
	prefixes := []struct {
		prefix string
		nsid   string
	}{
		{"AppBskyFeed", "app.bsky.feed."},
		{"AppBskyActor", "app.bsky.actor."},
		{"AppBskyGraph", "app.bsky.graph."},
		{"AppBskyNotification", "app.bsky.notification."},
		{"AppBskyBookmark", "app.bsky.bookmark."},
		{"ChatBskyConvo", "chat.bsky.convo."},
		{"ComAtprotoRepo", "com.atproto.repo."},
		{"ComAtprotoServer", "com.atproto.server."},
		{"ComAtprotoIdentity", "com.atproto.identity."},
		{"ComAtprotoAdmin", "com.atproto.admin."},
		{"ComAtprotoSync", "com.atproto.sync."},
		{"ComAtprotoLabel", "com.atproto.label."},
		{"AiGftdApps", "ai.gftd.apps."},
		{"AiGftdStream", "ai.gftd.stream."},
		{"AiGftdIdentity", "ai.gftd.identity."},
		{"AiGftdConvo", "ai.gftd.convo."},
		{"AiGftdSignal", "ai.gftd.signal."},
		{"AiGftd", "ai.gftd."},
	}

	for _, p := range prefixes {
		if strings.HasPrefix(method, p.prefix) {
			rest := method[len(p.prefix):]
			if len(rest) > 0 {
				rest = strings.ToLower(rest[:1]) + rest[1:]
			}
			return p.nsid + rest
		}
	}
	return method
}

func normalizePMNSID(name string) string {
	clean := strings.TrimSpace(name)
	clean = regexp.MustCompile(`\$\{[^}]+\}`).ReplaceAllString(clean, "")
	for strings.Contains(clean, "..") {
		clean = strings.ReplaceAll(clean, "..", ".")
	}
	clean = strings.Trim(clean, ".")
	if strings.Contains(clean, ".") {
		return clean
	}
	if strings.Contains(name, ".") {
		return name
	}
	return methodToNSID(clean)
}

func computeHandlerScore(queries []pmQueryCall, bottlenecks []pmBottleneck) float64 {
	if len(queries) == 0 {
		return 100
	}

	score := 100.0
	for _, b := range bottlenecks {
		switch b.Severity {
		case "critical":
			score -= 25
		case "high":
			score -= 15
		case "medium":
			score -= 5
		}
	}
	if score < 0 {
		score = 0
	}
	return score
}

func gradeScore(score float64) string {
	switch {
	case score >= 90:
		return "A"
	case score >= 70:
		return "B"
	case score >= 50:
		return "C"
	case score >= 30:
		return "D"
	default:
		return "F"
	}
}

func computePMSummary(handlers []pmHandlerAnalysis) pmSummary {
	s := pmSummary{TotalHandlers: len(handlers)}
	var scoreSum float64
	var allBottlenecks []pmBottleneck

	for _, h := range handlers {
		s.TotalQueries += h.QueryCount
		s.UnfilteredScans += (h.QueryCount - h.FilteredCount)
		s.UncachedQueries += (h.QueryCount - h.CachedCount)
		if h.Sequential {
			s.SequentialChains++
		}
		scoreSum += h.Score
		for _, b := range h.Bottlenecks {
			switch b.Severity {
			case "critical":
				s.CriticalCount++
			case "high":
				s.HighCount++
			case "medium":
				s.MediumCount++
			}
			allBottlenecks = append(allBottlenecks, b)
		}
	}

	if len(handlers) > 0 {
		s.OverallScore = scoreSum / float64(len(handlers))
	}
	s.OverallGrade = gradeScore(s.OverallScore)

	// Top bottlenecks (critical first, max 10)
	sort.Slice(allBottlenecks, func(i, j int) bool {
		sevOrder := map[string]int{"critical": 0, "high": 1, "medium": 2}
		return sevOrder[allBottlenecks[i].Severity] < sevOrder[allBottlenecks[j].Severity]
	})
	if len(allBottlenecks) > 10 {
		allBottlenecks = allBottlenecks[:10]
	}
	s.TopBottlenecks = allBottlenecks
	return s
}

// ── Output ──

func printPMText(report *pmReport) {
	s := &report.Summary
	fmt.Printf("process-mining: %d handlers, %d queries, score=%.0f grade=%s\n\n",
		s.TotalHandlers, s.TotalQueries, s.OverallScore, s.OverallGrade)

	fmt.Printf("── Issues ──\n")
	fmt.Printf("  unfiltered_scans:  %d\n", s.UnfilteredScans)
	fmt.Printf("  uncached_queries:  %d\n", s.UncachedQueries)
	fmt.Printf("  sequential_chains: %d\n", s.SequentialChains)
	fmt.Printf("  critical:          %d\n", s.CriticalCount)
	fmt.Printf("  high:              %d\n", s.HighCount)
	fmt.Printf("  medium:            %d\n", s.MediumCount)

	fmt.Printf("\n── Handlers ──\n")
	fmt.Printf("%-35s %6s %6s %6s %6s %6s\n", "HANDLER", "QUERY", "CACHE", "FILTR", "SCORE", "GRADE")
	fmt.Printf("%s\n", strings.Repeat("─", 80))
	for _, h := range report.Handlers {
		fmt.Printf("%-35s %6d %6d %6d %6.0f %6s\n",
			h.Handler.Name, h.QueryCount, h.CachedCount, h.FilteredCount, h.Score, h.Grade)
	}

	if len(s.TopBottlenecks) > 0 {
		fmt.Printf("\n── Top Bottlenecks ──\n")
		for _, b := range s.TopBottlenecks {
			fmt.Printf("[%s] %s: %s\n", strings.ToUpper(b.Severity), b.Handler, b.Message)
			fmt.Printf("  → %s (%s:%d)\n", b.Fix, b.File, b.Line)
		}
	}
}

func printFlowDiagram(a *pmHandlerAnalysis) {
	fmt.Printf("Flow: %s (%s)\n", a.Handler.Name, a.Handler.NSID)
	fmt.Printf("  file: %s:%d\n", a.Handler.File, a.Handler.Line)
	fmt.Printf("  queries: %d (cached: %d, filtered: %d)\n", a.QueryCount, a.CachedCount, a.FilteredCount)
	fmt.Printf("  score: %.0f (%s)\n\n", a.Score, a.Grade)

	if len(a.Flow) == 0 {
		fmt.Println("  (no queries detected)")
		return
	}

	inParallel := false
	for _, step := range a.Flow {
		prefix := "  "
		if step.Parallel && !inParallel {
			fmt.Println("  ┌─ Promise.all([")
			inParallel = true
			prefix = "  │  "
		} else if step.Parallel {
			prefix = "  │  "
		} else if !step.Parallel && inParallel {
			fmt.Println("  └─ ])")
			inParallel = false
			prefix = "  "
		}

		cacheTag := "MISS"
		if step.Cached {
			cacheTag = "HIT "
		}
		filterTag := "NO-FILTER"
		if step.Filtered {
			filterTag = "FILTERED "
		}
		label := step.Label
		if label == "" {
			label = "raw"
		}

		fmt.Printf("%s%d. [%s] [%s] %s(:%s)\n", prefix, step.Step, cacheTag, filterTag, step.Function, label)
	}
	if inParallel {
		fmt.Println("  └─ ])")
	}

	if len(a.Bottlenecks) > 0 {
		fmt.Printf("\n  Bottlenecks:\n")
		for _, b := range a.Bottlenecks {
			fmt.Printf("  [%s] %s → %s\n", strings.ToUpper(b.Severity), b.Message, b.Fix)
		}
	}
}
