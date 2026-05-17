package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func TestAgentRuntimeHMACSHA256Hex(t *testing.T) {
	got := hmacSHA256Hex("key", []byte("body"))
	want := "515aae133b435d4000956731f68ae5cf5eb85d4f0dc6a546d2bfcd3595ec1ae1"
	if got != want {
		t.Fatalf("hmacSHA256Hex() = %s, want %s", got, want)
	}
}

func TestAgentRuntimeRenderPublicManifest(t *testing.T) {
	dir := t.TempDir()
	manifest := filepath.Join(dir, "worker.yaml")
	if err := os.WriteFile(manifest, []byte(`
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langserver-worker
  namespace: agent-runtime-test
  annotations:
    etzhayyim.com/runtime-kind: k8s-langserver
spec:
  template:
    spec:
      serviceAccountName: langserver-worker
      containers:
        - name: worker
          image: registry.example.com/langserver-worker:20260513
          resources:
            requests:
              cpu: "100m"
              memory: "128Mi"
            limits:
              cpu: "500m"
              memory: "512Mi"
          env:
            - name: PUBLIC_ENDPOINT
              value: https://worker.example.com
            - name: PRIVATE_TOKEN
              valueFrom:
                secretKeyRef:
                  name: worker-token
                  key: token
`), 0o644); err != nil {
		t.Fatal(err)
	}

	rendered, err := renderAgentRuntimePublic("test-cluster", []string{manifest})
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Schema     string   `json:"schema"`
		Cluster    string   `json:"cluster"`
		Namespace  string   `json:"namespace"`
		Image      string   `json:"image"`
		Redactions []string `json:"redactions"`
	}
	if err := json.Unmarshal(rendered, &doc); err != nil {
		t.Fatalf("rendered JSON did not decode: %v\n%s", err, rendered)
	}
	if doc.Schema != agentRuntimeSchema {
		t.Fatalf("schema = %q, want %q", doc.Schema, agentRuntimeSchema)
	}
	if doc.Cluster != "test-cluster" {
		t.Fatalf("cluster = %q", doc.Cluster)
	}
	if doc.Namespace != "agent-runtime-test" {
		t.Fatalf("namespace = %q", doc.Namespace)
	}
	if doc.Image != "registry.example.com/langserver-worker:20260513" {
		t.Fatalf("image = %q", doc.Image)
	}
	foundEnvRedaction := false
	foundSecretRefRedaction := false
	for _, redaction := range doc.Redactions {
		if redaction == "env" {
			foundEnvRedaction = true
		}
		if redaction == "secretRef" {
			foundSecretRefRedaction = true
		}
	}
	if !foundEnvRedaction || !foundSecretRefRedaction {
		t.Fatalf("public runtime JSON should declare env and secretRef redactions: %+v", doc.Redactions)
	}
}

func TestAgentRuntimeValidationHelpers(t *testing.T) {
	if !isHexAddress("0x1234567890abcdef1234567890ABCDEF12345678") {
		t.Fatal("mixed-case address should validate")
	}
	if isHexAddress("0x1234") {
		t.Fatal("short address should not validate")
	}
	if !isZeroAddress("0x0000000000000000000000000000000000000000") {
		t.Fatal("zero address should be detected")
	}
	if !isBytes32Hex("0x" + strings.Repeat("a", 64)) {
		t.Fatal("bytes32 hex should validate")
	}
	if isBytes32Hex("0x" + strings.Repeat("a", 62)) {
		t.Fatal("short bytes32 should not validate")
	}
}

func TestAgentRuntimeRegisterDryRunFromRegistration(t *testing.T) {
	dir := t.TempDir()
	registrationPath := filepath.Join(dir, "registration.json")
	if err := os.WriteFile(registrationPath, []byte(`{
  "schema": "https://etzhayyim.com/schemas/erc8004-agent-registration/v1.json",
  "rootIdentity": {
    "address": "0x1234567890abcdef1234567890ABCDEF12345678",
    "rootDid": "did:erc725:gftd:260425:0x1234567890abcdef1234567890ABCDEF12345678"
  }
}`), 0o644); err != nil {
		t.Fatal(err)
	}
	outPath := filepath.Join(dir, "out.json")
	if err := runAgentRuntimeRegister([]string{
		"--registration", registrationPath,
		"--agent-uri", "ipfs://bafy-agent-registration",
		"--dry-run",
		"--out", outPath,
	}); err != nil {
		t.Fatal(err)
	}
	var result struct {
		DryRun       bool   `json:"dryRun"`
		Submitted    bool   `json:"submitted"`
		RootDID      string `json:"rootDid"`
		RootDIDHash  string `json:"rootDidHash"`
		Owner        string `json:"owner"`
		AgentURI     string `json:"agentURI"`
		MetadataHash string `json:"metadataHash"`
		Registry     string `json:"registry"`
	}
	data, err := os.ReadFile(outPath)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatal(err)
	}
	if !result.DryRun || result.Submitted {
		t.Fatalf("dry-run register should not submit: %+v", result)
	}
	if result.Owner != "0x1234567890abcdef1234567890ABCDEF12345678" {
		t.Fatalf("owner = %q", result.Owner)
	}
	if result.AgentURI != "ipfs://bafy-agent-registration" {
		t.Fatalf("agentURI = %q", result.AgentURI)
	}
	if result.RootDID == "" || !isBytes32Hex(result.RootDIDHash) || !isBytes32Hex(result.MetadataHash) {
		t.Fatalf("missing register hashes: %+v", result)
	}
	if result.Registry != defaultAgentRegistryAddress {
		t.Fatalf("registry = %q", result.Registry)
	}
}

