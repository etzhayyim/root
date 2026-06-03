package main

// `e7m actor` — declarative actor deploy from actor.toml.
//
// Per ADR-2605232000 (agent-led autonomous deploy).
//
// Each etzhayyim actor that wants to be deployable via `e7m actor deploy`
// MUST include a top-level actor.toml in its `20-actors/<name>/` directory
// describing its deployment topology (DID Workers, k8s Pods, CF Pages, etc).
// `e7m actor deploy` resolves the manifest, runs preflight checks, and
// invokes the per-stage executor (wrangler / kubectl / docker / cloudflared)
// in the order declared. Each invocation is non-interactive and can be
// constrained by a capability JWT (--capability <path>).

import (
	"bytes"
	"crypto/ed25519"
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

// actorTOML describes an actor's deployment topology in a declarative form.
// One file per actor at `20-actors/<name>/actor.toml`. Hand-edited; not generated.
type actorTOML struct {
	Actor struct {
		Name      string `toml:"name"`
		Did       string `toml:"did"`
		Nanoid    string `toml:"nanoid"`
		Manifest  string `toml:"manifest"`
		PrimaryAdr string `toml:"primary_adr"`
	} `toml:"actor"`
	Stages []actorStage `toml:"stages"`
}

type actorStage struct {
	Name        string            `toml:"name"`        // e.g. "did-worker", "k8s-pod", "pages-deploy", "smoke"
	Description string            `toml:"description"`
	Type        string            `toml:"type"`        // cf-worker / cf-pages / k8s / docker-build / cf-tunnel / cmd / smoke
	WorkingDir  string            `toml:"working_dir"` // relative to repo root
	Command     []string          `toml:"command"`     // exec.Command args; honors $VAR expansion
	Env         map[string]string `toml:"env"`         // env vars set when invoking command
	DependsOn   []string          `toml:"depends_on"`  // other stage names that must complete first
	RequireCap  []string          `toml:"require_cap"` // capability NSIDs needed (deploy.cfWorker / deploy.k8s / …)
	OnError     string            `toml:"on_error"`    // continue / abort (default: abort)
	DryRunSafe  bool              `toml:"dry_run_safe"` // true if Command has no side effects
}

func runActor(args []string) error {
	if len(args) == 0 {
		printActorUsage()
		return nil
	}
	switch args[0] {
	case "deploy":
		return runActorDeploy(args[1:])
	case "list":
		return runActorList(args[1:])
	case "show":
		return runActorShow(args[1:])
	case "help", "--help", "-h":
		printActorUsage()
		return nil
	default:
		return fmt.Errorf("unknown actor subcommand: %s", args[0])
	}
}

func printActorUsage() {
	fmt.Printf(`etzhayyim actor — declarative actor deploy (per ADR-2605232000)

USAGE:
  etzhayyim actor <subcommand> [flags]

SUBCOMMANDS:
  deploy   Deploy an actor by reading 20-actors/<name>/actor.toml
  list     List all actors that have an actor.toml
  show     Print resolved deployment plan for an actor

DEPLOY FLAGS:
  --actor <name>           actor name (default: inferred from cwd)
  --only <stage>           run only the named stage
  --skip <stage>           skip the named stage (repeatable)
  --capability <path>      path to a capability JWS (gates which stages can run)
  --agent-token <token>    short-lived scoped JWT (mint with 'etzhayyim agent-token')
  --dry-run                print actions without executing
  --non-interactive        fail (not prompt) on missing creds or confirmations
  --commit-sha <sha>       git commit to record in the audit event (default: HEAD)

EXAMPLES:
  # Human-driven full deploy
  etzhayyim actor deploy --actor karute

  # Agent-driven, capability-gated, single stage
  TOKEN=$(etzhayyim agent-token --lxm deploy.cfWorker:karute-did-web --ttl 60 \
                            --capability ~/.etzhayyim/cap-karute-deploy.jws)
  etzhayyim actor deploy --actor karute --only did-worker --agent-token "$TOKEN" --non-interactive

  # Dry-run (no side effects)
  etzhayyim actor deploy --actor karute --dry-run
`)
}

func runActorDeploy(args []string) error {
	fs := flag.NewFlagSet("actor deploy", flag.ContinueOnError)
	actorName := fs.String("actor", "", "actor name (default: inferred from cwd)")
	only := fs.String("only", "", "run only the named stage")
	var skipStages stringSliceFlag
	fs.Var(&skipStages, "skip", "skip the named stage (repeatable)")
	capabilityPath := fs.String("capability", "", "path to a capability JWS")
	agentToken := fs.String("agent-token", "", "short-lived scoped JWT")
	dryRun := fs.Bool("dry-run", false, "print actions without executing")
	nonInteractive := fs.Bool("non-interactive", false, "fail on missing creds")
	commitSha := fs.String("commit-sha", "", "git commit recorded in audit event (default: HEAD)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printActorUsage()
			return nil
		}
		return err
	}

	repoRoot, err := findRepoRoot()
	if err != nil {
		return err
	}

	name, err := resolveActorName(repoRoot, *actorName)
	if err != nil {
		return err
	}

	tomlPath := filepath.Join(repoRoot, "20-actors", name, "actor.toml")
	manifest, err := loadActorTOML(tomlPath)
	if err != nil {
		return fmt.Errorf("read %s: %w", tomlPath, err)
	}

	if *commitSha == "" {
		out, _ := exec.Command("git", "-C", repoRoot, "rev-parse", "--short", "HEAD").Output()
		*commitSha = strings.TrimSpace(string(out))
	}

	// Capability verification (lightweight in v1; full Ed25519 verification in
	// a follow-up). For now we only assert the file exists when --capability
	// is passed and surface the agent-token in the env for downstream tools.
	cap, err := loadCapability(*capabilityPath)
	if err != nil && *capabilityPath != "" {
		return fmt.Errorf("capability: %w", err)
	}

	// Stage filtering
	stages := manifest.Stages
	if *only != "" {
		stages = filterStagesByName(stages, *only)
		if len(stages) == 0 {
			return fmt.Errorf("--only: no stage named %q in actor.toml", *only)
		}
	}
	stages = removeStages(stages, skipStages)

	// Preflight
	if err := preflight(stages, *nonInteractive); err != nil {
		return err
	}

	for _, st := range stages {
		// Capability gate
		if err := stageGate(&st, cap, *agentToken); err != nil {
			emitDeployEvent(manifest, &st, *commitSha, "denied", err.Error(), 0)
			if st.OnError == "continue" {
				fmt.Fprintf(os.Stderr, "etzhayyim actor: stage %q gated, continuing: %v\n", st.Name, err)
				continue
			}
			return fmt.Errorf("stage %q: %w", st.Name, err)
		}

		started := time.Now()
		fmt.Printf("━━ %s ━━ %s\n", st.Name, st.Description)

		if *dryRun {
			fmt.Printf("  [dry-run] would run: %s\n", strings.Join(st.Command, " "))
			emitDeployEvent(manifest, &st, *commitSha, "dry-run", "", 0)
			continue
		}

		err := executeStage(repoRoot, &st, *agentToken)
		dur := time.Since(started).Milliseconds()
		if err != nil {
			emitDeployEvent(manifest, &st, *commitSha, "error", err.Error(), dur)
			if st.OnError == "continue" {
				fmt.Fprintf(os.Stderr, "etzhayyim actor: stage %q failed, continuing: %v\n", st.Name, err)
				continue
			}
			return fmt.Errorf("stage %q failed: %w", st.Name, err)
		}
		emitDeployEvent(manifest, &st, *commitSha, "ok", "", dur)
		fmt.Printf("  ✓ %s (%dms)\n", st.Name, dur)
	}

	fmt.Println("✓ actor deploy complete")
	return nil
}

