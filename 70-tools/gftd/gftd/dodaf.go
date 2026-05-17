// dodaf.go — DoDAF v2-aligned Rule Registry (Parquet + DuckDB + MCP)
//
// Stores all Claude-facing rules, constraints, lexicon, and activity policies as
// structured Parquet data queryable by file context and tag.
//
// DoDAF v2 view mapping:
//
//	AV-2  Integrated Dictionary  → av2_dictionary.parquet
//	TV-1  Technical Standards    → tv1_standards.parquet    (constraints/rules)
//	OV-5  Operational Activity   → ov5_activities.parquet   (permitted/prohibited)
//
// Storage: 80-data/dodaf/{view}.parquet (DuckDB-queryable, ZSTD compressed)
//
// MCP surface: gftd.dodaf.tv1.query / gftd.dodaf.av2.get / gftd.dodaf.rules.context
// → Seeded to kagami via: gftd dodaf seed
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ── Types ──────────────────────────────────────────────────────────────────

// dodafTV1Row is one row in tv1_standards.parquet (TV-1: Technical Standards).
type dodafTV1Row struct {
	ID           string   `json:"id"`
	Title        string   `json:"title"`
	View         string   `json:"view"`
	StandardRef  string   `json:"standard_ref"`
	Rule         string   `json:"rule"`
	Severity     string   `json:"severity"`
	Permitted    bool     `json:"permitted"`
	ScopeFolders []string `json:"scope_folders"`
	ScopeTags    []string `json:"scope_tags"`
	ScopeExts    []string `json:"scope_exts"`
	Evidence     string   `json:"evidence"`
	Status       string   `json:"status"`
	Source       string   `json:"source"`
	CreatedAt    string   `json:"created_at"`
}

// dodafAV2Row is one row in av2_dictionary.parquet (AV-2: Integrated Dictionary).
type dodafAV2Row struct {
	ID         string   `json:"id"`
	Term       string   `json:"term"`
	Definition string   `json:"definition"`
	Aliases    []string `json:"aliases"`
	Domain     string   `json:"domain"`
	ScopeTags  []string `json:"scope_tags"`
	Source     string   `json:"source"`
	Status     string   `json:"status"`
	CreatedAt  string   `json:"created_at"`
}

// dodafOV5Row is one row in ov5_activities.parquet (OV-5: Operational Activity).
type dodafOV5Row struct {
	ID        string   `json:"id"`
	Action    string   `json:"action"`
	Permitted bool     `json:"permitted"`
	Reason    string   `json:"reason"`
	ScopeTags []string `json:"scope_tags"`
	AltAction string   `json:"alt_action"`
	Source    string   `json:"source"`
	CreatedAt string   `json:"created_at"`
}

// ── Seed data ──────────────────────────────────────────────────────────────

