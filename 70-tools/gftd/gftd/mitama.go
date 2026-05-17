package main

import (
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

// runMitama implements `gftd mitama` — register an actor-manifest.jsonld to the graph.
// No Worker deploy. No build. Just graph MERGE via PDS Shared Executor.
//
// Usage:
//
//	gftd mitama [-dir <path>]           # register actor manifest
//	gftd mitama list                    # list all T1 actors
//	gftd mitama inspect <did>           # inspect actor manifest
//	gftd mitama dormant <did>           # set actor status to dormant
//	gftd mitama revive <did>            # set actor status to active
//	gftd mitama shinka                  # coverage/gap fill + site+CC ingest + murakumo + actor shinka
func runMitama(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "list":
			return runMitamaList(args[1:])
		case "schema-status":
			return runMitamaSchemaStatus(args[1:])
		case "inspect":
			return runMitamaInspect(args[1:])
		case "dormant":
			return runMitamaDormant(args[1:])
		case "revive":
			return runMitamaRevive(args[1:])
		case "shinka", "collect":
			return runMitamaShinka(args[1:])
		}
	}
	return runMitamaRegister(args)
}

type mitamaShinkaStageResult struct {
	Stage      string `json:"stage"`
	Status     string `json:"status"`
	DurationMs int64  `json:"durationMs"`
	Error      string `json:"error,omitempty"`
}

