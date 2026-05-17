package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

const (
	murakumoTrainingDir = "projects/ai-gftd-project-model-moe-moe-kyun/training"
)

type murakumoStep struct {
	Command string `json:"command"`
	NSID    string `json:"nsid"`
	Purpose string `json:"purpose"`
}

var murakumoSteps = []murakumoStep{
	{Command: "plan", NSID: "ai.gftd.murakumo.planPipeline", Purpose: "Show the canonical Hayate V6 data/train/inference pipeline steps."},
	{Command: "graph-extract", NSID: "ai.gftd.murakumo.graphExtract", Purpose: "Extract entities/relations from did_domains with Qwen4B worker."},
	{Command: "graph-ingest", NSID: "ai.gftd.murakumo.graphIngest", Purpose: "Register graph entities as DID nodes and store entities/relations into LanceDB."},
	{Command: "coverage-export", NSID: "ai.gftd.murakumo.coverageExport", Purpose: "Export coverage domains from yata/PDS into coverage_domains npy."},
	{Command: "fleet-plan", NSID: "ai.gftd.murakumo.fleetPlan", Purpose: "Generate slot allocation plan for Hayate V6 fleet training."},
	{Command: "train-experts", NSID: "ai.gftd.murakumo.trainExperts", Purpose: "Run phase-2 expert training and persist bf16/int8 experts."},
	{Command: "eval", NSID: "ai.gftd.murakumo.evalV6", Purpose: "Run Hayate V6 benchmark/eval for regression checks."},
	{Command: "optimize", NSID: "ai.gftd.murakumo.optimizeCycle", Purpose: "Run one efficient optimization cycle (ingest -> score -> chunk-train -> eval)."},
	{Command: "kubelet-deploy", NSID: "", Purpose: "Deploy the murakumo-agent to the Mac mini fleet and start Virtual Kubelets."},
}

type fleetPlan struct {
	TargetSlots int `json:"target_slots"`
	ActualSlots int `json:"actual_slots"`
	Labels      int `json:"labels"`
	TotalTokens int `json:"total_tokens"`
	Allocation  []struct {
		Label   string `json:"label"`
		Tokens  int    `json:"tokens"`
		Samples int    `json:"samples"`
		Slots   int    `json:"slots"`
	} `json:"allocation"`
}

type nsidRegistry struct {
	NSIDs map[string]nsidMeta `json:"nsids"`
}

type nsidMeta struct {
	Method   string `json:"method"`
	Category string `json:"category"`
}

func runMurakumo(args []string) error {
	if len(args) == 0 {
		printMurakumoUsage()
		return nil
	}

	switch args[0] {
	case "plan":
		return runMurakumoPlan(args[1:])
	case "graph-extract":
		return runMurakumoGraphExtract(args[1:])
	case "graph-ingest":
		return runMurakumoGraphIngest(args[1:])
	case "coverage-export":
		return runMurakumoCoverageExport(args[1:])
	case "fleet-plan":
		return runMurakumoFleetPlan(args[1:])
	case "train-experts":
		return runMurakumoTrainExperts(args[1:])
	case "eval":
		return runMurakumoEval(args[1:])
	case "optimize":
		return runMurakumoOptimize(args[1:])
	case "kubelet-deploy":
		return runMurakumoKubeletDeploy(args[1:])
	case "xrpc":
		return runMurakumoXrpc(args[1:])
	case "fleet":
		return runMurakumoFleet(args[1:])
	case "models":
		return runMurakumoModels(args[1:])
	case "help", "--help", "-h":
		printMurakumoUsage()
		return nil
	default:
		return fmt.Errorf("unknown murakumo command: %s", args[0])
	}
}

func printMurakumoUsage() {
	fmt.Printf(`gftd murakumo — Hayate V6 graph/train/inference orchestration

USAGE:
  gftd murakumo <command> [flags]

COMMANDS:
  plan              Show ai.gftd.murakumo.* step mapping (JSON optional)
  graph-extract     Run Qwen4B graph entity extraction from did_domains
  graph-ingest      Ingest graph_results into yata DID graph + LanceDB tables
  coverage-export   Build coverage_domains from PDS/yata export
  fleet             Fleet operations (jotai/status/state)
  fleet-plan        Generate fleet_plan.json from expert_domains
  train-experts     Run phase-2 expert training for selected labels
  eval              Run V6 benchmark (and optional sql eval)
  optimize          Run efficient optimization cycle (ingest/score/train/eval)
  kubelet-deploy    Deploy murakumo-agent to Mac mini fleet and print start command
  xrpc              Call arbitrary /xrpc/{NSID} endpoint
  models            Declarative fleet model placement (declare/list/apply)

Run 'gftd murakumo <command> --help' for command-specific flags.
`)
}

func runMurakumoPlan(args []string) error {
	fs := flag.NewFlagSet("murakumo plan", flag.ContinueOnError)
	asJSON := fs.Bool("json", false, "emit JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if fs.NArg() != 0 {
		return fmt.Errorf("unexpected args: %s", strings.Join(fs.Args(), " "))
	}
	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{"steps": murakumoSteps})
	}

	fmt.Println("Murakumo Pipeline (ai.gftd.murakumo.*)")
	for i, s := range murakumoSteps {
		fmt.Printf("%d. gftd murakumo %s\n", i+1, s.Command)
		fmt.Printf("   NSID: %s\n", s.NSID)
		fmt.Printf("   %s\n", s.Purpose)
	}
	fmt.Printf("%d. gftd murakumo xrpc --nsid ai.gftd.murakumo.runPipeline --payload-file run.json\n", len(murakumoSteps)+1)
	return nil
}

type murakumoClusterStatus struct {
	TotalWorkers    int `json:"totalWorkers"`
	BrowserSessions int `json:"browserSessions"`
	PollWorkers     int `json:"pollWorkers"`
	IdleWorkers     int `json:"idleWorkers"`
	PendingTasks    int `json:"pendingTasks"`
	ActiveTasks     int `json:"activeTasks"`
	ActiveLeases    int `json:"activeLeases"`
}

type murakumoWorkerStatus struct {
	WorkerID      string `json:"workerId"`
	SessionID     string `json:"sessionId"`
	NodeID        string `json:"nodeId"`
	State         string `json:"state"`
	GPUTier       string `json:"gpuTier"`
	TasksDone     int    `json:"tasksDone"`
	TasksFailed   int    `json:"tasksFailed"`
	LastHeartbeat int64  `json:"lastHeartbeat"`
}

type murakumoListWorkersResponse struct {
	Workers []murakumoWorkerStatus `json:"workers"`
	Total   int                    `json:"total"`
}

func runMurakumoFleet(args []string) error {
	if len(args) == 0 {
		printMurakumoFleetUsage()
		return nil
	}
	switch args[0] {
	case "jotai", "status", "state":
		return runMurakumoFleetJotai(args[1:])
	case "nodes":
		return runMurakumoFleetNomad("node", "status", args[1:])
	case "deploy":
		return runMurakumoFleetDeploy(args[1:])
	case "versions":
		return runMurakumoFleetVersions(args[1:])
	case "drain":
		return runMurakumoFleetDrain(args[1:])
	case "undrain":
		return runMurakumoFleetUndrain(args[1:])
	case "restart":
		return runMurakumoFleetRestart(args[1:])
	case "logs":
		return runMurakumoFleetLogs(args[1:])
	case "watch":
		return runMurakumoFleetWatch(args[1:])
	case "help", "--help", "-h":
		printMurakumoFleetUsage()
		return nil
	default:
		return fmt.Errorf("unknown murakumo fleet command: %s", args[0])
	}
}

