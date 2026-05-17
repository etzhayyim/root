package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"strings"
	"sync"
	"text/tabwriter"
	"time"
)

// jokyoStatus holds per-actor autonomous agent health metrics.
type jokyoStatus struct {
	Nanoid       string `json:"nanoid"`
	Name         string `json:"name"`
	DID          string `json:"did"`
	Posts        int    `json:"posts"`
	PostsWeek    int    `json:"posts_week"`
	Likes        int    `json:"likes"`
	Followers    int    `json:"followers"`
	Convos       int    `json:"convos"`
	DomainRecs   int    `json:"domain_records"`
	KyumeiRecs   int    `json:"kyumei_records"`
	JouchoJoy    int    `json:"joucho_joy"`
	JouchoCal    int    `json:"joucho_calm"`
	JouchoStr    int    `json:"joucho_stress"`
	JouchoGra    int    `json:"joucho_gratitude"`
	JouchoFoc    int    `json:"joucho_focus"`
	KyumeiAt     string `json:"kyumei_last_at"`
	KyumeiAge    int    `json:"kyumei_age_hours"`
	HealthOK     bool   `json:"health_ok"`
	HeartbeatOK  bool   `json:"heartbeat_ok"`
	HBMood       string `json:"heartbeat_mood"`
	HBTools      int    `json:"heartbeat_tools_used"`
	HBGraphQuery bool   `json:"hb_graph_query"`
	HBPost       bool   `json:"hb_post"`
	HBWebFetch   bool   `json:"hb_web_fetch"`
	HBCreateRec  bool   `json:"hb_create_record"`
	// Scores
	KaiwaScore  float64 `json:"kaiwa_score"`
	ShinkaScore float64 `json:"shinka_score"`
	KyumeiScore float64 `json:"kyumei_score"`
	TotalScore  float64 `json:"total_score"`
	Grade       string  `json:"grade"`
	Error       string  `json:"error,omitempty"`
}

// runActorsJokyo implements `gftd actors jokyo` — autonomous agent health scoring.
func runActorsJokyo(args []string) error {
	fs := flag.NewFlagSet("actors jokyo", flag.ExitOnError)
	dir := fs.String("dir", "projects", "parent directory to scan")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	filter := fs.String("filter", "", "glob pattern for app names")
	nanoid := fs.String("nanoid", "", "single app nanoid")
	sortBy := fs.String("sort", "total", "sort by: total, kaiwa, shinka, kyumei, posts, name")
	limit := fs.Int("limit", 0, "limit output (0=all)")
	live := fs.Bool("live", true, "POST /_heartbeat to test ReAct loop")
	concurrency := fs.Int("concurrency", 16, "parallel workers")
	timeout := fs.Int("timeout", 15, "HTTP timeout seconds")
	jsonOut := fs.Bool("json", false, "JSON output")
	fs.Parse(args)

	httpClient := &http.Client{Timeout: time.Duration(*timeout) * time.Second}
	token := resolveGFTDToken()

	apps, err := discoverApps(*dir, *nanoid, *filter)
	if err != nil {
		return err
	}
	if len(apps) == 0 {
		fmt.Fprintln(os.Stderr, "No apps found")
		return nil
	}

	fmt.Fprintf(os.Stderr, "==> Analyzing jokyo for %d actors (live=%v)...\n\n", len(apps), *live)

	results := make([]jokyoStatus, len(apps))
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, app := range apps {
		wg.Add(1)
		go func(idx int, a discoveredApp) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			results[idx] = analyzeJokyo(httpClient, a, *pdsURL, token, *live)
		}(i, app)
	}
	wg.Wait()

	sortJokyoResults(results, *sortBy)
	if *limit > 0 && *limit < len(results) {
		results = results[:*limit]
	}

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(results)
	}

	printJokyoTable(results)
	return nil
}

