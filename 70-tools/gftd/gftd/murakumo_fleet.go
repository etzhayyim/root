package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"time"
)

// fleetNode defines a Mac Mini fleet member.
type fleetNode struct {
	Name string
	User string
	IP   string
}

var fleetNodes = []fleetNode{
	{"zebulun", "zebulun", "192.168.1.11"},
	{"issachar", "issachar", "192.168.1.12"},
	{"dan", "dan", "192.168.1.13"},
	{"benjamin", "benjamin", "192.168.1.14"},
	{"joseph", "joseph", "192.168.1.15"},
	{"levi", "levi", "192.168.1.16"},
	{"judah", "judah", "192.168.1.17"},
	{"simeon", "simeon", "192.168.1.18"},
	{"naphtali", "naphtali", "192.168.1.19"},
	{"asher", "asher", "192.168.1.20"},
}

const (
	fleetSSHPass       = "260308"
	daemonDeployPath   = "/usr/local/share/murakumo/daemon.py"
	daemonVenvPython   = "$HOME/.local/share/murakumo-venv/bin/python3"
	kubeletAgentSrc    = "50-infra/k8s/murakumo-kubelet/agent/murakumo-agent.py"
	kubeletAgentDst    = "~/.gftd/murakumo-kubelet/agent/murakumo-agent.py"
)

