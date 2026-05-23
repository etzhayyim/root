// bench.go — `e7m bench` subcommands: dispatch baien benches to a remote host
// loaded with baien (BitNet b1.58 2B-4T). Today's targets are EVO-X2 (gad)
// per ADR-2605202345; other hosts work as long as Python + transformers
// (and optionally lm-eval-harness) are installed.
package main

import (
	_ "embed"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"time"
)

//go:embed embedded/microbench.py
var microbenchPy []byte

//go:embed embedded/lm_eval_wrapper.py
var lmEvalWrapperPy []byte

const (
	defaultBenchHost  = "evo"
	defaultBenchModel = "microsoft/bitnet-b1.58-2B-4T-bf16"
)

func runBench(args []string) error {
	if len(args) == 0 {
		printBenchUsage()
		return nil
	}
	switch args[0] {
	case "micro":
		return cmdBenchMicro(args[1:])
	case "core4":
		return cmdBenchCore4(args[1:])
	case "list":
		return cmdBenchList(args[1:])
	case "distill":
		return cmdBenchDistill(args[1:])
	case "rope-extend":
		return cmdBenchRopeExtend(args[1:])
	case "mx-train":
		return cmdBenchMxTrain(args[1:])
	case "help", "--help", "-h":
		printBenchUsage()
		return nil
	default:
		return fmt.Errorf("unknown bench subcommand: %s\nRun 'e7m bench help' for usage.", args[0])
	}
}

// ----- subcommand: mx-train ----------------------------------------------

func cmdBenchMxTrain(args []string) error {
	fs := flag.NewFlagSet("bench mx-train", flag.ContinueOnError)
	phase := fs.String("phase", "A", "training phase A/B/C/D (per ADR-2605232500)")
	graftDir := fs.String("graft-data-dir", "~/baien-graft/batch-001",
		"baien-graft sample.json root (on local host where the trainer runs)")
	outRoot := fs.String("out-root", "baien-mx-out",
		"trainer output dir on local host")
	dryRun := fs.Bool("dry-run", false, "walk trainer setup without loading SigLIP/baien")
	if err := fs.Parse(args); err != nil {
		return err
	}
	cmdline := []string{
		"python", "-m", "baien_mx_train",
		"--graft-data-dir", *graftDir,
		"--phase", *phase,
		"--out-root", *outRoot,
	}
	if *dryRun {
		cmdline = append(cmdline, "--dry-run")
	}
	fmt.Printf("[bench mx-train] %s\n", strings.Join(cmdline, " "))
	c := exec.Command(cmdline[0], cmdline[1:]...)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	c.Dir = "70-tools/baien-mx-train"
	return c.Run()
}

// ----- subcommand: distill ------------------------------------------------

func cmdBenchDistill(args []string) error {
	fs := flag.NewFlagSet("bench distill", flag.ContinueOnError)
	benchDir := fs.String("bench-dir", filepath.Join("90-docs", "baien"),
		"baien bench output dir (default: 90-docs/baien)")
	maxIter := fs.Int("max-iter", 3, "max ReAct loop iterations")
	nPer := fs.Int("n-per-category", 200, "training examples per weak category")
	source := fs.String("source", "hf",
		"distill source: 'hf' (default, public datasets like lordx64/reasoning-distill-opus-4-7-max-sft) "+
			"or 'teacher' (on-fleet OSS teacher fallback per ADR §3b)")
	quick := fs.Bool("quick", false, "N=50, epochs=1 — fast iteration")
	dryRun := fs.Bool("dry-run", false, "walk the graph without fetching dataset / training")
	if err := fs.Parse(args); err != nil {
		return err
	}
	cmdline := []string{
		"python", "-m", "baien_distill",
		"--bench-dir", *benchDir,
		"--max-iter", fmt.Sprintf("%d", *maxIter),
		"--n-per-category", fmt.Sprintf("%d", *nPer),
		"--source", *source,
	}
	if *quick {
		cmdline = append(cmdline, "--quick")
	}
	if *dryRun {
		cmdline = append(cmdline, "--dry-run")
	}
	fmt.Printf("[bench distill] %s\n", strings.Join(cmdline, " "))
	c := exec.Command(cmdline[0], cmdline[1:]...)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	c.Dir = "70-tools/baien-distill"
	return c.Run()
}

