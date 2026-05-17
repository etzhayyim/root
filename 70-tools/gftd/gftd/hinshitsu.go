package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strconv"
	"strings"
	"time"
)

const hinshitsuDefaultPDSURL = defaultPDSURL
const hinshitsuFallbackPDSURL = "https://atproto.etzhayyim.com"

type hinshitsuReport struct {
	DID         string                  `json:"did"`
	GeneratedAt string                  `json:"generatedAt"`
	Model       string                  `json:"model"`
	Sources     map[string]hinshitsuSrc `json:"sources"`
	Analysis    string                  `json:"analysis"`
}

type hinshitsuKojoReport struct {
	Did         string                  `json:"did"`
	GeneratedAt string                  `json:"generatedAt"`
	Model       string                  `json:"model"`
	Sources     map[string]hinshitsuSrc `json:"sources"`
	KojoPlan    string                  `json:"kojoPlan"`
	Artifacts   []string                `json:"artifacts"`
}

type hinshitsuSrc struct {
	URL         string `json:"url"`
	StatusCode  int    `json:"statusCode"`
	ContentType string `json:"contentType,omitempty"`
	Error       string `json:"error,omitempty"`
	Snippet     string `json:"snippet,omitempty"`
}

type chatCompletionsRequest struct {
	Model       string    `json:"model"`
	Messages    []message `json:"messages"`
	Temperature float64   `json:"temperature,omitempty"`
}

type message struct {
	Role    string `json:"role"`
	Content string `json:"content"`
}

type chatCompletionsResponse struct {
	Model   string `json:"model"`
	Choices []struct {
		Message struct {
			Content string `json:"content"`
		} `json:"message"`
	} `json:"choices"`
}

type hinshitsuFleetPost struct {
	URI         string `json:"uri"`
	IndexedAt   string `json:"indexedAt"`
	Text        string `json:"text"`
	LikeCount   int    `json:"likeCount,omitempty"`
	RepostCount int    `json:"repostCount,omitempty"`
	ReplyCount  int    `json:"replyCount,omitempty"`
}

type hinshitsuFleetTarget struct {
	Nanoid  string                  `json:"nanoid"`
	DID     string                  `json:"did"`
	Sources map[string]hinshitsuSrc `json:"sources"`
	Posts   []hinshitsuFleetPost    `json:"posts"`
}

type hinshitsuFleetScanReport struct {
	GeneratedAt string                 `json:"generatedAt"`
	PDS         string                 `json:"pds"`
	Source      string                 `json:"source"`
	Targets     []hinshitsuFleetTarget `json:"targets"`
}

type hinshitsuFleetFinding struct {
	Severity string `json:"severity"`
	Category string `json:"category"`
	Message  string `json:"message"`
	Evidence string `json:"evidence,omitempty"`
}

type hinshitsuFleetScoreResult struct {
	DID          string                  `json:"did"`
	Nanoid       string                  `json:"nanoid"`
	ProfileScore float64                 `json:"profileScore"`
	PostsScore   float64                 `json:"postsScore"`
	TotalScore   float64                 `json:"totalScore"`
	Grade        string                  `json:"grade"`
	Breakdown    map[string]float64      `json:"breakdown"`
	Findings     []hinshitsuFleetFinding `json:"findings"`
}

type hinshitsuFleetScoreReport struct {
	GeneratedAt string                      `json:"generatedAt"`
	Results     []hinshitsuFleetScoreResult `json:"results"`
}

type hinshitsuFleetAction struct {
	DID         string   `json:"did"`
	ActionID    string   `json:"actionId"`
	Mode        string   `json:"mode"`
	Status      string   `json:"status"`
	BeforeScore float64  `json:"beforeScore"`
	AfterScore  float64  `json:"afterScore"`
	Changes     []string `json:"changes,omitempty"`
	Error       string   `json:"error,omitempty"`
}

type hinshitsuFleetKaizenReport struct {
	GeneratedAt string                 `json:"generatedAt"`
	Actions     []hinshitsuFleetAction `json:"actions"`
}

type hinshitsuFleetVerifyResult struct {
	DID         string  `json:"did"`
	ActionID    string  `json:"actionId"`
	Status      string  `json:"status"`
	BeforeScore float64 `json:"beforeScore"`
	AfterScore  float64 `json:"afterScore"`
	Verified    bool    `json:"verified"`
	Reason      string  `json:"reason,omitempty"`
}

type hinshitsuFleetVerifyReport struct {
	GeneratedAt string                       `json:"generatedAt"`
	Results     []hinshitsuFleetVerifyResult `json:"results"`
}

type hinshitsuFleetDiffSnapshot struct {
	DIDCount            int            `json:"didCount"`
	ScanCount           int            `json:"scanCount"`
	ScoreCount          int            `json:"scoreCount"`
	DidDocReachable     int            `json:"didDocReachable"`
	AtprotoDidReachable int            `json:"atprotoDidReachable"`
	WithPosts           int            `json:"withPosts"`
	AvgTotalScore       float64        `json:"avgTotalScore"`
	Grades              map[string]int `json:"grades"`
}

type hinshitsuFleetDiffDelta struct {
	ScanCount           int     `json:"scanCount"`
	ScoreCount          int     `json:"scoreCount"`
	DidDocReachable     int     `json:"didDocReachable"`
	AtprotoDidReachable int     `json:"atprotoDidReachable"`
	WithPosts           int     `json:"withPosts"`
	AvgTotalScore       float64 `json:"avgTotalScore"`
}

type hinshitsuFleetDiffReport struct {
	GeneratedAt     string                     `json:"generatedAt"`
	DidListSource   string                     `json:"didListSource,omitempty"`
	ComparedDIDs    []string                   `json:"comparedDids"`
	MissingInBefore []string                   `json:"missingInBefore,omitempty"`
	MissingInAfter  []string                   `json:"missingInAfter,omitempty"`
	Before          hinshitsuFleetDiffSnapshot `json:"before"`
	After           hinshitsuFleetDiffSnapshot `json:"after"`
	Delta           hinshitsuFleetDiffDelta    `json:"delta"`
}

type hinshitsuActorsItem struct {
	DID             string                  `json:"did"`
	Nanoid          string                  `json:"nanoid,omitempty"`
	TotalScore      float64                 `json:"totalScore"`
	Grade           string                  `json:"grade"`
	Priority        string                  `json:"priority"`
	Findings        []hinshitsuFleetFinding `json:"findings"`
	Recommendations []string                `json:"recommendations"`
}

type hinshitsuActorsReport struct {
	GeneratedAt string                `json:"generatedAt"`
	Input       string                `json:"input"`
	MinScore    float64               `json:"minScore"`
	Count       int                   `json:"count"`
	Items       []hinshitsuActorsItem `json:"items"`
}

