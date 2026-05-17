// kosei_stack.go — Full stack + SBOM scanning for gftd kosei
//
// Scans each App component directory and extracts:
//   - Cloudflare bindings    (wrangler.jsonc)
//   - npm dependencies       (package.json)
//   - WIT imports            (wit/world.wit)
//   - App features           (magatama.jsonld extensions)
//   - Source-level signals   (src/*.ts, *.go, *.rs keywords)
//
// Subcommands:
//   gftd kosei stack <nanoid>    Full stack detail for one app
//   gftd kosei sbom  <nanoid>    SBOM for one app (deps + bindings)
//   gftd kosei matrix            Cross-app technology matrix
//   gftd kosei stats             Aggregate statistics across all apps
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
	"text/tabwriter"
)

// ── Stack types ────────────────────────────────────────────────────────────

// koseiStack holds all technology-stack signals for one component.
type koseiStack struct {
	// Language / runtime
	Language      string `json:"language"`       // "typescript" | "rust" | "go" | "python"
	Framework     string `json:"framework"`      // "ts-native"
	GuestLanguage string `json:"guest_language"` // from build.guestLanguage

	// Cloudflare bindings (from wrangler.jsonc)
	HasAssets    bool     `json:"has_assets"`     // ASSETS → Svelte CSR
	HasWorkersAI bool     `json:"has_workers_ai"` // AI → CF Workers AI
	HasBrowser   bool     `json:"has_browser"`    // HEADLESS_BROWSER → browser automation
	HasPDSRPC    bool     `json:"has_pds_rpc"`    // PDS_RPC entrypoint
	HasGraphSQL bool     `json:"has_graph_sql"` // legacy graph binding marker
	R2Count      int      `json:"r2_count"`       // R2 bucket bindings
	ServiceCount int      `json:"service_count"`  // total service bindings
	SecretCount  int      `json:"secret_count"`   // secrets store bindings
	CFBindings   []string `json:"cf_bindings"`    // all binding names

	// App features (from magatama.jsonld)
	ContentMode   string `json:"content_mode"`   // "timeline" | "interactive" | "game"
	HasSubscribe  bool   `json:"has_subscribe"`  // subscribeRepos trigger
	CollCount     int    `json:"coll_count"`     // subscribeRepos collection count
	HasEvolver    bool   `json:"has_evolver"`    // agentic evolver block
	HasSpace      bool   `json:"has_space"`      // space/channel (W Protocol convo)
	HasGame       bool   `json:"has_game"`       // game config
	HasDesktop    bool   `json:"has_desktop"`    // desktop app packaging
	HasSignal     bool   `json:"has_signal"`     // Signal E2E (component.compose.signal)
	RequiresCount int    `json:"requires_count"` // interfaces.requires count
	ProvidesCount int    `json:"provides_count"` // interfaces.provides count
	HasConvoPrmpt bool   `json:"has_convo_prompt"` // convoSystemPrompt set

	// Source-level detection (src/**/*.ts, *.go, *.rs)
	HasWebGPU bool `json:"has_webgpu"` // WebGPU / wgpu
	HasONNX   bool `json:"has_onnx"`   // ONNX / transformers.js
	HasFIDO2  bool `json:"has_fido2"`  // FIDO2 / WebAuthn
	HasWASM   bool `json:"has_wasm"`   // compiled WASM
	HasMCP    bool `json:"has_mcp"`    // MCP server capability
	HasBPMN   bool `json:"has_bpmn"`   // BPMN pipeline
	HasWIT    bool `json:"has_wit"`    // WIT contract (world.wit)

	// RisingWave / data layer signals
	HasRisingWave bool `json:"has_risingwave"` // RisingWave / KAGAMI graph DB usage
	HasYata      bool `json:"has_yata"`      // yata / LanceDB graph engine

	// Svelte frontend
	HasSvelte    bool   `json:"has_svelte"`    // svelte/ dir present
	SvelteVersion string `json:"svelte_version"` // from package.json

	// SBOM
	NPMDeps     []string `json:"npm_deps"`      // npm deps (non-@types, non-standard)
	WITImports  []string `json:"wit_imports"`   // WIT imports from world.wit
	CargoCrates []string `json:"cargo_crates"`  // Cargo.toml deps
}

// ── Scanner ────────────────────────────────────────────────────────────────