func printBenchUsage() {
	fmt.Printf(`e7m bench — baien bench dispatch (BitNet b1.58 2B-4T)

USAGE:
  e7m bench <subcommand> [flags]

SUBCOMMANDS:
  micro    Run baien-microbench (15 verifiable prompts, rule-based scorer).
           ~5 min on EVO-X2 CPU bf16. No external eval harness required.
  core4    Run lm-eval-harness Core 4 (IFEval / GPQA Diamond / MMLU-Redux /
           Global PIQA). ~4h on EVO-X2 CPU bf16. Requires lm-eval installed
           on the target host.
  list     List supported benches and their estimated runtime.
  distill  Run the baien-distill ReAct loop (analyze → fetch_dataset → SFT → eval).
           Per ADR-2605231300. Default source=hf (Opus-distilled Apache-2.0 SFT);
           --source teacher falls back to on-fleet OSS teacher generation.
  rope-extend  Stage 1 of ADR-2605231600 — run microbench_long under 3 RoPE
           configs (baseline / linear×4 / NTK×4) and emit a side-by-side
           pass-rate matrix to decide whether to promote to Stage 2 (YaRN).
  mx-train  baien Move 1 image graft self-training (frozen SigLIP + 1.58-bit
           projector + frozen baien trunk) per ADR-2605232500. Phase A=80s
           smoke / B=40min bootstrap / C=6.7h scale on EVO-X2 ROCm.

COMMON FLAGS:
  --host <alias>     SSH host (default: %s). Must accept ssh <alias>:python.
  --model <hf-id>    HuggingFace model id (default: %s).
  --out <dir>        Local directory to mirror results into.
                     Default: 90-docs/baien/<bench>-<YYMMDD>/.

EXAMPLES:
  e7m bench list
  e7m bench micro                                # full 15-prompt run on default host
  e7m bench micro --limit 3                      # quick sanity (3 prompts)
  e7m bench core4 --only gpqa_diamond_zeroshot   # one task only
  e7m bench core4 --host judah                   # dispatch to another fleet node

SEE ALSO:
  - 90-docs/baien/frontier-bench-snapshot-260523.md (latest results snapshot)
  - 70-tools/scripts/bench/baien-microbench/   (Python harness source of truth)
  - ADR-2605092350 (baien design)
  - ADR-2605202345 (EVO-X2 fleet integration; default bench host)
`, defaultBenchHost, defaultBenchModel)
}

// ----- subcommand: micro --------------------------------------------------

func cmdBenchMicro(args []string) error {
	fs := flag.NewFlagSet("bench micro", flag.ContinueOnError)
	host := fs.String("host", defaultBenchHost, "SSH host alias")
	model := fs.String("model", defaultBenchModel, "HuggingFace model id")
	out := fs.String("out", "", "local output dir (default: 90-docs/baien/microbench-<date>/)")
	limit := fs.Int("limit", 0, "if >0, run only N prompts")
	if err := fs.Parse(args); err != nil {
		return err
	}
	stamp := time.Now().Format("060102") // YYMMDD
	if *out == "" {
		*out = filepath.Join("90-docs", "baien", "microbench-"+stamp)
	}
	if err := os.MkdirAll(*out, 0o755); err != nil {
		return fmt.Errorf("mkdir out: %w", err)
	}

	scriptPath := filepath.Join(*out, "microbench.py")
	if err := os.WriteFile(scriptPath, microbenchPy, 0o644); err != nil {
		return fmt.Errorf("write embedded script: %w", err)
	}

	// relative paths land in remote user's home (C:\Users\gad on Windows / $HOME on POSIX).
	// Avoid absolute `C:/...` here — scp parses the first colon as host:path separator.
	remoteScript := "baien-microbench.py"
	remoteResults := "results-" + stamp + ".jsonl"

	fmt.Printf("[bench micro] host=%s model=%s out=%s\n", *host, *model, *out)
	if err := scpTo(scriptPath, *host, remoteScript); err != nil {
		return err
	}

	cmd := fmt.Sprintf(
		`set TORCH_COMPILE_DISABLE=1 & set TORCHINDUCTOR_DISABLE=1 & del %s 2>nul & python %s --model %s --out %s`,
		remoteResults, remoteScript, *model, remoteResults,
	)
	if *limit > 0 {
		cmd += fmt.Sprintf(" --limit %d", *limit)
	}
	if err := sshRunStream(*host, cmd); err != nil {
		return fmt.Errorf("remote micro run: %w", err)
	}

	localResults := filepath.Join(*out, "results.jsonl")
	if err := scpFrom(*host, remoteResults, localResults); err != nil {
		return err
	}
	fmt.Printf("[bench micro] results → %s\n", localResults)
	return summarizeMicro(localResults)
}

type microRow struct {
	ID       string  `json:"id"`
	Category string  `json:"category"`
	OK       bool    `json:"ok"`
	Reason   string  `json:"reason"`
	Elapsed  float64 `json:"elapsed_sec"`
	Response string  `json:"response"`
}

