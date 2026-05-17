package main

import (
	"bytes"
	"context"
	"crypto/sha256"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

const (
	defaultOllamaBase  = "http://127.0.0.1:11434"
	defaultShinkaModel = "gemma3:4b"
	murakumoEndpoint   = "https://murakumo.etzhayyim.com"
	// ADR 0023: hardcoded `murk_NQhD...` removed. Callers must provide a
	// platform key via $MURAKUMO_API_KEY (expected to be a `sk_live_*` token
	// that carries the `murakumo:inference` scope). Empty string means
	// unauthenticated — gateway returns 401.
	murakumoAPIKey = ""
)

// shinkaResult holds the LLM-generated domain knowledge for one actor.
type shinkaResult struct {
	DID            string   `json:"did"`
	Nanoid         string   `json:"nanoid"`
	DomainSummary  string   `json:"domain_summary"`
	SubDIDs        []subDID `json:"sub_dids"`
	KnowledgeEdges []kEdge  `json:"knowledge_edges"`
	Error          string   `json:"error,omitempty"`
}

type subDID struct {
	Path        string `json:"path"`
	DisplayName string `json:"display_name"`
	Description string `json:"description"`
}

type kEdge struct {
	From     string `json:"from"`
	Relation string `json:"relation"`
	To       string `json:"to"`
}

// runActorsShinka implements `gftd actors shinka` — agentic domain knowledge creation.
func runActorsShinka(args []string) error {
	fs := flag.NewFlagSet("actors shinka", flag.ExitOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", "https://atproto.etzhayyim.com"), "PDS base URL")
	ollamaBase := fs.String("ollama", envOr("OLLAMA_BASE", defaultOllamaBase), "Ollama API base URL")
	model := fs.String("model", envOr("GFTD_SHINKA_MODEL", defaultShinkaModel), "LLM model name")
	useMurakumo := fs.Bool("murakumo", false, "use Murakumo OpenAI-compatible API instead of Ollama")
	murakumoURL := fs.String("murakumo-url", envOr("GFTD_MURAKUMO", murakumoEndpoint), "Murakumo API base URL")
	concurrency := fs.Int("concurrency", 4, "parallel actor processing")
	limit := fs.Int("limit", 50, "max actors to process")
	dryRun := fs.Bool("dry-run", false, "generate plans but don't write to PDS")
	filter := fs.String("filter", "", "nanoid/projectId substring filter")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	// Select LLM backend
	var llmGenerate func(prompt string) (string, error)
	if *useMurakumo {
		apiKey := envOr("MURAKUMO_API_KEY", murakumoAPIKey)
		if err := checkMurakumo(*murakumoURL, apiKey); err != nil {
			return fmt.Errorf("murakumo not ready: %w", err)
		}
		llmGenerate = func(prompt string) (string, error) {
			return murakumoGenerate(*murakumoURL, apiKey, *model, prompt)
		}
		fmt.Fprintf(os.Stderr, "Using Murakumo (%s) model=%s\n", *murakumoURL, *model)
	} else {
		if err := checkOllama(*ollamaBase, *model); err != nil {
			return fmt.Errorf("ollama not ready: %w\nRun: ollama pull %s\nOr use --murakumo flag for Murakumo API", err, *model)
		}
		llmGenerate = func(prompt string) (string, error) {
			return ollamaGenerate(*ollamaBase, *model, prompt)
		}
	}

	// Fetch active actors from PDS
	actors, err := fetchActors(*pdsURL, *limit)
	if err != nil {
		return fmt.Errorf("fetch actors: %w", err)
	}

	if *filter != "" {
		var filtered []actorInfo
		for _, a := range actors {
			f := strings.ToLower(*filter)
			if strings.Contains(strings.ToLower(a.Nanoid), f) || strings.Contains(strings.ToLower(a.ProjectID), f) || strings.Contains(strings.ToLower(a.Handle), f) || strings.Contains(strings.ToLower(a.DID), f) {
				filtered = append(filtered, a)
			}
		}
		actors = filtered
	}

	fmt.Fprintf(os.Stderr, "Processing %d actors with %s (concurrency=%d)\n", len(actors), *model, *concurrency)

	// Process actors in parallel
	results := make([]shinkaResult, len(actors))
	var processed int64
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, actor := range actors {
		wg.Add(1)
		sem <- struct{}{}
		go func(idx int, a actorInfo) {
			defer wg.Done()
			defer func() { <-sem }()

			result := processActor(llmGenerate, a)
			results[idx] = result

			if !*dryRun && result.Error == "" {
				writeResult(*pdsURL, a, result)
			}

			n := atomic.AddInt64(&processed, 1)
			if !*jsonOut {
				fmt.Fprintf(os.Stderr, "\r[%d/%d] %s", n, len(actors), a.Nanoid)
			}
		}(i, actor)
	}
	wg.Wait()

	if !*jsonOut {
		fmt.Fprintln(os.Stderr)
	}

	// Output
	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		enc.Encode(results)
	} else {
		var okCount, subDIDCount, edgeCount int
		for _, r := range results {
			if r.Error == "" {
				okCount++
				subDIDCount += len(r.SubDIDs)
				edgeCount += len(r.KnowledgeEdges)
			}
		}
		fmt.Printf("\nShinka complete: %d/%d actors, %d sub-DIDs, %d knowledge edges\n",
			okCount, len(actors), subDIDCount, edgeCount)
		if *dryRun {
			fmt.Println("(dry-run — nothing written to PDS)")
		}
	}

	return nil
}

type actorInfo struct {
	DID         string `json:"did"`
	Nanoid      string `json:"nanoid"`
	ProjectID   string `json:"projectId"`
	Handle      string `json:"handle"`
	DisplayName string `json:"displayName"`
	Description string `json:"description"`
}

func fetchActors(pdsURL string, limit int) ([]actorInfo, error) {
	// Primary: PDS XRPC ai.gftd.actor.list
	actors, err := fetchActorsXRPC(pdsURL, limit)
	if err == nil && len(actors) > 0 {
		return actors, nil
	}
	fmt.Fprintf(os.Stderr, "actor.list failed (%v), trying direct SQL fallback...\n", err)

	// Fallback 1: graph SQL query
	actors, err = fetchActorsR2SQL(limit)
	if err == nil && len(actors) > 0 {
		return actors, nil
	}
	fmt.Fprintf(os.Stderr, "SQL fallback failed (%v), trying local magatama.jsonld scan...\n", err)

	// Fallback 2: Local magatama.jsonld scan
	return fetchActorsLocal(limit)
}

func fetchActorsXRPC(pdsURL string, limit int) ([]actorInfo, error) {
	var all []actorInfo
	cursor := ""
	const pageSize = 50

	for len(all) < limit {
		payload := map[string]interface{}{
			"status":     "active",
			"batchLimit": pageSize,
		}
		if cursor != "" {
			payload["cursor"] = cursor
		}
		body, _ := json.Marshal(payload)
		req, _ := http.NewRequest("POST", pdsURL+"/xrpc/ai.gftd.actor.list", bytes.NewReader(body))
		req.Header.Set("Content-Type", "application/json")
		setAuthHeaders(req)

		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return nil, err
		}

		var result struct {
			Actors []actorInfo `json:"actors"`
			Cursor string      `json:"cursor"`
			Error  string      `json:"error"`
		}
		if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
			resp.Body.Close()
			return nil, err
		}
		resp.Body.Close()

		if result.Error != "" {
			return nil, fmt.Errorf("PDS: %s", result.Error)
		}
		if len(result.Actors) == 0 {
			break
		}

		all = append(all, result.Actors...)
		cursor = result.Cursor
		if cursor == "" || len(result.Actors) < pageSize {
			break
		}
	}

	if len(all) > limit {
		all = all[:limit]
	}
	return all, nil
}

