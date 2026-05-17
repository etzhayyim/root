// gftd agent-token — mint a short-lived scoped service-auth JWT for
// programmatic agents (Claude Code, scripts, CI).
//
// Flow:
//
//	gftd auth login                                 (once, human)
//	gftd auth create-api-key --name "claude-jun"   (once, store as env)
//	export GFTD_TOKEN=sk_live_...                  (CI / Claude shell)
//	AT_TOKEN=$(gftd agent-token \
//	  --lxm com.atproto.repo.applyWrites \
//	  --aud did:web:atproto.etzhayyim.com \
//	  --ttl 60)
//	curl -H "Authorization: Bearer $AT_TOKEN" https://atproto.etzhayyim.com/xrpc/...
//
// The underlying primitive is the standard atproto
// `com.atproto.server.getServiceAuth` endpoint (lexicon-registered in
// ai-gftd-pds-2603241700). That endpoint mints a DID-signed ES256 JWT
// with an `lxm` claim binding the token to exactly one NSID. Grants
// therefore flow through the existing Permission-Set machinery on API
// keys — no new graph schema required.
//
// This command is deliberately stateless: every invocation re-reads the
// base token from `GFTD_TOKEN` / `~/.gftd/auth.json` and calls
// `getServiceAuth` fresh. The resulting JWT is written to stdout so the
// caller can `export` it into an env var or pipe it directly into curl.
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"time"
)

// runAgentToken mints a short-lived service-auth JWT scoped to a single
// NSID via `com.atproto.server.getServiceAuth`.
func runAgentToken(args []string) error {
	fs := flag.NewFlagSet("agent-token", flag.ContinueOnError)
	lxm := fs.String("lxm", "", "NSID to bind the token to (required). Example: com.atproto.repo.applyWrites")
	aud := fs.String("aud", "", "Audience DID. Defaults to `did:web:<pds-host>` derived from --pds.")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	ttl := fs.Int("ttl", 60, "Token lifetime in seconds (1..3600). PDS may clamp.")
	sub := fs.String("sub", "", "Optional subject DID for the JWT `sub` claim (defaults to caller DID = iss). Per atproto permission spec + ADR-2604231800.")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if strings.TrimSpace(*lxm) == "" {
		fs.Usage()
		return fmt.Errorf("--lxm is required")
	}
	if *ttl < 1 || *ttl > 3600 {
		return fmt.Errorf("--ttl must be in [1, 3600]")
	}

	baseToken := resolveGFTDToken()
	if baseToken == "" {
		return fmt.Errorf("no GFTD token found — run `gftd auth login` or set GFTD_TOKEN")
	}

	pdsURL := strings.TrimRight(strings.TrimSpace(*pds), "/")
	if pdsURL == "" {
		pdsURL = "https://atproto.etzhayyim.com"
	}

	// Derive aud from PDS host if not explicitly given.
	audience := strings.TrimSpace(*aud)
	if audience == "" {
		if u, err := url.Parse(pdsURL); err == nil && u.Hostname() != "" {
			audience = "did:web:" + u.Hostname()
		} else {
			audience = "did:web:atproto.etzhayyim.com"
		}
	}

	expUnix := time.Now().Unix() + int64(*ttl)
	payload := map[string]any{
		"aud": audience,
		"lxm": *lxm,
		"exp": expUnix,
	}
	if s := strings.TrimSpace(*sub); s != "" {
		payload["sub"] = s
	}
	body, _ := json.Marshal(payload)

	target := pdsURL + "/xrpc/com.atproto.server.getServiceAuth"
	req, err := http.NewRequest("POST", target, bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+baseToken)
	if did := resolveActiveDID(); did != "" {
		req.Header.Set("X-Active-DID", did)
	}
	if org := resolveOrgHint(); org != "" {
		req.Header.Set("X-Gftd-Org-Id", org)
	}

	if *verbose {
		fmt.Fprintf(os.Stderr, "[agent-token] POST %s lxm=%s aud=%s ttl=%ds\n", target, *lxm, audience, *ttl)
	}

	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("getServiceAuth: %w", err)
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if *verbose {
		fmt.Fprintf(os.Stderr, "[agent-token] HTTP %d\n", resp.StatusCode)
	}
	if resp.StatusCode >= 400 {
		return fmt.Errorf("getServiceAuth: HTTP %d: %s", resp.StatusCode, truncStr(string(raw), 400))
	}

	var out struct {
		Token string `json:"token"`
	}
	if err := json.Unmarshal(raw, &out); err != nil {
		return fmt.Errorf("getServiceAuth: parse response: %w", err)
	}
	if out.Token == "" {
		return fmt.Errorf("getServiceAuth: empty token")
	}

	fmt.Println(out.Token)
	return nil
}
