// gftd murakumo models — declarative model placement across the murakumo
// mac mini fleet. SSoT = 60-apps/ai-gftd-project-murakumo/fleet-models.json.
//
//	gftd murakumo models declare           # print declared placement
//	gftd murakumo models list              # diff declared vs actual on each mini
//	gftd murakumo models apply [--dry-run] # reconcile actual → declared
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"sync"
	"time"
)

const fleetModelsPath = "60-apps/ai-gftd-project-murakumo/fleet-models.json"

type modelComponent struct {
	File   string `json:"file"`
	Path   string `json:"path"`
	HFRepo string `json:"hf_repo"`
	HFFile string `json:"hf_file"`
}

type modelDecl struct {
	Kind          string           `json:"kind"`
	OllamaTag     string           `json:"ollama_tag,omitempty"`
	Filename      string           `json:"filename,omitempty"`
	Path          string           `json:"path,omitempty"`
	HFRepo        string           `json:"hf_repo,omitempty"`
	HFFile        string           `json:"hf_file,omitempty"`
	DiffusersRepo string           `json:"diffusers_repo,omitempty"`
	Components    []modelComponent `json:"components,omitempty"`
	SizeGB        float64          `json:"size_gb"`
	Purpose       string           `json:"purpose,omitempty"`
	TargetMinis   []string         `json:"target_minis"`
}

type fleetModelsDecl struct {
	Fleet  []string             `json:"fleet"`
	Models map[string]modelDecl `json:"models"`
}

func loadFleetModels() (*fleetModelsDecl, error) {
	root, err := findGitRoot(".")
	if err != nil {
		return nil, fmt.Errorf("find repo root: %w", err)
	}
	path := filepath.Join(root, fleetModelsPath)
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read %s: %w", path, err)
	}
	var d fleetModelsDecl
	if err := json.Unmarshal(b, &d); err != nil {
		return nil, fmt.Errorf("parse %s: %w", path, err)
	}
	return &d, nil
}

func runMurakumoModels(args []string) error {
	if len(args) == 0 {
		fmt.Println(`gftd murakumo models — declarative fleet model placement

USAGE:
  gftd murakumo models declare [--json]      # print declared placement
  gftd murakumo models list [--json]          # actual vs declared per mini
  gftd murakumo models apply [--dry-run]      # reconcile (HF_TOKEN env required)
                       [--target <name,...>]  # only these models
                       [--only-mini <h,...>]  # only these minis
`)
		return nil
	}
	switch args[0] {
	case "declare":
		return runMurakumoModelsDeclare(args[1:])
	case "list":
		return runMurakumoModelsList(args[1:])
	case "apply":
		return runMurakumoModelsApply(args[1:])
	case "help", "--help", "-h":
		return runMurakumoModels(nil)
	default:
		return fmt.Errorf("unknown subcommand: %s", args[0])
	}
}

// ── declare ────────────────────────────────────────────────────────────────

func runMurakumoModelsDeclare(args []string) error {
	fs := flag.NewFlagSet("declare", flag.ContinueOnError)
	asJSON := fs.Bool("json", false, "emit JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	d, err := loadFleetModels()
	if err != nil {
		return err
	}
	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(d)
	}
	fmt.Printf("Fleet: %s\n\n", strings.Join(d.Fleet, ", "))
	for _, name := range sortedModelNames(d) {
		m := d.Models[name]
		fmt.Printf("  %-22s [%s]  %.1f GB\n", name, m.Kind, m.SizeGB)
		if m.Purpose != "" {
			fmt.Printf("    %s\n", m.Purpose)
		}
		fmt.Printf("    target: %s (%d/%d minis)\n", strings.Join(m.TargetMinis, ", "), len(m.TargetMinis), len(d.Fleet))
		switch m.Kind {
		case "ollama":
			fmt.Printf("    ollama_tag: %s\n", m.OllamaTag)
		case "comfyui_checkpoint":
			fmt.Printf("    hf: %s/%s → %s/%s\n", m.HFRepo, m.HFFile, m.Path, m.Filename)
		case "comfyui_diffusers":
			fmt.Printf("    diffusers_repo: %s (HF cache via DiffusersLoader)\n", m.DiffusersRepo)
		case "comfyui_wan":
			for _, c := range m.Components {
				fmt.Printf("    component: %s/%s ← %s/%s\n", c.Path, c.File, c.HFRepo, c.HFFile)
			}
		}
		fmt.Println()
	}
	return nil
}