func runActorList(_ []string) error {
	repoRoot, err := findRepoRoot()
	if err != nil {
		return err
	}
	actorsDir := filepath.Join(repoRoot, "20-actors")
	entries, err := os.ReadDir(actorsDir)
	if err != nil {
		return err
	}
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		tomlPath := filepath.Join(actorsDir, e.Name(), "actor.toml")
		if _, err := os.Stat(tomlPath); err == nil {
			fmt.Println(e.Name())
		}
	}
	return nil
}

func runActorShow(args []string) error {
	fs := flag.NewFlagSet("actor show", flag.ContinueOnError)
	actorName := fs.String("actor", "", "actor name")
	if err := fs.Parse(args); err != nil {
		return err
	}
	repoRoot, err := findRepoRoot()
	if err != nil {
		return err
	}
	name, err := resolveActorName(repoRoot, *actorName)
	if err != nil {
		return err
	}
	manifest, err := loadActorTOML(filepath.Join(repoRoot, "20-actors", name, "actor.toml"))
	if err != nil {
		return err
	}
	b, _ := json.MarshalIndent(manifest, "", "  ")
	fmt.Println(string(b))
	return nil
}

// ── helpers ───────────────────────────────────────────────────────────

type stringSliceFlag []string

func (s *stringSliceFlag) String() string         { return strings.Join(*s, ",") }
func (s *stringSliceFlag) Set(value string) error { *s = append(*s, value); return nil }