// koseiScanStack scans an app directory and populates a koseiStack.
func koseiScanStack(appDir string, meta koseiAppMeta) koseiStack {
	s := koseiStack{
		Language:      "typescript",
		Framework:     "ts-native",
		GuestLanguage: meta.GuestLang,
		ContentMode:   meta.Description, // placeholder; overwrite from jld
		HasSubscribe:  len(meta.Collections) > 0,
		CollCount:     len(meta.Collections),
		RequiresCount: len(meta.Requires),
	}

	// Fix ContentMode — re-read from raw jld
	s.ContentMode = koseiReadContentMode(filepath.Join(appDir, "magatama.jsonld"))

	// Svelte
	if _, err := os.Stat(filepath.Join(appDir, "svelte")); err == nil {
		s.HasSvelte = true
	}
	s.HasAssets = s.HasSvelte // Svelte → ASSETS binding (appview)

	// WIT
	witPath := filepath.Join(appDir, "wit", "world.wit")
	if _, err := os.Stat(witPath); err == nil {
		s.HasWIT = true
		s.WITImports = koseiScanWITImports(witPath)
		// Signal E2E check
		for _, imp := range s.WITImports {
			if strings.Contains(imp, "signal") {
				s.HasSignal = true
			}
			if strings.Contains(imp, "browser") || strings.Contains(imp, "automation") {
				s.HasBrowser = true
			}
			if strings.Contains(imp, "mcp") || strings.Contains(imp, "capability") {
				s.HasMCP = true
			}
			if strings.Contains(imp, "risingwave") || strings.Contains(imp, "kagami") {
				s.HasRisingWave = true
			}
			if strings.Contains(imp, "yata") || strings.Contains(imp, "lancedb") {
				s.HasYata = true
			}
		}
	}

	// wrangler.jsonc
	koseiScanWrangler(appDir, &s)

	// package.json
	koseiScanPackageJSON(appDir, &s)

	// Cargo.toml
	koseiScanCargo(appDir, &s)

	// Extended magatama.jsonld fields
	koseiScanJSONLDExtended(filepath.Join(appDir, "magatama.jsonld"), &s)

	// Source keyword scan
	koseiScanSourceKeywords(appDir, &s)

	// Derive language
	if s.GuestLanguage != "" {
		switch s.GuestLanguage {
		case "rust":
			s.Language = "rust"
		case "go":
			s.Language = "go"
		case "python":
			s.Language = "python"
		}
	}
	if len(s.CargoCrates) > 0 {
		s.Language = "rust"
		s.HasWASM = true
	}

	return s
}

// koseiScanWrangler parses wrangler.jsonc for CF bindings.
func koseiScanWrangler(appDir string, s *koseiStack) {
	data, err := os.ReadFile(filepath.Join(appDir, "wrangler.jsonc"))
	if err != nil {
		data, err = os.ReadFile(filepath.Join(appDir, "wrangler.toml"))
		if err != nil {
			return
		}
	}

	// Strip JSONC comments
	stripped := stripJSONCComments(string(data))

	var wr struct {
		AI      *struct{} `json:"ai"`
		Browser *struct{} `json:"browser"`
		Assets  *struct{} `json:"assets"`
		R2      []struct {
			Binding string `json:"binding"`
		} `json:"r2_buckets"`
		Services []struct {
			Binding    string `json:"binding"`
			Entrypoint string `json:"entrypoint"`
		} `json:"services"`
		Secrets []struct {
			Binding string `json:"binding"`
		} `json:"secrets_store_secrets"`
		KV []struct {
			Binding string `json:"binding"`
		} `json:"kv_namespaces"`
		DO []struct {
			Name    string `json:"name"`
			ClassName string `json:"class_name"`
		} `json:"durable_objects"`
		D1 []struct {
			Binding string `json:"binding"`
		} `json:"d1_databases"`
		Queues struct {
			Consumers []struct{ Queue string `json:"queue"` } `json:"consumers"`
			Producers []struct{ Binding string `json:"binding"` } `json:"producers"`
		} `json:"queues"`
	}
	if json.Unmarshal([]byte(stripped), &wr) != nil {
		return
	}

	s.HasWorkersAI = wr.AI != nil
	s.HasBrowser = s.HasBrowser || wr.Browser != nil
	s.HasAssets = s.HasAssets || wr.Assets != nil
	s.R2Count = len(wr.R2)
	s.ServiceCount = len(wr.Services)
	s.SecretCount = len(wr.Secrets)

	// Collect all binding names
	bindingSet := make(map[string]bool)
	for _, r := range wr.R2 {
		bindingSet[r.Binding] = true
	}
	for _, sv := range wr.Services {
		bindingSet[sv.Binding] = true
		if strings.Contains(sv.Binding, "GRAPH_QUERY_SERVICE") || strings.Contains(sv.Binding, "KAGAMI") {
			s.HasGraphSQL = true
		}
		if strings.EqualFold(sv.Entrypoint, "PdsRPC") {
			s.HasPDSRPC = true
		}
		if strings.Contains(sv.Binding, "RISINGWAVE") {
			s.HasRisingWave = true
		}
	}
	for _, sec := range wr.Secrets {
		bindingSet[sec.Binding] = true
	}
	for _, kv := range wr.KV {
		bindingSet[kv.Binding] = true
	}
	for _, d := range wr.DO {
		bindingSet[d.Name] = true
	}
	for _, d := range wr.D1 {
		bindingSet[d.Binding] = true
	}
	// Collect keys
	for k := range bindingSet {
		s.CFBindings = append(s.CFBindings, k)
	}
	sort.Strings(s.CFBindings)

	// Legacy graph binding check via binding name
	for _, sv := range wr.Services {
		if strings.Contains(sv.Binding, "KAGAMI") {
			s.HasGraphSQL = true
			s.HasRisingWave = true
		}
	}
}

