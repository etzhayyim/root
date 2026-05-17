// kosei_suggest.go — Tier suggestion heuristics for gftd kosei
//
// Suggests T1/T2/T3 tier assignments with responsibility-first rules:
//  1. T3 = infra workers (gateway/auth/graph/runtime core)
//  2. T2 = product app worker (self UI/UX + app domain logic)
//  3. T1 = Mitama actor (20-actors/*/actor-manifest.jsonld)
//
// Confidence levels:
//
//	high  — matched known infra/actor catalog
//	med   — matched role heuristics (UI/runtime/collections)
//	low   — fallback
package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"text/tabwriter"
	"time"
)

// ── Known tier lists ───────────────────────────────────────────────────────

// knownT3 are infra workers (platform backend responsibilities).
var knownT3 = map[string]string{
	"auth":        "infra worker: authentication/control-plane",
	"pds":         "infra worker: sole external data gateway",
	"kagami":      "infra worker: graph database query plane",
	"graph":       "infra worker: graph query service",
	"murakumo":    "infra worker: model/runtime orchestration",
	"llm":         "infra worker: inference gateway",
	"browser":     "infra worker: browser fetch/render gateway",
	"repo":        "infra worker: git/storage backend",
	"relay":       "infra worker: protocol relay",
	"dispatcher":  "infra worker: dispatch control-plane",
	"moderation":  "infra worker: policy moderation backend",
	"email-relay": "infra worker: mail relay backend",
	"git-server":  "infra worker: git server backend",
}

// knownT2 are app workers (user-facing product responsibilities).
var knownT2 = map[string]string{
	"yoro":         "app worker: user-facing social product",
	"maps":         "app worker: spatial product UX",
	"pptx":         "app worker: presentation editor UX",
	"xlsx":         "app worker: spreadsheet editor UX",
	"canvas":       "app worker: collaborative canvas UX",
	"organizer":    "app worker: end-user organizer UX",
	"gazo":         "app worker: image product UX",
	"ameno":        "app worker: inference product UX",
	"isekai":       "app worker: world/game UX",
	"joucho":       "app worker: wellbeing scoring UX",
	"baminiku":     "app worker: game/live UX",
	"mangaka":      "app worker: manga editor UX",
	"mailer":       "app worker: messaging/email UX",
	"calendar":     "app worker: scheduling UX",
	"calendar-mcp": "app worker: scheduling UX",
	"credits":      "app worker: ledger/payment UX",
	"okaimono":     "app worker: commerce UX",
	"omise":        "app worker: commerce/payment UX",
	"om1s3sh0p":    "app worker: commerce/payment UX",
	"org4n1z3":     "app worker: organizer UX",
	"is3k41w0":     "app worker: world/game UX",
	"outlook":      "app worker: email client UX",
	"s4b10t05":     "app worker: game UX",
	"sabiotoshi":   "app worker: game UX",
}

// T2 keyword patterns (app behavior signals).
var t2SourceKeywords = []string{
	"appview", "iframe", "ui", "editor", "dashboard",
	"bpmn", "workflow", "pipeline", "subscribeRepos",
	"scheduler", "cronSchedule", "setAlarm",
	"actor-manifest", "actorManifest",
	"durable object", "durableobject",
}

// ── Suggestion logic ───────────────────────────────────────────────────────

// koseiSuggestion is the output of the heuristic.
type koseiSuggestion struct {
	Nanoid     string
	Name       string
	Current    string // existing tier or "?"
	Suggested  string
	Confidence string // "high" | "med" | "low"
	Reason     string
}