func findRepoRoot() (string, error) {
	out, err := exec.Command("git", "rev-parse", "--show-toplevel").Output()
	if err != nil {
		// Fallback: walk up from cwd looking for deps.toml
		cwd, _ := os.Getwd()
		for d := cwd; d != "/"; d = filepath.Dir(d) {
			if _, err := os.Stat(filepath.Join(d, "deps.toml")); err == nil {
				return d, nil
			}
		}
		return "", fmt.Errorf("could not find repo root (not a git repo + no deps.toml ancestor)")
	}
	return strings.TrimSpace(string(out)), nil
}

func resolveActorName(repoRoot, given string) (string, error) {
	if given != "" {
		return given, nil
	}
	cwd, _ := os.Getwd()
	rel, err := filepath.Rel(repoRoot, cwd)
	if err != nil {
		return "", err
	}
	parts := strings.Split(rel, string(os.PathSeparator))
	if len(parts) >= 2 && parts[0] == "20-actors" {
		return parts[1], nil
	}
	return "", fmt.Errorf("--actor <name> required (cwd is not under 20-actors/<name>/)")
}

func loadActorTOML(path string) (*actorTOML, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	manifest, err := parseActorTOML(data)
	if err != nil {
		return nil, err
	}
	if manifest.Actor.Name == "" {
		return nil, fmt.Errorf("%s: [actor] name is required", path)
	}
	return manifest, nil
}

