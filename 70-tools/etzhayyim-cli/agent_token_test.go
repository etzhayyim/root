package main

// Tests for `e7m agent-token` JWS mint + structural verify.

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"strings"
	"testing"
	"time"
)

func TestSignJWS_RoundTrip(t *testing.T) {
	pub, priv, err := ed25519.GenerateKey(rand.Reader)
	if err != nil {
		t.Fatal(err)
	}
	now := time.Now().Unix()
	payload := map[string]any{
		"iss": "did:web:steward.example",
		"sub": "did:web:agent.example",
		"aud": "did:web:karute.example",
		"lxm": "deploy.cfWorker:karute-did-web",
		"iat": now,
		"exp": now + 60,
		"jti": "abc",
	}
	jws, err := signJWS(priv, payload, "did:web:steward.example#key-0")
	if err != nil {
		t.Fatal(err)
	}
	parts := strings.Split(jws, ".")
	if len(parts) != 3 {
		t.Fatalf("want 3 parts, got %d", len(parts))
	}
	// Verify using the matching pubkey
	signingInput := parts[0] + "." + parts[1]
	sig, err := base64.RawURLEncoding.DecodeString(parts[2])
	if err != nil {
		t.Fatal(err)
	}
	if !ed25519.Verify(pub, []byte(signingInput), sig) {
		t.Fatal("signature did not verify")
	}
	// Decode and check claims
	payloadBytes, _ := base64.RawURLEncoding.DecodeString(parts[1])
	got := map[string]any{}
	if err := json.Unmarshal(payloadBytes, &got); err != nil {
		t.Fatal(err)
	}
	if got["lxm"] != "deploy.cfWorker:karute-did-web" {
		t.Fatalf("lxm: got %v", got["lxm"])
	}
	if got["aud"] != "did:web:karute.example" {
		t.Fatalf("aud: got %v", got["aud"])
	}
}

func TestSignJWS_WrongKeyVerifyFails(t *testing.T) {
	_, priv, _ := ed25519.GenerateKey(rand.Reader)
	otherPub, _, _ := ed25519.GenerateKey(rand.Reader)
	payload := map[string]any{"sub": "did:web:agent.example", "exp": time.Now().Unix() + 60}
	jws, _ := signJWS(priv, payload, "kid")
	parts := strings.Split(jws, ".")
	signingInput := parts[0] + "." + parts[1]
	sig, _ := base64.RawURLEncoding.DecodeString(parts[2])
	if ed25519.Verify(otherPub, []byte(signingInput), sig) {
		t.Fatal("verify should have failed with wrong key")
	}
}

func TestInferAudienceFromLxm(t *testing.T) {
	cases := []struct {
		in  string
		out string
	}{
		{"com.etzhayyim.apps.karute.createSoapNote", "did:web:karute.etzhayyim.com"},
		{"com.etzhayyim.apps.hc.createTask", "did:web:hc.etzhayyim.com"},
		{"deploy.cfWorker:karute-did-web", "did:web:karute-did-web.etzhayyim.com"},
		{"deploy.k8s:lg-karute", "did:web:lg-karute.etzhayyim.com"},
		{"unknown.scope", ""},
	}
	for _, c := range cases {
		got := inferAudienceFromLxm(c.in)
		if got != c.out {
			t.Errorf("inferAudienceFromLxm(%q): got %q want %q", c.in, got, c.out)
		}
	}
}

func TestRandomHex_Unique(t *testing.T) {
	seen := map[string]bool{}
	for i := 0; i < 100; i++ {
		s, err := randomHex(16)
		if err != nil {
			t.Fatal(err)
		}
		if len(s) != 32 {
			t.Fatalf("len=%d", len(s))
		}
		if seen[s] {
			t.Fatal("collision in 100 samples — randomness broken")
		}
		seen[s] = true
	}
}