func summarizeMicro(path string) error {
	f, err := os.Open(path)
	if err != nil {
		return err
	}
	defer f.Close()
	dec := json.NewDecoder(f)
	byCat := map[string][2]int{} // [pass, total]
	var pass, total int
	for {
		var r microRow
		if err := dec.Decode(&r); err != nil {
			if err == io.EOF {
				break
			}
			return err
		}
		total++
		c := byCat[r.Category]
		c[1]++
		if r.OK {
			pass++
			c[0]++
		}
		byCat[r.Category] = c
	}
	fmt.Println()
	fmt.Printf("[summary] %d/%d = %.1f%%\n", pass, total, 100*float64(pass)/float64(total))
	for cat, pt := range byCat {
		fmt.Printf("  %-14s %d/%d = %.1f%%\n", cat, pt[0], pt[1], 100*float64(pt[0])/float64(pt[1]))
	}
	return nil
}

// ----- subcommand: core4 --------------------------------------------------

type core4Task struct {
	Name        string // lm-eval task id
	DisplayName string
	EstMin      int
}

// task ids verified against lm-eval-harness on EVO-X2 (lm-eval 0.4.x).
// Revised 2026-05-23 per ADR-2605232400: switched mmlu_redux_generative
// (~35h on baien CPU) to the loglikelihood ll-score `mmlu_redux` (~25 min
// on ComfyUI ROCm). matches §A frontier table's MMLU-Redux=acc metric.
var core4Tasks = []core4Task{
	{"gpqa_diamond_zeroshot", "GPQA Diamond (HF-gated, requires HF_TOKEN)", 10},
	{"mmlu_redux", "MMLU-Redux (loglikelihood, all 57 subjects)", 25},
	{"global_piqa_completions", "Global PIQA (ll-ranking, 100+ langs)", 60},
	{"ifeval", "IFEval (Google 541 verifiable prompts, generative)", 150},
}