func runMitamaShinka(args []string) error {
	fs := flag.NewFlagSet("mitama shinka", flag.ContinueOnError)
	domain := fs.String("domain", "maps", "domain key (seed app filter)")
	nanoid := fs.String("nanoid", "uqpel6i6", "target app nanoid for app coverage")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	crawl := fs.String("crawl", "CC-MAIN-2026-12", "Common Crawl crawl ID")
	ccDomain := fs.String("cc-domain", "", "CommonCrawler domain filter (e.g. *.go.jp)")
	ccModel := fs.String("cc-model", "qwen3.5-9b", "CommonCrawler intel model")
	ccMinPages := fs.Int("cc-min-pages", 20, "CommonCrawler intel min pages")
	ccLimit := fs.Int("cc-limit", 300, "CommonCrawler intel limit")
	ccConcurrency := fs.Int("cc-concurrency", 1, "CommonCrawler intel concurrency")
	downloadWorkers := fs.Int("download-workers", 4, "CommonCrawler download workers")
	withDownload := fs.Bool("with-download", false, "include CommonCrawler download stage")
	shinkaModel := fs.String("shinka-model", "qwen3.5-32b", "actors shinka model (Murakumo)")
	shinkaLimit := fs.Int("shinka-limit", 40, "actors shinka target actor count")
	shinkaConcurrency := fs.Int("shinka-concurrency", 4, "actors shinka concurrency")
	filter := fs.String("filter", "", "actors shinka filter (default: domain)")
	ccTopic := fs.String("cc-topic", "", "actors common-crawler-coverage topic filter")
	mapsHost := fs.String("maps-host", "https://maps.etzhayyim.com", "maps host for seedGeoDomains XRPC")
	ccIndex := fs.String("cc-index", "", "ccIndex passed to maps.seedGeoDomains (optional)")
	categories := fs.String("categories", "", "site seed categories csv (optional)")
	countries := fs.String("countries", "", "site seed countries csv (optional)")
	continueOnError := fs.Bool("continue-on-error", true, "continue pipeline even if a stage fails")
	dryRun := fs.Bool("dry-run", false, "print stages only; skip mutating operations")
	jsonOut := fs.Bool("json", false, "output stage result summary as JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	token := resolveGFTDToken()
	if token == "" && !*dryRun {
		return fmt.Errorf("no auth token — run: gftd auth login (or set GFTD_TOKEN)")
	}
	if token != "" {
		_ = os.Setenv("GFTD_TOKEN", token)
	}

	repoRoot, _ := findGitRoot(".")
	appDir := "60-apps"
	if strings.TrimSpace(repoRoot) != "" {
		appDir = filepath.Join(repoRoot, "60-apps")
	}

	shinkaFilter := strings.TrimSpace(*filter)
	if shinkaFilter == "" {
		shinkaFilter = strings.TrimSpace(*domain)
	}

	type stageDef struct {
		name   string
		action func() error
	}
	stages := make([]stageDef, 0, 12)
	stages = append(stages,
		stageDef{
			name: "coverage-before",
			action: func() error {
				return runWorldCoverage([]string{
					"-domain", *domain,
					"-pds", *pdsURL,
				})
			},
		},
		stageDef{
			name: "app-coverage-before",
			action: func() error {
				return runAppsCoverage([]string{
					"-nanoid", *nanoid,
					"-dir", appDir,
					"-pds", *pdsURL,
				})
			},
		},
		stageDef{
			name: "seed-gap",
			action: func() error {
				args := []string{
					"--app", *domain,
					"--pds", *pdsURL,
				}
				if *dryRun {
					args = append(args, "--dry-run")
				}
				return runSeed(args)
			},
		},
		stageDef{
			name: "site-seed",
			action: func() error {
				if *dryRun {
					return nil
				}
				return mitamaSeedGeoDomains(*mapsHost, token, *ccIndex, csvToList(*categories), csvToList(*countries))
			},
		},
	)
	if *withDownload {
		stages = append(stages, stageDef{
			name: "cc-download",
			action: func() error {
				args := []string{
					"download",
					"--crawl", *crawl,
					"--workers", fmt.Sprintf("%d", *downloadWorkers),
				}
				return runCommonCrawler(args)
			},
		})
	}
	stages = append(stages,
		stageDef{
			name: "cc-graph",
			action: func() error {
				return runCommonCrawler([]string{
					"graph",
					"--crawl", *crawl,
					"--output", "sql",
					"--domain", strings.TrimSpace(*ccDomain),
				})
			},
		},
		stageDef{
			name: "cc-intel",
			action: func() error {
				args := []string{
					"intel",
					"--model", *ccModel,
					"--limit", fmt.Sprintf("%d", *ccLimit),
					"--min-pages", fmt.Sprintf("%d", *ccMinPages),
					"--concurrency", fmt.Sprintf("%d", *ccConcurrency),
					"--resume",
				}
				if strings.TrimSpace(*ccDomain) != "" {
					args = append(args, "--domain", strings.TrimSpace(*ccDomain))
				}
				return runCommonCrawler(args)
			},
		},
		stageDef{
			name: "cc-inject",
			action: func() error {
				args := []string{
					"inject",
					"--source", "intel",
					"--pds", *pdsURL,
				}
				if *dryRun {
					args = append(args, "--dry-run")
				}
				return runCommonCrawler(args)
			},
		},
		stageDef{
			name: "murakumo-coverage-export",
			action: func() error {
				return runMurakumo([]string{
					"coverage-export",
					"--pds-url", *pdsURL,
				})
			},
		},
		stageDef{
			name: "murakumo-eval",
			action: func() error {
				return runMurakumo([]string{
					"eval",
					"--mode", "quick",
					"--limit", "20",
					"--pds-url", *pdsURL,
				})
			},
		},
		stageDef{
			name: "actors-shinka",
			action: func() error {
				args := []string{
					"--pds", *pdsURL,
					"--murakumo",
					"--model", *shinkaModel,
					"--limit", fmt.Sprintf("%d", *shinkaLimit),
					"--concurrency", fmt.Sprintf("%d", *shinkaConcurrency),
					"--filter", shinkaFilter,
				}
				if *dryRun {
					args = append(args, "--dry-run")
				}
				return runActorsShinka(args)
			},
		},
		stageDef{
			name: "cc-coverage",
			action: func() error {
				args := []string{"--format", "text", "--top", "30"}
				if strings.TrimSpace(*ccTopic) != "" {
					args = append(args, "--topic", strings.TrimSpace(*ccTopic))
				}
				if *ccMinPages > 0 {
					args = append(args, "--min-pages", fmt.Sprintf("%d", *ccMinPages))
				}
				return runActorsCCCoverage(args)
			},
		},
		stageDef{
			name: "app-coverage-after",
			action: func() error {
				return runAppsCoverage([]string{
					"-nanoid", *nanoid,
					"-dir", appDir,
					"-pds", *pdsURL,
				})
			},
		},
		stageDef{
			name: "coverage-after",
			action: func() error {
				return runWorldCoverage([]string{
					"-domain", *domain,
					"-pds", *pdsURL,
				})
			},
		},
	)

	results := make([]mitamaShinkaStageResult, 0, len(stages))
	var failures int
	for _, st := range stages {
		start := time.Now()
		fmt.Printf("\n[mitama.shinka] stage=%s\n", st.name)
		if *dryRun {
			fmt.Printf("[mitama.shinka] dry-run skip stage execution\n")
			results = append(results, mitamaShinkaStageResult{
				Stage:      st.name,
				Status:     "skipped",
				DurationMs: time.Since(start).Milliseconds(),
			})
			continue
		}
		err := st.action()
		row := mitamaShinkaStageResult{
			Stage:      st.name,
			DurationMs: time.Since(start).Milliseconds(),
		}
		if err != nil {
			row.Status = "failed"
			row.Error = err.Error()
			failures++
			fmt.Fprintf(os.Stderr, "[mitama.shinka] stage failed: %s: %v\n", st.name, err)
			results = append(results, row)
			if !*continueOnError {
				break
			}
			continue
		}
		row.Status = "ok"
		results = append(results, row)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(map[string]any{
			"pipeline": "mitama.shinka",
			"domain":   *domain,
			"nanoid":   *nanoid,
			"dryRun":   *dryRun,
			"results":  results,
			"failures": failures,
		})
	}

	if failures > 0 {
		return fmt.Errorf("mitama shinka completed with %d failed stages", failures)
	}
	fmt.Printf("\n[mitama.shinka] complete: %d stages OK\n", len(results))
	return nil
}

func csvToList(s string) []string {
	v := strings.TrimSpace(s)
	if v == "" {
		return nil
	}
	parts := strings.Split(v, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		t := strings.TrimSpace(p)
		if t != "" {
			out = append(out, t)
		}
	}
	return out
}

func mitamaSeedGeoDomains(mapsHost, token, ccIndex string, categories, countries []string) error {
	host := strings.TrimRight(strings.TrimSpace(mapsHost), "/")
	if host == "" {
		return fmt.Errorf("maps host is empty")
	}
	body := map[string]any{}
	if strings.TrimSpace(ccIndex) != "" {
		body["ccIndex"] = strings.TrimSpace(ccIndex)
	}
	if len(categories) > 0 {
		body["categories"] = categories
	}
	if len(countries) > 0 {
		body["countries"] = countries
	}
	b, _ := json.Marshal(body)
	req, err := http.NewRequest("POST", host+"/xrpc/ai.gftd.apps.maps.seedGeoDomains", bytes.NewReader(b))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	if strings.TrimSpace(token) != "" {
		req.Header.Set("Authorization", "Bearer "+strings.TrimSpace(token))
	}
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("seedGeoDomains failed (HTTP %d): %s", resp.StatusCode, truncStr(string(respBody), 300))
	}
	fmt.Printf("[mitama.shinka] site-seed response: %s\n", truncStr(string(respBody), 300))
	return nil
}