// sanitizePath converts a sub-DID path candidate to a valid URL-safe path:
// lowercase, spaces→hyphens, non-alphanumeric/hyphen characters removed.
func sanitizePath(path string) string {
	path = strings.ToLower(strings.ReplaceAll(path, " ", "-"))
	var b strings.Builder
	for _, r := range path {
		if (r >= 'a' && r <= 'z') || (r >= '0' && r <= '9') || r == '-' {
			b.WriteRune(r)
		}
	}
	return b.String()
}

func processActor(llmGenerate func(string) (string, error), actor actorInfo) shinkaResult {
	result := shinkaResult{DID: actor.DID, Nanoid: actor.Nanoid}

	// Build domain context from available actor metadata.
	var contextParts []string
	contextParts = append(contextParts, fmt.Sprintf("nanoid=%q", actor.Nanoid))
	contextParts = append(contextParts, fmt.Sprintf("handle=%q", actor.Handle))
	if actor.DisplayName != "" {
		contextParts = append(contextParts, fmt.Sprintf("displayName=%q", actor.DisplayName))
	}
	if actor.Description != "" {
		contextParts = append(contextParts, fmt.Sprintf("description=%q", actor.Description))
	}
	domainContext := strings.Join(contextParts, ", ")

	prompt := fmt.Sprintf(`You are a domain knowledge architect for an AI agent platform called etzhayyim.com.
Given an AI agent's identity metadata, generate structured domain knowledge as JSON.

Actor metadata: %s

Output a JSON object with exactly these keys:
- "domain_summary": 2-3 sentences describing this agent's domain, purpose, and key capabilities
- "sub_dids": array of 3-5 sub-entities this agent manages, each with "path" (URL-safe slug), "display_name", "description"
- "knowledge_edges": array of 5-8 edges, each with "from": "%s", "relation", "to" (specific concept)

Relations available: EXPERTISE_IN, DEPENDS_ON, PRODUCES, CONSUMES, REGULATES, SERVES, MONITORS, ANALYZES

Example for a legal intelligence agent (nanoid="hanrei"):
{
  "domain_summary": "hanrei.etzhayyim.com specializes in global judicial intelligence, covering case law from 83 jurisdictions. It monitors court decisions and extracts structured legal precedents. The agent provides AI-powered legal research across multiple legal systems.",
  "sub_dids": [
    {"path": "japan", "display_name": "Japanese Courts", "description": "Supreme Court and High Court decisions"},
    {"path": "icj", "display_name": "International Court of Justice", "description": "ICJ judgments and advisory opinions"},
    {"path": "echr", "display_name": "European Court of Human Rights", "description": "ECHR case law and decisions"}
  ],
  "knowledge_edges": [
    {"from": "hanrei", "relation": "EXPERTISE_IN", "to": "case-law"},
    {"from": "hanrei", "relation": "MONITORS", "to": "judicial-proceedings"},
    {"from": "hanrei", "relation": "PRODUCES", "to": "legal-precedent-records"},
    {"from": "hanrei", "relation": "DEPENDS_ON", "to": "court-data-sources"},
    {"from": "hanrei", "relation": "SERVES", "to": "legal-researchers"},
    {"from": "hanrei", "relation": "REGULATES", "to": "legal-compliance"},
    {"from": "hanrei", "relation": "ANALYZES", "to": "judicial-trends"}
  ]
}

Now generate for the actor above. Be specific to this agent's domain. Output ONLY valid JSON:`, domainContext, actor.Nanoid)

	resp, err := llmGenerate(prompt)
	if err != nil {
		result.Error = err.Error()
		return result
	}

	// Parse JSON from LLM response
	jsonStr := extractJSONBlock(resp)
	if os.Getenv("SHINKA_DEBUG") != "" {
		fmt.Fprintf(os.Stderr, "[debug] actor=%s resp_len=%d json_len=%d\n", actor.Nanoid, len(resp), len(jsonStr))
		os.WriteFile("/tmp/shinka_resp.txt", []byte(resp), 0o644)
	}
	if jsonStr == "" {
		result.Error = "no JSON in LLM response"
		return result
	}

	var parsed struct {
		DomainSummary  string   `json:"domain_summary"`
		SubDIDs        []subDID `json:"sub_dids"`
		KnowledgeEdges []kEdge  `json:"knowledge_edges"`
	}
	if err := json.Unmarshal([]byte(jsonStr), &parsed); err != nil {
		result.Error = fmt.Sprintf("JSON parse: %v", err)
		return result
	}

	result.DomainSummary = parsed.DomainSummary
	result.SubDIDs = parsed.SubDIDs
	result.KnowledgeEdges = parsed.KnowledgeEdges
	return result
}

