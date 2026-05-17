package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	neturl "net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"sync"
	"text/tabwriter"
	"time"
)

// shinkaStatus holds the shinka/kyumei-koji health for a single app.
type shinkaStatus struct {
	Nanoid      string
	Name        string
	DID         string
	HasJoucho   bool   // resolveHeartbeatCadence in app.ts
	HasInbox    bool   // createInboxBuffer in app.ts
	HasCadence  bool   // createCadenceState in app.ts
	HasOldTimer bool   // heartbeatCount % N (violation)
	HeartbeatOK bool   // /_heartbeat returns ok:true
	HBActions   string // actions summary from last heartbeat
	HBMood      string // joucho mood from heartbeat response
	HasDrill    bool   // shouldDrill implementation
	HasValidate bool   // shouldValidate implementation
	HasAnalyze  bool   // shouldAnalyze implementation
	HasEngage   bool   // shouldEngage implementation
	ShinkaScore int
	DomainScore int
	DomainGrade string
	DomainGaps  []string
	KGNodes     int
	KGLabels    int
	KGScore     int
	HyokaScore  int
	HyokaGrade  string
	SubDIDFresh []subDIDFreshness
	StaleSubDID int
	Error       string
}

type subDIDFreshness struct {
	Path        string `json:"path"`
	Collection  string `json:"collection,omitempty"`
	LastUpdated string `json:"last_updated,omitempty"`
	AgeHours    int    `json:"age_hours,omitempty"`
	Stale       bool   `json:"stale,omitempty"`
}

var (
	reShinkaCollectionFull = regexp.MustCompile(`["']((?:ai\.gftd\.apps|app\.bsky)\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_.-]+)["']`)
	reShinkaPathDecl       = regexp.MustCompile(`path:\s*"([^"]+)"`)
)

// hyokaFlatRow is the per-actor row written to the hyoka Parquet table.
type hyokaFlatRow struct {
	SnapshotAt  string `json:"snapshot_at"`
	Nanoid      string `json:"nanoid"`
	Name        string `json:"name"`
	HasJoucho   bool   `json:"has_joucho"`
	HasInbox    bool   `json:"has_inbox"`
	HasCadence  bool   `json:"has_cadence"`
	HasDrill    bool   `json:"has_drill"`
	HasValidate bool   `json:"has_validate"`
	HasAnalyze  bool   `json:"has_analyze"`
	HasEngage   bool   `json:"has_engage"`
	ShinkaScore int    `json:"shinka_score"`
	DomainScore int    `json:"domain_score"`
	DomainGrade string `json:"domain_grade"`
	KGNodes     int    `json:"kg_nodes"`
	KGLabels    int    `json:"kg_labels"`
	KGScore     int    `json:"kg_score"`
	HyokaScore  int    `json:"hyoka_score"`
	HyokaGrade  string `json:"hyoka_grade"`
	StaleSubDID int    `json:"stale_sub_did"`
}