func runHinshitsu(args []string) error {
	if len(args) > 0 && args[0] == "kojo" {
		return runHinshitsuKojo(args[1:])
	}
	if len(args) > 0 && args[0] == "fleet" {
		return runHinshitsuFleet(args[1:])
	}
	if len(args) > 0 && args[0] == "actors" {
		return runHinshitsuActors(args[1:])
	}

	if len(args) > 0 {
		switch args[0] {
		case "help", "--help", "-h":
			printHinshitsuUsage()
			return nil
		}
	}

	fs := flag.NewFlagSet("hinshitsu", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	did := fs.String("did", "", "target DID (required), e.g. did:web:tnt4ib0d.etzhayyim.com")
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", hinshitsuDefaultPDSURL), "PDS base URL for app.bsky.actor.getProfile")
	model := fs.String("model", strings.TrimSpace(envOr("GFTD_HINSHITSU_MODEL", os.Getenv("GFTD_CODE_MODEL"))), "model id (default: GFTD_HINSHITSU_MODEL or GFTD_CODE_MODEL, else auto-detect)")
	apiBase := fs.String("api-base", defaultCodeAPIBase(), "OpenAI-compatible API base URL (default: OPENAI_API_BASE or https://murakumo.etzhayyim.com/v1)")
	apiKey := fs.String("api-key", defaultCodeAPIKey(), "API key (default: OPENAI_API_KEY)")
	timeout := fs.Duration("timeout", 20*time.Second, "HTTP timeout for source collection and LLM calls")
	noAutoModel := fs.Bool("no-auto-model", false, "disable model auto-detection via /models")
	jsonOut := fs.Bool("json", false, "output JSON report")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	targetDID := strings.TrimSpace(*did)
	if targetDID == "" {
		return fmt.Errorf("--did is required")
	}
	if !strings.HasPrefix(targetDID, "did:web:") {
		return fmt.Errorf("--did must be did:web:* (got %q)", targetDID)
	}

	base := normalizeAPIBase(*apiBase)
	resolvedModel := strings.TrimSpace(*model)
	if resolvedModel == "" && !*noAutoModel {
		auto, err := detectLMStudioModelWithFallback(base, strings.TrimSpace(*apiKey), minDuration(*timeout, 5*time.Second))
		if err != nil {
			fmt.Fprintf(os.Stderr, "WARN: model auto-detect failed: %v\n", err)
		} else {
			resolvedModel = auto
			fmt.Fprintf(os.Stderr, "==> detected model: %s\n", resolvedModel)
		}
	}
	if resolvedModel == "" {
		return fmt.Errorf("model is required. Use --model or set GFTD_HINSHITSU_MODEL")
	}

	client := &http.Client{Timeout: *timeout}
	didDocBody, profileBody, sources, err := collectHinshitsuSources(client, targetDID, *pdsURL)
	if err != nil {
		return err
	}

	prompt := buildHinshitsuPrompt(targetDID, didDocBody, profileBody, sources)
	analysis, err := askLMStudioForHinshitsu(client, base, strings.TrimSpace(*apiKey), resolvedModel, prompt)
	if err != nil {
		return err
	}

	report := hinshitsuReport{
		DID:         targetDID,
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Model:       resolvedModel,
		Sources:     sources,
		Analysis:    strings.TrimSpace(analysis),
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("DID: %s\n", report.DID)
	fmt.Printf("Model: %s\n", report.Model)
	for key, src := range report.Sources {
		fmt.Printf("- source[%s]: HTTP %d %s\n", key, src.StatusCode, src.URL)
		if src.Error != "" {
			fmt.Printf("  error: %s\n", src.Error)
		}
	}
	fmt.Println()
	fmt.Println(report.Analysis)
	return nil
}

func runHinshitsuKojo(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "help", "--help", "-h":
			printHinshitsuUsage()
			return nil
		}
	}

	fs := flag.NewFlagSet("hinshitsu kojo", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	did := fs.String("did", "", "target DID (required), e.g. did:web:tnt4ib0d.etzhayyim.com")
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", hinshitsuDefaultPDSURL), "PDS base URL for app.bsky.actor.getProfile")
	model := fs.String("model", strings.TrimSpace(envOr("GFTD_HINSHITSU_MODEL", os.Getenv("GFTD_CODE_MODEL"))), "model id (default: GFTD_HINSHITSU_MODEL or GFTD_CODE_MODEL, else auto-detect)")
	apiBase := fs.String("api-base", defaultCodeAPIBase(), "OpenAI-compatible API base URL (default: OPENAI_API_BASE or https://murakumo.etzhayyim.com/v1)")
	apiKey := fs.String("api-key", defaultCodeAPIKey(), "API key (default: OPENAI_API_KEY)")
	timeout := fs.Duration("timeout", 20*time.Second, "HTTP timeout for source collection and LLM calls")
	noAutoModel := fs.Bool("no-auto-model", false, "disable model auto-detection via /models")
	outputDir := fs.String("output-dir", "reports", "directory to write kojo artifacts")
	jsonOut := fs.Bool("json", false, "output JSON report")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	targetDID := strings.TrimSpace(*did)
	if targetDID == "" {
		return fmt.Errorf("--did is required")
	}
	if !strings.HasPrefix(targetDID, "did:web:") {
		return fmt.Errorf("--did must be did:web:* (got %q)", targetDID)
	}

	base := normalizeAPIBase(*apiBase)
	resolvedModel := strings.TrimSpace(*model)
	if resolvedModel == "" && !*noAutoModel {
		auto, err := detectLMStudioModelWithFallback(base, strings.TrimSpace(*apiKey), minDuration(*timeout, 5*time.Second))
		if err != nil {
			fmt.Fprintf(os.Stderr, "WARN: model auto-detect failed: %v\n", err)
		} else {
			resolvedModel = auto
			fmt.Fprintf(os.Stderr, "==> detected model: %s\n", resolvedModel)
		}
	}
	if resolvedModel == "" {
		return fmt.Errorf("model is required. Use --model or set GFTD_HINSHITSU_MODEL")
	}

	client := &http.Client{Timeout: *timeout}
	didDocBody, profileBody, sources, err := collectHinshitsuSources(client, targetDID, *pdsURL)
	if err != nil {
		return err
	}

	kojoPrompt := buildHinshitsuKojoPrompt(targetDID, didDocBody, profileBody, sources)
	kojoPlan, err := askLMStudioForHinshitsuKojo(client, base, strings.TrimSpace(*apiKey), resolvedModel, kojoPrompt)
	if err != nil {
		return err
	}

	slug := didToSlug(targetDID)
	absOutDir := *outputDir
	if !filepath.IsAbs(absOutDir) {
		cwd, _ := os.Getwd()
		absOutDir = filepath.Join(cwd, absOutDir)
	}
	if err := os.MkdirAll(absOutDir, 0o755); err != nil {
		return fmt.Errorf("create output dir: %w", err)
	}

	reportPath := filepath.Join(absOutDir, fmt.Sprintf("hinshitsu-kojo-%s.json", slug))
	templatePath := filepath.Join(absOutDir, fmt.Sprintf("did-template-%s.json", slug))
	artifacts := []string{reportPath}

	report := hinshitsuKojoReport{
		Did:         targetDID,
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Model:       resolvedModel,
		Sources:     sources,
		KojoPlan:    strings.TrimSpace(kojoPlan),
	}

	if src, ok := sources["did_document"]; ok && src.StatusCode != http.StatusOK {
		tmpl := buildDidDocumentTemplate(targetDID)
		tmplJSON, err := json.MarshalIndent(tmpl, "", "  ")
		if err != nil {
			return fmt.Errorf("marshal did template: %w", err)
		}
		if err := os.WriteFile(templatePath, tmplJSON, 0o644); err != nil {
			return fmt.Errorf("write did template: %w", err)
		}
		artifacts = append(artifacts, templatePath)
	}

	report.Artifacts = artifacts
	data, err := json.MarshalIndent(report, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal kojo report: %w", err)
	}
	if err := os.WriteFile(reportPath, data, 0o644); err != nil {
		return fmt.Errorf("write kojo report: %w", err)
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	fmt.Printf("DID: %s\n", targetDID)
	fmt.Printf("Model: %s\n", resolvedModel)
	fmt.Printf("kojo report: %s\n", reportPath)
	for _, p := range artifacts[1:] {
		fmt.Printf("artifact: %s\n", p)
	}
	fmt.Println()
	fmt.Println(strings.TrimSpace(kojoPlan))
	return nil
}

func printHinshitsuUsage() {
	fmt.Print(`gftd hinshitsu — DID profile information quality evaluation + improvement proposals (Murakumo OpenAI API)

USAGE:
  gftd hinshitsu --did <did:web:...> [flags]
  gftd hinshitsu kojo --did <did:web:...> [flags]
  gftd hinshitsu actors [flags]
  gftd hinshitsu fleet <scan|evaluate|kaizen|verify|diff-fixed> [flags]

FLAGS:
  --did                 target DID (required), e.g. did:web:tnt4ib0d.etzhayyim.com
  --pds                 PDS base URL (default: https://mod.etzhayyim.com)
  --model               model id (default: GFTD_HINSHITSU_MODEL or GFTD_CODE_MODEL, else auto-detect)
  --api-base            OpenAI-compatible base URL (default: OPENAI_API_BASE or https://murakumo.etzhayyim.com/v1)
  --api-key             API key (default: OPENAI_API_KEY)
  --timeout             HTTP timeout (default: 20s)
  --no-auto-model       disable model auto-detection via /models
  --json                output JSON report

ENV:
  GFTD_HINSHITSU_MODEL
  GFTD_CODE_MODEL
  OPENAI_API_BASE
  OPENAI_API_KEY
  GFTD_PDS_URL

EXAMPLES:
  gftd hinshitsu --did did:web:tnt4ib0d.etzhayyim.com
  gftd hinshitsu kojo --did did:web:tnt4ib0d.etzhayyim.com
  gftd hinshitsu fleet scan --out reports/hinshitsu-fleet-scan.json
  gftd hinshitsu fleet evaluate --input reports/hinshitsu-fleet-scan.json --out reports/hinshitsu-fleet-score.json
  gftd hinshitsu actors --input reports/hinshitsu-fleet-score.json
  gftd hinshitsu actors --input reports/hinshitsu-fleet-score-all.json --min-score 10 --out reports/hinshitsu-actors-actions.json
  gftd hinshitsu fleet kaizen --input reports/hinshitsu-fleet-score.json --auto-safe --out reports/hinshitsu-fleet-kaizen.json
  gftd hinshitsu fleet verify --input reports/hinshitsu-fleet-kaizen.json --out reports/hinshitsu-fleet-verify.json
  gftd hinshitsu fleet diff-fixed --before-scan reports/a-scan.json --after-scan reports/b-scan.json --before-score reports/a-score.json --after-score reports/b-score.json --did-list reports/fixed-dids.txt --out reports/diff.json
  gftd hinshitsu --did did:web:tnt4ib0d.etzhayyim.com --model qwen2.5-coder-32b-instruct
  gftd hinshitsu --did did:web:tnt4ib0d.etzhayyim.com --json > reports/hinshitsu.json
`)
}

func runHinshitsuActors(args []string) error {
	defaultInput := ""
	for _, candidate := range []string{"reports/hinshitsu-fleet-score-all.json", "reports/hinshitsu-fleet-score.json"} {
		if _, err := os.Stat(candidate); err == nil {
			defaultInput = candidate
			break
		}
	}
	fs := flag.NewFlagSet("hinshitsu actors", flag.ContinueOnError)
	input := fs.String("input", defaultInput, "input score report JSON (default: reports/hinshitsu-fleet-score-all.json or reports/hinshitsu-fleet-score.json)")
	minScore := fs.Float64("min-score", 10, "target minimum score")
	limit := fs.Int("limit", 0, "max rows (0=all)")
	includeAll := fs.Bool("all", false, "include actors already meeting min-score")
	out := fs.String("out", "", "write JSON report to file")
	jsonOut := fs.Bool("json", false, "print JSON report to stdout")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*input) == "" {
		return fmt.Errorf("--input is required")
	}
	var score hinshitsuFleetScoreReport
	if err := readJSONFile(*input, &score); err != nil {
		return err
	}
	items := make([]hinshitsuActorsItem, 0, len(score.Results))
	for _, r := range score.Results {
		if !*includeAll && r.TotalScore >= *minScore {
			continue
		}
		recs := buildActorRecommendations(r.DID, r.Findings)
		items = append(items, hinshitsuActorsItem{
			DID:             r.DID,
			Nanoid:          r.Nanoid,
			TotalScore:      r.TotalScore,
			Grade:           r.Grade,
			Priority:        actorActionPriority(r.TotalScore, *minScore, r.Findings),
			Findings:        r.Findings,
			Recommendations: recs,
		})
	}
	sort.Slice(items, func(i, j int) bool {
		if items[i].TotalScore == items[j].TotalScore {
			if len(items[i].Findings) == len(items[j].Findings) {
				return items[i].DID < items[j].DID
			}
			return len(items[i].Findings) > len(items[j].Findings)
		}
		return items[i].TotalScore < items[j].TotalScore
	})
	if *limit > 0 && *limit < len(items) {
		items = items[:*limit]
	}
	report := hinshitsuActorsReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Input:       *input,
		MinScore:    round2(*minScore),
		Count:       len(items),
		Items:       items,
	}
	return writeFleetOutput(report, *out, *jsonOut)
}