func printMurakumoFleetUsage() {
	fmt.Printf(`gftd murakumo fleet — fleet operations (Nomad-backed)

USAGE:
  gftd murakumo fleet <command> [flags]

COMMANDS:
  jotai     Show fleet status (XRPC + Nomad combined)
  status    Alias of jotai
  nodes     Show Nomad node status
  deploy    Deploy daemon.py to nodes + Nomad rolling restart
  versions  Show per-worker daemon version from CoordinatorDO
  drain     Gracefully drain a node (move tasks to other nodes)
  undrain   Re-enable a drained node
  restart   Rolling restart of inference job
  logs      Show allocation logs for a node
  watch     Continuous fleet monitoring (Ctrl-C to stop)
`)
}

func runMurakumoFleetJotai(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet jotai", flag.ContinueOnError)
	pdsURL := fs.String("pds-url", defaultPDSURL, "Murakumo base URL")
	token := fs.String("token", strings.TrimSpace(os.Getenv("PDS_TOKEN")), "Bearer token (optional)")
	apiKey := fs.String("api-key", strings.TrimSpace(os.Getenv("MURAKUMO_API_KEY")), "x-api-key header (optional)")
	limit := fs.Int("limit", 50, "max workers to list")
	timeoutSec := fs.Int("timeout", 15, "HTTP timeout seconds")
	localFallback := fs.Bool("local-fallback", true, "fallback to local fleet status script if XRPC query fails")
	localScript := fs.String("local-script", "projects/ai-gftd-project-murakumo/nomad/setup-nomad-fleet.sh", "local fallback status script path")
	asJSON := fs.Bool("json", false, "emit JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if fs.NArg() != 0 {
		return fmt.Errorf("unexpected args: %s", strings.Join(fs.Args(), " "))
	}
	if *limit <= 0 {
		return errors.New("--limit must be > 0")
	}
	if *timeoutSec <= 0 {
		return errors.New("--timeout must be > 0")
	}

	var cluster murakumoClusterStatus
	clusterBody, clusterErr := callMurakumoFleetQuery(*pdsURL, "GetClusterStatus", map[string]any{}, *token, *apiKey, time.Duration(*timeoutSec)*time.Second)
	if clusterErr == nil {
		if err := json.Unmarshal(clusterBody, &cluster); err != nil {
			clusterErr = fmt.Errorf("decode GetClusterStatus: %w", err)
		}
	}

	var workersResp murakumoListWorkersResponse
	workersBody, workersErr := callMurakumoFleetQuery(*pdsURL, "ListWorkers", map[string]any{"limit": *limit}, *token, *apiKey, time.Duration(*timeoutSec)*time.Second)
	if workersErr == nil {
		if err := json.Unmarshal(workersBody, &workersResp); err != nil {
			workersErr = fmt.Errorf("decode ListWorkers: %w", err)
		}
	}

	xrpcOK := clusterErr == nil && workersErr == nil
	localStatus := ""
	var localErr error
	if !xrpcOK && *localFallback {
		repoRoot, err := findGitRoot(".")
		if err != nil {
			localErr = err
		} else {
			localStatus, localErr = runMurakumoFleetLocalStatus(repoRoot, *localScript)
		}
	}

	sort.Slice(workersResp.Workers, func(i, j int) bool {
		if workersResp.Workers[i].NodeID == workersResp.Workers[j].NodeID {
			return workersResp.Workers[i].WorkerID < workersResp.Workers[j].WorkerID
		}
		return workersResp.Workers[i].NodeID < workersResp.Workers[j].NodeID
	})

	if *asJSON {
		out := map[string]any{
			"endpoint":     strings.TrimRight(*pdsURL, "/"),
			"fetchedAt":    time.Now().UTC().Format(time.RFC3339),
			"cluster":      cluster,
			"workers":      workersResp.Workers,
			"workersTotal": workersResp.Total,
			"workersLimit": *limit,
			"xrpcOk":       xrpcOK,
			"localFallback": map[string]any{
				"enabled": *localFallback,
				"script":  *localScript,
				"status":  localStatus,
			},
		}
		if clusterErr != nil {
			out["clusterError"] = clusterErr.Error()
		}
		if workersErr != nil {
			out["workersError"] = workersErr.Error()
		}
		if localErr != nil {
			out["localFallbackError"] = localErr.Error()
		}
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(out)
	}

	if !xrpcOK {
		if localStatus != "" {
			fmt.Fprintf(os.Stderr, "warn: xrpc fleet status unavailable\n")
			if clusterErr != nil {
				fmt.Fprintf(os.Stderr, "  GetClusterStatus: %v\n", clusterErr)
			}
			if workersErr != nil {
				fmt.Fprintf(os.Stderr, "  ListWorkers: %v\n", workersErr)
			}
			fmt.Printf("%s\n", strings.TrimRight(localStatus, "\n"))
			return nil
		}
		if localErr != nil {
			return fmt.Errorf("xrpc fleet status failed (GetClusterStatus=%v, ListWorkers=%v), local fallback failed: %v", clusterErr, workersErr, localErr)
		}
		return fmt.Errorf("xrpc fleet status failed (GetClusterStatus=%v, ListWorkers=%v)", clusterErr, workersErr)
	}

	fmt.Printf("Murakumo Fleet Jotai\n")
	fmt.Printf("endpoint: %s\n", strings.TrimRight(*pdsURL, "/"))
	fmt.Printf("fetched:  %s\n\n", time.Now().Format(time.RFC3339))
	fmt.Printf("workers: total=%d poll=%d browser=%d idle=%d\n", cluster.TotalWorkers, cluster.PollWorkers, cluster.BrowserSessions, cluster.IdleWorkers)
	fmt.Printf("tasks:   pending=%d active=%d active_leases=%d\n\n", cluster.PendingTasks, cluster.ActiveTasks, cluster.ActiveLeases)
	fmt.Printf("%-18s %-14s %-8s %-6s %-8s %-8s %s\n", "node_id", "worker_id", "state", "tier", "done", "failed", "last_heartbeat")
	for _, w := range workersResp.Workers {
		fmt.Printf(
			"%-18s %-14s %-8s %-6s %-8d %-8d %s\n",
			truncateForTable(w.NodeID, 18),
			truncateForTable(w.WorkerID, 14),
			truncateForTable(w.State, 8),
			truncateForTable(w.GPUTier, 6),
			w.TasksDone,
			w.TasksFailed,
			formatHeartbeat(w.LastHeartbeat),
		)
	}
	fmt.Printf("\nlisted %d / total %d workers\n", len(workersResp.Workers), workersResp.Total)
	return nil
}