// koseiSuggestTier suggests a tier for one app.
func koseiSuggestTier(meta koseiAppMeta, wsRoot string) koseiSuggestion {
	sug := koseiSuggestion{
		Nanoid:  meta.Nanoid,
		Name:    meta.Name,
		Current: "?",
	}

	// Derive app slug from DID (did:web:auth.etzhayyim.com → "auth") or folder name.
	appSlug := meta.Nanoid
	if meta.DID != "" {
		// did:web:auth.etzhayyim.com → auth
		parts := strings.Split(meta.DID, ":")
		if len(parts) >= 3 {
			host := parts[2] // "auth.etzhayyim.com"
			appSlug = strings.TrimSuffix(host, ".etzhayyim.com")
		}
	}
	// Also check folder name as fallback
	dirSlug := ""
	if meta.Dir != "" {
		parts := strings.Split(meta.Dir, "/")
		for _, p := range parts {
			if strings.HasPrefix(p, "ai-gftd-project-") {
				dirSlug = strings.TrimPrefix(p, "ai-gftd-project-")
				break
			}
		}
	}

	// 0. Known T3 list (infra workers)
	for _, key := range []string{meta.Nanoid, appSlug, dirSlug} {
		nk := normalizeTierKey(key)
		if reason, ok := knownT3[nk]; ok && nk != "" {
			sug.Suggested = "T3"
			sug.Confidence = "high"
			sug.Reason = reason
			return sug
		}
	}

	// 1. Known T2 list (app workers)
	for _, key := range []string{meta.Nanoid, appSlug, dirSlug} {
		nk := normalizeTierKey(key)
		if reason, ok := knownT2[nk]; ok && nk != "" {
			sug.Suggested = "T2"
			sug.Confidence = "high"
			sug.Reason = reason
			return sug
		}
	}

	// 2. magatama.jsonld role signals
	uiType := strings.ToLower(strings.TrimSpace(meta.UIType))
	if uiType == "appview" || uiType == "iframe" || uiType == "yoro" {
		sug.Suggested = "T2"
		sug.Confidence = "med"
		sug.Reason = fmt.Sprintf("uiType=%s indicates product app worker", meta.UIType)
	}

	// subscribeRepos trigger with custom collections → app worker candidate
	if len(meta.Collections) > 0 {
		sug.Suggested = "T2"
		sug.Confidence = "med"
		sug.Reason = fmt.Sprintf("subscribeRepos trigger with %d collection(s) → app/reactive worker", len(meta.Collections))
	}

	// system+headless workers are usually infra-oriented.
	if strings.EqualFold(meta.PerformerType, "system") && uiType == "" {
		sug.Suggested = "T3"
		sug.Confidence = "med"
		sug.Reason = "system performer without product UI → infra worker"
		return sug
	}

	// If app signals already identified from metadata, keep T2.
	if sug.Suggested == "T2" {
		return sug
	}

	// 3. Source file keyword scan (app signals only)
	appDir := filepath.Join(wsRoot, meta.Dir)
	t2Score, t2Hit := scanSourceKeywords(appDir, t2SourceKeywords)

	if t2Score > 0 {
		sug.Suggested = "T2"
		sug.Confidence = "med"
		sug.Reason = fmt.Sprintf("source keyword: %s", strings.Join(t2Hit[:koseiMin(3, len(t2Hit))], ", "))
		return sug
	}

	// 4. Mitama actor = T1 fallback.
	if isMitamaActorNanoid(wsRoot, meta.Nanoid) {
		sug.Suggested = "T1"
		sug.Confidence = "high"
		sug.Reason = "mitama actor manifest detected (shared executor + primitives)"
		return sug
	}

	// 5. Default T1
	sug.Suggested = "T1"
	sug.Confidence = "low"
	sug.Reason = "no app/infra worker signals detected — shared executor sufficient"
	return sug
}

// scanSourceKeywords returns (hit count, matched keywords) for given patterns in app dir.
func scanSourceKeywords(dir string, keywords []string) (int, []string) {
	var hits []string
	hitSet := make(map[string]bool)

	_ = filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() {
			return nil
		}
		name := info.Name()
		// Check filename itself
		nameLower := strings.ToLower(name)
		for _, kw := range keywords {
			if strings.Contains(nameLower, strings.ToLower(kw)) && !hitSet[kw] {
				hits = append(hits, kw)
				hitSet[kw] = true
			}
		}
		// Only scan small text files for content
		if info.Size() > 512*1024 {
			return nil
		}
		ext := strings.ToLower(filepath.Ext(name))
		if ext != ".ts" && ext != ".go" && ext != ".rs" && ext != ".toml" && ext != ".json" && ext != ".wit" {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		content := strings.ToLower(string(data))
		for _, kw := range keywords {
			if !hitSet[kw] && strings.Contains(content, strings.ToLower(kw)) {
				hits = append(hits, kw)
				hitSet[kw] = true
			}
		}
		return nil
	})

	return len(hits), hits
}