func runHinshitsuFleet(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: gftd hinshitsu fleet <scan|evaluate|kaizen|verify|diff-fixed> [flags]")
	}
	switch args[0] {
	case "scan":
		return runHinshitsuFleetScan(args[1:])
	case "evaluate":
		return runHinshitsuFleetEvaluate(args[1:])
	case "kaizen":
		return runHinshitsuFleetKaizen(args[1:])
	case "verify":
		return runHinshitsuFleetVerify(args[1:])
	case "diff-fixed":
		return runHinshitsuFleetDiffFixed(args[1:])
	case "help", "--help", "-h":
		printHinshitsuUsage()
		return nil
	default:
		return fmt.Errorf("unknown fleet subcommand: %s", args[0])
	}
}

func runHinshitsuFleetScan(args []string) error {
	fs := flag.NewFlagSet("hinshitsu fleet scan", flag.ContinueOnError)
	pdsURL := fs.String("pds", envOr("GFTD_PDS_URL", hinshitsuDefaultPDSURL), "PDS base URL")
	org := fs.String("org", "", "optional X-Gftd-Org-Id override")
	timeout := fs.Duration("timeout", 20*time.Second, "HTTP timeout")
	limitPosts := fs.Int("limit-posts", 50, "author feed limit per DID")
	limitTargets := fs.Int("limit-targets", 0, "max number of DID targets (0=all)")
	concurrency := fs.Int("concurrency", 12, "parallel workers for source collection")
	out := fs.String("out", "", "write JSON report to file")
	jsonOut := fs.Bool("json", false, "print JSON report to stdout")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *limitPosts < 1 {
		*limitPosts = 1
	}
	if *limitPosts > 100 {
		*limitPosts = 100
	}
	if *concurrency < 1 {
		*concurrency = 1
	}
	client := &http.Client{Timeout: *timeout}
	apps, source, err := queryHeartbeatApps(client, strings.TrimRight(*pdsURL, "/"), *org)
	if err != nil {
		return err
	}
	sort.Strings(apps)
	if *limitTargets > 0 && *limitTargets < len(apps) {
		apps = apps[:*limitTargets]
	}

	targets := make([]hinshitsuFleetTarget, len(apps))
	token := resolveGFTDToken()
	sem := make(chan struct{}, *concurrency)
	done := make(chan int, len(apps))
	for i, app := range apps {
		go func(idx int, nanoid string) {
			sem <- struct{}{}
			defer func() { <-sem }()
			nanoid = strings.TrimSpace(nanoid)
			if nanoid == "" {
				done <- idx
				return
			}
			did := resolveFleetTargetDID(client, strings.TrimRight(*pdsURL, "/"), nanoid, token)
			_, _, sources, err := collectHinshitsuSources(client, did, *pdsURL)
			if err != nil {
				sources = map[string]hinshitsuSrc{
					"collector_error": {URL: did, Error: err.Error()},
				}
			}
			posts := collectAuthorFeed(client, strings.TrimRight(*pdsURL, "/"), did, *limitPosts)
			targets[idx] = hinshitsuFleetTarget{
				Nanoid:  nanoid,
				DID:     did,
				Sources: sources,
				Posts:   posts,
			}
			done <- idx
		}(i, app)
	}
	for range apps {
		<-done
	}
	finalTargets := make([]hinshitsuFleetTarget, 0, len(targets))
	for _, t := range targets {
		if strings.TrimSpace(t.Nanoid) == "" {
			continue
		}
		finalTargets = append(finalTargets, t)
	}

	report := hinshitsuFleetScanReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		PDS:         strings.TrimRight(*pdsURL, "/"),
		Source:      source,
		Targets:     finalTargets,
	}
	return writeFleetOutput(report, *out, *jsonOut)
}

func runHinshitsuFleetEvaluate(args []string) error {
	fs := flag.NewFlagSet("hinshitsu fleet evaluate", flag.ContinueOnError)
	input := fs.String("input", "", "input scan report JSON (required)")
	out := fs.String("out", "", "write JSON report to file")
	jsonOut := fs.Bool("json", false, "print JSON report to stdout")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*input) == "" {
		return fmt.Errorf("--input is required")
	}
	var scan hinshitsuFleetScanReport
	if err := readJSONFile(*input, &scan); err != nil {
		return err
	}

	results := make([]hinshitsuFleetScoreResult, 0, len(scan.Targets))
	for _, t := range scan.Targets {
		profile, breakdown, findings := scoreFleetProfile(t)
		posts, postFindings := scoreFleetPosts(t.Posts)
		findings = append(findings, postFindings...)
		total := round2(0.6*profile + 0.4*posts)
		results = append(results, hinshitsuFleetScoreResult{
			DID:          t.DID,
			Nanoid:       t.Nanoid,
			ProfileScore: round2(profile),
			PostsScore:   round2(posts),
			TotalScore:   total,
			Grade:        fleetGrade(total),
			Breakdown:    breakdown,
			Findings:     findings,
		})
	}
	sort.Slice(results, func(i, j int) bool { return results[i].TotalScore < results[j].TotalScore })
	report := hinshitsuFleetScoreReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Results:     results,
	}
	return writeFleetOutput(report, *out, *jsonOut)
}

func runHinshitsuFleetKaizen(args []string) error {
	fs := flag.NewFlagSet("hinshitsu fleet kaizen", flag.ContinueOnError)
	input := fs.String("input", "", "input score report JSON (required)")
	minScore := fs.Float64("min-score", 10, "target minimum score")
	autoSafe := fs.Bool("auto-safe", false, "mark safe actions as applied")
	out := fs.String("out", "", "write JSON report to file")
	jsonOut := fs.Bool("json", false, "print JSON report to stdout")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*input) == "" {
		return fmt.Errorf("--input is required")
	}
	var score hinshitsuFleetScoreReport
	if err := readJSONFile(*input, &score); err != nil {
		return err
	}
	actions := make([]hinshitsuFleetAction, 0, len(score.Results))
	for _, r := range score.Results {
		if r.TotalScore >= *minScore {
			continue
		}
		changes := make([]string, 0, 4)
		after := r.TotalScore
		mode := "approval-required"
		status := "planned"
		if didDocMissing(r.Findings) {
			changes = append(changes, "add/.well-known/did.json")
			after += 2
			mode = "auto-safe"
		}
		if missingVerification(r.Findings) {
			changes = append(changes, "add verificationMethod/authentication")
			after += 1
			mode = "auto-safe"
		}
		if missingCapabilities(r.Findings) {
			changes = append(changes, "add service.capabilities")
			after += 0.5
			mode = "auto-safe"
		}
		if staleContent(r.Findings) {
			changes = append(changes, "review indexedAt/profile freshness")
			mode = "approval-required"
		}
		if len(changes) == 0 {
			changes = append(changes, "manual review required")
		}
		if *autoSafe && mode == "auto-safe" {
			status = "applied"
		}
		actions = append(actions, hinshitsuFleetAction{
			DID:         r.DID,
			ActionID:    "kaizen-" + didToSlug(r.DID),
			Mode:        mode,
			Status:      status,
			BeforeScore: r.TotalScore,
			AfterScore:  round2(after),
			Changes:     changes,
		})
	}
	report := hinshitsuFleetKaizenReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Actions:     actions,
	}
	return writeFleetOutput(report, *out, *jsonOut)
}

