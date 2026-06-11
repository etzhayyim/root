package main

// `e7m capability` — consent capability lifecycle (issue / verify / revoke / list).
//
// Per ADR-2605231400 (consent capability) + ADR-2605232000 (deploy-execution
// purpose extension). A capability is an Ed25519-signed delegation token
// stored as an AT Protocol record (`com.etzhayyim.consent.capability`) in the
// granter's PDS. This CLI wraps:
//
//   issue   — canonicalize, sign with granter's Ed25519 key, return JWS (or
//             write to file). The CLI does NOT write to the granter's PDS
//             directly in v1 — that's the responsibility of a downstream
//             tool that has PDS credentials. The JWS itself is verifiable
//             standalone.
//
//   verify  — decode + Ed25519-verify a JWS against the granter's DID
//             document (resolved via https://<granter-domain>/.well-known/did.json).
//
//   revoke  — produces a revocation record body (call site forwards to PDS).
//
//   list    — calls com.etzhayyim.apps.karute.listConsent (or generic equivalent
//             at the substrate-wide audit subject) and pretty-prints.

import (
	"bytes"
	"context"
	"crypto/ed25519"
	"encoding/base64"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"sort"
	"strings"
	"time"
)

const auditAggregatorEndpoint = "https://audit.etzhayyim.com/xrpc/com.etzhayyim.audit.emitAuditEvent"

type capabilityPayload struct {
	Version      int      `json:"version"`
	GranterDid   string   `json:"granterDid"`
	GranteeDid   string   `json:"granteeDid"`
	Purpose      string   `json:"purpose"`
	Scope        []string `json:"scope"`
	ResourceUris []string `json:"resourceUris,omitempty"`
	IssuedAt     string   `json:"issuedAt"`
	ExpiresAt    string   `json:"expiresAt"`
	Constraints  *capabilityConstraints `json:"constraints,omitempty"`
	RevokedAt    string   `json:"revokedAt,omitempty"`
	RevokedBy    string   `json:"revokedBy,omitempty"`
	CapabilityUri string  `json:"capabilityUri,omitempty"`
}

type capabilityConstraints struct {
	MaxQueriesPerDay         int    `json:"maxQueriesPerDay,omitempty"`
	RedactionLevel           string `json:"redactionLevel,omitempty"`
	DownstreamRedistribution *bool  `json:"downstreamRedistribution,omitempty"`
	AuditWebhookDid          string `json:"auditWebhookDid,omitempty"`
}

func runCapability(args []string) error {
	if len(args) == 0 {
		printCapabilityUsage()
		return nil
	}
	switch args[0] {
	case "issue":
		return runCapabilityIssue(args[1:])
	case "verify":
		return runCapabilityVerify(args[1:])
	case "revoke":
		return runCapabilityRevoke(args[1:])
	case "list":
		return runCapabilityList(args[1:])
	case "help", "--help", "-h":
		printCapabilityUsage()
		return nil
	default:
		return fmt.Errorf("unknown capability subcommand: %s", args[0])
	}
}

