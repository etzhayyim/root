package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func runAgentOrganismPublish(args []string) error {
	fs := flag.NewFlagSet("agent organism publish", flag.ContinueOnError)
	agentDID := fs.String("agent-did", agentEnvDefault("AGENT_DID", defaultOrganismAgentDID), "agent DID to publish")
	out := fs.String("out", "90-docs/proof/kami-agent-erc8004-registration.local.json", "rendered registration JSON path")
	proofOut := fs.String("proof-out", "90-docs/proof/kami-agent-erc8004-publish-attempt.local.json", "publish/update proof JSON path")
	ipfsBase := fs.String("ipfs", defaultIPFSGateway, "IPFS gateway/proxy base URL")
	rpcURL := fs.String("rpc-url", defaultPrivateChainRPC, "private-chain RPC URL")
	chainID := fs.String("chain-id", defaultPrivateChainID, "private-chain ID")
	registry := fs.String("registry", defaultAgentRegistryAddress, "GftdAgentRegistry address")
	tokenID := fs.String("token-id", agentEnvDefault("AGENT_ERC8004_AGENT_ID", "3"), "ERC-8004 token id to update")
	dryRun := fs.Bool("dry-run", true, "render and plan without writing to IPFS or chain")
	submitChain := fs.Bool("submit-chain", false, "after IPFS publish, update agentURI via Safe setAgentURI")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if fs.NArg() != 0 {
		return fmt.Errorf("unexpected arguments: %s", strings.Join(fs.Args(), " "))
	}
	if strings.TrimSpace(*agentDID) == "" {
		return fmt.Errorf("--agent-did must not be empty")
	}
	if !*dryRun && *submitChain && strings.TrimSpace(*tokenID) == "" {
		return fmt.Errorf("--token-id is required with --submit-chain")
	}

	root := agentRepoRoot()
	publishArgs := []string{
		"--agent-did", *agentDID,
		"--out", agentRepoPath(root, *out),
		"--publish-ipfs",
		"--ipfs", *ipfsBase,
		"--publish-proof-out", agentRepoPath(root, *proofOut),
	}
	if !*dryRun {
		publishArgs = append(publishArgs, "--no-dry-run")
	}
	cmd, err := agentCommand(root, organismPublishCLIName, organismPythonPublishModule, publishArgs...)
	if err != nil {
		return err
	}
	cmd.Dir = root
	publishOutput, err := cmd.CombinedOutput()
	if err != nil {
		return fmt.Errorf("publish agent registration failed: %w: %s", err, truncateForLog(string(publishOutput), 1200))
	}

	var proof map[string]any
	if err := readAgentVerifyJSON(agentRepoPath(root, *proofOut), &proof); err != nil {
		return err
	}
	agentRegistration, _ := proof["agentRegistration"].(map[string]any)
	agentURI := strings.TrimSpace(fmt.Sprint(agentRegistration["uri"]))
	metadataHash := strings.TrimSpace(fmt.Sprint(agentRegistration["sha256"]))
	result := map[string]any{
		"ok":                true,
		"dryRun":            *dryRun,
		"agentDid":          *agentDID,
		"registrationOut":   *out,
		"proofOut":          *proofOut,
		"agentRegistration": agentRegistration,
		"chain": map[string]any{
			"submitChain": *submitChain,
			"submitted":   false,
			"chainId":     *chainID,
			"rpcUrl":      *rpcURL,
			"registry":    *registry,
			"tokenId":     *tokenID,
		},
	}
	if *submitChain {
		if *dryRun {
			result["ok"] = false
			result["chain"].(map[string]any)["blocked"] = "submit-chain requires --no-dry-run"
		} else {
			tx, err := sendSetAgentURIViaSafe(root, *rpcURL, *chainID, *registry, *tokenID, agentURI, metadataHash)
			if err != nil {
				return err
			}
			chain := result["chain"].(map[string]any)
			chain["submitted"] = true
			chain["txHash"] = tx.TxHash
			chain["safeTxHash"] = tx.SafeTxHash
			chain["agentURI"] = agentURI
			chain["metadataHash"] = metadataHash
			proof["chain"] = chain
			if err := writeJSONFile(agentRepoPath(root, *proofOut), proof); err != nil {
				return err
			}
		}
	}
	outBytes, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	fmt.Println(string(outBytes))
	if !result["ok"].(bool) {
		return fmt.Errorf("agent organism publish blocked")
	}
	return nil
}