func TestAgentRuntimeRenderAgentRegistration(t *testing.T) {
	rendered, err := renderAgentRegistration([]byte(`{
  "agent": {
    "agentRegistry": "eip155:260425:0x0000000000000000000000000000000000000000",
    "agentId": "TBD_AFTER_AGENT_REGISTRY_MINT"
  },
  "protocols": [
    {
      "kind": "k8s-runtime",
      "publicManifestCid": "ipfs://TBD_PUBLIC_RUNTIME_MANIFEST_CID"
    },
    {
      "kind": "ipfs-publication",
      "artifacts": ["ipfs://TBD_PUBLIC_RUNTIME_MANIFEST_CID", "ipfs://TBD_POLICY_CID"]
    }
  ]
}`), "260425", defaultAgentRegistryAddress, "ipfs://bafy-runtime")
	if err != nil {
		t.Fatal(err)
	}
	var doc struct {
		Agent struct {
			AgentRegistry string `json:"agentRegistry"`
		} `json:"agent"`
		Protocols []map[string]any `json:"protocols"`
	}
	if err := json.Unmarshal(rendered, &doc); err != nil {
		t.Fatal(err)
	}
	if doc.Agent.AgentRegistry != "eip155:260425:"+defaultAgentRegistryAddress {
		t.Fatalf("agent registry was not rendered: %s", doc.Agent.AgentRegistry)
	}
	if doc.Protocols[0]["publicManifestCid"] != "ipfs://bafy-runtime" {
		t.Fatalf("runtime CID was not rendered: %+v", doc.Protocols[0])
	}
	artifacts := doc.Protocols[1]["artifacts"].([]any)
	if artifacts[0] != "ipfs://bafy-runtime" {
		t.Fatalf("artifact CID was not rendered: %+v", artifacts)
	}
}

func TestAgentRuntimePublishAgentDryRun(t *testing.T) {
	dir := t.TempDir()
	manifest := filepath.Join(dir, "worker.yaml")
	if err := os.WriteFile(manifest, []byte(`
apiVersion: apps/v1
kind: Deployment
metadata:
  name: langserver-worker
  namespace: agent-runtime-test
  annotations:
    etzhayyim.com/runtime-kind: k8s-langserver
spec:
  template:
    spec:
      containers:
        - name: worker
          image: registry.example.com/langserver-worker:20260513
`), 0o644); err != nil {
		t.Fatal(err)
	}
	registrationPath := filepath.Join(dir, "registration.json")
	if err := os.WriteFile(registrationPath, []byte(`{
  "agent": {
    "agentRegistry": "eip155:260425:0x0000000000000000000000000000000000000000"
  },
  "rootIdentity": {
    "address": "0x1234567890abcdef1234567890ABCDEF12345678",
    "rootDid": "did:erc725:gftd:260425:0x1234567890abcdef1234567890ABCDEF12345678"
  },
  "protocols": [
    {
      "kind": "k8s-runtime",
      "publicManifestCid": "ipfs://TBD_PUBLIC_RUNTIME_MANIFEST_CID"
    }
  ]
}`), 0o644); err != nil {
		t.Fatal(err)
	}
	resultPath := filepath.Join(dir, "result.json")
	renderedRegistrationPath := filepath.Join(dir, "rendered-registration.json")
	if err := runAgentRuntimePublishAgent([]string{
		"--registration", registrationPath,
		"--cluster", "test-cluster",
		"--dry-run",
		"--out", resultPath,
		"--registration-out", renderedRegistrationPath,
		manifest,
	}); err != nil {
		t.Fatal(err)
	}
	var result struct {
		DryRun  bool `json:"dryRun"`
		Runtime struct {
			URI       string `json:"uri"`
			Published bool   `json:"published"`
		} `json:"runtime"`
		AgentRegistration struct {
			URI       string `json:"uri"`
			Published bool   `json:"published"`
		} `json:"agentRegistration"`
		Chain struct {
			Submitted bool   `json:"submitted"`
			RootHash  string `json:"rootDidHash"`
		} `json:"chain"`
	}
	data, err := os.ReadFile(resultPath)
	if err != nil {
		t.Fatal(err)
	}
	if err := json.Unmarshal(data, &result); err != nil {
		t.Fatal(err)
	}
	if !result.DryRun || result.Runtime.Published || result.AgentRegistration.Published || result.Chain.Submitted {
		t.Fatalf("publish-agent dry-run should not publish or submit: %+v", result)
	}
	if result.Runtime.URI != "ipfs://DRY_RUN_RUNTIME_CID" {
		t.Fatalf("runtime uri = %q", result.Runtime.URI)
	}
	if !isBytes32Hex(result.Chain.RootHash) {
		t.Fatalf("root hash = %q", result.Chain.RootHash)
	}
	renderedRegistration, err := os.ReadFile(renderedRegistrationPath)
	if err != nil {
		t.Fatal(err)
	}
	if !strings.Contains(string(renderedRegistration), "ipfs://DRY_RUN_RUNTIME_CID") {
		t.Fatalf("rendered registration did not include runtime URI:\n%s", renderedRegistration)
	}
}
