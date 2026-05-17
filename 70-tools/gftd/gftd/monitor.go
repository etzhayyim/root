package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"text/tabwriter"
	"time"
)

type appStatus struct {
	Nanoid     string
	Name       string
	UIType     string
	HealthCode int
	HealthOK   bool
	MetaOK     bool
	MetaName   string
	MetaUI     string
	ProfileOK  bool
	WaveResult string
	Error      string
	LatencyMs  int64
}

type appMeta struct {
	Nanoid    string `json:"nanoid"`
	Name      string `json:"name"`
	Runtime   string `json:"runtime"`
	UI        string `json:"ui"`
	Version   string `json:"version"`
	Template  string `json:"template"`
	Source    string `json:"source"`
	DeploySHA string `json:"deploy_sha"`
	DeployAt  string `json:"deploy_at"`
}

func runMonitor(args []string) error {
	fs := flag.NewFlagSet("monitor", flag.ExitOnError)
	dir := fs.String("dir", "projects", "parent directory to scan for magatama.jsonld")
	nanoid := fs.String("nanoid", "", "check a single app by nanoid")
	filter := fs.String("filter", "", "glob pattern for app names")
	wave := fs.String("wave", "", "send wave to nanoid (or 'all')")
	message := fs.String("message", "", "custom wave message")
	concurrency := fs.Int("concurrency", 16, "parallel health check workers")
	timeout := fs.Int("timeout", 10, "HTTP timeout in seconds")
	fs.Parse(args)

	httpClient := &http.Client{Timeout: time.Duration(*timeout) * time.Second}

	// Wave mode
	if *wave != "" {
		return runWave(httpClient, *dir, *wave, *message)
	}

	// Discovery: find all ESM apps
	apps, err := discoverApps(*dir, *nanoid, *filter)
	if err != nil {
		return err
	}
	if len(apps) == 0 {
		fmt.Fprintln(os.Stderr, "No apps found")
		return nil
	}

	fmt.Fprintf(os.Stderr, "==> Checking %d apps (concurrency=%d)...\n\n", len(apps), *concurrency)

	// Parallel health check
	results := make([]appStatus, len(apps))
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, app := range apps {
		wg.Add(1)
		go func(idx int, a discoveredApp) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()
			results[idx] = checkApp(httpClient, a)
		}(i, app)
	}
	wg.Wait()

	// Sort by health status (healthy first, then by name)
	sort.Slice(results, func(i, j int) bool {
		if results[i].HealthOK != results[j].HealthOK {
			return results[i].HealthOK
		}
		return results[i].Name < results[j].Name
	})

	// Output table
	printStatusTable(results)

	return nil
}

type discoveredApp struct {
	Nanoid string
	Name   string
	UIType string
	DID    string
	Dir    string
}

func discoverApps(dir, singleNanoid, filter string) ([]discoveredApp, error) {
	var apps []discoveredApp

	err := filepath.Walk(dir, func(path string, info os.FileInfo, err error) error {
		if err != nil || info.IsDir() || info.Name() != "magatama.jsonld" {
			return nil
		}
		data, err := os.ReadFile(path)
		if err != nil {
			return nil
		}
		var jld struct {
			ID      string `json:"@id"`
			Nanoid  string `json:"nanoid"`
			UIType  string `json:"uiType"`
			Profile struct {
				DisplayName string `json:"displayName"`
			} `json:"profile"`
		}
		if json.Unmarshal(data, &jld) != nil {
			return nil
		}
		if jld.Nanoid == "" {
			return nil
		}
		if singleNanoid != "" && jld.Nanoid != singleNanoid {
			return nil
		}
		if filter != "" {
			matched, _ := filepath.Match(filter, jld.Profile.DisplayName)
			matchedNanoid, _ := filepath.Match(filter, jld.Nanoid)
			if !matched && !matchedNanoid {
				return nil
			}
		}
		apps = append(apps, discoveredApp{
			Nanoid: jld.Nanoid,
			Name:   jld.Profile.DisplayName,
			UIType: jld.UIType,
			DID:    jld.ID,
			Dir:    filepath.Dir(path),
		})
		return nil
	})
	return apps, err
}

func checkApp(client *http.Client, app discoveredApp) appStatus {
	s := appStatus{
		Nanoid: app.Nanoid,
		Name:   app.Name,
		UIType: app.UIType,
	}

	base := "https://" + app.Nanoid + ".etzhayyim.com"

	// 1. Health check
	start := time.Now()
	resp, err := client.Get(base + "/health")
	s.LatencyMs = time.Since(start).Milliseconds()
	if err != nil {
		s.HealthCode = 0
		s.Error = "unreachable"
	} else {
		s.HealthCode = resp.StatusCode
		s.HealthOK = resp.StatusCode == 200
		resp.Body.Close()
	}

	// 2. Meta check
	resp, err = client.Get(base + "/_app/meta")
	if err == nil {
		defer resp.Body.Close()
		body, _ := io.ReadAll(resp.Body)
		var meta appMeta
		if json.Unmarshal(body, &meta) == nil && meta.Nanoid != "" {
			s.MetaOK = true
			s.MetaName = meta.Name
			s.MetaUI = meta.UI
		}
	}

	// 3. Profile check (yoro profile page returns 200 if profile exists)
	profileURL := "https://yoro.etzhayyim.com/profile/did:web:" + app.Nanoid + ".etzhayyim.com"
	resp, err = client.Get(profileURL)
	if err == nil {
		s.ProfileOK = resp.StatusCode == 200
		resp.Body.Close()
	}

	return s
}

