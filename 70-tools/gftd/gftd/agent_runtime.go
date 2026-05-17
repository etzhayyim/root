package main

import (
	"bytes"
	"crypto/hmac"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"

	"golang.org/x/crypto/sha3"
)

const (
	agentRuntimeSchema          = "https://etzhayyim.com/schemas/k8s-runtime-public/v1.json"
	defaultIPFSGateway          = "https://ipfs.etzhayyim.com"
	defaultPrivateChainRPC      = "https://geth.etzhayyim.com"
	defaultPrivateChainID       = "260425"
	defaultAgentRegistryAddress = "0xcA3480edDAfa39c9377B83eEB18291286C8Cb865"
)

func runAgentRuntime(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("agent-runtime subcommand required: render, publish")
	}
	switch args[0] {
	case "render":
		return runAgentRuntimeRender(args[1:])
	case "publish":
		return runAgentRuntimePublish(args[1:])
	case "register":
		return runAgentRuntimeRegister(args[1:])
	case "publish-agent":
		return runAgentRuntimePublishAgent(args[1:])
	case "holochain-plan":
		return runAgentRuntimeHolochainPlan(args[1:])
	case "help", "--help", "-h":
		fmt.Fprintln(os.Stderr, "Usage: gftd agent-runtime <render|publish|register|publish-agent|holochain-plan> [flags]")
		return nil
	default:
		return fmt.Errorf("unknown agent-runtime subcommand %q. Available: render, publish, register, publish-agent, holochain-plan", args[0])
	}
}

func runAgentRuntimeRender(args []string) error {
	fs := flag.NewFlagSet("agent-runtime render", flag.ContinueOnError)
	cluster := fs.String("cluster", "", "public cluster label (required)")
	out := fs.String("out", "", "output JSON path (default stdout)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *cluster == "" {
		return fmt.Errorf("--cluster is required")
	}
	if fs.NArg() == 0 {
		return fmt.Errorf("at least one k8s manifest path is required")
	}
	rendered, err := renderAgentRuntimePublic(*cluster, fs.Args())
	if err != nil {
		return err
	}
	if *out == "" {
		fmt.Print(string(rendered))
		return nil
	}
	if err := os.MkdirAll(filepath.Dir(*out), 0o755); err != nil {
		return err
	}
	return os.WriteFile(*out, rendered, 0o644)
}

