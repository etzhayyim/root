package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
	"text/tabwriter"
	"time"
)

// appCoverageReport holds per-app domain knowledge coverage evaluation.
type appCoverageReport struct {
	Nanoid        string                 `json:"nanoid"`
	Name          string                 `json:"name"`
	DID           string                 `json:"did"`
	DomainScore   int                    `json:"domain_score"`
	DomainGrade   string                 `json:"domain_grade"`
	LiveRecords   int                    `json:"live_records"`
	LiveDIDs      int                    `json:"live_dids"`
	LiveCases     int                    `json:"live_cases"`
	XRPCCoverage  map[string]interface{} `json:"xrpc_coverage,omitempty"`
	LiveByDID     []didCoverageInfo      `json:"live_by_did,omitempty"`
	KnowledgeAxes []knowledgeAxis        `json:"knowledge_axes"`
	Gaps          []string               `json:"gaps,omitempty"`
	OverallScore  float64                `json:"overall_score"`
	OverallGrade  string                 `json:"overall_grade"`
	Error         string                 `json:"error,omitempty"`
}

type didCoverageInfo struct {
	ActorDID string `json:"actor_did"`
	Records  int    `json:"records"`
}

// knowledgeAxis represents one evaluation axis for domain knowledge.
type knowledgeAxis struct {
	Name   string  `json:"name"`
	Score  float64 `json:"score"`
	Max    float64 `json:"max"`
	Detail string  `json:"detail"`
}