func callMurakumoFleetQuery(baseURL, method string, payload map[string]any, token, apiKey string, timeout time.Duration) ([]byte, error) {
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}
	url := fmt.Sprintf("%s/xrpc/gftd.murakumo.v1.MurakumoQueryService/%s", strings.TrimRight(baseURL, "/"), method)
	req, err := http.NewRequest("POST", url, bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Connect-Protocol-Version", "1")
	if t := strings.TrimSpace(token); t != "" {
		req.Header.Set("Authorization", "Bearer "+t)
	}
	if k := strings.TrimSpace(apiKey); k != "" {
		req.Header.Set("x-api-key", k)
	}
	client := &http.Client{Timeout: timeout}
	resp, err := client.Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return nil, fmt.Errorf("%s failed: HTTP %d: %s", method, resp.StatusCode, strings.TrimSpace(string(respBody)))
	}
	return respBody, nil
}

func truncateForTable(v string, width int) string {
	if width <= 0 {
		return ""
	}
	if len(v) <= width {
		return v
	}
	if width <= 1 {
		return v[:width]
	}
	if width <= 3 {
		return v[:width]
	}
	return v[:width-3] + "..."
}

func formatHeartbeat(ts int64) string {
	if ts <= 0 {
		return "-"
	}
	var t time.Time
	if ts > 1_000_000_000_000 {
		t = time.UnixMilli(ts)
	} else {
		t = time.Unix(ts, 0)
	}
	age := time.Since(t).Round(time.Second)
	if age < 0 {
		age = 0
	}
	return fmt.Sprintf("%s ago", age.String())
}

func runMurakumoFleetLocalStatus(repoRoot, localScript string) (string, error) {
	scriptPath := strings.TrimSpace(localScript)
	if scriptPath == "" {
		return "", errors.New("local script path is empty")
	}
	if !filepath.IsAbs(scriptPath) {
		scriptPath = filepath.Join(repoRoot, scriptPath)
	}
	if _, err := os.Stat(scriptPath); err != nil {
		return "", err
	}
	cmd := exec.Command("bash", scriptPath, "status")
	cmd.Dir = repoRoot
	out, err := cmd.CombinedOutput()
	if err != nil {
		return "", fmt.Errorf("%w: %s", err, strings.TrimSpace(string(out)))
	}
	return string(out), nil
}

// ── Nomad fleet commands ──

const defaultNomadAddr = "http://benjamin.local:4646"

func resolveNomadAddr() string {
	if v := os.Getenv("NOMAD_ADDR"); v != "" {
		return v
	}
	return defaultNomadAddr
}

// runMurakumoFleetNomad runs a nomad CLI command (thin wrapper).
func runMurakumoFleetNomad(nomadCmd, subCmd string, args []string) error {
	nomadBin, err := exec.LookPath("nomad")
	if err != nil {
		return fmt.Errorf("nomad not found in PATH. Install: ./nomad/setup-nomad-fleet.sh install")
	}
	cmdArgs := []string{nomadCmd, subCmd}
	cmdArgs = append(cmdArgs, args...)
	cmd := exec.Command(nomadBin, cmdArgs...)
	cmd.Env = append(os.Environ(), "NOMAD_ADDR="+resolveNomadAddr())
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// runMurakumoFleetDrain gracefully drains a node so tasks migrate elsewhere.
func runMurakumoFleetDrain(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet drain", flag.ContinueOnError)
	deadline := fs.String("deadline", "1m", "drain deadline")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if fs.NArg() == 0 {
		return errors.New("usage: gftd murakumo fleet drain <node-name>")
	}
	nodeName := fs.Arg(0)
	nodeID, err := resolveNomadNodeID(nodeName)
	if err != nil {
		return err
	}
	fmt.Printf("draining node %s (id=%s, deadline=%s)...\n", nodeName, nodeID[:8], *deadline)
	return runNomadCmd("node", "drain", "-enable", "-deadline", *deadline, "-yes", nodeID)
}

// runMurakumoFleetUndrain re-enables a drained node.
func runMurakumoFleetUndrain(args []string) error {
	if len(args) == 0 {
		return errors.New("usage: gftd murakumo fleet undrain <node-name>")
	}
	nodeName := args[0]
	nodeID, err := resolveNomadNodeID(nodeName)
	if err != nil {
		return err
	}
	fmt.Printf("enabling node %s (id=%s)...\n", nodeName, nodeID[:8])
	return runNomadCmd("node", "drain", "-disable", "-yes", nodeID)
}

// runMurakumoFleetRestart triggers a rolling restart of the inference job.
func runMurakumoFleetRestart(args []string) error {
	fmt.Println("triggering rolling restart of murakumo-inference...")
	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}
	jobFile := filepath.Join(repoRoot, "projects/ai-gftd-project-murakumo/nomad/murakumo-inference.nomad.hcl")
	if _, err := os.Stat(jobFile); err != nil {
		return fmt.Errorf("job file not found: %s", jobFile)
	}
	return runNomadCmd("job", "run", jobFile)
}

// runMurakumoFleetLogs shows allocation logs for a specific node.
func runMurakumoFleetLogs(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet logs", flag.ContinueOnError)
	follow := fs.Bool("f", false, "follow (tail -f)")
	task := fs.String("task", "daemon", "task name (daemon or watchdog)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if fs.NArg() == 0 {
		return errors.New("usage: gftd murakumo fleet logs [-f] [-task daemon|watchdog] <node-name>")
	}
	nodeName := fs.Arg(0)
	allocID, err := resolveNomadAllocID(nodeName)
	if err != nil {
		return err
	}
	logArgs := []string{"alloc", "logs", "-task", *task}
	if *follow {
		logArgs = append(logArgs, "-f")
	}
	logArgs = append(logArgs, allocID)
	return runNomadCmd(logArgs...)
}