// isMitamaActorNanoid returns true if nanoid exists in 20-actors actor-manifest catalog.
func isMitamaActorNanoid(wsRoot, nanoid string) bool {
	nk := normalizeTierKey(nanoid)
	if nk == "" {
		return false
	}
	pattern := filepath.Join(wsRoot, "20-actors", "*", "actor-manifest.jsonld")
	files, err := filepath.Glob(pattern)
	if err != nil {
		return false
	}
	for _, p := range files {
		data, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		var m map[string]any
		if err := json.Unmarshal(data, &m); err != nil {
			continue
		}
		if v, _ := m["nanoid"].(string); normalizeTierKey(v) == nk {
			return true
		}
	}
	return false
}

func normalizeTierKey(s string) string {
	return strings.ToLower(strings.TrimSpace(s))
}

func koseiMin(a, b int) int {
	if a < b {
		return a
	}
	return b
}

// ── Suggest command ────────────────────────────────────────────────────────

func runKoseiSuggest(args []string) error {
	fs := flag.NewFlagSet("kosei suggest", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root")
	dataDir := fs.String("data-dir", "", "data directory")
	apply := fs.Bool("apply", false, "save suggestions to config.json")
	onlyUnknown := fs.Bool("unknown", true, "only suggest for apps without a tier assignment")
	minConf := fs.String("confidence", "low", "minimum confidence to show: low, med, high")
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

	cfg := koseiLoadConfig(dDir)

	var suggestions []koseiSuggestion
	for _, s := range states {
		if *onlyUnknown && s.Tier != "?" {
			continue
		}
		sug := koseiSuggestTier(s.koseiAppMeta, wsRoot)
		sug.Current = s.Tier
		if confLevel(sug.Confidence) < confLevel(*minConf) {
			continue
		}
		suggestions = append(suggestions, sug)
	}

	if *jsonOut {
		return encodeJSON(suggestions)
	}

	if len(suggestions) == 0 {
		fmt.Println("No suggestions (all apps have tier assignments).")
		fmt.Println("Use --unknown=false to show suggestions for all apps.")
		return nil
	}

	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "NANOID\tCURRENT\tSUGGESTED\tCONF\tREASON")
	fmt.Fprintln(w, "──────\t───────\t─────────\t────\t──────")
	for _, s := range suggestions {
		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\n",
			s.Nanoid, s.Current, s.Suggested, s.Confidence, truncStr(s.Reason, 60))
	}
	w.Flush()
	fmt.Printf("\n%d suggestion(s)\n", len(suggestions))

	if *apply {
		now := time.Now().UTC().Format(time.RFC3339)
		applied := 0
		for _, s := range suggestions {
			cfg.Apps[s.Nanoid] = koseiAppCfg{
				Tier:       s.Suggested,
				Notes:      s.Reason,
				AssignedAt: now,
				AssignedBy: "auto",
			}
			if err := koseiAppendChange(dDir, koseiChangeRow{
				ChangedAt: now,
				AppName:   s.Name,
				Nanoid:    s.Nanoid,
				OldTier:   s.Current,
				NewTier:   s.Suggested,
				Reason:    fmt.Sprintf("[auto] %s (conf=%s)", s.Reason, s.Confidence),
				ChangedBy: "auto",
			}); err != nil {
				fmt.Fprintf(os.Stderr, "warn: change log write: %v\n", err)
			}
			applied++
		}
		cfg.UpdatedAt = now
		if err := koseiSaveConfig(dDir, cfg); err != nil {
			return fmt.Errorf("save config: %w", err)
		}
		fmt.Printf("\n✓ Applied %d suggestion(s) to config.json\n", applied)
	} else {
		fmt.Println("\nRun with --apply to save suggestions to config.json.")
	}

	return nil
}

func confLevel(c string) int {
	switch c {
	case "high":
		return 3
	case "med":
		return 2
	default:
		return 1
	}
}

func encodeJSON(v any) error {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(v)
}