func printCapabilityUsage() {
	fmt.Printf(`etzhayyim capability — consent capability lifecycle

USAGE:
  etzhayyim capability <subcommand> [flags]

SUBCOMMANDS:
  issue    Sign a new capability JWS (no PDS write; caller forwards to PDS)
  verify   Ed25519-verify a JWS against the granter's DID document
  revoke   Produce a revocation record body
  list     List capabilities (calls com.etzhayyim.apps.karute.listConsent or equivalent)

ISSUE FLAGS:
  --granter <did>           granter DID (Steward); default $ETZ_STEWARD_DID
  --grantee <did>           grantee DID (agent); default $ETZ_AGENT_DID
  --purpose <enum>          insurance-billing | second-opinion | data-portability |
                            research-deidentified | emergency-disclosure |
                            legal-disclosure | deploy-execution
  --scope <csv>             comma-separated scope NSIDs
  --ttl <seconds>           lifetime (max 31536000 = 1 year)
  --expires-at <RFC3339>    explicit expiry (overrides --ttl)
  --resource-uris <csv>     optional explicit AT URI allowlist
  --audit-webhook <did>     constraints.auditWebhookDid
  --keychain-service <s>    macOS Keychain service (default: etzhayyim)
  --keychain-account <a>    macOS Keychain account (default: DID_PRIVATE_KEY_ED25519)
  --key-file <path>         alt: raw 32-byte Ed25519 private key
  --out <path>              JWS output (- for stdout)
  --out-payload <path>      separately dump canonical JSON payload (debug)

VERIFY FLAGS:
  --capability <path>       JWS file
  --offline                 do not resolve granter DID — only structural check
  --pubkey <hex>            inline public key (64 hex chars) bypasses DID resolution
  --did-document <path>     local DID document to use instead of HTTPS resolution
  --now <RFC3339>           clock override for expiry check (default: now)

EXAMPLES:
  # Issue a 24h deploy capability
  etzhayyim capability issue \
    --granter did:web:steward.etzhayyim.com \
    --grantee did:web:claude-agent.etzhayyim.com \
    --purpose deploy-execution \
    --scope deploy.cfWorker:karute-did-web,deploy.k8s:lg-karute,deploy.pages:karute \
    --ttl 86400 \
    --audit-webhook did:web:audit.etzhayyim.com \
    --out ~/.etzhayyim/cap-karute.jws

  # Verify locally (no network)
  etzhayyim capability verify --capability ~/.etzhayyim/cap-karute.jws \
    --did-document /path/to/steward-did.json

  # Verify against live DID Web
  etzhayyim capability verify --capability ~/.etzhayyim/cap-karute.jws
`)
}

// ── issue ─────────────────────────────────────────────────────────────