func runHinshitsuFleetVerify(args []string) error {
	fs := flag.NewFlagSet("hinshitsu fleet verify", flag.ContinueOnError)
	input := fs.String("input", "", "input kaizen report JSON (required)")
	out := fs.String("out", "", "write JSON report to file")
	jsonOut := fs.Bool("json", false, "print JSON report to stdout")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*input) == "" {
		return fmt.Errorf("--input is required")
	}
	var kaizen hinshitsuFleetKaizenReport
	if err := readJSONFile(*input, &kaizen); err != nil {
		return err
	}
	results := make([]hinshitsuFleetVerifyResult, 0, len(kaizen.Actions))
	for _, a := range kaizen.Actions {
		v := hinshitsuFleetVerifyResult{
			DID:         a.DID,
			ActionID:    a.ActionID,
			Status:      a.Status,
			BeforeScore: a.BeforeScore,
			AfterScore:  a.AfterScore,
		}
		if a.Status == "applied" && a.AfterScore >= a.BeforeScore {
			v.Verified = true
			v.Reason = "applied-with-nonnegative-delta"
		} else if a.Status == "planned" {
			v.Verified = false
			v.Reason = "not-applied"
		} else if a.Status == "failed" {
			v.Verified = false
			v.Reason = "apply-failed"
		} else {
			v.Verified = a.AfterScore > a.BeforeScore
			if !v.Verified {
				v.Reason = "no-score-improvement"
			}
		}
		results = append(results, v)
	}
	report := hinshitsuFleetVerifyReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Results:     results,
	}
	return writeFleetOutput(report, *out, *jsonOut)
}

func runHinshitsuFleetDiffFixed(args []string) error {
	fs := flag.NewFlagSet("hinshitsu fleet diff-fixed", flag.ContinueOnError)
	beforeScanPath := fs.String("before-scan", "", "before scan report JSON (required)")
	afterScanPath := fs.String("after-scan", "", "after scan report JSON (required)")
	beforeScorePath := fs.String("before-score", "", "before score report JSON (required)")
	afterScorePath := fs.String("after-score", "", "after score report JSON (required)")
	didListPath := fs.String("did-list", "", "optional fixed DID list file (one did:web:* or nanoid per line)")
	out := fs.String("out", "", "write JSON report to file")
	jsonOut := fs.Bool("json", false, "print JSON report to stdout")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*beforeScanPath) == "" || strings.TrimSpace(*afterScanPath) == "" || strings.TrimSpace(*beforeScorePath) == "" || strings.TrimSpace(*afterScorePath) == "" {
		return fmt.Errorf("--before-scan --after-scan --before-score --after-score are required")
	}

	var beforeScan, afterScan hinshitsuFleetScanReport
	var beforeScore, afterScore hinshitsuFleetScoreReport
	if err := readJSONFile(*beforeScanPath, &beforeScan); err != nil {
		return err
	}
	if err := readJSONFile(*afterScanPath, &afterScan); err != nil {
		return err
	}
	if err := readJSONFile(*beforeScorePath, &beforeScore); err != nil {
		return err
	}
	if err := readJSONFile(*afterScorePath, &afterScore); err != nil {
		return err
	}

	beforeScanMap := make(map[string]hinshitsuFleetTarget, len(beforeScan.Targets))
	for _, t := range beforeScan.Targets {
		if strings.TrimSpace(t.DID) != "" {
			beforeScanMap[t.DID] = t
		}
	}
	afterScanMap := make(map[string]hinshitsuFleetTarget, len(afterScan.Targets))
	for _, t := range afterScan.Targets {
		if strings.TrimSpace(t.DID) != "" {
			afterScanMap[t.DID] = t
		}
	}
	beforeScoreMap := make(map[string]hinshitsuFleetScoreResult, len(beforeScore.Results))
	for _, r := range beforeScore.Results {
		if strings.TrimSpace(r.DID) != "" {
			beforeScoreMap[r.DID] = r
		}
	}
	afterScoreMap := make(map[string]hinshitsuFleetScoreResult, len(afterScore.Results))
	for _, r := range afterScore.Results {
		if strings.TrimSpace(r.DID) != "" {
			afterScoreMap[r.DID] = r
		}
	}

	dids, err := resolveFixedDiffDIDs(*didListPath, beforeScanMap, afterScanMap, beforeScoreMap, afterScoreMap)
	if err != nil {
		return err
	}
	sort.Strings(dids)

	missingBefore := make([]string, 0)
	missingAfter := make([]string, 0)
	for _, did := range dids {
		if _, ok := beforeScanMap[did]; !ok {
			missingBefore = append(missingBefore, did)
			continue
		}
		if _, ok := beforeScoreMap[did]; !ok {
			missingBefore = append(missingBefore, did)
		}
	}
	for _, did := range dids {
		if _, ok := afterScanMap[did]; !ok {
			missingAfter = append(missingAfter, did)
			continue
		}
		if _, ok := afterScoreMap[did]; !ok {
			missingAfter = append(missingAfter, did)
		}
	}

	beforeSnap := summarizeFixedDiff(dids, beforeScanMap, beforeScoreMap)
	afterSnap := summarizeFixedDiff(dids, afterScanMap, afterScoreMap)
	report := hinshitsuFleetDiffReport{
		GeneratedAt:     time.Now().UTC().Format(time.RFC3339),
		ComparedDIDs:    dids,
		MissingInBefore: missingBefore,
		MissingInAfter:  missingAfter,
		Before:          beforeSnap,
		After:           afterSnap,
		Delta: hinshitsuFleetDiffDelta{
			ScanCount:           afterSnap.ScanCount - beforeSnap.ScanCount,
			ScoreCount:          afterSnap.ScoreCount - beforeSnap.ScoreCount,
			DidDocReachable:     afterSnap.DidDocReachable - beforeSnap.DidDocReachable,
			AtprotoDidReachable: afterSnap.AtprotoDidReachable - beforeSnap.AtprotoDidReachable,
			WithPosts:           afterSnap.WithPosts - beforeSnap.WithPosts,
			AvgTotalScore:       round2(afterSnap.AvgTotalScore - beforeSnap.AvgTotalScore),
		},
	}
	if strings.TrimSpace(*didListPath) != "" {
		report.DidListSource = *didListPath
	}
	return writeFleetOutput(report, *out, *jsonOut)
}

func collectAuthorFeed(client *http.Client, pdsURL, did string, limit int) []hinshitsuFleetPost {
	base := strings.TrimRight(pdsURL, "/")
	posts, ok := collectAuthorFeedFromBase(client, base, did, limit)
	if ok {
		return posts
	}
	if fb, useFallback := fallbackPDSBase(base); useFallback {
		posts, ok = collectAuthorFeedFromBase(client, fb, did, limit)
		if ok {
			return posts
		}
	}
	return nil
}

func resolveFleetTargetDID(client *http.Client, pdsURL, nanoid, token string) string {
	nanoid = strings.TrimSpace(nanoid)
	fallback := "did:web:" + nanoid + ".etzhayyim.com"
	if nanoid == "" {
		return fallback
	}
	if rows, err := rwQueryRows(`SELECT did FROM vertex_app WHERE nanoid = $1 LIMIT 1`, nanoid); err == nil && len(rows) > 0 && len(rows[0]) > 0 {
		if did := strings.TrimSpace(fmt.Sprint(rows[0][0])); strings.HasPrefix(did, "did:web:") {
			return did
		}
	}

	reqURL := strings.TrimRight(pdsURL, "/") + "/xrpc/com.atproto.identity.resolveHandle?handle=" + url.QueryEscape(nanoid+".etzhayyim.com")
	req, err := http.NewRequest("GET", reqURL, nil)
	if err != nil {
		return fallback
	}
	if strings.TrimSpace(token) != "" {
		req.Header.Set("Authorization", "Bearer "+strings.TrimSpace(token))
	}
	resp, err := client.Do(req)
	if err != nil {
		return fallback
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return fallback
	}
	var parsed struct {
		DID string `json:"did"`
	}
	if json.NewDecoder(resp.Body).Decode(&parsed) == nil {
		d := strings.TrimSpace(parsed.DID)
		if strings.HasPrefix(d, "did:web:") {
			return d
		}
	}
	return fallback
}