// runMurakumoFleetWatch continuously monitors fleet health.
func runMurakumoFleetWatch(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet watch", flag.ContinueOnError)
	interval := fs.Int("interval", 15, "poll interval in seconds")
	asJSON := fs.Bool("json", false, "emit JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	nomadAddr := resolveNomadAddr()
	murakumoURL := defaultPDSURL
	client := &http.Client{Timeout: 10 * time.Second}

	fmt.Printf("watching fleet (interval=%ds, nomad=%s) — Ctrl-C to stop\n\n", *interval, nomadAddr)

	for {
		now := time.Now().Format("15:04:05")

		// 1. Query Nomad nodes
		nodeReq, _ := http.NewRequest("GET", nomadAddr+"/v1/nodes", nil)
		nodeResp, nodeErr := client.Do(nodeReq)
		readyCount, totalCount := 0, 0
		var nodeNames []string
		if nodeErr == nil {
			defer nodeResp.Body.Close()
			var nodes []struct {
				Name   string `json:"Name"`
				Status string `json:"Status"`
				Drain  bool   `json:"Drain"`
			}
			if json.NewDecoder(nodeResp.Body).Decode(&nodes) == nil {
				totalCount = len(nodes)
				for _, n := range nodes {
					mark := "+"
					if n.Status != "ready" {
						mark = "!"
					} else if n.Drain {
						mark = "~"
					} else {
						readyCount++
					}
					nodeNames = append(nodeNames, mark+n.Name)
				}
			}
		}

		// 2. Query XRPC cluster status
		clusterBody, clusterErr := callMurakumoFleetQuery(murakumoURL, "GetClusterStatus", map[string]any{}, "", "", 10*time.Second)
		var cluster murakumoClusterStatus
		if clusterErr == nil {
			json.Unmarshal(clusterBody, &cluster)
		}

		if *asJSON {
			out := map[string]any{
				"time":        now,
				"nomadNodes":  totalCount,
				"nomadReady":  readyCount,
				"coordinator": cluster,
			}
			if nodeErr != nil {
				out["nomadError"] = nodeErr.Error()
			}
			if clusterErr != nil {
				out["coordinatorError"] = clusterErr.Error()
			}
			enc := json.NewEncoder(os.Stdout)
			enc.Encode(out)
		} else {
			status := "OK"
			if readyCount < totalCount {
				status = fmt.Sprintf("DEGRADED (%d/%d)", readyCount, totalCount)
			}
			if nodeErr != nil {
				status = "NOMAD_UNREACHABLE"
			}

			fmt.Printf("[%s] nomad=%s nodes=%d/%d workers=%d pending=%d active=%d  %s\n",
				now, status, readyCount, totalCount,
				cluster.PollWorkers, cluster.PendingTasks, cluster.ActiveTasks,
				strings.Join(nodeNames, " "),
			)

			if readyCount < totalCount && nodeErr == nil {
				fmt.Printf("         WARN: %d node(s) not ready\n", totalCount-readyCount)
			}
			if clusterErr != nil {
				fmt.Printf("         WARN: coordinator unreachable: %v\n", clusterErr)
			}
		}

		time.Sleep(time.Duration(*interval) * time.Second)
	}
}

// resolveNomadNodeID finds the Nomad node ID by fleet_node meta name.
func resolveNomadNodeID(nodeName string) (string, error) {
	nomadAddr := resolveNomadAddr()
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(nomadAddr + "/v1/nodes")
	if err != nil {
		return "", fmt.Errorf("cannot reach nomad: %w", err)
	}
	defer resp.Body.Close()
	var nodes []struct {
		ID   string            `json:"ID"`
		Name string            `json:"Name"`
		Meta map[string]string `json:"Meta"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&nodes); err != nil {
		return "", fmt.Errorf("decode nodes: %w", err)
	}
	for _, n := range nodes {
		if n.Name == nodeName || n.Meta["fleet_node"] == nodeName {
			return n.ID, nil
		}
	}
	return "", fmt.Errorf("node not found: %s", nodeName)
}

// resolveNomadAllocID finds the running allocation ID for a node.
func resolveNomadAllocID(nodeName string) (string, error) {
	nomadAddr := resolveNomadAddr()
	client := &http.Client{Timeout: 10 * time.Second}
	resp, err := client.Get(nomadAddr + "/v1/job/murakumo-inference/allocations")
	if err != nil {
		return "", fmt.Errorf("cannot reach nomad: %w", err)
	}
	defer resp.Body.Close()
	var allocs []struct {
		ID           string `json:"ID"`
		NodeName     string `json:"NodeName"`
		ClientStatus string `json:"ClientStatus"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&allocs); err != nil {
		return "", fmt.Errorf("decode allocs: %w", err)
	}
	for _, a := range allocs {
		if a.NodeName == nodeName && a.ClientStatus == "running" {
			return a.ID, nil
		}
	}
	return "", fmt.Errorf("no running allocation found for node: %s", nodeName)
}

// runNomadCmd executes a nomad CLI command with NOMAD_ADDR set.
func runNomadCmd(args ...string) error {
	nomadBin, err := exec.LookPath("nomad")
	if err != nil {
		return fmt.Errorf("nomad not found in PATH")
	}
	cmd := exec.Command(nomadBin, args...)
	cmd.Env = append(os.Environ(), "NOMAD_ADDR="+resolveNomadAddr())
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func runMurakumoOptimize(args []string) error {
	fs := flag.NewFlagSet("murakumo optimize", flag.ContinueOnError)
	pythonBin := fs.String("python-bin", "python3.11", "python executable")
	lancedbURI := fs.String("lancedb-uri", "/Volumes/251220/lancedb", "LanceDB URI")
	didDomains := fs.String("did-domains", "/Volumes/251220/did_domains", "did_domains root")
	ingest := fs.Bool("ingest", true, "run did_domains -> LanceDB ingest chunk")
	ingestStart := fs.Int("ingest-start", 0, "ingest label start offset")
	ingestCount := fs.Int("ingest-count", 10, "ingest label count per cycle")
	ingestMaxRows := fs.Int("ingest-max-rows", 500, "max rows per label during ingest")
	scoreData := fs.Bool("score-data", true, "compute/update quality score in schema_registry")
	scoreSampleRows := fs.Int("score-sample-rows", 64, "sample rows per label for quality scoring")
	trainNLabels := fs.Int("train-n-labels", 19, "candidate labels used by train selector")
	trainStart := fs.Int("train-start", 0, "training chunk start offset")
	trainCount := fs.Int("train-count", 4, "number of train chunks to run in this cycle")
	focusLabels := fs.String("focus-labels", "", "comma-separated exact labels to prioritize (e.g. GSM8K,Education_CC)")
	trainMinRows := fs.Int("train-min-rows", 50, "minimum rows per label for training candidates")
	samplesPer := fs.Int("samples-per", 200, "samples per label")
	epochs := fs.Int("epochs", 1, "epochs")
	slotsPer := fs.Int("slots-per", 128, "slots per label")
	batchSize := fs.Int("batch-size", 2, "batch size")
	lr := fs.Float64("lr", 1e-4, "learning rate")
	runEval := fs.Bool("eval", true, "run lightweight eval after training chunks")
	evalLimit := fs.Int("eval-limit", 20, "eval question limit")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	pdsToken := fs.String("pds-token", "", "PDS bearer token (default: auto-issue)")
	yataTrack := fs.Bool("yata-track", true, "write optimize lifecycle records to yata")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *trainCount < 0 || *ingestCount < 0 {
		return errors.New("--train-count/--ingest-count must be >= 0")
	}

	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}
	resolvedToken, err := ensurePDSToken(repoRoot, *pdsToken)
	if err != nil {
		return err
	}
	runID := fmt.Sprintf("murakumo-optimize-%d", time.Now().Unix())
	if *yataTrack {
		stmt := fmt.Sprintf(
			"MERGE (o:MurakumoOptimizeRun {run_id: \"%s\"}) SET o.phase = \"start\", o.ingest_start = %d, o.ingest_count = %d, o.train_start = %d, o.train_count = %d, o.created_at = timestamp()",
			murakumoSqlEscape(runID), *ingestStart, *ingestCount, *trainStart, *trainCount,
		)
		_ = postYataQuery(*pdsURL, resolvedToken, stmt)
	}

	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.optimizeCycle")
	env := append([]string{}, os.Environ()...)
	env = setEnv(env, "HAYATE_LANCEDB_URI", *lancedbURI)
	env = setEnv(env, "PDS_TOKEN", resolvedToken)
	env = setEnv(env, "PDS_URL", *pdsURL)

	if *ingest && *ingestCount > 0 {
		ingestScript := filepath.Join(repoRoot, murakumoTrainingDir, "ingest_did_domains_to_lancedb.py")
		if _, err := os.Stat(ingestScript); err != nil {
			return fmt.Errorf("missing script: %s", ingestScript)
		}
		if err := runCmdEnv(repoRoot, env, *pythonBin,
			ingestScript,
			"--did-domains", *didDomains,
			"--lancedb-uri", *lancedbURI,
			"--label-start", fmt.Sprintf("%d", *ingestStart),
			"--label-count", fmt.Sprintf("%d", *ingestCount),
			"--max-rows-per-label", fmt.Sprintf("%d", *ingestMaxRows),
			"--min-rows", "4",
			"--drop-existing",
		); err != nil {
			return err
		}
	}

	if *scoreData {
		scoreScript := filepath.Join(repoRoot, murakumoTrainingDir, "update_schema_quality.py")
		if _, err := os.Stat(scoreScript); err != nil {
			return fmt.Errorf("missing script: %s", scoreScript)
		}
		if err := runCmdEnv(repoRoot, env, *pythonBin,
			scoreScript,
			"--lancedb-uri", *lancedbURI,
			"--sample-rows", fmt.Sprintf("%d", *scoreSampleRows),
			"--min-rows", fmt.Sprintf("%d", *trainMinRows),
		); err != nil {
			return err
		}
	}

	targetLabels := []string{}
	for _, x := range strings.Split(strings.TrimSpace(*focusLabels), ",") {
		x = strings.TrimSpace(x)
		if x != "" {
			targetLabels = append(targetLabels, x)
		}
	}

	for i := 0; i < *trainCount; i++ {
		chunk := *trainStart + i
		trainScript := filepath.Join(repoRoot, murakumoTrainingDir, "run_expert_training.py")
		if _, err := os.Stat(trainScript); err != nil {
			return fmt.Errorf("missing script: %s", trainScript)
		}
		args := []string{
			trainScript,
			"--min-rows", fmt.Sprintf("%d", *trainMinRows),
			"--samples-per", fmt.Sprintf("%d", *samplesPer),
			"--epochs", fmt.Sprintf("%d", *epochs),
			"--slots-per", fmt.Sprintf("%d", *slotsPer),
			"--batch-size", fmt.Sprintf("%d", *batchSize),
			"--lr", fmt.Sprintf("%g", *lr),
		}
		if i < len(targetLabels) {
			fmt.Fprintf(os.Stderr, "==> optimize focused train label=%s\n", targetLabels[i])
			args = append(args, "--label", targetLabels[i])
		} else {
			fmt.Fprintf(os.Stderr, "==> optimize local train chunk=%d\n", chunk)
			args = append(args,
				"--n-labels", fmt.Sprintf("%d", *trainNLabels),
				"--label-start", fmt.Sprintf("%d", chunk),
				"--label-count", "1",
			)
		}
		if err := runCmdEnv(repoRoot, env, *pythonBin, args...); err != nil {
			return err
		}
	}

	if *runEval {
		if err := runMurakumoEval([]string{
			"--python-bin", *pythonBin,
			"--pds-url", *pdsURL,
			"--pds-token", resolvedToken,
			"--mode", "eval",
			"--limit", fmt.Sprintf("%d", *evalLimit),
			"--sql=false",
			"--dim", "256",
			"--groups", "1",
			"--mamba-per-group", "2",
			"--slots", "1024",
			"--top-m", "32",
			"--yata-track", fmt.Sprintf("%t", *yataTrack),
		}); err != nil {
			return err
		}
	}

	if *yataTrack {
		stmt := fmt.Sprintf(
			"MERGE (o:MurakumoOptimizeRun {run_id: \"%s\"}) SET o.phase = \"completed\", o.completed_at = timestamp()",
			murakumoSqlEscape(runID),
		)
		_ = postYataQuery(*pdsURL, resolvedToken, stmt)
	}
	return nil
}

func runMurakumoGraphExtract(args []string) error {
	fs := flag.NewFlagSet("murakumo graph-extract", flag.ContinueOnError)
	pythonBin := fs.String("python-bin", "python3.11", "python executable")
	workerScript := fs.String("worker-script", "/Volumes/251220/lfm_worker.py", "path to extraction worker script")
	labels := fs.String("labels", "", "comma-separated labels (required)")
	output := fs.String("output", "/Volumes/251220/graph_results/graph_entities.jsonl", "jsonl output path")
	samples := fs.Int("samples", 50, "samples per label")
	labelsPerBatch := fs.Int("labels-per-batch", 1, "number of labels per worker invocation (default: 1)")
	continueOnError := fs.Bool("continue-on-error", true, "continue with next label batch when one batch fails")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*labels) == "" {
		return errors.New("--labels is required")
	}
	if *labelsPerBatch <= 0 {
		return errors.New("--labels-per-batch must be > 0")
	}
	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}
	if _, err := ensurePDSToken(repoRoot, ""); err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(*output), 0o755); err != nil {
		return err
	}
	if err := os.WriteFile(*output, nil, 0o644); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.graphExtract")
	labelList := []string{}
	for _, x := range strings.Split(*labels, ",") {
		x = strings.TrimSpace(x)
		if x != "" {
			labelList = append(labelList, x)
		}
	}
	if len(labelList) == 0 {
		return errors.New("no valid labels after parsing --labels")
	}

	for i := 0; i < len(labelList); i += *labelsPerBatch {
		j := i + *labelsPerBatch
		if j > len(labelList) {
			j = len(labelList)
		}
		chunk := strings.Join(labelList[i:j], ",")
		partPath := fmt.Sprintf("%s.part-%d", *output, i/(*labelsPerBatch))
		_ = os.Remove(partPath)
		fmt.Fprintf(os.Stderr, "==> graph-extract batch %d-%d/%d labels=%s\n", i+1, j, len(labelList), chunk)
		if err := runCmd(".", *pythonBin,
			*workerScript,
			"--labels", chunk,
			"--output", partPath,
			"--samples", fmt.Sprintf("%d", *samples),
		); err != nil {
			if !*continueOnError {
				return err
			}
			fmt.Fprintf(os.Stderr, "WARN: batch failed (%s): %v\n", chunk, err)
			continue
		}
		b, err := os.ReadFile(partPath)
		if err != nil {
			if !*continueOnError {
				return err
			}
			fmt.Fprintf(os.Stderr, "WARN: cannot read batch output (%s): %v\n", partPath, err)
			continue
		}
		if len(b) > 0 {
			f, err := os.OpenFile(*output, os.O_APPEND|os.O_WRONLY, 0o644)
			if err != nil {
				if !*continueOnError {
					return err
				}
				fmt.Fprintf(os.Stderr, "WARN: cannot append output (%s): %v\n", *output, err)
				continue
			}
			_, _ = f.Write(b)
			_ = f.Close()
		}
	}
	return nil
}