// runMonitorShinka implements `gftd monitor shinka` — shinka/kyumei-koji health analysis.
func runMonitorShinka(args []string) error {
	fs := flag.NewFlagSet("monitor shinka", flag.ExitOnError)
	dir := fs.String("dir", "60-apps", "parent directory to scan")
	filter := fs.String("filter", "", "glob pattern for app names")
	nanoid := fs.String("nanoid", "", "check a single app by nanoid")
	concurrency := fs.Int("concurrency", 16, "parallel workers")
	timeout := fs.Int("timeout", 10, "HTTP timeout in seconds")
	live := fs.Bool("live", false, "also POST /_heartbeat to test live cadence")
	hyoka := fs.Bool("hyoka", false, "include domain coverage + actor knowledge graph metrics (requires PDS access)")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL for hyoka mode")
	freshnessHours := fs.Int("freshness-hours", 24, "sub-DID freshness warning threshold (hours)")
	jsonOut := fs.Bool("json", false, "JSON output")
	storeOut := fs.Bool("store", false, "store results to 80-data/hyoka/ Parquet (requires duckdb)")
	gate := fs.Bool("gate", false, "fail if hyoka regresses beyond thresholds (use with --store)")
	maxAvgDrop := fs.Float64("max-avg-drop", 3.0, "max allowed avg hyoka_score drop (gate)")
	maxTop10Drop := fs.Float64("max-top10-drop", 5.0, "max allowed top-10 avg drop (gate)")
	maxLowIncrease := fs.Int("max-low-increase", 5, "max allowed increase in low-score (<60) actors (gate)")
	fs.Parse(args)

	httpClient := &http.Client{Timeout: time.Duration(*timeout) * time.Second}
	token := resolveGFTDToken()

	domainByNanoid := map[string]domainAppReport{}
	wsRoot, wsErr := findGitRoot(".")
	if *hyoka && wsErr == nil {
		for _, d := range collectAndScoreDomainApps(wsRoot) {
			domainByNanoid[d.Nanoid] = d
		}
	}

	apps, err := discoverApps(*dir, *nanoid, *filter)
	if err != nil {
		return err
	}
	if len(apps) == 0 {
		fmt.Fprintln(os.Stderr, "No apps found")
		return nil
	}

	fmt.Fprintf(os.Stderr, "==> Analyzing shinka/kyumei-koji for %d apps...\n\n", len(apps))

	results := make([]shinkaStatus, len(apps))
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, app := range apps {
		wg.Add(1)
		go func(idx int, a discoveredApp) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			results[idx] = analyzeShinkaApp(httpClient, a, *live, *hyoka, *pdsURL, token, domainByNanoid, *freshnessHours)
		}(i, app)
	}
	wg.Wait()

	sort.Slice(results, func(i, j int) bool {
		si := shinkaScore(results[i])
		sj := shinkaScore(results[j])
		if si != sj {
			return si > sj
		}
		return results[i].Name < results[j].Name
	})

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(results)
	}

	if !*jsonOut {
		printShinkaTable(results)
	}

	if *storeOut && wsErr == nil {
		if err := storeHyokaResults(wsRoot, results, *gate, *maxAvgDrop, *maxTop10Drop, *maxLowIncrease); err != nil {
			return err
		}
	}
	return nil
}