func writeResult(pdsURL string, actor actorInfo, result shinkaResult) {
	// Batch all writes via applyWrites for compatibility with mod.etzhayyim.com (bootstrap token).
	// Individual XRPC endpoints (actor.update, actor.create, repo.putRecord) require session auth
	// which bootstrap token cannot provide.
	var writes []map[string]interface{}

	// 1. Update actor description via App record update
	if result.DomainSummary != "" {
		writes = append(writes, map[string]interface{}{
			"action":     "update",
			"collection": "ai.gftd.actor.app",
			"rkey":       actor.Nanoid,
			"value": map[string]interface{}{
				"nanoid":      actor.Nanoid,
				"did":         actor.DID,
				"displayName": actor.DisplayName,
				"description": result.DomainSummary,
			},
		})
	}

	// 2. Create sub-DIDs (path-based) via identity.did records.
	for _, sub := range result.SubDIDs {
		path := sanitizePath(sub.Path)
		if path == "" {
			continue
		}
		subDID := actor.DID + ":" + path
		rkey := seedStableRKey("did:" + path)
		writes = append(writes, map[string]interface{}{
			"action":     "update",
			"collection": "ai.gftd.identity.did",
			"rkey":       rkey,
			"value": map[string]interface{}{
				"id":           subDID,
				"display_name": sub.DisplayName,
				"description":  sub.Description,
				"status":       "active",
				"controller":   actor.DID,
				"actorDid":     actor.DID,
				"sourceType":   "shinka",
				"sourceId":     "shinka:" + actor.Nanoid,
				"created_at":   time.Now().UTC().Format(time.RFC3339),
			},
		})
	}

	// 3. Knowledge edges as domain records — idempotent via deterministic rkey.
	for _, edge := range result.KnowledgeEdges {
		key := fmt.Sprintf("%s:%s:%s", edge.From, edge.Relation, edge.To)
		sum := sha256.Sum256([]byte(key))
		rkey := fmt.Sprintf("%x", sum[:8])
		writes = append(writes, map[string]interface{}{
			"action":     "update",
			"collection": "ai.gftd.actor.knowledgeEdge",
			"rkey":       rkey,
			"value": map[string]interface{}{
				"from":      edge.From,
				"relation":  edge.Relation,
				"to":        edge.To,
				"createdAt": time.Now().UTC().Format(time.RFC3339),
			},
		})
	}

	if len(writes) == 0 {
		return
	}

	// Batch in groups of 50 (PDS applyWrites limit)
	for i := 0; i < len(writes); i += 50 {
		end := i + 50
		if end > len(writes) {
			end = len(writes)
		}
		batch := writes[i:end]
		payload, _ := json.Marshal(map[string]interface{}{
			"repo":   actor.DID,
			"writes": batch,
		})
		req, _ := http.NewRequest("POST", pdsURL+"/xrpc/com.atproto.repo.applyWrites", bytes.NewReader(payload))
		req.Header.Set("Content-Type", "application/json")
		setAuthHeaders(req)
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			fmt.Fprintf(os.Stderr, "[shinka] applyWrites failed: %v\n", err)
			continue
		}
		defer resp.Body.Close()
		if resp.StatusCode >= 400 {
			b, _ := io.ReadAll(resp.Body)
			fmt.Fprintf(os.Stderr, "[shinka] applyWrites → %d: %s\n", resp.StatusCode, string(b[:min(len(b), 200)]))
		}
	}
}