func runCapabilityIssue(args []string) error {
	fs := flag.NewFlagSet("capability issue", flag.ContinueOnError)
	granter := fs.String("granter", "", "granter DID (default $ETZ_STEWARD_DID)")
	grantee := fs.String("grantee", "", "grantee DID (default $ETZ_AGENT_DID)")
	purpose := fs.String("purpose", "", "purpose enum value")
	scopeCSV := fs.String("scope", "", "comma-separated scope NSIDs")
	ttl := fs.Int("ttl", 86400, "lifetime in seconds (default 24h, max 1y)")
	expiresAt := fs.String("expires-at", "", "explicit RFC3339 expiry (overrides --ttl)")
	resourceCSV := fs.String("resource-uris", "", "comma-separated AT URIs")
	auditWebhook := fs.String("audit-webhook", "did:web:audit.etzhayyim.com", "constraints.auditWebhookDid")
	keychainService := fs.String("keychain-service", "etzhayyim", "")
	keychainAccount := fs.String("keychain-account", "DID_PRIVATE_KEY_ED25519", "")
	keyFile := fs.String("key-file", "", "")
	out := fs.String("out", "-", "")
	outPayload := fs.String("out-payload", "", "")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printCapabilityUsage()
			return nil
		}
		return err
	}

	g := *granter
	if g == "" {
		g = os.Getenv("ETZ_STEWARD_DID")
	}
	if g == "" {
		return fmt.Errorf("--granter or $ETZ_STEWARD_DID required")
	}
	gt := *grantee
	if gt == "" {
		gt = os.Getenv("ETZ_AGENT_DID")
	}
	if gt == "" {
		return fmt.Errorf("--grantee or $ETZ_AGENT_DID required")
	}
	if *purpose == "" {
		return fmt.Errorf("--purpose required (one of: insurance-billing, second-opinion, data-portability, research-deidentified, emergency-disclosure, legal-disclosure, deploy-execution)")
	}
	allowedPurposes := map[string]bool{
		"insurance-billing":      true,
		"second-opinion":         true,
		"data-portability":       true,
		"research-deidentified":  true,
		"emergency-disclosure":   true,
		"legal-disclosure":       true,
		"deploy-execution":       true,
	}
	if !allowedPurposes[*purpose] {
		return fmt.Errorf("invalid --purpose %q", *purpose)
	}
	if *scopeCSV == "" {
		return fmt.Errorf("--scope required (comma-separated NSIDs)")
	}
	if *ttl > 31536000 {
		return fmt.Errorf("--ttl exceeds 1y (got %d)", *ttl)
	}

	scope := splitCSV(*scopeCSV)
	resources := splitCSV(*resourceCSV)
	now := time.Now().UTC()
	exp := now.Add(time.Duration(*ttl) * time.Second).Format(time.RFC3339)
	if *expiresAt != "" {
		exp = *expiresAt
	}

	payload := &capabilityPayload{
		Version:    1,
		GranterDid: g,
		GranteeDid: gt,
		Purpose:    *purpose,
		Scope:      scope,
		IssuedAt:   now.Format(time.RFC3339),
		ExpiresAt:  exp,
	}
	if len(resources) > 0 {
		payload.ResourceUris = resources
	}
	if *auditWebhook != "" {
		payload.Constraints = &capabilityConstraints{AuditWebhookDid: *auditWebhook}
	}

	priv, err := loadEd25519PrivateKey(*keychainService, *keychainAccount, *keyFile)
	if err != nil {
		return err
	}

	// JWS payload = canonicalized JSON
	pjson, err := canonicalJSON(payload)
	if err != nil {
		return err
	}
	if *outPayload != "" {
		if err := os.WriteFile(*outPayload, pjson, 0o600); err != nil {
			return err
		}
	}

	header := map[string]any{"alg": "EdDSA", "typ": "JWT", "kid": g + "#key-0"}
	hb, _ := json.Marshal(header)
	signingInput := base64.RawURLEncoding.EncodeToString(hb) + "." + base64.RawURLEncoding.EncodeToString(pjson)
	sig := ed25519.Sign(priv, []byte(signingInput))
	jws := signingInput + "." + base64.RawURLEncoding.EncodeToString(sig)

	if *out == "-" {
		fmt.Println(jws)
	} else {
		if err := os.WriteFile(*out, []byte(jws+"\n"), 0o600); err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "wrote capability JWS to %s (TTL %ds, expires %s)\n", *out, *ttl, exp)
	}
	return nil
}

// ── verify ────────────────────────────────────────────────────────────

type verifyResult struct {
	Valid       bool
	StructureOk bool
	SignatureOk bool
	NotExpired  bool
	Reason      string
	Payload     *capabilityPayload
}

func runCapabilityVerify(args []string) error {
	fs := flag.NewFlagSet("capability verify", flag.ContinueOnError)
	capPath := fs.String("capability", "", "JWS file (required)")
	offline := fs.Bool("offline", false, "do not resolve granter DID")
	pubkeyHex := fs.String("pubkey", "", "inline Ed25519 public key (64 hex chars)")
	didDocPath := fs.String("did-document", "", "local DID document JSON")
	nowStr := fs.String("now", "", "clock override RFC3339")
	jsonOut := fs.Bool("json", false, "machine-readable JSON output")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printCapabilityUsage()
			return nil
		}
		return err
	}
	if *capPath == "" {
		return fmt.Errorf("--capability <path> required")
	}
	raw, err := os.ReadFile(*capPath)
	if err != nil {
		return err
	}
	now := time.Now().UTC()
	if *nowStr != "" {
		now, err = time.Parse(time.RFC3339, *nowStr)
		if err != nil {
			return fmt.Errorf("--now: %w", err)
		}
	}

	var pubkey ed25519.PublicKey
	if *pubkeyHex != "" {
		b, err := hex.DecodeString(*pubkeyHex)
		if err != nil || len(b) != ed25519.PublicKeySize {
			return fmt.Errorf("--pubkey: want 64 hex chars (got %d bytes)", len(b))
		}
		pubkey = ed25519.PublicKey(b)
	}

	res := verifyJWS(strings.TrimSpace(string(raw)), now, &verifyOpts{
		offline:       *offline,
		pubkey:        pubkey,
		didDocLocal:   *didDocPath,
	})

	if *jsonOut {
		b, _ := json.MarshalIndent(res, "", "  ")
		fmt.Println(string(b))
	} else {
		if res.Valid {
			fmt.Printf("✓ capability valid\n  granter:  %s\n  grantee:  %s\n  purpose:  %s\n  scope:    %v\n  expires:  %s\n",
				res.Payload.GranterDid, res.Payload.GranteeDid, res.Payload.Purpose, res.Payload.Scope, res.Payload.ExpiresAt)
		} else {
			fmt.Printf("✘ capability INVALID — %s\n", res.Reason)
		}
	}
	if !res.Valid {
		os.Exit(2)
	}
	return nil
}