// storeHyokaResults stores per-actor hyoka results to Parquet and optionally gates on regression.
func storeHyokaResults(wsRoot string, results []shinkaStatus, gate bool, maxAvgDrop, maxTop10Drop float64, maxLowIncrease int) error {
	now := time.Now().UTC().Format(time.RFC3339)

	rows := make([]hyokaFlatRow, 0, len(results))
	for _, r := range results {
		rows = append(rows, hyokaFlatRow{
			SnapshotAt:  now,
			Nanoid:      r.Nanoid,
			Name:        r.Name,
			HasJoucho:   r.HasJoucho,
			HasInbox:    r.HasInbox,
			HasCadence:  r.HasCadence,
			HasDrill:    r.HasDrill,
			HasValidate: r.HasValidate,
			HasAnalyze:  r.HasAnalyze,
			HasEngage:   r.HasEngage,
			ShinkaScore: r.ShinkaScore,
			DomainScore: r.DomainScore,
			DomainGrade: r.DomainGrade,
			KGNodes:     r.KGNodes,
			KGLabels:    r.KGLabels,
			KGScore:     r.KGScore,
			HyokaScore:  r.HyokaScore,
			HyokaGrade:  r.HyokaGrade,
			StaleSubDID: r.StaleSubDID,
		})
	}

	// Compute current stats in memory.
	var sumScore float64
	lowCount := 0
	sorted := make([]int, len(results))
	for i, r := range results {
		sumScore += float64(r.HyokaScore)
		if r.HyokaScore < 60 {
			lowCount++
		}
		sorted[i] = r.HyokaScore
	}
	sort.Sort(sort.Reverse(sort.IntSlice(sorted)))
	avgScore := 0.0
	if len(results) > 0 {
		avgScore = sumScore / float64(len(results))
	}
	top10Sum := 0.0
	top10N := 0
	for i, s := range sorted {
		if i >= 10 {
			break
		}
		top10Sum += float64(s)
		top10N++
	}
	top10Avg := 0.0
	if top10N > 0 {
		top10Avg = top10Sum / float64(top10N)
	}

	summary := fmt.Sprintf("%s actors=%d avg=%.2f top10=%.2f low=%d", now[:10], len(results), avgScore, top10Avg, lowCount)
	parquetFile, err := storeParquet(wsRoot, "hyoka", summary, rows)
	if err != nil {
		return fmt.Errorf("hyoka store: %w", err)
	}
	fmt.Fprintf(os.Stderr, "hyoka stored: %s\n", parquetFile)
	fmt.Fprintf(os.Stderr, "hyoka summary: avg=%.2f top10=%.2f low=%d\n", avgScore, top10Avg, lowCount)

	if !gate {
		return nil
	}

	// Gate: query previous snapshot stats via DuckDB.
	prevSQL := `
SELECT round(avg(hyoka_score),2) AS avg_score,
  round(avg(CASE WHEN rn <= 10 THEN hyoka_score END),2) AS top10_avg,
  count(CASE WHEN hyoka_score < 60 THEN 1 END) AS low_count
FROM (
  SELECT hyoka_score,
    row_number() OVER (ORDER BY hyoka_score DESC) AS rn
  FROM $TABLE
  WHERE snapshot_at = (
    SELECT snapshot_at FROM $TABLE
    GROUP BY snapshot_at ORDER BY snapshot_at DESC LIMIT 1 OFFSET 1
  )
)`
	rows2, err := queryParquetJSON(wsRoot, "hyoka", prevSQL)
	if err != nil || len(rows2) == 0 {
		// No previous snapshot — skip gate.
		fmt.Fprintf(os.Stderr, "hyoka gate: no previous snapshot, skipping regression check\n")
		return nil
	}

	prevAvg, _ := rows2[0]["avg_score"].(float64)
	prevTop10, _ := rows2[0]["top10_avg"].(float64)
	prevLow, _ := rows2[0]["low_count"].(float64)

	var failures []string
	if avgDrop := prevAvg - avgScore; avgDrop > maxAvgDrop {
		failures = append(failures, fmt.Sprintf("avg_hyoka drop %.2f > %.2f (prev=%.2f curr=%.2f)", avgDrop, maxAvgDrop, prevAvg, avgScore))
	}
	if top10Drop := prevTop10 - top10Avg; top10Drop > maxTop10Drop {
		failures = append(failures, fmt.Sprintf("top10_hyoka drop %.2f > %.2f (prev=%.2f curr=%.2f)", top10Drop, maxTop10Drop, prevTop10, top10Avg))
	}
	if lowIncrease := lowCount - int(prevLow); lowIncrease > maxLowIncrease {
		failures = append(failures, fmt.Sprintf("low-score increase %d > %d (prev=%d curr=%d)", lowIncrease, maxLowIncrease, int(prevLow), lowCount))
	}
	if len(failures) > 0 {
		fmt.Fprintln(os.Stderr, "hyoka gate failed:")
		for _, f := range failures {
			fmt.Fprintf(os.Stderr, "  - %s\n", f)
		}
		return fmt.Errorf("hyoka gate: regression detected")
	}
	fmt.Fprintf(os.Stderr, "hyoka gate: ✅ passed\n")
	return nil
}