func dodafSeedTV1() []dodafTV1Row {
	now := time.Now().UTC().Format(time.RFC3339)
	return []dodafTV1Row{
		{
			ID: "cf-wasm-no-dynamic-compile", View: "TV-1",
			Title:       "CF Workers: WebAssembly.compile() blocked at runtime",
			StandardRef: "Cloudflare Workers V8 embedder policy",
			Rule:        "WebAssembly.compile(bytes) called at request time returns CompileError: 'Wasm code generation disallowed by embedder'. Only static WASM imports via CompiledWasm wrangler rule (import MODULE from '*.wasm') are supported. New contract = new worker deploy.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/", "_archive/30-graph/kagami-live-260414/wasm/"},
			ScopeTags:    []string{"cloudflare", "wasm", "assemblyscript"},
			ScopeExts:    []string{".ts", ".wasm", ".jsonc"},
			Evidence:     "h0g3t3st.etzhayyim.com/xrpc/ai.gftd.apps.hoge.wasmEval — validated 2026-04-08",
			Status:       "[PRODUCTION]",
			Source:       "60-apps/ai-gftd-project-hoge/appview/src/index.ts",
			CreatedAt:    now,
		},
		{
			ID: "cf-wasm-static-import-ok", View: "TV-1",
			Title:       "CF Workers: static WASM import via CompiledWasm rule works",
			StandardRef: "Cloudflare Workers CompiledWasm rule",
			Rule:        "Static WASM import (import MODULE from '*.wasm') with CompiledWasm wrangler rule ('rules':[{type:'CompiledWasm',globs:['**/*.wasm']}]) works correctly. new WebAssembly.Instance(MODULE, imports) per-request instantiation is ~0ms.",
			Severity:    "info", Permitted: true,
			ScopeFolders: []string{"60-apps/", "_archive/30-graph/kagami-live-260414/wasm/"},
			ScopeTags:    []string{"cloudflare", "wasm", "assemblyscript"},
			ScopeExts:    []string{".ts", ".jsonc"},
			Evidence:     "h0g3t3st.etzhayyim.com/xrpc/ai.gftd.apps.hoge.wasmTest — add=7,fib=55,sum=5050,mul=42 validated 2026-04-08",
			Status:       "[PRODUCTION]",
			Source:       "60-apps/ai-gftd-project-hoge/appview/src/index.ts",
			CreatedAt:    now,
		},
		{
			ID: "cf-worker-no-kv", View: "TV-1",
			Title:       "CF Workers: KV usage prohibited",
			StandardRef: "W Protocol Event Stream architecture",
			Rule:        "magatama.KvGet() / magatama.KvPut() are prohibited. All data must flow through W Protocol Event Stream (ComAtprotoRepoCreateRecord / Preferences). Use PDS_SERVICE service binding for all data access.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/"},
			ScopeTags:    []string{"cloudflare", "typescript", "magatama"},
			ScopeExts:    []string{".ts"},
			Evidence:     "70-tools/gftd/gftd/code_quality.go kv-usage rule",
			Status:       "[PRODUCTION]",
			Source:       "60-apps/CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "cf-worker-pds-gateway-only", View: "TV-1",
			Title:       "CF Workers: all data access via PDS_SERVICE binding only",
			StandardRef: "PDS Gateway Pattern",
			Rule:        "App Workers must use env.PDS_SERVICE service binding for all data access. Direct graph RPC binding in app Workers is prohibited. globalThis.fetch() to llm.etzhayyim.com or other internal services is prohibited. Data path: App Worker → env.PDS_SERVICE → PDS Worker → graph SQL path → RisingWave.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/"},
			ScopeTags:    []string{"cloudflare", "typescript", "magatama", "pds"},
			ScopeExts:    []string{".ts", ".jsonc"},
			Evidence:     "50-infra/CLAUDE.md §PDS Gateway Pattern",
			Status:       "[PRODUCTION]",
			Source:       "50-infra/CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "xrpc-sole-api", View: "TV-1",
			Title:       "XRPC (/xrpc/{NSID}) is the sole external API surface",
			StandardRef: "AT Protocol XRPC standard",
			Rule:        "All public API endpoints must use /xrpc/{NSID} format (AT Protocol native). REST endpoints for business mutations are prohibited. Duplicate public contract paths are prohibited. Internal path: PDS_SERVICE RPC.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/", "50-infra/"},
			ScopeTags:    []string{"at-protocol", "xrpc", "typescript"},
			ScopeExts:    []string{".ts"},
			Evidence:     "CLAUDE.md root §XRPC = sole API",
			Status:       "[PRODUCTION]",
			Source:       "CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "shannon-redundancy-prohibition", View: "TV-1",
			Title:       "Shannon Redundancy Prohibition: single source of truth",
			StandardRef: "Shannon information theory",
			Rule:        "Each rule/fact must appear in exactly one location in the hierarchy. Copying the same rule to multiple CLAUDE.md files is prohibited (entropy=0). Stale comments are prohibited. Dead code '// removed' comments are prohibited. After editing, verify no parent-child duplication.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{},
			ScopeTags:    []string{"claude", "docs", "code-review"},
			ScopeExts:    []string{".md", ".ts", ".go"},
			Evidence:     "CLAUDE.md root §CRITICAL: Shannon Redundancy Prohibition",
			Status:       "[PRODUCTION]",
			Source:       "CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "at-protocol-repo-always-public", View: "TV-1",
			Title:       "AT Protocol: Repo records are always public (federable)",
			StandardRef: "AT Protocol specification",
			Rule:        "AT Protocol Repo records (created via ComAtprotoRepoCreateRecord) are always public and federable. PII, financial data, and user config must use Preferences() (server-side, NOT in Repo). Never write PII to createRecord. E2E = signal:v1:{ciphertext} field encryption (W Protocol extension).",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/"},
			ScopeTags:    []string{"at-protocol", "privacy", "typescript"},
			ScopeExts:    []string{".ts"},
			Evidence:     "CLAUDE.md root §AT Protocol Faithful Public/Private",
			Status:       "[PRODUCTION]",
			Source:       "CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "write-only-derived-architecture", View: "TV-1",
			Title:       "Write-Only Derived Architecture: handlers write only (η=100%)",
			StandardRef: "260407-write-only-derived-architecture-design.md",
			Rule:        "Handlers must only call writePublic() or writePrivate(). Calling postFeed(), sdk.hostImports.invoke(), or sdk.hostImports.appBskyFeedPost() inside a handler is prohibited. Social posts, tool invocations, and notifications are auto-derived by the PDS commit pipeline via magatama.jsonld 'derive' rules.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/"},
			ScopeTags:    []string{"at-protocol", "typescript", "magatama", "design-e"},
			ScopeExts:    []string{".ts", ".jsonld"},
			Evidence:     "90-docs/260407-write-only-derived-architecture-design.md",
			Status:       "[PRODUCTION]",
			Source:       "CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "no-synthetic-data-production", View: "TV-1",
			Title:       "No synthetic data in production API responses",
			StandardRef: "Shannon information theory — entropy=0 for fabricated data",
			Rule:        "200 OK responses must only contain data that actually exists in the graph/DB. Empty graph query → empty array. Unknown author/DID → empty string (never fake DID like 'unknown.etzhayyim.com'). 0 results → 0 results (no hardcoded list). Not found → 404 (never return fake record as 200). Prohibited patterns: buildSynthetic*, SEED_* hardcoded lists, fallbackSeeds, catch block returning fabricated data.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/", "50-infra/"},
			ScopeTags:    []string{"typescript", "api", "data-integrity"},
			ScopeExts:    []string{".ts"},
			Evidence:     "CLAUDE.md root §CRITICAL: No Synthetic Data in Production Responses",
			Status:       "[PRODUCTION]",
			Source:       "CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "cf-wasm-component-model-not-supported", View: "TV-1",
			Title:       "CF Workers: WASM Component Model is not supported",
			StandardRef: "Cloudflare Workers V8 runtime",
			Rule:        "WASM Component Model (WIT-based components, wasmtime component instantiation) does NOT work on Cloudflare Workers (V8-based). Only basic WASM modules are supported. Use AssemblyScript for pure numeric WASM contracts on CF Workers.",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/", "_archive/30-graph/kagami-live-260414/wasm/"},
			ScopeTags:    []string{"cloudflare", "wasm", "assemblyscript"},
			ScopeExts:    []string{".wasm", ".wit", ".ts"},
			Evidence:     "Codebase search: zero Component Model usage in CF Workers workers — 2026-04-08",
			Status:       "[PRODUCTION]",
			Source:       "CLAUDE.md",
			CreatedAt:    now,
		},
		{
			ID: "do-sqlite-prohibited", View: "TV-1",
			Title:       "CF Workers: Durable Object SQLite is prohibited",
			StandardRef: "W Protocol Event Stream architecture",
			Rule:        "DurableObjectState.storage.sql / durable-object-sql WIT / raw DO-sql-exec() direct calls are prohibited. DO is used for alarm + browser rendering only. All data goes through W Protocol Event Stream (PDS → graph SQL path → RisingWave).",
			Severity:    "critical", Permitted: false,
			ScopeFolders: []string{"60-apps/", "50-infra/"},
			ScopeTags:    []string{"cloudflare", "typescript", "durable-objects"},
			ScopeExts:    []string{".ts"},
			Evidence:     "70-tools/gftd/gftd/code_quality.go dosqlexec rule",
			Status:       "[PRODUCTION]",
			Source:       "60-apps/CLAUDE.md",
			CreatedAt:    now,
		},
	}
}

