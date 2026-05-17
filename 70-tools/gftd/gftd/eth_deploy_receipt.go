package main

import (
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

// ADR-0074 Phase 2-A.4 — record an immutable deploy receipt on the gftd
// private chain (260425). Best-effort, non-fatal: if any prerequisite is
// missing the deploy still completes and we just emit a single-line stderr
// note.
//
// Why this exists: `registerProfileToYata` writes to a mutable graph node
// that anyone with write access can later overwrite. There's no
// cryptographic provenance for "this version of this app was deployed at
// this time by this signer". `DeployRegistry.recordDeploy(...)` mints one
// `Deployed` event per call; the event log on chain 260425 becomes the
// authoritative version lineage.
//
// Path of least resistance for now: shell out to Foundry's `cast send`,
// which is already a hard dep for the local contract test/deploy loop and
// signs locally without requiring the sealer key to leave the machine.
// If `cast` isn't on PATH, we skip with a one-line note rather than
// blocking the deploy.
func recordDeployToChain(cfg *magatamaJSONLD, appID string, compDir string) {
	const (
		chainID        = "260425"
		deployRegistry = "0x995AD6A2bb4D8916Ba036f5B2e29E7739Ee243b5"
		rpcURL         = "https://geth.etzhayyim.com"
	)

	if _, err := exec.LookPath("cast"); err != nil {
		// Foundry isn't installed. The deploy was successful — provenance
		// is just an additive feature, no need to surface this loudly on
		// every machine that doesn't have it.
		return
	}

	sealerPriv, err := keychainGet("gftd.private-chain", "SEALER_PRIV")
	if err != nil || sealerPriv == "" {
		fmt.Fprintln(os.Stderr, "  [deploy-receipt] SEALER_PRIV missing in macOS Keychain — skipping on-chain receipt")
		return
	}

	nanoid := strings.TrimSpace(cfg.Nanoid)
	if nanoid == "" {
		nanoid = appID
	}
	// bytes32 carries up to 32 ASCII chars. nanoid is 8, slugs ~12 — fits.
	if len(nanoid) > 32 {
		nanoid = nanoid[:32]
	}
	nanoidHex := bytes32FromString(nanoid)

	// `magatama.jsonld` is the signed-source-of-truth for the app's identity
	// + capabilities. Hashing it captures any change that would matter for
	// a downstream consumer (capabilities, profile, governance, version).
	manifestPath := filepath.Join(compDir, "magatama.jsonld")
	manifestBytes, err := os.ReadFile(manifestPath)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  [deploy-receipt] cannot read %s: %v\n", manifestPath, err)
		return
	}
	contentHash := sha256.Sum256(manifestBytes)
	contentHashHex := "0x" + hex.EncodeToString(contentHash[:])

	commitShaHex := bytes32FromString(currentGitCommit())

	// Phase 2-A doesn't yet anchor a CAR / IPLD CID for the build artefacts;
	// reserved for Phase 2-C when we start storing build manifests in CAS.
	emptyMagatamaCid := "0x" + hex.EncodeToString(make([]byte, 16))

	cmd := exec.Command(
		"cast", "send",
		"--rpc-url", rpcURL,
		"--private-key", sealerPriv,
		"--chain-id", chainID,
		"--gas-price", "1500000000",
		"--legacy",
		deployRegistry,
		"recordDeploy(bytes32,bytes32,bytes32,bytes16)",
		nanoidHex, contentHashHex, commitShaHex, emptyMagatamaCid,
	)
	cmd.Env = append(os.Environ(),
		// Avoid `cast` writing to ~/.foundry on shared CI runners
		"FOUNDRY_DISABLE_NIGHTLY_WARNING=1",
	)
	out, err := cmd.CombinedOutput()
	if err != nil {
		fmt.Fprintf(os.Stderr, "  [deploy-receipt] cast send failed: %v\n", err)
		fmt.Fprintf(os.Stderr, "  [deploy-receipt] output: %s\n", truncateForLog(string(out), 240))
		return
	}
	txHash := extractCastTxHash(string(out))
	fmt.Fprintf(os.Stderr, "  ✓ on-chain deploy receipt — chain=260425 nanoid=%s tx=%s\n", nanoid, txHash)
}

// keychainGet reads a `service / account` entry from the macOS Keychain.
// Returns an empty string + error on any failure.
func keychainGet(service, account string) (string, error) {
	cmd := exec.Command("security", "find-generic-password", "-s", service, "-a", account, "-w")
	cmd.Stderr = nil
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

// bytes32FromString right-pads `s` (truncated to 32 bytes) into a 0x-prefixed
// 32-byte hex string suitable for ABI bytes32.
func bytes32FromString(s string) string {
	var buf [32]byte
	copy(buf[:], s)
	return "0x" + hex.EncodeToString(buf[:])
}

func currentGitCommit() string {
	cmd := exec.Command("git", "rev-parse", "HEAD")
	cmd.Stderr = nil
	out, err := cmd.Output()
	if err != nil {
		return time.Now().UTC().Format("2006-01-02T15:04:05Z")
	}
	return strings.TrimSpace(string(out))
}

// extractCastTxHash pulls the `transactionHash` out of `cast send` JSON-ish
// stdout. Falls back to "(see logs)" when the format is unexpected.
func extractCastTxHash(out string) string {
	for _, line := range strings.Split(out, "\n") {
		line = strings.TrimSpace(line)
		if !strings.HasPrefix(line, "transactionHash") {
			continue
		}
		// "transactionHash         0x…" — accept tab or runs of spaces.
		fields := strings.Fields(line)
		if len(fields) >= 2 {
			return fields[1]
		}
	}
	return "(see logs)"
}

func truncateForLog(s string, n int) string {
	if len(s) <= n {
		return s
	}
	return s[:n] + "…"
}