// koseiScanPackageJSON reads package.json for npm deps.
func koseiScanPackageJSON(appDir string, s *koseiStack) {
	data, err := os.ReadFile(filepath.Join(appDir, "package.json"))
	if err != nil {
		// Try svelte/package.json
		data, err = os.ReadFile(filepath.Join(appDir, "svelte", "package.json"))
		if err != nil {
			return
		}
	}
	var pkg struct {
		Dependencies    map[string]string `json:"dependencies"`
		DevDependencies map[string]string `json:"devDependencies"`
	}
	if json.Unmarshal(data, &pkg) != nil {
		return
	}

	// Merge all deps
	all := make(map[string]string)
	for k, v := range pkg.Dependencies {
		all[k] = v
	}
	for k, v := range pkg.DevDependencies {
		all[k] = v
	}

	// Notable packages (exclude @types/, cloudflare:, workspace:)
	notable := map[string]bool{
		"@huggingface/transformers": true, "onnxruntime-web": true,
		"@onnxruntime/web": true, "transformers": true,
		"tweetnacl": true, "libsodium-wrappers": true,
		"@noble/hashes": true, "@noble/curves": true,
		"fflate": true, "zod": true,
		"hono": true, "svelte": true, "@sveltejs/kit": true,
		"leaflet": true, "three": true, "@threlte/core": true,
		"tone": true, "sharp": true,
		"playwright": true, "puppeteer": true,
		"@playwright/test": true,
		"drizzle-orm": true, "prisma": true,
		"better-sqlite3": true, "duckdb": true,
		"wgpu": true, "webgpu-utils": true,
		"@webgpu/types": true,
	}

	var deps []string
	for pkg, ver := range all {
		if strings.HasPrefix(pkg, "@types/") {
			continue
		}
		if strings.HasPrefix(pkg, "cloudflare") {
			continue
		}
		if strings.Contains(ver, "workspace") {
			continue
		}
		if notable[pkg] || strings.Contains(pkg, "transformers") || strings.Contains(pkg, "onnx") {
			deps = append(deps, pkg+"@"+ver)
		}

		// Feature detection
		if strings.Contains(pkg, "transformers") || strings.Contains(pkg, "onnx") {
			s.HasONNX = true
		}
		if strings.Contains(pkg, "webgpu") || pkg == "wgpu" {
			s.HasWebGPU = true
		}
		if strings.Contains(pkg, "playwright") || strings.Contains(pkg, "puppeteer") {
			s.HasBrowser = true
		}
		if pkg == "svelte" || strings.HasPrefix(pkg, "@sveltejs/") {
			s.HasSvelte = true
			if pkg == "svelte" {
				s.SvelteVersion = ver
			}
		}
		if strings.Contains(pkg, "fido") || strings.Contains(pkg, "webauthn") {
			s.HasFIDO2 = true
		}
	}

	sort.Strings(deps)
	s.NPMDeps = deps
}

// koseiScanCargo reads Cargo.toml for Rust crates.
func koseiScanCargo(appDir string, s *koseiStack) {
	data, err := os.ReadFile(filepath.Join(appDir, "Cargo.toml"))
	if err != nil {
		return
	}
	// Simple TOML parsing — extract [dependencies] section
	var crates []string
	inDeps := false
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "[dependencies]") {
			inDeps = true
			continue
		}
		if strings.HasPrefix(line, "[") {
			inDeps = false
		}
		if inDeps && strings.Contains(line, "=") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				name := strings.TrimSpace(parts[0])
				ver := strings.TrimSpace(parts[1])
				crates = append(crates, name+"="+ver)
				if strings.Contains(name, "wgpu") || strings.Contains(name, "naga") {
					s.HasWebGPU = true
				}
			}
		}
	}
	s.CargoCrates = crates
	if len(crates) > 0 {
		s.HasWASM = true
	}
}

// koseiScanJSONLDExtended reads extended fields from magatama.jsonld.
func koseiScanJSONLDExtended(jPath string, s *koseiStack) {
	data, err := os.ReadFile(jPath)
	if err != nil {
		return
	}
	var jld struct {
		ContentMode      string `json:"contentMode"`
		ConvoSystemPrompt string `json:"convoSystemPrompt"`
		Evolver          *struct{} `json:"evolver"`
		Space            *struct{} `json:"space"`
		Game             *struct{} `json:"game"`
		Desktop          *struct{} `json:"desktop"`
		Framework        string    `json:"framework"`
		Component        *struct {
			Compose *struct {
				Signal string `json:"signal"`
			} `json:"compose"`
			Env map[string]interface{} `json:"env"`
		} `json:"component"`
		Interfaces *struct {
			Provides []interface{} `json:"provides"`
			Requires []interface{} `json:"requires"`
		} `json:"interfaces"`
		Triggers *struct {
			SubscribeRepos *struct {
				Collections []string `json:"collections"`
			} `json:"subscribeRepos"`
		} `json:"triggers"`
	}
	if json.Unmarshal(data, &jld) != nil {
		return
	}

	s.ContentMode = jld.ContentMode
	s.HasConvoPrmpt = jld.ConvoSystemPrompt != ""
	s.HasEvolver = jld.Evolver != nil
	s.HasSpace = jld.Space != nil
	s.HasGame = jld.Game != nil
	s.HasDesktop = jld.Desktop != nil
	s.Framework = jld.Framework
	if jld.Component != nil && jld.Component.Compose != nil {
		s.HasSignal = jld.Component.Compose.Signal != ""
	}
	if jld.Interfaces != nil {
		s.ProvidesCount = len(jld.Interfaces.Provides)
		// RequiresCount already set from koseiAppMeta
	}
	if jld.Triggers != nil && jld.Triggers.SubscribeRepos != nil {
		s.HasSubscribe = len(jld.Triggers.SubscribeRepos.Collections) > 0
		s.CollCount = len(jld.Triggers.SubscribeRepos.Collections)
	}
}