func runAgentRuntimePublish(args []string) error {
	fs := flag.NewFlagSet("agent-runtime publish", flag.ContinueOnError)
	cluster := fs.String("cluster", "", "public cluster label (required)")
	out := fs.String("out", "", "optional output JSON path")
	ipfsBase := fs.String("ipfs", defaultIPFSGateway, "IPFS gateway/proxy base URL")
	dryRun := fs.Bool("dry-run", true, "render and hash without writing to IPFS")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *cluster == "" {
		return fmt.Errorf("--cluster is required")
	}
	if fs.NArg() == 0 {
		return fmt.Errorf("at least one k8s manifest path is required")
	}
	rendered, err := renderAgentRuntimePublic(*cluster, fs.Args())
	if err != nil {
		return err
	}
	sum := sha256.Sum256(rendered)
	result := map[string]any{
		"ok":        true,
		"dryRun":    *dryRun,
		"sha256":    "0x" + hex.EncodeToString(sum[:]),
		"bytes":     len(rendered),
		"schema":    agentRuntimeSchema,
		"kind":      "k8s-runtime",
		"ipfsBase":  strings.TrimRight(*ipfsBase, "/"),
		"published": false,
	}
	if !*dryRun {
		cid, err := ipfsAddJSON(*ipfsBase, "k8s-runtime-public.json", rendered)
		if err != nil {
			return err
		}
		result["published"] = true
		result["cid"] = cid
		result["uri"] = "ipfs://" + cid
		result["gatewayUrl"] = strings.TrimRight(*ipfsBase, "/") + "/ipfs/" + cid
	}
	outBytes, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	outBytes = append(outBytes, '\n')
	if *out != "" {
		if err := os.MkdirAll(filepath.Dir(*out), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(*out, outBytes, 0o644); err != nil {
			return err
		}
	}
	fmt.Print(string(outBytes))
	return nil
}

func runAgentRuntimeRegister(args []string) error {
	fs := flag.NewFlagSet("agent-runtime register", flag.ContinueOnError)
	registrationPath := fs.String("registration", "", "ERC-8004 agent registration JSON path; used to derive root DID, owner, and metadata hash")
	agentURI := fs.String("agent-uri", "", "published ERC-8004 agent registration URI, usually ipfs://... (required)")
	rootDID := fs.String("root-did", "", "ERC-725 root DID; defaults to registration.rootIdentity.rootDid")
	agentOwner := fs.String("owner", "", "agent owner address; defaults to registration.rootIdentity.address when non-zero")
	metadataHash := fs.String("metadata-hash", "", "bytes32 metadata hash; defaults to sha256(registration JSON)")
	registry := fs.String("registry", defaultAgentRegistryAddress, "GftdAgentRegistry address")
	rpcURL := fs.String("rpc-url", defaultPrivateChainRPC, "private-chain RPC URL")
	chainID := fs.String("chain-id", defaultPrivateChainID, "private-chain ID")
	out := fs.String("out", "", "optional output JSON path")
	dryRun := fs.Bool("dry-run", true, "build registration transaction without broadcasting")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *agentURI == "" {
		return fmt.Errorf("--agent-uri is required")
	}

	var registrationBytes []byte
	var registration agentRegistrationDocument
	if *registrationPath != "" {
		var err error
		registrationBytes, err = os.ReadFile(*registrationPath)
		if err != nil {
			return err
		}
		if err := json.Unmarshal(registrationBytes, &registration); err != nil {
			return fmt.Errorf("parse registration JSON: %w", err)
		}
		if *rootDID == "" {
			*rootDID = strings.TrimSpace(registration.RootIdentity.RootDID)
		}
		if *agentOwner == "" && !isZeroAddress(registration.RootIdentity.Address) {
			*agentOwner = strings.TrimSpace(registration.RootIdentity.Address)
		}
		if *metadataHash == "" {
			sum := sha256.Sum256(registrationBytes)
			*metadataHash = "0x" + hex.EncodeToString(sum[:])
		}
	}
	if *rootDID == "" {
		return fmt.Errorf("--root-did is required when --registration does not provide rootIdentity.rootDid")
	}
	if *agentOwner == "" {
		return fmt.Errorf("--owner is required when --registration does not provide a non-zero rootIdentity.address")
	}
	if *metadataHash == "" {
		*metadataHash = "0x" + strings.Repeat("0", 64)
	}
	if !isHexAddress(*agentOwner) {
		return fmt.Errorf("--owner must be an EVM address")
	}
	if !isHexAddress(*registry) {
		return fmt.Errorf("--registry must be an EVM address")
	}
	if !isBytes32Hex(*metadataHash) {
		return fmt.Errorf("--metadata-hash must be bytes32 hex")
	}
	rootDIDHash, err := castKeccak(*rootDID)
	if err != nil {
		return err
	}

	result := map[string]any{
		"ok":           true,
		"dryRun":       *dryRun,
		"chainId":      *chainID,
		"rpcUrl":       *rpcURL,
		"registry":     *registry,
		"rootDid":      *rootDID,
		"rootDidHash":  rootDIDHash,
		"owner":        *agentOwner,
		"agentURI":     *agentURI,
		"metadataHash": *metadataHash,
		"submitted":    false,
	}
	if !*dryRun {
		txHash, err := sendRegisterAgent(*rpcURL, *chainID, *registry, rootDIDHash, *agentOwner, *agentURI, *metadataHash)
		if err != nil {
			return err
		}
		result["submitted"] = true
		result["txHash"] = txHash
	}
	outBytes, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	outBytes = append(outBytes, '\n')
	if *out != "" {
		if err := os.MkdirAll(filepath.Dir(*out), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(*out, outBytes, 0o644); err != nil {
			return err
		}
	}
	fmt.Print(string(outBytes))
	return nil
}

func runAgentRuntimePublishAgent(args []string) error {
	fs := flag.NewFlagSet("agent-runtime publish-agent", flag.ContinueOnError)
	registrationPath := fs.String("registration", "", "ERC-8004 agent registration JSON template path (required)")
	cluster := fs.String("cluster", "", "public cluster label (required)")
	rootDID := fs.String("root-did", "", "ERC-725 root DID; defaults to registration.rootIdentity.rootDid")
	agentOwner := fs.String("owner", "", "agent owner address; defaults to registration.rootIdentity.address when non-zero")
	registry := fs.String("registry", defaultAgentRegistryAddress, "GftdAgentRegistry address")
	rpcURL := fs.String("rpc-url", defaultPrivateChainRPC, "private-chain RPC URL")
	chainID := fs.String("chain-id", defaultPrivateChainID, "private-chain ID")
	ipfsBase := fs.String("ipfs", defaultIPFSGateway, "IPFS gateway/proxy base URL")
	out := fs.String("out", "", "optional output JSON path")
	updatedRegistrationOut := fs.String("registration-out", "", "optional rendered registration JSON path")
	dryRun := fs.Bool("dry-run", true, "render, hash, and plan without writing to IPFS or chain")
	submitChain := fs.Bool("submit-chain", false, "submit registerAgent transaction after publishing; requires --dry-run=false")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *registrationPath == "" {
		return fmt.Errorf("--registration is required")
	}
	if *cluster == "" {
		return fmt.Errorf("--cluster is required")
	}
	if fs.NArg() == 0 {
		return fmt.Errorf("at least one k8s manifest path is required")
	}

	runtimePublic, err := renderAgentRuntimePublic(*cluster, fs.Args())
	if err != nil {
		return err
	}
	runtimeSum := sha256.Sum256(runtimePublic)
	runtimeCID := "DRY_RUN_RUNTIME_CID"
	if !*dryRun {
		runtimeCID, err = ipfsAddJSON(*ipfsBase, "k8s-runtime-public.json", runtimePublic)
		if err != nil {
			return err
		}
	}
	runtimeURI := "ipfs://" + runtimeCID

	registrationBytes, err := os.ReadFile(*registrationPath)
	if err != nil {
		return err
	}
	var registration agentRegistrationDocument
	if err := json.Unmarshal(registrationBytes, &registration); err != nil {
		return fmt.Errorf("parse registration JSON: %w", err)
	}
	if *rootDID == "" {
		*rootDID = strings.TrimSpace(registration.RootIdentity.RootDID)
	}
	if *agentOwner == "" && !isZeroAddress(registration.RootIdentity.Address) {
		*agentOwner = strings.TrimSpace(registration.RootIdentity.Address)
	}
	if *submitChain && *dryRun {
		return fmt.Errorf("--submit-chain requires --dry-run=false")
	}
	if *submitChain && *rootDID == "" {
		return fmt.Errorf("--root-did is required to submit chain registration")
	}
	if *submitChain && *agentOwner == "" {
		return fmt.Errorf("--owner is required to submit chain registration")
	}
	if *agentOwner != "" && !isHexAddress(*agentOwner) {
		return fmt.Errorf("--owner must be an EVM address")
	}
	if !isHexAddress(*registry) {
		return fmt.Errorf("--registry must be an EVM address")
	}

	renderedRegistration, err := renderAgentRegistration(registrationBytes, *chainID, *registry, runtimeURI)
	if err != nil {
		return err
	}
	registrationSum := sha256.Sum256(renderedRegistration)
	metadataHash := "0x" + hex.EncodeToString(registrationSum[:])
	agentCID := "DRY_RUN_AGENT_REGISTRATION_CID"
	if !*dryRun {
		agentCID, err = ipfsAddJSON(*ipfsBase, "agent-registration.json", renderedRegistration)
		if err != nil {
			return err
		}
	}
	agentURI := "ipfs://" + agentCID
	rootDIDHash := ""
	if *rootDID != "" {
		rootDIDHash, err = castKeccak(*rootDID)
		if err != nil {
			return err
		}
	}

	result := map[string]any{
		"ok":     true,
		"dryRun": *dryRun,
		"runtime": map[string]any{
			"schema":    agentRuntimeSchema,
			"sha256":    "0x" + hex.EncodeToString(runtimeSum[:]),
			"bytes":     len(runtimePublic),
			"cid":       runtimeCID,
			"uri":       runtimeURI,
			"published": !*dryRun,
		},
		"agentRegistration": map[string]any{
			"sha256":    metadataHash,
			"bytes":     len(renderedRegistration),
			"cid":       agentCID,
			"uri":       agentURI,
			"published": !*dryRun,
		},
		"chain": map[string]any{
			"chainId":      *chainID,
			"rpcUrl":       *rpcURL,
			"registry":     *registry,
			"rootDid":      *rootDID,
			"rootDidHash":  rootDIDHash,
			"owner":        *agentOwner,
			"metadataHash": metadataHash,
			"submitChain":  *submitChain,
			"submitted":    false,
		},
		"ipfsBase": strings.TrimRight(*ipfsBase, "/"),
	}
	if *updatedRegistrationOut != "" {
		if err := os.MkdirAll(filepath.Dir(*updatedRegistrationOut), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(*updatedRegistrationOut, renderedRegistration, 0o644); err != nil {
			return err
		}
	}
	if !*dryRun && *submitChain {
		txHash, err := sendRegisterAgent(*rpcURL, *chainID, *registry, rootDIDHash, *agentOwner, agentURI, metadataHash)
		if err != nil {
			return err
		}
		chainResult := result["chain"].(map[string]any)
		chainResult["submitted"] = true
		chainResult["txHash"] = txHash
	}
	outBytes, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	outBytes = append(outBytes, '\n')
	if *out != "" {
		if err := os.MkdirAll(filepath.Dir(*out), 0o755); err != nil {
			return err
		}
		if err := os.WriteFile(*out, outBytes, 0o644); err != nil {
			return err
		}
	}
	fmt.Print(string(outBytes))
	return nil
}

func renderAgentRuntimePublic(cluster string, manifests []string) ([]byte, error) {
	root := agentRuntimeRepoRoot()
	script := filepath.Join(root, "70-tools/scripts/contract/render-agent-runtime-public.py")
	cmdArgs := append([]string{script, "--cluster", cluster}, manifests...)
	cmd := exec.Command("python3", cmdArgs...)
	cmd.Dir = root
	out, err := cmd.CombinedOutput()
	if err != nil {
		return nil, fmt.Errorf("render public runtime: %w: %s", err, truncateForLog(string(out), 1600))
	}
	return out, nil
}

func agentRuntimeRepoRoot() string {
	cwd, _ := os.Getwd()
	if root, err := findGitRoot(cwd); err == nil {
		return root
	}
	return cwd
}

func ipfsAddJSON(ipfsBase, filename string, body []byte) (string, error) {
	hmacKey, err := keychainGet("gftd.cloudflare", "IPFS_HMAC")
	if err != nil || hmacKey == "" {
		return "", fmt.Errorf("IPFS_HMAC missing in macOS Keychain; rerun with --dry-run or provision gftd.cloudflare/IPFS_HMAC")
	}
	var form bytes.Buffer
	writer := multipart.NewWriter(&form)
	part, err := writer.CreateFormFile("file", filename)
	if err != nil {
		return "", err
	}
	if _, err := part.Write(body); err != nil {
		return "", err
	}
	if err := writer.Close(); err != nil {
		return "", err
	}

	endpoint := strings.TrimRight(ipfsBase, "/") + "/api/v0/add?pin=true&cid-version=1"
	req, err := http.NewRequest(http.MethodPost, endpoint, bytes.NewReader(form.Bytes()))
	if err != nil {
		return "", err
	}
	req.Header.Set("content-type", writer.FormDataContentType())
	req.Header.Set("x-gftd-ipfs-auth", hmacSHA256Hex(hmacKey, form.Bytes()))
	client := &http.Client{Timeout: 30 * time.Second}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("ipfs add HTTP %d: %s", resp.StatusCode, truncateForLog(string(respBody), 400))
	}
	var parsed struct {
		Hash string `json:"Hash"`
		CID  string `json:"Cid"`
		Name string `json:"Name"`
	}
	if err := json.Unmarshal(respBody, &parsed); err != nil {
		return "", fmt.Errorf("parse ipfs add response: %w: %s", err, truncateForLog(string(respBody), 400))
	}
	cid := strings.TrimSpace(parsed.Hash)
	if cid == "" {
		cid = strings.TrimSpace(parsed.CID)
	}
	if cid == "" {
		return "", fmt.Errorf("ipfs add response missing CID: %s", truncateForLog(string(respBody), 400))
	}

	// Best-effort explicit pin for Kubo proxies that ignore add?pin=true.
	_ = ipfsPin(ipfsBase, hmacKey, cid)
	return cid, nil
}

func ipfsPin(ipfsBase, hmacKey, cid string) error {
	values := url.Values{}
	values.Set("arg", cid)
	values.Set("recursive", "true")
	body := []byte(values.Encode())
	req, err := http.NewRequest(http.MethodPost, strings.TrimRight(ipfsBase, "/")+"/api/v0/pin/add", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("content-type", "application/x-www-form-urlencoded")
	req.Header.Set("x-gftd-ipfs-auth", hmacSHA256Hex(hmacKey, body))
	resp, err := (&http.Client{Timeout: 15 * time.Second}).Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("pin HTTP %d", resp.StatusCode)
	}
	return nil
}

func renderAgentRegistration(template []byte, chainID, registry, runtimeURI string) ([]byte, error) {
	var doc map[string]any
	if err := json.Unmarshal(template, &doc); err != nil {
		return nil, fmt.Errorf("parse registration template: %w", err)
	}
	if agent, ok := doc["agent"].(map[string]any); ok {
		agent["agentRegistry"] = "eip155:" + chainID + ":" + registry
	}
	if protocols, ok := doc["protocols"].([]any); ok {
		for _, item := range protocols {
			protocol, ok := item.(map[string]any)
			if !ok {
				continue
			}
			switch protocol["kind"] {
			case "k8s-runtime":
				protocol["publicManifestCid"] = runtimeURI
			case "ipfs-publication":
				if artifacts, ok := protocol["artifacts"].([]any); ok {
					found := false
					for i, artifact := range artifacts {
						if s, ok := artifact.(string); ok && strings.Contains(s, "TBD_PUBLIC_RUNTIME_MANIFEST_CID") {
							artifacts[i] = runtimeURI
							found = true
						}
					}
					if !found {
						protocol["artifacts"] = append(artifacts, runtimeURI)
					}
				} else {
					protocol["artifacts"] = []any{runtimeURI}
				}
			}
		}
	}
	out, err := json.MarshalIndent(doc, "", "  ")
	if err != nil {
		return nil, err
	}
	return append(out, '\n'), nil
}

type agentRegistrationDocument struct {
	RootIdentity struct {
		Address string `json:"address"`
		RootDID string `json:"rootDid"`
	} `json:"rootIdentity"`
}

func castKeccak(value string) (string, error) {
	if _, err := exec.LookPath("cast"); err == nil {
		cmd := exec.Command("cast", "keccak", value)
		out, err := cmd.CombinedOutput()
		if err != nil {
			return "", fmt.Errorf("cast keccak failed: %w: %s", err, truncateForLog(string(out), 300))
		}
		hash := strings.TrimSpace(string(out))
		if !isBytes32Hex(hash) {
			return "", fmt.Errorf("cast keccak returned invalid bytes32: %q", hash)
		}
		return hash, nil
	}
	hasher := sha3.NewLegacyKeccak256()
	_, _ = hasher.Write([]byte(value))
	hash := "0x" + hex.EncodeToString(hasher.Sum(nil))
	if !isBytes32Hex(hash) {
		return "", fmt.Errorf("keccak returned invalid bytes32: %q", hash)
	}
	return hash, nil
}

func sendRegisterAgent(rpcURL, chainID, registry, rootDIDHash, agentOwner, agentURI, metadataHash string) (string, error) {
	if _, err := exec.LookPath("cast"); err != nil {
		return "", fmt.Errorf("cast is required to register agent on-chain: %w", err)
	}
	sealerPriv, err := keychainGet("gftd.private-chain", "SEALER_PRIV")
	if err != nil || sealerPriv == "" {
		return "", fmt.Errorf("SEALER_PRIV missing in macOS Keychain service gftd.private-chain")
	}
	cmd := exec.Command(
		"cast", "send",
		"--rpc-url", rpcURL,
		"--private-key", sealerPriv,
		"--chain-id", chainID,
		"--gas-price", "1500000000",
		"--legacy",
		registry,
		"registerAgent(bytes32,address,string,bytes32)",
		rootDIDHash,
		agentOwner,
		agentURI,
		metadataHash,
	)
	cmd.Env = append(os.Environ(), "FOUNDRY_DISABLE_NIGHTLY_WARNING=1")
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("cast send registerAgent failed: %w: %s", err, truncateForLog(string(out), 600))
	}
	return extractCastTxHash(string(out)), nil
}

func isHexAddress(value string) bool {
	value = strings.TrimSpace(value)
	if len(value) != 42 || !strings.HasPrefix(value, "0x") {
		return false
	}
	_, err := hex.DecodeString(value[2:])
	return err == nil
}

func isZeroAddress(value string) bool {
	return strings.EqualFold(strings.TrimSpace(value), "0x0000000000000000000000000000000000000000")
}

func isBytes32Hex(value string) bool {
	value = strings.TrimSpace(value)
	if len(value) != 66 || !strings.HasPrefix(value, "0x") {
		return false
	}
	_, err := hex.DecodeString(value[2:])
	return err == nil
}

func hmacSHA256Hex(key string, body []byte) string {
	mac := hmac.New(sha256.New, []byte(key))
	mac.Write(body)
	return hex.EncodeToString(mac.Sum(nil))
}
