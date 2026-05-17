package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strconv"
	"strings"
	"time"
)

const (
	defaultOrganismAgentDID       = "did:web:kami-agent.etzhayyim.com"
	defaultOrganismStatusWebURL   = "http://127.0.0.1:8765"
	defaultOrganismStatusWebHost  = "127.0.0.1"
	defaultOrganismStatusWebPort  = "8765"
	organismStatusCLIName         = "magatama-agent-status"
	organismStatusWebCLIName      = "magatama-agent-status-web"
	organismPublishCLIName        = "magatama-agent-erc8004"
	organismPythonStatusModule    = "pymagatama.agent_status_main"
	organismPythonStatusWebModule = "pymagatama.agent_status_web_main"
	organismPythonPublishModule   = "pymagatama.agent_erc8004_main"
)

func runAgent(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("agent subcommand required: organism status, verify")
	}
	if isHelpArg(args[0]) {
		fmt.Fprintln(os.Stderr, "Usage: gftd agent <organism status|verify> [flags]")
		return nil
	}
	if args[0] == "verify" {
		return runAgentVerify(args[1:])
	}
	if args[0] != "organism" {
		return fmt.Errorf("unknown agent subcommand %q. Available: organism status, verify", args[0])
	}
	if len(args) < 2 {
		return fmt.Errorf("agent organism subcommand required: status, publish")
	}
	if isHelpArg(args[1]) {
		fmt.Fprintln(os.Stderr, "Usage: gftd agent organism <status|publish> [flags]")
		return nil
	}
	switch args[1] {
	case "status":
		return runAgentOrganismStatus(args[2:])
	case "publish":
		return runAgentOrganismPublish(args[2:])
	default:
		return fmt.Errorf("unknown agent organism subcommand %q. Available: status, publish", args[1])
	}
}

func runAgentOrganismStatus(args []string) error {
	fs := flag.NewFlagSet("agent organism status", flag.ContinueOnError)
	agentDID := fs.String("agent-did", agentEnvDefault("AGENT_DID", defaultOrganismAgentDID), "agent DID to inspect")
	asJSON := fs.Bool("json", false, "emit JSON status from magatama-agent-status")
	web := fs.Bool("web", false, "check the status WebUI; start it in the foreground if it is not running")
	statusURL := fs.String("url", agentEnvDefault("AGENT_STATUS_PUBLIC_URL", defaultOrganismStatusWebURL), "status WebUI base URL")
	openBrowser := fs.Bool("open", false, "open the status WebUI in the default browser when --web is used")
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
	if *web {
		return runAgentOrganismStatusWeb(*agentDID, *statusURL, *openBrowser)
	}
	return runAgentStatusCLI(*agentDID, *asJSON)
}

func runAgentStatusCLI(agentDID string, asJSON bool) error {
	root := agentRepoRoot()
	cmd, err := agentCommand(root, organismStatusCLIName, organismPythonStatusModule, agentStatusArgs(agentDID, asJSON)...)
	if err != nil {
		return err
	}
	return runAgentPassthrough(cmd)
}

func runAgentOrganismStatusWeb(agentDID string, statusURL string, openBrowser bool) error {
	baseURL := strings.TrimRight(statusURL, "/")
	if baseURL == "" {
		baseURL = defaultOrganismStatusWebURL
	}
	if summary, ok := fetchAgentStatusWebSummary(baseURL, agentDID); ok {
		fmt.Printf("Agent organism status WebUI: %s\n", baseURL)
		if summary.HealthLevel != "" {
			fmt.Printf("health: %s score=%.2f\n", summary.HealthLevel, summary.HealthScore)
		}
		if openBrowser {
			if err := openAgentStatusURL(baseURL); err != nil {
				return err
			}
		}
		return nil
	}

	host, port := agentWebHostPort(baseURL)
	root := agentRepoRoot()
	cmd, err := agentCommand(root, organismStatusWebCLIName, organismPythonStatusWebModule, "--agent-did", agentDID, "--host", host, "--port", port)
	if err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "Starting agent organism status WebUI at http://%s:%s\n", host, port)
	if openBrowser {
		_ = openAgentStatusURL(baseURL)
	}
	return runAgentPassthrough(cmd)
}

func agentStatusArgs(agentDID string, asJSON bool) []string {
	args := []string{"--agent-did", agentDID}
	if asJSON {
		args = append(args, "--json")
	}
	return args
}