func dodafSeedAV2() []dodafAV2Row {
	now := time.Now().UTC().Format(time.RFC3339)
	return []dodafAV2Row{
		{
			ID: "compiled-wasm", Term: "CompiledWasm",
			Definition: "Wrangler rule that converts .wasm ESM imports into WebAssembly.Module at bundle time. Declared in wrangler.jsonc as {\"rules\":[{\"type\":\"CompiledWasm\",\"globs\":[\"**/*.wasm\"]}]}. Allows static import of WASM modules that are instantiated per-request.",
			Aliases:    []string{"CompiledWasm rule", "wasm static import"},
			Domain:     "cloudflare",
			ScopeTags:  []string{"cloudflare", "wasm"},
			Source:     "60-apps/ai-gftd-project-hoge/appview/wrangler.jsonc",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "magatama-app", Term: "App",
			Definition: "TS Native Cloudflare Worker app using @gftd/magatama-host-sdk with WIT contracts. Single-file architecture (src/app.ts). Deployed as account-level Worker with {nanoid}.etzhayyim.com/* route. createWorkerExport() is the entry point.",
			Aliases:    []string{"magatama", "TS native app", "magatama component"},
			Domain:     "platform",
			ScopeTags:  []string{"typescript", "cloudflare", "magatama"},
			Source:     "20-actors/magatama/CLAUDE.md",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "xrpc", Term: "XRPC",
			Definition: "AT Protocol Remote Procedure Call format. All public APIs use /xrpc/{NSID} path. NSID format: {namespace}.{method} in camelCase (e.g. ai.gftd.apps.hoge.wasmTest). XRPC is the sole external API surface — no REST endpoints for business logic.",
			Aliases:    []string{"XRPC", "AT Protocol RPC", "/xrpc/"},
			Domain:     "at-protocol",
			ScopeTags:  []string{"at-protocol", "xrpc", "api"},
			Source:     "10-protocol/wproto/xrpc/",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "kagami", Term: "kagami",
			Definition: "Graph query layer using RisingWave + Hyperdrive. P10v2 typed columnar schema (1 AT record = 1 row). Sql transpilation is archived. Accessed through the graph SQL path from the PDS Worker.",
			Aliases:    []string{"graph SQL path", "Hyperdrive"},
			Domain:     "infrastructure",
			ScopeTags:  []string{"graph-db", "duckdb", "parquet"},
			Source:     "_archive/30-graph/kagami-live-260414/CLAUDE.md",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "nanoid-did", Term: "nanoid DID",
			Definition: "Canonical DID format: did:web:{nanoid}.etzhayyim.com. AT Protocol repo always uses nanoid DID. Vanity domain (e.g. hoge.etzhayyim.com) is a handle/alias only — never used as repo DID. PDS normalizes writes via normalizeRepoToNanoidDid().",
			Aliases:    []string{"canonical DID", "did:web:{nanoid}.etzhayyim.com"},
			Domain:     "at-protocol",
			ScopeTags:  []string{"at-protocol", "did", "identity"},
			Source:     "50-infra/CLAUDE.md §Canonical DID",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "w-protocol", Term: "W Protocol",
			Definition: "AT Protocol superset extending AT Protocol with Signal Protocol E2E encryption, WIT contracts, wRPC streaming, and Multi-DID per actor. All entities have AI Agent DIDs. Federable with AT Protocol network.",
			Aliases:    []string{"W Protocol", "wproto"},
			Domain:     "protocol",
			ScopeTags:  []string{"at-protocol", "w-protocol", "protocol"},
			Source:     "10-protocol/wproto/CLAUDE.md",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "pds-service", Term: "PDS_SERVICE",
			Definition: "Cloudflare Workers service binding from App Worker to PDS Worker. The sole data gateway for all read/write operations. Exposes: createRecord(), query(), batchImport(), updateRecord(), deleteRecord(), uploadBlob(). Direct graph RPC binding in app Workers is prohibited.",
			Aliases:    []string{"PDS_SERVICE binding", "env.PDS_SERVICE"},
			Domain:     "infrastructure",
			ScopeTags:  []string{"cloudflare", "pds", "service-binding"},
			Source:     "50-infra/CLAUDE.md §PDS Gateway Pattern",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "shannon-score", Term: "Shannon entropy score",
			Definition: "H = -Σ p(x)·log₂(p(x)). In the platform context: measures information density of code/docs (η=1 means no redundancy). Applied to: CLAUDE.md rules (single source of truth), code coupling (DSM), uncertainty propagation (BayesNet), throughput bottlenecks, implementation cost. Tools: gftd shannon, gftd mokuteki.",
			Aliases:    []string{"Shannon entropy", "η", "information entropy"},
			Domain:     "information-theory",
			ScopeTags:  []string{"shannon", "metrics", "docs"},
			Source:     "70-tools/gftd/CLAUDE.md §gftd shannon",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
		{
			ID: "dodaf-v2", Term: "DoDAF v2",
			Definition: "Department of Defense Architecture Framework version 2. Viewpoints: AV (All View), OV (Operational View), SV (Systems View), TV (Technical Standards View), CV (Capability View). Used for: AV-2 Integrated Dictionary (lexicon), TV-1 Technical Standards (constraints), OV-5 Operational Activities (permitted/prohibited). gftd dodaf implements a Parquet-based DoDAF v2 rule registry.",
			Aliases:    []string{"DoDAF", "Department of Defense Architecture Framework"},
			Domain:     "architecture",
			ScopeTags:  []string{"dodaf", "architecture", "docs"},
			Source:     "70-tools/gftd/gftd/dodaf.go",
			Status:     "[PRODUCTION]", CreatedAt: now,
		},
	}
}

func dodafSeedOV5() []dodafOV5Row {
	now := time.Now().UTC().Format(time.RFC3339)
	return []dodafOV5Row{
		{
			ID: "ov5-wasm-static-import", Action: "import MODULE from '*.wasm' (CompiledWasm rule)",
			Permitted: true, Reason: "Bundled at deploy time by wrangler CompiledWasm rule. Works on CF Workers V8.",
			ScopeTags: []string{"cloudflare", "wasm"}, AltAction: "",
			Source: "60-apps/ai-gftd-project-hoge/appview/src/index.ts", CreatedAt: now,
		},
		{
			ID: "ov5-wasm-dynamic-compile", Action: "WebAssembly.compile(userBytes) at request time",
			Permitted: false, Reason: "Blocked by CF Workers V8 embedder: 'Wasm code generation disallowed by embedder'.",
			ScopeTags: []string{"cloudflare", "wasm"}, AltAction: "Pre-bundle WASM at deploy time via CompiledWasm rule",
			Source: "60-apps/ai-gftd-project-hoge/appview/src/index.ts", CreatedAt: now,
		},
		{
			ID: "ov5-kv-usage", Action: "KvGet() / KvPut() in App",
			Permitted: false, Reason: "KV bypasses W Protocol Event Stream. All data must flow through PDS_SERVICE.",
			ScopeTags: []string{"cloudflare", "magatama"}, AltAction: "sdk.pds.createRecord() for write, sdk.graph.query() for read",
			Source: "60-apps/CLAUDE.md", CreatedAt: now,
		},
		{
			ID: "ov5-synthetic-200", Action: "Return fabricated data in 200 OK response",
			Permitted: false, Reason: "No synthetic data principle: 200 OK must only contain data that exists in graph/DB.",
			ScopeTags: []string{"api", "data-integrity"}, AltAction: "Return empty array [] or 404 when data does not exist",
			Source: "CLAUDE.md", CreatedAt: now,
		},
		{
			ID: "ov5-pds-direct-fetch", Action: "globalThis.fetch('https://atproto.etzhayyim.com/...')",
			Permitted: false, Reason: "Direct HTTP to PDS from App Worker bypasses service binding RPC. same-zone fetch() is prohibited.",
			ScopeTags: []string{"cloudflare", "pds"}, AltAction: "env.PDS_SERVICE.query() or env.PDS_SERVICE.createRecord()",
			Source: "50-infra/CLAUDE.md", CreatedAt: now,
		},
		{
			ID: "ov5-shannon-copy-paste-rule", Action: "Copy a rule from parent CLAUDE.md into child CLAUDE.md",
			Permitted: false, Reason: "Shannon Redundancy Prohibition: each rule lives in exactly one location. Duplication = entropy=0.",
			ScopeTags: []string{"docs", "claude"}, AltAction: "Write a 1-line pointer to the authoritative source in the child CLAUDE.md",
			Source: "CLAUDE.md", CreatedAt: now,
		},
	}
}

// ── Helper: resolve data directory ────────────────────────────────────────

func dodafDataDir(wsRoot string) string {
	return filepath.Join(wsRoot, "80-data", "dodaf")
}

func dodafParquetPath(wsRoot, view string) string {
	return filepath.Join(dodafDataDir(wsRoot), view+".parquet")
}

// writeJSONToParquet marshals rows as JSON array, then converts to Parquet via DuckDB.
func writeJSONToParquet(rows interface{}, parquetPath string) error {
	dir := filepath.Dir(parquetPath)
	if err := os.MkdirAll(dir, 0755); err != nil {
		return fmt.Errorf("mkdir: %w", err)
	}
	tmpJSON := parquetPath + ".tmp.json"
	b, err := json.Marshal(rows)
	if err != nil {
		return fmt.Errorf("json marshal: %w", err)
	}
	if err := os.WriteFile(tmpJSON, b, 0644); err != nil {
		return fmt.Errorf("write json: %w", err)
	}
	defer os.Remove(tmpJSON)

	sql := fmt.Sprintf(
		`COPY (SELECT * FROM read_json_auto('%s')) TO '%s' (FORMAT PARQUET, COMPRESSION ZSTD);`,
		tmpJSON, parquetPath,
	)
	cmd := exec.Command("duckdb", "-c", sql)
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("duckdb parquet write: %w", err)
	}
	return nil
}