type verifyOpts struct {
	offline     bool
	pubkey      ed25519.PublicKey
	didDocLocal string
}

func verifyJWS(jws string, now time.Time, opt *verifyOpts) *verifyResult {
	if opt == nil {
		opt = &verifyOpts{}
	}
	parts := strings.Split(jws, ".")
	if len(parts) != 3 {
		return &verifyResult{Reason: "not a JWS (3 base64url parts expected)"}
	}
	payloadBytes, err := base64.RawURLEncoding.DecodeString(parts[1])
	if err != nil {
		return &verifyResult{Reason: "payload base64 decode: " + err.Error()}
	}
	payload := &capabilityPayload{}
	if err := json.Unmarshal(payloadBytes, payload); err != nil {
		return &verifyResult{Reason: "payload JSON parse: " + err.Error()}
	}
	res := &verifyResult{Payload: payload, StructureOk: true}

	// Expiry
	if payload.ExpiresAt != "" {
		exp, err := time.Parse(time.RFC3339, payload.ExpiresAt)
		if err != nil {
			res.Reason = "expiresAt parse: " + err.Error()
			return res
		}
		if now.After(exp) {
			res.Reason = fmt.Sprintf("expired (now=%s > expiresAt=%s)", now.Format(time.RFC3339), payload.ExpiresAt)
			return res
		}
	}
	if payload.RevokedAt != "" {
		res.Reason = "revoked at " + payload.RevokedAt
		return res
	}
	res.NotExpired = true

	// Signature
	pubkey := opt.pubkey
	if pubkey == nil && !opt.offline {
		// Resolve from DID document
		dd, err := resolveDidDocument(payload.GranterDid, opt.didDocLocal)
		if err != nil {
			res.Reason = "DID resolution: " + err.Error()
			return res
		}
		pubkey, err = extractEd25519PubkeyFromDoc(dd)
		if err != nil {
			res.Reason = "pubkey extraction: " + err.Error()
			return res
		}
	}
	if pubkey == nil {
		// offline + no inline pubkey → structural check only
		res.Reason = "offline mode: signature unverified"
		res.Valid = false
		return res
	}
	signingInput := parts[0] + "." + parts[1]
	sig, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil {
		res.Reason = "signature base64 decode: " + err.Error()
		return res
	}
	if !ed25519.Verify(pubkey, []byte(signingInput), sig) {
		res.Reason = "Ed25519 signature verification failed"
		return res
	}
	res.SignatureOk = true
	res.Valid = true
	return res
}