// analyzeShinkaApp checks a single app's shinka implementation quality.
func analyzeShinkaApp(
	client *http.Client,
	app discoveredApp,
	live bool,
	hyoka bool,
	pdsURL string,
	token string,
	domainByNanoid map[string]domainAppReport,
	freshnessHours int,
) shinkaStatus {
	s := shinkaStatus{
		Nanoid: app.Nanoid,
		Name:   app.Name,
		DID:    fmt.Sprintf("did:web:%s.etzhayyim.com", app.Nanoid),
	}

	// Read app.ts source to check implementation patterns
	appTS := filepath.Join(app.Dir, "src", "app.ts")
	data, err := os.ReadFile(appTS)
	if err != nil {
		s.Error = "no app.ts"
		return s
	}
	src := string(data)

	s.HasJoucho = strings.Contains(src, "resolveHeartbeatCadence")
	s.HasInbox = strings.Contains(src, "createInboxBuffer")
	s.HasCadence = strings.Contains(src, "createCadenceState")
	s.HasOldTimer = strings.Contains(src, "heartbeatCount %") || strings.Contains(src, "heartbeatCount %")
	s.HasDrill = strings.Contains(src, "shouldDrill")
	s.HasValidate = strings.Contains(src, "shouldValidate")
	s.HasAnalyze = strings.Contains(src, "shouldAnalyze")
	s.HasEngage = strings.Contains(src, "shouldEngage")
	s.ShinkaScore = shinkaScore(s)
	if freshnessHours > 0 {
		collections := extractShinkaCollectionLiterals(src, collectionNamespaceCandidates(app))
		paths := extractShinkaSubDIDPaths(src)
		s.SubDIDFresh = probeSubDIDFreshness(client, pdsURL, token, app.Nanoid, paths, collections, freshnessHours)
		for _, f := range s.SubDIDFresh {
			if f.Stale {
				s.StaleSubDID++
			}
		}
	}

	// Live heartbeat test
	if live {
		url := fmt.Sprintf("https://%s.etzhayyim.com/_heartbeat", app.Nanoid)
		req, _ := http.NewRequest("POST", url, nil)
		token := resolveGFTDToken()
		if token != "" {
			req.Header.Set("Authorization", "Bearer "+token)
		}
		resp, err := client.Do(req)
		if err != nil {
			s.Error = "heartbeat unreachable"
		} else {
			defer resp.Body.Close()
			body, _ := io.ReadAll(resp.Body)
			var hb struct {
				OK      bool            `json:"ok"`
				Actions json.RawMessage `json:"actions"`
			}
			if json.Unmarshal(body, &hb) == nil {
				s.HeartbeatOK = hb.OK
				// Try to extract mood from actions
				var actions []map[string]interface{}
				if json.Unmarshal(hb.Actions, &actions) == nil {
					for _, a := range actions {
						if m, ok := a["mood"]; ok {
							s.HBMood = fmt.Sprintf("%v", m)
						}
						if act, ok := a["action"]; ok {
							s.HBActions = fmt.Sprintf("%v", act)
						}
					}
				}
			}
		}
	}

	if hyoka {
		if dr, ok := domainByNanoid[app.Nanoid]; ok {
			s.DomainScore = dr.DomainScore
			s.DomainGrade = dr.Grade
			s.DomainGaps = dr.Missing
		}

		didPrefix := s.DID + ":"
		_ = client
		_ = pdsURL
		_ = token
		// P10v2 has no generic `MATCH (n)` equivalent — per-vertex-table counts
		// would require a UNION across ~180 tables. Approximate via vertex_did
		// for node count; distinct labels count is fixed at 1 for this repo.
		s.KGNodes = rwCountInt(`SELECT COUNT(*)::bigint FROM vertex_did WHERE did = $1 OR did LIKE $2 || '%' OR repo = $1`, s.DID, didPrefix)
		s.KGLabels = 0

		kgNodesScore := int(tierScore(s.KGNodes, 1, 10, 100))
		kgLabelScore := int(tierScore(s.KGLabels, 3, 8, 20))
		s.KGScore = min(100, int(float64(kgNodesScore)*0.7+float64(kgLabelScore)*0.3))
		s.HyokaScore = min(100, int(0.45*float64(s.ShinkaScore)+0.35*float64(s.DomainScore)+0.20*float64(s.KGScore)))
		s.HyokaGrade = coverageGrade(float64(s.HyokaScore))
	}

	return s
}