// duckdbQuery runs a SELECT and streams output to stdout.
func duckdbQuery(sql string) error {
	cmd := exec.Command("duckdb", "-c", sql)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// duckdbQueryJSON runs a SELECT and returns JSON rows.
func duckdbQueryJSON(sql string) ([]map[string]interface{}, error) {
	tmpOut := fmt.Sprintf("/tmp/dodaf-query-%d.json", time.Now().UnixNano())
	defer os.Remove(tmpOut)

	wrapSQL := fmt.Sprintf(`COPY (%s) TO '%s' (FORMAT JSON);`, strings.TrimRight(strings.TrimSpace(sql), ";"), tmpOut)
	cmd := exec.Command("duckdb", "-c", wrapSQL)
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return nil, fmt.Errorf("duckdb query: %w", err)
	}
	b, err := os.ReadFile(tmpOut)
	if err != nil {
		return nil, fmt.Errorf("read json output: %w", err)
	}
	// DuckDB JSON output: newline-delimited JSON objects
	var rows []map[string]interface{}
	for _, line := range strings.Split(strings.TrimSpace(string(b)), "\n") {
		if line == "" {
			continue
		}
		var row map[string]interface{}
		if err := json.Unmarshal([]byte(line), &row); err == nil {
			rows = append(rows, row)
		}
	}
	return rows, nil
}

// ── Subcommands ────────────────────────────────────────────────────────────

// runDodaf dispatches gftd dodaf subcommands.
func runDodaf(args []string) error {
	if len(args) == 0 {
		fmt.Fprintf(os.Stderr, `gftd dodaf — DoDAF v2-aligned Rule Registry

SUBCOMMANDS:
  init                   Initialize Parquet files with seed data (TV-1, AV-2, OV-5)
  tv1 query              Query TV-1 technical standards/constraints
  av2 get <term>         Look up AV-2 integrated dictionary entry
  rules context          All-views context query (by file path and/or tags)
  add                    Add a new entry to a DoDAF view
  validate               Check CLAUDE.md for rules not yet in registry
  migrate [--dry-run]    Extract all ## CRITICAL: sections → Parquet, replace body with pointer
  seed                   Push registry to kagami (enables MCP gftd.dodaf.* tools)
`)
		return nil
	}
	switch args[0] {
	case "init":
		return runDodafInit(args[1:])
	case "tv1":
		if len(args) < 2 {
			return fmt.Errorf("usage: gftd dodaf tv1 <query>")
		}
		switch args[1] {
		case "query":
			return runDodafTV1Query(args[2:])
		default:
			return fmt.Errorf("unknown tv1 subcommand: %s", args[1])
		}
	case "av2":
		if len(args) < 2 {
			return fmt.Errorf("usage: gftd dodaf av2 <get>")
		}
		switch args[1] {
		case "get":
			return runDodafAV2Get(args[2:])
		default:
			return fmt.Errorf("unknown av2 subcommand: %s", args[1])
		}
	case "rules":
		if len(args) < 2 {
			return fmt.Errorf("usage: gftd dodaf rules <context>")
		}
		switch args[1] {
		case "context":
			return runDodafRulesContext(args[2:])
		default:
			return fmt.Errorf("unknown rules subcommand: %s", args[1])
		}
	case "add":
		return runDodafAdd(args[1:])
	case "validate":
		return runDodafValidate(args[1:])
	case "migrate":
		return runDodafMigrate(args[1:])
	case "seed":
		return runDodafSeedKagami(args[1:])
	default:
		return fmt.Errorf("unknown dodaf subcommand: %s", args[0])
	}
}

// runDodafInit creates the initial Parquet files with seed data.
func runDodafInit(args []string) error {
	fs := flag.NewFlagSet("dodaf init", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	force := fs.Bool("force", false, "overwrite existing Parquet files")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}

	writes := []struct {
		view string
		path string
		fn   func() interface{}
	}{
		{"tv1_standards", dodafParquetPath(wsRoot, "tv1_standards"), func() interface{} { return dodafSeedTV1() }},
		{"av2_dictionary", dodafParquetPath(wsRoot, "av2_dictionary"), func() interface{} { return dodafSeedAV2() }},
		{"ov5_activities", dodafParquetPath(wsRoot, "ov5_activities"), func() interface{} { return dodafSeedOV5() }},
	}

	for _, w := range writes {
		if !*force {
			if _, err := os.Stat(w.path); err == nil {
				fmt.Fprintf(os.Stderr, "skip (exists): %s — use --force to overwrite\n", w.path)
				continue
			}
		}
		fmt.Fprintf(os.Stderr, "writing %s → %s\n", w.view, w.path)
		if err := writeJSONToParquet(w.fn(), w.path); err != nil {
			return fmt.Errorf("%s: %w", w.view, err)
		}
		fmt.Fprintf(os.Stderr, "ok: %s\n", w.path)
	}
	fmt.Fprintf(os.Stderr, "\nDone. Query with:\n")
	fmt.Fprintf(os.Stderr, "  gftd dodaf tv1 query --tags cloudflare,wasm\n")
	fmt.Fprintf(os.Stderr, "  gftd dodaf av2 get CompiledWasm\n")
	fmt.Fprintf(os.Stderr, "  gftd dodaf rules context --path src/index.ts --tags cloudflare\n")
	return nil
}