// runAppsCoverage evaluates domain knowledge coverage for one or all apps.
func runAppsCoverage(args []string) error {
	fs := flag.NewFlagSet("apps coverage", flag.ExitOnError)
	dir := fs.String("dir", "projects", "parent directory to scan")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	nanoid := fs.String("nanoid", "", "single app nanoid (or positional arg)")
	jsonOut := fs.Bool("json", false, "JSON output")
	timeout := fs.Int("timeout", 15, "HTTP timeout seconds")
	fs.Parse(args)

	// Accept positional nanoid: gftd apps <nanoid> coverage
	if *nanoid == "" && fs.NArg() > 0 {
		*nanoid = fs.Arg(0)
	}

	if *nanoid == "" {
		return fmt.Errorf("nanoid required: gftd apps coverage -nanoid <id>  or  gftd apps <id> coverage")
	}

	httpClient := &http.Client{Timeout: time.Duration(*timeout) * time.Second}
	token := resolveGFTDToken()

	// 1. Discover app
	apps, err := discoverApps(*dir, *nanoid, "")
	if err != nil {
		return err
	}
	if len(apps) == 0 {
		return fmt.Errorf("app not found: %s", *nanoid)
	}
	app := apps[0]
	did := strings.TrimSpace(app.DID)
	if did == "" || !strings.HasPrefix(did, "did:") {
		did = fmt.Sprintf("did:web:%s.etzhayyim.com", app.Nanoid)
	}
	repoDIDs := repoDIDCandidates(did, app.Nanoid)

	fmt.Fprintf(os.Stderr, "==> Evaluating domain coverage for %s (%s)...\n\n", app.Name, app.Nanoid)

	report := appCoverageReport{
		Nanoid: app.Nanoid,
		Name:   app.Name,
		DID:    did,
	}

	// 2. Static analysis: domain coverage score from app.ts AST
	wsRoot, _ := findGitRoot(".")
	domainApps := collectAndScoreDomainApps(wsRoot)
	for _, da := range domainApps {
		if da.Nanoid == app.Nanoid {
			report.DomainScore = da.DomainScore
			report.DomainGrade = da.Grade
			report.Gaps = da.Missing

			report.KnowledgeAxes = append(report.KnowledgeAxes,
				knowledgeAxis{Name: "graph_labels", Score: float64(min(len(da.SqlLabels)*10, 30)), Max: 30, Detail: strings.Join(da.SqlLabels, ", ")},
				knowledgeAxis{Name: "collection_kinds", Score: float64(min(len(da.CollectionKinds)*10, 20)), Max: 20, Detail: strings.Join(da.CollectionKinds, ", ")},
				knowledgeAxis{Name: "custom_commands", Score: float64(min(len(da.CustomCommands)*5, 15)), Max: 15, Detail: fmt.Sprintf("%d custom + %d template", len(da.CustomCommands), da.TemplateCmds)},
				knowledgeAxis{Name: "business_rules", Score: float64(min(da.BusinessRules, 15)), Max: 15, Detail: fmt.Sprintf("%d rules", da.BusinessRules)},
				knowledgeAxis{Name: "data_structures", Score: float64(min(da.Lines/100, 10)), Max: 10, Detail: fmt.Sprintf("%d lines", da.Lines)},
				knowledgeAxis{Name: "data_sources", Score: float64(min(da.DataSources*3, 5)), Max: 5, Detail: fmt.Sprintf("%d sources", da.DataSources)},
				knowledgeAxis{Name: "did_paths", Score: float64(min(len(da.DIDPaths)*3, 5)), Max: 5, Detail: strings.Join(da.DIDPaths, ", ")},
			)
			break
		}
	}

	// 3. PDS live data: listRecords-based counts (repo + sub-DID aware)
	appCollections := []string{}
	subPaths := []string{}
	if appTsPath := findAppTs(app.Dir); appTsPath != "" {
		if content, err := os.ReadFile(appTsPath); err == nil {
			src := string(content)
			appCollections = extractCollectionLiterals(src, collectionNamespaceCandidates(app))
			for _, sd := range extractSubDIDDeclarations(src) {
				if strings.TrimSpace(sd.Path) != "" {
					subPaths = append(subPaths, sd.Path)
				}
			}
		}
	}
	if len(appCollections) == 0 {
		appCollections = queryAppCollections(httpClient, *pdsURL, token, repoDIDs)
	}
	repoCandidates := append([]string{}, repoDIDs...)
	for _, p := range subPaths {
		repoCandidates = append(repoCandidates, derivePathDidAliases(repoDIDs, p)...)
	}
	// dedupe repo list
	repoSeen := map[string]bool{}
	uniqueRepos := make([]string, 0, len(repoCandidates))
	for _, rdid := range repoCandidates {
		rdid = strings.TrimSpace(rdid)
		if rdid == "" || repoSeen[rdid] {
			continue
		}
		repoSeen[rdid] = true
		uniqueRepos = append(uniqueRepos, rdid)
	}
	recordSeen := map[string]bool{}
	didCounts := map[string]int{}
	for _, repoDID := range uniqueRepos {
		for _, col := range appCollections {
			entries := listCollectionRecordEntriesForRepo(httpClient, *pdsURL, token, repoDID, col, 250)
			for _, rec := range entries {
				key := rec.URI
				if key == "" {
					key = fmt.Sprintf("%s|%s|%s", repoDID, col, strVal(rec.Value["id"]))
				}
				if recordSeen[key] {
					continue
				}
				recordSeen[key] = true
				report.LiveRecords++
				actor := strings.TrimSpace(strVal(rec.Value["actorDid"]))
				if actor == "" {
					if repoFromURI := atURIRepo(rec.URI); repoFromURI != "" {
						actor = repoFromURI
					} else {
						actor = repoDID
					}
				}
				didCounts[actor]++
			}
		}
	}
	for actor, cnt := range didCounts {
		report.LiveByDID = append(report.LiveByDID, didCoverageInfo{ActorDID: actor, Records: cnt})
	}
	report.LiveDIDs = len(report.LiveByDID)

	// 4. XRPC coverageStats (app self-evaluation)
	xrpcAppName := inferCoverageAppName(app, appCollections)
	xrpcCoverage := queryXRPCCoverageStats(httpClient, app.Nanoid, xrpcAppName, token)
	if xrpcCoverage != nil {
		report.XRPCCoverage = xrpcCoverage
	}

	// 5. World coverage match
	for _, wd := range worldDomains {
		appHost := strings.TrimSuffix(wd.App, ".etzhayyim.com")
		if appHost == app.Nanoid || strings.Contains(wd.App, app.Name+".etzhayyim.com") {
			report.LiveCases = report.LiveRecords
			break
		}
	}

	// 6. Overall score: 40% domain + 25% live data + 20% XRPC self-eval + 15% DID utilization
	domainPct := float64(report.DomainScore)
	livePct := tierScore(report.LiveRecords, 1, 10, 100)
	didPct := tierScore(report.LiveDIDs, 1, 3, 10)
	xrpcPct := 0.0
	if report.XRPCCoverage != nil {
		if total, ok := report.XRPCCoverage["totalJurisdictions"]; ok {
			if t, ok := total.(float64); ok && t > 0 {
				xrpcPct = 100
			}
		} else {
			xrpcPct = 50 // has coverageStats but no jurisdiction count
		}
	}

	report.OverallScore = 0.40*domainPct + 0.25*livePct + 0.20*xrpcPct + 0.15*didPct
	report.OverallGrade = coverageGrade(report.OverallScore)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printAppCoverageReport(report)
	return nil
}

// queryXRPCCoverageStats calls the app's XRPC coverageStats endpoint.
func queryXRPCCoverageStats(client *http.Client, nanoid, appName, token string) map[string]interface{} {
	if strings.TrimSpace(appName) == "" {
		appName = nanoid
	}
	url := fmt.Sprintf("https://%s.etzhayyim.com/xrpc/ai.gftd.apps.%s.coverageStats", nanoid, appName)
	req, err := http.NewRequest("POST", url, strings.NewReader("{}"))
	if err != nil {
		return nil
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return nil
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil
	}

	body, _ := io.ReadAll(resp.Body)
	var result map[string]interface{}
	if json.Unmarshal(body, &result) != nil {
		return nil
	}
	return result
}