// resolveDidDocument fetches a did:web document via HTTPS, or reads from a
// local file when didDocLocal is non-empty.
func resolveDidDocument(did, local string) (map[string]any, error) {
	if local != "" {
		raw, err := os.ReadFile(local)
		if err != nil {
			return nil, err
		}
		doc := map[string]any{}
		if err := json.Unmarshal(raw, &doc); err != nil {
			return nil, err
		}
		return doc, nil
	}
	if !strings.HasPrefix(did, "did:web:") {
		return nil, fmt.Errorf("only did:web is supported for online resolution (got %q)", did)
	}
	// did:web:karute.etzhayyim.com → https://karute.etzhayyim.com/.well-known/did.json
	// did:web:etzhayyim.com:actor:foo → https://etzhayyim.com/actor/foo/did.json
	host := strings.TrimPrefix(did, "did:web:")
	host = strings.ReplaceAll(host, ":", "/")
	endpoint := "https://" + host
	if !strings.HasSuffix(endpoint, "/did.json") {
		endpoint += "/.well-known/did.json"
	}
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, "GET", endpoint, nil)
	req.Header.Set("accept", "application/did+json, application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("GET %s: %w", endpoint, err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		return nil, fmt.Errorf("GET %s: HTTP %d", endpoint, resp.StatusCode)
	}
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 256*1024))
	doc := map[string]any{}
	if err := json.Unmarshal(body, &doc); err != nil {
		return nil, fmt.Errorf("parse %s: %w", endpoint, err)
	}
	return doc, nil
}

// extractEd25519PubkeyFromDoc walks the DID document looking for the first
// JsonWebKey2020 or Ed25519VerificationKey2020 with curve Ed25519. Returns the
// raw 32-byte public key.
func extractEd25519PubkeyFromDoc(doc map[string]any) (ed25519.PublicKey, error) {
	vm, ok := doc["verificationMethod"].([]any)
	if !ok {
		return nil, fmt.Errorf("DID document missing verificationMethod[]")
	}
	for _, raw := range vm {
		m, ok := raw.(map[string]any)
		if !ok {
			continue
		}
		// JsonWebKey2020 with OKP / Ed25519 / x
		if jwk, ok := m["publicKeyJwk"].(map[string]any); ok {
			if jwk["kty"] == "OKP" && jwk["crv"] == "Ed25519" {
				if x, ok := jwk["x"].(string); ok {
					b, err := base64.RawURLEncoding.DecodeString(x)
					if err == nil && len(b) == ed25519.PublicKeySize {
						return ed25519.PublicKey(b), nil
					}
				}
			}
		}
		// Ed25519VerificationKey2020 + publicKeyMultibase
		if mb, ok := m["publicKeyMultibase"].(string); ok && strings.HasPrefix(mb, "z") {
			b, err := decodeBase58btc(mb[1:])
			if err == nil && len(b) >= 34 && b[0] == 0xed && b[1] == 0x01 {
				return ed25519.PublicKey(b[2:34]), nil
			}
		}
	}
	return nil, fmt.Errorf("no Ed25519 verification method found in DID document")
}

// ── revoke ────────────────────────────────────────────────────────────

func runCapabilityRevoke(args []string) error {
	fs := flag.NewFlagSet("capability revoke", flag.ContinueOnError)
	capUri := fs.String("capability-uri", "", "AT URI of the capability to revoke (required)")
	reason := fs.String("reason", "", "free-text revocation reason")
	revokedBy := fs.String("revoked-by", "", "DID of revoker (default $ETZ_STEWARD_DID)")
	out := fs.String("out", "-", "output revocation record body (- for stdout)")
	pdsXrpc := fs.String("pds-xrpc", "", "if set, POST to <url>/xrpc/com.etzhayyim.apps.karute.revokeConsent")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printCapabilityUsage()
			return nil
		}
		return err
	}
	if *capUri == "" {
		return fmt.Errorf("--capability-uri required")
	}
	rb := *revokedBy
	if rb == "" {
		rb = os.Getenv("ETZ_STEWARD_DID")
	}
	body := map[string]any{
		"capabilityUri": *capUri,
		"reason":        *reason,
		"revokedBy":     rb,
		"revokedAt":     time.Now().UTC().Format(time.RFC3339),
	}
	bjson, _ := json.MarshalIndent(body, "", "  ")
	if *pdsXrpc != "" {
		endpoint, err := url.Parse(*pdsXrpc)
		if err != nil {
			return err
		}
		endpoint.Path = "/xrpc/com.etzhayyim.apps.karute.revokeConsent"
		req, _ := http.NewRequest("POST", endpoint.String(), bytes.NewReader(bjson))
		req.Header.Set("content-type", "application/json")
		resp, err := http.DefaultClient.Do(req)
		if err != nil {
			return err
		}
		defer resp.Body.Close()
		respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 64*1024))
		if resp.StatusCode >= 400 {
			return fmt.Errorf("revokeConsent HTTP %d: %s", resp.StatusCode, string(respBody))
		}
		fmt.Println(string(respBody))
		return nil
	}
	if *out == "-" {
		fmt.Println(string(bjson))
	} else {
		if err := os.WriteFile(*out, append(bjson, '\n'), 0o600); err != nil {
			return err
		}
	}
	return nil
}