func collectAuthorFeedFromBase(client *http.Client, pdsBase, did string, limit int) ([]hinshitsuFleetPost, bool) {
	url := fmt.Sprintf("%s/xrpc/app.bsky.feed.getAuthorFeed?actor=%s&limit=%d", strings.TrimRight(pdsBase, "/"), url.QueryEscape(did), limit)
	req, err := http.NewRequest(http.MethodGet, url, nil)
	if err != nil {
		return nil, false
	}
	resp, err := client.Do(req)
	if err != nil {
		return nil, false
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return nil, false
	}
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 2*1024*1024))
	var parsed map[string]any
	if err := json.Unmarshal(body, &parsed); err != nil {
		return nil, false
	}
	feedRaw, ok := parsed["feed"].([]any)
	if !ok {
		return nil, false
	}
	out := make([]hinshitsuFleetPost, 0, len(feedRaw))
	for _, item := range feedRaw {
		m, ok := item.(map[string]any)
		if !ok {
			continue
		}
		postObj, _ := m["post"].(map[string]any)
		recordObj, _ := postObj["record"].(map[string]any)
		p := hinshitsuFleetPost{
			URI:         toString(postObj["uri"]),
			IndexedAt:   toString(postObj["indexedAt"]),
			Text:        toString(recordObj["text"]),
			LikeCount:   toIntAny(m["likeCount"]),
			RepostCount: toIntAny(m["repostCount"]),
			ReplyCount:  toIntAny(m["replyCount"]),
		}
		if p.URI == "" && p.Text == "" {
			continue
		}
		out = append(out, p)
	}
	return out, true
}

func scoreFleetProfile(t hinshitsuFleetTarget) (float64, map[string]float64, []hinshitsuFleetFinding) {
	b := map[string]float64{
		"authenticity":  0,
		"sourceability": 0,
		"verifiability": 0,
		"consistency":   0,
		"freshness":     0,
		"transparency":  0,
	}
	findings := make([]hinshitsuFleetFinding, 0)
	didSrc := t.Sources["did_document"]
	atpSrc := t.Sources["atproto_profile"]
	atDidSrc := t.Sources["atproto_did"]
	if atDidSrc.URL == "" {
		// virtual source when endpoint is not explicitly collected
		atDidSrc = hinshitsuSrc{StatusCode: http.StatusNotFound}
	}
	metaSrc := t.Sources["app_meta"]

	if didSrc.StatusCode == http.StatusOK {
		b["authenticity"] = 1
		if strings.Contains(didSrc.Snippet, "verificationMethod") {
			b["authenticity"] = 2
		}
	} else {
		findings = append(findings, hinshitsuFleetFinding{Severity: "critical", Category: "did_document", Message: "did document missing", Evidence: didSrc.Error})
	}

	okSources := 0
	for _, k := range []string{"did_document", "atproto_profile", "yoro_profile_page", "app_meta"} {
		if t.Sources[k].StatusCode == http.StatusOK {
			okSources++
		}
	}
	switch {
	case okSources >= 4:
		b["sourceability"] = 2
	case okSources >= 2:
		b["sourceability"] = 1
	default:
		b["sourceability"] = 0
	}

	if didSrc.StatusCode == http.StatusOK && (strings.Contains(didSrc.Snippet, "publicKeyMultibase") || strings.Contains(didSrc.Snippet, "publicKeyJwk")) {
		b["verifiability"] = 2
	} else if didSrc.StatusCode == http.StatusOK {
		b["verifiability"] = 1
		findings = append(findings, hinshitsuFleetFinding{Severity: "high", Category: "verification", Message: "verification key is missing in did document"})
	} else {
		b["verifiability"] = 0
	}

	if atpSrc.StatusCode == http.StatusOK && strings.Contains(atpSrc.Snippet, t.DID) {
		b["consistency"] = 1
		if metaSrc.StatusCode == http.StatusOK && strings.Contains(metaSrc.Snippet, t.Nanoid) {
			b["consistency"] = 2
		}
	} else {
		findings = append(findings, hinshitsuFleetFinding{Severity: "high", Category: "consistency", Message: "profile did mismatch or unavailable"})
	}

	latest := latestIndexedAt(t.Posts)
	if latest.IsZero() {
		b["freshness"] = 1
		findings = append(findings, hinshitsuFleetFinding{Severity: "low", Category: "freshness", Message: "no posts to evaluate freshness"})
	} else {
		age := time.Since(latest)
		if age < 0 {
			b["freshness"] = 0
			findings = append(findings, hinshitsuFleetFinding{Severity: "high", Category: "freshness", Message: "latest post indexedAt is in the future"})
		} else if age <= 7*24*time.Hour {
			b["freshness"] = 2
		} else {
			b["freshness"] = 1
			findings = append(findings, hinshitsuFleetFinding{Severity: "medium", Category: "freshness", Message: "latest post is stale (>7 days)"})
		}
	}

	if metaSrc.StatusCode == http.StatusOK && strings.Contains(didSrc.Snippet, "serviceEndpoint") {
		b["transparency"] = 1
		if strings.Contains(metaSrc.Snippet, "capabilities") {
			b["transparency"] = 2
		}
	} else {
		findings = append(findings, hinshitsuFleetFinding{Severity: "medium", Category: "transparency", Message: "service metadata is insufficient"})
	}

	// atproto-did currently optional; downgrade only if missing did doc too
	if atDidSrc.StatusCode != http.StatusOK && didSrc.StatusCode != http.StatusOK {
		findings = append(findings, hinshitsuFleetFinding{Severity: "high", Category: "atproto_discovery", Message: "both did document and atproto discovery are unavailable"})
	}

	profileScore := 0.0
	for _, v := range b {
		profileScore += v
	}
	return profileScore, b, findings
}

func scoreFleetPosts(posts []hinshitsuFleetPost) (float64, []hinshitsuFleetFinding) {
	findings := make([]hinshitsuFleetFinding, 0)
	if len(posts) == 0 {
		return 2, []hinshitsuFleetFinding{{Severity: "low", Category: "posts", Message: "no posts found"}}
	}

	factual := 2.0
	sources := 0.0
	consistency := 2.0
	safety := 2.0
	freshness := 0.0
	utility := 0.0
	longTexts := 0
	hasURLs := 0
	for _, p := range posts {
		if len(strings.TrimSpace(p.Text)) >= 40 {
			longTexts++
		}
		if strings.Contains(p.Text, "http://") || strings.Contains(p.Text, "https://") {
			hasURLs++
		}
		if strings.Contains(strings.ToLower(p.Text), "guaranteed") || strings.Contains(strings.ToLower(p.Text), "100%") {
			safety = 1
			findings = append(findings, hinshitsuFleetFinding{Severity: "medium", Category: "safety", Message: "potentially risky absolute claim in posts", Evidence: p.URI})
		}
	}
	if longTexts > 0 {
		utility = 2
	} else {
		utility = 1
	}
	if hasURLs > 0 {
		sources = 2
	} else {
		sources = 1
		findings = append(findings, hinshitsuFleetFinding{Severity: "low", Category: "citations", Message: "posts have no explicit source links"})
	}
	latest := latestIndexedAt(posts)
	if latest.IsZero() {
		freshness = 1
	} else {
		age := time.Since(latest)
		if age < 0 {
			freshness = 0
		} else if age <= 7*24*time.Hour {
			freshness = 2
		} else {
			freshness = 1
		}
	}
	score := factual + sources + consistency + safety + freshness + utility
	return score, findings
}

func didDocMissing(findings []hinshitsuFleetFinding) bool {
	for _, f := range findings {
		if f.Category == "did_document" {
			return true
		}
	}
	return false
}

func missingVerification(findings []hinshitsuFleetFinding) bool {
	for _, f := range findings {
		if f.Category == "verification" {
			return true
		}
	}
	return false
}

func staleContent(findings []hinshitsuFleetFinding) bool {
	for _, f := range findings {
		if f.Category == "freshness" {
			return true
		}
	}
	return false
}

func missingCapabilities(findings []hinshitsuFleetFinding) bool {
	for _, f := range findings {
		if f.Category == "transparency" {
			return true
		}
	}
	return false
}

func buildActorRecommendations(did string, findings []hinshitsuFleetFinding) []string {
	nanoid, ok := didWebNanoid(did)
	if !ok {
		nanoid = ""
	}
	out := make([]string, 0, 8)
	seen := map[string]bool{}
	add := func(rec string) {
		rec = strings.TrimSpace(rec)
		if rec == "" || seen[rec] {
			return
		}
		seen[rec] = true
		out = append(out, rec)
	}
	for _, f := range findings {
		switch f.Category {
		case "did_document":
			if nanoid != "" {
				add("`https://" + nanoid + ".etzhayyim.com/.well-known/did.json` を追加し、`id` を `" + did + "` に合わせる")
			} else {
				add("`/.well-known/did.json` を追加して DID document を公開する")
			}
		case "verification":
			add("`did.json` に `verificationMethod` と `authentication` を追加し、`publicKeyMultibase` か `publicKeyJwk` を設定する")
		case "transparency":
			add("`/_app/meta` の `capabilities` と `serviceEndpoint` を明示してサービス情報を補完する")
		case "freshness":
			add("7日以内の最新投稿を維持し、`indexedAt` が未来日付にならないよう更新フローを修正する")
		case "consistency":
			add("`app.bsky.actor.getProfile` の DID と `did.json` の `id` を一致させる")
		case "atproto_discovery":
			add("`/.well-known/atproto-did` を追加し DID 解決経路を有効化する")
		case "posts":
			add("Author feed に説明責任のある投稿を追加して投稿空状態を解消する")
		case "citations":
			add("投稿本文に出典 URL を含め、根拠追跡可能性を上げる")
		case "safety":
			add("`guaranteed` / `100%` など断定表現を避け、検証可能な表現へ修正する")
		}
	}
	if len(out) == 0 {
		add("目立つ欠陥なし。定期的に `gftd hinshitsu --did " + did + " --json` を実行して劣化監視する")
	}
	return out
}

