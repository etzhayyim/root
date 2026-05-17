package main

import (
	"bytes"
	"context"
	"crypto/rand"
	"crypto/sha256"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

const (
	authAuthorizeURL = "https://authn.etzhayyim.com/oauth/authorize" // ADR-0024: auth.etzhayyim.com retired
	authTokenURL     = "https://authn.etzhayyim.com/oauth/token"     // ADR-0024: auth.etzhayyim.com retired
	authClientID     = "gftd-cli"
	authCallbackPort = 9876
	defaultPDSURL    = "https://atproto.etzhayyim.com"

	// Keychain service name (macOS) — CLAUDE.md §Local Secret Storage
	keychainService = "gftd.auth"
)

// tokenStore persists credentials to ~/.gftd/auth.json
//
// ADR-0022 step 5: `APIKey` (sk_live_*) is the canonical bearer. Legacy JWT
// fields (AccessToken / IDToken / RefreshToken / ExpiresAt) are read-only for
// backward compatibility with stores written before `gftd auth migrate` ran.
type tokenStore struct {
	APIKey       string `json:"api_key,omitempty"`       // sk_live_* — canonical bearer
	AccessToken  string `json:"access_token,omitempty"`  // legacy JWT (read-compat only)
	IDToken      string `json:"id_token,omitempty"`      // legacy AT Protocol JWT (read-compat only)
	RefreshToken string `json:"refresh_token,omitempty"` // legacy OAuth refresh (read-compat only)
	ExpiresAt    int64  `json:"expires_at,omitempty"`    // legacy JWT expiry (API keys don't expire)
	Sub          string `json:"sub,omitempty"`
	Email        string `json:"email,omitempty"`
	ActiveDID    string `json:"active_did,omitempty"` // Switched DID (org/sub-org). Empty = Sub (personal DID)
}

func authDir() string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".gftd")
}

func authFile() string {
	return filepath.Join(authDir(), "auth.json")
}

func loadTokenStore() (*tokenStore, error) {
	data, err := os.ReadFile(authFile())
	if err != nil {
		// Fall back to Keychain when the file is missing.
		if key, kErr := readFromKeychain("api_key"); kErr == nil && key != "" {
			return &tokenStore{APIKey: key}, nil
		}
		return nil, err
	}
	var ts tokenStore
	if err := json.Unmarshal(data, &ts); err != nil {
		return nil, err
	}
	// If file store is expired but Keychain has a fresh API key, prefer it.
	if ts.APIKey == "" && ts.expired() {
		if key, kErr := readFromKeychain("api_key"); kErr == nil && key != "" {
			ts.APIKey = key
			ts.ExpiresAt = 0 // API keys don't expire
		}
	}
	return &ts, nil
}