// runMurakumoKubeletDeploy deploys the murakumo-agent via SSH and starts the virtual kubelets.
func runMurakumoKubeletDeploy(args []string) error {
	fs := flag.NewFlagSet("murakumo kubelet-deploy", flag.ContinueOnError)
	nodes := fs.String("nodes", "", "comma-separated node names (default: all)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}

	agentSrc := filepath.Join(repoRoot, kubeletAgentSrc)
	if _, err := os.Stat(agentSrc); err != nil {
		return fmt.Errorf("murakumo-agent.py not found: %s", agentSrc)
	}

	targets := fleetNodes
	if *nodes != "" {
		targets = filterFleetNodes(strings.Split(*nodes, ","))
	}

	if len(targets) == 0 {
		return errors.New("no target nodes")
	}

	fmt.Printf("Deploying murakumo-agent to %d nodes...\n", len(targets))

	if _, err := exec.LookPath("sshpass"); err != nil {
		return fmt.Errorf("sshpass not found. Install: brew install hudochenkov/sshpass/sshpass")
	}

	var wg sync.WaitGroup
	for _, n := range targets {
		wg.Add(1)
		go func(node fleetNode) {
			defer wg.Done()
			
			// 1. Mkdir
			exec.Command("sshpass", "-p", fleetSSHPass, "ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=3", fmt.Sprintf("%s@%s", node.User, node.IP), "mkdir -p ~/.gftd/murakumo-kubelet/agent && mkdir -p ~/Library/LaunchAgents").Run()
			
			// 2. SCP
			exec.Command("sshpass", "-p", fleetSSHPass, "scp", "-o", "StrictHostKeyChecking=no", agentSrc, fmt.Sprintf("%s@%s:%s", node.User, node.IP, kubeletAgentDst)).Run()
			
			// 3. Plist & Load
			plistCmd := fmt.Sprintf(`cat << 'INNER_EOF' > ~/Library/LaunchAgents/ai.gftd.murakumo-agent.plist
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>ai.gftd.murakumo-agent</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/env</string>
        <string>python3</string>
        <string>/Users/%s/.gftd/murakumo-kubelet/agent/murakumo-agent.py</string>
        <string>8888</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/murakumo-agent.out.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/murakumo-agent.err.log</string>
</dict>
</plist>
INNER_EOF
launchctl unload ~/Library/LaunchAgents/ai.gftd.murakumo-agent.plist 2>/dev/null || true
launchctl load ~/Library/LaunchAgents/ai.gftd.murakumo-agent.plist
`, node.User)
			
			exec.Command("sshpass", "-p", fleetSSHPass, "ssh", "-o", "StrictHostKeyChecking=no", fmt.Sprintf("%s@%s", node.User, node.IP), plistCmd).Run()
			
			fmt.Printf("✔ Deployed agent to %s (%s)\n", node.Name, node.IP)
		}(n)
	}
	wg.Wait()

	fmt.Println("\nAgent deployment complete. To start the local Virtual Kubelets, run:")
	fmt.Println("cd 50-infra/k8s/murakumo-kubelet && python3 start_kubelets.py")
	return nil
}

// runMurakumoFleetDeploy deploys daemon.py to fleet nodes via SSH + triggers Nomad rolling restart.
func runMurakumoFleetDeploy(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet deploy", flag.ContinueOnError)
	nodes := fs.String("nodes", "", "comma-separated node names (default: all)")
	skipRestart := fs.Bool("skip-restart", false, "skip Nomad rolling restart after deploy")
	dryRun := fs.Bool("dry-run", false, "show what would be done without executing")
	concurrency := fs.Int("concurrency", 4, "parallel SSH operations")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}

	daemonSrc := filepath.Join(repoRoot, "projects/ai-gftd-project-murakumo/cli/daemon.py")
	if _, err := os.Stat(daemonSrc); err != nil {
		return fmt.Errorf("daemon.py not found: %s", daemonSrc)
	}

	// Resolve target nodes
	targets := fleetNodes
	if *nodes != "" {
		targets = filterFleetNodes(strings.Split(*nodes, ","))
	}

	if len(targets) == 0 {
		return errors.New("no target nodes")
	}

	// Read daemon.py version for display
	daemonVersion := readDaemonVersion(daemonSrc)
	fmt.Printf("Deploying daemon.py v%s to %d nodes\n", daemonVersion, len(targets))

	if *dryRun {
		for _, n := range targets {
			fmt.Printf("  [dry-run] %s (%s@%s) — scp %s → %s\n", n.Name, n.User, n.IP, daemonSrc, daemonDeployPath)
		}
		fmt.Println("\n  [dry-run] nomad job run murakumo-inference.nomad.hcl")
		return nil
	}

	// Check sshpass availability
	if _, err := exec.LookPath("sshpass"); err != nil {
		return fmt.Errorf("sshpass not found. Install: brew install hudochenkov/sshpass/sshpass")
	}

	// Deploy in parallel
	type result struct {
		Node  string
		OK    bool
		Error string
	}
	results := make([]result, len(targets))
	var wg sync.WaitGroup
	sem := make(chan struct{}, *concurrency)

	for i, node := range targets {
		wg.Add(1)
		sem <- struct{}{}
		go func(idx int, n fleetNode) {
			defer wg.Done()
			defer func() { <-sem }()
			err := deployDaemonToNode(n, daemonSrc)
			if err != nil {
				results[idx] = result{Node: n.Name, OK: false, Error: err.Error()}
			} else {
				results[idx] = result{Node: n.Name, OK: true}
			}
		}(i, node)
	}
	wg.Wait()

	// Report
	okCount := 0
	for _, r := range results {
		status := "OK"
		if !r.OK {
			status = "FAIL: " + r.Error
		} else {
			okCount++
		}
		fmt.Printf("  [%s] %s\n", r.Node, status)
	}
	fmt.Printf("\nDeployed: %d/%d nodes\n", okCount, len(targets))

	// Nomad rolling restart
	if !*skipRestart && okCount > 0 {
		fmt.Println("\nTriggering Nomad rolling restart...")
		jobFile := filepath.Join(repoRoot, "projects/ai-gftd-project-murakumo/nomad/murakumo-inference.nomad.hcl")
		if err := runNomadCmd("job", "run", jobFile); err != nil {
			fmt.Fprintf(os.Stderr, "warning: nomad job run failed: %v\n", err)
			fmt.Fprintf(os.Stderr, "  nodes updated but Nomad restart skipped. Run manually:\n")
			fmt.Fprintf(os.Stderr, "  NOMAD_ADDR=%s nomad job run %s\n", resolveNomadAddr(), jobFile)
		} else {
			fmt.Println("Rolling restart initiated (max_parallel=1, auto_revert=true)")
		}
	}

	return nil
}

