package main

// `e7m agent-token` — mint an Ed25519 JWS for agent-led XRPC / deploy calls.
//
// Per ADR-2605232000 (agent-led autonomous deploy) + ADR-2605231400
// (consent capability — the parent authority).
//
// The output JWS payload claims:
//
//	{
//	  "iss": "did:web:<issuer>",          // who minted (Steward)
//	  "sub": "did:web:<agent>",           // who is authorized (Agent)
//	  "aud": "did:web:<target>",          // who must verify (target actor / Worker)
//	  "lxm": "deploy.cfWorker:karute-did-web", // single scope per token
//	  "cap": "at://did:plc:.../com.etzhayyim.consent.capability/abc", // parent capability URI
//	  "iat": <unix>,
//	  "exp": <unix + ttl>,
//	  "jti": "<uuid>"
//	}
//
// Signature: Ed25519 over `base64url(headerJSON) + "." + base64url(payloadJSON)`,
// using the issuer's private key from macOS Keychain
// (`service=etzhayyim, account=DID_PRIVATE_KEY_ED25519_<actor-upper>`).

import (
	"crypto/ed25519"
	"crypto/rand"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"strings"
	"time"
)

func runAgentToken(args []string) error {
	fs := flag.NewFlagSet("agent-token", flag.ContinueOnError)
	lxm := fs.String("lxm", "", "scope NSID (single value; e.g. 'deploy.cfWorker:karute-did-web' or 'com.etzhayyim.apps.karute.createSoapNote')")
	ttl := fs.Int("ttl", 60, "lifetime in seconds (default 60)")
	issuer := fs.String("issuer", "", "issuer DID (default: $ETZ_STEWARD_DID)")
	agent := fs.String("agent", "", "agent DID being authorized (default: $ETZ_AGENT_DID)")
	audience := fs.String("audience", "", "audience DID (default: derived from --lxm prefix)")
	capability := fs.String("capability", "", "AT URI of the parent consent capability (purpose=deploy-execution)")
	keychainAccount := fs.String("keychain-account", "DID_PRIVATE_KEY_ED25519", "macOS Keychain account name for the signing key")
	keychainService := fs.String("keychain-service", "etzhayyim", "macOS Keychain service name")
	keyFile := fs.String("key-file", "", "alternative: path to a raw 32-byte Ed25519 private key (mutually exclusive with keychain)")
	out := fs.String("out", "-", "output destination (- for stdout, path for file)")
	verbose := fs.Bool("verbose", false, "print claim payload to stderr before signing")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printAgentTokenUsage()
			return nil
		}
		return err
	}
	if *lxm == "" {
		printAgentTokenUsage()
		return fmt.Errorf("--lxm required")
	}
	if *ttl < 1 || *ttl > 3600 {
		return fmt.Errorf("--ttl must be 1..3600 (one hour upper bound by spec)")
	}

	issDid := *issuer
	if issDid == "" {
		issDid = os.Getenv("ETZ_STEWARD_DID")
	}
	if issDid == "" {
		return fmt.Errorf("--issuer or $ETZ_STEWARD_DID required")
	}
	agentDid := *agent
	if agentDid == "" {
		agentDid = os.Getenv("ETZ_AGENT_DID")
	}
	if agentDid == "" {
		return fmt.Errorf("--agent or $ETZ_AGENT_DID required (e.g. did:web:claude-agent.etzhayyim.com)")
	}
	audDid := *audience
	if audDid == "" {
		audDid = inferAudienceFromLxm(*lxm)
	}

	priv, err := loadEd25519PrivateKey(*keychainService, *keychainAccount, *keyFile)
	if err != nil {
		return err
	}

	now := time.Now().Unix()
	jti, err := randomHex(16)
	if err != nil {
		return err
	}
	payload := map[string]any{
		"iss": issDid,
		"sub": agentDid,
		"aud": audDid,
		"lxm": *lxm,
		"iat": now,
		"exp": now + int64(*ttl),
		"jti": jti,
	}
	if *capability != "" {
		payload["cap"] = *capability
	}
	if *verbose {
		b, _ := json.MarshalIndent(payload, "", "  ")
		fmt.Fprintln(os.Stderr, "agent-token claim:")
		fmt.Fprintln(os.Stderr, string(b))
	}

	jws, err := signJWS(priv, payload, issDid+"#key-0")
	if err != nil {
		return err
	}

	if *out == "-" {
		fmt.Println(jws)
	} else {
		if err := os.WriteFile(*out, []byte(jws+"\n"), 0o600); err != nil {
			return err
		}
		fmt.Fprintf(os.Stderr, "wrote token to %s\n", *out)
	}
	return nil
}