func runMurakumoGraphIngest(args []string) error {
	fs := flag.NewFlagSet("murakumo graph-ingest", flag.ContinueOnError)
	pythonBin := fs.String("python-bin", "python3.11", "python executable")
	input := fs.String("input", "/Volumes/251220/graph_results", "input jsonl file or directory")
	lancedbURI := fs.String("lancedb-uri", "/Volumes/251220/lancedb", "LanceDB URI")
	pushYata := fs.Bool("push-yata", true, "push generated MERGE statements via ai.gftd.kagami.sql")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	pdsToken := fs.String("pds-token", "", "PDS bearer token (default: $PDS_TOKEN)")
	sqlOut := fs.String("sql-out", "/Volumes/251220/graph_results/graph_entities.sql", "generated Sql output")
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
	scriptPath := filepath.Join(repoRoot, murakumoTrainingDir, "ingest_graph_entities.py")
	if _, err := os.Stat(scriptPath); err != nil {
		return fmt.Errorf("missing script: %s", scriptPath)
	}

	resolvedToken, err := ensurePDSToken(repoRoot, *pdsToken)
	if err != nil {
		return err
	}

	cmdArgs := []string{
		scriptPath,
		"--input", *input,
		"--lancedb-uri", *lancedbURI,
		"--pds-url", *pdsURL,
		"--sql-out", *sqlOut,
	}
	if *pushYata {
		cmdArgs = append(cmdArgs, "--push-yata")
	}
	if resolvedToken != "" {
		cmdArgs = append(cmdArgs, "--pds-token", resolvedToken)
	}

	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.graphIngest")
	return runCmd(repoRoot, *pythonBin, cmdArgs...)
}

