package main

// Tests for the capability lifecycle (issue / verify / revoke).
// Self-contained — no live DID resolution; tests inject a local DID document.

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

// helper: generate a fresh Ed25519 keypair + matching DID document JSON file.
func mkTestSteward(t *testing.T) (priv ed25519.PrivateKey, pub ed25519.PublicKey, didDocPath string, granterDid string) {
	t.Helper()
	pubK, privK, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatalf("keygen: %v", err)
	}
	granterDid = "did:web:test-steward.example"
	didDoc := map[string]any{
		"@context": []any{"https://www.w3.org/ns/did/v1"},
		"id":       granterDid,
		"verificationMethod": []any{
			map[string]any{
				"id":         granterDid + "#key-0",
				"type":       "JsonWebKey2020",
				"controller": granterDid,
				"publicKeyJwk": map[string]any{
					"kty": "OKP",
					"crv": "Ed25519",
					"x":   base64.RawURLEncoding.EncodeToString(pubK),
					"kid": "key-0",
				},
			},
		},
	}
	b, _ := json.Marshal(didDoc)
	didDocPath = filepath.Join(t.TempDir(), "did.json")
	if err := os.WriteFile(didDocPath, b, 0o600); err != nil {
		t.Fatalf("write didDoc: %v", err)
	}
	return privK, pubK, didDocPath, granterDid
}

// helper: sign a capability payload as JWS (mirrors runCapabilityIssue).
func signCapability(t *testing.T, priv ed25519.PrivateKey, payload *capabilityPayload, granter string) string {
	t.Helper()
	pjson, err := canonicalJSON(payload)
	if err != nil {
		t.Fatalf("canonicalize: %v", err)
	}
	header := map[string]any{"alg": "EdDSA", "typ": "JWT", "kid": granter + "#key-0"}
	hb, _ := json.Marshal(header)
	signingInput := base64.RawURLEncoding.EncodeToString(hb) + "." + base64.RawURLEncoding.EncodeToString(pjson)
	sig := ed25519.Sign(priv, []byte(signingInput))
	return signingInput + "." + base64.RawURLEncoding.EncodeToString(sig)
}

func TestVerifyJWS_Valid(t *testing.T) {
	priv, _, didDocPath, granter := mkTestSteward(t)
	now := time.Now().UTC()
	cap := &capabilityPayload{
		Version:    1,
		GranterDid: granter,
		GranteeDid: "did:web:claude-agent.example",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.cfWorker:karute-did-web"},
		IssuedAt:   now.Format(time.RFC3339),
		ExpiresAt:  now.Add(time.Hour).Format(time.RFC3339),
	}
	jws := signCapability(t, priv, cap, granter)
	res := verifyJWS(jws, now, &verifyOpts{didDocLocal: didDocPath})
	if !res.Valid {
		t.Fatalf("expected valid, got reason=%q", res.Reason)
	}
	if !res.SignatureOk || !res.NotExpired {
		t.Fatalf("flags: sig=%v exp=%v", res.SignatureOk, res.NotExpired)
	}
	if res.Payload.Purpose != "deploy-execution" {
		t.Fatalf("payload purpose=%q", res.Payload.Purpose)
	}
}

func TestVerifyJWS_Expired(t *testing.T) {
	priv, _, didDocPath, granter := mkTestSteward(t)
	now := time.Now().UTC()
	cap := &capabilityPayload{
		Version:    1,
		GranterDid: granter,
		GranteeDid: "did:web:claude-agent.example",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.k8s:lg-karute"},
		IssuedAt:   now.Add(-2 * time.Hour).Format(time.RFC3339),
		ExpiresAt:  now.Add(-1 * time.Hour).Format(time.RFC3339),
	}
	jws := signCapability(t, priv, cap, granter)
	res := verifyJWS(jws, now, &verifyOpts{didDocLocal: didDocPath})
	if res.Valid {
		t.Fatalf("expected expired, got valid")
	}
	if !strings.Contains(res.Reason, "expired") {
		t.Fatalf("expected reason to mention expired, got %q", res.Reason)
	}
}

func TestVerifyJWS_ForgedPayload(t *testing.T) {
	priv, _, didDocPath, granter := mkTestSteward(t)
	now := time.Now().UTC()
	cap := &capabilityPayload{
		Version:    1,
		GranterDid: granter,
		GranteeDid: "did:web:claude-agent.example",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.cfWorker:karute-did-web"},
		IssuedAt:   now.Format(time.RFC3339),
		ExpiresAt:  now.Add(time.Hour).Format(time.RFC3339),
	}
	jws := signCapability(t, priv, cap, granter)
	// Tamper: swap payload but keep header + signature
	parts := strings.Split(jws, ".")
	cap.Scope = []string{"deploy.evil:bypass"}
	tampered, _ := canonicalJSON(cap)
	parts[1] = base64.RawURLEncoding.EncodeToString(tampered)
	forged := strings.Join(parts, ".")
	res := verifyJWS(forged, now, &verifyOpts{didDocLocal: didDocPath})
	if res.Valid {
		t.Fatalf("expected forged to be rejected, got valid")
	}
	if !strings.Contains(res.Reason, "Ed25519") {
		t.Fatalf("expected reason to mention Ed25519, got %q", res.Reason)
	}
}