// ── graph SQL actor fallback ──

// fetchActorsR2SQL lists actor apps directly from RisingWave (vertex_app).
func fetchActorsR2SQL(limit int) ([]actorInfo, error) {
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	sql := fmt.Sprintf(`SELECT vertex_id, repo, val FROM vertex_app LIMIT %d`, limit)
	resp, err := db.RawQuery(ctx, sql)
	if err != nil {
		return nil, err
	}
	rows := resp.Rows
	var actors []actorInfo
	for _, row := range rows {
		vertexID := fmt.Sprintf("%v", row["vertex_id"])
		repo := fmt.Sprintf("%v", row["repo"])
		did := repo

		// Parse val for display_name/nanoid
		var rec map[string]interface{}
		if valStr, ok := row["val"].(string); ok && valStr != "" {
			json.Unmarshal([]byte(valStr), &rec)
		}

		nanoid := ""
		handle := ""
		if rec != nil {
			nanoid = fmt.Sprintf("%v", rec["nanoid"])
			handle = fmt.Sprintf("%v", rec["display_name"])
		}
		if nanoid == "" || nanoid == "<nil>" {
			// Extract nanoid from vertex_id or repo
			if repo != "" && repo != "<nil>" {
				parts := strings.Split(repo, ":")
				if len(parts) >= 3 {
					host := parts[2]
					nanoid = strings.TrimSuffix(host, ".etzhayyim.com")
				}
			}
			if nanoid == "" {
				nanoid = vertexID
			}
		}
		if did == "" || did == "<nil>" {
			did = repo
		}
		if did == "" || did == "<nil>" {
			did = "did:web:" + nanoid + ".etzhayyim.com"
		}
		if handle == "" || handle == "<nil>" {
			handle = nanoid + ".etzhayyim.com"
		}
		if nanoid == "" || nanoid == "<nil>" {
			continue
		}
		actors = append(actors, actorInfo{
			DID:    did,
			Nanoid: nanoid,
			Handle: handle,
		})
	}
	return actors, nil
}

