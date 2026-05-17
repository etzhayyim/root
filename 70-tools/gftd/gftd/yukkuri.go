package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

// runYukkuri dispatches gftd yukkuri subcommands.
//
// Usage:
//
//	gftd yukkuri compose   --topic "..." [--outline "..."] [--owner-did "did:..."]
//	gftd yukkuri list      [--owner-did "did:..."] [--status queued|script|...] [--offset N] [--limit N]
//	gftd yukkuri get       --video-id <rkey>
//	gftd yukkuri health
//
// The XRPC base URL defaults to https://yukkuri.etzhayyim.com (or $YUKKURI_URL).
// All subcommands POST to /xrpc/ai.gftd.apps.yukkuri.<Method> using setAuthHeaders.
func runYukkuri(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: gftd yukkuri <compose|list|get|health> [flags]")
	}
	switch args[0] {
	case "compose":
		return runYukkuriCompose(args[1:])
	case "list":
		return runYukkuriList(args[1:])
	case "get":
		return runYukkuriGet(args[1:])
	case "health":
		return runYukkuriHealth(args[1:])
	default:
		return fmt.Errorf("unknown yukkuri subcommand %q. Available: compose, list, get, health", args[0])
	}
}

// yukkuriBaseURL returns the effective XRPC base URL (env override or default).
func yukkuriBaseURL() string {
	if u := strings.TrimRight(os.Getenv("YUKKURI_URL"), "/"); u != "" {
		return u
	}
	return "https://yukkuri.etzhayyim.com"
}

// yukkuriXRPC posts to /xrpc/<nsid> and returns the parsed response body.
func yukkuriXRPC(nsid string, payload map[string]any) (map[string]any, error) {
	raw, err := json.Marshal(payload)
	if err != nil {
		return nil, fmt.Errorf("marshal: %w", err)
	}
	url := yukkuriBaseURL() + "/xrpc/" + nsid
	req, err := http.NewRequest(http.MethodPost, url, bytes.NewReader(raw))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	setAuthHeaders(req)

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return nil, fmt.Errorf("XRPC %s → HTTP %d: %s", nsid, resp.StatusCode, strings.TrimSpace(string(body)))
	}
	var out map[string]any
	if err := json.Unmarshal(body, &out); err != nil {
		return nil, fmt.Errorf("parse response: %w", err)
	}
	return out, nil
}

// printYukkuriResult emits pretty JSON or a one-liner summary.
func printYukkuriResult(result map[string]any, asJSON bool) {
	if asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		_ = enc.Encode(result)
		return
	}
	// Human-readable fallback: dump top-level string/number fields.
	for _, k := range []string{"ok", "error", "videoId", "videoUri", "status", "total", "latencyMs"} {
		if v, ok := result[k]; ok {
			fmt.Printf("%s: %v\n", k, v)
		}
	}
	if videos, ok := result["videos"].([]any); ok {
		fmt.Printf("videos: %d item(s)\n", len(videos))
		for _, v := range videos {
			if m, ok := v.(map[string]any); ok {
				fmt.Printf("  - %s [%s] %s\n", m["videoId"], m["status"], m["topic"])
			}
		}
	}
}

// ── compose ───────────────────────────────────────────────────────────────

func runYukkuriCompose(args []string) error {
	fs := flag.NewFlagSet("yukkuri compose", flag.ContinueOnError)
	topic    := fs.String("topic", "", "Video topic (required)")
	outline  := fs.String("outline", "", "Optional outline / scene breakdown")
	ownerDid := fs.String("owner-did", "", "Owner DID (defaults to authenticated DID)")
	asJSON   := fs.Bool("json", false, "Output raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *topic == "" {
		return fmt.Errorf("--topic is required")
	}
	payload := map[string]any{"topic": *topic}
	if *outline != "" {
		payload["outline"] = *outline
	}
	if *ownerDid != "" {
		payload["ownerDid"] = *ownerDid
	}
	result, err := yukkuriXRPC("ai.gftd.apps.yukkuri.compose", payload)
	if err != nil {
		return err
	}
	printYukkuriResult(result, *asJSON)
	return nil
}

// ── list ──────────────────────────────────────────────────────────────────

func runYukkuriList(args []string) error {
	fs := flag.NewFlagSet("yukkuri list", flag.ContinueOnError)
	ownerDid := fs.String("owner-did", "", "Filter by owner DID")
	status   := fs.String("status", "", "Filter by status (queued|script|assembled|editready|rendered|published|rejected)")
	offset   := fs.Int("offset", 0, "Pagination offset")
	limit    := fs.Int("limit", 20, "Page size (max 200)")
	asJSON   := fs.Bool("json", false, "Output raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	payload := map[string]any{"offset": *offset, "limit": *limit}
	if *ownerDid != "" {
		payload["ownerDid"] = *ownerDid
	}
	if *status != "" {
		payload["status"] = *status
	}
	result, err := yukkuriXRPC("ai.gftd.apps.yukkuri.listVideos", payload)
	if err != nil {
		return err
	}
	printYukkuriResult(result, *asJSON)
	return nil
}

// ── get ───────────────────────────────────────────────────────────────────

func runYukkuriGet(args []string) error {
	fs := flag.NewFlagSet("yukkuri get", flag.ContinueOnError)
	videoID := fs.String("video-id", "", "Video rkey / ID (required)")
	asJSON  := fs.Bool("json", false, "Output raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	// Also accept positional arg.
	if *videoID == "" && len(fs.Args()) > 0 {
		*videoID = fs.Args()[0]
	}
	if *videoID == "" {
		return fmt.Errorf("--video-id is required")
	}
	result, err := yukkuriXRPC("ai.gftd.apps.yukkuri.getVideo", map[string]any{"videoId": *videoID})
	if err != nil {
		return err
	}
	printYukkuriResult(result, *asJSON)
	return nil
}

// ── health ────────────────────────────────────────────────────────────────

func runYukkuriHealth(args []string) error {
	fs := flag.NewFlagSet("yukkuri health", flag.ContinueOnError)
	asJSON := fs.Bool("json", false, "Output raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	result, err := yukkuriXRPC("ai.gftd.apps.yukkuri.health", map[string]any{})
	if err != nil {
		return err
	}
	printYukkuriResult(result, *asJSON)
	return nil
}
