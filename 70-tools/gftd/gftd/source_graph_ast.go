package main

import (
	"go/ast"
	"go/parser"
	"go/token"
	"regexp"
)

// --- Layer 2: AST-based extraction for Go, TypeScript, Rust ---

// sgASTResult holds auto-extracted facts from source code.
type sgASTResult struct {
	Writes   []string // WRecord/WRecordUpdate/AppBskyFeedPostAs collection kinds
	Reads    []string // G("Label") / Q("table") targets
	Calls    []string // Invoke(did, method) → "did#method"
	Commands []string // app.Command("", "name", ...) names
	Queries  []string // app.Query("", "name", ...) names
	Handlers []string // HandleWCommit handler func names
	HasServe bool     // app.Serve() detected
	Sends    []string // magatama.Send() outbound HTTP targets
	DIDs     []string // DIDCreate(path) paths
	Follows  []string // Follow(did) targets
	Funcs    []sgASTFunc
}

type sgASTFunc struct {
	Name       string
	Line       int
	Writes     []string
	Reads      []string
	Calls      []string
	Commands   []string
}

// --- Go AST extraction (go/ast) ---

func sgExtractGoAST(path string, content []byte) sgASTResult {
	var result sgASTResult

	fset := token.NewFileSet()
	f, err := parser.ParseFile(fset, path, content, parser.ParseComments)
	if err != nil {
		// Fallback to regex if AST parsing fails (e.g. TinyGo edge cases)
		return sgExtractGoRegex(string(content))
	}

	ast.Inspect(f, func(n ast.Node) bool {
		call, ok := n.(*ast.CallExpr)
		if !ok {
			return true
		}

		sel := sgCallSelector(call)
		if sel == "" {
			return true
		}

		switch sel {
		// Write operations
		case "magatama.WRecord", "magatama.WRecordUpdate", "magatama.WRecordDelete":
			if s := sgFirstStringArg(call); s != "" {
				result.Writes = append(result.Writes, s)
			}
		case "magatama.AppBskyFeedPostAs", "magatama.ATPostWithRecord":
			if sel == "magatama.ATPostWithRecord" {
				// ATPostWithRecord(text, collection, rkey)
				if s := sgNthStringArg(call, 1); s != "" {
					result.Writes = append(result.Writes, s)
				}
			}
		case "magatama.DIDCreate":
			if s := sgFirstStringArg(call); s != "" {
				result.DIDs = append(result.DIDs, s)
			}
		case "magatama.DIDWrite":
			if s := sgFirstStringArg(call); s != "" {
				result.DIDs = append(result.DIDs, s)
			}
			if s := sgNthStringArg(call, 1); s != "" {
				result.Writes = append(result.Writes, s)
			}

		// Read operations
		case "magatama.G":
			if s := sgFirstStringArg(call); s != "" {
				result.Reads = append(result.Reads, "sql:"+s)
			}
		case "magatama.GQueryRaw":
			result.Reads = append(result.Reads, "sql:raw")

		// Cross-actor invocation
		case "magatama.Invoke":
			did := sgFirstStringArg(call)
			method := sgNthStringArg(call, 1)
			if did != "" && method != "" {
				result.Calls = append(result.Calls, did+"#"+method)
			}

		// Registration
		case "app.Command":
			if s := sgNthStringArg(call, 1); s != "" {
				result.Commands = append(result.Commands, s)
			}
		case "app.Query":
			if s := sgNthStringArg(call, 1); s != "" {
				result.Queries = append(result.Queries, s)
			}
		case "magatama.HandleWCommit":
			if len(call.Args) > 0 {
				if ident, ok := call.Args[0].(*ast.Ident); ok {
					result.Handlers = append(result.Handlers, ident.Name)
				}
			}
		case "app.Serve":
			result.HasServe = true

		// Outbound
		case "magatama.Send":
			result.Sends = append(result.Sends, "outbound-http")
		case "magatama.Follow":
			if s := sgFirstStringArg(call); s != "" {
				result.Follows = append(result.Follows, s)
			}
		}

		return true
	})

	// Extract per-function breakdown
	for _, decl := range f.Decls {
		fn, ok := decl.(*ast.FuncDecl)
		if !ok {
			continue
		}
		funcResult := sgASTFunc{
			Name: fn.Name.Name,
			Line: fset.Position(fn.Pos()).Line,
		}

		ast.Inspect(fn.Body, func(n ast.Node) bool {
			call, ok := n.(*ast.CallExpr)
			if !ok {
				return true
			}
			sel := sgCallSelector(call)
			switch sel {
			case "magatama.WRecord", "magatama.WRecordUpdate", "magatama.WRecordDelete":
				if s := sgFirstStringArg(call); s != "" {
					funcResult.Writes = append(funcResult.Writes, s)
				}
			case "magatama.G":
				if s := sgFirstStringArg(call); s != "" {
					funcResult.Reads = append(funcResult.Reads, "sql:"+s)
				}
			case "magatama.Invoke":
				did := sgFirstStringArg(call)
				method := sgNthStringArg(call, 1)
				if did != "" && method != "" {
					funcResult.Calls = append(funcResult.Calls, did+"#"+method)
				}
			}
			return true
		})

		if len(funcResult.Writes) > 0 || len(funcResult.Reads) > 0 || len(funcResult.Calls) > 0 {
			result.Funcs = append(result.Funcs, funcResult)
		}
	}

	return result
}