func cmdBenchCore4(args []string) error {
	fs := flag.NewFlagSet("bench core4", flag.ContinueOnError)
	host := fs.String("host", defaultBenchHost, "SSH host alias")
	model := fs.String("model", defaultBenchModel, "HuggingFace model id")
	out := fs.String("out", "", "local output dir (default: 90-docs/baien/lm-eval-<date>/)")
	only := fs.String("only", "", "comma-separated subset (e.g. 'ifeval,gpqa_diamond_zeroshot')")
	batchSize := fs.Int("batch-size", 1, "lm-eval batch size (CPU bf16 → keep small)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	stamp := time.Now().Format("060102")
	if *out == "" {
		*out = filepath.Join("90-docs", "baien", "lm-eval-"+stamp)
	}
	if err := os.MkdirAll(*out, 0o755); err != nil {
		return err
	}

	tasks := core4Tasks
	if *only != "" {
		want := map[string]bool{}
		for _, s := range strings.Split(*only, ",") {
			want[strings.TrimSpace(s)] = true
		}
		var filtered []core4Task
		for _, t := range tasks {
			if want[t.Name] {
				filtered = append(filtered, t)
			}
		}
		tasks = filtered
	}

	fmt.Printf("[bench core4] host=%s model=%s out=%s\n", *host, *model, *out)
	fmt.Println("[bench core4] tasks:")
	for _, t := range tasks {
		fmt.Printf("  - %-26s ~%d min\n", t.Name, t.EstMin)
	}

	// Relative path -- lands in remote user's home. No `C:/` prefix (scp colon clash).
	remoteOut := "lm-eval-" + stamp
	prep := fmt.Sprintf("if not exist %s mkdir %s", remoteOut, remoteOut)
	if err := sshRunStream(*host, prep); err != nil {
		return fmt.Errorf("remote mkdir: %w", err)
	}

	// Stage the inductor-suppression wrapper once per run (lm-eval-harness's
	// torch.compile probe needs MSVC `cl` on Windows; we patch it out).
	wrapperLocal := filepath.Join(*out, "lm_eval_wrapper.py")
	if err := os.WriteFile(wrapperLocal, lmEvalWrapperPy, 0o644); err != nil {
		return fmt.Errorf("write embedded lm-eval wrapper: %w", err)
	}
	remoteWrapper := "lm_eval_wrapper.py"
	if err := scpTo(wrapperLocal, *host, remoteWrapper); err != nil {
		return err
	}

	// Prefer the ROCm-capable ComfyUI python_embeded over system Python so
	// baien gets gfx1151 (per ADR-2605202345 + ADR-2605232400 revision).
	// Falls back to bare `python` if the env var is unset.
	pyCmd := "C:\\Users\\gad\\ComfyUI\\ComfyUI_windows_portable\\python_embeded\\python.exe"
	for _, t := range tasks {
		fmt.Printf("\n[bench core4] running %s (est ~%d min) via ROCm python...\n", t.Name, t.EstMin)
		remoteFile := remoteOut + "/" + t.Name + ".json"
		// model_args use transformers `bitnet` arch via lm-eval `hf` provider.
		// Invoke the wrapper so dynamo+inductor are pre-patched before lm-eval imports.
		cmd := fmt.Sprintf(
			`%s %s run --model hf --model_args pretrained=%s,dtype=bfloat16 `+
				`--tasks %s --batch_size %d --output_path %s --log_samples`,
			pyCmd, remoteWrapper, *model, t.Name, *batchSize, remoteOut,
		)
		if err := sshRunStream(*host, cmd); err != nil {
			fmt.Fprintf(os.Stderr, "  WARN: %s failed: %v (continuing)\n", t.Name, err)
			continue
		}
		// pull the per-task results directory back
		localTaskDir := filepath.Join(*out, t.Name)
		if err := os.MkdirAll(localTaskDir, 0o755); err != nil {
			return err
		}
		// lm-eval writes results to <output_path>/<sanitized_model>/results_*.json
		_ = scpFromRecursive(*host, remoteOut+"/*", localTaskDir)
		_ = remoteFile // reserved for future per-task json pull
	}

	fmt.Printf("\n[bench core4] done. results → %s\n", *out)
	fmt.Println("  Next: e7m bench list  or  edit 90-docs/baien/frontier-bench-snapshot-260523.md")
	return nil
}

// ----- subcommand: rope-extend --------------------------------------------

func cmdBenchRopeExtend(args []string) error {
	fs := flag.NewFlagSet("bench rope-extend", flag.ContinueOnError)
	model := fs.String("model", defaultBenchModel, "HuggingFace model id")
	outDir := fs.String("out", "", "local output dir (default: 90-docs/baien/context-extend-<YYMMDD>/)")
	only := fs.String("only", "", "comma-separated subset of configs (A_baseline,B_linear_x4,C_ntk_x4)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	stamp := time.Now().Format("060102")
	if *outDir == "" {
		*outDir = filepath.Join("90-docs", "baien", "context-extend-"+stamp)
	}
	if err := os.MkdirAll(*outDir, 0o755); err != nil {
		return err
	}

	script := filepath.Join("70-tools", "baien-distill", "scripts", "rope_extend_probe.py")
	cmdline := []string{"python", script,
		"--model", *model,
		"--out-dir", *outDir,
	}
	if *only != "" {
		cmdline = append(cmdline, "--only", *only)
	}
	fmt.Printf("[bench rope-extend] %s\n", strings.Join(cmdline, " "))
	c := exec.Command(cmdline[0], cmdline[1:]...)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}

// ----- subcommand: list ---------------------------------------------------

func cmdBenchList(_ []string) error {
	fmt.Println("Supported benches (e7m bench):")
	fmt.Println()
	fmt.Println("  micro                       15 verifiable prompts, rule-based, ~5 min")
	fmt.Println("                              IFEval×5 / MMLU×5 / Reasoning×1 / MLing×2 / Gen×2")
	fmt.Println()
	fmt.Println("  core4 (lm-eval-harness):")
	for _, t := range core4Tasks {
		fmt.Printf("    %-28s ~%3d min   (%s)\n", t.Name, t.EstMin, t.DisplayName)
	}
	fmt.Println()
	fmt.Println("Frontier reference (§A of frontier-bench-snapshot-260523.md):")
	fmt.Println("  IFEval         91.9–94.5 (Opus/K2/GLM/DS/Qwen)")
	fmt.Println("  MMLU-Redux     94.3–95.3")
	fmt.Println("  GPQA Diamond   86.2–92.4")
	fmt.Println("  Global PIQA    89.2–91.4")
	return nil
}

// ----- ssh / scp helpers --------------------------------------------------

func sshRunStream(host, cmd string) error {
	c := exec.Command("ssh", host, cmd)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}

func scpTo(localPath, host, remotePath string) error {
	target := host + ":" + remotePath
	c := exec.Command("scp", "-q", localPath, target)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}

func scpFrom(host, remotePath, localPath string) error {
	src := host + ":" + remotePath
	c := exec.Command("scp", "-q", src, localPath)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}

func scpFromRecursive(host, remotePath, localPath string) error {
	src := host + ":" + remotePath
	c := exec.Command("scp", "-q", "-r", src, localPath)
	c.Stdout = os.Stdout
	c.Stderr = os.Stderr
	return c.Run()
}