func runMurakumoCoverageExport(args []string) error {
	fs := flag.NewFlagSet("murakumo coverage-export", flag.ContinueOnError)
	pythonBin := fs.String("python-bin", "python3.11", "python executable")
	output := fs.String("output", "/Volumes/251220/coverage_domains", "coverage output directory")
	targetTokens := fs.Int("target-tokens", 1000000000, "target tokens")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	pdsToken := fs.String("pds-token", "", "PDS bearer token (default: $PDS_TOKEN)")
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
	scriptPath := filepath.Join(repoRoot, murakumoTrainingDir, "generate_yata_training.py")
	if _, err := os.Stat(scriptPath); err != nil {
		return fmt.Errorf("missing script: %s", scriptPath)
	}

	resolvedToken, err := ensurePDSToken(repoRoot, *pdsToken)
	if err != nil {
		return err
	}
	env := append([]string{}, os.Environ()...)
	env = setEnv(env, "PDS_URL", *pdsURL)
	env = setEnv(env, "PDS_TOKEN", resolvedToken)

	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.coverageExport")
	return runCmdEnv(repoRoot, env, *pythonBin,
		scriptPath,
		"coverage-export",
		"--target-tokens", fmt.Sprintf("%d", *targetTokens),
		"--output", *output,
	)
}

func runMurakumoFleetPlan(args []string) error {
	fs := flag.NewFlagSet("murakumo fleet-plan", flag.ContinueOnError)
	pythonBin := fs.String("python-bin", "python3.11", "python executable")
	dataDir := fs.String("data-dir", "/Volumes/251220/expert_domains", "expert domain npy directory")
	targetSlots := fs.Int("target-slots", 500000, "total target slots")
	dim := fs.Int("dim", 512, "model dim")
	groups := fs.Int("groups", 2, "groups")
	mambaPerGroup := fs.Int("mamba-per-group", 6, "mamba blocks per group")
	topM := fs.Int("top-m", 128, "top-M experts per token")
	batchSize := fs.Int("batch-size", 2, "batch size")
	lr := fs.Float64("lr", 1e-4, "learning rate")
	dataSource := fs.String("data-source", "lance", "data source: lance|npy")
	lancedbURI := fs.String("lancedb-uri", "/Volumes/251220/lancedb", "LanceDB URI")
	yataDir := fs.String("yata-dir", "/Volumes/251220/yata", "yata data dir")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	pdsToken := fs.String("pds-token", "", "PDS bearer token (default: auto-issue)")
	yataTrack := fs.Bool("yata-track", true, "write schedule/progress records to yata")
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
	scriptPath := filepath.Join(repoRoot, murakumoTrainingDir, "hayate_v5_split.py")
	if _, err := os.Stat(scriptPath); err != nil {
		return fmt.Errorf("missing script: %s", scriptPath)
	}
	env := append([]string{}, os.Environ()...)
	env = setEnv(env, "HAYATE_LANCEDB_URI", *lancedbURI)
	env = setEnv(env, "YATA_DATA_DIR", *yataDir)
	resolvedToken, err := ensurePDSToken(repoRoot, *pdsToken)
	if err != nil {
		return err
	}
	env = setEnv(env, "PDS_TOKEN", resolvedToken)

	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.fleetPlan")
	if err := runCmdEnv(repoRoot, env, *pythonBin,
		scriptPath,
		"fleet",
		"--data-dir", *dataDir,
		"--target-slots", fmt.Sprintf("%d", *targetSlots),
		"--dim", fmt.Sprintf("%d", *dim),
		"--groups", fmt.Sprintf("%d", *groups),
		"--mamba-per-group", fmt.Sprintf("%d", *mambaPerGroup),
		"--top-m", fmt.Sprintf("%d", *topM),
		"--batch-size", fmt.Sprintf("%d", *batchSize),
		"--lr", fmt.Sprintf("%g", *lr),
		"--data-source", *dataSource,
	); err != nil {
		return err
	}
	if *yataTrack {
		return writeFleetPlanToYata(repoRoot, *pdsURL, resolvedToken)
	}
	return nil
}