// sgCallSelector extracts "pkg.Func" from a call expression.
func sgCallSelector(call *ast.CallExpr) string {
	switch fn := call.Fun.(type) {
	case *ast.SelectorExpr:
		if x, ok := fn.X.(*ast.Ident); ok {
			return x.Name + "." + fn.Sel.Name
		}
	}
	return ""
}

func sgFirstStringArg(call *ast.CallExpr) string {
	return sgNthStringArg(call, 0)
}

func sgNthStringArg(call *ast.CallExpr, n int) string {
	if n >= len(call.Args) {
		return ""
	}
	lit, ok := call.Args[n].(*ast.BasicLit)
	if !ok || lit.Kind != token.STRING {
		return ""
	}
	s := lit.Value
	if len(s) >= 2 && s[0] == '"' && s[len(s)-1] == '"' {
		return s[1 : len(s)-1]
	}
	return s
}

// sgExtractGoRegex is the fallback when go/ast fails.
func sgExtractGoRegex(content string) sgASTResult {
	var result sgASTResult
	for _, p := range goRegexPatterns {
		matches := p.re.FindAllStringSubmatch(content, -1)
		for _, m := range matches {
			if len(m) < 2 {
				continue
			}
			val := m[1]
			switch p.kind {
			case "write":
				result.Writes = append(result.Writes, val)
			case "read":
				result.Reads = append(result.Reads, val)
			case "command":
				result.Commands = append(result.Commands, val)
			case "serve":
				result.HasServe = true
			case "handler":
				result.Handlers = append(result.Handlers, val)
			}
		}
	}
	return result
}

var goRegexPatterns = []struct {
	re   *regexp.Regexp
	kind string
}{
	{regexp.MustCompile(`magatama\.WRecord(?:Update|Delete)?\("([^"]+)"`), "write"},
	{regexp.MustCompile(`magatama\.ATPostWithRecord\([^,]+,\s*"([^"]+)"`), "write"},
	{regexp.MustCompile(`magatama\.G\("([^"]+)"`), "read"},
	{regexp.MustCompile(`magatama\.Q\("([^"]+)"`), "read"},
	{regexp.MustCompile(`app\.Command\("",\s*"([^"]+)"`), "command"},
	{regexp.MustCompile(`app\.Query\("",\s*"([^"]+)"`), "command"},
	{regexp.MustCompile(`(app\.Serve\(\))`), "serve"},
	{regexp.MustCompile(`magatama\.HandleWCommit\((\w+)\)`), "handler"},
}

// --- TypeScript regex-based AST extraction ---