// ── list (probe actual state) ──────────────────────────────────────────────

type miniStatus struct {
	Mini   string
	Models map[string]bool // true = present
	Err    string
}

func runMurakumoModelsList(args []string) error {
	fs := flag.NewFlagSet("list", flag.ContinueOnError)
	asJSON := fs.Bool("json", false, "emit JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}
	d, err := loadFleetModels()
	if err != nil {
		return err
	}
	statuses := probeFleet(d)

	if *asJSON {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(map[string]any{"fleet": d.Fleet, "statuses": statuses})
	}

	modelNames := sortedModelNames(d)
	header := fmt.Sprintf("%-12s", "mini")
	for _, n := range modelNames {
		header += fmt.Sprintf(" %-22s", n)
	}
	fmt.Println(header)
	fmt.Println(strings.Repeat("─", len(header)))

	for _, mini := range d.Fleet {
		var st *miniStatus
		for i := range statuses {
			if statuses[i].Mini == mini {
				st = &statuses[i]
				break
			}
		}
		row := fmt.Sprintf("%-12s", mini)
		for _, name := range modelNames {
			decl := d.Models[name]
			declared := contains(decl.TargetMinis, mini)
			actual := st != nil && st.Models[name]
			row += " " + statusCell(declared, actual)
		}
		fmt.Println(row)
	}
	fmt.Println()
	fmt.Println("legend:  ✓ ok   ✗ declared but missing   ~ present but not declared   - n/a")
	return nil
}

func statusCell(declared, actual bool) string {
	cell := func(s string) string { return fmt.Sprintf("%-22s", s) }
	switch {
	case declared && actual:
		return cell("✓ deployed")
	case declared && !actual:
		return cell("✗ MISSING")
	case !declared && actual:
		return cell("~ orphan")
	default:
		return cell("-")
	}
}

func probeFleet(d *fleetModelsDecl) []miniStatus {
	out := make([]miniStatus, len(d.Fleet))
	var wg sync.WaitGroup
	for i, mini := range d.Fleet {
		wg.Add(1)
		go func(i int, mini string) {
			defer wg.Done()
			st := miniStatus{Mini: mini, Models: map[string]bool{}}
			for name, m := range d.Models {
				st.Models[name] = probeModelOnMini(mini, m)
			}
			out[i] = st
		}(i, mini)
	}
	wg.Wait()
	return out
}

func probeModelOnMini(mini string, m modelDecl) bool {
	var probe string
	switch m.Kind {
	case "ollama":
		probe = fmt.Sprintf(`curl -fsS --max-time 3 http://localhost:11434/api/tags 2>/dev/null | grep -q '"name":"%s"'`, m.OllamaTag)
	case "comfyui_checkpoint":
		probe = fmt.Sprintf(`test -s ~/comfyui/%s/%s`, m.Path, m.Filename)
	case "comfyui_diffusers":
		cache := strings.ReplaceAll(m.DiffusersRepo, "/", "--")
		probe = fmt.Sprintf(`test -d ~/.cache/huggingface/hub/models--%s/snapshots`, cache)
	case "comfyui_wan":
		var parts []string
		for _, c := range m.Components {
			parts = append(parts, fmt.Sprintf("test -s ~/comfyui/%s/%s", c.Path, c.File))
		}
		probe = strings.Join(parts, " && ")
	default:
		return false
	}
	out, err := sshOnMini(mini, probe, 6*time.Second)
	if err != nil {
		_ = out
		return false
	}
	return true
}

// ── apply ─────────────────────────────────────────────────────────────────

func runMurakumoModelsApply(args []string) error {
	fs := flag.NewFlagSet("apply", flag.ContinueOnError)
	dryRun := fs.Bool("dry-run", false, "show what would be deployed")
	targetFlag := fs.String("target", "", "comma-separated model names (default: all)")
	miniFlag := fs.String("only-mini", "", "comma-separated mini names (default: all)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	d, err := loadFleetModels()
	if err != nil {
		return err
	}
	hfToken := os.Getenv("HF_TOKEN")
	if hfToken == "" {
		hfToken = os.Getenv("HUGGING_FACE_HUB_TOKEN")
	}

	wantModels := map[string]bool{}
	if *targetFlag == "" {
		for k := range d.Models {
			wantModels[k] = true
		}
	} else {
		for _, k := range strings.Split(*targetFlag, ",") {
			wantModels[strings.TrimSpace(k)] = true
		}
	}
	wantMinis := map[string]bool{}
	if *miniFlag == "" {
		for _, m := range d.Fleet {
			wantMinis[m] = true
		}
	} else {
		for _, m := range strings.Split(*miniFlag, ",") {
			wantMinis[strings.TrimSpace(m)] = true
		}
	}

	statuses := probeFleet(d)
	statusByMini := map[string]*miniStatus{}
	for i := range statuses {
		statusByMini[statuses[i].Mini] = &statuses[i]
	}

	// Build action plan
	var actions []deployAction
	for _, mini := range d.Fleet {
		if !wantMinis[mini] {
			continue
		}
		for _, name := range sortedModelNames(d) {
			if !wantModels[name] {
				continue
			}
			m := d.Models[name]
			if !contains(m.TargetMinis, mini) {
				continue
			}
			if st := statusByMini[mini]; st != nil && st.Models[name] {
				continue
			}
			actions = append(actions, deployAction{Mini: mini, Model: name, Decl: m})
		}
	}

	if len(actions) == 0 {
		fmt.Println("Nothing to do — fleet matches declaration.")
		return nil
	}

	fmt.Printf("Plan: %d deploy actions\n", len(actions))
	for _, a := range actions {
		fmt.Printf("  + %s ← %s [%s]\n", a.Mini, a.Model, a.Decl.Kind)
	}
	if *dryRun {
		fmt.Println("\n(dry-run, no changes applied)")
		return nil
	}
	if (needsHF(actions)) && hfToken == "" {
		return fmt.Errorf("HF_TOKEN env not set — required for HF downloads")
	}

	// Execute actions in parallel per-mini (serial per mini to avoid disk thrash)
	byMini := map[string][]deployAction{}
	for _, a := range actions {
		byMini[a.Mini] = append(byMini[a.Mini], a)
	}
	var wg sync.WaitGroup
	type result struct {
		Mini  string
		Model string
		OK    bool
		Msg   string
	}
	resCh := make(chan result, len(actions))
	for mini, acts := range byMini {
		wg.Add(1)
		go func(mini string, acts []deployAction) {
			defer wg.Done()
			for _, a := range acts {
				msg, err := deployOnMini(mini, a.Decl, hfToken)
				if err != nil {
					resCh <- result{Mini: mini, Model: a.Model, OK: false, Msg: err.Error()}
					return // stop this mini's queue on first failure
				}
				resCh <- result{Mini: mini, Model: a.Model, OK: true, Msg: msg}
			}
		}(mini, acts)
	}
	wg.Wait()
	close(resCh)

	ok, fail := 0, 0
	for r := range resCh {
		mark := "✓"
		if !r.OK {
			mark = "✗"
			fail++
		} else {
			ok++
		}
		fmt.Printf("  %s %-12s %-22s  %s\n", mark, r.Mini, r.Model, r.Msg)
	}
	fmt.Printf("\nApply done: %d ok, %d fail\n", ok, fail)
	if fail > 0 {
		return fmt.Errorf("%d failures", fail)
	}
	return nil
}

type deployAction struct {
	Mini  string
	Model string
	Decl  modelDecl
}

func needsHF(actions []deployAction) bool {
	for _, a := range actions {
		switch a.Decl.Kind {
		case "comfyui_checkpoint", "comfyui_diffusers", "comfyui_wan":
			return true
		}
	}
	return false
}

func deployOnMini(mini string, m modelDecl, hfToken string) (string, error) {
	switch m.Kind {
	case "ollama":
		// ensure ollama serve is running (use abs path — non-interactive SSH PATH is minimal),
		// then `ollama pull <tag>`. detach with disown so daemon survives SSH disconnect.
		cmd := fmt.Sprintf(`OLLAMA=/opt/homebrew/opt/ollama/bin/ollama; pgrep -f "ollama serve" >/dev/null || { OLLAMA_HOST=0.0.0.0:11434 OLLAMA_CONTEXT_LENGTH=16384 nohup $OLLAMA serve > /tmp/ollama.log 2>&1 & disown; sleep 3; }; $OLLAMA pull %s 2>&1 | tail -1`, m.OllamaTag)
		out, err := sshOnMini(mini, cmd, 10*time.Minute)
		if err != nil {
			return "", fmt.Errorf("ollama pull: %s", strings.TrimSpace(out))
		}
		return "pulled " + m.OllamaTag, nil
	case "comfyui_checkpoint":
		url := fmt.Sprintf("https://huggingface.co/%s/resolve/main/%s", m.HFRepo, m.HFFile)
		cmd := fmt.Sprintf(`set -e; mkdir -p ~/comfyui/%s; cd ~/comfyui/%s; if [ -s '%s' ]; then echo "already present"; else curl -sL --fail -H 'Authorization: Bearer %s' -o '%s' '%s' && ls -lh '%s' | awk '{print $5}'; fi`,
			m.Path, m.Path, m.Filename, hfToken, m.Filename, url, m.Filename)
		out, err := sshOnMini(mini, cmd, 20*time.Minute)
		if err != nil {
			return "", fmt.Errorf("download: %s", strings.TrimSpace(out))
		}
		return "size=" + strings.TrimSpace(out), nil
	case "comfyui_diffusers":
		// Use huggingface-cli (in murakumo-venv) to populate HF hub cache
		cmd := fmt.Sprintf(`set -e; export HF_TOKEN='%s'; ~/.local/share/murakumo-venv/bin/python3 -c "from huggingface_hub import snapshot_download; snapshot_download('%s', allow_patterns=['*.json','*.txt','*.safetensors','*.bin','*.fp16.safetensors'])" 2>&1 | tail -3`,
			hfToken, m.DiffusersRepo)
		out, err := sshOnMini(mini, cmd, 30*time.Minute)
		if err != nil {
			return "", fmt.Errorf("diffusers fetch: %s", strings.TrimSpace(out))
		}
		return "diffusers cache OK", nil
	case "comfyui_wan":
		for _, c := range m.Components {
			url := fmt.Sprintf("https://huggingface.co/%s/resolve/main/%s", c.HFRepo, c.HFFile)
			cmd := fmt.Sprintf(`set -e; mkdir -p ~/comfyui/%s; cd ~/comfyui/%s; if [ -s '%s' ]; then exit 0; fi; curl -sL --fail -H 'Authorization: Bearer %s' -o '%s' '%s' && ls -lh '%s' | awk '{print $5}'`,
				c.Path, c.Path, c.File, hfToken, c.File, url, c.File)
			out, err := sshOnMini(mini, cmd, 30*time.Minute)
			if err != nil {
				return "", fmt.Errorf("wan component %s: %s", c.File, strings.TrimSpace(out))
			}
			_ = out
		}
		return "wan stack OK", nil
	}
	return "", fmt.Errorf("unsupported kind: %s", m.Kind)
}

// ── SSH helper ─────────────────────────────────────────────────────────────

func sshOnMini(mini, cmd string, timeout time.Duration) (string, error) {
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	target := fmt.Sprintf("%s@%s.murakumo.lan", mini, mini)
	args := []string{
		"-o", "BatchMode=yes",
		"-o", "ConnectTimeout=5",
		"-o", "StrictHostKeyChecking=no",
		target, cmd,
	}
	out, err := exec.CommandContext(ctx, "ssh", args...).CombinedOutput()
	return string(out), err
}

// ── small utils ────────────────────────────────────────────────────────────

func sortedModelNames(d *fleetModelsDecl) []string {
	names := make([]string, 0, len(d.Models))
	for k := range d.Models {
		names = append(names, k)
	}
	sort.Strings(names)
	return names
}

func contains(ss []string, s string) bool {
	for _, x := range ss {
		if x == s {
			return true
		}
	}
	return false
}