// ── Local magatama.jsonld scan ──

func fetchActorsLocal(limit int) ([]actorInfo, error) {
	root, err := findGitRoot(".")
	if err != nil {
		return nil, err
	}
	pattern := filepath.Join(root, "projects", "*", "wasm", "*", "magatama.jsonld")
	matches, _ := filepath.Glob(pattern)
	var actors []actorInfo
	for _, m := range matches {
		if len(actors) >= limit {
			break
		}
		data, err := os.ReadFile(m)
		if err != nil {
			continue
		}
		var cfg struct {
			Nanoid  string `json:"nanoid"`
			Name    string `json:"name"`
			Project string `json:"project"`
			Profile struct {
				DisplayName string `json:"displayName"`
				Description string `json:"description"`
			} `json:"profile"`
		}
		if err := json.Unmarshal(data, &cfg); err != nil || cfg.Nanoid == "" {
			continue
		}
		handle := cfg.Profile.DisplayName
		if handle == "" {
			handle = cfg.Name
		}
		actors = append(actors, actorInfo{
			DID:         "did:web:" + cfg.Nanoid + ".etzhayyim.com",
			Nanoid:      cfg.Nanoid,
			ProjectID:   cfg.Project,
			Handle:      handle,
			DisplayName: cfg.Profile.DisplayName,
			Description: cfg.Profile.Description,
		})
	}
	fmt.Fprintf(os.Stderr, "local scan: found %d actors from magatama.jsonld\n", len(actors))
	return actors, nil
}

// ── Ollama helpers ──