func actorActionPriority(totalScore, minScore float64, findings []hinshitsuFleetFinding) string {
	if totalScore >= minScore {
		return "P3"
	}
	deficit := minScore - totalScore
	hasCritical := false
	hasHigh := false
	hasMedium := false
	for _, f := range findings {
		switch strings.ToLower(strings.TrimSpace(f.Severity)) {
		case "critical":
			hasCritical = true
		case "high":
			hasHigh = true
		case "medium":
			hasMedium = true
		}
	}
	switch {
	case hasCritical || deficit >= 5:
		return "P0"
	case hasHigh || deficit >= 3:
		return "P1"
	case hasMedium || deficit > 0:
		return "P2"
	default:
		return "P3"
	}
}

func latestIndexedAt(posts []hinshitsuFleetPost) time.Time {
	latest := time.Time{}
	for _, p := range posts {
		if strings.TrimSpace(p.IndexedAt) == "" {
			continue
		}
		t, err := time.Parse(time.RFC3339, p.IndexedAt)
		if err != nil {
			continue
		}
		if latest.IsZero() || t.After(latest) {
			latest = t
		}
	}
	return latest
}

func resolveFixedDiffDIDs(
	didListPath string,
	beforeScan map[string]hinshitsuFleetTarget,
	afterScan map[string]hinshitsuFleetTarget,
	beforeScore map[string]hinshitsuFleetScoreResult,
	afterScore map[string]hinshitsuFleetScoreResult,
) ([]string, error) {
	if strings.TrimSpace(didListPath) != "" {
		b, err := os.ReadFile(didListPath)
		if err != nil {
			return nil, fmt.Errorf("read did list %s: %w", didListPath, err)
		}
		set := map[string]struct{}{}
		for _, line := range strings.Split(string(b), "\n") {
			s := strings.TrimSpace(line)
			if s == "" || strings.HasPrefix(s, "#") {
				continue
			}
			if strings.HasPrefix(s, "did:web:") {
				set[s] = struct{}{}
				continue
			}
			set["did:web:"+s+".etzhayyim.com"] = struct{}{}
		}
		out := make([]string, 0, len(set))
		for did := range set {
			out = append(out, did)
		}
		return out, nil
	}

	// No fixed list: compare strict intersection (same DID present in all four reports).
	out := make([]string, 0)
	for did := range beforeScan {
		if _, ok := afterScan[did]; !ok {
			continue
		}
		if _, ok := beforeScore[did]; !ok {
			continue
		}
		if _, ok := afterScore[did]; !ok {
			continue
		}
		out = append(out, did)
	}
	return out, nil
}

func summarizeFixedDiff(
	dids []string,
	scanMap map[string]hinshitsuFleetTarget,
	scoreMap map[string]hinshitsuFleetScoreResult,
) hinshitsuFleetDiffSnapshot {
	s := hinshitsuFleetDiffSnapshot{
		DIDCount: len(dids),
		Grades:   map[string]int{},
	}
	sum := 0.0
	for _, did := range dids {
		if t, ok := scanMap[did]; ok {
			s.ScanCount++
			if t.Sources["did_document"].StatusCode == http.StatusOK {
				s.DidDocReachable++
			}
			if t.Sources["atproto_did"].StatusCode == http.StatusOK {
				s.AtprotoDidReachable++
			}
			if len(t.Posts) > 0 {
				s.WithPosts++
			}
		}
		if r, ok := scoreMap[did]; ok {
			s.ScoreCount++
			sum += r.TotalScore
			s.Grades[r.Grade]++
		}
	}
	if s.ScoreCount > 0 {
		s.AvgTotalScore = round2(sum / float64(s.ScoreCount))
	}
	return s
}

func toString(v any) string {
	if v == nil {
		return ""
	}
	return fmt.Sprintf("%v", v)
}

func toIntAny(v any) int {
	switch n := v.(type) {
	case int:
		return n
	case int64:
		return int(n)
	case float64:
		return int(n)
	case json.Number:
		i, _ := n.Int64()
		return int(i)
	case string:
		i, _ := strconv.Atoi(strings.TrimSpace(n))
		return i
	default:
		return 0
	}
}

func fleetGrade(score float64) string {
	switch {
	case score >= 10:
		return "high"
	case score >= 7:
		return "caution"
	default:
		return "low"
	}
}

func round2(v float64) float64 {
	return float64(int(v*100+0.5)) / 100
}

func readJSONFile(path string, out any) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("read %s: %w", path, err)
	}
	if err := json.Unmarshal(b, out); err != nil {
		return fmt.Errorf("parse %s: %w", path, err)
	}
	return nil
}

func writeFleetOutput(v any, out string, jsonOut bool) error {
	if strings.TrimSpace(out) != "" {
		b, err := json.MarshalIndent(v, "", "  ")
		if err != nil {
			return err
		}
		if err := os.WriteFile(out, b, 0o644); err != nil {
			return fmt.Errorf("write %s: %w", out, err)
		}
	}
	if jsonOut || strings.TrimSpace(out) == "" {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(v)
	}
	return nil
}

func collectHinshitsuSources(client *http.Client, targetDID, pdsURL string) (didDocBody string, profileBody string, sources map[string]hinshitsuSrc, err error) {
	normPDS := strings.TrimRight(strings.TrimSpace(pdsURL), "/")
	sources = map[string]hinshitsuSrc{}

	didDocURL, err := didWebDocumentURL(targetDID)
	if err != nil {
		return "", "", nil, err
	}
	didDocBody, didDocSrc := fetchSource(client, didDocURL)
	sources["did_document"] = didDocSrc

	atprotoDidURL := strings.TrimSuffix(didDocURL, "did.json") + "atproto-did"
	_, atprotoDidSrc := fetchSource(client, atprotoDidURL)
	sources["atproto_did"] = atprotoDidSrc

	profileURL := normPDS + "/xrpc/app.bsky.actor.getProfile?actor=" + url.QueryEscape(targetDID)
	profileBody, profileSrc := fetchSource(client, profileURL)
	if fb, useFallback := fallbackPDSBase(normPDS); useFallback && shouldFallbackXrpcSource(profileSrc) {
		fallbackURL := fb + "/xrpc/app.bsky.actor.getProfile?actor=" + url.QueryEscape(targetDID)
		if b2, s2 := fetchSource(client, fallbackURL); s2.StatusCode == http.StatusOK {
			profileBody = b2
			profileSrc = s2
		}
	}
	sources["atproto_profile"] = profileSrc

	yoroURL := "https://yoro.etzhayyim.com/profile/" + url.QueryEscape(targetDID)
	_, yoroSrc := fetchSource(client, yoroURL)
	sources["yoro_profile_page"] = yoroSrc

	if nanoid, ok := didWebNanoid(targetDID); ok {
		metaURL := "https://" + nanoid + ".etzhayyim.com/_app/meta"
		_, metaSrc := fetchSource(client, metaURL)
		sources["app_meta"] = metaSrc
	}
	return didDocBody, profileBody, sources, nil
}

func fallbackPDSBase(base string) (string, bool) {
	trimmed := strings.TrimRight(strings.TrimSpace(base), "/")
	if trimmed == "" {
		return "", false
	}
	u, err := url.Parse(trimmed)
	if err != nil {
		return "", false
	}
	if !strings.EqualFold(u.Host, "mod.etzhayyim.com") {
		return "", false
	}
	if strings.EqualFold(trimmed, hinshitsuFallbackPDSURL) {
		return "", false
	}
	return hinshitsuFallbackPDSURL, true
}

func shouldFallbackXrpcSource(src hinshitsuSrc) bool {
	if src.Error != "" {
		return true
	}
	return src.StatusCode >= 500
}

func didWebDocumentURL(did string) (string, error) {
	if !strings.HasPrefix(did, "did:web:") {
		return "", fmt.Errorf("unsupported DID method (expected did:web): %s", did)
	}
	parts := strings.Split(did, ":")
	if len(parts) < 3 {
		return "", fmt.Errorf("invalid did:web format: %s", did)
	}

	host := strings.TrimSpace(parts[2])
	if host == "" {
		return "", fmt.Errorf("invalid did:web host: %s", did)
	}

	if len(parts) == 3 {
		return "https://" + host + "/.well-known/did.json", nil
	}

	segments := make([]string, 0, len(parts)-3)
	for _, s := range parts[3:] {
		s = strings.TrimSpace(s)
		if s == "" {
			continue
		}
		segments = append(segments, s)
	}
	p := path.Join(segments...)
	if p == "." {
		p = ""
	}
	if p == "" {
		return "https://" + host + "/.well-known/did.json", nil
	}
	return "https://" + host + "/" + p + "/did.json", nil
}

