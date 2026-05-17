package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

// runTraining dispatches `gftd training` subcommands.
//
// ADR-2605070700 — RisingWave-native model training + weight lineage.
// Thin wrapper around the BPMN-as-actor XRPC surface
// (`ai.gftd.apps.training.*`) routed via PDS → bpmn-dispatcher
// (ADR-2604282300 K8s-internal routing).
func runTraining(args []string) error {
	if len(args) == 0 {
		return runTrainingHelp(nil)
	}
	switch args[0] {
	case "run":
		return runTrainingRun(args[1:])
	case "promote":
		return runTrainingPromote(args[1:])
	case "eval":
		return runTrainingEval(args[1:])
	case "list-runs":
		return runTrainingListRuns(args[1:])
	case "list-checkpoints":
		return runTrainingListCheckpoints(args[1:])
	case "list-snapshots":
		return runTrainingListSnapshots(args[1:])
	case "serving":
		return runTrainingServing(args[1:])
	case "coverage":
		return runTrainingCoverage(args[1:])
	case "help", "--help", "-h":
		return runTrainingHelp(args[1:])
	default:
		fmt.Fprintf(os.Stderr, "unknown training subcommand: %s\n\n", args[0])
		return runTrainingHelp(nil)
	}
}

func runTrainingHelp(_ []string) error {
	fmt.Print(`gftd training — RisingWave-native model training + weight lineage (ADR-2605070700)

Subcommands:
  run                Start a fine-tune / LoRA / distillation run
  promote            Promote a checkpoint to a serving alias (Murakumo / RunPod / ...)
  eval               Run benches against an existing checkpoint
  list-runs          Recent training runs (filter --kind / --status / --limit)
  list-checkpoints   Checkpoints (filter --run / --only-final / --limit)
  list-snapshots     Dataset snapshots (filter --dataset / --status / --limit)
  serving            Currently-active serving alias → checkpoint promotions
  coverage           Single-shot pipeline summary (counts + bytes + last-* timestamps)

Usage (Go flag convention: flags BEFORE positional args):
  gftd training run --kind sft --base <model> --dataset <name> [flags]
  gftd training promote --alias <alias> [--target <serving>] <checkpointId>
  gftd training eval --bench mmlu,arc_challenge [flags] <checkpointId>
  gftd training list-runs [--kind sft] [--status running] [--limit 20]
  gftd training list-checkpoints [--run <runId>] [--only-final] [--limit 20]
  gftd training list-snapshots [--dataset gftd-corpus] [--limit 20]
  gftd training serving [--alias murakumo:]
  gftd training coverage

Auth:
  Requires GFTD_TOKEN or 'gftd authn signin'.
  For programmatic / Claude-agent use, prefer minting a scoped JWT first:

    AT_TOKEN=$(gftd agent-token --lxm ai.gftd.apps.training.runSft --ttl 60) \
      GFTD_TOKEN=$AT_TOKEN gftd training run --kind sft --base ... --dataset ...

  Per CLAUDE.md / agent-token rule: long-lived tokens are revocable but
  unscoped. agent-token bounds blast radius to one NSID.

Endpoints (route via PDS → bpmn-dispatcher, ADR-2604282300):
  ai.gftd.apps.training.runSft
  ai.gftd.apps.training.runLora
  ai.gftd.apps.training.runDistill
  ai.gftd.apps.training.runEval
  ai.gftd.apps.training.promote

`)
	return nil
}

// ──────────────────────────────────────────────────────────────────────
// gftd training run
// ──────────────────────────────────────────────────────────────────────

