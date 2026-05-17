// xrpc.go — gftd xrpc: invoke any XRPC endpoint on an App or PDS.
//
// Designed for use by Claude Code chat agents to trigger commands on deployed apps.
//
// Examples:
//
//	# Seed all platforms on media-gamers (nanoid a7m8oocs)
//	gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{"step":"platforms"}' --app a7m8oocs
//
//	# Seed games batch 0-9
//	gftd xrpc ai.gftd.apps.media_gamers.catalog.seedGames -d '{"offset":0,"limit":10}' --app a7m8oocs
//
//	# Generate guides for a specific game
//	gftd xrpc ai.gftd.apps.media_gamers.catalog.generateAll -d '{"slug":"elden-ring"}' --app a7m8oocs
//
//	# Query (GET) — no body
//	gftd xrpc ai.gftd.apps.media_gamers.catalog.getGame --app a7m8oocs
//
//	# Route through PDS (default when --app is omitted)
//	gftd xrpc com.atproto.server.describeServer
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

func runXRPC(args []string) error {
	fs := flag.NewFlagSet("xrpc", flag.ContinueOnError)
	data := fs.String("d", "", "JSON body for POST requests")
	appNanoid := fs.String("app", "", "App nanoid (routes to https://{nanoid}.etzhayyim.com/xrpc/{nsid})")
	baseURL := fs.String("url", "", "Override base URL (e.g. https://a7m8oocs.etzhayyim.com)")
	method := fs.String("X", "", "HTTP method: GET or POST (inferred from -d if omitted)")
	jsonOut := fs.Bool("json", false, "Pretty-print JSON response (default: raw stdout)")
	verbose := fs.Bool("v", false, "Verbose: print URL and status code to stderr")

	// Go's flag package stops at the first non-flag argument (the NSID), so flags
	// that follow the NSID would be silently ignored. Pre-pass: extract the NSID
	// (first arg that looks like an NSID — contains dots, no leading dash) and move
	// it to the end so the flag parser sees all flags first.
	nsid, flagArgs := extractNSID(args)

	if err := fs.Parse(flagArgs); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if nsid == "" {
		return fmt.Errorf("usage: gftd xrpc <nsid> [-d <json>] [--app <nanoid>] [--url <base>]\n\nExamples:\n  gftd xrpc ai.gftd.apps.media_gamers.catalog.seedAll -d '{\"step\":\"platforms\"}' --app a7m8oocs\n  gftd xrpc ai.gftd.apps.media_gamers.catalog.seedGames -d '{\"offset\":0,\"limit\":10}' --app a7m8oocs\n  gftd xrpc ai.gftd.apps.media_gamers.catalog.generateAll -d '{\"slug\":\"elden-ring\"}' --app a7m8oocs\n  gftd xrpc com.atproto.server.describeServer")
	}

	// Resolve base URL
	base := resolveXRPCBaseURL(*baseURL, *appNanoid, nsid)

	endpoint := strings.TrimRight(base, "/") + "/xrpc/" + nsid

	// Infer HTTP method
	httpMethod := strings.ToUpper(*method)
	if httpMethod == "" {
		if *data != "" {
			httpMethod = "POST"
		} else {
			httpMethod = "GET"
		}
	}

	// Build request
	var body io.Reader
	if *data != "" {
		body = bytes.NewBufferString(*data)
	}

	req, err := http.NewRequest(httpMethod, endpoint, body)
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}

	if *data != "" {
		req.Header.Set("Content-Type", "application/json")
	}
	req.Header.Set("Accept", "application/json")
	setAuthHeaders(req)

	if *verbose {
		fmt.Fprintf(os.Stderr, "[xrpc] %s %s\n", httpMethod, endpoint)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("request failed: %w", err)
	}
	defer resp.Body.Close()

	respBody, err := io.ReadAll(resp.Body)
	if err != nil {
		return fmt.Errorf("read response: %w", err)
	}

	if *verbose {
		fmt.Fprintf(os.Stderr, "[xrpc] status: %s\n", resp.Status)
	}

	// Print response
	if *jsonOut && json.Valid(respBody) {
		var out any
		if err := json.Unmarshal(respBody, &out); err == nil {
			enc := json.NewEncoder(os.Stdout)
			enc.SetIndent("", "  ")
			_ = enc.Encode(out)
			return nil
		}
	}

	os.Stdout.Write(respBody)
	if len(respBody) > 0 && respBody[len(respBody)-1] != '\n' {
		fmt.Println()
	}

	// Non-2xx = error
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("XRPC %s: HTTP %s", nsid, resp.Status)
	}
	return nil
}

// extractNSID separates the NSID positional argument from flag arguments.
// The NSID is identified as the first arg that doesn't start with '-' and
// contains at least one dot (NSID always looks like com.atproto.* or ai.gftd.*).
// All other args are returned as flagArgs for flag.Parse().
func extractNSID(args []string) (nsid string, flagArgs []string) {
	for i := 0; i < len(args); i++ {
		a := args[i]
		if !strings.HasPrefix(a, "-") && strings.Contains(a, ".") && nsid == "" {
			nsid = a
			continue
		}
		flagArgs = append(flagArgs, a)
		// If this is a flag that takes a value (single-char or known multi-char),
		// consume the next arg as its value so we don't mis-classify it.
		if strings.HasPrefix(a, "-") && !strings.Contains(a, "=") {
			stripped := strings.TrimLeft(a, "-")
			if stripped == "d" || stripped == "X" || stripped == "app" || stripped == "url" {
				if i+1 < len(args) {
					i++
					flagArgs = append(flagArgs, args[i])
				}
			}
		}
	}
	return nsid, flagArgs
}

// resolveXRPCBaseURL resolves the base URL for an XRPC call.
//
// Priority:
//  1. --url flag (explicit override)
//  2. --app <nanoid> → https://{nanoid}.etzhayyim.com
//  3. Infer from NSID prefix (ai.gftd.apps.{app_slug}.*) via known nanoid map
//  4. Fall back to PDS (https://atproto.etzhayyim.com)
func resolveXRPCBaseURL(flagURL, appNanoid, nsid string) string {
	if flagURL != "" {
		return flagURL
	}
	if appNanoid != "" {
		return "https://" + appNanoid + ".etzhayyim.com"
	}
	// Infer from NSID: ai.gftd.apps.{slug}.* → look up in knownApps
	if b := inferBaseFromNSID(nsid); b != "" {
		return b
	}
	return resolvePDSBaseURL()
}

// knownApps maps app slug (from NSID 4th segment) to nanoid.
// Extend as new apps are registered.
var knownApps = map[string]string{
	"media_gamers":  "a7m8oocs",
	"media_anime":   "animegr01",
	"autorace":      "q7v8yed1k",
	"keirin":        "k31r1njp",
	"kyotei":        "qv8yed1k",
	"handotai":      "dtyy44cr",
	"hanrei":        "h4nr31jp",
	"kakaku":        "k4k4kux1",
	"gtin":          "gt1n4k7m",
}

func inferBaseFromNSID(nsid string) string {
	// NSID pattern: ai.gftd.apps.{slug}.{method}
	parts := strings.Split(nsid, ".")
	if len(parts) >= 4 && parts[0] == "ai" && parts[1] == "gftd" && parts[2] == "apps" {
		slug := parts[3]
		if nanoid, ok := knownApps[slug]; ok {
			return "https://" + nanoid + ".etzhayyim.com"
		}
	}
	return ""
}