// parseActorTOML is a minimal TOML reader sufficient for actor.toml.
// We avoid adding a 3rd-party TOML dep to keep e7m self-contained;
// the schema is small and stable.
//
// Supports:
//
//	[actor]
//	name = "karute"
//	[[stages]]
//	name = "did-worker"
//	command = ["wrangler", "deploy"]
//	[stages.env]
//	FOO = "bar"
//
// Limitations: no nested tables beyond [stages.env]; no array-of-table
// nesting; expects exactly one [actor] block and one or more [[stages]].
func parseActorTOML(data []byte) (*actorTOML, error) {
	manifest := &actorTOML{}
	lines := strings.Split(string(data), "\n")
	mode := "" // "", "actor", "stage", "stage.env"
	var curStage *actorStage
	for ln, raw := range lines {
		line := strings.TrimSpace(raw)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		// Section header
		if strings.HasPrefix(line, "[") {
			line = strings.TrimSpace(line)
			switch {
			case line == "[actor]":
				mode = "actor"
			case line == "[[stages]]":
				if curStage != nil {
					manifest.Stages = append(manifest.Stages, *curStage)
				}
				curStage = &actorStage{Env: map[string]string{}}
				mode = "stage"
			case line == "[stages.env]":
				mode = "stage.env"
			default:
				return nil, fmt.Errorf("line %d: unsupported section header %q", ln+1, line)
			}
			continue
		}
		// key = value
		eq := strings.Index(line, "=")
		if eq < 0 {
			return nil, fmt.Errorf("line %d: not key=value: %q", ln+1, line)
		}
		key := strings.TrimSpace(line[:eq])
		val := strings.TrimSpace(line[eq+1:])
		switch mode {
		case "actor":
			s, err := tomlString(val)
			if err != nil {
				return nil, fmt.Errorf("line %d: %w", ln+1, err)
			}
			switch key {
			case "name":
				manifest.Actor.Name = s
			case "did":
				manifest.Actor.Did = s
			case "nanoid":
				manifest.Actor.Nanoid = s
			case "manifest":
				manifest.Actor.Manifest = s
			case "primary_adr":
				manifest.Actor.PrimaryAdr = s
			}
		case "stage":
			if curStage == nil {
				return nil, fmt.Errorf("line %d: stage key %q before [[stages]]", ln+1, key)
			}
			switch key {
			case "name":
				s, _ := tomlString(val)
				curStage.Name = s
			case "description":
				s, _ := tomlString(val)
				curStage.Description = s
			case "type":
				s, _ := tomlString(val)
				curStage.Type = s
			case "working_dir":
				s, _ := tomlString(val)
				curStage.WorkingDir = s
			case "on_error":
				s, _ := tomlString(val)
				curStage.OnError = s
			case "dry_run_safe":
				curStage.DryRunSafe = val == "true"
			case "command":
				arr, err := tomlStringArray(val)
				if err != nil {
					return nil, fmt.Errorf("line %d: %w", ln+1, err)
				}
				curStage.Command = arr
			case "depends_on":
				arr, _ := tomlStringArray(val)
				curStage.DependsOn = arr
			case "require_cap":
				arr, _ := tomlStringArray(val)
				curStage.RequireCap = arr
			}
		case "stage.env":
			if curStage == nil {
				return nil, fmt.Errorf("line %d: stage.env key %q before [[stages]]", ln+1, key)
			}
			s, _ := tomlString(val)
			curStage.Env[key] = s
		default:
			return nil, fmt.Errorf("line %d: key %q outside any section", ln+1, key)
		}
	}
	if curStage != nil {
		manifest.Stages = append(manifest.Stages, *curStage)
	}
	return manifest, nil
}

func tomlString(v string) (string, error) {
	v = strings.TrimSpace(v)
	if len(v) >= 2 && v[0] == '"' && v[len(v)-1] == '"' {
		return v[1 : len(v)-1], nil
	}
	return "", fmt.Errorf("expected quoted string, got %q", v)
}

func tomlStringArray(v string) ([]string, error) {
	v = strings.TrimSpace(v)
	if !strings.HasPrefix(v, "[") || !strings.HasSuffix(v, "]") {
		return nil, fmt.Errorf("expected [\"a\", \"b\", ...], got %q", v)
	}
	inner := strings.TrimSpace(v[1 : len(v)-1])
	if inner == "" {
		return nil, nil
	}
	// Split on `","` after stripping surrounding `"`.
	parts := splitTopLevelCommas(inner)
	out := make([]string, 0, len(parts))
	for _, p := range parts {
		s, err := tomlString(strings.TrimSpace(p))
		if err != nil {
			return nil, err
		}
		out = append(out, s)
	}
	return out, nil
}

