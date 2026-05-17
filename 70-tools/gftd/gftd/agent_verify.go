package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const (
	defaultAgentPublicationProof = "90-docs/proof/kami-agent-erc8004-publish-attempt.local.json"
	defaultAgentRuntimeArtifact  = "90-docs/proof/kami-agent-runtime-artifact.local.json"
	defaultAgentRuntimeReceipt   = "90-docs/proof/kami-agent-runtime-receipt.local.json"
	defaultAgentVerifyRPC        = "https://geth.etzhayyim.com"
	defaultAgentRegistry         = "0xcA3480edDAfa39c9377B83eEB18291286C8Cb865"
	defaultRuntimeRegistry       = "0x9C730960e9BF7A403E610Dca0C8a565CF655b6a1"
)

type agentVerifyResult struct {
	OK        bool                        `json:"ok"`
	AgentDID  string                      `json:"agentDid"`
	Checks    map[string]agentVerifyCheck `json:"checks"`
	Evidence  map[string]any              `json:"evidence"`
	Generated string                      `json:"generatedAt"`
}

type agentVerifyCheck struct {
	OK      bool   `json:"ok"`
	Detail  string `json:"detail,omitempty"`
	Error   string `json:"error,omitempty"`
	Skipped bool   `json:"skipped,omitempty"`
}

type agentPublicationProof struct {
	AgentRegistration struct {
		CID        string `json:"cid"`
		URI        string `json:"uri"`
		GatewayURL string `json:"gatewayUrl"`
	} `json:"agentRegistration"`
	Chain struct {
		TokenID     int    `json:"tokenId"`
		RootDIDHash string `json:"rootDidHash"`
		Owner       string `json:"owner"`
		AgentURI    string `json:"agentURI"`
		TxHash      string `json:"txHash"`
	} `json:"chain"`
}

type agentRuntimeArtifactProof struct {
	ArtifactID  string `json:"artifactId"`
	Kind        string `json:"kind"`
	Version     int    `json:"version"`
	ArtifactURI string `json:"artifactURI"`
	TxHash      string `json:"txHash"`
	Status      string `json:"status"`
}

type agentRuntimeReceiptProof struct {
	JobID      string `json:"jobId"`
	ArtifactID string `json:"artifactId"`
	TxHash     string `json:"txHash"`
	Submitted  bool   `json:"submitted"`
}