// shinkaScore returns a 0-100 score for sorting.
func shinkaScore(s shinkaStatus) int {
	score := 0
	if s.HasJoucho {
		score += 30
	}
	if s.HasInbox {
		score += 15
	}
	if s.HasCadence {
		score += 15
	}
	if s.HasDrill {
		score += 10
	}
	if s.HasValidate {
		score += 10
	}
	if s.HasAnalyze {
		score += 10
	}
	if s.HasEngage {
		score += 10
	}
	if s.HasOldTimer {
		score -= 30 // penalty
	}
	if score < 0 {
		score = 0
	}
	return score
}

func printShinkaTable(results []shinkaStatus) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

	joucho := 0
	oldTimer := 0
	drill := 0
	for _, r := range results {
		if r.HasJoucho {
			joucho++
		}
		if r.HasOldTimer {
			oldTimer++
		}
		if r.HasDrill {
			drill++
		}
	}

	fmt.Fprintf(w, "\nShinka/Kyumei-Koji Health (%d apps)\n\n", len(results))
	fmt.Fprintln(w, "Shinka\tHyoka\tDomain\tKG\tNanoid\tName\tJoucho\tInbox\tCadence\tDrill\tValidate\tAnalyze\tEngage\tOldTimer\tStaleSubDID\tMood")
	fmt.Fprintln(w, "------\t-----\t------\t--\t--------\t--------------------\t------\t-----\t-------\t-----\t--------\t-------\t------\t--------\t-----------\t----")

	for _, r := range results {
		fmt.Fprintf(w, "%d\t%s\t%d\t%d\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%s\t%d\t%s\n",
			r.ShinkaScore,
			hyokaCell(r),
			r.DomainScore,
			r.KGScore,
			r.Nanoid,
			truncateStr(r.Name, 20),
			boolMark(r.HasJoucho),
			boolMark(r.HasInbox),
			boolMark(r.HasCadence),
			boolMark(r.HasDrill),
			boolMark(r.HasValidate),
			boolMark(r.HasAnalyze),
			boolMark(r.HasEngage),
			violationMark(r.HasOldTimer),
			r.StaleSubDID,
			r.HBMood,
		)
	}

	fmt.Fprintln(w)
	fmt.Fprintf(w, "Summary:\n")
	fmt.Fprintf(w, "  joucho cadence:  %d/%d (%.0f%%)\n", joucho, len(results), pct(joucho, len(results)))
	fmt.Fprintf(w, "  old timer (!!):  %d/%d (%.0f%% violation)\n", oldTimer, len(results), pct(oldTimer, len(results)))
	fmt.Fprintf(w, "  kyumei-koji:     %d/%d (%.0f%% have shouldDrill)\n", drill, len(results), pct(drill, len(results)))
	w.Flush()
}

func hyokaCell(s shinkaStatus) string {
	if s.HyokaScore == 0 && s.DomainScore == 0 && s.KGScore == 0 {
		return "—"
	}
	if s.HyokaGrade != "" {
		return fmt.Sprintf("%d(%s)", s.HyokaScore, s.HyokaGrade)
	}
	return fmt.Sprintf("%d", s.HyokaScore)
}

func boolMark(b bool) string {
	if b {
		return "✓"
	}
	return "·"
}

func violationMark(b bool) string {
	if b {
		return "!! ✗"
	}
	return "✓"
}

func pct(n, total int) float64 {
	if total == 0 {
		return 0
	}
	return float64(n) / float64(total) * 100
}