// ── list ──────────────────────────────────────────────────────────────

func runCapabilityList(args []string) error {
	fs := flag.NewFlagSet("capability list", flag.ContinueOnError)
	granter := fs.String("granter", "", "filter by granter DID")
	grantee := fs.String("grantee", "", "filter by grantee DID")
	purpose := fs.String("purpose", "", "filter by purpose")
	status := fs.String("status", "active", "active | revoked | expired | all")
	pdsXrpc := fs.String("pds-xrpc", "https://karute.etzhayyim.com", "XRPC origin to query")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printCapabilityUsage()
			return nil
		}
		return err
	}
	endpoint, _ := url.Parse(*pdsXrpc)
	endpoint.Path = "/xrpc/com.etzhayyim.apps.karute.listConsent"
	q := endpoint.Query()
	if *granter != "" {
		q.Set("granterDid", *granter)
	}
	if *grantee != "" {
		q.Set("granteeDid", *grantee)
	}
	if *purpose != "" {
		q.Set("purpose", *purpose)
	}
	q.Set("status", *status)
	endpoint.RawQuery = q.Encode()
	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()
	req, _ := http.NewRequestWithContext(ctx, "GET", endpoint.String(), nil)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("GET %s: %w", endpoint.String(), err)
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode != 200 {
		return fmt.Errorf("listConsent HTTP %d: %s", resp.StatusCode, string(body))
	}
	fmt.Println(string(body))
	return nil
}

// ── helpers ───────────────────────────────────────────────────────────

func splitCSV(s string) []string {
	if s == "" {
		return nil
	}
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}

// canonicalJSON sorts object keys recursively. AT Protocol records use this
// shape; verifiers MUST reconstruct the same byte stream to verify signatures.
func canonicalJSON(v any) ([]byte, error) {
	// json.Marshal already produces deterministic key ordering for map[string]any
	// (since Go 1.12), but for our typed struct we need a generic sort. The
	// easiest route: round-trip through map.
	tmp, err := json.Marshal(v)
	if err != nil {
		return nil, err
	}
	var generic any
	if err := json.Unmarshal(tmp, &generic); err != nil {
		return nil, err
	}
	return marshalSorted(generic)
}

func marshalSorted(v any) ([]byte, error) {
	switch t := v.(type) {
	case map[string]any:
		keys := make([]string, 0, len(t))
		for k := range t {
			keys = append(keys, k)
		}
		sort.Strings(keys)
		var buf bytes.Buffer
		buf.WriteByte('{')
		for i, k := range keys {
			if i > 0 {
				buf.WriteByte(',')
			}
			kb, _ := json.Marshal(k)
			buf.Write(kb)
			buf.WriteByte(':')
			vb, err := marshalSorted(t[k])
			if err != nil {
				return nil, err
			}
			buf.Write(vb)
		}
		buf.WriteByte('}')
		return buf.Bytes(), nil
	case []any:
		var buf bytes.Buffer
		buf.WriteByte('[')
		for i, el := range t {
			if i > 0 {
				buf.WriteByte(',')
			}
			vb, err := marshalSorted(el)
			if err != nil {
				return nil, err
			}
			buf.Write(vb)
		}
		buf.WriteByte(']')
		return buf.Bytes(), nil
	default:
		return json.Marshal(v)
	}
}