func printStatusTable(results []appStatus) {
	w := tabwriter.NewWriter(os.Stdout, 0, 0, 2, ' ', 0)

	healthy := 0
	degraded := 0
	for _, r := range results {
		if r.HealthOK {
			healthy++
		} else {
			degraded++
		}
	}

	fmt.Fprintf(w, "\nApp Status Monitor (%d apps)\n\n", len(results))
	fmt.Fprintln(w, "Nanoid\tName\tHealth\tMeta\tProfile\tLatency")
	fmt.Fprintln(w, "--------\t--------------------\t------\t----\t-------\t-------")

	for _, r := range results {
		health := fmt.Sprintf("✗ %d", r.HealthCode)
		if r.HealthOK {
			health = "✓ 200"
		}
		if r.HealthCode == 0 {
			health = "✗ ?"
		}

		meta := "✗"
		if r.MetaOK {
			meta = "✓"
		}

		profile := "✗"
		if r.ProfileOK {
			profile = "✓"
		}

		latency := fmt.Sprintf("%dms", r.LatencyMs)

		fmt.Fprintf(w, "%s\t%s\t%s\t%s\t%s\t%s\n",
			r.Nanoid, truncateStr(r.Name, 20), health, meta, profile, latency)
	}

	fmt.Fprintln(w)
	fmt.Fprintf(w, "Summary: %d/%d healthy, %d degraded\n", healthy, len(results), degraded)
	w.Flush()
}

func truncateStrMon(s string, max int) string {
	if len(s) <= max {
		return s
	}
	return s[:max-1] + "…"
}

// --- Wave ---

func runWave(client *http.Client, dir, target, message string) error {
	if message == "" {
		message = "Hello from gftd monitor!"
	}

	var targets []discoveredApp

	if target == "all" {
		var err error
		targets, err = discoverApps(dir, "", "")
		if err != nil {
			return err
		}
	} else {
		targets = []discoveredApp{{Nanoid: target, Name: target}}
	}

	fmt.Fprintf(os.Stderr, "==> Waving to %d app(s)...\n\n", len(targets))

	token := resolveGFTDToken()

	var wg sync.WaitGroup
	sem := make(chan struct{}, 8)
	var mu sync.Mutex
	success := 0
	failed := 0

	for _, app := range targets {
		wg.Add(1)
		go func(a discoveredApp) {
			defer wg.Done()
			sem <- struct{}{}
			defer func() { <-sem }()

			result, err := waveApp(client, a.Nanoid, message, token)
			mu.Lock()
			defer mu.Unlock()
			if err != nil {
				fmt.Printf("  ✗ %s (%s): %v\n", a.Nanoid, a.Name, err)
				failed++
			} else {
				fmt.Printf("  ✓ %s (%s): %s\n", a.Nanoid, a.Name, result)
				success++
			}
		}(app)
	}
	wg.Wait()

	fmt.Fprintf(os.Stderr, "\n==> Wave complete: %d success, %d failed\n", success, failed)
	return nil
}

func waveApp(client *http.Client, nanoid, message, token string) (string, error) {
	url := fmt.Sprintf("https://%s.etzhayyim.com/xrpc/gftd.magatama.v1.MagatamaCommandService/Execute", nanoid)

	body := map[string]any{
		"command": "wave",
		"args":    json.RawMessage(mustJSON(map[string]string{"message": message, "from": "gftd-cli"})),
	}
	bodyJSON, _ := json.Marshal(body)

	req, err := http.NewRequest("POST", url, bytes.NewReader(bodyJSON))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("unreachable: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)

	if resp.StatusCode >= 300 {
		// Fallback: try simple GET to wake app
		wakeURL := fmt.Sprintf("https://%s.etzhayyim.com/_app/meta", nanoid)
		wakeResp, wakeErr := client.Get(wakeURL)
		if wakeErr == nil {
			wakeResp.Body.Close()
		}
		return "", fmt.Errorf("HTTP %d: %s", resp.StatusCode, truncateStr(string(respBody), 100))
	}

	var result map[string]string
	if json.Unmarshal(respBody, &result) == nil {
		if g, ok := result["greeting"]; ok {
			return g, nil
		}
	}
	return strings.TrimSpace(string(respBody)), nil
}

func mustJSON(v any) []byte {
	b, _ := json.Marshal(v)
	return b
}