func runAgentVerify(args []string) error {
	fs := flag.NewFlagSet("agent verify", flag.ContinueOnError)
	agentDID := fs.String("did", agentEnvDefault("AGENT_DID", defaultOrganismAgentDID), "agent DID to verify")
	rpcURL := fs.String("rpc-url", defaultAgentVerifyRPC, "private-chain RPC URL")
	publicationPath := fs.String("publication-proof", defaultAgentPublicationProof, "ERC-8004 publication proof JSON")
	artifactPath := fs.String("artifact-proof", defaultAgentRuntimeArtifact, "runtime artifact proof JSON")
	receiptPath := fs.String("receipt-proof", defaultAgentRuntimeReceipt, "runtime receipt proof JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	root := agentRepoRoot()
	result := agentVerifyResult{
		OK:        true,
		AgentDID:  strings.TrimSpace(*agentDID),
		Checks:    map[string]agentVerifyCheck{},
		Evidence:  map[string]any{},
		Generated: time.Now().UTC().Format(time.RFC3339),
	}
	publication := agentPublicationProof{}
	artifact := agentRuntimeArtifactProof{}
	receipt := agentRuntimeReceiptProof{}
	addCheck := func(name string, check agentVerifyCheck) {
		result.Checks[name] = check
		if !check.OK && !check.Skipped {
			result.OK = false
		}
	}
	if err := readAgentVerifyJSON(filepath.Join(root, *publicationPath), &publication); err != nil {
		addCheck("proof.publication", agentVerifyCheck{OK: false, Error: err.Error()})
	} else {
		addCheck("proof.publication", agentVerifyCheck{OK: true, Detail: publication.Chain.AgentURI})
	}
	if err := readAgentVerifyJSON(filepath.Join(root, *artifactPath), &artifact); err != nil {
		addCheck("proof.runtimeArtifact", agentVerifyCheck{OK: false, Error: err.Error()})
	} else {
		addCheck("proof.runtimeArtifact", agentVerifyCheck{OK: true, Detail: artifact.ArtifactID})
	}
	if err := readAgentVerifyJSON(filepath.Join(root, *receiptPath), &receipt); err != nil {
		addCheck("proof.runtimeReceipt", agentVerifyCheck{OK: false, Error: err.Error()})
	} else {
		addCheck("proof.runtimeReceipt", agentVerifyCheck{OK: true, Detail: receipt.JobID})
	}
	verifyAgentRegistry(*rpcURL, publication, &result, addCheck)
	verifyRuntimeRegistry(*rpcURL, artifact, receipt, &result, addCheck)
	verifyIPFS(publication, addCheck)
	verifyOrganismStatus(root, result.AgentDID, publication, &result, addCheck)
	verifyRWProjection(root, publication, artifact, receipt, addCheck)
	out, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	fmt.Println(string(out))
	if !result.OK {
		return fmt.Errorf("agent verify failed")
	}
	return nil
}

func readAgentVerifyJSON(path string, target any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	return json.Unmarshal(data, target)
}

func verifyAgentRegistry(rpcURL string, proof agentPublicationProof, result *agentVerifyResult, add func(string, agentVerifyCheck)) {
	tokenID := strconv.Itoa(proof.Chain.TokenID)
	chainToken, err := castAgentVerify(rpcURL, defaultAgentRegistry, "tokenByRootDid(bytes32)(uint256)", proof.Chain.RootDIDHash)
	if err != nil {
		add("chain.erc8004.tokenByRootDid", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	add("chain.erc8004.tokenByRootDid", agentVerifyCheck{OK: strings.TrimSpace(chainToken) == tokenID, Detail: strings.TrimSpace(chainToken)})
	chainURI, err := castAgentVerify(rpcURL, defaultAgentRegistry, "agentURI(uint256)(string)", tokenID)
	if err != nil {
		add("chain.erc8004.agentURI", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	chainURI = strings.Trim(strings.TrimSpace(chainURI), `"`)
	add("chain.erc8004.agentURI", agentVerifyCheck{OK: chainURI == proof.Chain.AgentURI, Detail: chainURI})
	result.Evidence["erc8004"] = map[string]any{"tokenId": tokenID, "agentURI": chainURI, "txHash": proof.Chain.TxHash}
}

func verifyRuntimeRegistry(rpcURL string, artifact agentRuntimeArtifactProof, receipt agentRuntimeReceiptProof, result *agentVerifyResult, add func(string, agentVerifyCheck)) {
	version, err := castAgentVerify(rpcURL, defaultRuntimeRegistry, "artifactVersionCount(bytes32)(uint32)", artifact.ArtifactID)
	if err != nil {
		add("chain.runtime.artifact", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	add("chain.runtime.artifact", agentVerifyCheck{OK: strings.TrimSpace(version) == strconv.Itoa(artifact.Version), Detail: strings.TrimSpace(version)})
	chainReceipt, err := castAgentVerify(rpcURL, defaultRuntimeRegistry, "receipts(bytes32)((bytes32,bytes32,bytes32,bytes32,bytes32,bytes32,bytes32,uint64,uint64,address))", receipt.JobID)
	if err != nil {
		add("chain.runtime.receipt", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	ok := strings.Contains(strings.ToLower(chainReceipt), strings.ToLower(receipt.ArtifactID))
	add("chain.runtime.receipt", agentVerifyCheck{OK: ok, Detail: receipt.JobID})
	result.Evidence["runtime"] = map[string]any{"artifactId": artifact.ArtifactID, "receiptJobId": receipt.JobID, "receiptTxHash": receipt.TxHash}
}

func verifyIPFS(proof agentPublicationProof, add func(string, agentVerifyCheck)) {
	url := proof.AgentRegistration.GatewayURL
	if url == "" && proof.AgentRegistration.CID != "" {
		url = "https://ipfs.etzhayyim.com/ipfs/" + proof.AgentRegistration.CID
	}
	if url == "" {
		add("ipfs.registration", agentVerifyCheck{OK: false, Error: "gateway URL missing"})
		return
	}
	client := http.Client{Timeout: 15 * time.Second}
	resp, err := client.Get(url)
	if err != nil {
		add("ipfs.registration", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	defer resp.Body.Close()
	io.Copy(io.Discard, resp.Body)
	add("ipfs.registration", agentVerifyCheck{OK: resp.StatusCode == http.StatusOK, Detail: resp.Status})
}

func verifyOrganismStatus(root string, agentDID string, proof agentPublicationProof, result *agentVerifyResult, add func(string, agentVerifyCheck)) {
	cmd, err := agentCommand(root, organismStatusCLIName, organismPythonStatusModule, "--agent-did", agentDID, "--json")
	if err != nil {
		add("organism.status", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	out, err := cmd.Output()
	if err != nil {
		add("organism.status", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	var status struct {
		OrganismState string `json:"organismState"`
		ERC8004       struct {
			AgentID string `json:"agentId"`
		} `json:"erc8004"`
	}
	if err := json.Unmarshal(out, &status); err != nil {
		add("organism.status", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	wantID := strconv.Itoa(proof.Chain.TokenID)
	add("organism.status", agentVerifyCheck{OK: status.ERC8004.AgentID == wantID, Detail: "state=" + status.OrganismState + " agentId=" + status.ERC8004.AgentID})
	result.Evidence["organismState"] = status.OrganismState
}

func verifyRWProjection(root string, publication agentPublicationProof, artifact agentRuntimeArtifactProof, receipt agentRuntimeReceiptProof, add func(string, agentVerifyCheck)) {
	script := `
import os, json
from pymagatama.local_agent_env import load_env_file, load_keychain_secret
load_env_file()
if not os.environ.get("RW_URL"):
    os.environ["RW_URL"] = load_keychain_secret(service="gftd.rw", account="ROOT_URL")
from pymagatama.db_sync import sync_cursor
with sync_cursor() as cur:
    cur.execute("SELECT COUNT(*) FROM vertex_agent_publication WHERE token_id=%s AND status='verified'", (os.environ["VERIFY_TOKEN_ID"],))
    p = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vertex_agent_runtime_artifact WHERE artifact_id=%s AND status='verified'", (os.environ["VERIFY_ARTIFACT_ID"],))
    a = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM vertex_agent_runtime_receipt WHERE job_id=%s AND status='verified'", (os.environ["VERIFY_JOB_ID"],))
    r = cur.fetchone()[0]
print(json.dumps({"publication": p, "artifact": a, "receipt": r}))
`
	python := filepath.Join(root, "20-actors", "magatama", "py", ".venv", "bin", "python")
	cmd := exec.Command(python, "-c", script)
	cmd.Env = append(agentCommandEnv(root),
		"VERIFY_TOKEN_ID="+strconv.Itoa(publication.Chain.TokenID),
		"VERIFY_ARTIFACT_ID="+artifact.ArtifactID,
		"VERIFY_JOB_ID="+receipt.JobID,
	)
	out, err := cmd.Output()
	if err != nil {
		add("rw.projection", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	var counts map[string]int
	if err := json.Unmarshal(bytes.TrimSpace(out), &counts); err != nil {
		add("rw.projection", agentVerifyCheck{OK: false, Error: err.Error()})
		return
	}
	ok := counts["publication"] > 0 && counts["artifact"] > 0 && counts["receipt"] > 0
	add("rw.projection", agentVerifyCheck{OK: ok, Detail: fmt.Sprintf("publication=%d artifact=%d receipt=%d", counts["publication"], counts["artifact"], counts["receipt"])})
}

func castAgentVerify(rpcURL string, contract string, signature string, args ...string) (string, error) {
	cmdArgs := append([]string{"call", contract, signature}, args...)
	cmdArgs = append(cmdArgs, "--rpc-url", rpcURL)
	out, err := exec.Command("cast", cmdArgs...).CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("cast call %s: %w: %s", signature, err, truncateForLog(string(out), 400))
	}
	return string(out), nil
}