func runMurakumoTrainExperts(args []string) error {
	fs := flag.NewFlagSet("murakumo train-experts", flag.ContinueOnError)
	label := fs.String("label", "", "single label to train (optional)")
	nLabels := fs.Int("n-labels", 2, "number of labels")
	labelStart := fs.Int("label-start", 0, "start offset in selected labels")
	labelCount := fs.Int("label-count", 0, "number of labels in this chunk (0: use --n-labels)")
	minRows := fs.Int("min-rows", 1, "minimum rows per label candidate")
	samplesPer := fs.Int("samples-per", 1000, "max samples per label")
	epochs := fs.Int("epochs", 1, "epochs")
	slotsPer := fs.Int("slots-per", 128, "slots per label")
	batchSize := fs.Int("batch-size", 2, "batch size")
	lr := fs.Float64("lr", 1e-4, "learning rate")
	device := fs.String("device", "wgpu", "training device (wgpu|cpu)")
	trainingPrecision := fs.String("training-precision", "bf16", "training precision (bf16)")
	seqLen := fs.Int("seq-len", 128, "sequence length")
	dim := fs.Int("dim", 512, "model dim")
	groups := fs.Int("groups", 1, "number of groups")
	mambaPerGroup := fs.Int("mamba-per-group", 1, "mamba blocks per group")
	backboneTable := fs.String("backbone-table", "weights_backbone_v6", "backbone table name")
	lancedbURI := fs.String("lancedb-uri", "/Volumes/251220/lancedb", "LanceDB URI")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	pdsToken := fs.String("pds-token", "", "PDS bearer token (default: auto-issue)")
	priority := fs.Int("priority", 8, "murakumo task priority")
	yataTrack := fs.Bool("yata-track", true, "write training progress records to yata")
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
	resolvedToken, err := ensurePDSToken(repoRoot, *pdsToken)
	if err != nil {
		return err
	}
	runID := fmt.Sprintf("murakumo-train-%d", time.Now().Unix())
	if *yataTrack {
		stmt := fmt.Sprintf("MERGE (r:MurakumoTrainRun {run_id: \"%s\"}) SET r.phase = \"submitted\", r.label = \"%s\", r.n_labels = %d, r.label_start = %d, r.label_count = %d, r.samples_per = %d, r.epochs = %d, r.slots_per = %d, r.device = \"%s\", r.training_precision = \"%s\"",
			murakumoSqlEscape(runID), murakumoSqlEscape(*label), *nLabels, *labelStart, *labelCount, *samplesPer, *epochs, *slotsPer, murakumoSqlEscape(*device), murakumoSqlEscape(*trainingPrecision))
		_ = postYataQuery(*pdsURL, resolvedToken, stmt)
	}

	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.trainExperts")
	payload := map[string]any{
		"label":             strings.TrimSpace(*label),
		"nLabels":           *nLabels,
		"labelStart":        *labelStart,
		"labelCount":        *labelCount,
		"minRows":           *minRows,
		"samplesPer":        *samplesPer,
		"epochs":            *epochs,
		"slotsPer":          *slotsPer,
		"batchSize":         *batchSize,
		"learningRate":      *lr,
		"backend":           strings.TrimSpace(*device),
		"trainingPrecision": strings.TrimSpace(*trainingPrecision),
		"seqLen":            *seqLen,
		"dim":               *dim,
		"groups":            *groups,
		"mambaPerGroup":     *mambaPerGroup,
		"backboneTable":     strings.TrimSpace(*backboneTable),
		"lancedbUri":        strings.TrimSpace(*lancedbURI),
		"priority":          *priority,
	}
	bodyBytes, err := json.Marshal(payload)
	if err != nil {
		return err
	}

	meta, ok, err := lookupNSIDMeta(repoRoot, "ai.gftd.murakumo.trainExperts")
	if err != nil {
		return err
	}
	if !ok {
		return errors.New("nsid not found in registry: ai.gftd.murakumo.trainExperts")
	}
	service := "MurakumoCommandService"
	if strings.EqualFold(meta.Category, "query") {
		service = "MurakumoQueryService"
	}
	url := fmt.Sprintf("%s/xrpc/gftd.murakumo.v1.%s/%s", strings.TrimRight(*pdsURL, "/"), service, meta.Method)
	respBody, err := postXrpcJSON(url, string(bodyBytes), resolvedToken, true)
	if err != nil {
		return err
	}
	fmt.Println(respBody)
	if *yataTrack {
		stmt := fmt.Sprintf("MERGE (r:MurakumoTrainRun {run_id: \"%s\"}) SET r.phase = \"accepted\", r.accepted_at = timestamp()",
			murakumoSqlEscape(runID))
		_ = postYataQuery(*pdsURL, resolvedToken, stmt)
	}
	return nil
}

func runMurakumoEval(args []string) error {
	fs := flag.NewFlagSet("murakumo eval", flag.ContinueOnError)
	pythonBin := fs.String("python-bin", "python3.11", "python executable")
	mode := fs.String("mode", "eval", "eval_v6_bench mode: quick|full|eval")
	checkpoint := fs.String("checkpoint", "", "checkpoint for --mode eval (default: auto-detect)")
	limit := fs.Int("limit", 20, "evaluation question limit (bench)")
	dim := fs.Int("dim", 256, "model dimension for eval_v6_bench")
	groups := fs.Int("groups", 1, "number of groups for eval_v6_bench")
	mambaPerGroup := fs.Int("mamba-per-group", 2, "mamba blocks per group for eval_v6_bench")
	slots := fs.Int("slots", 1024, "moe slots for eval_v6_bench")
	topM := fs.Int("top-m", 32, "top-m experts for eval_v6_bench")
	runSql := fs.Bool("sql", false, "run eval_v6_sql.py after benchmark")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	pdsToken := fs.String("pds-token", "", "PDS bearer token (default: auto-issue)")
	yataTrack := fs.Bool("yata-track", true, "write eval progress records to yata")
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
	benchScript := filepath.Join(repoRoot, murakumoTrainingDir, "eval_v6_bench.py")
	sqlScript := filepath.Join(repoRoot, murakumoTrainingDir, "eval_v6_sql.py")
	if _, err := os.Stat(benchScript); err != nil {
		return fmt.Errorf("missing script: %s", benchScript)
	}
	resolvedToken, err := ensurePDSToken(repoRoot, *pdsToken)
	if err != nil {
		return err
	}
	runID := fmt.Sprintf("murakumo-eval-%d", time.Now().Unix())
	if *yataTrack {
		stmt := fmt.Sprintf("MERGE (e:MurakumoEvalRun {run_id: \"%s\"}) SET e.phase = \"start\", e.mode = \"%s\", e.limit = %d",
			murakumoSqlEscape(runID), murakumoSqlEscape(*mode), *limit)
		_ = postYataQuery(*pdsURL, resolvedToken, stmt)
	}

	fmt.Fprintf(os.Stderr, "==> NSID %s\n", "ai.gftd.murakumo.evalV6")
	benchArgs := []string{
		benchScript,
		"--mode", *mode,
		"--limit", fmt.Sprintf("%d", *limit),
		"--dim", fmt.Sprintf("%d", *dim),
		"--groups", fmt.Sprintf("%d", *groups),
		"--mamba-per-group", fmt.Sprintf("%d", *mambaPerGroup),
		"--slots", fmt.Sprintf("%d", *slots),
		"--top-m", fmt.Sprintf("%d", *topM),
	}
	if strings.TrimSpace(*mode) == "eval" {
		ckptPath := strings.TrimSpace(*checkpoint)
		if ckptPath == "" {
			candidate := filepath.Join(repoRoot, murakumoTrainingDir, "data", "hayate_v6_bench.npz")
			if _, err := os.Stat(candidate); err == nil {
				ckptPath = candidate
			}
		}
		if ckptPath == "" {
			return errors.New("eval mode requires --checkpoint (auto-detect failed)")
		}
		benchArgs = append(benchArgs, "--checkpoint", ckptPath)
	} else if strings.TrimSpace(*checkpoint) != "" {
		benchArgs = append(benchArgs, "--checkpoint", strings.TrimSpace(*checkpoint))
	}
	if err := runCmd(repoRoot, *pythonBin, benchArgs...); err != nil {
		return err
	}
	if *runSql {
		if _, err := os.Stat(sqlScript); err != nil {
			return fmt.Errorf("missing script: %s", sqlScript)
		}
		if err := runCmd(repoRoot, *pythonBin, sqlScript); err != nil {
			return err
		}
	}
	if *yataTrack {
		stmt := fmt.Sprintf("MERGE (e:MurakumoEvalRun {run_id: \"%s\"}) SET e.phase = \"completed\", e.completed_at = timestamp()",
			murakumoSqlEscape(runID))
		_ = postYataQuery(*pdsURL, resolvedToken, stmt)
	}
	return nil
}