func extractShinkaCollectionLiterals(content string, appNSCandidates []string) []string {
	matches := reShinkaCollectionFull.FindAllStringSubmatch(content, -1)
	seen := map[string]bool{}
	out := make([]string, 0, len(matches))
	prefixes := make([]string, 0, len(appNSCandidates))
	for _, ns := range appNSCandidates {
		ns = normalizeDomainLookup(ns)
		if ns == "" {
			continue
		}
		prefixes = append(prefixes, "ai.gftd.apps."+ns+".")
	}
	for _, m := range matches {
		if len(m) < 2 {
			continue
		}
		col := strings.TrimSpace(m[1])
		if col == "" || seen[col] {
			continue
		}
		if len(prefixes) > 0 {
			ok := false
			for _, pfx := range prefixes {
				if strings.HasPrefix(col, pfx) {
					ok = true
					break
				}
			}
			if !ok {
				continue
			}
		}
		seen[col] = true
		out = append(out, col)
	}
	return out
}

func extractShinkaSubDIDPaths(content string) []string {
	matches := reShinkaPathDecl.FindAllStringSubmatch(content, -1)
	seen := map[string]bool{}
	out := make([]string, 0, len(matches))
	for _, m := range matches {
		if len(m) < 2 {
			continue
		}
		p := strings.TrimSpace(m[1])
		if p == "" || seen[p] {
			continue
		}
		seen[p] = true
		out = append(out, p)
	}
	return out
}

func probeSubDIDFreshness(client *http.Client, pdsURL, token, nanoid string, paths, collections []string, thresholdHours int) []subDIDFreshness {
	if len(paths) == 0 || len(collections) == 0 {
		return nil
	}
	now := time.Now().UTC()
	out := make([]subDIDFreshness, 0, len(paths))
	for _, path := range paths {
		subdidPath := strings.ReplaceAll(strings.Trim(path, "/"), "/", ":")
		subdid := fmt.Sprintf("did:web:%s.etzhayyim.com:%s", nanoid, subdidPath)
		var bestTS time.Time
		bestCol := ""
		for _, col := range collections {
			ts := latestRecordTimestamp(client, pdsURL, token, subdid, col)
			if ts.After(bestTS) {
				bestTS = ts
				bestCol = col
			}
		}
		f := subDIDFreshness{Path: path, Collection: bestCol}
		if !bestTS.IsZero() {
			f.LastUpdated = bestTS.Format(time.RFC3339)
			f.AgeHours = int(now.Sub(bestTS).Hours())
			f.Stale = f.AgeHours >= thresholdHours
		} else {
			f.Stale = true
		}
		out = append(out, f)
	}
	return out
}

func latestRecordTimestamp(client *http.Client, pdsURL, token, repo, collection string) time.Time {
	base := strings.TrimRight(pdsURL, "/") + "/xrpc/com.atproto.repo.listRecords"
	q := neturl.Values{}
	q.Set("repo", repo)
	q.Set("collection", collection)
	q.Set("limit", "1")
	req, err := http.NewRequest("GET", base+"?"+q.Encode(), nil)
	if err != nil {
		return time.Time{}
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := client.Do(req)
	if err != nil {
		return time.Time{}
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		return time.Time{}
	}
	var payload struct {
		Records []struct {
			Value map[string]interface{} `json:"value"`
		} `json:"records"`
	}
	body, _ := io.ReadAll(resp.Body)
	if json.Unmarshal(body, &payload) != nil || len(payload.Records) == 0 {
		return time.Time{}
	}
	raw := strVal(payload.Records[0].Value["updatedAt"])
	if raw == "" {
		raw = strVal(payload.Records[0].Value["createdAt"])
	}
	if raw == "" {
		return time.Time{}
	}
	if ts, err := time.Parse(time.RFC3339, raw); err == nil {
		return ts.UTC()
	}
	return time.Time{}
}