func TestVerifyJWS_Revoked(t *testing.T) {
	priv, _, didDocPath, granter := mkTestSteward(t)
	now := time.Now().UTC()
	cap := &capabilityPayload{
		Version:    1,
		GranterDid: granter,
		GranteeDid: "did:web:claude-agent.example",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.k8s:lg-karute"},
		IssuedAt:   now.Format(time.RFC3339),
		ExpiresAt:  now.Add(time.Hour).Format(time.RFC3339),
		RevokedAt:  now.Add(-1 * time.Minute).Format(time.RFC3339),
	}
	jws := signCapability(t, priv, cap, granter)
	res := verifyJWS(jws, now, &verifyOpts{didDocLocal: didDocPath})
	if res.Valid {
		t.Fatalf("expected revoked to be rejected, got valid")
	}
	if !strings.Contains(res.Reason, "revoked") {
		t.Fatalf("reason: %q", res.Reason)
	}
}

func TestVerifyJWS_WrongKey(t *testing.T) {
	priv1, _, _, granter := mkTestSteward(t)
	// Second steward's DID doc has a different key
	_, _, otherDidDocPath, _ := mkTestSteward(t)
	now := time.Now().UTC()
	cap := &capabilityPayload{
		Version:    1,
		GranterDid: granter,
		GranteeDid: "did:web:claude-agent.example",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.k8s:lg-karute"},
		IssuedAt:   now.Format(time.RFC3339),
		ExpiresAt:  now.Add(time.Hour).Format(time.RFC3339),
	}
	jws := signCapability(t, priv1, cap, granter)
	// Verify against a DID doc holding a DIFFERENT pubkey — must fail.
	res := verifyJWS(jws, now, &verifyOpts{didDocLocal: otherDidDocPath})
	if res.Valid {
		t.Fatalf("expected wrong-key rejection, got valid")
	}
}

func TestVerifyJWS_Offline(t *testing.T) {
	priv, _, _, granter := mkTestSteward(t)
	now := time.Now().UTC()
	cap := &capabilityPayload{
		Version:    1,
		GranterDid: granter,
		GranteeDid: "did:web:claude-agent.example",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.cfWorker:karute-did-web"},
		IssuedAt:   now.Format(time.RFC3339),
		ExpiresAt:  now.Add(time.Hour).Format(time.RFC3339),
	}
	jws := signCapability(t, priv, cap, granter)
	// offline: structural-only check, signature NOT verified.
	// verifyJWS marks the result as invalid but the payload is still populated.
	res := verifyJWS(jws, now, &verifyOpts{offline: true})
	if res.Valid {
		t.Fatalf("offline mode should not mark valid")
	}
	if res.Payload == nil || res.Payload.Purpose != "deploy-execution" {
		t.Fatalf("payload not parsed in offline mode")
	}
	if !strings.Contains(res.Reason, "offline") {
		t.Fatalf("reason: %q", res.Reason)
	}
}

func TestVerifyJWS_MalformedJWS(t *testing.T) {
	now := time.Now().UTC()
	cases := []struct {
		name string
		jws  string
	}{
		{"empty", ""},
		{"one-part", "abc"},
		{"two-parts", "abc.def"},
		{"bad-base64", "!!!.!!!.!!!"},
	}
	for _, c := range cases {
		t.Run(c.name, func(t *testing.T) {
			res := verifyJWS(c.jws, now, &verifyOpts{offline: true})
			if res.Valid {
				t.Fatalf("expected invalid for %q", c.name)
			}
		})
	}
}

func TestExtractEd25519PubkeyFromDoc_JWK(t *testing.T) {
	_, pubK, didDocPath, _ := mkTestSteward(t)
	raw, _ := os.ReadFile(didDocPath)
	doc := map[string]any{}
	if err := json.Unmarshal(raw, &doc); err != nil {
		t.Fatal(err)
	}
	got, err := extractEd25519PubkeyFromDoc(doc)
	if err != nil {
		t.Fatal(err)
	}
	if !pubK.Equal(got) {
		t.Fatalf("pubkey mismatch")
	}
}

func TestExtractEd25519PubkeyFromDoc_NoVM(t *testing.T) {
	doc := map[string]any{"id": "did:web:foo"}
	_, err := extractEd25519PubkeyFromDoc(doc)
	if err == nil {
		t.Fatalf("expected error for missing verificationMethod")
	}
}

func TestCanonicalJSON_DeterministicKeyOrder(t *testing.T) {
	payload := &capabilityPayload{
		Version:    1,
		GranterDid: "did:web:a",
		GranteeDid: "did:web:b",
		Purpose:    "deploy-execution",
		Scope:      []string{"deploy.k8s:x"},
		IssuedAt:   "2026-01-01T00:00:00Z",
		ExpiresAt:  "2026-01-02T00:00:00Z",
	}
	b1, _ := canonicalJSON(payload)
	b2, _ := canonicalJSON(payload)
	if string(b1) != string(b2) {
		t.Fatalf("canonicalJSON not deterministic across calls")
	}
	// Sanity: keys appear in sorted order
	s := string(b1)
	first := strings.Index(s, "expiresAt")
	second := strings.Index(s, "granterDid")
	if first < 0 || second < 0 || first > second {
		t.Fatalf("expected expiresAt before granterDid; got %q", s)
	}
}