// runMitamaRegister reads actor-manifest.jsonld and registers it via PDS XRPC.
func runMitamaRegister(args []string) error {
	fs := flag.NewFlagSet("mitama", flag.ContinueOnError)
	dir := fs.String("dir", ".", "directory containing actor-manifest.jsonld")
	dryRun := fs.Bool("dry-run", false, "validate only, do not register")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	absDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}

	// Find actor-manifest.jsonld
	manifestPath := filepath.Join(absDir, "actor-manifest.jsonld")
	if _, err := os.Stat(manifestPath); err != nil {
		return fmt.Errorf("actor-manifest.jsonld not found in %s", absDir)
	}

	// Read and parse manifest
	data, err := os.ReadFile(manifestPath)
	if err != nil {
		return fmt.Errorf("read manifest: %w", err)
	}

	var manifest map[string]any
	if err := json.Unmarshal(data, &manifest); err != nil {
		return fmt.Errorf("parse manifest: %w", err)
	}

	// Validate required fields
	errors := validateActorManifest(manifest)
	if len(errors) > 0 {
		fmt.Fprintf(os.Stderr, "[mitama] Validation errors:\n")
		for _, e := range errors {
			fmt.Fprintf(os.Stderr, "  ✗ %s\n", e)
		}
		return fmt.Errorf("manifest validation failed (%d errors)", len(errors))
	}

	did := manifest["@id"].(string)
	name := manifest["name"].(string)
	nanoid := manifest["nanoid"].(string)
	runtime := actorManifestRuntime(manifest)
	edge := actorManifestEdge(manifest)

	fmt.Printf("[mitama] Phase 1: 検証\n")
	fmt.Printf("  ✓ actor-manifest.jsonld (name: %s, nanoid: %s, did: %s)\n", name, nanoid, did)
	fmt.Printf("  ✓ runtime: %s\n", runtime)
	fmt.Printf("  ✓ edge: %s\n", edge)

	if caps, ok := manifest["capabilities"].([]any); ok {
		fmt.Printf("  ✓ capabilities: %d primitives\n", len(caps))
	}
	if pipelines, ok := manifest["pipelines"].([]any); ok {
		fmt.Printf("  ✓ pipelines: %d\n", len(pipelines))
	}
	if actors, ok := manifest["actors"].([]any); ok {
		fmt.Printf("  ✓ actors (path-based DIDs): %d\n", len(actors))
	}

	if *dryRun {
		fmt.Printf("\n[mitama] Dry run — validation passed. No registration.\n")
		return nil
	}

	// Resolve auth token
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no auth token — run: gftd auth login")
	}

	// Phase 2: Register manifest via PDS XRPC
	fmt.Printf("\n[mitama] Phase 2: 魂入れ (graph MERGE)\n")

	pdsBase := resolvePDSBaseURL()
	registerURL := pdsBase + "/xrpc/ai.gftd.actor.registerManifest"

	body, _ := json.Marshal(manifest)
	req, err := http.NewRequest("POST", registerURL, strings.NewReader(string(body)))
	if err != nil {
		return fmt.Errorf("create request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("register manifest: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		var errBody map[string]any
		json.NewDecoder(resp.Body).Decode(&errBody)
		return fmt.Errorf("registration failed (HTTP %d): %v", resp.StatusCode, errBody)
	}

	var result map[string]any
	json.NewDecoder(resp.Body).Decode(&result)

	fmt.Printf("  ✓ ActorManifest MERGED in graph (did: %s)\n", did)
	fmt.Printf("  ✓ PDS Shared Executor will execute pipelines on cron/subscribeRepos triggers\n")

	fmt.Printf("\n[mitama] 魂入れ完了: %s は自律稼働を開始しました\n", did)
	fmt.Printf("  Worker deploy: 不要\n")
	fmt.Printf("  Build: 不要\n")
	fmt.Printf("  Runtime: %s via AgentGateway MCP\n", runtime)

	return nil
}