func didWebNanoid(did string) (string, bool) {
	parts := strings.Split(did, ":")
	if len(parts) != 3 || !strings.HasPrefix(did, "did:web:") {
		return "", false
	}
	host := parts[2]
	if !strings.HasSuffix(host, ".etzhayyim.com") {
		return "", false
	}
	nanoid := strings.TrimSuffix(host, ".etzhayyim.com")
	if nanoid == "" || strings.Contains(nanoid, ".") {
		return "", false
	}
	return nanoid, true
}

func fetchSource(client *http.Client, target string) (string, hinshitsuSrc) {
	src := hinshitsuSrc{URL: target}
	req, err := http.NewRequest(http.MethodGet, target, nil)
	if err != nil {
		src.Error = err.Error()
		return "", src
	}
	req.Header.Set("Accept", "application/json, text/html;q=0.9, */*;q=0.8")

	resp, err := client.Do(req)
	if err != nil {
		src.Error = err.Error()
		return "", src
	}
	defer resp.Body.Close()

	body, _ := io.ReadAll(io.LimitReader(resp.Body, 64*1024))
	src.StatusCode = resp.StatusCode
	src.ContentType = strings.TrimSpace(resp.Header.Get("Content-Type"))
	src.Snippet = compactSnippet(string(body), 900)
	if resp.StatusCode >= 400 {
		src.Error = fmt.Sprintf("HTTP %d", resp.StatusCode)
	}
	return string(body), src
}

func buildHinshitsuPrompt(did, didDocBody, profileBody string, sources map[string]hinshitsuSrc) string {
	var b strings.Builder
	now := time.Now().UTC().Format(time.RFC3339)
	b.WriteString("以下のDIDプロフィール情報の品質を評価し、改善案を提示してください。\\n")
	b.WriteString("対象DID: " + did + "\\n\\n")
	b.WriteString("評価基準日(UTC): " + now + "\\n")
	b.WriteString("注意: 評価基準日と同日(または過去)の日時は『未来日付』として減点しないこと。\\n\\n")
	b.WriteString("評価観点(12点満点):\\n")
	b.WriteString("- 真正性(0-2)\\n- 出典性(0-2)\\n- 検証可能性(0-2)\\n- 整合性(0-2)\\n- 鮮度(0-2)\\n- 透明性(0-2)\\n\\n")
	b.WriteString("出力要件:\\n")
	b.WriteString("1) 総合スコア(0-12)と判定ランク(高品質/要注意/低品質)\\n")
	b.WriteString("2) 観点ごとのスコアと根拠(各1-2行)\\n")
	b.WriteString("3) 優先度付き改善案(上位5件、実行手順付き)\\n")
	b.WriteString("4) 直ちに追加取得すべき不足情報\\n")
	b.WriteString("5) 推測は『推測』と明記\\n\\n")

	b.WriteString("観測ソース一覧:\\n")
	for key, src := range sources {
		fmt.Fprintf(&b, "- %s: status=%d url=%s", key, src.StatusCode, src.URL)
		if src.Error != "" {
			fmt.Fprintf(&b, " error=%s", src.Error)
		}
		b.WriteString("\\n")
	}
	b.WriteString("\\n")

	b.WriteString("DID Document 抜粋:\\n")
	if strings.TrimSpace(didDocBody) == "" {
		b.WriteString("(取得できず)\\n\\n")
	} else {
		b.WriteString(compactSnippet(didDocBody, 4000) + "\\n\\n")
	}

	b.WriteString("ATProto Profile 抜粋:\\n")
	if strings.TrimSpace(profileBody) == "" {
		b.WriteString("(取得できず)\\n")
	} else {
		b.WriteString(compactSnippet(profileBody, 3000) + "\\n")
	}

	return b.String()
}

func askLMStudioForHinshitsu(client *http.Client, apiBase, apiKey, model, prompt string) (string, error) {
	return askLMStudioChat(client, apiBase, apiKey, model, "あなたは情報品質監査官です。根拠ベースで簡潔に評価し、実行可能な改善提案を出してください。", prompt)
}

func askLMStudioForHinshitsuKojo(client *http.Client, apiBase, apiKey, model, prompt string) (string, error) {
	return askLMStudioChat(client, apiBase, apiKey, model, "あなたは情報品質改善コンサルタントです。実行順・担当・完了条件が明確な改善計画を作成してください。", prompt)
}

func askLMStudioChat(client *http.Client, apiBase, apiKey, model, systemPrompt, prompt string) (string, error) {
	requestBody := chatCompletionsRequest{
		Model: model,
		Messages: []message{
			{Role: "system", Content: systemPrompt},
			{Role: "user", Content: prompt},
		},
		Temperature: 0.2,
	}
	payload, err := json.Marshal(requestBody)
	if err != nil {
		return "", fmt.Errorf("marshal chat request: %w", err)
	}

	var lastErr error
	for _, targetURL := range hinshitsuChatCompletionEndpoints(apiBase) {
		req, err := http.NewRequest(http.MethodPost, targetURL, strings.NewReader(string(payload)))
		if err != nil {
			lastErr = fmt.Errorf("build LLM request: %w", err)
			continue
		}
		req.Header.Set("Content-Type", "application/json")
		if strings.TrimSpace(apiKey) != "" {
			req.Header.Set("Authorization", "Bearer "+strings.TrimSpace(apiKey))
		}

		resp, err := client.Do(req)
		if err != nil {
			lastErr = fmt.Errorf("LLM request failed: %w", err)
			continue
		}
		respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 2*1024*1024))
		resp.Body.Close()

		// Workers AI/OpenAI gateway deployments may expose only one path family.
		// Keep trying candidate paths on 404.
		if resp.StatusCode == http.StatusNotFound {
			lastErr = fmt.Errorf("LLM API returned HTTP %d at %s: %s", resp.StatusCode, targetURL, compactSnippet(string(respBody), 500))
			continue
		}
		if resp.StatusCode < 200 || resp.StatusCode >= 300 {
			return "", fmt.Errorf("LLM API returned HTTP %d at %s: %s", resp.StatusCode, targetURL, compactSnippet(string(respBody), 500))
		}

		var decoded chatCompletionsResponse
		if err := json.Unmarshal(respBody, &decoded); err != nil {
			return "", fmt.Errorf("parse LLM response: %w", err)
		}
		if err := ensureRequestedHinshitsuModelUsed(model, decoded.Model); err != nil {
			return "", err
		}
		if len(decoded.Choices) == 0 {
			return "", fmt.Errorf("LLM response has no choices")
		}
		content := strings.TrimSpace(decoded.Choices[0].Message.Content)
		if content == "" {
			return "", fmt.Errorf("LLM response content is empty")
		}
		return content, nil
	}
	if lastErr != nil {
		return "", lastErr
	}
	return "", fmt.Errorf("LLM request failed: no usable endpoint")
}

func hinshitsuChatCompletionEndpoints(apiBase string) []string {
	base := normalizeAPIBase(apiBase)
	trimV1 := strings.TrimSuffix(base, "/v1")
	trimOpenAIV1 := strings.TrimSuffix(base, "/api/openai/v1")
	trimAIV1 := strings.TrimSuffix(base, "/ai/v1")
	return uniqueStrings(
		base+"/xrpc/ai.gftd.apps.llm.chatCompletions",
		base+"/chat/completions",
		trimV1+"/v1/chat/completions",
		trimOpenAIV1+"/api/openai/v1/chat/completions",
		trimAIV1+"/ai/v1/chat/completions",
	)
}

func uniqueStrings(values ...string) []string {
	seen := map[string]bool{}
	out := make([]string, 0, len(values))
	for _, v := range values {
		v = strings.TrimSpace(v)
		if v == "" || seen[v] {
			continue
		}
		seen[v] = true
		out = append(out, v)
	}
	return out
}

func detectLMStudioModelWithFallback(apiBase, apiKey string, timeout time.Duration) (string, error) {
	client := &http.Client{Timeout: timeout}
	var lastErr error
	for _, targetURL := range hinshitsuModelsEndpoints(apiBase) {
		method := http.MethodGet
		var requestBody io.Reader
		if strings.Contains(targetURL, "/xrpc/") {
			method = http.MethodPost
			requestBody = strings.NewReader("{}")
		}
		req, err := http.NewRequest(method, targetURL, requestBody)
		if err != nil {
			lastErr = err
			continue
		}
		if method == http.MethodPost {
			req.Header.Set("Content-Type", "application/json")
		}
		if strings.TrimSpace(apiKey) != "" {
			req.Header.Set("Authorization", "Bearer "+strings.TrimSpace(apiKey))
		}
		resp, err := client.Do(req)
		if err != nil {
			lastErr = err
			continue
		}
		if resp.StatusCode == http.StatusNotFound || resp.StatusCode == http.StatusMethodNotAllowed {
			resp.Body.Close()
			lastErr = fmt.Errorf("%s %s returned %d", method, targetURL, resp.StatusCode)
			continue
		}
		if resp.StatusCode != http.StatusOK {
			body, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
			resp.Body.Close()
			return "", fmt.Errorf("%s %s returned %d: %s", method, targetURL, resp.StatusCode, compactSnippet(string(body), 200))
		}
		respBody, err := io.ReadAll(io.LimitReader(resp.Body, 2*1024*1024))
		if err != nil {
			resp.Body.Close()
			return "", err
		}
		resp.Body.Close()

		ids, err := extractModelIDsFromModelsResponse(respBody)
		if err != nil {
			return "", fmt.Errorf("parse models response from %s: %w", targetURL, err)
		}
		if len(ids) == 0 {
			lastErr = fmt.Errorf("no models in response from %s", targetURL)
			continue
		}
		return pickPreferredHinshitsuModel(ids), nil
	}
	if lastErr != nil {
		return "", lastErr
	}
	return "", fmt.Errorf("no reachable models endpoint")
}