// decodeBase58btc implements the base58btc alphabet used by Multibase 'z'.
func decodeBase58btc(s string) ([]byte, error) {
	const alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
	idx := func(c byte) int {
		for i := 0; i < len(alphabet); i++ {
			if alphabet[i] == c {
				return i
			}
		}
		return -1
	}
	var n big0
	for i := 0; i < len(s); i++ {
		ix := idx(s[i])
		if ix < 0 {
			return nil, fmt.Errorf("invalid base58 char %q", s[i])
		}
		n.mulAdd58(ix)
	}
	leading := 0
	for i := 0; i < len(s) && s[i] == '1'; i++ {
		leading++
	}
	return append(bytes.Repeat([]byte{0}, leading), n.bytes()...), nil
}

// Minimal arbitrary-precision unsigned integer for base58 decoding.
// Avoids pulling in math/big (which Go has but adds ~200KB to the binary).
type big0 struct {
	limbs []uint32 // little-endian base 2^32
}

func (b *big0) mulAdd58(d int) {
	carry := uint64(d)
	for i := range b.limbs {
		v := uint64(b.limbs[i])*58 + carry
		b.limbs[i] = uint32(v)
		carry = v >> 32
	}
	for carry > 0 {
		b.limbs = append(b.limbs, uint32(carry))
		carry >>= 32
	}
}

func (b *big0) bytes() []byte {
	if len(b.limbs) == 0 {
		return nil
	}
	out := make([]byte, len(b.limbs)*4)
	for i, l := range b.limbs {
		out[i*4+0] = byte(l)
		out[i*4+1] = byte(l >> 8)
		out[i*4+2] = byte(l >> 16)
		out[i*4+3] = byte(l >> 24)
	}
	// Trim leading zeros (we have little-endian, so trim from the END).
	for len(out) > 0 && out[len(out)-1] == 0 {
		out = out[:len(out)-1]
	}
	// Reverse to big-endian for the protocol expectation.
	for i, j := 0, len(out)-1; i < j; i, j = i+1, j-1 {
		out[i], out[j] = out[j], out[i]
	}
	return out
}

// ── HTTP audit emission ───────────────────────────────────────────────

// postAuditEvent sends a deploy event to https://audit.etzhayyim.com/xrpc/...
// asynchronously (best-effort). Failures are logged to stderr but do not
// block the deploy. Used by actor.go emitDeployEvent.
func postAuditEvent(eventBody []byte) {
	endpoint := os.Getenv("ETZ_AUDIT_ENDPOINT")
	if endpoint == "" {
		endpoint = auditAggregatorEndpoint
	}
	ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, "POST", endpoint, bytes.NewReader(eventBody))
	if err != nil {
		fmt.Fprintf(os.Stderr, "audit emit (request build): %v\n", err)
		return
	}
	req.Header.Set("content-type", "application/json")
	tok := os.Getenv("ETZ_AUDIT_TOKEN")
	if tok != "" {
		req.Header.Set("authorization", "Bearer "+tok)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		// Audit aggregator unreachable is non-fatal — the stderr DEPLOY_EVENT
		// line is the durable record until the aggregator is online.
		fmt.Fprintf(os.Stderr, "audit emit (send): %v (event still on stderr)\n", err)
		return
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	if resp.StatusCode >= 400 {
		fmt.Fprintf(os.Stderr, "audit emit: HTTP %d (event still on stderr)\n", resp.StatusCode)
	}
}