func actorManifestRuntime(m map[string]any) string {
	if runtime, ok := m["runtime"].(string); ok && runtime != "" {
		return runtime
	}
	if tier, ok := m["executionTier"].(string); ok && tier != "" {
		return "legacy-" + tier
	}
	return ""
}

func actorManifestEdge(m map[string]any) string {
	if edge, ok := m["edge"].(string); ok && edge != "" {
		return edge
	}
	return "sveltekit-proxy"
}

// validateActorManifest validates required fields in an actor manifest.
func validateActorManifest(m map[string]any) []string {
	var errors []string

	if ctx, ok := m["@context"].(string); !ok || ctx != "https://etzhayyim.com/ns/actor/v1" {
		errors = append(errors, `@context must be "https://etzhayyim.com/ns/actor/v1"`)
	}
	if id, ok := m["@id"].(string); !ok || !strings.HasPrefix(id, "did:") {
		errors = append(errors, "@id must be a DID")
	}
	if _, ok := m["name"].(string); !ok {
		errors = append(errors, "name required")
	}
	if _, ok := m["nanoid"].(string); !ok {
		errors = append(errors, "nanoid required")
	}
	runtime := actorManifestRuntime(m)
	if runtime != "k8s-langserver" && runtime != "legacy-T1" && runtime != "legacy-T2" && runtime != "legacy-T3" {
		errors = append(errors, "runtime must be k8s-langserver")
	}
	edge := actorManifestEdge(m)
	if edge != "sveltekit-proxy" {
		errors = append(errors, "edge must be sveltekit-proxy")
	}

	validPrimitives := map[string]bool{
		"graph.query": true, "graph.write": true, "graph.vectorSearch": true,
		"agent.chat": true, "agent.invoke": true, "identity.resolve": true,
		"browser.fetch": true, "signal.encrypt": true, "consent.check": true,
		"derive:social": true, "dmn.evaluate": true, "form.collect": true,
	}
	if caps, ok := m["capabilities"].([]any); ok {
		for _, cap := range caps {
			if capStr, ok := cap.(string); ok && !validPrimitives[capStr] {
				errors = append(errors, fmt.Sprintf("invalid capability: %s", capStr))
			}
		}
	}

	// k8s-langserver actors still expose declarative pipelines; custom code
	// belongs behind AgentGateway MCP as a LangServer method, not in manifest.
	if runtime == "k8s-langserver" || runtime == "legacy-T1" {
		if pipelines, ok := m["pipelines"].([]any); ok {
			for _, p := range pipelines {
				pipeline, _ := p.(map[string]any)
				steps, _ := pipeline["steps"].([]any)
				for _, s := range steps {
					step, _ := s.(map[string]any)
					if fn, _ := step["fn"].(string); fn == "custom" {
						errors = append(errors, "T1 actors cannot have custom handlers (use T2)")
					}
				}
			}
		}
	}

	errors = append(errors, validateGraphWriteSchemaGuards(m)...)

	return errors
}