func inferCoverageAppName(app discoveredApp, collections []string) string {
	if inferred := inferAppNameFromCollections(collections); inferred != "" {
		return inferred
	}
	// Extract from dir name: ai-gftd-wasm-{name}-{nanoid} → {name}
	dir := app.Dir
	parts := strings.Split(dir, "/")
	for _, p := range parts {
		if strings.HasPrefix(p, "ai-gftd-wasm-") {
			trimmed := strings.TrimPrefix(p, "ai-gftd-wasm-")
			// Remove trailing nanoid: "hanrei-jp-h4nr31jp" → "hanrei"
			if idx := strings.LastIndex(trimmed, "-"); idx > 0 {
				// Check if the suffix after last dash looks like a nanoid
				suffix := trimmed[idx+1:]
				if len(suffix) == 8 && suffix == app.Nanoid {
					return strings.ReplaceAll(trimmed[:idx], "-", "")
				}
			}
			// Fallback: remove the last segment as nanoid
			segs := strings.Split(trimmed, "-")
			if len(segs) > 1 {
				return strings.Join(segs[:len(segs)-1], "")
			}
			return trimmed
		}
	}
	return app.Nanoid
}

func inferAppNameFromCollections(cols []string) string {
	for _, col := range cols {
		parts := strings.Split(strings.TrimSpace(col), ".")
		// ai.gftd.apps.{app}.{collection}
		if len(parts) >= 5 && parts[0] == "ai" && parts[1] == "gftd" && parts[2] == "apps" {
			name := strings.TrimSpace(parts[3])
			if name != "" {
				return name
			}
		}
	}
	return ""
}

func coverageGrade(score float64) string {
	switch {
	case score >= 80:
		return "S"
	case score >= 60:
		return "A"
	case score >= 40:
		return "B"
	case score >= 20:
		return "C"
	default:
		return "D"
	}
}

func printAppCoverageReport(r appCoverageReport) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

	fmt.Fprintf(w, "App Coverage Report: %s (%s)\n", r.Name, r.Nanoid)
	fmt.Fprintf(w, "DID: %s\n\n", r.DID)

	// Overall
	fmt.Fprintf(w, "Overall\t%s\t%.1f / 100\n", r.OverallGrade, r.OverallScore)
	fmt.Fprintf(w, "Domain Score\t%s\t%d / 100\n", r.DomainGrade, r.DomainScore)
	fmt.Fprintf(w, "Live Records\t\t%d\n", r.LiveRecords)
	fmt.Fprintf(w, "Live Sub-DIDs\t\t%d\n", r.LiveDIDs)
	fmt.Fprintln(w)

	if len(r.LiveByDID) > 0 {
		fmt.Fprintln(w, "Live by DID:")
		fmt.Fprintln(w, "  Actor DID\tRecords")
		fmt.Fprintln(w, "  ---------\t-------")
		for _, d := range r.LiveByDID {
			fmt.Fprintf(w, "  %s\t%d\n", truncateStr(d.ActorDID, 64), d.Records)
		}
		fmt.Fprintln(w)
	}

	// Knowledge axes
	fmt.Fprintln(w, "Knowledge Axis\tScore\tMax\tDetail")
	fmt.Fprintln(w, "--------------\t-----\t---\t------")
	for _, ax := range r.KnowledgeAxes {
		fmt.Fprintf(w, "%s\t%.0f\t%.0f\t%s\n", ax.Name, ax.Score, ax.Max, ax.Detail)
	}
	fmt.Fprintln(w)

	// XRPC self-evaluation
	if r.XRPCCoverage != nil {
		fmt.Fprintln(w, "App Self-Evaluation (XRPC coverageStats):")
		for k, v := range r.XRPCCoverage {
			fmt.Fprintf(w, "  %s\t%v\n", k, v)
		}
		fmt.Fprintln(w)
	}

	// Gaps
	if len(r.Gaps) > 0 {
		fmt.Fprintln(w, "Gaps:")
		for _, g := range r.Gaps {
			fmt.Fprintf(w, "  - %s\n", g)
		}
		fmt.Fprintln(w)
	}

	w.Flush()
}

func atURIRepo(uri string) string {
	s := strings.TrimSpace(uri)
	if !strings.HasPrefix(s, "at://") {
		return ""
	}
	rest := strings.TrimPrefix(s, "at://")
	if i := strings.Index(rest, "/"); i >= 0 {
		return rest[:i]
	}
	return ""
}