// deployDaemonToNode copies daemon.py to a fleet node and ensures venv + deps.
func deployDaemonToNode(n fleetNode, daemonSrc string) error {
	host := fmt.Sprintf("%s@%s", n.User, n.IP)
	sshOpts := []string{"-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=no", "-o", "PreferredAuthentications=password"}

	// scp daemon.py → /tmp/daemon.py
	scpArgs := append([]string{"-p", fleetSSHPass, "scp"}, sshOpts...)
	scpArgs = append(scpArgs, daemonSrc, host+":/tmp/daemon.py")
	if err := runQuietCmd("sshpass", scpArgs...); err != nil {
		return fmt.Errorf("scp: %w", err)
	}

	// SSH: mkdir + cp + ensure venv + install deps
	remoteScript := fmt.Sprintf(`
echo %s | sudo -S mkdir -p /usr/local/share/murakumo 2>/dev/null
echo %s | sudo -S cp /tmp/daemon.py %s 2>/dev/null
VENV=$HOME/.local/share/murakumo-venv
if [ ! -f "$VENV/bin/python3" ]; then
  PY=""
  for p in python3.12 python3.13 python3.14 python3; do
    if command -v "$p" &>/dev/null; then PY="$p"; break; fi
  done
  [ -z "$PY" ] && exit 1
  "$PY" -m venv "$VENV" 2>/dev/null
fi
$VENV/bin/python3 -c "import mlx_lm, httpx" 2>/dev/null || $VENV/bin/pip install mlx mlx_lm httpx -q 2>/dev/null
# Kill old daemon process so Nomad restarts with new code
pkill -f "daemon.py" 2>/dev/null || true
`, fleetSSHPass, fleetSSHPass, daemonDeployPath)

	sshArgs := append([]string{"-p", fleetSSHPass, "ssh"}, sshOpts...)
	sshArgs = append(sshArgs, host, "bash", "-c", "'"+remoteScript+"'")
	return runQuietCmd("sshpass", sshArgs...)
}

// runMurakumoFleetVersions queries CoordinatorDO for per-worker daemon versions.
func runMurakumoFleetVersions(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet versions", flag.ContinueOnError)
	murakumoURL := fs.String("url", envOr("GFTD_MURAKUMO", murakumoEndpoint), "Murakumo API base URL")
	apiKey := fs.String("api-key", envOr("MURAKUMO_API_KEY", murakumoAPIKey), "API key")
	asJSON := fs.Bool("json", false, "emit JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Query workers from CoordinatorDO
	body, err := callMurakumoFleetQuery(*murakumoURL, "ListWorkers", map[string]any{"limit": 50}, "", *apiKey, 15*time.Second)
	if err != nil {
		return fmt.Errorf("ListWorkers: %w", err)
	}

	var resp struct {
		Workers []struct {
			WorkerID      string `json:"workerId"`
			NodeID        string `json:"nodeId"`
			State         string `json:"state"`
			GPUTier       string `json:"gpuTier"`
			DaemonVersion string `json:"daemonVersion"`
			LastHeartbeat int64  `json:"lastHeartbeat"`
			TasksDone     int    `json:"tasksDone"`
		} `json:"workers"`
	}
	if err := json.Unmarshal(body, &resp); err != nil {
		return fmt.Errorf("decode: %w", err)
	}

	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(resp.Workers)
	}

	fmt.Printf("%-12s %-16s %-8s %-8s %-16s %-12s %s\n",
		"NODE", "WORKER", "STATE", "GPU", "DAEMON_VERSION", "TASKS_DONE", "LAST_HB")
	fmt.Println(strings.Repeat("-", 90))

	versionCount := map[string]int{}
	for _, w := range resp.Workers {
		ver := w.DaemonVersion
		if ver == "" {
			ver = "(unknown)"
		}
		versionCount[ver]++
		hb := "never"
		if w.LastHeartbeat > 0 {
			ago := time.Since(time.Unix(w.LastHeartbeat, 0)).Truncate(time.Second)
			hb = ago.String() + " ago"
		}
		fmt.Printf("%-12s %-16s %-8s %-8s %-16s %-12d %s\n",
			w.NodeID, truncateWorkerID(w.WorkerID, 14), w.State, w.GPUTier, ver, w.TasksDone, hb)
	}

	fmt.Printf("\nVersion distribution:\n")
	for ver, count := range versionCount {
		fmt.Printf("  %s: %d workers\n", ver, count)
	}

	return nil
}

// --- helpers ---

func filterFleetNodes(names []string) []fleetNode {
	nameSet := map[string]bool{}
	for _, n := range names {
		nameSet[strings.TrimSpace(n)] = true
	}
	var out []fleetNode
	for _, n := range fleetNodes {
		if nameSet[n.Name] {
			out = append(out, n)
		}
	}
	return out
}

func readDaemonVersion(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return "unknown"
	}
	for _, line := range strings.Split(string(data), "\n") {
		if strings.HasPrefix(strings.TrimSpace(line), "VERSION") && strings.Contains(line, "=") {
			parts := strings.SplitN(line, "=", 2)
			return strings.Trim(strings.TrimSpace(parts[1]), "\"' ")
		}
	}
	return "unknown"
}

func truncateWorkerID(s string, maxLen int) string {
	if len(s) <= maxLen {
		return s
	}
	return s[:maxLen-2] + ".."
}

func runQuietCmd(name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Stdout = nil
	cmd.Stderr = nil
	return cmd.Run()
}