func runMurakumoXrpc(args []string) error {
	fs := flag.NewFlagSet("murakumo xrpc", flag.ContinueOnError)
	nsid := fs.String("nsid", "", "NSID (e.g. ai.gftd.murakumo.graphExtract)")
	payload := fs.String("payload", "", "inline JSON payload")
	payloadFile := fs.String("payload-file", "", "path to JSON payload file")
	pdsURL := fs.String("pds-url", defaultPDSURL, "PDS base URL")
	token := fs.String("token", "", "Bearer token (default: $PDS_TOKEN)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if strings.TrimSpace(*nsid) == "" {
		return errors.New("--nsid is required")
	}

	body := strings.TrimSpace(*payload)
	if body == "" && strings.TrimSpace(*payloadFile) != "" {
		b, err := os.ReadFile(strings.TrimSpace(*payloadFile))
		if err != nil {
			return err
		}
		body = string(b)
	}
	if body == "" {
		body = "{}"
	}
	if !json.Valid([]byte(body)) {
		return errors.New("payload is not valid JSON")
	}
	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}
	resolvedToken, err := ensurePDSToken(repoRoot, *token)
	if err != nil {
		return err
	}

	nsidName := strings.TrimSpace(*nsid)
	if strings.HasPrefix(nsidName, "ai.gftd.murakumo.") {
		meta, ok, err := lookupNSIDMeta(repoRoot, nsidName)
		if err != nil {
			return err
		}
		if !ok {
			return fmt.Errorf("nsid not found in registry: %s", nsidName)
		}
		service := "MurakumoCommandService"
		if strings.EqualFold(meta.Category, "query") {
			service = "MurakumoQueryService"
		}
		url := fmt.Sprintf(
			"%s/xrpc/gftd.murakumo.v1.%s/%s",
			strings.TrimRight(*pdsURL, "/"),
			service,
			meta.Method,
		)
		respBody, svcErr := postXrpcJSON(url, body, resolvedToken, true)
		if svcErr == nil {
			fmt.Println(respBody)
			return nil
		}
		// Compatibility fallback: some environments expose the legacy /xrpc/{NSID} route only.
		legacyURL := strings.TrimRight(*pdsURL, "/") + "/xrpc/" + nsidName
		legacyBody, legacyErr := postXrpcJSON(legacyURL, body, resolvedToken, false)
		if legacyErr == nil {
			fmt.Println(legacyBody)
			return nil
		}
		return fmt.Errorf("murakumo xrpc failed: service route error: %v; legacy route error: %v", svcErr, legacyErr)
	}

	url := strings.TrimRight(*pdsURL, "/") + "/xrpc/" + nsidName
	respBody, err := postXrpcJSON(url, body, resolvedToken, false)
	if err != nil {
		return err
	}
	fmt.Println(respBody)
	return nil
}

func postXrpcJSON(url, body, token string, connectProtocol bool) (string, error) {
	req, err := http.NewRequest("POST", url, bytes.NewBufferString(body))
	if err != nil {
		return "", err
	}
	req.Header.Set("Content-Type", "application/json")
	if connectProtocol {
		req.Header.Set("Connect-Protocol-Version", "1")
	}
	if token != "" {
		req.Header.Set("Authorization", "Bearer "+token)
	}
	resp, err := (&http.Client{}).Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("xrpc call failed: HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(respBody)))
	}
	return string(respBody), nil
}

func lookupNSIDMeta(repoRoot, nsid string) (nsidMeta, bool, error) {
	regPath := filepath.Join(repoRoot, "packages/contract/at-protocol-nsids.json")
	b, err := os.ReadFile(regPath)
	if err != nil {
		return nsidMeta{}, false, err
	}
	var reg nsidRegistry
	if err := json.Unmarshal(b, &reg); err != nil {
		return nsidMeta{}, false, err
	}
	m, ok := reg.NSIDs[nsid]
	return m, ok, nil
}

func ensurePDSToken(repoRoot string, explicit string) (string, error) {
	if t := strings.TrimSpace(explicit); t != "" {
		return t, nil
	}
	if t := strings.TrimSpace(os.Getenv("PDS_TOKEN")); t != "" {
		return t, nil
	}

	issueScript := filepath.Join(repoRoot, murakumoTrainingDir, "issue_pds_tokens.sh")
	if _, err := os.Stat(issueScript); err != nil {
		return "", fmt.Errorf("PDS_TOKEN missing and token issue script not found: %s", issueScript)
	}

	tmpEnv := filepath.Join(os.TempDir(), "pds_tokens.env")
	cmd := exec.Command("bash", issueScript)
	cmd.Dir = repoRoot
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	cmd.Env = append(os.Environ(), "OUT_FILE="+tmpEnv)
	if err := cmd.Run(); err != nil {
		return "", fmt.Errorf("failed to issue PDS token: %w", err)
	}

	token, err := readTokenFromEnvFile(tmpEnv, "PDS_TOKEN")
	if err != nil {
		return "", err
	}
	if token == "" {
		return "", errors.New("token issuance succeeded but PDS_TOKEN was empty")
	}
	_ = os.Setenv("PDS_TOKEN", token)
	return token, nil
}

func readTokenFromEnvFile(path, key string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	prefix := "export " + key + "="
	sc := bufio.NewScanner(f)
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if !strings.HasPrefix(line, prefix) {
			continue
		}
		v := strings.TrimPrefix(line, prefix)
		v = strings.Trim(v, "\"'")
		return strings.TrimSpace(v), nil
	}
	if err := sc.Err(); err != nil {
		return "", err
	}
	return "", fmt.Errorf("%s not found in %s", key, path)
}

func postYataQuery(pdsURL, token, statement string) error {
	if strings.TrimSpace(token) == "" {
		return errors.New("missing token")
	}
	body, _ := json.Marshal(map[string]any{"statement": statement})
	req, err := http.NewRequest("POST", strings.TrimRight(pdsURL, "/")+"/xrpc/ai.gftd.kagami.sql", bytes.NewReader(body))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := (&http.Client{}).Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		b, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("queryExec http %d: %s", resp.StatusCode, strings.TrimSpace(string(b)))
	}
	return nil
}

func writeFleetPlanToYata(repoRoot, pdsURL, token string) error {
	planPath := filepath.Join(repoRoot, "fleet_plan.json")
	b, err := os.ReadFile(planPath)
	if err != nil {
		return err
	}
	var plan fleetPlan
	if err := json.Unmarshal(b, &plan); err != nil {
		return err
	}
	runID := fmt.Sprintf("murakumo-fleet-%d", time.Now().Unix())
	summary := fmt.Sprintf("MERGE (r:MurakumoFleetRun {run_id: \"%s\"}) SET r.target_slots = %d, r.actual_slots = %d, r.labels = %d, r.total_tokens = %d, r.created_at = timestamp()",
		murakumoSqlEscape(runID), plan.TargetSlots, plan.ActualSlots, plan.Labels, plan.TotalTokens)
	if err := postYataQuery(pdsURL, token, summary); err != nil {
		return err
	}
	for _, a := range plan.Allocation {
		stmt := fmt.Sprintf("MERGE (t:MurakumoFleetTask {run_id: \"%s\", label: \"%s\"}) SET t.slots = %d, t.tokens = %d, t.samples = %d",
			murakumoSqlEscape(runID), murakumoSqlEscape(a.Label), a.Slots, a.Tokens, a.Samples)
		if err := postYataQuery(pdsURL, token, stmt); err != nil {
			return err
		}
	}
	return nil
}

func murakumoSqlEscape(v string) string {
	return strings.ReplaceAll(strings.ReplaceAll(v, "\\", "\\\\"), "\"", "\\\"")
}