// koseiScanWITImports reads WIT imports from world.wit.
func koseiScanWITImports(witPath string) []string {
	data, err := os.ReadFile(witPath)
	if err != nil {
		return nil
	}
	re := regexp.MustCompile(`(?m)^\s*import\s+(\S+)`)
	matches := re.FindAllStringSubmatch(string(data), -1)
	var imports []string
	for _, m := range matches {
		if len(m) >= 2 {
			imports = append(imports, m[1])
		}
	}
	return imports
}

// koseiScanSourceKeywords scans source files for technology keywords.
func koseiScanSourceKeywords(appDir string, s *koseiStack) {
	keywords := map[string]*bool{
		"webgpu":       &s.HasWebGPU,
		"wgpu":         &s.HasWebGPU,
		"gpubuffer":    &s.HasWebGPU,
		"onnx":         &s.HasONNX,
		"transformers": &s.HasONNX,
		"fido2":        &s.HasFIDO2,
		"webauthn":     &s.HasFIDO2,
		"passkey":      &s.HasFIDO2,
		"risingwave":    &s.HasRisingWave,
		"stream load":  &s.HasRisingWave,
		"graph_sql":   &s.HasGraphSQL,
		"yata":         &s.HasYata,
		"lancedb":      &s.HasYata,
		"bpmn":         &s.HasBPMN,
		"pipeline":     &s.HasBPMN,
		"mcp":          &s.HasMCP,
	}

	srcDirs := []string{
		filepath.Join(appDir, "src"),
		filepath.Join(appDir, "svelte", "src"),
	}

	for _, dir := range srcDirs {
		_ = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
			if err != nil || info.IsDir() {
				return nil
			}
			if info.Size() > 256*1024 {
				return nil
			}
			ext := strings.ToLower(filepath.Ext(path))
			if ext != ".ts" && ext != ".js" && ext != ".rs" && ext != ".go" && ext != ".svelte" {
				return nil
			}
			data, err := os.ReadFile(path)
			if err != nil {
				return nil
			}
			content := strings.ToLower(string(data))
			for kw, flag := range keywords {
				if !*flag && strings.Contains(content, kw) {
					*flag = true
				}
			}
			// WASM check
			if !s.HasWASM && (strings.Contains(content, "wasm") || strings.Contains(content, "webassembly")) {
				s.HasWASM = true
			}
			return nil
		})
	}
}

// koseiReadContentMode reads contentMode from magatama.jsonld.
func koseiReadContentMode(jPath string) string {
	data, err := os.ReadFile(jPath)
	if err != nil {
		return ""
	}
	var jld struct {
		ContentMode string `json:"contentMode"`
	}
	if json.Unmarshal(data, &jld) != nil {
		return ""
	}
	return jld.ContentMode
}

// ── JSONC comment stripper ─────────────────────────────────────────────────

var (
	jsoNCLineCommentRE  = regexp.MustCompile(`//[^\n]*`)
	jsoNCBlockCommentRE = regexp.MustCompile(`/\*.*?\*/`)
)

func stripJSONCComments(s string) string {
	s = jsoNCBlockCommentRE.ReplaceAllString(s, "")
	s = jsoNCLineCommentRE.ReplaceAllString(s, "")
	return s
}

// ── Stack subcommand ───────────────────────────────────────────────────────

