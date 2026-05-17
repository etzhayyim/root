package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func runCode(args []string) error {
	if len(args) > 0 && args[0] == "exec" {
		return runCodeExec(args[1:])
	}
	if len(args) > 0 && args[0] == "agent" {
		return runCodeAgent(args[1:])
	}
	if len(args) > 0 && args[0] == "bench" {
		return runCodeBench(args[1:])
	}

	if len(args) > 0 {
		switch args[0] {
		case "help", "--help", "-h":
			printCodeUsage()
			return nil
		}
	}

	// default: interactive — delegate to terminal-agent REPL
	return runCodeAgent(args)
}

// runCodeExec runs the terminal-agent in non-interactive one-shot mode.
// It is called programmatically by kaizen_logs.go with --dir and --message flags.
func runCodeExec(args []string) error {
	if len(args) > 0 {
		switch args[0] {
		case "help", "--help", "-h":
			printCodeExecUsage()
			return nil
		}
	}

	fs := flag.NewFlagSet("code exec", flag.ContinueOnError)
	fs.SetOutput(os.Stdout)

	dir := fs.String("dir", ".", "working directory for the agent")
	message := fs.String("message", "", "one-shot prompt (required)")
	model := fs.String("model", envOr("AGENT_MODEL", "anthropic/claude-sonnet-4-6"), "OpenRouter model id")
	apiKey := fs.String("api-key", envOr("OPENROUTER_API_KEY", ""), "OpenRouter API key")
	uvBin := fs.String("uv-bin", "uv", "uv binary path/name")
	dryRun := fs.Bool("dry-run", false, "print resolved command and exit")

	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	msg := strings.TrimSpace(*message)
	if msg == "" && fs.NArg() > 0 {
		msg = strings.Join(fs.Args(), " ")
	}
	if msg == "" {
		return fmt.Errorf("--message is required for 'gftd code exec'")
	}

	if strings.TrimSpace(*apiKey) == "" {
		return fmt.Errorf(
			"OPENROUTER_API_KEY is not set.\n" +
				"Set it via env or --api-key, or load from Keychain:\n" +
				"  security find-generic-password -s gftd.openrouter -w",
		)
	}

	workDir, err := filepath.Abs(*dir)
	if err != nil {
		return fmt.Errorf("resolve --dir: %w", err)
	}
	if stat, err := os.Stat(workDir); err != nil || !stat.IsDir() {
		return fmt.Errorf("working directory not found: %s", workDir)
	}

	agentDir, err := resolveAgentDir("")
	if err != nil {
		return err
	}

	env := os.Environ()
	env = setEnv(env, "OPENROUTER_API_KEY", strings.TrimSpace(*apiKey))
	env = setEnv(env, "AGENT_MODEL", strings.TrimSpace(*model))

	uvArgs := []string{"run", "agent", "--local", "--message", msg, "--dir", workDir}

	fmt.Fprintf(os.Stderr, "==> gftd code exec: model=%s dir=%s\n", strings.TrimSpace(*model), workDir)
	if *dryRun {
		fmt.Fprintf(os.Stderr, "==> dry-run: %s %s\n", *uvBin, strings.Join(uvArgs, " "))
		return nil
	}

	return runCmdEnv(agentDir, env, *uvBin, uvArgs...)
}

func printCodeUsage() {
	fmt.Print(`gftd code — terminal-agent (LangGraph) code assistant

USAGE:
  gftd code [flags]                   launch interactive REPL (delegates to gftd code agent)
  gftd code exec [flags]              non-interactive one-shot (--message required)
  gftd code agent [flags]             launch REPL (connects to AGENT_SERVER)
  gftd code agent --local [flags]     run graph in-process (no server)
  gftd code agent server [flags]      start LangGraph Server (langgraph dev)
  gftd code bench [flags]             run bench.py benchmark suite

FLAGS (exec):
  --dir         working directory for the agent (default: .)
  --message     one-shot prompt (required)
  --model       OpenRouter model id (default: AGENT_MODEL or anthropic/claude-sonnet-4-6)
  --api-key     OpenRouter API key (default: OPENROUTER_API_KEY)
  --uv-bin      uv binary (default: uv)
  --dry-run     print resolved command and exit

ENV:
  OPENROUTER_API_KEY    required
  AGENT_MODEL           optional — default model

KEYCHAIN:
  security find-generic-password -s gftd.openrouter -w

EXAMPLES:
  gftd code                                             # interactive REPL
  gftd code exec --message "fix failing tests"         # one-shot
  gftd code exec --dir /tmp/work --message "refactor"  # one-shot in specific dir
  gftd code agent --local                              # in-process REPL (no server)
  gftd code agent server                               # start LangGraph Server
`)
}

func printCodeExecUsage() {
	fmt.Print(`gftd code exec — non-interactive one-shot terminal-agent (LangGraph)

USAGE:
  gftd code exec [flags]

FLAGS:
  --dir         working directory for the agent (default: .)
  --message     one-shot prompt (required)
  --model       OpenRouter model id (default: AGENT_MODEL or anthropic/claude-sonnet-4-6)
  --api-key     OpenRouter API key (default: OPENROUTER_API_KEY)
  --uv-bin      uv binary (default: uv)
  --dry-run     print resolved command and exit

EXAMPLES:
  gftd code exec --message "fix the failing test in pkg/auth"
  gftd code exec --dir /tmp/work --message "refactor the parser"
`)
}

func splitArgsOnDoubleDash(args []string) (left []string, right []string) {
	for i, a := range args {
		if a == "--" {
			return args[:i], args[i+1:]
		}
	}
	return args, nil
}

func envOr(key, fallback string) string {
	v := strings.TrimSpace(os.Getenv(key))
	if v == "" {
		return fallback
	}
	return v
}
