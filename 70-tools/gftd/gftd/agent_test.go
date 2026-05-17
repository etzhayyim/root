package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestAgentStatusArgs(t *testing.T) {
	got := agentStatusArgs("did:web:kami-agent.etzhayyim.com", true)
	want := []string{"--agent-did", "did:web:kami-agent.etzhayyim.com", "--json"}
	if len(got) != len(want) {
		t.Fatalf("len=%d want=%d args=%v", len(got), len(want), got)
	}
	for i := range want {
		if got[i] != want[i] {
			t.Fatalf("arg[%d]=%q want %q", i, got[i], want[i])
		}
	}
}

func TestExtractSafeTxHash(t *testing.T) {
	got := extractSafeTxHash("Safe nonce: 8\n  txHash:\n  0xabc123\n  Signer1: 0x1\n")
	if got != "0xabc123" {
		t.Fatalf("got %q", got)
	}
}

func TestAgentRepoPath(t *testing.T) {
	root := filepath.Join("tmp", "repo")
	if got := agentRepoPath(root, "90-docs/proof.json"); got != filepath.Join(root, "90-docs/proof.json") {
		t.Fatalf("relative path=%q", got)
	}
	abs := filepath.Join(string(os.PathSeparator), "tmp", "proof.json")
	if got := agentRepoPath(root, abs); got != abs {
		t.Fatalf("absolute path=%q", got)
	}
}

func TestAgentWebHostPort(t *testing.T) {
	tests := []struct {
		name string
		url  string
		host string
		port string
	}{
		{name: "default port", url: "http://127.0.0.1:8765", host: "127.0.0.1", port: "8765"},
		{name: "explicit host", url: "http://localhost:9999", host: "localhost", port: "9999"},
		{name: "missing port", url: "http://localhost", host: "localhost", port: "8765"},
		{name: "invalid", url: ":", host: "127.0.0.1", port: "8765"},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			host, port := agentWebHostPort(tt.url)
			if host != tt.host || port != tt.port {
				t.Fatalf("(%q, %q), want (%q, %q)", host, port, tt.host, tt.port)
			}
		})
	}
}

func TestAgentCommandEnvAddsDefaults(t *testing.T) {
	t.Setenv("AGENT_DAEMON_ENV_FILE", "")
	t.Setenv("PYTHONPATH", "")
	root := t.TempDir()
	env := agentCommandEnv(root)
	wantEnvFile := "AGENT_DAEMON_ENV_FILE=" + filepath.Join(root, "ops", "local-agent", "agent-daemon.env")
	wantPythonPath := "PYTHONPATH=" + filepath.Join(root, "20-actors", "magatama", "py", "src")
	if !containsEnv(env, wantEnvFile) {
		t.Fatalf("missing %q in env", wantEnvFile)
	}
	if !containsEnv(env, wantPythonPath) {
		t.Fatalf("missing %q in env", wantPythonPath)
	}
}

func containsEnv(env []string, want string) bool {
	for _, item := range env {
		if item == want {
			return true
		}
	}
	return false
}

func TestIsExecutableFile(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "tool")
	if err := os.WriteFile(path, []byte("#!/bin/sh\n"), 0o755); err != nil {
		t.Fatal(err)
	}
	if !isExecutableFile(path) {
		t.Fatalf("%s should be executable", path)
	}
}

func TestReadAgentVerifyJSON(t *testing.T) {
	path := filepath.Join(t.TempDir(), "proof.json")
	if err := os.WriteFile(path, []byte(`{"chain":{"tokenId":3,"agentURI":"ipfs://bafy"}}`), 0o644); err != nil {
		t.Fatal(err)
	}
	var proof agentPublicationProof
	if err := readAgentVerifyJSON(path, &proof); err != nil {
		t.Fatal(err)
	}
	if proof.Chain.TokenID != 3 || proof.Chain.AgentURI != "ipfs://bafy" {
		t.Fatalf("unexpected proof: %+v", proof.Chain)
	}
}