func sgExtractTSAST(content string) sgASTResult {
	var result sgASTResult

	for _, p := range tsRegexPatterns {
		matches := p.re.FindAllStringSubmatch(content, -1)
		for _, m := range matches {
			if len(m) < 2 {
				continue
			}
			val := m[1]
			switch p.kind {
			case "write":
				result.Writes = append(result.Writes, val)
			case "read_sql":
				result.Reads = append(result.Reads, "sql:"+val)
			case "read_sql_raw":
				result.Reads = append(result.Reads, "sql:raw")
			case "import":
				// Track as a call dependency
			case "xrpc_method":
				result.Commands = append(result.Commands, val)
			case "func":
				result.Funcs = append(result.Funcs, sgASTFunc{Name: val})
			}
		}
	}

	// Extract Sql labels from inline MATCH/OPTIONAL MATCH statements
	// Matches all (var:Label) patterns within Sql strings
	sqlLabelRe := regexp.MustCompile(`\(\w*:(\w+)`)
	// Separate MERGE labels (writes) from MATCH labels (reads)
	mergeBlockRe := regexp.MustCompile(`MERGE\s*\(\w*:(\w+)`)
	for _, m := range mergeBlockRe.FindAllStringSubmatch(content, -1) {
		if len(m) >= 2 {
			result.Writes = append(result.Writes, "sql:"+m[1])
		}
	}

	// All labels in MATCH contexts are reads
	matchBlockRe := regexp.MustCompile(`(?:MATCH|WHERE|WITH|RETURN)\s[^;]*`)
	for _, block := range matchBlockRe.FindAllString(content, -1) {
		for _, m := range sqlLabelRe.FindAllStringSubmatch(block, -1) {
			if len(m) >= 2 {
				result.Reads = append(result.Reads, "sql:"+m[1])
			}
		}
	}

	// Deduplicate
	result.Reads = sgDedup(result.Reads)
	result.Writes = sgDedup(result.Writes)

	return result
}

var tsRegexPatterns = []struct {
	re   *regexp.Regexp
	kind string
}{
	// Sql RPC calls: sql(`MATCH ...`, appId), mutate(`MERGE ...`, appId)
	{regexp.MustCompile(`\.sql\(\s*` + "`" + `([^` + "`" + `]+)` + "`"), "read_sql_raw"},
	{regexp.MustCompile(`\.mutate\(\s*` + "`" + `([^` + "`" + `]+)` + "`"), "write"},
	// Import tracking
	{regexp.MustCompile(`import\s+.*\s+from\s+["']([^"']+)["']`), "import"},
	// XRPC method handlers: case "MethodName":
	{regexp.MustCompile(`case\s+"(\w+)":\s*(?:return|{\s*)`), "xrpc_method"},
	// Async function exports
	{regexp.MustCompile(`(?:export\s+)?async\s+function\s+(\w+)`), "func"},
	// createRecord/mergeRecord calls with collection arg
	{regexp.MustCompile(`createRecord\([^,]*,\s*"([^"]+)"`), "write"},
	{regexp.MustCompile(`mergeRecord\([^,]*,\s*"([^"]+)"`), "write"},
}

// --- Rust regex-based AST extraction ---

func sgExtractRustAST(content string) sgASTResult {
	var result sgASTResult

	for _, p := range rustRegexPatterns {
		matches := p.re.FindAllStringSubmatch(content, -1)
		for _, m := range matches {
			if len(m) < 2 {
				continue
			}
			val := m[1]
			switch p.kind {
			case "write":
				result.Writes = append(result.Writes, val)
			case "read":
				result.Reads = append(result.Reads, "sql:"+val)
			case "command":
				result.Commands = append(result.Commands, val)
			case "query":
				result.Queries = append(result.Queries, val)
			case "serve":
				result.HasServe = true
			case "invoke":
				result.Calls = append(result.Calls, val)
			case "did_create":
				result.DIDs = append(result.DIDs, val)
			case "follow":
				result.Follows = append(result.Follows, val)
			case "func":
				result.Funcs = append(result.Funcs, sgASTFunc{Name: val})
			case "handler":
				result.Handlers = append(result.Handlers, val)
			}
		}
	}

	// Extract capability tags from CommandOption::WithCapabilityTags
	capRe := regexp.MustCompile(`WithCapabilityTags\(vec!\[((?:"[^"]+(?:"\.into\(\))?[^"]*)+)\]`)
	for _, m := range capRe.FindAllStringSubmatch(content, -1) {
		if len(m) >= 2 {
			// Extract individual tag strings
			tagRe := regexp.MustCompile(`"([^"]+)"`)
			for _, tm := range tagRe.FindAllStringSubmatch(m[1], -1) {
				if len(tm) >= 2 {
					result.Commands = append(result.Commands, "cap:"+tm[1])
				}
			}
		}
	}

	return result
}

