package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// nonoManifest represents a nono-manifest.jsonld capability provider definition.
type nonoManifest struct {
	Context          string            `json:"@context"`
	ID               string            `json:"@id"`
	Name             string            `json:"name"`
	Nanoid           string            `json:"nanoid"`
	Type             string            `json:"type"` // always "nono"
	Bindings         []string          `json:"bindings"`
	PrimitiveBackend []string          `json:"primitiveBackend,omitempty"`
	Skills           []nonoSkill       `json:"skills,omitempty"`
	Governance       *governanceConfig `json:"governance,omitempty"`
}

type nonoSkill struct {
	NSID         string `json:"nsid"`
	Description  string `json:"description"`
	InputSchema  any    `json:"inputSchema,omitempty"`
	OutputSchema any    `json:"outputSchema,omitempty"`
}

// runNono implements `gftd nono` — capability Worker lifecycle.
//
// Usage:
//
//	gftd nono build  [-dir <path>]   # esbuild + validation
//	gftd nono deploy [-dir <path>]   # CF Worker deploy + skill registration
//	gftd nono list                   # list all nono capability Workers
//	gftd nono skills <nanoid>        # list skills provided by a nono
func runNono(args []string) error {
	if len(args) == 0 {
		fmt.Println(`gftd nono — capability Worker lifecycle

SUBCOMMANDS:
  build   [-dir <path>]    Build nono Worker (esbuild + validation)
  deploy  [-dir <path>]    Deploy nono Worker + register skills
  list                     List all nono capability Workers
  skills  <nanoid|name>    List skills provided by a nono`)
		return nil
	}

	switch args[0] {
	case "build":
		return runNonoBuild(args[1:])
	case "deploy":
		return runNonoDeploy(args[1:])
	case "list":
		return runNonoList(args[1:])
	case "skills":
		return runNonoSkills(args[1:])
	default:
		return fmt.Errorf("unknown nono subcommand: %s. Available: build, deploy, list, skills", args[0])
	}
}

// runNonoBuild builds a nono Worker (validates + esbuild).
func runNonoBuild(args []string) error {
	fs := flag.NewFlagSet("nono build", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component directory")
	if err := fs.Parse(args); err != nil {
		return err
	}

	compDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}

	// Must have magatama.jsonld (nono Workers still use magatama.jsonld for deploy config)
	cfg, err := readMagatamaJSONLD(compDir)
	if err != nil {
		return fmt.Errorf("magatama.jsonld required: %w", err)
	}

	fmt.Printf("[nono build] %s (nanoid: %s)\n", cfg.Name, cfg.Nanoid)

	// Validate src/app.ts exists
	appTs := filepath.Join(compDir, "src", "app.ts")
	if _, err := os.Stat(appTs); err != nil {
		return fmt.Errorf("src/app.ts not found — nono Workers require app.ts entry point")
	}
	fmt.Printf("  ✓ src/app.ts exists\n")

	// Check for CF bindings that justify nono status
	nonoManifestPath := filepath.Join(compDir, "nono-manifest.jsonld")
	if _, err := os.Stat(nonoManifestPath); err == nil {
		data, _ := os.ReadFile(nonoManifestPath)
		var nm nonoManifest
		if json.Unmarshal(data, &nm) == nil && len(nm.Bindings) > 0 {
			fmt.Printf("  ✓ nono-manifest.jsonld (bindings: %s)\n", strings.Join(nm.Bindings, ", "))
		}
	} else {
		fmt.Printf("  ℹ no nono-manifest.jsonld (optional — bindings documented in wrangler.jsonc)\n")
	}

	// Delegate to standard build
	fmt.Printf("\n[nono build] Running standard build...\n")
	return runBuild([]string{"-dir", compDir})
}

