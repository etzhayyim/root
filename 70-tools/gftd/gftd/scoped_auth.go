// ADR-0022 step 2: per-request NSID-scoped Service Auth JWT auto-mint.
//
// setAuthHeaders() derives the target NSID from req.URL.Path and, when a base
// token is available, calls com.atproto.server.getServiceAuth to obtain a
// 60s ES256 JWT with `lxm = <nsid>`. The scoped JWT replaces the base token
// on the outgoing request so the caller's blast radius is bounded to exactly
// one method.
//
// Fallbacks (each logged only when GFTD_SCOPED_AUTH_DEBUG=1 to keep tests quiet):
//   - NSID cannot be derived from URL  → send base token (non-XRPC endpoints)
//   - NSID is com.atproto.server.getServiceAuth → send base token (bootstrap)
//   - GFTD_SCOPED_AUTH=off              → send base token (kill switch)
//   - getServiceAuth returns non-2xx or network error → send base token (degraded)
//
// Cache: process-local map keyed by sha256(baseToken)[:16] + nsid, TTL = mint
// response expiry minus 10s. Concurrency-safe via sync.Mutex.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"strings"
	"sync"
	"time"
)

type scopedJWTEntry struct {
	token string
	exp   time.Time
}

var (
	scopedJWTMu    sync.Mutex
	scopedJWTCache = map[string]scopedJWTEntry{}
)

const (
	scopedJWTDefaultTTL = 300 // seconds — well under getServiceAuth's 3600 cap
	scopedJWTSkew       = 10 * time.Second
	serviceAuthNSID     = "com.atproto.server.getServiceAuth"
)

// nsidFromURLPath extracts the NSID from a URL path of the form ".../xrpc/{nsid}".
// Returns "" when the path does not include /xrpc/.
func nsidFromURLPath(u *url.URL) string {
	if u == nil {
		return ""
	}
	path := u.Path
	const marker = "/xrpc/"
	i := strings.Index(path, marker)
	if i < 0 {
		return ""
	}
	rest := path[i+len(marker):]
	if slash := strings.IndexByte(rest, '/'); slash >= 0 {
		rest = rest[:slash]
	}
	if q := strings.IndexByte(rest, '?'); q >= 0 {
		rest = rest[:q]
	}
	return rest
}

func scopedAuthEnabled() bool {
	v := strings.ToLower(strings.TrimSpace(os.Getenv("GFTD_SCOPED_AUTH")))
	return v != "off" && v != "0" && v != "false"
}

func scopedAuthDebug() bool {
	return os.Getenv("GFTD_SCOPED_AUTH_DEBUG") == "1"
}

func scopedCacheKey(baseToken, nsid string) string {
	sum := sha256.Sum256([]byte(baseToken))
	return hex.EncodeToString(sum[:8]) + ":" + nsid
}

// mintScopedJWT returns a cached or freshly minted ES256 Service Auth JWT scoped
// to `nsid` by calling com.atproto.server.getServiceAuth. Returns "" on any
// failure so callers can fall back to the base token.
func mintScopedJWT(baseToken, nsid string) string {
	if baseToken == "" || nsid == "" || nsid == serviceAuthNSID {
		return ""
	}
	cacheKey := scopedCacheKey(baseToken, nsid)

	scopedJWTMu.Lock()
	if e, ok := scopedJWTCache[cacheKey]; ok && time.Now().Before(e.exp) {
		scopedJWTMu.Unlock()
		return e.token
	}
	scopedJWTMu.Unlock()

	pdsURL := resolvePDSBaseURL()
	audience := "did:web:atproto.etzhayyim.com"
	if u, err := url.Parse(pdsURL); err == nil && u.Hostname() != "" {
		audience = "did:web:" + u.Hostname()
	}

	expUnix := time.Now().Unix() + int64(scopedJWTDefaultTTL)
	body, _ := json.Marshal(map[string]any{
		"aud": audience,
		"lxm": nsid,
		"exp": expUnix,
	})
	req, err := http.NewRequest("POST", pdsURL+"/xrpc/"+serviceAuthNSID, bytes.NewReader(body))
	if err != nil {
		if scopedAuthDebug() {
			fmt.Fprintf(os.Stderr, "[scoped-auth] build request failed: %v\n", err)
		}
		return ""
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+baseToken)
	if did := resolveActiveDID(); did != "" {
		req.Header.Set("X-Active-DID", did)
	}
	if org := resolveOrgHint(); org != "" {
		req.Header.Set("X-Gftd-Org-Id", org)
	}

	client := &http.Client{Timeout: 8 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		if scopedAuthDebug() {
			fmt.Fprintf(os.Stderr, "[scoped-auth] getServiceAuth network error: %v\n", err)
		}
		return ""
	}
	defer resp.Body.Close()
	raw, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		if scopedAuthDebug() {
			fmt.Fprintf(os.Stderr, "[scoped-auth] getServiceAuth HTTP %d for lxm=%s: %s\n", resp.StatusCode, nsid, truncStr(string(raw), 200))
		}
		return ""
	}
	var out struct {
		Token string `json:"token"`
	}
	if err := json.Unmarshal(raw, &out); err != nil || out.Token == "" {
		if scopedAuthDebug() {
			fmt.Fprintf(os.Stderr, "[scoped-auth] getServiceAuth parse failed: %v\n", err)
		}
		return ""
	}

	scopedJWTMu.Lock()
	scopedJWTCache[cacheKey] = scopedJWTEntry{
		token: out.Token,
		exp:   time.Unix(expUnix, 0).Add(-scopedJWTSkew),
	}
	scopedJWTMu.Unlock()
	return out.Token
}
