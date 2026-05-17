// kagami_client — vestigial compatibility types from the archived kagami
// HTTP proxy layer. Runtime code paths now talk to RisingWave directly via
// `db.Pool()` / `db.RawQuery()` / sqlc-generated queries.
//
// This file only keeps the shared helpers (string/math utilities,
// `kagamiConfig` / `kagamiResponse` types) that legacy callers still
// reference as struct-valued parameters. Nothing here performs HTTP.
package main

import (
	"encoding/json"
	"fmt"
	"strings"
)

// toInt64FromAny converts an any value (typically float64 from JSON) to int64.
func toInt64FromAny(v any) int64 {
	switch n := v.(type) {
	case int64:
		return n
	case int32:
		return int64(n)
	case int:
		return int64(n)
	case float64:
		return int64(n)
	case float32:
		return int64(n)
	case json.Number:
		if i, err := n.Int64(); err == nil {
			return i
		}
	case string:
		var i int64
		if _, err := fmt.Sscanf(n, "%d", &i); err == nil {
			return i
		}
	}
	return 0
}

// sqlEscape escapes a string for use in SQL single-quoted literals.
func sqlEscape(s string) string {
	return strings.ReplaceAll(s, "'", "''")
}

// extractHostFromRepo extracts the host part from a DID repo string.
func extractHostFromRepo(repo string) string {
	repo = strings.TrimPrefix(repo, "did:web:")
	if idx := strings.Index(repo, ":"); idx >= 0 {
		repo = repo[:idx]
	}
	return strings.TrimSuffix(repo, ".etzhayyim.com")
}

// domainMatchesHost checks if a worldDomain matches a given host string.
func domainMatchesHost(wd worldDomain, host string) bool {
	primary := strings.TrimSuffix(wd.App, ".etzhayyim.com")
	primary = normalizeDomainLookup(primary)
	if primary != "" && (host == primary || strings.HasPrefix(host, primary+"-") || strings.HasPrefix(host, primary+".")) {
		return true
	}
	for _, alt := range wd.AltPrefixes {
		alt = strings.TrimSpace(alt)
		if alt == "" {
			continue
		}
		if strings.HasSuffix(alt, "-") {
			if strings.HasPrefix(host, alt) {
				return true
			}
		} else if host == alt {
			return true
		}
	}
	return false
}

// kagamiConfig is retained as a compatibility stub. The Endpoint/TimeoutMs
// fields are ignored — runtime code reads from the pgx pool instead.
type kagamiConfig struct {
	Endpoint  string
	TimeoutMs int
}

// kagamiResponse mirrors the legacy HTTP response shape (columns + row maps).
// Retained so callers that still declare variables of this type compile.
type kagamiResponse struct {
	Columns []string         `json:"columns"`
	Rows    []map[string]any `json:"rows"`
	Engine  string           `json:"engine,omitempty"`
	Elapsed int              `json:"elapsed,omitempty"`
	Error   string           `json:"error,omitempty"`
	Detail  string           `json:"detail,omitempty"`
}