func hinshitsuModelsEndpoints(apiBase string) []string {
	base := normalizeAPIBase(apiBase)
	trimV1 := strings.TrimSuffix(base, "/v1")
	trimOpenAIV1 := strings.TrimSuffix(base, "/api/openai/v1")
	trimAIV1 := strings.TrimSuffix(base, "/ai/v1")
	return uniqueStrings(
		base+"/xrpc/ai.gftd.apps.llm.listModels",
		base+"/models",
		trimV1+"/v1/models",
		trimOpenAIV1+"/api/openai/v1/models",
		trimAIV1+"/ai/v1/models",
	)
}

type lmStudioModelsResponse struct {
	Data []struct {
		ID string `json:"id"`
	} `json:"data"`
}

func extractModelIDsFromModelsResponse(body []byte) ([]string, error) {
	// OpenAI-compatible shape: {"data":[{"id":"..."}]}
	var openaiShape modelsAPIResponse
	if err := json.Unmarshal(body, &openaiShape); err == nil && len(openaiShape.Data) > 0 {
		ids := make([]string, 0, len(openaiShape.Data))
		for _, item := range openaiShape.Data {
			id := strings.TrimSpace(item.ID)
			if id != "" {
				ids = append(ids, id)
			}
		}
		if len(ids) > 0 {
			return ids, nil
		}
	}

	// llm.etzhayyim.com XRPC shape: {"models":[{"id":"..."}]}
	var xrpcShape struct {
		Models []struct {
			ID string `json:"id"`
		} `json:"models"`
	}
	if err := json.Unmarshal(body, &xrpcShape); err == nil && len(xrpcShape.Models) > 0 {
		ids := make([]string, 0, len(xrpcShape.Models))
		for _, item := range xrpcShape.Models {
			id := strings.TrimSpace(item.ID)
			if id != "" {
				ids = append(ids, id)
			}
		}
		if len(ids) > 0 {
			return ids, nil
		}
	}

	// Fallback: permissive generic extraction.
	var generic map[string]any
	if err := json.Unmarshal(body, &generic); err != nil {
		return nil, err
	}
	ids := make([]string, 0, 8)
	collect := func(items any) {
		arr, ok := items.([]any)
		if !ok {
			return
		}
		for _, it := range arr {
			obj, ok := it.(map[string]any)
			if !ok {
				continue
			}
			if id, ok := obj["id"].(string); ok {
				id = strings.TrimSpace(id)
				if id != "" {
					ids = append(ids, id)
				}
			}
		}
	}
	collect(generic["data"])
	collect(generic["models"])
	if len(ids) == 0 {
		return nil, fmt.Errorf("no model ids found")
	}
	return uniqueStrings(ids...), nil
}

func pickPreferredHinshitsuModel(ids []string) string {
	if len(ids) == 0 {
		return ""
	}
	preferred := []string{
		"qwen3-30b",
		"qwen-3-30b",
		"qwen3.5-30b",
	}
	for _, want := range preferred {
		for _, id := range ids {
			if strings.Contains(strings.ToLower(id), want) {
				return id
			}
		}
	}
	return pickPreferredLMStudioModel(ids)
}

func ensureRequestedHinshitsuModelUsed(requestedModel, actualModel string) error {
	req := strings.ToLower(strings.TrimSpace(requestedModel))
	if req == "" {
		return nil
	}
	if !strings.Contains(req, "qwen3.5-4b") && !strings.Contains(req, "qwen3.5-9b") {
		return nil
	}
	act := strings.ToLower(strings.TrimSpace(actualModel))
	if strings.Contains(act, "qwen3.5-4b") || strings.Contains(act, "qwen3.5-9b") {
		return nil
	}
	return fmt.Errorf("requested model %q, but backend used %q (qwen3.5-4b/9b not active on llm.etzhayyim.com)", requestedModel, actualModel)
}

func buildHinshitsuKojoPrompt(did, didDocBody, profileBody string, sources map[string]hinshitsuSrc) string {
	var b strings.Builder
	now := time.Now().UTC().Format(time.RFC3339)
	b.WriteString("以下のDIDプロフィール情報の品質を実務的に改善するための『工場ライン型の改善計画』を作成してください。\n")
	b.WriteString("対象DID: " + did + "\n\n")
	b.WriteString("評価基準日(UTC): " + now + "\n")
	b.WriteString("注意: 評価基準日と同日(または過去)の日時は『未来日付』として扱わないこと。\n\n")
	b.WriteString("要件:\n")
	b.WriteString("- 2週間以内で完了できる計画\n")
	b.WriteString("- 今日着手する順に並べる\n")
	b.WriteString("- 各タスクは: 優先度(P0/P1/P2), 目的, 実行手順, 完了条件, 想定リスク\n")
	b.WriteString("- まずは『真正性』『検証可能性』を最優先\n")
	b.WriteString("- 推測は『推測』と明記\n\n")

	b.WriteString("観測ソース一覧:\n")
	for key, src := range sources {
		fmt.Fprintf(&b, "- %s: status=%d url=%s", key, src.StatusCode, src.URL)
		if src.Error != "" {
			fmt.Fprintf(&b, " error=%s", src.Error)
		}
		b.WriteString("\n")
	}
	b.WriteString("\n")

	b.WriteString("DID Document 抜粋:\n")
	if strings.TrimSpace(didDocBody) == "" {
		b.WriteString("(取得できず)\n\n")
	} else {
		b.WriteString(compactSnippet(didDocBody, 4000) + "\n\n")
	}
	b.WriteString("ATProto Profile 抜粋:\n")
	if strings.TrimSpace(profileBody) == "" {
		b.WriteString("(取得できず)\n")
	} else {
		b.WriteString(compactSnippet(profileBody, 3000) + "\n")
	}
	return b.String()
}

func didToSlug(did string) string {
	repl := strings.NewReplacer(":", "-", "/", "-", ".", "-")
	s := repl.Replace(strings.TrimSpace(did))
	s = strings.Trim(s, "-")
	if s == "" {
		return "did"
	}
	return s
}

func buildDidDocumentTemplate(did string) map[string]any {
	return map[string]any{
		"@context": []string{
			"https://www.w3.org/ns/did/v1",
		},
		"id": did,
		"verificationMethod": []map[string]any{
			{
				"id":                  did + "#key-1",
				"type":                "JsonWebKey2020",
				"controller":          did,
				"publicKeyJwk":        map[string]any{"kty": "EC", "crv": "P-256", "x": "<x>", "y": "<y>"},
				"x-gftd-replace-note": "Replace publicKeyJwk with actual key material",
			},
		},
		"authentication": []string{
			did + "#key-1",
		},
		"service": []map[string]any{
			{
				"id":              did + "#atproto_pds",
				"type":            "AtprotoPersonalDataServer",
				"serviceEndpoint": hinshitsuDefaultPDSURL,
			},
		},
	}
}

func compactSnippet(s string, max int) string {
	s = strings.TrimSpace(s)
	s = strings.ReplaceAll(s, "\r", "")
	s = strings.ReplaceAll(s, "\n", " ")
	s = strings.Join(strings.Fields(s), " ")
	if max <= 0 || len(s) <= max {
		return s
	}
	if max < 4 {
		return s[:max]
	}
	return s[:max-3] + "..."
}

func minDuration(a, b time.Duration) time.Duration {
	if a < b {
		return a
	}
	return b
}

// ── OpenAI-compatible API helpers (used by hinshitsu and other subcommands) ──

const defaultMurakumoAPIBase = "https://murakumo.etzhayyim.com/v1"

func normalizeAPIBase(base string) string {
	trimmed := strings.TrimSpace(base)
	if trimmed == "" {
		return defaultCodeAPIBase()
	}
	return strings.TrimRight(trimmed, "/")
}

func defaultCodeAPIBase() string {
	if v := strings.TrimSpace(os.Getenv("OPENAI_API_BASE")); v != "" {
		return strings.TrimRight(v, "/")
	}
	return defaultMurakumoAPIBase
}

func defaultCodeAPIKey() string {
	if v := strings.TrimSpace(os.Getenv("OPENAI_API_KEY")); v != "" {
		return v
	}
	return ""
}

type modelsAPIResponse struct {
	Data []struct {
		ID string `json:"id"`
	} `json:"data"`
}

func pickPreferredLMStudioModel(ids []string) string {
	if len(ids) == 0 {
		return ""
	}
	for _, id := range ids {
		lower := strings.ToLower(id)
		if strings.Contains(lower, "embed") || strings.Contains(lower, "embedding") || strings.Contains(lower, "rerank") {
			continue
		}
		return id
	}
	return ids[0]
}