func agentCommand(root string, binaryName string, pythonModule string, args ...string) (*exec.Cmd, error) {
	if bin := filepath.Join(root, "20-actors", "magatama", "py", ".venv", "bin", binaryName); isExecutableFile(bin) {
		cmd := exec.Command(bin, args...)
		cmd.Env = agentCommandEnv(root)
		return cmd, nil
	}
	if bin, err := exec.LookPath(binaryName); err == nil {
		cmd := exec.Command(bin, args...)
		cmd.Env = agentCommandEnv(root)
		return cmd, nil
	}
	if python := filepath.Join(root, "20-actors", "magatama", "py", ".venv", "bin", "python"); isExecutableFile(python) {
		moduleArgs := append([]string{"-m", pythonModule}, args...)
		cmd := exec.Command(python, moduleArgs...)
		cmd.Env = agentCommandEnv(root)
		return cmd, nil
	}
	if python, err := exec.LookPath("python3"); err == nil {
		moduleArgs := append([]string{"-m", pythonModule}, args...)
		cmd := exec.Command(python, moduleArgs...)
		cmd.Env = agentCommandEnv(root)
		return cmd, nil
	}
	return nil, fmt.Errorf("%s not found; run the magatama Python environment setup first", binaryName)
}

func runAgentPassthrough(cmd *exec.Cmd) error {
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

func agentRepoRoot() string {
	if cwd, err := os.Getwd(); err == nil {
		if root, err := findGitRoot(cwd); err == nil {
			return root
		}
		return cwd
	}
	return "."
}

func agentCommandEnv(root string) []string {
	env := os.Environ()
	env = appendEnvIfMissing(env, "AGENT_DAEMON_ENV_FILE", filepath.Join(root, "ops", "local-agent", "agent-daemon.env"))
	env = prependPythonPath(env, filepath.Join(root, "20-actors", "magatama", "py", "src"))
	return env
}

func appendEnvIfMissing(env []string, key string, value string) []string {
	prefix := key + "="
	for i, item := range env {
		if strings.HasPrefix(item, prefix) {
			if strings.TrimSpace(strings.TrimPrefix(item, prefix)) == "" {
				env[i] = prefix + value
			}
			return env
		}
	}
	return append(env, prefix+value)
}

func prependPythonPath(env []string, path string) []string {
	key := "PYTHONPATH"
	prefix := key + "="
	for i, item := range env {
		if strings.HasPrefix(item, prefix) {
			current := strings.TrimPrefix(item, prefix)
			if current == "" {
				env[i] = prefix + path
			} else {
				env[i] = prefix + path + string(os.PathListSeparator) + current
			}
			return env
		}
	}
	return append(env, prefix+path)
}

func isExecutableFile(path string) bool {
	info, err := os.Stat(path)
	if err != nil || info.IsDir() {
		return false
	}
	return info.Mode()&0o111 != 0
}

func isHelpArg(arg string) bool {
	return arg == "help" || arg == "--help" || arg == "-h"
}

func agentEnvDefault(key string, fallback string) string {
	if value := strings.TrimSpace(os.Getenv(key)); value != "" {
		return value
	}
	return fallback
}

type agentStatusWebSummary struct {
	HealthLevel string
	HealthScore float64
}

func fetchAgentStatusWebSummary(baseURL string, agentDID string) (agentStatusWebSummary, bool) {
	healthClient := http.Client{Timeout: time.Second}
	healthResp, err := healthClient.Get(baseURL + "/health")
	if err != nil {
		return agentStatusWebSummary{}, false
	}
	io.Copy(io.Discard, healthResp.Body)
	healthResp.Body.Close()
	if healthResp.StatusCode != http.StatusOK {
		return agentStatusWebSummary{}, false
	}

	statusURL := baseURL + "/api/status?agentDid=" + url.QueryEscape(agentDID)
	client := http.Client{Timeout: 8 * time.Second}
	resp, err := client.Get(statusURL)
	if err != nil {
		return agentStatusWebSummary{}, true
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		io.Copy(io.Discard, resp.Body)
		return agentStatusWebSummary{}, true
	}
	var payload struct {
		HealthEvaluation struct {
			Level string  `json:"level"`
			Score float64 `json:"score"`
		} `json:"healthEvaluation"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return agentStatusWebSummary{}, true
	}
	return agentStatusWebSummary{HealthLevel: payload.HealthEvaluation.Level, HealthScore: payload.HealthEvaluation.Score}, true
}

func agentWebHostPort(baseURL string) (string, string) {
	parsed, err := url.Parse(baseURL)
	if err != nil {
		return defaultOrganismStatusWebHost, defaultOrganismStatusWebPort
	}
	host := parsed.Hostname()
	if host == "" {
		host = defaultOrganismStatusWebHost
	}
	port := parsed.Port()
	if port == "" {
		switch parsed.Scheme {
		case "https":
			port = "443"
		case "http", "":
			port = defaultOrganismStatusWebPort
		default:
			port = defaultOrganismStatusWebPort
		}
	}
	if _, err := strconv.Atoi(port); err != nil {
		port = defaultOrganismStatusWebPort
	}
	return host, port
}

func openAgentStatusURL(statusURL string) error {
	var cmd *exec.Cmd
	switch runtime.GOOS {
	case "darwin":
		cmd = exec.Command("open", statusURL)
	case "windows":
		cmd = exec.Command("rundll32", "url.dll,FileProtocolHandler", statusURL)
	default:
		cmd = exec.Command("xdg-open", statusURL)
	}
	if err := cmd.Start(); err != nil {
		return fmt.Errorf("open status WebUI: %w", err)
	}
	return nil
}