func runKoseiStackCmd(args []string) error {
	target, flagArgs := koseiExtractTarget(args)
	if target == "" {
		return fmt.Errorf("usage: gftd kosei stack <nanoid>")
	}

	fs := flag.NewFlagSet("kosei stack", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	var found *koseiAppState
	for i := range states {
		if states[i].Nanoid == target || states[i].Name == target {
			found = &states[i]
			break
		}
	}
	if found == nil {
		return fmt.Errorf("app %q not found", target)
	}

	// Scan stack
	appDir := filepath.Join(wsRoot, found.Dir)
	stack := koseiScanStack(appDir, found.koseiAppMeta)

	if *jsonOut {
		return encodeJSON(map[string]any{"meta": found, "stack": stack})
	}

	printKoseiStack(found, stack)
	return nil
}

func printKoseiStack(s *koseiAppState, st koseiStack) {
	fmt.Printf("Stack: %s  (%s)\n", s.Name, s.Nanoid)
	fmt.Printf("DID:   %s\n", s.DID)
	fmt.Printf("Dir:   %s\n\n", s.Dir)

	fmt.Printf("── Execution ──────────────────────────────────────\n")
	fmt.Printf("  Tier:       %s  (η=%.3f)\n", s.Tier, s.Efficiency)
	fmt.Printf("  Language:   %s\n", st.Language)
	fmt.Printf("  Framework:  %s\n", st.Framework)
	fmt.Printf("  UI Type:    %s\n", s.UIType)
	fmt.Printf("  Content:    %s\n", st.ContentMode)
	fmt.Printf("  PerformerType: %s\n\n", s.PerformerType)

	fmt.Printf("── Cloudflare Bindings ────────────────────────────\n")
	fmt.Printf("  Workers AI:      %s\n", boolStr(st.HasWorkersAI))
	fmt.Printf("  Headless Browser: %s\n", boolStr(st.HasBrowser))
	fmt.Printf("  Svelte Assets:   %s\n", boolStr(st.HasAssets))
	fmt.Printf("  legacyGraphSQL:  %s\n", boolStr(st.HasGraphSQL))
	fmt.Printf("  PDS_RPC:         %s\n", boolStr(st.HasPDSRPC))
	fmt.Printf("  R2 buckets:      %d\n", st.R2Count)
	fmt.Printf("  Services:        %d\n", st.ServiceCount)
	fmt.Printf("  Secrets:         %d\n", st.SecretCount)
	if len(st.CFBindings) > 0 {
		fmt.Printf("  All bindings:    %s\n\n", strings.Join(st.CFBindings, ", "))
	}

	fmt.Printf("── Data Layer ─────────────────────────────────────\n")
	fmt.Printf("  RisingWave:     %s\n", boolStr(st.HasRisingWave))
	fmt.Printf("  Yata/LanceDB:  %s\n", boolStr(st.HasYata))
	fmt.Printf("  subscribeRepos: %s (%d collections)\n", boolStr(st.HasSubscribe), st.CollCount)
	if len(s.Collections) > 0 {
		fmt.Printf("  Collections:\n")
		for _, c := range s.Collections {
			fmt.Printf("    • %s\n", c)
		}
	}

	fmt.Printf("\n── Features ───────────────────────────────────────\n")
	fmt.Printf("  WebGPU/wgpu:   %s\n", boolStr(st.HasWebGPU))
	fmt.Printf("  ONNX/ML:       %s\n", boolStr(st.HasONNX))
	fmt.Printf("  FIDO2:         %s\n", boolStr(st.HasFIDO2))
	fmt.Printf("  Signal E2E:    %s\n", boolStr(st.HasSignal))
	fmt.Printf("  WASM:          %s\n", boolStr(st.HasWASM))
	fmt.Printf("  MCP server:    %s\n", boolStr(st.HasMCP))
	fmt.Printf("  BPMN pipeline: %s\n", boolStr(st.HasBPMN))
	fmt.Printf("  Evolver:       %s\n", boolStr(st.HasEvolver))
	fmt.Printf("  Space/Channel: %s\n", boolStr(st.HasSpace))
	fmt.Printf("  Game config:   %s\n", boolStr(st.HasGame))
	fmt.Printf("  Desktop app:   %s\n", boolStr(st.HasDesktop))
	fmt.Printf("  Convo prompt:  %s\n", boolStr(st.HasConvoPrmpt))
	fmt.Printf("  WIT contract:  %s\n", boolStr(st.HasWIT))
	fmt.Printf("  WIT requires:  %d  provides: %d\n\n", st.RequiresCount, st.ProvidesCount)

	if len(st.WITImports) > 0 {
		fmt.Printf("── WIT Imports ────────────────────────────────────\n")
		for _, imp := range st.WITImports {
			fmt.Printf("  import %s\n", imp)
		}
		fmt.Println()
	}

	if len(st.NPMDeps) > 0 {
		fmt.Printf("── Notable npm deps ───────────────────────────────\n")
		for _, d := range st.NPMDeps {
			fmt.Printf("  %s\n", d)
		}
		fmt.Println()
	}

	if len(st.CargoCrates) > 0 {
		fmt.Printf("── Cargo crates ───────────────────────────────────\n")
		for _, c := range st.CargoCrates {
			fmt.Printf("  %s\n", c)
		}
	}
}

// ── SBOM subcommand ────────────────────────────────────────────────────────

func runKoseiSBOM(args []string) error {
	target, flagArgs := koseiExtractTarget(args)
	if target == "" {
		return fmt.Errorf("usage: gftd kosei sbom <nanoid> [--json]")
	}

	fs := flag.NewFlagSet("kosei sbom", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	var found *koseiAppState
	for i := range states {
		if states[i].Nanoid == target {
			found = &states[i]
			break
		}
	}
	if found == nil {
		return fmt.Errorf("app %q not found", target)
	}

	appDir := filepath.Join(wsRoot, found.Dir)
	stack := koseiScanStack(appDir, found.koseiAppMeta)

	type sbomOutput struct {
		Nanoid      string            `json:"nanoid"`
		Name        string            `json:"name"`
		DID         string            `json:"did"`
		Tier        string            `json:"tier"`
		Language    string            `json:"language"`
		Framework   string            `json:"framework"`
		CFBindings  []string          `json:"cf_bindings"`
		NPMDeps     []string          `json:"npm_deps"`
		CargoCrates []string          `json:"cargo_crates"`
		WITImports  []string          `json:"wit_imports"`
		Collections []string          `json:"subscribeRepos_collections"`
		Features    map[string]bool   `json:"features"`
	}

	out := sbomOutput{
		Nanoid:      found.Nanoid,
		Name:        found.Name,
		DID:         found.DID,
		Tier:        found.Tier,
		Language:    stack.Language,
		Framework:   stack.Framework,
		CFBindings:  stack.CFBindings,
		NPMDeps:     stack.NPMDeps,
		CargoCrates: stack.CargoCrates,
		WITImports:  stack.WITImports,
		Collections: found.Collections,
		Features: map[string]bool{
			"webgpu":      stack.HasWebGPU,
			"onnx":        stack.HasONNX,
			"fido2":       stack.HasFIDO2,
			"signal_e2e":  stack.HasSignal,
			"wasm":        stack.HasWASM,
			"mcp":         stack.HasMCP,
			"bpmn":        stack.HasBPMN,
			"evolver":     stack.HasEvolver,
			"risingwave":   stack.HasRisingWave,
			"workers_ai":  stack.HasWorkersAI,
			"browser":     stack.HasBrowser,
			"svelte":      stack.HasSvelte,
			"subscribe":   stack.HasSubscribe,
		},
	}

	if *jsonOut {
		return encodeJSON(out)
	}

	fmt.Printf("SBOM: %s  (%s)\n\n", out.Name, out.Nanoid)
	fmt.Printf("Language:   %s\n", out.Language)
	fmt.Printf("Framework:  %s\n", out.Framework)
	fmt.Printf("Tier:       %s\n\n", out.Tier)

	fmt.Printf("CF Bindings (%d):\n", len(out.CFBindings))
	for _, b := range out.CFBindings {
		fmt.Printf("  %s\n", b)
	}

	if len(out.NPMDeps) > 0 {
		fmt.Printf("\nNPM Deps (%d notable):\n", len(out.NPMDeps))
		for _, d := range out.NPMDeps {
			fmt.Printf("  %s\n", d)
		}
	}
	if len(out.CargoCrates) > 0 {
		fmt.Printf("\nCargo Crates (%d):\n", len(out.CargoCrates))
		for _, c := range out.CargoCrates {
			fmt.Printf("  %s\n", c)
		}
	}
	if len(out.WITImports) > 0 {
		fmt.Printf("\nWIT Imports (%d):\n", len(out.WITImports))
		for _, i := range out.WITImports {
			fmt.Printf("  import %s\n", i)
		}
	}
	if len(out.Collections) > 0 {
		fmt.Printf("\nSubscribeRepos Collections (%d):\n", len(out.Collections))
		for _, c := range out.Collections {
			fmt.Printf("  %s\n", c)
		}
	}

	fmt.Printf("\nFeatures:\n")
	var feats []string
	for k, v := range out.Features {
		if v {
			feats = append(feats, k)
		}
	}
	sort.Strings(feats)
	for _, f := range feats {
		fmt.Printf("  ✓ %s\n", f)
	}

	return nil
}

// ── Matrix subcommand ──────────────────────────────────────────────────────

func runKoseiMatrix(args []string) error {
	fs := flag.NewFlagSet("kosei matrix", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	filterTier := fs.String("tier", "", "filter by tier: T1, T2, T3")
	limit := fs.Int("limit", 50, "max apps to show (0=all)")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	if *filterTier != "" {
		ft := strings.ToUpper(*filterTier)
		var filtered []koseiAppState
		for _, s := range states {
			if s.Tier == ft {
				filtered = append(filtered, s)
			}
		}
		states = filtered
	}

	sort.Slice(states, func(i, j int) bool {
		if states[i].Tier != states[j].Tier {
			return states[i].Tier < states[j].Tier
		}
		return states[i].Nanoid < states[j].Nanoid
	})

	if *limit > 0 && len(states) > *limit {
		states = states[:*limit]
	}

	type matrixRow struct {
		Nanoid     string `json:"nanoid"`
		Name       string `json:"name"`
		Tier       string `json:"tier"`
		Language   string `json:"language"`
		UIType     string `json:"ui_type"`
		HasSvelte  bool   `json:"svelte"`
		HasWebGPU  bool   `json:"webgpu"`
		HasONNX    bool   `json:"onnx"`
		HasFIDO2   bool   `json:"fido2"`
		HasSignal  bool   `json:"signal_e2e"`
		HasWASM    bool   `json:"wasm"`
		HasMCP     bool   `json:"mcp"`
		HasBPMN    bool   `json:"bpmn"`
		HasAI      bool   `json:"workers_ai"`
		HasBrowser bool   `json:"browser"`
		HasKagami  bool   `json:"risingwave"`
		HasYata    bool   `json:"yata"`
		HasEvolver bool   `json:"evolver"`
		HasSub     bool   `json:"subscribe"`
		CollCount  int    `json:"coll_count"`
	}

	var rows []matrixRow
	for _, s := range states {
		appDir := filepath.Join(wsRoot, s.Dir)
		st := koseiScanStack(appDir, s.koseiAppMeta)
		rows = append(rows, matrixRow{
			Nanoid:     s.Nanoid,
			Name:       s.Name,
			Tier:       s.Tier,
			Language:   st.Language,
			UIType:     s.UIType,
			HasSvelte:  st.HasSvelte,
			HasWebGPU:  st.HasWebGPU,
			HasONNX:    st.HasONNX,
			HasFIDO2:   st.HasFIDO2,
			HasSignal:  st.HasSignal,
			HasWASM:    st.HasWASM,
			HasMCP:     st.HasMCP,
			HasBPMN:    st.HasBPMN,
			HasAI:      st.HasWorkersAI,
			HasBrowser: st.HasBrowser,
			HasKagami:  st.HasRisingWave,
			HasYata:    st.HasYata,
			HasEvolver: st.HasEvolver,
			HasSub:     st.HasSubscribe,
			CollCount:  st.CollCount,
		})
	}

	if *jsonOut {
		return encodeJSON(rows)
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 1, ' ', 0)
	// Header
	fmt.Fprintln(w, "NANOID\tNAME\tTIER\tLANG\tUI\tSVLT\tWGPU\tONNX\tFIDO\tSIGN\tWASM\tMCP\tBPMN\tAI\tBROW\tSR\tYATA\tEVOL\tSUB\tCOLL")
	fmt.Fprintln(w, "──────\t────\t────\t────\t──\t────\t────\t────\t────\t────\t────\t───\t────\t──\t────\t──\t────\t────\t───\t────")
	for _, r := range rows {
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\n",
			r.Nanoid, truncStr(r.Name, 20), r.Tier,
			shortLang(r.Language), shortUI(r.UIType),
			boolDot(r.HasSvelte), boolDot(r.HasWebGPU), boolDot(r.HasONNX),
			boolDot(r.HasFIDO2), boolDot(r.HasSignal), boolDot(r.HasWASM),
			boolDot(r.HasMCP), boolDot(r.HasBPMN), boolDot(r.HasAI),
			boolDot(r.HasBrowser), boolDot(r.HasKagami), boolDot(r.HasYata),
			boolDot(r.HasEvolver), boolDot(r.HasSub), r.CollCount,
		)
	}
	w.Flush()
	fmt.Printf("\n%d apps | SVLT=Svelte  WGPU=WebGPU  ONNX  FIDO=FIDO2  SIGN=Signal  WASM  MCP  BPMN  AI=WorkersAI  BROW=Browser  SR=RisingWave  YATA  EVOL=Evolver  SUB=subscribeRepos\n", len(rows))
	return nil
}

// ── Stats subcommand ───────────────────────────────────────────────────────

func runKoseiStats(args []string) error {
	fs := flag.NewFlagSet("kosei stats", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, dDir, err := koseiResolveRoots(*workspaceDir, *dataDir)
	if err != nil {
		return err
	}

	states, err := koseiLoadStates(wsRoot, dDir)
	if err != nil {
		return err
	}

	type stats struct {
		TotalApps    int     `json:"total_apps"`
		SystemEta    float64 `json:"system_eta"`
		TierCounts   map[string]int `json:"tier_counts"`
		Languages    map[string]int `json:"languages"`
		UITypes      map[string]int `json:"ui_types"`
		FeatureCounts map[string]int `json:"feature_counts"`
	}

	st := stats{
		TotalApps:    len(states),
		TierCounts:   make(map[string]int),
		Languages:    make(map[string]int),
		UITypes:      make(map[string]int),
		FeatureCounts: make(map[string]int),
	}
	st.SystemEta = koseiSystemEta(states)

	for _, s := range states {
		st.TierCounts[s.Tier]++
		st.UITypes[s.UIType]++
	}

	fmt.Fprintf(os.Stderr, "Scanning stacks (%d apps)...\n", len(states))
	for _, s := range states {
		appDir := filepath.Join(wsRoot, s.Dir)
		stack := koseiScanStack(appDir, s.koseiAppMeta)
		st.Languages[stack.Language]++
		if stack.HasWebGPU { st.FeatureCounts["webgpu"]++ }
		if stack.HasONNX { st.FeatureCounts["onnx"]++ }
		if stack.HasFIDO2 { st.FeatureCounts["fido2"]++ }
		if stack.HasSignal { st.FeatureCounts["signal_e2e"]++ }
		if stack.HasWASM { st.FeatureCounts["wasm"]++ }
		if stack.HasMCP { st.FeatureCounts["mcp"]++ }
		if stack.HasBPMN { st.FeatureCounts["bpmn"]++ }
		if stack.HasWorkersAI { st.FeatureCounts["workers_ai"]++ }
		if stack.HasBrowser { st.FeatureCounts["browser"]++ }
		if stack.HasRisingWave { st.FeatureCounts["risingwave"]++ }
		if stack.HasYata { st.FeatureCounts["yata"]++ }
		if stack.HasEvolver { st.FeatureCounts["evolver"]++ }
		if stack.HasSubscribe { st.FeatureCounts["subscribe_repos"]++ }
		if stack.HasSvelte { st.FeatureCounts["svelte"]++ }
		if stack.HasSignal { st.FeatureCounts["signal"]++ }
		if stack.HasGame { st.FeatureCounts["game"]++ }
		if stack.HasDesktop { st.FeatureCounts["desktop"]++ }
		if stack.HasSpace { st.FeatureCounts["space_channel"]++ }
		if stack.HasConvoPrmpt { st.FeatureCounts["convo_prompt"]++ }
		if stack.HasWIT { st.FeatureCounts["wit_contract"]++ }
	}

	if *jsonOut {
		return encodeJSON(st)
	}

	fmt.Printf("gftd kosei stats — %d apps  system η=%.3f\n\n", st.TotalApps, st.SystemEta)

	fmt.Printf("Tier Distribution:\n")
	for _, t := range []string{"T1", "T2", "T3", "?"} {
		n := st.TierCounts[t]
		fmt.Printf("  %s  %4d  (%5.1f%%)\n", t, n, float64(n)/float64(st.TotalApps)*100)
	}

	fmt.Printf("\nLanguages:\n")
	langs := koseiSortedMapKeys(st.Languages)
	for _, l := range langs {
		fmt.Printf("  %-15s  %4d\n", l, st.Languages[l])
	}

	fmt.Printf("\nUI Types:\n")
	uis := koseiSortedMapKeys(st.UITypes)
	for _, u := range uis {
		fmt.Printf("  %-15s  %4d\n", u, st.UITypes[u])
	}

	fmt.Printf("\nFeature Adoption:\n")
	type featCount struct{ name string; count int }
	var feats []featCount
	for k, v := range st.FeatureCounts {
		feats = append(feats, featCount{k, v})
	}
	sort.Slice(feats, func(i, j int) bool { return feats[i].count > feats[j].count })
	for _, f := range feats {
		bar := strings.Repeat("█", f.count*30/st.TotalApps)
		fmt.Printf("  %-20s  %4d  %s\n", f.name, f.count, bar)
	}

	return nil
}

// ── Extended snapshot with stack ───────────────────────────────────────────

// koseiSnapshotRowFull extends koseiSnapshotRow with full stack fields.
type koseiSnapshotRowFull struct {
	// Identity + tier (from koseiSnapshotRow)
	SnapshotAt    string  `json:"snapshot_at"`
	AppName       string  `json:"app_name"`
	Nanoid        string  `json:"nanoid"`
	DID           string  `json:"did"`
	Tier          string  `json:"tier"`
	Efficiency    float64 `json:"efficiency"`
	PerformerType string  `json:"performer_type"`
	UIType        string  `json:"ui_type"`
	RuntimeType   string  `json:"runtime_type"`
	AssignedBy    string  `json:"assigned_by"`
	Notes         string  `json:"notes"`

	// Stack
	Language     string `json:"language"`
	Framework    string `json:"framework"`
	ContentMode  string `json:"content_mode"`
	HasSvelte    bool   `json:"has_svelte"`
	HasWebGPU    bool   `json:"has_webgpu"`
	HasONNX      bool   `json:"has_onnx"`
	HasFIDO2     bool   `json:"has_fido2"`
	HasSignal    bool   `json:"has_signal"`
	HasWASM      bool   `json:"has_wasm"`
	HasMCP       bool   `json:"has_mcp"`
	HasBPMN      bool   `json:"has_bpmn"`
	HasWorkersAI bool   `json:"has_workers_ai"`
	HasBrowser   bool   `json:"has_browser"`
	HasRisingWave bool   `json:"has_risingwave"`
	HasYata      bool   `json:"has_yata"`
	HasGraphSQL bool   `json:"has_graph_sql"`
	HasEvolver   bool   `json:"has_evolver"`
	HasSpace     bool   `json:"has_space"`
	HasGame      bool   `json:"has_game"`
	HasDesktop   bool   `json:"has_desktop"`
	HasSubscribe bool   `json:"has_subscribe"`
	CollCount    int    `json:"coll_count"`
	RequireCount int    `json:"require_count"`
	ProvideCount int    `json:"provide_count"`
	R2Count      int    `json:"r2_count"`
	ServiceCount int    `json:"service_count"`
	SecretCount  int    `json:"secret_count"`
	NPMDepCount  int    `json:"npm_dep_count"`
	WITImportCount int  `json:"wit_import_count"`
	HasWIT       bool   `json:"has_wit"`
}

// ── Helpers ────────────────────────────────────────────────────────────────

func boolStr(b bool) string {
	if b {
		return "yes"
	}
	return "—"
}

func boolDot(b bool) string {
	if b {
		return "●"
	}
	return "·"
}

func shortLang(l string) string {
	switch l {
	case "typescript":
		return "TS"
	case "rust":
		return "RS"
	case "go":
		return "GO"
	case "python":
		return "PY"
	default:
		return "??"
	}
}

func shortUI(u string) string {
	switch u {
	case "appview":
		return "APP"
	case "yoro":
		return "YRO"
	default:
		return "—  "
	}
}

func koseiSortedMapKeys(m map[string]int) []string {
	keys := make([]string, 0, len(m))
	for k := range m {
		keys = append(keys, k)
	}
	sort.Strings(keys)
	return keys
}