// runDodafTV1Query queries TV-1 technical standards by tags, path, or severity.
func runDodafTV1Query(args []string) error {
	fs := flag.NewFlagSet("dodaf tv1 query", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	tags := fs.String("tags", "", "comma-separated tags to filter (e.g. cloudflare,wasm)")
	path := fs.String("path", "", "file path for scope matching")
	severity := fs.String("severity", "", "filter by severity: critical|high|medium|info")
	permitted := fs.String("permitted", "", "filter by permitted: true|false")
	jsonOut := fs.Bool("json", false, "output as JSON")
	_ = fs.String("data-dir", "", "data directory (default: <workspace>/80-data/dodaf)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}
	parquetFile := dodafParquetPath(wsRoot, "tv1_standards")
	if _, err := os.Stat(parquetFile); err != nil {
		return fmt.Errorf("tv1_standards.parquet not found — run: gftd dodaf init")
	}

	var conditions []string
	if *severity != "" {
		conditions = append(conditions, fmt.Sprintf("severity = '%s'", strings.ReplaceAll(*severity, "'", "''")))
	}
	if *permitted != "" {
		val := "true"
		if *permitted == "false" {
			val = "false"
		}
		conditions = append(conditions, fmt.Sprintf("permitted = %s", val))
	}
	if *tags != "" {
		for _, tag := range strings.Split(*tags, ",") {
			tag = strings.TrimSpace(tag)
			if tag != "" {
				conditions = append(conditions, fmt.Sprintf("list_contains(scope_tags, '%s')", strings.ReplaceAll(tag, "'", "''")))
			}
		}
	}
	if *path != "" {
		conditions = append(conditions, fmt.Sprintf(
			"(len(scope_folders) = 0 OR EXISTS (SELECT 1 FROM unnest(scope_folders) AS t(f) WHERE '%s' LIKE f || '%%'))",
			strings.ReplaceAll(*path, "'", "''"),
		))
	}

	where := ""
	if len(conditions) > 0 {
		where = "WHERE " + strings.Join(conditions, " AND ")
	}

	if *jsonOut {
		sql := fmt.Sprintf(`SELECT * FROM read_parquet('%s') %s ORDER BY severity, id;`, parquetFile, where)
		rows, err := duckdbQueryJSON(sql)
		if err != nil {
			return err
		}
		b, _ := json.MarshalIndent(rows, "", "  ")
		fmt.Println(string(b))
		return nil
	}

	sql := fmt.Sprintf(`
SELECT id, severity, permitted,
  title,
  left(rule, 80) AS rule_preview,
  status, evidence
FROM read_parquet('%s')
%s
ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, id;`,
		parquetFile, where)
	return duckdbQuery(sql)
}

// runDodafAV2Get looks up an AV-2 integrated dictionary entry by term.
func runDodafAV2Get(args []string) error {
	fs := flag.NewFlagSet("dodaf av2 get", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}
	parquetFile := dodafParquetPath(wsRoot, "av2_dictionary")
	if _, err := os.Stat(parquetFile); err != nil {
		return fmt.Errorf("av2_dictionary.parquet not found — run: gftd dodaf init")
	}

	query := strings.Join(fs.Args(), " ")
	if query == "" {
		// List all
		sql := fmt.Sprintf(`SELECT id, term, domain, left(definition, 80) AS definition_preview FROM read_parquet('%s') ORDER BY domain, term;`, parquetFile)
		return duckdbQuery(sql)
	}

	escaped := strings.ReplaceAll(query, "'", "''")
	where := fmt.Sprintf(`WHERE lower(term) = lower('%s') OR lower(id) = lower('%s') OR list_contains(aliases, '%s')`,
		escaped, escaped, escaped)

	if *jsonOut {
		sql := fmt.Sprintf(`SELECT * FROM read_parquet('%s') %s LIMIT 5;`, parquetFile, where)
		rows, err := duckdbQueryJSON(sql)
		if err != nil {
			return err
		}
		b, _ := json.MarshalIndent(rows, "", "  ")
		fmt.Println(string(b))
		return nil
	}

	sql := fmt.Sprintf(`SELECT term, domain, definition, aliases, source, status FROM read_parquet('%s') %s LIMIT 5;`, parquetFile, where)
	return duckdbQuery(sql)
}

// runDodafRulesContext queries all views by file path and/or tags.
func runDodafRulesContext(args []string) error {
	fs := flag.NewFlagSet("dodaf rules context", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	path := fs.String("path", "", "file path for scope matching")
	tags := fs.String("tags", "", "comma-separated tags")
	jsonOut := fs.Bool("json", false, "output as JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}

	var tagList []string
	if *tags != "" {
		for _, t := range strings.Split(*tags, ",") {
			if t = strings.TrimSpace(t); t != "" {
				tagList = append(tagList, t)
			}
		}
	}

	// Build tag condition helper
	tagCond := func(col string) string {
		if len(tagList) == 0 {
			return ""
		}
		var parts []string
		for _, t := range tagList {
			parts = append(parts, fmt.Sprintf("list_contains(%s, '%s')", col, strings.ReplaceAll(t, "'", "''")))
		}
		return "(" + strings.Join(parts, " OR ") + ")"
	}

	pathCond := func(col string) string {
		if *path == "" || col == "" {
			return ""
		}
		return fmt.Sprintf("(len(%s) = 0 OR EXISTS (SELECT 1 FROM unnest(%s) AS t(f) WHERE '%s' LIKE f || '%%'))",
			col, col, strings.ReplaceAll(*path, "'", "''"))
	}

	buildWhere := func(tagCol, folderCol string) string {
		var parts []string
		if tc := tagCond(tagCol); tc != "" {
			parts = append(parts, tc)
		}
		if pc := pathCond(folderCol); pc != "" {
			parts = append(parts, pc)
		}
		if len(parts) == 0 {
			return ""
		}
		return "WHERE " + strings.Join(parts, " AND ")
	}

	if *jsonOut {
		result := map[string]interface{}{}

		for _, view := range []struct{ name, file, tagCol, folderCol string }{
			{"standards", "tv1_standards", "scope_tags", "scope_folders"},
			{"dictionary", "av2_dictionary", "scope_tags", ""},
			{"activities", "ov5_activities", "scope_tags", ""},
		} {
			pf := dodafParquetPath(wsRoot, view.file)
			if _, err := os.Stat(pf); err != nil {
				continue
			}
			where := buildWhere(view.tagCol, view.folderCol)
			sql := fmt.Sprintf(`SELECT * FROM read_parquet('%s') %s LIMIT 20;`, pf, where)
			rows, err := duckdbQueryJSON(sql)
			if err != nil {
				fmt.Fprintf(os.Stderr, "warn: %s query failed: %v\n", view.name, err)
				continue
			}
			result[view.name] = rows
		}

		b, _ := json.MarshalIndent(result, "", "  ")
		fmt.Println(string(b))
		return nil
	}

	// Human-readable output
	fmt.Println("=== TV-1: Technical Standards ===")
	tv1 := dodafParquetPath(wsRoot, "tv1_standards")
	if _, err := os.Stat(tv1); err == nil {
		where := buildWhere("scope_tags", "scope_folders")
		sql := fmt.Sprintf(`SELECT id, severity, permitted, title, status FROM read_parquet('%s') %s ORDER BY severity, id LIMIT 20;`, tv1, where)
		_ = duckdbQuery(sql)
	}

	fmt.Println("\n=== AV-2: Dictionary ===")
	av2 := dodafParquetPath(wsRoot, "av2_dictionary")
	if _, err := os.Stat(av2); err == nil {
		where := buildWhere("scope_tags", "")
		sql := fmt.Sprintf(`SELECT term, domain, left(definition,60) AS def FROM read_parquet('%s') %s ORDER BY domain, term LIMIT 10;`, av2, where)
		_ = duckdbQuery(sql)
	}

	fmt.Println("\n=== OV-5: Activities (Permitted/Prohibited) ===")
	ov5 := dodafParquetPath(wsRoot, "ov5_activities")
	if _, err := os.Stat(ov5); err == nil {
		where := buildWhere("scope_tags", "")
		sql := fmt.Sprintf(`SELECT permitted, action, left(reason,60) AS reason FROM read_parquet('%s') %s ORDER BY permitted, id LIMIT 10;`, ov5, where)
		_ = duckdbQuery(sql)
	}

	return nil
}

// runDodafAdd interactively (or via flags) adds a new entry to a DoDAF view.
func runDodafAdd(args []string) error {
	fs := flag.NewFlagSet("dodaf add", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	view := fs.String("view", "tv1", "view to add to: tv1 | av2 | ov5")
	id := fs.String("id", "", "unique ID (e.g. cf-wasm-no-dynamic-compile)")
	title := fs.String("title", "", "short title")
	rule := fs.String("rule", "", "full rule/definition text")
	severity := fs.String("severity", "high", "severity: critical|high|medium|info")
	permitted := fs.Bool("permitted", false, "true if this is a permitted action")
	tags := fs.String("tags", "", "comma-separated scope tags")
	evidence := fs.String("evidence", "", "evidence reference (file:line or URL)")
	source := fs.String("source", "", "source CLAUDE.md file")
	status := fs.String("status", "[PRODUCTION]", "status: [PRODUCTION]|[DESIGN]|[IMPLEMENTED]")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	if *id == "" || *rule == "" {
		return fmt.Errorf("--id and --rule are required")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}

	now := time.Now().UTC().Format(time.RFC3339)
	var tagList []string
	if *tags != "" {
		for _, t := range strings.Split(*tags, ",") {
			if t = strings.TrimSpace(t); t != "" {
				tagList = append(tagList, t)
			}
		}
	}

	switch *view {
	case "tv1":
		pf := dodafParquetPath(wsRoot, "tv1_standards")
		var existing []dodafTV1Row
		if _, err := os.Stat(pf); err == nil {
			rows, err := duckdbQueryJSON(fmt.Sprintf(`SELECT * FROM read_parquet('%s');`, pf))
			if err == nil {
				b, _ := json.Marshal(rows)
				_ = json.Unmarshal(b, &existing)
			}
		}
		existing = append(existing, dodafTV1Row{
			ID: *id, Title: *title, View: "TV-1", Rule: *rule,
			Severity: *severity, Permitted: *permitted,
			ScopeTags: tagList, Evidence: *evidence, Source: *source,
			Status: *status, CreatedAt: now,
		})
		if err := writeJSONToParquet(existing, pf); err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "added TV-1: %s → %s\n", *id, pf)
	case "av2":
		pf := dodafParquetPath(wsRoot, "av2_dictionary")
		var existing []dodafAV2Row
		if _, err := os.Stat(pf); err == nil {
			rows, err := duckdbQueryJSON(fmt.Sprintf(`SELECT * FROM read_parquet('%s');`, pf))
			if err == nil {
				b, _ := json.Marshal(rows)
				_ = json.Unmarshal(b, &existing)
			}
		}
		existing = append(existing, dodafAV2Row{
			ID: *id, Term: *title, Definition: *rule,
			ScopeTags: tagList, Source: *source, Status: *status, CreatedAt: now,
		})
		if err := writeJSONToParquet(existing, pf); err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "added AV-2: %s → %s\n", *id, pf)
	case "ov5":
		pf := dodafParquetPath(wsRoot, "ov5_activities")
		var existing []dodafOV5Row
		if _, err := os.Stat(pf); err == nil {
			rows, err := duckdbQueryJSON(fmt.Sprintf(`SELECT * FROM read_parquet('%s');`, pf))
			if err == nil {
				b, _ := json.Marshal(rows)
				_ = json.Unmarshal(b, &existing)
			}
		}
		existing = append(existing, dodafOV5Row{
			ID: *id, Action: *title, Reason: *rule, Permitted: *permitted,
			ScopeTags: tagList, Source: *source, CreatedAt: now,
		})
		if err := writeJSONToParquet(existing, pf); err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "added OV-5: %s → %s\n", *id, pf)
	default:
		return fmt.Errorf("unknown view: %s (use tv1, av2, or ov5)", *view)
	}
	return nil
}

// runDodafValidate scans CLAUDE.md files for CRITICAL rules not yet in TV-1 registry.
func runDodafValidate(args []string) error {
	fs := flag.NewFlagSet("dodaf validate", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}

	pf := dodafParquetPath(wsRoot, "tv1_standards")
	if _, err := os.Stat(pf); err != nil {
		return fmt.Errorf("tv1_standards.parquet not found — run: gftd dodaf init")
	}

	// Collect registered IDs
	rows, err := duckdbQueryJSON(fmt.Sprintf(`SELECT id FROM read_parquet('%s');`, pf))
	if err != nil {
		return err
	}
	registered := map[string]bool{}
	for _, r := range rows {
		if id, ok := r["id"].(string); ok {
			registered[id] = true
		}
	}

	// Scan CLAUDE.md files for ## CRITICAL: lines
	criticalSections := 0
	var unregistered []string
	err = filepath.Walk(wsRoot, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			if info.Name() == "node_modules" || info.Name() == ".git" || info.Name() == ".turbo" || info.Name() == "dist" {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Name() != "CLAUDE.md" {
			return nil
		}
		b, err := os.ReadFile(p)
		if err != nil {
			return nil
		}
		rel, _ := filepath.Rel(wsRoot, p)
		lines := strings.Split(string(b), "\n")
		for i, line := range lines {
			if !strings.HasPrefix(line, "## CRITICAL:") {
				continue
			}
			criticalSections++
			title := strings.TrimSpace(strings.TrimPrefix(line, "## CRITICAL:"))

			// Check if the next non-blank line is already a pointer (already migrated)
			alreadyMigrated := false
			for j := i + 1; j < len(lines) && j < i+5; j++ {
				trimmed := strings.TrimSpace(lines[j])
				if trimmed == "" {
					continue
				}
				if strings.HasPrefix(trimmed, "→ `gftd dodaf tv1 query --id") {
					alreadyMigrated = true
				}
				break
			}
			if alreadyMigrated {
				continue
			}

			// Check if any registered entry has this text in title or rule
			found := false
			for _, r := range rows {
				t, _ := r["title"].(string)
				if strings.Contains(strings.ToLower(t), strings.ToLower(title[:min(len(title), 30)])) {
					found = true
					break
				}
			}
			if !found {
				unregistered = append(unregistered, fmt.Sprintf("%s: %s", rel, title))
			}
		}
		return nil
	})
	if err != nil {
		return err
	}

	fmt.Printf("DoDAF Registry Validation\n")
	fmt.Printf("  Registered TV-1 entries: %d\n", len(registered))
	fmt.Printf("  ## CRITICAL: sections in CLAUDE.md files: %d\n", criticalSections)
	fmt.Printf("  Potentially unregistered: %d\n\n", len(unregistered))
	for _, u := range unregistered {
		fmt.Printf("  ? %s\n", u)
	}
	if len(unregistered) > 0 {
		fmt.Printf("\nRun: gftd dodaf add --view tv1 --id <id> --title <title> --rule <rule>\n")
	}
	return nil
}

// dodafSection holds one extracted ## CRITICAL: section from a CLAUDE.md file.
type dodafSection struct {
	File    string
	Title   string
	Body    string // full body (may include code blocks)
	RuleText string // first prose paragraph only (no code blocks)
}

// extractCriticalSections parses a CLAUDE.md file and returns all ## CRITICAL: sections.
func extractCriticalSections(content, relPath string) []dodafSection {
	lines := strings.Split(content, "\n")
	var sections []dodafSection
	var cur *dodafSection
	for i, line := range lines {
		if strings.HasPrefix(line, "## CRITICAL:") {
			if cur != nil {
				cur.RuleText = extractProse(cur.Body)
				sections = append(sections, *cur)
			}
			title := strings.TrimSpace(strings.TrimPrefix(line, "## CRITICAL:"))
			cur = &dodafSection{File: relPath, Title: title}
		} else if cur != nil {
			if strings.HasPrefix(line, "## ") || strings.HasPrefix(line, "# ") {
				_ = i
				cur.RuleText = extractProse(cur.Body)
				sections = append(sections, *cur)
				cur = nil
			} else {
				cur.Body += line + "\n"
			}
		}
	}
	if cur != nil {
		cur.RuleText = extractProse(cur.Body)
		sections = append(sections, *cur)
	}
	return sections
}

// extractProse returns the first prose paragraph from a markdown body, stripping code blocks.
func extractProse(body string) string {
	lines := strings.Split(body, "\n")
	inCode := false
	var prose []string
	for _, l := range lines {
		if strings.HasPrefix(l, "```") {
			inCode = !inCode
			continue
		}
		if inCode {
			continue
		}
		trimmed := strings.TrimSpace(l)
		if trimmed == "" {
			if len(prose) > 0 {
				break // stop at first blank line after prose
			}
			continue
		}
		// Skip table rows and headers
		if strings.HasPrefix(trimmed, "|") || strings.HasPrefix(trimmed, "-") {
			continue
		}
		prose = append(prose, trimmed)
	}
	rule := strings.Join(prose, " ")
	if len(rule) > 800 {
		rule = rule[:800] + "..."
	}
	return rule
}

// dodafIDFromTitle produces a slug ID from a CRITICAL section title.
func dodafIDFromTitle(file, title string) string {
	// Use file base + title slug
	base := filepath.Base(filepath.Dir(file))
	if base == "." || base == "" {
		base = "root"
	}
	slug := strings.ToLower(title)
	slug = strings.NewReplacer(
		" ", "-", "/", "-", "（", "", "）", "", "(", "", ")", "",
		"→", "", "`", "", "'", "", "\"", "", ".", "-", ":", "",
		"　", "-", "—", "-", "・", "-",
	).Replace(slug)
	// collapse multiple dashes
	for strings.Contains(slug, "--") {
		slug = strings.ReplaceAll(slug, "--", "-")
	}
	slug = strings.Trim(slug, "-")
	if len(slug) > 50 {
		slug = slug[:50]
		slug = strings.Trim(slug, "-")
	}
	id := base + "-" + slug
	if len(id) > 60 {
		id = id[:60]
		id = strings.Trim(id, "-")
	}
	return id
}

// dodafTagsForFile infers scope_tags from the file path.
func dodafTagsForFile(relPath string) []string {
	tags := []string{"claude", "docs"}
	if strings.Contains(relPath, "60-apps/") {
		tags = append(tags, "at-protocol", "magatama", "typescript")
	}
	if strings.Contains(relPath, "50-infra/") {
		tags = append(tags, "cloudflare", "infrastructure")
	}
	if strings.Contains(relPath, "40-engine/svelte/") {
		tags = append(tags, "svelte", "frontend")
	}
	if strings.Contains(relPath, "30-graph/") {
		tags = append(tags, "graph-db", "duckdb")
	}
	if strings.Contains(relPath, "70-tools/") {
		tags = append(tags, "gftd-cli", "tooling")
	}
	if strings.Contains(relPath, "CLAUDE.md") && !strings.Contains(relPath, "/") {
		// root CLAUDE.md
		tags = append(tags, "root-policy")
	}
	return tags
}

// runDodafMigrate extracts all ## CRITICAL: sections from CLAUDE.md files,
// adds them to the TV-1 Parquet registry, and replaces the section body
// in each CLAUDE.md with a single pointer line.
func runDodafMigrate(args []string) error {
	fs := flag.NewFlagSet("dodaf migrate", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	dryRun := fs.Bool("dry-run", false, "print plan without modifying files")
	skipPointer := fs.Bool("skip-pointer", false, "only update Parquet, do not rewrite CLAUDE.md files")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}
	pf := dodafParquetPath(wsRoot, "tv1_standards")
	if _, err := os.Stat(pf); err != nil {
		return fmt.Errorf("tv1_standards.parquet not found — run: gftd dodaf init")
	}

	// Load existing IDs to avoid duplicates
	existing, _ := duckdbQueryJSON(fmt.Sprintf(`SELECT id FROM read_parquet('%s')`, pf))
	registeredIDs := map[string]bool{}
	for _, r := range existing {
		if id, ok := r["id"].(string); ok {
			registeredIDs[id] = true
		}
	}

	// Load all existing rows to merge with new ones
	allRows, _ := duckdbQueryJSON(fmt.Sprintf(`SELECT * FROM read_parquet('%s')`, pf))
	var tv1Rows []dodafTV1Row
	for _, r := range allRows {
		b, _ := json.Marshal(r)
		var row dodafTV1Row
		if err := json.Unmarshal(b, &row); err == nil {
			tv1Rows = append(tv1Rows, row)
		}
	}

	now := time.Now().UTC().Format(time.RFC3339)
	newCount := 0
	rewriteCount := 0

	err = filepath.Walk(wsRoot, func(p string, info os.FileInfo, err error) error {
		if err != nil {
			return nil
		}
		if info.IsDir() {
			if info.Name() == "node_modules" || info.Name() == ".git" || info.Name() == ".turbo" || info.Name() == "dist" {
				return filepath.SkipDir
			}
			return nil
		}
		if info.Name() != "CLAUDE.md" {
			return nil
		}

		content, err := os.ReadFile(p)
		if err != nil {
			return nil
		}
		relPath, _ := filepath.Rel(wsRoot, p)
		sections := extractCriticalSections(string(content), relPath)
		if len(sections) == 0 {
			return nil
		}

		// Build new content for this CLAUDE.md
		newContent := string(content)
		modified := false

		for _, sec := range sections {
			id := dodafIDFromTitle(relPath, sec.Title)
			// Ensure unique ID
			origID := id
			for i := 2; registeredIDs[id] && i < 20; i++ {
				id = fmt.Sprintf("%s-%d", origID, i)
			}

			ruleText := sec.RuleText
			if ruleText == "" {
				ruleText = sec.Title
			}
			tags := dodafTagsForFile(relPath)

			if !registeredIDs[id] {
				row := dodafTV1Row{
					ID: id, Title: sec.Title, View: "TV-1",
					StandardRef: "CLAUDE.md policy",
					Rule:        ruleText,
					Severity:    "high",
					Permitted:   false,
					ScopeTags:   tags,
					Evidence:    relPath,
					Status:      "[PRODUCTION]",
					Source:      relPath,
					CreatedAt:   now,
				}
				tv1Rows = append(tv1Rows, row)
				registeredIDs[id] = true
				newCount++
				if *dryRun {
					fmt.Printf("+ TV-1 [%s] %s\n  rule: %s\n\n", id, sec.Title, dodafTruncate(ruleText, 100))
				}
			}

			// Replace section body with pointer in CLAUDE.md
			if !*skipPointer {
				header := "## CRITICAL: " + sec.Title
				pointer := fmt.Sprintf("→ `gftd dodaf tv1 query --id %s` / MCP `gftd.dodaf.tv1.query`", id)
				// Replace: header + body → header + pointer
				oldBlock := header + "\n" + sec.Body
				newBlock := header + "\n\n" + pointer + "\n\n"
				if strings.Contains(newContent, oldBlock) {
					newContent = strings.Replace(newContent, oldBlock, newBlock, 1)
					modified = true
					rewriteCount++
					if *dryRun {
						fmt.Printf("~ CLAUDE.md pointer: %s\n  %s\n\n", relPath, pointer)
					}
				}
			}
		}

		if modified && !*dryRun {
			if err := os.WriteFile(p, []byte(newContent), info.Mode()); err != nil {
				fmt.Fprintf(os.Stderr, "warn: failed to rewrite %s: %v\n", relPath, err)
			}
		}
		return nil
	})
	if err != nil {
		return err
	}

	if *dryRun {
		fmt.Printf("\n[dry-run] would add %d TV-1 entries, update %d CLAUDE.md files\n", newCount, rewriteCount)
		fmt.Printf("Run without --dry-run to apply.\n")
		return nil
	}

	// Write updated Parquet
	if newCount > 0 {
		fmt.Fprintf(os.Stderr, "writing %d new + %d existing TV-1 entries to %s\n", newCount, len(tv1Rows)-newCount, pf)
		if err := writeJSONToParquet(tv1Rows, pf); err != nil {
			return fmt.Errorf("write parquet: %w", err)
		}
	}

	fmt.Printf("migrated: %d new TV-1 entries added, %d CLAUDE.md files updated with pointers\n", newCount, rewriteCount)
	return nil
}

func dodafTruncate(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "..."
}

// runDodafSeedKagami pushes the registry to PDS/kagami for MCP access.
func runDodafSeedKagami(args []string) error {
	fs := flag.NewFlagSet("dodaf seed", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	pdsURL := fs.String("pds", "https://atproto.etzhayyim.com", "PDS URL")
	dryRun := fs.Bool("dry-run", false, "print records without seeding")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if _, err := exec.LookPath("duckdb"); err != nil {
		return fmt.Errorf("duckdb not found — install: brew install duckdb")
	}
	wsRoot, err := resolveShannonRoot(*wsDir)
	if err != nil {
		return err
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("auth required — run: gftd auth login")
	}

	pf := dodafParquetPath(wsRoot, "tv1_standards")
	if _, err := os.Stat(pf); err != nil {
		return fmt.Errorf("tv1_standards.parquet not found — run: gftd dodaf init")
	}

	rows, err := duckdbQueryJSON(fmt.Sprintf(`SELECT * FROM read_parquet('%s') LIMIT 100;`, pf))
	if err != nil {
		return err
	}

	fmt.Fprintf(os.Stderr, "seeding %d TV-1 constraints to %s ...\n", len(rows), *pdsURL)
	seeded := 0
	for _, row := range rows {
		record := map[string]interface{}{
			"$type":      "ai.gftd.dodaf.tv1Standard",
			"dodaf_id":   row["id"],
			"title":      row["title"],
			"rule":       row["rule"],
			"severity":   row["severity"],
			"permitted":  row["permitted"],
			"scope_tags": row["scope_tags"],
			"evidence":   row["evidence"],
			"status":     row["status"],
			"created_at": row["created_at"],
		}
		if *dryRun {
			b, _ := json.MarshalIndent(record, "  ", "  ")
			fmt.Printf("  [dry-run] %s\n%s\n", row["id"], b)
			continue
		}
		payload := map[string]interface{}{
			"repo":       "",
			"collection": "ai.gftd.dodaf.tv1Standard",
			"record":     record,
		}
		b, _ := json.Marshal(payload)
		url := *pdsURL + "/xrpc/com.atproto.repo.createRecord"
		cmd := exec.Command("curl", "-s", "-X", "POST", url,
			"-H", "Content-Type: application/json",
			"-H", "Authorization: Bearer "+token,
			"-d", string(b))
		cmd.Stdout = os.Stderr
		cmd.Stderr = os.Stderr
		if err := cmd.Run(); err != nil {
			fmt.Fprintf(os.Stderr, "warn: seed failed for %v: %v\n", row["id"], err)
			continue
		}
		seeded++
	}
	if !*dryRun {
		fmt.Fprintf(os.Stderr, "seeded: %d/%d TV-1 constraints\n", seeded, len(rows))
	}
	return nil
}

func min(a, b int) int {
	if a < b {
		return a
	}
	return b
}