// runNonoDeploy deploys a nono Worker and registers skills.
func runNonoDeploy(args []string) error {
	fs := flag.NewFlagSet("nono deploy", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component directory")
	skipSkills := fs.Bool("skip-skills", false, "skip skill registration after deploy")
	if err := fs.Parse(args); err != nil {
		return err
	}

	compDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}

	cfg, err := readMagatamaJSONLD(compDir)
	if err != nil {
		return fmt.Errorf("magatama.jsonld required: %w", err)
	}

	appID := cfg.AppID()
	fmt.Printf("[nono deploy] Phase 1: Worker deploy\n")
	fmt.Printf("  name: %s, nanoid: %s\n", cfg.Name, appID)

	// Standard Worker deploy (wrangler)
	if err := deployWorker(cfg, compDir, deployWorkerOptions{}); err != nil {
		return fmt.Errorf("worker deploy failed: %w", err)
	}

	if *skipSkills {
		fmt.Printf("\n[nono deploy] Skill registration skipped (--skip-skills)\n")
		return nil
	}

	// Phase 2: Register nono skills to graph
	fmt.Printf("\n[nono deploy] Phase 2: Skill registration\n")

	nonoManifestPath := filepath.Join(compDir, "nono-manifest.jsonld")
	if _, err := os.Stat(nonoManifestPath); err != nil {
		fmt.Printf("  ℹ no nono-manifest.jsonld — skill registration skipped\n")
		fmt.Printf("  ℹ skills are auto-discovered from sdk.app.command() via MCP tools/list\n")
		return nil
	}

	data, err := os.ReadFile(nonoManifestPath)
	if err != nil {
		return fmt.Errorf("read nono-manifest.jsonld: %w", err)
	}

	var nm nonoManifest
	if err := json.Unmarshal(data, &nm); err != nil {
		return fmt.Errorf("parse nono-manifest.jsonld: %w", err)
	}

	token := resolveGFTDToken()
	if token == "" {
		fmt.Printf("  ⚠ no auth token — skill registration requires authentication\n")
		return nil
	}

	// Register nono manifest to graph
	pdsBase := resolvePDSBaseURL()
	regBody, _ := json.Marshal(map[string]any{
		"@context":         "https://etzhayyim.com/ns/nono/v1",
		"@id":              nm.ID,
		"name":             nm.Name,
		"nanoid":           nm.Nanoid,
		"type":             "nono",
		"bindings":         nm.Bindings,
		"primitiveBackend": nm.PrimitiveBackend,
		"skills":           nm.Skills,
		"status":           "active",
	})

	req, err := http.NewRequest("POST", pdsBase+"/xrpc/ai.gftd.actor.registerManifest", strings.NewReader(string(regBody)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Printf("  ⚠ skill registration failed: %v\n", err)
		return nil
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		fmt.Printf("  ⚠ skill registration HTTP %d\n", resp.StatusCode)
		return nil
	}

	fmt.Printf("  ✓ nono registered: %s (%d bindings, %d skills)\n",
		nm.Name, len(nm.Bindings), len(nm.Skills))

	if len(nm.PrimitiveBackend) > 0 {
		fmt.Printf("  ✓ primitive backend: %s\n", strings.Join(nm.PrimitiveBackend, ", "))
	}

	for _, skill := range nm.Skills {
		fmt.Printf("    - %s: %s\n", skill.NSID, skill.Description)
	}

	fmt.Printf("\n[nono deploy] Complete: %s deployed as capability Worker\n", nm.Name)
	return nil
}

// runNonoList lists all registered nono capability Workers.
func runNonoList(args []string) error {
	fs := flag.NewFlagSet("nono list", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		return err
	}

	token := resolveGFTDToken()
	if token == "" {
		// Offline mode: scan 60-apps for nono candidates
		return nonoListOffline()
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	result, err := db.RawQuery(ctx, `
		SELECT did, name, nanoid, bindings
		FROM vertex_actor_manifest
		WHERE type = 'nono' AND status = 'active'
		ORDER BY name
		LIMIT 50
	`)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  database query failed, falling back to offline scan\n")
		return nonoListOffline()
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(result)
	}

	rows := result.Rows
	if len(rows) == 0 {
		fmt.Println("No nono Workers registered in database. Showing offline scan:")
		return nonoListOffline()
	}

	fmt.Printf("%-20s %-12s %-30s %s\n", "NAME", "NANOID", "BINDINGS", "DID")
	fmt.Printf("%-20s %-12s %-30s %s\n", "----", "------", "--------", "---")
	for _, r := range rows {
		fmt.Printf("%-20s %-12s %-30s %s\n",
			r["name"], r["nanoid"], r["bindings"], r["did"])
	}
	return nil
}

// nonoListOffline lists known nono Workers from hardcoded registry.
func nonoListOffline() error {
	nonos := []struct {
		name    string
		binding string
		backend string
		nanoid  string
	}{
		{"llm", "env.AI (Workers AI)", "agent.chat", "llm8cf4ai"},
		{"site", "HEADLESS_BROWSER", "browser.fetch", "w3bpg001"},
		{"livecam", "Murakumo CoreML fleet", "-", "zio3cb3r"},
		{"mangaka", "env.AI (flux-1-schnell)", "-", "mng4k4x1"},
		{"briefing", "WebRTC (kami-rtc)", "-", "w3olw1pf"},
		{"stripe", "Stripe API + Webhooks", "-", "st4rp301"},
		{"watashi", "Native CGEvent/Win32", "-", "mfbtsuyc"},
		{"sense", "Camera/LiDAR/WiFi/BT/Mic", "-", "sense"},
		{"pptx", "wgpu WebGPU rendering", "-", "t53br1o0"},
		{"xlsx", "HTML DOM grid", "-", "il0ndq6a"},
	}

	fmt.Printf("%-15s %-12s %-30s %s\n", "NAME", "NANOID", "CF BINDING", "PRIMITIVE BACKEND")
	fmt.Printf("%-15s %-12s %-30s %s\n", "----", "------", "----------", "----------------")
	for _, n := range nonos {
		fmt.Printf("%-15s %-12s %-30s %s\n", n.name, n.nanoid, n.binding, n.backend)
	}
	fmt.Printf("\nTotal: %d nono capability Workers\n", len(nonos))
	return nil
}

// runNonoSkills lists skills provided by a specific nono.
func runNonoSkills(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: gftd nono skills <nanoid|name>")
	}
	target := args[0]

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no auth token — run: gftd auth login")
	}

	// Resolve DID from nanoid or name
	did := target
	if !strings.HasPrefix(did, "did:") {
		did = "did:web:" + target + ".etzhayyim.com"
	}

	pdsBase := resolvePDSBaseURL()

	// Try to fetch nono manifest from graph
	body := fmt.Sprintf(`{"did":"%s"}`, did)
	req, err := http.NewRequest("POST", pdsBase+"/xrpc/ai.gftd.actor.getManifest", strings.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode == 404 {
		// Fallback: query MCP tools/list from the nono Worker directly
		fmt.Printf("No manifest in graph. Querying MCP tools/list from %s...\n\n", target)
		return nonoSkillsFromMCP(target)
	}

	var manifest map[string]any
	json.NewDecoder(resp.Body).Decode(&manifest)

	skills, _ := manifest["skills"].([]any)
	primitiveBackend, _ := manifest["primitiveBackend"].([]any)
	bindings, _ := manifest["bindings"].([]any)

	name, _ := manifest["name"].(string)
	fmt.Printf("Nono: %s\n", name)
	if len(bindings) > 0 {
		fmt.Printf("Bindings: %v\n", bindings)
	}
	if len(primitiveBackend) > 0 {
		fmt.Printf("Primitive Backend: %v\n", primitiveBackend)
	}
	fmt.Printf("\nSkills (%d):\n", len(skills))
	for _, s := range skills {
		skill, _ := s.(map[string]any)
		fmt.Printf("  %-50s %s\n", skill["nsid"], skill["description"])
	}
	return nil
}

// nonoSkillsFromMCP queries MCP tools/list from a nono Worker endpoint.
func nonoSkillsFromMCP(nanoid string) error {
	mcpURL := "https://mcp.etzhayyim.com/mcp"
	body := fmt.Sprintf(`{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{"nanoid":"%s"}}`, nanoid)
	req, err := http.NewRequest("POST", mcpURL, strings.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("MCP query failed: %w", err)
	}
	defer resp.Body.Close()

	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)

	mcpResult, _ := result["result"].(map[string]any)
	tools, _ := mcpResult["tools"].([]any)

	fmt.Printf("MCP Tools (%d):\n", len(tools))
	for _, t := range tools {
		tool, _ := t.(map[string]any)
		fmt.Printf("  %-50s %s\n", tool["name"], tool["description"])
	}
	return nil
}