func validateGraphWriteSchemaGuards(m map[string]any) []string {
	var errs []string
	pipelines, _ := m["pipelines"].([]any)
	if len(pipelines) == 0 {
		return nil
	}

	// ActorCoverageSnapshot is mapped to graphar.vertex_actor_coverage.
	allowed := map[string]bool{
		"vertex_id": true, "rkey": true, "repo": true, "did": true,
		"collection": true, "status": true,
		"actorDid": true, "actorName": true, "nanoid": true, "bucket": true,
		"nodeCount": true, "latestTs": true, "topCollections": true,
		"freshnessRate": true, "totalNodes": true, "freshNodes": true, "snapshotTs": true,
		"_alive": true, "_seq": true,
	}

	reMerge := regexp.MustCompile(`MERGE\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(ActorCoverageSnapshot)\s*\{`)
	reMergeBody := regexp.MustCompile(`MERGE\s*\(\s*%s\s*:\s*%s\s*\{([^}]*)\}`)
	reMapKey := regexp.MustCompile(`([A-Za-z_][A-Za-z0-9_]*)\s*:`)

	for pi, p := range pipelines {
		pipeline, _ := p.(map[string]any)
		steps, _ := pipeline["steps"].([]any)
		for si, s := range steps {
			step, _ := s.(map[string]any)
			if fn, _ := step["fn"].(string); fn != "graph.write" {
				continue
			}
			args, _ := step["args"].(map[string]any)
			template, _ := args["template"].(string)
			if template == "" {
				if sql, _ := args["sql"].(string); sql != "" {
					template = sql
				}
			}
			if template == "" {
				continue
			}

			mm := reMerge.FindStringSubmatch(template)
			if len(mm) == 0 {
				continue
			}
			alias := mm[1]
			label := mm[2]
			if label != "ActorCoverageSnapshot" {
				continue
			}

			keys := map[string]struct{}{}
			bodyRe := regexp.MustCompile(fmt.Sprintf(reMergeBody.String(), regexp.QuoteMeta(alias), regexp.QuoteMeta(label)))
			bm := bodyRe.FindStringSubmatch(template)
			if len(bm) > 1 {
				for _, km := range reMapKey.FindAllStringSubmatch(bm[1], -1) {
					if len(km) > 1 {
						keys[km[1]] = struct{}{}
					}
				}
			}

			reSetKey := regexp.MustCompile(fmt.Sprintf(`\b%s\.([A-Za-z_][A-Za-z0-9_]*)\s*=`, regexp.QuoteMeta(alias)))
			for _, sm := range reSetKey.FindAllStringSubmatch(template, -1) {
				if len(sm) > 1 {
					keys[sm[1]] = struct{}{}
				}
			}

			var bad []string
			for k := range keys {
				if !allowed[k] {
					bad = append(bad, k)
				}
			}
			sort.Strings(bad)
			if len(bad) > 0 {
				errs = append(errs,
					fmt.Sprintf("pipeline[%d] step[%d] graph.write ActorCoverageSnapshot uses columns outside vertex_actor_coverage schema: %s", pi, si, strings.Join(bad, ",")))
			}
		}
	}

	return errs
}