func (ts *tokenStore) save() error {
	if err := os.MkdirAll(authDir(), 0700); err != nil {
		return err
	}
	data, err := json.MarshalIndent(ts, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(authFile(), data, 0600); err != nil {
		return err
	}
	// Mirror credential to macOS Keychain for cross-tool reuse (CLAUDE.md §Local Secret Storage).
	// Errors are silently ignored — Keychain is a convenience layer, not a hard requirement.
	if ts.APIKey != "" {
		_ = saveToKeychain("api_key", ts.APIKey)
	} else if ts.AccessToken != "" {
		_ = saveToKeychain("access_token", ts.AccessToken)
	}
	return nil
}

// ── macOS Keychain helpers ─────────────────────────────────────────────────

// saveToKeychain persists a credential to macOS Keychain under service "gftd.auth".
// No-op on non-Darwin platforms.
func saveToKeychain(account, value string) error {
	if runtime.GOOS != "darwin" {
		return nil
	}
	return exec.Command("security", "add-generic-password",
		"-s", keychainService, "-a", account, "-w", value, "-U").Run()
}

// readFromKeychain retrieves a credential from macOS Keychain.
// Returns ("", err) on non-Darwin or when the entry does not exist.
func readFromKeychain(account string) (string, error) {
	if runtime.GOOS != "darwin" {
		return "", fmt.Errorf("keychain: not darwin")
	}
	out, err := exec.Command("security", "find-generic-password",
		"-s", keychainService, "-a", account, "-w").Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

// deleteFromKeychain removes a Keychain entry. No-op on non-Darwin.
func deleteFromKeychain(account string) {
	if runtime.GOOS != "darwin" {
		return
	}
	_ = exec.Command("security", "delete-generic-password",
		"-s", keychainService, "-a", account).Run()
}

func (ts *tokenStore) expired() bool {
	// API keys don't expire. Only legacy JWT sessions track ExpiresAt.
	if ts.APIKey != "" {
		return false
	}
	if ts.ExpiresAt == 0 {
		return false
	}
	return time.Now().Unix() > ts.ExpiresAt-60 // 60s buffer
}

// bearerFromStore returns the canonical bearer credential. Preference order:
// (1) APIKey (ADR-0022 canonical), (2) IDToken (legacy), (3) AccessToken (legacy).
func bearerFromStore(ts *tokenStore) string {
	if ts == nil {
		return ""
	}
	if ts.APIKey != "" {
		return ts.APIKey
	}
	if ts.IDToken != "" {
		return ts.IDToken
	}
	return ts.AccessToken
}

func refreshTokenStore(ts *tokenStore) (*tokenStore, error) {
	if ts == nil {
		return nil, fmt.Errorf("no token store")
	}
	if strings.TrimSpace(ts.RefreshToken) == "" {
		return nil, fmt.Errorf("no refresh token")
	}
	params := url.Values{
		"grant_type":    {"refresh_token"},
		"client_id":     {authClientID},
		"refresh_token": {ts.RefreshToken},
	}
	resp, err := http.PostForm(authTokenURL, params)
	if err != nil {
		return nil, fmt.Errorf("refresh token exchange: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		bodyBytes := make([]byte, 2048)
		n, _ := resp.Body.Read(bodyBytes)
		return nil, fmt.Errorf("refresh failed: %s %s", resp.Status, string(bodyBytes[:n]))
	}
	var tokenResp struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		ExpiresIn    int64  `json:"expires_in"`
		IDToken      string `json:"id_token"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&tokenResp); err != nil {
		return nil, fmt.Errorf("parse refresh response: %w", err)
	}
	bearer := tokenResp.IDToken
	if bearer == "" {
		bearer = tokenResp.AccessToken
	}
	if bearer == "" {
		return nil, fmt.Errorf("refresh response missing token")
	}
	sub, email := parseJWTClaims(bearer)
	next := *ts
	next.AccessToken = bearer
	if tokenResp.IDToken != "" {
		next.IDToken = tokenResp.IDToken
	} else {
		next.IDToken = bearer
	}
	if tokenResp.RefreshToken != "" {
		next.RefreshToken = tokenResp.RefreshToken
	}
	if tokenResp.ExpiresIn > 0 {
		next.ExpiresAt = time.Now().Unix() + tokenResp.ExpiresIn
	}
	if sub != "" {
		next.Sub = sub
	}
	if email != "" {
		next.Email = email
	}
	if err := next.save(); err != nil {
		return nil, fmt.Errorf("save refreshed token: %w", err)
	}
	return &next, nil
}

func loadValidTokenStore() (*tokenStore, error) {
	ts, err := loadTokenStore()
	if err != nil {
		return nil, err
	}
	if !ts.expired() {
		return ts, nil
	}
	refreshed, refreshErr := refreshTokenStore(ts)
	if refreshErr != nil {
		return ts, refreshErr
	}
	return refreshed, nil
}

func authDisplayName(email, sub string) string {
	if email != "" {
		return email
	}
	if sub != "" {
		return sub
	}
	return "(unknown)"
}

func authIdentityLine(email, sub string) string {
	return authDisplayName(email, sub)
}

// runAuth dispatches auth subcommands: login, token, whoami, logout, dids, switch
// runAuthn — AuthN namespace (authn.etzhayyim.com, T4 topology ADR-0024).
// Scope: sign-in/sign-out/session-level ops (passkey, OAuth PKCE, token, whoami, migrate).
func runAuthn(args []string) error {
	if len(args) == 0 {
		fmt.Println(`gftd authn — Authentication (authn.etzhayyim.com, OAuth2 Auth Code + PKCE)

COMMANDS:
  signin         Authenticate via browser (passkey / OAuth PKCE) — replaces 'auth login'
  signout        Remove stored credentials — replaces 'auth logout'
  revoke         Server-side token revocation (RFC 7009, ADR-2604240914 Y2)
  token          Print current access token to stdout
  whoami         Show current authentication info
  migrate        Convert legacy session-JWT store to API key store (ADR-0022)

CI/CD:
  Set GFTD_TOKEN env var (API key sk_live_* or JWT) to skip interactive signin.

Authorization / DID / API key management: see 'gftd authz'.`)
		return nil
	}
	switch args[0] {
	case "signin", "login": // login kept as alias for muscle memory
		return runAuthLogin()
	case "signout", "logout":
		return runAuthLogout()
	case "revoke":
		return runAuthRevoke(args[1:])
	case "token":
		return runAuthToken()
	case "whoami":
		return runAuthWhoami()
	case "migrate":
		return runAuthMigrate(args[1:])
	default:
		return fmt.Errorf("unknown authn command: %s (available: signin, signout, revoke, token, whoami, migrate)", args[0])
	}
}

// runAuthz — AuthZ namespace (authz.etzhayyim.com, T4 topology ADR-0024).
// Scope: DID selection, API key issuance, scope management, linked method.
func runAuthz(args []string) error {
	if len(args) == 0 {
		fmt.Println(`gftd authz — Authorization (authz.etzhayyim.com, DID / API key / scope management)

COMMANDS:
  dids              List DIDs controlled by the authenticated user
  switch <did>      Switch active DID (act as org/sub-org DID)
  switch --reset    Reset to personal DID
  create-api-key    Create a new API key (sk_live_*) for CLI/SDK access
                    --name: key name  --scopes: comma-separated (read,write,admin,seed,shinka)
                    --test: issue sk_test_* instead of sk_live_*
  list-api-keys     List active API keys
  revoke-api-key    Revoke an API key by ID

Sign-in / sign-out / session: see 'gftd authn'.`)
		return nil
	}
	switch args[0] {
	case "dids":
		return runAuthDIDs()
	case "switch":
		return runAuthSwitch(args[1:])
	case "create-api-key":
		return runAuthCreateApiKey(args[1:])
	case "list-api-keys":
		return runAuthListApiKeys()
	case "revoke-api-key":
		return runAuthRevokeApiKey(args[1:])
	default:
		return fmt.Errorf("unknown authz command: %s (available: dids, switch, create-api-key, list-api-keys, revoke-api-key)", args[0])
	}
}

// ── API Key management ──

func runAuthCreateApiKey(args []string) error {
	fs := flag.NewFlagSet("create-api-key", flag.ExitOnError)
	name := fs.String("name", "default", "key name")
	scopes := fs.String("scopes", "read,write", "comma-separated scopes")
	test := fs.Bool("test", false, "issue sk_test_ instead of sk_live_")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL")
	_ = fs.Parse(args)

	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("auth required — run 'gftd authn signin' first")
	}
	payload, _ := json.Marshal(map[string]any{"name": *name, "scopes": *scopes, "test": *test})
	req, _ := http.NewRequest("POST", *pdsURL+"/xrpc/ai.gftd.auth.createApiKey", bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("createApiKey: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("createApiKey HTTP %d: %s", resp.StatusCode, string(body))
	}
	var result struct {
		Key      string   `json:"key"`
		KeyID    string   `json:"keyId"`
		Name     string   `json:"name"`
		Scopes   []string `json:"scopes"`
		OwnerDID string   `json:"ownerDid"`
	}
	_ = json.Unmarshal(body, &result)

	fmt.Println("API Key created successfully!")
	fmt.Println()
	fmt.Printf("  Key:     %s\n", result.Key)
	fmt.Printf("  ID:      %s\n", result.KeyID)
	fmt.Printf("  Name:    %s\n", result.Name)
	fmt.Printf("  Scopes:  %s\n", strings.Join(result.Scopes, ", "))
	fmt.Printf("  Owner:   %s\n", result.OwnerDID)
	fmt.Println()
	fmt.Println("⚠ Save this key now — it cannot be retrieved again.")
	fmt.Println()
	fmt.Println("Usage:")
	fmt.Printf("  export GFTD_TOKEN=%s\n", result.Key)
	fmt.Println("  gftd seed --app sovereign")
	return nil
}

func runAuthListApiKeys() error {
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("auth required — run 'gftd authn signin' first")
	}
	req, _ := http.NewRequest("POST", defaultPDSURL+"/xrpc/ai.gftd.auth.listApiKeys", nil)
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("listApiKeys: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("listApiKeys HTTP %d: %s", resp.StatusCode, string(body))
	}
	var result struct {
		Keys []map[string]any `json:"keys"`
	}
	_ = json.Unmarshal(body, &result)
	if len(result.Keys) == 0 {
		fmt.Println("No active API keys.")
		return nil
	}
	fmt.Printf("%-20s %-20s %-30s %s\n", "ID", "NAME", "SCOPES", "PREFIX")
	for _, k := range result.Keys {
		fmt.Printf("%-20s %-20s %-30s %s\n",
			k["id"], k["name"], k["scopes"], k["prefix"])
	}
	return nil
}

func runAuthRevokeApiKey(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: gftd auth revoke-api-key <keyId>")
	}
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("auth required — run 'gftd authn signin' first")
	}
	payload, _ := json.Marshal(map[string]any{"keyId": args[0]})
	req, _ := http.NewRequest("POST", defaultPDSURL+"/xrpc/ai.gftd.auth.revokeApiKey", bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("revokeApiKey: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return fmt.Errorf("revokeApiKey HTTP %d: %s", resp.StatusCode, string(body))
	}
	fmt.Printf("API key %s revoked.\n", args[0])
	return nil
}

// runAuthLogin performs OAuth2 Auth Code + PKCE flow with localhost redirect
func runAuthLogin() error {
	// Generate PKCE code_verifier and code_challenge
	verifierBytes := make([]byte, 32)
	if _, err := rand.Read(verifierBytes); err != nil {
		return fmt.Errorf("generate PKCE verifier: %w", err)
	}
	codeVerifier := base64.RawURLEncoding.EncodeToString(verifierBytes)
	challengeHash := sha256.Sum256([]byte(codeVerifier))
	codeChallenge := base64.RawURLEncoding.EncodeToString(challengeHash[:])

	// Generate state
	stateBytes := make([]byte, 16)
	rand.Read(stateBytes)
	state := base64.RawURLEncoding.EncodeToString(stateBytes)

	redirectURI := fmt.Sprintf("http://127.0.0.1:%d/callback", authCallbackPort)

	// Build authorization URL
	params := url.Values{
		"client_id":             {authClientID},
		"redirect_uri":          {redirectURI},
		"response_type":         {"code"},
		"scope":                 {"openid profile email"},
		"state":                 {state},
		"code_challenge":        {codeChallenge},
		"code_challenge_method": {"S256"},
	}
	authURL := authAuthorizeURL + "?" + params.Encode()

	// Start local HTTP server for callback
	codeCh := make(chan string, 1)
	errCh := make(chan error, 1)

	mux := http.NewServeMux()
	mux.HandleFunc("/callback", func(w http.ResponseWriter, r *http.Request) {
		if r.URL.Query().Get("state") != state {
			http.Error(w, "Invalid state", 400)
			errCh <- fmt.Errorf("OAuth state mismatch")
			return
		}
		if errMsg := r.URL.Query().Get("error"); errMsg != "" {
			http.Error(w, errMsg, 400)
			errCh <- fmt.Errorf("OAuth error: %s: %s", errMsg, r.URL.Query().Get("error_description"))
			return
		}
		code := r.URL.Query().Get("code")
		if code == "" {
			http.Error(w, "No code", 400)
			errCh <- fmt.Errorf("no authorization code received")
			return
		}
		w.Header().Set("Content-Type", "text/html")
		fmt.Fprint(w, `<html><body><h2>✓ gftd authn signin successful</h2><p>You can close this tab.</p><script>window.close()</script></body></html>`)
		codeCh <- code
	})

	listener, err := net.Listen("tcp", fmt.Sprintf("127.0.0.1:%d", authCallbackPort))
	if err != nil {
		return fmt.Errorf("start callback server on port %d: %w", authCallbackPort, err)
	}
	server := &http.Server{Handler: mux}
	go server.Serve(listener)
	defer server.Shutdown(context.Background())

	// Open browser
	fmt.Printf("Opening browser for authentication...\n")
	fmt.Printf("If browser doesn't open, visit:\n  %s\n\n", authURL)
	openBrowser(authURL)

	// Wait for callback
	var code string
	select {
	case code = <-codeCh:
	case err := <-errCh:
		return err
	case <-time.After(120 * time.Second):
		return fmt.Errorf("authentication timed out (120s)")
	}

	// Exchange code for tokens
	tokenParams := url.Values{
		"grant_type":    {"authorization_code"},
		"client_id":     {authClientID},
		"code":          {code},
		"redirect_uri":  {redirectURI},
		"code_verifier": {codeVerifier},
	}
	resp, err := http.PostForm(authTokenURL, tokenParams)
	if err != nil {
		return fmt.Errorf("token exchange: %w", err)
	}
	defer resp.Body.Close()

	if resp.StatusCode != 200 {
		bodyBytes := make([]byte, 4096)
		n, _ := resp.Body.Read(bodyBytes)
		return fmt.Errorf("token exchange failed: %s %s", resp.Status, string(bodyBytes[:n]))
	}

	var tokenResp struct {
		AccessToken  string `json:"access_token"`
		RefreshToken string `json:"refresh_token"`
		ExpiresIn    int64  `json:"expires_in"`
		TokenType    string `json:"token_type"`
		IDToken      string `json:"id_token"`
		APIKey       string `json:"api_key"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&tokenResp); err != nil {
		return fmt.Errorf("parse token response: %w", err)
	}

	// auth.etzhayyim.com returns AT Protocol JWT as both access_token and id_token.
	bearerToken := tokenResp.IDToken
	if bearerToken == "" {
		bearerToken = tokenResp.AccessToken // fallback
	}

	sub, email := parseJWTClaims(bearerToken)

	// ADR-0022 bootstrap: auth.etzhayyim.com now mints sk_live_* server-side in /oauth/token
	// (via PDS service binding with internal trust). Prefer that key; fall back to
	// the legacy round-trip exchangeSessionForAPIKey for older auth Workers.
	apiKey := tokenResp.APIKey
	var apiKeyErr error
	if apiKey == "" {
		apiKey, apiKeyErr = exchangeSessionForAPIKey(bearerToken, "gftd-cli-login")
	}

	ts := &tokenStore{
		Sub:   sub,
		Email: email,
	}
	if apiKey != "" {
		ts.APIKey = apiKey
	} else {
		// createApiKey unavailable (offline / older PDS) — fall back to storing
		// the session JWT so login still works; `gftd auth migrate` can complete
		// the conversion later.
		ts.AccessToken = bearerToken
		ts.IDToken = tokenResp.IDToken
		ts.RefreshToken = tokenResp.RefreshToken
		ts.ExpiresAt = time.Now().Unix() + tokenResp.ExpiresIn
	}
	if err := ts.save(); err != nil {
		return fmt.Errorf("save token: %w", err)
	}

	fmt.Printf("✓ Authenticated as %s (%s)\n", authDisplayName(email, sub), sub)
	if apiKey != "" {
		fmt.Printf("  API key issued and stored in %s\n", authFile())
	} else {
		fmt.Printf("  Session token stored in %s\n", authFile())
		if apiKeyErr != nil {
			fmt.Fprintf(os.Stderr, "  note: API key issuance deferred (%v). Run 'gftd auth migrate' later.\n", apiKeyErr)
		}
	}
	return nil
}

// exchangeSessionForAPIKey issues a long-lived sk_live_* API key using a freshly
// obtained session JWT. Returns ("", nil) when the PDS endpoint is unreachable
// so callers can fall back to storing the JWT itself.
func exchangeSessionForAPIKey(sessionJWT, name string) (string, error) {
	payload, _ := json.Marshal(map[string]any{
		"name":   name,
		"scopes": "read,write",
	})
	req, _ := http.NewRequest("POST", defaultPDSURL+"/xrpc/ai.gftd.auth.createApiKey", bytes.NewReader(payload))
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+sessionJWT)
	client := &http.Client{Timeout: 15 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", fmt.Errorf("createApiKey network error: %w", err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(resp.Body)
	if resp.StatusCode >= 400 {
		return "", fmt.Errorf("createApiKey HTTP %d: %s", resp.StatusCode, string(body))
	}
	var result struct {
		Key string `json:"key"`
	}
	if err := json.Unmarshal(body, &result); err != nil || result.Key == "" {
		return "", fmt.Errorf("createApiKey: empty key in response")
	}
	return result.Key, nil
}

// runAuthMigrate converts a legacy session-JWT store to an API-key store.
// ADR-0022 step 5 migration entry point for existing `~/.gftd/auth.json` files.
func runAuthMigrate(args []string) error {
	fs := flag.NewFlagSet("migrate", flag.ContinueOnError)
	keyName := fs.String("name", "gftd-cli-migrated", "API key name")
	dryRun := fs.Bool("dry-run", false, "print what would change without writing")
	if err := fs.Parse(args); err != nil {
		return err
	}
	ts, err := loadTokenStore()
	if err != nil {
		return fmt.Errorf("no token store found — run 'gftd authn signin' first: %w", err)
	}
	if ts.APIKey != "" {
		fmt.Println("✓ Already migrated (APIKey is set). No action needed.")
		return nil
	}
	sessionJWT := bearerFromStore(ts)
	if sessionJWT == "" {
		return fmt.Errorf("no legacy session token found to migrate")
	}
	if *dryRun {
		fmt.Printf("Would: POST %s/xrpc/ai.gftd.auth.createApiKey (name=%s) using stored session JWT.\n", defaultPDSURL, *keyName)
		fmt.Printf("Would: overwrite %s with { api_key, sub, email, active_did } only.\n", authFile())
		return nil
	}
	apiKey, err := exchangeSessionForAPIKey(sessionJWT, *keyName)
	if err != nil {
		return fmt.Errorf("migrate: %w", err)
	}
	next := &tokenStore{
		APIKey:    apiKey,
		Sub:       ts.Sub,
		Email:     ts.Email,
		ActiveDID: ts.ActiveDID,
	}
	if err := next.save(); err != nil {
		return fmt.Errorf("save migrated store: %w", err)
	}
	fmt.Printf("✓ Migrated to API key (%s...).\n", truncStr(apiKey, 18))
	fmt.Printf("  Legacy access_token / id_token / refresh_token cleared from %s\n", authFile())
	return nil
}

// runAuthToken prints the current access token to stdout

// runAuthToken prints the current access token to stdout
func runAuthToken() error {
	// Check env var first
	if token := os.Getenv("GFTD_TOKEN"); token != "" {
		fmt.Print(token)
		return nil
	}

	ts, err := loadValidTokenStore()
	if err != nil {
		return fmt.Errorf("not authenticated. Run 'gftd authn signin' first")
	}
	if ts.expired() {
		return fmt.Errorf("token expired. Run 'gftd authn signin' to re-authenticate")
	}
	fmt.Print(bearerFromStore(ts))
	return nil
}

// runAuthWhoami shows current auth info
func runAuthWhoami() error {
	if token := os.Getenv("GFTD_TOKEN"); token != "" {
		sub, email := parseJWTClaims(token)
		fmt.Printf("Source:  GFTD_TOKEN env var\n")
		fmt.Printf("Sub:     %s\n", sub)
		fmt.Printf("Identity:%s%s\n", strings.Repeat(" ", 3), authIdentityLine(email, sub))
		return nil
	}

	ts, err := loadValidTokenStore()
	if err != nil {
		return fmt.Errorf("not authenticated. Run 'gftd authn signin' first")
	}

	fmt.Printf("Source:     %s\n", authFile())
	fmt.Printf("Sub:        %s\n", ts.Sub)
	fmt.Printf("Identity:   %s\n", authIdentityLine(ts.Email, ts.Sub))
	if ts.ActiveDID != "" && ts.ActiveDID != ts.Sub {
		fmt.Printf("Active DID: %s\n", ts.ActiveDID)
	} else {
		fmt.Printf("Active DID: %s (personal)\n", ts.Sub)
	}
	if ts.ExpiresAt > 0 {
		remaining := time.Until(time.Unix(ts.ExpiresAt, 0))
		if remaining > 0 {
			fmt.Printf("Expires:    %s (in %s)\n", time.Unix(ts.ExpiresAt, 0).Format(time.RFC3339), remaining.Round(time.Second))
		} else {
			fmt.Printf("Expires:    EXPIRED\n")
		}
	}
	return nil
}

// runAuthLogout removes stored credentials (file + Keychain)
func runAuthLogout() error {
	if err := os.Remove(authFile()); err != nil && !os.IsNotExist(err) {
		return err
	}
	deleteFromKeychain("api_key")
	deleteFromKeychain("access_token")
	fmt.Println("✓ Logged out. Credentials removed.")
	return nil
}

// runAuthRevoke — server-side token revocation (RFC 7009 via /oauth/revoke).
//
// Default: revokes the access_token + refresh_token found in
// ~/.gftd/auth.json, then clears the local store (same as logout).
// --token <jwt> : revoke a specific token only; local store untouched.
// --keep-local  : call server-side revoke but keep the local store.
//
// POSTs application/x-www-form-urlencoded to
// ${PDS_URL}/oauth/revoke with {token, token_type_hint?}. The endpoint
// returns 200 for both success and unknown tokens per RFC 7009 §2.2 — a
// non-200 response here means the PDS is unreachable, not that the
// token was "bad".
func runAuthRevoke(args []string) error {
	fs := flag.NewFlagSet("revoke", flag.ExitOnError)
	explicitToken := fs.String("token", "", "revoke this specific token (JWT / sk_* key); when set, ignore the local store")
	pdsURL := fs.String("pds", defaultPDSURL, "PDS base URL hosting /oauth/revoke")
	keepLocal := fs.Bool("keep-local", false, "do not delete ~/.gftd/auth.json after server-side revoke")
	quiet := fs.Bool("q", false, "suppress per-token confirmation output")
	_ = fs.Parse(args)

	type revokeTarget struct {
		Token string
		Hint  string // "access_token" | "refresh_token" | ""
		Label string // user-facing description
	}
	var targets []revokeTarget

	if *explicitToken != "" {
		targets = append(targets, revokeTarget{Token: *explicitToken, Label: "--token argument"})
	} else {
		ts, err := loadTokenStore()
		if err != nil || ts == nil {
			return fmt.Errorf("no stored credentials — run 'gftd authn signin' or pass --token <jwt>")
		}
		// Prefer revoking AT Protocol session tokens. API keys (sk_*) are
		// revoked via `gftd authz revoke-api-key` — don't send them to
		// /oauth/revoke, that endpoint expects a JWT.
		if ts.AccessToken != "" {
			targets = append(targets, revokeTarget{
				Token: ts.AccessToken, Hint: "access_token", Label: "access_token",
			})
		}
		if ts.RefreshToken != "" {
			targets = append(targets, revokeTarget{
				Token: ts.RefreshToken, Hint: "refresh_token", Label: "refresh_token",
			})
		}
		if ts.IDToken != "" && ts.IDToken != ts.AccessToken {
			targets = append(targets, revokeTarget{
				Token: ts.IDToken, Hint: "access_token", Label: "id_token",
			})
		}
		if len(targets) == 0 {
			if ts.APIKey != "" {
				return fmt.Errorf("local store has only an API key (sk_*) — use 'gftd authz revoke-api-key' for api_key lifecycle")
			}
			return fmt.Errorf("no revocable tokens found in local store")
		}
	}

	revokeURL := strings.TrimRight(*pdsURL, "/") + "/oauth/revoke"
	errs := 0
	for _, t := range targets {
		form := url.Values{}
		form.Set("token", t.Token)
		if t.Hint != "" {
			form.Set("token_type_hint", t.Hint)
		}
		req, err := http.NewRequest("POST", revokeURL, strings.NewReader(form.Encode()))
		if err != nil {
			return fmt.Errorf("build revoke request: %w", err)
		}
		req.Header.Set("Content-Type", "application/x-www-form-urlencoded")
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			errs++
			fmt.Fprintf(os.Stderr, "✘ %s: POST /oauth/revoke failed: %v\n", t.Label, err)
			continue
		}
		// RFC 7009 §2.2: 200 for both success and unknown tokens. Anything
		// else is an RS-level problem (network / 5xx) the user should see.
		body, _ := io.ReadAll(resp.Body)
		_ = resp.Body.Close()
		if resp.StatusCode != 200 {
			errs++
			fmt.Fprintf(os.Stderr, "✘ %s: status=%d body=%s\n", t.Label, resp.StatusCode, strings.TrimSpace(string(body)))
			continue
		}
		if !*quiet {
			fmt.Printf("✓ %s revoked (server ack)\n", t.Label)
		}
	}

	if errs > 0 {
		return fmt.Errorf("%d/%d revoke calls failed", errs, len(targets))
	}

	// Server said 200 for everything. Clear the local store so a subsequent
	// gftd command doesn't silently reuse the now-revoked JWT.
	if *explicitToken == "" && !*keepLocal {
		if err := os.Remove(authFile()); err != nil && !os.IsNotExist(err) {
			return fmt.Errorf("local store cleanup: %w", err)
		}
		deleteFromKeychain("access_token")
		if !*quiet {
			fmt.Println("✓ Local credential store cleared.")
		}
	}
	return nil
}

// queryControlledDIDs queries RisingWave for DIDs controlled by the given DID.
func queryControlledDIDs(token string) ([]controlledDID, error) {
	sub, _ := parseJWTClaims(token)
	if sub == "" {
		return nil, fmt.Errorf("cannot extract DID from token")
	}
	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()
	result, err := db.RawQuery(ctx, `
		SELECT did, performer_type AS type, COALESCE(status, 'active') AS status
		FROM vertex_diddocument
		WHERE controller = $1
		  AND did IS NOT NULL
		ORDER BY did
		LIMIT 100
	`, sub)
	if err != nil {
		return nil, err
	}

	var dids []controlledDID
	for _, row := range result.Rows {
		did := fmt.Sprintf("%v", row["did"])
		ptype := fmt.Sprintf("%v", row["type"])
		status := fmt.Sprintf("%v", row["status"])
		if did == "<nil>" {
			did = ""
		}
		if ptype == "<nil>" {
			ptype = ""
		}
		if status == "<nil>" || status == "" {
			status = "active"
		}
		if did != "" {
			dids = append(dids, controlledDID{DID: did, PerformerType: ptype, Status: status})
		}
	}
	return dids, nil
}

type controlledDID struct {
	DID           string `json:"did"`
	PerformerType string `json:"performer_type"`
	Status        string `json:"status"`
}

// runAuthDIDs lists DIDs controlled by the authenticated user
func runAuthDIDs() error {
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("not authenticated. Run 'gftd authn signin' first")
	}

	sub, _ := parseJWTClaims(token)
	fmt.Printf("DIDs controlled by %s:\n\n", sub)

	dids, err := queryControlledDIDs(token)
	if err != nil {
		// Degrade gracefully when PDS graph query is temporarily unavailable.
		if sub != "" {
			fmt.Fprintf(os.Stderr, "warning: controlled DID query failed: %v\n", err)
			fmt.Fprintln(os.Stderr, "         falling back to token subject only")
			dids = []controlledDID{{DID: sub, PerformerType: "user", Status: "active"}}
		} else {
			return err
		}
	}

	if len(dids) == 0 {
		fmt.Println("  (none)")
		return nil
	}

	for _, d := range dids {
		status := ""
		if d.Status != "" && d.Status != "active" {
			status = fmt.Sprintf(" [%s]", d.Status)
		}
		ptype := ""
		if d.PerformerType != "" {
			ptype = fmt.Sprintf(" (%s)", d.PerformerType)
		}
		fmt.Printf("  %s%s%s\n", d.DID, ptype, status)
	}
	return nil
}

