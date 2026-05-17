package main

import (
	"bytes"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/user"
	"runtime"
	"strings"
	"time"
)

// ocelCLIEvent represents a CLI command event emitted to Analytics Engine via PDS.
type ocelCLIEvent struct {
	Method  string  `json:"method"`  // e.g. "gftd.build", "gftd.deploy"
	Ms      float64 `json:"ms"`      // command duration in milliseconds
	Status  int     `json:"status"`  // 0=success, 1=error
	Auth    string  `json:"auth"`    // "cli"
	Type    string  `json:"type"`    // "cli"
	Colo    string  `json:"colo"`    // hostname
	Country string  `json:"country"` // OS/arch
	UA      string  `json:"ua"`      // "gftd/{version}"
	Err     string  `json:"err,omitempty"`
}

// emitOcelCLIEvent sends a CLI command event to PDS Analytics Engine (fire-and-forget).
// Never blocks or returns errors — logging failures are silently ignored.
func emitOcelCLIEvent(method string, durationMs float64, status int, errMsg string) {
	pdsURL := os.Getenv("GFTD_PDS_URL")
	if pdsURL == "" {
		pdsURL = defaultPDSURL
	}

	hostname, _ := os.Hostname()
	osArch := fmt.Sprintf("%s/%s", runtime.GOOS, runtime.GOARCH)
	ua := fmt.Sprintf("gftd/%s", version)

	evt := ocelCLIEvent{
		Method:  method,
		Ms:      durationMs,
		Status:  status,
		Auth:    "cli",
		Type:    "cli",
		Colo:    hostname,
		Country: osArch,
		UA:      ua,
		Err:     errMsg,
	}

	body, err := json.Marshal(evt)
	if err != nil {
		return
	}

	endpoint := strings.TrimRight(pdsURL, "/") + "/xrpc/ai.gftd.pds.emitOcel"
	req, err := http.NewRequest("POST", endpoint, bytes.NewReader(body))
	if err != nil {
		return
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", ua)

	// Attach auth if available (best-effort)
	token := resolveGFTDToken()
	// ai.gftd.pds.emitOcel is internal-only. Skip emit for regular user/session tokens
	// to avoid noisy 4xx logs.
	if token == "" || !isLikelyInternalToken(token) {
		return
	}
	req.Header.Set("Authorization", "Bearer "+token)

	// Add CLI user identity
	if u, err := user.Current(); err == nil {
		req.Header.Set("X-CLI-User", u.Username)
	}

	client := &http.Client{Timeout: 5 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return
	}
	resp.Body.Close()
}

func isLikelyInternalToken(token string) bool {
	parts := strings.Split(token, ".")
	if len(parts) < 2 {
		return false
	}
	payloadB64 := parts[1]
	decoded, err := base64.RawURLEncoding.DecodeString(payloadB64)
	if err != nil {
		return false
	}
	var payload map[string]any
	if err := json.Unmarshal(decoded, &payload); err != nil {
		return false
	}
	iss := strings.ToLower(fmt.Sprint(payload["iss"]))
	scope := strings.ToLower(fmt.Sprint(payload["scope"]))
	aud := strings.ToLower(fmt.Sprint(payload["aud"]))
	return strings.Contains(iss, "internal") ||
		strings.Contains(scope, "internal") ||
		strings.Contains(aud, "internal")
}

// withOcelLog wraps a CLI command function to emit OCEL events on completion.
// Records command name, duration, and success/failure status.
func withOcelLog(command string, fn func() error) error {
	start := time.Now()
	err := fn()
	durationMs := float64(time.Since(start).Milliseconds())

	status := 0
	errMsg := ""
	if err != nil {
		status = 1
		errMsg = err.Error()
		if len(errMsg) > 200 {
			errMsg = errMsg[:200]
		}
	}

	// Fire-and-forget: emit in background goroutine
	go emitOcelCLIEvent(command, durationMs, status, errMsg)

	// Brief sleep to allow the goroutine to send before process exit
	time.Sleep(50 * time.Millisecond)

	return err
}