// runMitamaList lists all T1 actors registered in the graph.
// Queries RisingWave directly via pgx (vertex_actor_manifest).
func runMitamaList(args []string) error {
	fs := flag.NewFlagSet("mitama list", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	if err := fs.Parse(args); err != nil {
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	q, err := db.Q(ctx)
	if err != nil {
		return fmt.Errorf("db: %w", err)
	}
	rows, err := q.ListActorManifests(ctx)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}

	if *jsonOut {
		out := make([]map[string]any, 0, len(rows))
		for _, r := range rows {
			out = append(out, map[string]any{
				"did":    r.Did.String,
				"name":   r.Name,
				"nanoid": r.Nanoid,
				"tier":   r.Tier,
			})
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{"rows": out})
	}

	fmt.Printf("%-30s %-12s %-8s %s\n", "NAME", "NANOID", "TIER", "DID")
	fmt.Printf("%-30s %-12s %-8s %s\n", "----", "------", "----", "---")
	seen := map[string]struct{}{}
	unique := 0
	for _, r := range rows {
		if r.Did.String != "" {
			if _, exists := seen[r.Did.String]; exists {
				continue
			}
			seen[r.Did.String] = struct{}{}
		}
		fmt.Printf("%-30s %-12s %-8s %s\n",
			r.Name, r.Nanoid, r.Tier, r.Did.String)
		unique++
	}
	fmt.Printf("\nTotal: %d actors\n", unique)
	return nil
}

// runMitamaSchemaStatus shows RisingWave schema change status for graphar tables.
func runMitamaSchemaStatus(args []string) error {
	fs := flag.NewFlagSet("mitama schema-status", flag.ContinueOnError)
	jsonOut := fs.Bool("json", false, "JSON output")
	timeoutSec := fs.Int("timeout", 60, "HTTP timeout seconds")
	table := fs.String("table", "vertex_actor_manifest", "table name filter (default: vertex_actor_manifest)")
	all := fs.Bool("all", false, "query all tables (can be slow)")
	state := fs.String("state", "", "state filter (e.g. RUNNING, FINISHED, CANCELLED)")
	if err := fs.Parse(args); err != nil {
		return err
	}

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no auth token — run: gftd auth login")
	}

	pdsBase := resolvePDSBaseURL()
	timeoutMs := *timeoutSec * 1000
	if timeoutMs < 1000 {
		timeoutMs = 1000
	}
	if timeoutMs > 60000 {
		timeoutMs = 60000
	}
	stmt := "SHOW ALTER TABLE COLUMN FROM graphar"
	var where []string
	if !*all && strings.TrimSpace(*table) != "" {
		safeTable := strings.ReplaceAll(strings.TrimSpace(*table), "'", "''")
		where = append(where, fmt.Sprintf("TableName = '%s'", safeTable))
	}
	if strings.TrimSpace(*state) != "" {
		safeState := strings.ToUpper(strings.ReplaceAll(strings.TrimSpace(*state), "'", "''"))
		where = append(where, fmt.Sprintf("State = '%s'", safeState))
	}
	if len(where) > 0 {
		stmt += " WHERE " + strings.Join(where, " AND ")
	}

	payload := map[string]any{
		"statement": stmt,
		"params":    map[string]any{},
		"timeoutMs": timeoutMs,
	}
	bodyBytes, _ := json.Marshal(payload)
	req, err := http.NewRequest("POST", pdsBase+"/xrpc/ai.gftd.kagami.sql", strings.NewReader(string(bodyBytes)))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	client := &http.Client{Timeout: time.Duration(*timeoutSec) * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("query failed: %w", err)
	}
	defer resp.Body.Close()

	var result map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&result)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("query failed (HTTP %d): %v", resp.StatusCode, result)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(result)
	}

	rows, _ := result["rows"].([]any)
	fmt.Printf("%-22s %-14s %-16s %-8s %s\n", "TABLE", "STATE", "CREATE_TIME", "PROGRESS", "MSG")
	fmt.Printf("%-22s %-14s %-16s %-8s %s\n", "-----", "-----", "-----------", "--------", "---")
	for _, r := range rows {
		row, _ := r.(map[string]any)
		table := fmt.Sprint(firstNonNil(row, "TableName", "Table"))
		state := fmt.Sprint(firstNonNil(row, "State", "JobState"))
		createTime := fmt.Sprint(firstNonNil(row, "CreateTime", "CreateTimeV2"))
		progress := fmt.Sprint(firstNonNil(row, "Progress", "ProgressState"))
		msg := fmt.Sprint(firstNonNil(row, "Msg", "Message"))
		fmt.Printf("%-22s %-14s %-16s %-8s %s\n", table, state, createTime, progress, msg)
	}
	fmt.Printf("\nTotal: %d schema change jobs\n", len(rows))
	return nil
}