// runAuthSwitch switches the active DID
func runAuthSwitch(args []string) error {
	ts, err := loadValidTokenStore()
	if err != nil {
		return fmt.Errorf("not authenticated. Run 'gftd authn signin' first")
	}
	if ts.expired() {
		return fmt.Errorf("token expired. Run 'gftd authn signin' to re-authenticate")
	}

	// --reset: clear active DID, revert to personal DID
	if len(args) > 0 && args[0] == "--reset" {
		ts.ActiveDID = ""
		if err := ts.save(); err != nil {
			return fmt.Errorf("save: %w", err)
		}
		fmt.Printf("✓ Switched back to personal DID: %s\n", ts.Sub)
		return nil
	}

	if len(args) == 0 {
		return fmt.Errorf("usage: gftd auth switch <did> | --reset")
	}

	targetDID := args[0]
	if !strings.HasPrefix(targetDID, "did:") {
		// Handle shorthand: "moj" → "did:web:moj.etzhayyim.com"
		if !strings.Contains(targetDID, ".") {
			targetDID = "did:web:" + targetDID + ".etzhayyim.com"
		} else {
			targetDID = "did:web:" + targetDID
		}
	}

	// Switching to own DID = reset
	if targetDID == ts.Sub {
		ts.ActiveDID = ""
		if err := ts.save(); err != nil {
			return fmt.Errorf("save: %w", err)
		}
		fmt.Printf("✓ Switched to personal DID: %s\n", ts.Sub)
		return nil
	}

	// Verify the user controls this DID
	token := resolveGFTDToken()
	dids, err := queryControlledDIDs(token)
	if err != nil {
		return fmt.Errorf("verify DID control: %w", err)
	}

	found := false
	for _, d := range dids {
		if d.DID == targetDID {
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("DID %s is not controlled by %s\n  Run 'gftd auth dids' to see available DIDs", targetDID, ts.Sub)
	}

	ts.ActiveDID = targetDID
	if err := ts.save(); err != nil {
		return fmt.Errorf("save: %w", err)
	}
	fmt.Printf("✓ Switched to DID: %s\n", targetDID)
	return nil
}

// resolveGFTDToken returns the best available auth token for PDS API calls.
// Priority: GFTD_TOKEN env > Keychain api_key > ~/.gftd/auth.json
func resolveGFTDToken() string {
	if token := os.Getenv("GFTD_TOKEN"); token != "" {
		return token
	}
	// Prefer Keychain API key (sk_live_* never expires)
	if key, err := readFromKeychain("api_key"); err == nil && key != "" {
		return key
	}
	if ts, err := loadValidTokenStore(); err == nil && !ts.expired() {
		return bearerFromStore(ts)
	}
	return ""
}

// resolveActiveDID returns the active DID (switched org DID or personal DID)
func resolveActiveDID() string {
	if ts, err := loadValidTokenStore(); err == nil && !ts.expired() {
		if ts.ActiveDID != "" {
			return ts.ActiveDID
		}
		return ts.Sub
	}
	return ""
}

// setAuthHeaders sets Authorization + X-Active-DID headers on a PDS API request.
//
// ADR-0022 step 2: when the request targets an XRPC endpoint (path contains
// /xrpc/{nsid}), the base token is wrapped into a short-lived ES256 Service
// Auth JWT scoped via `lxm = <nsid>` (see scoped_auth.go). Falls back to the
// base token when NSID cannot be derived, when the NSID is getServiceAuth
// itself (bootstrap), or when minting fails. Controlled by GFTD_SCOPED_AUTH
// (set to "off" to disable).
func setAuthHeaders(req *http.Request) {
	base := resolveGFTDToken()
	if base != "" {
		outgoing := base
		if scopedAuthEnabled() {
			if nsid := nsidFromURLPath(req.URL); nsid != "" {
				if scoped := mintScopedJWT(base, nsid); scoped != "" {
					outgoing = scoped
				}
			}
		}
		req.Header.Set("Authorization", "Bearer "+outgoing)
	}
	if did := resolveActiveDID(); did != "" {
		req.Header.Set("X-Active-DID", did)
	}
	if org := resolveOrgHint(); org != "" {
		req.Header.Set("X-Gftd-Org-Id", org)
	}
}

func resolveOrgHint() string {
	if org := strings.TrimSpace(os.Getenv("GFTD_ORG_ID")); org != "" {
		return org
	}
	return inferOrgFromActiveDID(resolveActiveDID())
}

func resolvePDSBaseURL() string {
	return strings.TrimRight(envOr("GFTD_PDS_URL", defaultPDSURL), "/")
}

// parseJWTClaims extracts sub and email from a JWT without verification
func parseJWTClaims(token string) (sub, email string) {
	parts := strings.Split(token, ".")
	if len(parts) != 3 {
		return "", ""
	}
	payload := parts[1]
	// Add padding
	switch len(payload) % 4 {
	case 2:
		payload += "=="
	case 3:
		payload += "="
	}
	data, err := base64.URLEncoding.DecodeString(payload)
	if err != nil {
		return "", ""
	}
	var claims struct {
		Sub   string `json:"sub"`
		Email string `json:"email"`
	}
	json.Unmarshal(data, &claims)
	return claims.Sub, claims.Email
}

func openBrowser(url string) {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", url)
	case "linux":
		cmd = exec.Command("xdg-open", url)
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", url)
	}
	if cmd != nil {
		cmd.Start()
	}
}