func printAgentTokenUsage() {
	fmt.Printf(`etzhayyim agent-token — mint an Ed25519-signed scoped JWS

USAGE:
  etzhayyim agent-token --lxm <nsid> [--ttl <sec>] [--issuer <did>] [--agent <did>] [--capability <at-uri>]

REQUIRED:
  --lxm <nsid>                Single scope NSID (one token = one scope)

OPTIONAL:
  --ttl <sec>                 Lifetime (default 60, max 3600)
  --issuer <did>              Issuer DID (default: $ETZ_STEWARD_DID)
  --agent <did>               Agent DID being authorized (default: $ETZ_AGENT_DID)
  --audience <did>            Audience DID (default: derived from --lxm prefix)
  --capability <at-uri>       Parent consent capability AT URI (purpose=deploy-execution)
  --keychain-service <name>   macOS Keychain service (default: etzhayyim)
  --keychain-account <name>   macOS Keychain account (default: DID_PRIVATE_KEY_ED25519)
  --key-file <path>           Alt: raw 32-byte Ed25519 private key file (mutually exclusive)
  --out <path>                Output destination (- for stdout)
  --verbose                   Print claim payload to stderr before signing

EXAMPLES:
  # Mint a 60s token for one karute write XRPC
  AT_TOKEN=$(etzhayyim agent-token --lxm com.etzhayyim.apps.karute.createSoapNote)
  curl -H "Authorization: Bearer $AT_TOKEN" https://karute.etzhayyim.com/xrpc/... -d '…'

  # Agent-led deploy stage
  TOKEN=$(etzhayyim agent-token \
    --lxm deploy.cfWorker:karute-did-web \
    --capability at://did:web:steward.etzhayyim.com/com.etzhayyim.consent.capability/3lzw1 \
    --ttl 300)
  etzhayyim actor deploy --actor karute --only did-worker --agent-token "$TOKEN"
`)
}

func inferAudienceFromLxm(lxm string) string {
	// "com.etzhayyim.apps.karute.createSoapNote" → did:web:karute.etzhayyim.com
	// "deploy.cfWorker:karute-did-web"    → did:web:karute-did-web.etzhayyim.com
	// "deploy.k8s:lg-karute"              → did:web:karute.etzhayyim.com (back-reference)
	if strings.HasPrefix(lxm, "com.etzhayyim.apps.") {
		parts := strings.Split(lxm, ".")
		if len(parts) >= 4 {
			return "did:web:" + parts[3] + ".etzhayyim.com"
		}
	}
	if strings.HasPrefix(lxm, "deploy.") {
		col := strings.Index(lxm, ":")
		if col > 0 {
			ident := lxm[col+1:]
			return "did:web:" + ident + ".etzhayyim.com"
		}
	}
	return ""
}

// ── Key handling ──────────────────────────────────────────────────────

func loadEd25519PrivateKey(service, account, keyFile string) (ed25519.PrivateKey, error) {
	if keyFile != "" {
		raw, err := os.ReadFile(keyFile)
		if err != nil {
			return nil, err
		}
		raw = []byte(strings.TrimSpace(string(raw)))
		decoded, err := base64.RawURLEncoding.DecodeString(string(raw))
		if err != nil {
			// Try base64 (not url-safe)
			decoded, err = base64.StdEncoding.DecodeString(string(raw))
			if err != nil {
				return nil, fmt.Errorf("key file decode: %w", err)
			}
		}
		if len(decoded) != ed25519.SeedSize && len(decoded) != ed25519.PrivateKeySize {
			return nil, fmt.Errorf("key file: want 32 or 64 bytes after b64 decode, got %d", len(decoded))
		}
		if len(decoded) == ed25519.SeedSize {
			return ed25519.NewKeyFromSeed(decoded), nil
		}
		return ed25519.PrivateKey(decoded), nil
	}
	// macOS Keychain
	cmd := exec.Command("security", "find-generic-password", "-s", service, "-a", account, "-w")
	out, err := cmd.Output()
	if err != nil {
		return nil, fmt.Errorf("keychain lookup failed (service=%s, account=%s): %w — try --key-file or generate with the actor-deploy README", service, account, err)
	}
	val := strings.TrimSpace(string(out))
	decoded, err := base64.RawURLEncoding.DecodeString(val)
	if err != nil {
		decoded, err = base64.StdEncoding.DecodeString(val)
		if err != nil {
			return nil, fmt.Errorf("keychain value decode: %w", err)
		}
	}
	if len(decoded) == ed25519.SeedSize {
		return ed25519.NewKeyFromSeed(decoded), nil
	}
	if len(decoded) == ed25519.PrivateKeySize {
		return ed25519.PrivateKey(decoded), nil
	}
	return nil, fmt.Errorf("keychain value: want 32 or 64 bytes after b64 decode, got %d", len(decoded))
}

// ── JWS ───────────────────────────────────────────────────────────────

func signJWS(priv ed25519.PrivateKey, payload map[string]any, keyId string) (string, error) {
	header := map[string]any{
		"alg": "EdDSA",
		"typ": "JWT",
		"kid": keyId,
	}
	hb, err := json.Marshal(header)
	if err != nil {
		return "", err
	}
	pb, err := json.Marshal(payload)
	if err != nil {
		return "", err
	}
	signingInput := base64.RawURLEncoding.EncodeToString(hb) + "." + base64.RawURLEncoding.EncodeToString(pb)
	sig := ed25519.Sign(priv, []byte(signingInput))
	return signingInput + "." + base64.RawURLEncoding.EncodeToString(sig), nil
}

func randomHex(n int) (string, error) {
	b := make([]byte, n)
	if _, err := rand.Read(b); err != nil {
		return "", err
	}
	const hex = "0123456789abcdef"
	out := make([]byte, n*2)
	for i, v := range b {
		out[i*2] = hex[v>>4]
		out[i*2+1] = hex[v&0x0f]
	}
	return string(out), nil
}
