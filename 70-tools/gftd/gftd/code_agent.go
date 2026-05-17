package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const agentAppRelPath = "60-apps/ai-gftd-terminal-agent"

// runCodeAgent implements `gftd code agent` and `gftd code agent server`.
//
// Usage:
//
//	gftd code agent           — connect to LangGraph Server (AGENT_SERVER) and launch REPL
//	gftd code agent --local   — run graph in-process (no server needed)
//	gftd code agent server    — start LangGraph Server with `langgraph dev`
//	gftd code bench           — run bench.py benchmark suite
func runCodeAgent(args []string) error {
	if len(args) > 0 && args[0] == "server" {
		return runCodeAgentServer(args[1:])
	}
	if len(args) > 0 {
		switch args[0] {
		case "help", "--help", "-h":
			printCodeAgentUsage()
			return nil
		}
	}

	fs := flag.NewFlagSet("code agent", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	local := fs.Bool("local", false, "run graph in-process (no server)")
	agentDir := fs.String("dir", "", "terminal-agent app dir (default: <repo>/60-apps/ai-gftd-terminal-agent)")
	model := fs.String("model", envOr("AGENT_MODEL", "anthropic/claude-sonnet-4-6"), "OpenRouter model id")
	apiKey := fs.String("api-key", envOr("OPENROUTER_API_KEY", ""), "OpenRouter API key")
	comfyURL := fs.String("comfyui-url", envOr("COMFYUI_UPSTREAM_URL", ""), "RunPod ComfyUI URL (https://{pod-id}-8188.proxy.runpod.net)")
	serverURL := fs.String("agent-server", envOr("AGENT_SERVER", "http://localhost:2024"), "LangGraph Server URL (server mode only)")
	uvBin := fs.String("uv-bin", "uv", "uv binary path/name")
	dryRun := fs.Bool("dry-run", false, "print resolved command and exit")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	workDir, err := resolveAgentDir(*agentDir)
	if err != nil {
		return err
	}

	if strings.TrimSpace(*apiKey) == "" {
		return fmt.Errorf(
			"OPENROUTER_API_KEY is not set.\n" +
				"Set it via env or --api-key, or load from Keychain:\n" +
				"  security find-generic-password -s gftd.openrouter -w",
		)
	}

	env := os.Environ()
	env = setEnv(env, "OPENROUTER_API_KEY", strings.TrimSpace(*apiKey))
	env = setEnv(env, "AGENT_MODEL", strings.TrimSpace(*model))
	if u := strings.TrimSpace(*comfyURL); u != "" {
		env = setEnv(env, "COMFYUI_UPSTREAM_URL", u)
	}
	if !*local {
		env = setEnv(env, "AGENT_SERVER", strings.TrimSpace(*serverURL))
	}

	uvArgs := []string{"run", "agent"}
	if *local {
		uvArgs = append(uvArgs, "--local")
	}

	fmt.Fprintf(os.Stderr, "==> gftd code agent: model=%s local=%v dir=%s\n",
		strings.TrimSpace(*model), *local, workDir)
	if *dryRun {
		fmt.Fprintf(os.Stderr, "==> dry-run: %s %s\n", *uvBin, strings.Join(uvArgs, " "))
		return nil
	}

	if _, err := exec.LookPath(*uvBin); err != nil {
		return fmt.Errorf("uv not found: %s — install via: curl -LsSf https://astral.sh/uv/install.sh | sh", *uvBin)
	}

	return runCmdEnv(workDir, env, *uvBin, uvArgs...)
}

// runCodeAgentServer starts the LangGraph Server via `langgraph dev` (or `uv run langgraph dev`).
func runCodeAgentServer(args []string) error {
	fs := flag.NewFlagSet("code agent server", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	agentDir := fs.String("dir", "", "terminal-agent app dir (default: <repo>/60-apps/ai-gftd-terminal-agent)")
	port := fs.String("port", "2024", "port for LangGraph Server")
	host := fs.String("host", "0.0.0.0", "host for LangGraph Server")
	uvBin := fs.String("uv-bin", "uv", "uv binary path/name")
	dryRun := fs.Bool("dry-run", false, "print resolved command and exit")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	workDir, err := resolveAgentDir(*agentDir)
	if err != nil {
		return err
	}

	// Prefer `uv run langgraph dev` so the venv is always activated.
	uvArgs := []string{"run", "langgraph", "dev",
		"--host", strings.TrimSpace(*host),
		"--port", strings.TrimSpace(*port),
	}

	fmt.Fprintf(os.Stderr, "==> gftd code agent server: %s:%s dir=%s\n",
		strings.TrimSpace(*host), strings.TrimSpace(*port), workDir)
	if *dryRun {
		fmt.Fprintf(os.Stderr, "==> dry-run: %s %s\n", *uvBin, strings.Join(uvArgs, " "))
		return nil
	}

	if _, err := exec.LookPath(*uvBin); err != nil {
		return fmt.Errorf("uv not found: %s", *uvBin)
	}

	return runCmdEnv(workDir, os.Environ(), *uvBin, uvArgs...)
}

// runCodeBench runs bench.py via `uv run python scripts/bench.py` with provider
// routing automatically applied based on the model ID.
func runCodeBench(args []string) error {
	fs := flag.NewFlagSet("code bench", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	model := fs.String("model", envOr("AGENT_MODEL", "anthropic/claude-sonnet-4-6"), "OpenRouter model id")
	apiKey := fs.String("api-key", envOr("OPENROUTER_API_KEY", ""), "OpenRouter API key")
	runs := fs.Int("runs", 3, "runs per benchmark")
	agentic := fs.Bool("agentic", false, "include agentic suite")
	swe := fs.Bool("swe", false, "include SWE-bench style harder tasks")
	latencyOnly := fs.Bool("latency-only", false, "latency benches only")
	skipTools := fs.Bool("skip-tools", false, "skip tool benches")
	jsonOut := fs.Bool("json", false, "JSON output")
	rwExport := fs.Bool("rw-export", false, "export results to RisingWave (RW_DATABASE_URL env)")
	outFile := fs.String("out", "", "write JSON to file")
	agentDir := fs.String("dir", "", "terminal-agent app dir (default: <repo>/60-apps/ai-gftd-terminal-agent)")
	uvBin := fs.String("uv-bin", "uv", "uv binary path/name")
	dryRun := fs.Bool("dry-run", false, "print resolved command and exit")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	workDir, err := resolveAgentDir(*agentDir)
	if err != nil {
		return err
	}

	if strings.TrimSpace(*apiKey) == "" {
		return fmt.Errorf(
			"OPENROUTER_API_KEY is not set.\n" +
				"Set it via env or --api-key, or load from Keychain:\n" +
				"  security find-generic-password -s gftd.openrouter -w",
		)
	}

	env := os.Environ()
	env = setEnv(env, "OPENROUTER_API_KEY", strings.TrimSpace(*apiKey))
	env = setEnv(env, "AGENT_MODEL", strings.TrimSpace(*model))
	if pc := providerConfigForModel(strings.TrimSpace(*model)); pc != "" {
		env = setEnv(env, "OPENROUTER_PROVIDER_CONFIG", pc)
	}

	uvArgs := []string{"run", "python", "scripts/bench.py",
		"--model", strings.TrimSpace(*model),
		"--runs", fmt.Sprintf("%d", *runs),
	}
	if *agentic {
		uvArgs = append(uvArgs, "--agentic")
	}
	if *swe {
		uvArgs = append(uvArgs, "--swe")
	}
	if *latencyOnly {
		uvArgs = append(uvArgs, "--latency-only")
	}
	if *skipTools {
		uvArgs = append(uvArgs, "--skip-tools")
	}
	if *jsonOut {
		uvArgs = append(uvArgs, "--json")
	}
	if *rwExport {
		uvArgs = append(uvArgs, "--rw-export")
	}
	if *outFile != "" {
		uvArgs = append(uvArgs, "--out", *outFile)
	}

	fmt.Fprintf(os.Stderr, "==> gftd code bench: model=%s agentic=%v swe=%v dir=%s\n",
		strings.TrimSpace(*model), *agentic, *swe, workDir)
	if pc := providerConfigForModel(strings.TrimSpace(*model)); pc != "" {
		fmt.Fprintf(os.Stderr, "==> provider routing: %s\n", pc)
	}
	if *dryRun {
		fmt.Fprintf(os.Stderr, "==> dry-run: %s %s\n", *uvBin, strings.Join(uvArgs, " "))
		return nil
	}

	if _, err := exec.LookPath(*uvBin); err != nil {
		return fmt.Errorf("uv not found: %s — install via: curl -LsSf https://astral.sh/uv/install.sh | sh", *uvBin)
	}

	return runCmdEnv(workDir, env, *uvBin, uvArgs...)
}

// providerConfigForModel returns the OpenRouter provider routing JSON for models
// that require specific provider selection (e.g. Kimi → Inceptron SE only,
// DeepSeek → US providers only). Returns "" for models with no routing constraint.
func providerConfigForModel(model string) string {
	switch {
	case strings.Contains(model, "kimi-k2") || strings.Contains(model, "moonshotai/kimi"):
		// Kimi K2.x: Inceptron (Sweden) only — prevents routing to Chinese API
		return `{"order":["Inceptron"],"allow_fallbacks":false}`
	case strings.Contains(model, "deepseek-v4-pro"):
		// DeepSeek V4 Pro: US providers only
		return `{"order":["AtlasCloud","NovitaAI","DeepInfra","Together","Fireworks"],"allow_fallbacks":false}`
	default:
		return ""
	}
}

func resolveAgentDir(override string) (string, error) {
	if override != "" {
		abs, err := filepath.Abs(override)
		if err != nil {
			return "", fmt.Errorf("resolve --dir: %w", err)
		}
		if stat, err := os.Stat(abs); err != nil || !stat.IsDir() {
			return "", fmt.Errorf("agent dir not found: %s", abs)
		}
		return abs, nil
	}

	cwd, err := os.Getwd()
	if err != nil {
		return "", fmt.Errorf("getwd: %w", err)
	}
	root, err := findGitRoot(cwd)
	if err != nil {
		return "", fmt.Errorf("cannot find git root (use --dir): %w", err)
	}
	dir := filepath.Join(root, agentAppRelPath)
	if stat, err := os.Stat(dir); err != nil || !stat.IsDir() {
		return "", fmt.Errorf(
			"terminal-agent app not found at %s\n"+
				"Run from the repo root or pass --dir explicitly.", dir)
	}
	return dir, nil
}

func printCodeAgentUsage() {
	fmt.Print(`gftd code agent — launch the OpenRouter + RunPod ComfyUI terminal agent
gftd code bench — benchmark latency, tool use, and agentic capability

USAGE:
  gftd code agent [flags]                   launch REPL (connects to AGENT_SERVER)
  gftd code agent --local [flags]           run graph in-process (no server)
  gftd code agent server [flags]            start LangGraph Server (langgraph dev)
  gftd code bench [flags]                   run bench.py benchmark suite

FLAGS (agent):
  --local               run graph in-process with MemorySaver checkpointer
  --dir                 path to terminal-agent app (default: <repo>/60-apps/ai-gftd-terminal-agent)
  --model               OpenRouter model id (default: AGENT_MODEL or anthropic/claude-sonnet-4-6)
  --api-key             OpenRouter API key (default: OPENROUTER_API_KEY)
  --comfyui-url         RunPod ComfyUI endpoint, e.g. https://{pod-id}-8188.proxy.runpod.net
                        (default: COMFYUI_UPSTREAM_URL)
  --agent-server        LangGraph Server URL for server mode (default: AGENT_SERVER or http://localhost:2024)
  --uv-bin              uv binary (default: uv)
  --dry-run             print resolved command and exit

FLAGS (server):
  --dir                 path to terminal-agent app
  --port                server port (default: 2024)
  --host                server host (default: 0.0.0.0)
  --uv-bin              uv binary (default: uv)
  --dry-run             print resolved command and exit

FLAGS (bench):
  --model               OpenRouter model id (default: AGENT_MODEL or anthropic/claude-sonnet-4-6)
  --api-key             OpenRouter API key (default: OPENROUTER_API_KEY)
  --runs                runs per benchmark (default: 3)
  --agentic             include agentic suite (bash task, multi-tool chain, error recovery)
  --swe                 include SWE-bench style harder tasks (code comprehension, bug hunt,
                        write+run+verify, multi-file synthesis)
  --latency-only        latency benches only
  --skip-tools          skip tool benches
  --json                JSON output (pipe-friendly)
  --rw-export           persist results to RisingWave (RW_DATABASE_URL or DATABASE_URL env)
  --out                 write JSON to file
  --dir                 path to terminal-agent app
  --uv-bin              uv binary (default: uv)
  --dry-run             print resolved command and exit
  Provider routing is auto-applied:
    moonshotai/kimi-k2.x  → Inceptron (SE) only, allow_fallbacks=false
    deepseek-v4-pro       → US providers only, allow_fallbacks=false

ENV:
  OPENROUTER_API_KEY    required — OpenRouter API key
  AGENT_MODEL           optional — default model
  COMFYUI_UPSTREAM_URL  optional — RunPod ComfyUI endpoint (agent only)
  AGENT_SERVER          optional — LangGraph Server URL (server mode)

KEYCHAIN:
  security find-generic-password -s gftd.openrouter -w   # read OpenRouter key
  security add-generic-password -s gftd.openrouter -a OPENROUTER_API_KEY -w sk-or-...

EXAMPLES:
  # local mode (no server, dev)
  OPENROUTER_API_KEY=$(security find-generic-password -s gftd.openrouter -w) \
    gftd code agent --local

  # server mode: start server in one terminal, REPL in another
  OPENROUTER_API_KEY=... gftd code agent server
  OPENROUTER_API_KEY=... gftd code agent

  # benchmark Kimi K2.6 vs Opus 4.6 (agentic + SWE comparison)
  gftd code bench --model moonshotai/kimi-k2.6 --agentic --swe --json > /tmp/kimi.json
  gftd code bench --model anthropic/claude-opus-4-6 --agentic --swe --json > /tmp/opus.json
  uv run python scripts/bench.py --compare /tmp/kimi.json /tmp/opus.json

  # persist results to RisingWave
  gftd code bench --model anthropic/claude-sonnet-4-6 --agentic --swe --rw-export

  # quick latency-only bench
  gftd code bench --latency-only

  # specific model (agent)
  gftd code agent --model google/gemini-2.5-pro --local
`)
}