var rustRegexPatterns = []struct {
	re   *regexp.Regexp
	kind string
}{
	// W Protocol Event Stream writes
	{regexp.MustCompile(`w_record\(\s*"([^"]+)"`), "write"},
	{regexp.MustCompile(`w_record_update\(\s*"([^"]+)"`), "write"},
	{regexp.MustCompile(`at_post_as\(\s*"([^"]+)"`), "write"},
	// magatama_rs SDK calls (method style)
	{regexp.MustCompile(`\.w_record\(\s*"([^"]+)"`), "write"},
	{regexp.MustCompile(`WRecord\(\s*"([^"]+)"`), "write"},
	{regexp.MustCompile(`WRecordUpdate\(\s*"([^"]+)"`), "write"},

	// Reads
	{regexp.MustCompile(`\.g\(\s*"([^"]+)"`), "read"},
	{regexp.MustCompile(`\.q\(\s*"([^"]+)"`), "read"},
	{regexp.MustCompile(`G\(\s*"([^"]+)"`), "read"},
	{regexp.MustCompile(`Q\(\s*"([^"]+)"`), "read"},

	// Command/Query registration
	{regexp.MustCompile(`app\.command\(\s*"[^"]*",\s*"([^"]+)"`), "command"},
	{regexp.MustCompile(`app\.query\(\s*"[^"]*",\s*"([^"]+)"`), "query"},

	// Serve (capture group needed for match handler)
	{regexp.MustCompile(`(app\.serve\(\))`), "serve"},
	{regexp.MustCompile(`(\.serve\(\))`), "serve"},

	// Cross-actor invoke
	{regexp.MustCompile(`invoke\(\s*"([^"]+)"\s*,\s*"([^"]+)"`), "invoke"},

	// DID operations
	{regexp.MustCompile(`did_create\(\s*"([^"]+)"`), "did_create"},
	{regexp.MustCompile(`DIDCreate\(\s*"([^"]+)"`), "did_create"},

	// Follow
	{regexp.MustCompile(`follow\(\s*"([^"]+)"`), "follow"},

	// Function definitions
	{regexp.MustCompile(`(?:pub\s+)?(?:async\s+)?fn\s+(\w+)\s*[<(]`), "func"},

	// HandleWCommit
	{regexp.MustCompile(`handle_w_commit\((\w+)\)`), "handler"},
	{regexp.MustCompile(`HandleWCommit\((\w+)\)`), "handler"},
}

// --- Helpers ---

func sgDedup(ss []string) []string {
	seen := make(map[string]bool, len(ss))
	out := make([]string, 0, len(ss))
	for _, s := range ss {
		if !seen[s] {
			seen[s] = true
			out = append(out, s)
		}
	}
	return out
}

// sgMergeASTIntoNode merges AST-extracted facts into an existing sgSourceNode.
// AST facts are authoritative for writes/reads/commands; @gftd: directives are kept for intent.
func sgMergeASTIntoNode(node *sgSourceNode, astResult sgASTResult) {
	node.Writes = sgMergeStrings(node.Writes, astResult.Writes)
	node.Reads = sgMergeStrings(node.Reads, astResult.Reads)
	node.Calls = sgMergeStrings(node.Calls, astResult.Calls)
}

func sgMergeStrings(a, b []string) []string {
	if len(b) == 0 {
		return a
	}
	seen := make(map[string]bool, len(a))
	for _, s := range a {
		seen[s] = true
	}
	merged := append([]string(nil), a...)
	for _, s := range b {
		if !seen[s] {
			merged = append(merged, s)
			seen[s] = true
		}
	}
	return merged
}