func splitTopLevelCommas(s string) []string {
	var out []string
	depth := 0
	inStr := false
	start := 0
	for i, r := range s {
		switch r {
		case '"':
			inStr = !inStr
		case '[', '(', '{':
			if !inStr {
				depth++
			}
		case ']', ')', '}':
			if !inStr {
				depth--
			}
		case ',':
			if !inStr && depth == 0 {
				out = append(out, s[start:i])
				start = i + 1
			}
		}
		_ = r
	}
	out = append(out, s[start:])
	return out
}

func filterStagesByName(stages []actorStage, name string) []actorStage {
	var out []actorStage
	for _, s := range stages {
		if s.Name == name {
			out = append(out, s)
		}
	}
	return out
}

func removeStages(stages []actorStage, skip []string) []actorStage {
	if len(skip) == 0 {
		return stages
	}
	skipSet := map[string]bool{}
	for _, n := range skip {
		skipSet[n] = true
	}
	var out []actorStage
	for _, s := range stages {
		if !skipSet[s.Name] {
			out = append(out, s)
		}
	}
	return out
}

// preflight checks for tools that the stages need.
func preflight(stages []actorStage, _ bool) error {
	needed := map[string]bool{}
	for _, st := range stages {
		switch st.Type {
		case "cf-worker", "cf-pages":
			needed["wrangler"] = true
		case "k8s":
			needed["kubectl"] = true
		case "docker-build":
			needed["docker"] = true
		case "cf-tunnel":
			needed["cloudflared"] = true
		}
	}
	missing := []string{}
	for tool := range needed {
		if _, err := exec.LookPath(tool); err != nil {
			missing = append(missing, tool)
		}
	}
	if len(missing) > 0 {
		return fmt.Errorf("missing required tools: %s", strings.Join(missing, ", "))
	}
	return nil
}

// ── stage execution ───────────────────────────────────────────────────

func executeStage(repoRoot string, st *actorStage, agentToken string) error {
	if len(st.Command) == 0 {
		return fmt.Errorf("stage %q: command is empty", st.Name)
	}
	cmd := exec.Command(st.Command[0], st.Command[1:]...)

	// Working dir
	cmd.Dir = repoRoot
	if st.WorkingDir != "" {
		cmd.Dir = filepath.Join(repoRoot, st.WorkingDir)
	}

	// Env: inherit parent, overlay stage env, surface the agent token.
	cmd.Env = os.Environ()
	for k, v := range st.Env {
		cmd.Env = append(cmd.Env, k+"="+v)
	}
	if agentToken != "" {
		cmd.Env = append(cmd.Env, "ETZ_AGENT_TOKEN="+agentToken)
	}

	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}

// ── capability + audit emission ──────────────────────────────────────

type capability struct {
	GranterDid  string   `json:"granterDid"`
	GranteeDid  string   `json:"granteeDid"`
	Purpose     string   `json:"purpose"`
	Scope       []string `json:"scope"`
	ExpiresAt   string   `json:"expiresAt"`
	CapabilityUri string `json:"capabilityUri"`
}

