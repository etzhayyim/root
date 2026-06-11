// baien.go — `e7m baien <subcommand>` for ad-hoc baien interaction.
//
// Sibling to `e7m bench` (bench.go). The two are split so that bench
// concerns (multi-task lm-eval runs, snapshot orchestration) stay
// separate from interactive / one-shot inference concerns.
package main

import (
	_ "embed"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

//go:embed embedded/baien_prompt.py
var baienPromptPy []byte

func runBaien(args []string) error {
	if len(args) == 0 {
		printBaienUsage()
		return nil
	}
	switch args[0] {
	case "prompt":
		return cmdBaienPrompt(args[1:])
	case "help", "--help", "-h":
		printBaienUsage()
		return nil
	default:
		return fmt.Errorf("unknown baien subcommand: %s\nRun 'e7m baien help' for usage.", args[0])
	}
}

func printBaienUsage() {
	fmt.Printf(`e7m baien — ad-hoc interaction with the baien BitNet b1.58 2B-4T model

USAGE:
  e7m baien <subcommand> [flags]

SUBCOMMANDS:
  prompt   Run a single-prompt inference. Default path is CPU bf16 so it
           can run alongside a ROCm bench job on EVO-X2 without GPU
           contention (per ADR-2605202345 + ADR-2605232400 §coexistence).

FLAGS (for prompt):
  --text "..."     prompt text (required unless --stdin)
  --stdin          read prompt from stdin
  --host <alias>   ssh alias for the host that has baien (default: %s)
  --model <id>     model id or local dir (default: %s)
  --rocm           dispatch via ComfyUI python_embeded (faster but
                   serializes against any ROCm bench currently running)
  --max-new <N>    max new tokens (default 256)
  --temperature <T>  0.0=greedy (default), >0=sampling
  --system "..."   optional system prompt
  --json           print one JSON object instead of plain text

EXAMPLES:
  e7m baien prompt --text "日本の首都は?"
  e7m baien prompt --text "explain BitNet 1.58 in 50 words" --max-new 80
  echo "list 3 EU capitals" | e7m baien prompt --stdin
  e7m baien prompt --text "hi" --rocm                    # uses GPU (post-Core 3')
  e7m baien prompt --text "summarize: ..." --json | jq .

SEE ALSO:
  e7m bench help               (canned bench prompts + lm-eval-harness)
  ADR-2605092350               (baien design / runtimes)
  ADR-2605202345               (EVO-X2 ROCm pod)
`, defaultBenchHost, defaultBenchModel)
}

// ----- subcommand: prompt -------------------------------------------------

func cmdBaienPrompt(args []string) error {
	fs := flag.NewFlagSet("baien prompt", flag.ContinueOnError)
	text := fs.String("text", "", "prompt text (required unless --stdin)")
	stdin := fs.Bool("stdin", false, "read prompt from stdin")
	host := fs.String("host", defaultBenchHost, "ssh alias")
	model := fs.String("model", defaultBenchModel, "model id or local dir")
	rocm := fs.Bool("rocm", false, "dispatch via ComfyUI python_embeded (GPU)")
	maxNew := fs.Int("max-new", 256, "max new tokens")
	temperature := fs.Float64("temperature", 0.0, "sampling temperature")
	system := fs.String("system", "", "system prompt (optional)")
	wantJSON := fs.Bool("json", false, "emit single JSON object")
	if err := fs.Parse(args); err != nil {
		return err
	}

	if !*stdin && *text == "" {
		return fmt.Errorf("either --text or --stdin is required")
	}

	// Stage the embedded prompt script in a temp dir, scp to the host.
	tmpDir, err := os.MkdirTemp("", "baien-prompt-*")
	if err != nil {
		return err
	}
	defer os.RemoveAll(tmpDir)
	localScript := filepath.Join(tmpDir, "baien_prompt.py")
	if err := os.WriteFile(localScript, baienPromptPy, 0o644); err != nil {
		return err
	}
	remoteScript := "baien_prompt.py"
	if err := scpTo(localScript, *host, remoteScript); err != nil {
		return err
	}

	pyCmd := "python"
	if *rocm {
		pyCmd = "C:\\Users\\gad\\ComfyUI\\ComfyUI_windows_portable\\python_embeded\\python.exe"
	}

	parts := []string{
		pyCmd, remoteScript,
		"--model", *model,
		"--max-new", fmt.Sprintf("%d", *maxNew),
		"--temperature", fmt.Sprintf("%g", *temperature),
	}
	if *wantJSON {
		parts = append(parts, "--json")
	}
	if *system != "" {
		parts = append(parts, "--system", _shellQuote(*system))
	}
	if *stdin {
		// We pipe through ssh stdin to the python's stdin.
		cmd := strings.Join(parts, " ")
		return runSshStdin(*host, cmd, os.Stdin)
	}
	parts = append(parts, "--prompt", _shellQuote(*text))
	cmd := strings.Join(parts, " ")
	return sshRunStream(*host, cmd)
}

// ----- helpers ------------------------------------------------------------

func _shellQuote(s string) string {
	// double-quote and escape inner double-quotes (Windows cmd-friendly).
	return "\"" + strings.ReplaceAll(s, "\"", "\\\"") + "\""
}

func runSshStdin(host, cmd string, stdin *os.File) error {
	c := exec.Command("ssh", host, cmd)
	c.Stdin = stdin
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}