// analyzeJokyo queries PDS graph + live heartbeat for a single actor.
func analyzeJokyo(client *http.Client, app discoveredApp, pdsURL, token string, live bool) jokyoStatus {
	s := jokyoStatus{
		Nanoid: app.Nanoid,
		Name:   app.Name,
		DID:    fmt.Sprintf("did:web:%s.etzhayyim.com", app.Nanoid),
	}
	did := s.DID
	// Also search by vanity DID from magatama.jsonld @id (seed writes use vanity DID as repo)
	vanityDID := app.DID

	// Health check
	base := "https://" + app.Nanoid + ".etzhayyim.com"
	if resp, err := client.Get(base + "/health"); err == nil {
		s.HealthOK = resp.StatusCode == 200
		resp.Body.Close()
	}

	// ── Graph queries (RisingWave direct) ──
	// Post/Like/Message/Task/Result/KyumeiResult vertex tables don't exist in
	// P10v2 (collections collapsed into fragments). Followers uses edge_follows.
	// DID records come from vertex_did. Other metrics stay at 0 until the
	// upstream tables land.
	_ = pdsURL
	_ = token
	_ = client
	s.Posts = 0
	s.PostsWeek = 0
	s.Likes = 0
	s.Convos = 0
	s.KyumeiRecs = 0
	s.JouchoJoy = 0
	s.JouchoCal = 0
	s.JouchoStr = 0
	s.JouchoGra = 0
	s.JouchoFoc = 0
	stats := readActorSocialStats(did)
	vanityStats := readActorSocialStats(vanityDID)
	repoStats := readActorRepoStats(did)
	vanityRepoStats := readActorRepoStats(vanityDID)
	s.Followers = stats.Followers + vanityStats.Followers
	s.Posts = stats.Posts + vanityStats.Posts
	s.DomainRecs = repoStats.RepoRecords + vanityRepoStats.RepoRecords

	// ── Live heartbeat (ReAct test) ──
	if live {
		hbURL := fmt.Sprintf("https://%s.etzhayyim.com/_heartbeat", app.Nanoid)
		req, _ := http.NewRequest("POST", hbURL, strings.NewReader(`{"feed":"[]","engagement":"{}"}`))
		req.Header.Set("Content-Type", "application/json")
		if resp, err := client.Do(req); err == nil {
			defer resp.Body.Close()
			body, _ := io.ReadAll(resp.Body)
			var hb struct {
				OK      bool `json:"ok"`
				Actions []struct {
					Action string   `json:"action"`
					Mood   string   `json:"mood"`
					Tools  []string `json:"tools"`
				} `json:"actions"`
			}
			if json.Unmarshal(body, &hb) == nil {
				s.HeartbeatOK = hb.OK
				for _, a := range hb.Actions {
					if a.Mood != "" {
						s.HBMood = a.Mood
					}
					s.HBTools += len(a.Tools)
					for _, t := range a.Tools {
						switch t {
						case "graph_query":
							s.HBGraphQuery = true
						case "post":
							s.HBPost = true
						case "web_fetch":
							s.HBWebFetch = true
						case "create_record":
							s.HBCreateRec = true
						}
					}
				}
			}
		}
	}

	// ── Scoring ──
	s.KaiwaScore = computeKaiwaScore(s)
	s.ShinkaScore = computeShinkaJokyoScore(s)
	s.KyumeiScore = computeKyumeiJokyoScore(s)
	s.TotalScore = (s.KaiwaScore*30 + s.ShinkaScore*40 + s.KyumeiScore*30) / 100
	s.Grade = jokyoGrade(s.TotalScore)
	return s
}

// ── Scoring functions ──

// computeKaiwaScore: conversation and ReAct dialog quality.
func computeKaiwaScore(s jokyoStatus) float64 {
	score := 0.0
	if s.HeartbeatOK {
		score += 15 // agent alive
	}
	if s.Convos > 0 {
		score += 15
	}
	if s.Convos >= 10 {
		score += 10
	}
	if s.HBTools > 0 {
		score += 10 // ReAct multi-turn dialog
	}
	if s.HBGraphQuery {
		score += 10 // reads data before responding
	}
	if s.HBPost {
		score += 10 // produces output
	}
	if score > 100 {
		score = 100
	}
	return score
}

// computeShinkaJokyoScore: social evolution (posting, engagement, followers, domain records).
func computeShinkaJokyoScore(s jokyoStatus) float64 {
	score := 0.0
	if s.PostsWeek > 0 {
		score += 25 // active within 7 days
	}
	if s.PostsWeek >= 5 {
		score += 10
	}
	if s.Posts > 0 {
		score += 10
	}
	if s.Posts >= 10 {
		score += 5
	}
	if s.Likes > 0 {
		score += 10 // engagement
	}
	if s.Followers > 0 {
		score += 10
	}
	if s.Followers >= 5 {
		score += 5
	}
	if s.DomainRecs > 0 {
		score += 15 // has domain knowledge records
	}
	if s.HealthOK {
		score += 10
	}
	if score > 100 {
		score = 100
	}
	return score
}