func loadCapability(path string) (*capability, error) {
	if path == "" {
		return nil, nil
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	jws := strings.TrimSpace(string(data))
	// Full Ed25519 verification against the granter's DID document.
	// Override mechanisms (Phase 2):
	//   ETZ_CAPABILITY_VERIFY=offline       — structural-only check (CI/dev)
	//   ETZ_CAPABILITY_DID_DOCUMENT=<path>  — local DID doc instead of HTTPS resolve
	// Per ADR-2605232000.
	offline := os.Getenv("ETZ_CAPABILITY_VERIFY") == "offline"
	didDocLocal := os.Getenv("ETZ_CAPABILITY_DID_DOCUMENT")
	res := verifyJWS(jws, time.Now().UTC(), &verifyOpts{offline: offline, didDocLocal: didDocLocal})
	if !res.Valid && !offline {
		return nil, fmt.Errorf("capability verify failed: %s", res.Reason)
	}
	if res.Payload == nil {
		return nil, fmt.Errorf("capability payload missing")
	}
	if res.Payload.Purpose != "deploy-execution" {
		return nil, fmt.Errorf("capability purpose=%q, want deploy-execution", res.Payload.Purpose)
	}
	return &capability{
		GranterDid:    res.Payload.GranterDid,
		GranteeDid:    res.Payload.GranteeDid,
		Purpose:       res.Payload.Purpose,
		Scope:         res.Payload.Scope,
		ExpiresAt:     res.Payload.ExpiresAt,
		CapabilityUri: res.Payload.CapabilityUri,
	}, nil
}

func stageGate(st *actorStage, cap *capability, agentToken string) error {
	if len(st.RequireCap) == 0 {
		return nil // unrestricted stage
	}
	if cap == nil && agentToken == "" {
		return fmt.Errorf("stage requires capability %v but none provided (--capability or --agent-token)", st.RequireCap)
	}
	if cap == nil {
		// Without a capability we still allow when the agent-token scope covers — but verification
		// of the JWT itself is a follow-up. In v1 we accept the token as a hint.
		return nil
	}
	scopeSet := map[string]bool{}
	for _, s := range cap.Scope {
		scopeSet[s] = true
	}
	for _, needed := range st.RequireCap {
		if !scopeSet[needed] {
			return fmt.Errorf("capability lacks scope %q (has %v)", needed, cap.Scope)
		}
	}
	return nil
}

func emitDeployEvent(manifest *actorTOML, st *actorStage, commitSha, outcome, errMsg string, durMs int64) {
	ev := map[string]any{
		"version":      1,
		"agentDid":     getenvOrEmpty("ETZ_AGENT_DID"),
		"stewardDid":   getenvOrEmpty("ETZ_STEWARD_DID"),
		"stage":        st.Name,
		"target":       map[string]string{"nsid": "deploy." + st.Type, "identifier": manifest.Actor.Name + "/" + st.Name},
		"command":      sanitizeCommand(st.Command),
		"commitSha":    commitSha,
		"outcome":      outcome,
		"durationMs":   durMs,
		"occurredAt":   time.Now().UTC().Format(time.RFC3339Nano),
	}
	if errMsg != "" {
		ev["errorCode"] = errMsg
	}
	// Stderr structured JSON (durable record — parent process / CI captures).
	b, _ := json.Marshal(ev)
	fmt.Fprintf(os.Stderr, "DEPLOY_EVENT %s\n", string(b))

	// Best-effort POST to the audit aggregator (Phase 2 wiring).
	// Failures do NOT block the deploy — stderr remains the source of truth
	// until the aggregator is online. Skip entirely when ETZ_AUDIT_DISABLE=1
	// (useful for dry-run loops where you don't want network calls).
	if os.Getenv("ETZ_AUDIT_DISABLE") != "1" {
		go postAuditEvent(b)
	}
}

func getenvOrEmpty(k string) string {
	v, _ := os.LookupEnv(k)
	return v
}

// sanitizeCommand drops any token that looks like a secret (--password, --token, etc.)
// from the audit-emission view. Conservative; only structural sanitization.
func sanitizeCommand(args []string) string {
	if len(args) == 0 {
		return ""
	}
	out := make([]string, 0, len(args))
	for i := 0; i < len(args); i++ {
		a := args[i]
		la := strings.ToLower(a)
		if strings.Contains(la, "password") || strings.Contains(la, "token") || strings.Contains(la, "secret") {
			out = append(out, a, "***")
			if i+1 < len(args) && !strings.HasPrefix(args[i+1], "-") {
				i++
			}
			continue
		}
		out = append(out, a)
	}
	return strings.Join(out, " ")
}

// Used by agent-token.go below.
var _ = ed25519.PublicKey(nil)
var _ = io.Discard
var _ bytes.Buffer