func firstNonNil(row map[string]any, keys ...string) any {
	for _, k := range keys {
		if v, ok := row[k]; ok && v != nil {
			return v
		}
	}
	return ""
}

// runMitamaInspect shows details of a specific actor manifest.
func runMitamaInspect(args []string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: gftd mitama inspect <did>")
	}
	did := args[0]
	if !strings.HasPrefix(did, "did:") {
		did = "did:web:" + did + ".etzhayyim.com"
	}

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no auth token — run: gftd auth login")
	}

	pdsBase := resolvePDSBaseURL()
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

	var manifest map[string]any
	_ = json.NewDecoder(resp.Body).Decode(&manifest)
	if resp.StatusCode == 404 {
		return fmt.Errorf("actor manifest not found: %s", did)
	}
	if resp.StatusCode >= 400 {
		return fmt.Errorf("query failed (HTTP %d): %v", resp.StatusCode, manifest)
	}

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(manifest)
}

// runMitamaDormant sets actor status to dormant.
func runMitamaDormant(args []string) error {
	return mitamaSetStatus(args, "dormant")
}

// runMitamaRevive sets actor status to active.
func runMitamaRevive(args []string) error {
	return mitamaSetStatus(args, "active")
}

func mitamaSetStatus(args []string, status string) error {
	if len(args) < 1 {
		return fmt.Errorf("usage: gftd mitama %s <did>", status)
	}
	did := args[0]
	if !strings.HasPrefix(did, "did:") {
		did = "did:web:" + did + ".etzhayyim.com"
	}

	ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
	defer cancel()
	resp, err := db.RawQuery(ctx, `
		UPDATE vertex_actor_manifest
		SET status = $2
		WHERE did = $1
		RETURNING did, status
	`, did, status)
	if err != nil {
		return fmt.Errorf("update failed: %w", err)
	}
	if len(resp.Rows) == 0 {
		return fmt.Errorf("actor manifest not found: %s", did)
	}

	fmt.Printf("[mitama] %s → %s\n", did, status)
	return nil
}