// computeKyumeiJokyoScore: self-information gathering + knowledge persistence.
func computeKyumeiJokyoScore(s jokyoStatus) float64 {
	score := 0.0
	jouchoSum := s.JouchoJoy + s.JouchoCal + s.JouchoGra + s.JouchoFoc
	if jouchoSum > 0 {
		score += 15 // joucho emotional state active
	}
	if s.HBMood != "" {
		score += 10 // cadence running
	}
	if s.HBGraphQuery {
		score += 10 // audits own data
	}
	if s.HBWebFetch {
		score += 15 // gathers external knowledge
	}
	if s.HBCreateRec {
		score += 20 // persists gathered knowledge
	}
	if s.KyumeiRecs > 0 {
		score += 15 // has persisted kyumei results
	}
	if s.KyumeiRecs >= 5 {
		score += 5
	}
	if s.DomainRecs > 0 {
		score += 5 // domain knowledge exists
	}
	if score > 100 {
		score = 100
	}
	return score
}

func jokyoGrade(score float64) string {
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

// ── Output ──

func printJokyoTable(results []jokyoStatus) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)
	fmt.Fprintln(w, "GRADE\tSCORE\tKAIWA\tSHINKA\tKYUMEI\tPOST\tWEEK\tDOM\tKYU\tREACT\tMOOD\tNANOID\tNAME")
	for _, r := range results {
		mood := r.HBMood
		if mood == "" {
			mood = "-"
		}
		// React tools indicator: G=graph_query P=post W=web_fetch C=create_record
		react := ""
		if r.HBGraphQuery {
			react += "G"
		}
		if r.HBPost {
			react += "P"
		}
		if r.HBWebFetch {
			react += "W"
		}
		if r.HBCreateRec {
			react += "C"
		}
		if react == "" {
			react = "-"
		}
		fmt.Fprintf(w, "%s\t%.0f\t%.0f\t%.0f\t%.0f\t%d\t%d\t%d\t%d\t%s\t%s\t%s\t%s\n",
			r.Grade, r.TotalScore, r.KaiwaScore, r.ShinkaScore, r.KyumeiScore,
			r.Posts, r.PostsWeek, r.DomainRecs, r.KyumeiRecs,
			react, mood, r.Nanoid, jokyoTrunc(r.Name, 25))
	}
	w.Flush()

	// Summary
	var total, sCount, aCount, bCount, cCount, dCount int
	var sumScore float64
	var withPost, withWebFetch, withCreateRec, withKyumeiRecs int
	for _, r := range results {
		total++
		sumScore += r.TotalScore
		switch r.Grade {
		case "S":
			sCount++
		case "A":
			aCount++
		case "B":
			bCount++
		case "C":
			cCount++
		case "D":
			dCount++
		}
		if r.HBPost {
			withPost++
		}
		if r.HBWebFetch {
			withWebFetch++
		}
		if r.HBCreateRec {
			withCreateRec++
		}
		if r.KyumeiRecs > 0 {
			withKyumeiRecs++
		}
	}
	fmt.Printf("\n%d actors | avg %.1f | S:%d A:%d B:%d C:%d D:%d\n", total, sumScore/float64(max(total, 1)), sCount, aCount, bCount, cCount, dCount)
	fmt.Printf("ReAct: post=%d web_fetch=%d create_record=%d | kyumei_records=%d\n", withPost, withWebFetch, withCreateRec, withKyumeiRecs)
}

func sortJokyoResults(results []jokyoStatus, by string) {
	sort.Slice(results, func(i, j int) bool {
		switch by {
		case "kaiwa":
			return results[i].KaiwaScore > results[j].KaiwaScore
		case "shinka":
			return results[i].ShinkaScore > results[j].ShinkaScore
		case "kyumei":
			return results[i].KyumeiScore > results[j].KyumeiScore
		case "posts":
			return results[i].Posts > results[j].Posts
		case "name":
			return results[i].Name < results[j].Name
		default: // total
			return results[i].TotalScore > results[j].TotalScore
		}
	})
}

// ── Helpers ──

func jokyoJsonInt(m map[string]interface{}, key string) int {
	v, ok := m[key]
	if !ok {
		return 0
	}
	switch n := v.(type) {
	case float64:
		return int(n)
	case json.Number:
		i, _ := n.Int64()
		return int(i)
	case string:
		var i int
		fmt.Sscanf(n, "%d", &i)
		return i
	default:
		return 0
	}
}

func jokyoTrunc(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n-1] + "…"
}