func checkOllama(base, model string) error {
	resp, err := http.Get(base + "/api/tags")
	if err != nil {
		return fmt.Errorf("cannot reach ollama at %s: %w", base, err)
	}
	defer resp.Body.Close()

	var tags struct {
		Models []struct {
			Name string `json:"name"`
		} `json:"models"`
	}
	json.NewDecoder(resp.Body).Decode(&tags)

	for _, m := range tags.Models {
		if strings.HasPrefix(m.Name, model) || strings.HasPrefix(model, strings.Split(m.Name, ":")[0]) {
			return nil
		}
	}
	return fmt.Errorf("model %q not found in ollama (available: %d models)", model, len(tags.Models))
}

func ollamaGenerate(base, model, prompt string) (string, error) {
	body, _ := json.Marshal(map[string]interface{}{
		"model":  model,
		"prompt": prompt,
		"stream": false,
		"format": "json", // Force JSON output mode — prevents prose/markdown wrapping
		"options": map[string]interface{}{
			"temperature": 0.3,
			"num_predict": 2048,
		},
	})

	client := &http.Client{Timeout: 120 * time.Second}
	resp, err := client.Post(base+"/api/generate", "application/json", bytes.NewReader(body))
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		b, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("ollama %d: %s", resp.StatusCode, string(b))
	}

	var result struct {
		Response string `json:"response"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	return result.Response, nil
}

// ── Murakumo helpers (OpenAI-compatible API) ──

func checkMurakumo(base, apiKey string) error {
	req, _ := http.NewRequest("GET", base+"/api/openai/v1/models", nil)
	req.Header.Set("Authorization", "Bearer "+apiKey)
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("cannot reach murakumo at %s: %w", base, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("murakumo %d: %s", resp.StatusCode, string(b[:min(len(b), 200)]))
	}
	return nil
}

func murakumoGenerate(base, apiKey, model, prompt string) (string, error) {
	body, _ := json.Marshal(map[string]interface{}{
		"model": model,
		"messages": []map[string]string{
			{
				"role":    "system",
				"content": "You are a domain knowledge architect. Always respond with valid JSON only. No markdown fences, no explanations, no preamble — just the JSON object.",
			},
			{"role": "user", "content": prompt},
		},
		"temperature":     0.3,
		"max_tokens":      8192,
		"response_format": map[string]string{"type": "json_object"},
	})

	req, _ := http.NewRequest("POST", base+"/api/openai/v1/chat/completions", bytes.NewReader(body))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+apiKey)

	client := &http.Client{Timeout: 200 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		b, _ := io.ReadAll(resp.Body)
		return "", fmt.Errorf("murakumo %d: %s", resp.StatusCode, string(b[:min(len(b), 200)]))
	}

	var result struct {
		Choices []struct {
			Message struct {
				Content string `json:"content"`
			} `json:"message"`
		} `json:"choices"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
		return "", err
	}
	if len(result.Choices) == 0 {
		return "", fmt.Errorf("murakumo: no choices in response")
	}
	return result.Choices[0].Message.Content, nil
}

// extractJSONBlock finds the first {...} JSON block in a string.
// Strips <think>...</think> reasoning blocks (Qwen3.5 etc.) before extraction.
func extractJSONBlock(s string) string {
	// Remove <think>...</think> blocks that reasoning models emit
	for {
		tStart := strings.Index(s, "<think>")
		if tStart < 0 {
			break
		}
		tEnd := strings.Index(s[tStart:], "</think>")
		if tEnd < 0 {
			// Unclosed think tag — remove everything from <think> onward
			s = s[:tStart]
			break
		}
		s = s[:tStart] + s[tStart+tEnd+len("</think>"):]
	}

	start := strings.Index(s, "{")
	if start < 0 {
		return ""
	}
	depth := 0
	for i := start; i < len(s); i++ {
		switch s[i] {
		case '{':
			depth++
		case '}':
			depth--
			if depth == 0 {
				return s[start : i+1]
			}
		}
	}
	return ""
}