func agentRepoPath(root string, path string) string {
	if filepath.IsAbs(path) {
		return path
	}
	return filepath.Join(root, path)
}

type safeSetAgentURIResult struct {
	TxHash     string
	SafeTxHash string
}

func sendSetAgentURIViaSafe(root, rpcURL, chainID, registry, tokenID, agentURI, metadataHash string) (safeSetAgentURIResult, error) {
	if !isHexAddress(registry) {
		return safeSetAgentURIResult{}, fmt.Errorf("--registry must be an EVM address")
	}
	if !isBytes32Hex(metadataHash) {
		return safeSetAgentURIResult{}, fmt.Errorf("metadata hash must be bytes32 hex")
	}
	calldataOut, err := exec.Command("cast", "calldata", "setAgentURI(uint256,string,bytes32)", tokenID, agentURI, metadataHash).CombinedOutput()
	if err != nil {
		return safeSetAgentURIResult{}, fmt.Errorf("cast calldata setAgentURI failed: %w: %s", err, truncateForLog(string(calldataOut), 400))
	}
	k1, err := keychainGet("gftd.safe-owners", "K1_PRIV")
	if err != nil || k1 == "" {
		return safeSetAgentURIResult{}, fmt.Errorf("K1_PRIV missing in macOS Keychain service gftd.safe-owners")
	}
	k2, err := keychainGet("gftd.safe-owners", "K2_PRIV")
	if err != nil || k2 == "" {
		return safeSetAgentURIResult{}, fmt.Errorf("K2_PRIV missing in macOS Keychain service gftd.safe-owners")
	}
	sender, err := keychainGet("gftd.private-chain", "SEALER_PRIV")
	if err != nil || sender == "" {
		return safeSetAgentURIResult{}, fmt.Errorf("SEALER_PRIV missing in macOS Keychain service gftd.private-chain")
	}
	contractsDir := filepath.Join(root, "50-infra", "vultr", "geth-private", "contracts")
	cmd := exec.Command("forge", "script", "script/ExecSafeCall.s.sol", "--rpc-url", rpcURL, "--broadcast", "--legacy")
	cmd.Dir = contractsDir
	cmd.Env = append(os.Environ(),
		"FOUNDRY_DISABLE_NIGHTLY_WARNING=1",
		"K1_PRIV="+k1,
		"K2_PRIV="+k2,
		"SENDER_PRIV="+sender,
		"TARGET="+registry,
		"CALLDATA="+strings.TrimSpace(string(calldataOut)),
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		return safeSetAgentURIResult{}, fmt.Errorf("Safe setAgentURI failed: %w: %s", err, truncateForLog(string(out), 1200))
	}
	txHash, err := readLatestSafeBroadcastTxHash(contractsDir, chainID)
	if err != nil {
		return safeSetAgentURIResult{}, err
	}
	return safeSetAgentURIResult{TxHash: txHash, SafeTxHash: extractSafeTxHash(string(out))}, nil
}

func readLatestSafeBroadcastTxHash(contractsDir string, chainID string) (string, error) {
	path := filepath.Join(contractsDir, "broadcast", "ExecSafeCall.s.sol", chainID, "run-latest.json")
	var payload struct {
		Transactions []struct {
			Hash            string `json:"hash"`
			TransactionType string `json:"transactionType"`
		} `json:"transactions"`
	}
	if err := readAgentVerifyJSON(path, &payload); err != nil {
		return "", err
	}
	for _, tx := range payload.Transactions {
		if tx.TransactionType == "CALL" && strings.HasPrefix(tx.Hash, "0x") {
			return tx.Hash, nil
		}
	}
	return "", fmt.Errorf("Safe broadcast tx hash not found in %s", path)
}

func extractSafeTxHash(output string) string {
	lines := strings.Split(output, "\n")
	for i, line := range lines {
		if strings.TrimSpace(line) == "txHash:" && i+1 < len(lines) {
			return strings.TrimSpace(lines[i+1])
		}
	}
	return ""
}

func writeJSONFile(path string, value any) error {
	out, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return err
	}
	out = append(out, '\n')
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return err
	}
	return os.WriteFile(path, out, 0o644)
}