func runTrainingRun(args []string) error {
	fs := flag.NewFlagSet("training run", flag.ContinueOnError)
	kind := fs.String("kind", "sft", "Run kind: sft | lora | distill")
	runID := fs.String("run-id", "", "Optional client-supplied run ID; auto-generated if omitted")
	base := fs.String("base", "", "Base model HF ID (e.g. google/gemma-2-2b-it). Required for sft/lora.")
	studentBase := fs.String("student-base", "", "Student base model HF ID. Required for distill.")
	baseRev := fs.String("base-revision", "", "HF revision pin (default: registry default)")
	dataset := fs.String("dataset", "", "Dataset name (resolved against v_training_text). Required.")
	label := fs.String("label", "", "Optional v_training_text.label filter")
	revision := fs.String("revision", "", "Optional dataset revision/content_hash to pin a prior snapshot")
	hyperparams := fs.String("hyperparams", "", "JSON-encoded hyperparams object")
	gpuTarget := fs.String("gpu", "", "GPU pool name (default: mitama-training-pool)")
	seed := fs.Int("seed", 0, "Random seed (0 = unset)")
	evalBenches := fs.String("eval-benches", "internal-loss", "Comma-separated bench names for the final-checkpoint eval")
	rationale := fs.String("rationale", "", "Free-form rationale (audit trail)")
	// distill-specific
	teacherKind := fs.String("teacher-kind", "", "distill only: run | actor | artifact")
	teacherRunID := fs.String("teacher-run-id", "", "distill (teacher-kind=run): teacher runId")
	teacherActor := fs.String("teacher-actor", "", "distill (teacher-kind=actor): teacher actor DID")
	teacherArtifact := fs.String("teacher-artifact", "", "distill (teacher-kind=artifact): existing teacher_label run id")
	distillMethod := fs.String("distill-method", "soft-logits", "distill only: hard-label | soft-logits | feature-match")
	temperature := fs.Float64("temperature", 1.0, "distill only: softmax temperature")

	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}

	kindLower := strings.ToLower(strings.TrimSpace(*kind))
	if kindLower != "sft" && kindLower != "lora" && kindLower != "distill" {
		return fmt.Errorf("--kind must be one of: sft | lora | distill (got %q)", *kind)
	}
	if strings.TrimSpace(*dataset) == "" {
		return fmt.Errorf("--dataset is required")
	}

	var nsid string
	input := map[string]any{}
	if *runID != "" {
		input["runId"] = *runID
	}
	input["datasetName"] = *dataset
	if *label != "" {
		input["datasetLabel"] = *label
	}
	if *revision != "" {
		input["datasetRevision"] = *revision
	}
	if *gpuTarget != "" {
		input["gpuTarget"] = *gpuTarget
	}
	if *seed != 0 {
		input["seed"] = *seed
	}
	if *rationale != "" {
		input["rationale"] = *rationale
	}
	if hp := strings.TrimSpace(*hyperparams); hp != "" {
		var hpObj map[string]any
		if err := json.Unmarshal([]byte(hp), &hpObj); err != nil {
			return fmt.Errorf("--hyperparams is not valid JSON: %w", err)
		}
		input["hyperparams"] = hpObj
	}
	if benches := strings.TrimSpace(*evalBenches); benches != "" {
		input["evalBenches"] = splitCSV(benches)
	}

	switch kindLower {
	case "sft":
		if strings.TrimSpace(*base) == "" {
			return fmt.Errorf("--base is required for kind=sft")
		}
		nsid = "ai.gftd.apps.training.runSft"
		input["baseModel"] = *base
		if *baseRev != "" {
			input["baseModelRevision"] = *baseRev
		}
	case "lora":
		if strings.TrimSpace(*base) == "" {
			return fmt.Errorf("--base is required for kind=lora")
		}
		nsid = "ai.gftd.apps.training.runLora"
		input["baseModel"] = *base
		if *baseRev != "" {
			input["baseModelRevision"] = *baseRev
		}
	case "distill":
		if strings.TrimSpace(*studentBase) == "" {
			return fmt.Errorf("--student-base is required for kind=distill")
		}
		if strings.TrimSpace(*teacherKind) == "" {
			return fmt.Errorf("--teacher-kind is required for kind=distill (run | actor | artifact)")
		}
		nsid = "ai.gftd.apps.training.runDistill"
		input["studentBaseModel"] = *studentBase
		if *baseRev != "" {
			input["studentBaseModelRevision"] = *baseRev
		}
		input["teacherKind"] = strings.ToLower(strings.TrimSpace(*teacherKind))
		if *teacherRunID != "" {
			input["teacherRunId"] = *teacherRunID
		}
		if *teacherActor != "" {
			input["teacherActorDid"] = *teacherActor
		}
		if *teacherArtifact != "" {
			input["teacherArtifactRunId"] = *teacherArtifact
		}
		input["distillMethod"] = *distillMethod
		input["temperature"] = *temperature
	}

	return postTrainingXRPC(*pds, nsid, input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training promote
// ──────────────────────────────────────────────────────────────────────

func runTrainingPromote(args []string) error {
	fs := flag.NewFlagSet("training promote", flag.ContinueOnError)
	alias := fs.String("alias", "", "Serving alias to promote to (e.g. murakumo:gemma4-e4b-it@20260507). Required.")
	target := fs.String("target", "", "Serving target hint (e.g. murakumo / runpod / vultr-gpu)")
	by := fs.String("by", "", "Promoting actor DID (default: caller)")
	rationale := fs.String("rationale", "", "Free-form rationale (audit trail)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() < 1 {
		return fmt.Errorf("checkpointId is required as a positional argument")
	}
	checkpointID := fs.Arg(0)
	if strings.TrimSpace(*alias) == "" {
		return fmt.Errorf("--alias is required")
	}

	input := map[string]any{
		"checkpointId": checkpointID,
		"alias":        *alias,
	}
	if *target != "" {
		input["servingTarget"] = *target
	}
	if *by != "" {
		input["promotedBy"] = *by
	}
	if *rationale != "" {
		input["rationale"] = *rationale
	}

	return postTrainingXRPC(*pds, "ai.gftd.apps.training.promote", input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training eval
// ──────────────────────────────────────────────────────────────────────

func runTrainingEval(args []string) error {
	fs := flag.NewFlagSet("training eval", flag.ContinueOnError)
	bench := fs.String("bench", "internal-loss", "Comma-separated bench names (e.g. mmlu,arc_challenge)")
	evalDataset := fs.String("eval-dataset", "", "Optional eval-only dataset snapshot name")
	evalRev := fs.String("eval-revision", "", "Optional eval dataset revision")
	limit := fs.Int("limit", 0, "Cap samples per bench (0 = unbounded)")
	gpuTarget := fs.String("gpu", "", "GPU pool name")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if fs.NArg() < 1 {
		return fmt.Errorf("checkpointId is required as a positional argument")
	}
	checkpointID := fs.Arg(0)

	benches := splitCSV(*bench)
	if len(benches) == 0 {
		return fmt.Errorf("--bench must list at least one bench name")
	}

	input := map[string]any{
		"checkpointId": checkpointID,
		"benches":      benches,
	}
	if *evalDataset != "" {
		input["evalDatasetName"] = *evalDataset
	}
	if *evalRev != "" {
		input["evalDatasetRevision"] = *evalRev
	}
	if *limit > 0 {
		input["sampleLimit"] = *limit
	}
	if *gpuTarget != "" {
		input["gpuTarget"] = *gpuTarget
	}

	return postTrainingXRPC(*pds, "ai.gftd.apps.training.runEval", input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training list-runs
// ──────────────────────────────────────────────────────────────────────

func runTrainingListRuns(args []string) error {
	fs := flag.NewFlagSet("training list-runs", flag.ContinueOnError)
	kind := fs.String("kind", "", "Filter by run kind: sft | lora | distill | dpo | pretrain")
	status := fs.String("status", "", "Filter by status: queued | running | done | failed")
	limit := fs.Int("limit", 50, "Max rows (1-500)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	input := map[string]any{"limit": *limit}
	if *kind != "" {
		input["kind"] = *kind
	}
	if *status != "" {
		input["status"] = *status
	}
	return postTrainingXRPC(*pds, "ai.gftd.apps.training.listRuns", input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training list-checkpoints
// ──────────────────────────────────────────────────────────────────────

func runTrainingListCheckpoints(args []string) error {
	fs := flag.NewFlagSet("training list-checkpoints", flag.ContinueOnError)
	run := fs.String("run", "", "Filter to one runId")
	onlyFinal := fs.Bool("only-final", false, "Return only is_final=true checkpoints")
	limit := fs.Int("limit", 50, "Max rows (1-500)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	input := map[string]any{"limit": *limit, "onlyFinal": *onlyFinal}
	if *run != "" {
		input["runId"] = *run
	}
	return postTrainingXRPC(*pds, "ai.gftd.apps.training.listCheckpoints", input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training list-snapshots
// ──────────────────────────────────────────────────────────────────────

func runTrainingListSnapshots(args []string) error {
	fs := flag.NewFlagSet("training list-snapshots", flag.ContinueOnError)
	dataset := fs.String("dataset", "", "Filter to one datasetName (e.g. gftd-corpus)")
	status := fs.String("status", "", "Filter by status: frozen | deprecated")
	limit := fs.Int("limit", 50, "Max rows (1-500)")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	input := map[string]any{"limit": *limit}
	if *dataset != "" {
		input["datasetName"] = *dataset
	}
	if *status != "" {
		input["status"] = *status
	}
	return postTrainingXRPC(*pds, "ai.gftd.apps.training.listSnapshots", input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training coverage
// ──────────────────────────────────────────────────────────────────────

func runTrainingCoverage(args []string) error {
	fs := flag.NewFlagSet("training coverage", flag.ContinueOnError)
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	return postTrainingXRPC(*pds, "ai.gftd.apps.training.coverage", map[string]any{}, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// gftd training serving
// ──────────────────────────────────────────────────────────────────────

func runTrainingServing(args []string) error {
	fs := flag.NewFlagSet("training serving", flag.ContinueOnError)
	alias := fs.String("alias", "", "Filter to alias substring")
	pds := fs.String("pds", resolvePDSBaseURL(), "PDS base URL")
	jsonOut := fs.Bool("json", false, "Emit raw JSON response")
	verbose := fs.Bool("v", false, "Print target URL + HTTP status to stderr")
	if err := fs.Parse(args); err != nil {
		return err
	}
	input := map[string]any{}
	if *alias != "" {
		input["alias"] = *alias
	}
	return postTrainingXRPC(*pds, "ai.gftd.apps.training.serving", input, *jsonOut, *verbose)
}

// ──────────────────────────────────────────────────────────────────────
// shared HTTP helper
// ──────────────────────────────────────────────────────────────────────

func postTrainingXRPC(pdsURL, nsid string, input map[string]any, jsonOut, verbose bool) error {
	token := resolveGFTDToken()
	if token == "" {
		return fmt.Errorf("no GFTD token found — run `gftd authn signin` or set GFTD_TOKEN")
	}
	pdsURL = strings.TrimRight(strings.TrimSpace(pdsURL), "/")
	if pdsURL == "" {
		pdsURL = "https://atproto.etzhayyim.com"
	}
	target := pdsURL + "/xrpc/" + nsid

	body, err := json.Marshal(input)
	if err != nil {
		return fmt.Errorf("marshal input: %w", err)
	}
	req, err := http.NewRequest("POST", target, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("build request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)

	if verbose {
		fmt.Fprintf(os.Stderr, "POST %s\n", target)
	}
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return fmt.Errorf("http: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if verbose {
		fmt.Fprintf(os.Stderr, "← %d %s\n", resp.StatusCode, http.StatusText(resp.StatusCode))
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("%s failed: %d %s: %s", nsid, resp.StatusCode, http.StatusText(resp.StatusCode), string(respBody))
	}

	if jsonOut {
		fmt.Println(string(respBody))
		return nil
	}

	// Pretty-print common fields.
	var out map[string]any
	if err := json.Unmarshal(respBody, &out); err != nil {
		fmt.Println(string(respBody))
		return nil
	}
	prettyPrintTrainingResponse(nsid, out)
	return nil
}

func prettyPrintTrainingResponse(nsid string, out map[string]any) {
	fmt.Printf("%s\n", nsid)
	// List endpoints — render as table.
	for _, listKey := range []string{"runs", "checkpoints", "snapshots", "serving"} {
		if rows, ok := out[listKey].([]any); ok {
			fmt.Printf("  count: %v\n", out["count"])
			for i, row := range rows {
				if m, ok := row.(map[string]any); ok {
					fmt.Printf("  [%d]\n", i)
					for _, k := range []string{"runId", "kind", "baseModel", "status",
						"checkpointId", "step", "isFinal", "weightB2Uri",
						"snapshotId", "datasetName", "label", "rowCount", "shardCount",
						"alias", "checkpointVertexId", "servingTarget", "promotedAt",
						"startedAt", "endedAt", "completedSteps", "weightByteSize"} {
						if v, ok := m[k]; ok && v != nil && v != "" && v != 0 && v != false {
							fmt.Printf("      %-22s %v\n", k+":", v)
						}
					}
				}
			}
			return
		}
	}
	// Procedure / coverage endpoints — flat fields.
	for _, k := range []string{"ok", "asOf",
		"runId", "runVertexId", "datasetSnapshotId",
		"finalCheckpointId", "finalCheckpointVertexId", "evalSummary",
		"alias", "checkpointId", "newEdgeId", "retiredEdgeId", "weightB2Uri",
		"evalCount", "primaryScores", "distilledFromEdgeId", "adapterRank",
		"teacherLabelArtifactRunId",
		"snapshotsCount", "datasetSnapshotRows",
		"runsTotal", "runsQueued", "runsRunning", "runsDone", "runsFailed",
		"checkpointsTotal", "checkpointsFinal", "checkpointBytesTotal",
		"evalsTotal", "servingActiveCount",
		"lastRunStartedAt", "lastCheckpointAt", "lastPromotedAt",
		"error"} {
		if v, ok := out[k]; ok {
			fmt.Printf("  %-26s %v\n", k+":", v)
		}
	}
}

func splitCSV(s string) []string {
	parts := strings.Split(s, ",")
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		p = strings.TrimSpace(p)
		if p != "" {
			out = append(out, p)
		}
	}
	return out
}
