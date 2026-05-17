package main

import (
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"
)

const (
	defaultWITWorld = "magatama:runtime/magatama-component"
)

func runBuild(args []string) error {
	fs := flag.NewFlagSet("build", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component source directory (default: current dir)")
	witDir := fs.String("wit-dir", "", "WIT definition directory (T3 Container / Rust contract-jco / extension only — TS Native + Lexicon Contract apps leave this empty, F-Plan 2026-04-13)")
	witWorld := fs.String("wit-world", defaultWITWorld, "WIT world identifier")
	noSvelte := fs.Bool("no-svelte", false, "skip svelte/pnpm build even if svelte/ dir exists")
	noCheck := fs.Bool("no-check", false, "skip svelte-check type validation")
	extension := fs.Bool("extension", false, "build as W Protocol extension component (world: gftd:w/w-extension)")
	depsScore := fs.Bool("deps-score", true, "evaluate deps.etzhayyim.com score after build (CI gate, default: on)")
	depsScoreURL := fs.String("deps-score-url", "https://deps.etzhayyim.com/", "deps score source URL")
	depsScoreMin := fs.Float64("deps-score-min", 0, "minimum allowed deps score (0 disables threshold check)")
	depsScoreTimeoutSec := fs.Int("deps-score-timeout-sec", 20, "deps score HTTP timeout in seconds")
	noLint := fs.Bool("no-lint", false, "skip pre-build lint checks")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	compDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}
	wsRoot := compDir
	if gr, grErr := findGitRoot(compDir); grErr == nil {
		wsRoot = gr
	}
	if !*noLint {
		if err := runLintTarget(wsRoot, "silent-catch"); err != nil {
			return fmt.Errorf("pre-build lint failed (silent-catch): %w", err)
		}
	}

	var cfg *magatamaJSONLD

	// Extension mode: override WIT world to gftd:w/w-extension
	if *extension {
		*witWorld = "gftd:w/w-extension"
		*noSvelte = true // Extensions don't have svelte frontends
		fmt.Fprintf(os.Stderr, "==> building W Protocol extension (world: %s)\n", *witWorld)
	}

	// Read magatama.jsonld for build defaults (optional — flags override)
	if loadedCfg, err := readMagatamaJSONLD(compDir); err == nil {
		cfg = loadedCfg
	} else if _, statErr := os.Stat(filepath.Join(compDir, "magatama.jsonld")); statErr == nil {
		// magatama.jsonld exists but failed validation — report as build error
		return fmt.Errorf("magatama.jsonld validation failed: %w", err)
	}
	if cfg != nil && cfg.Build != nil {
		if *witWorld == defaultWITWorld && cfg.Build.WITWorld != "" {
			*witWorld = cfg.Build.WITWorld
		}
	}

	// Resolve WIT dir (F-Plan 2026-04-13: optional for TS Native + Lexicon Contract).
	// Only required for T3 Container / Rust contract-jco generators that pass --wit-dir
	// or set MAGATAMA_WIT_DIR. The legacy packages/contract/wit/ fallback is removed
	// (the path was archived to _archive/00-contracts/wit/ on 2026-04-12).
	resolvedWITDir := *witDir
	if resolvedWITDir == "" {
		if env := os.Getenv("MAGATAMA_WIT_DIR"); env != "" {
			resolvedWITDir = env
		}
	}

	// Extension mode: try the wproto WIT dir (contains w-extension world).
	if *extension && resolvedWITDir == "" {
		if gitRoot, err := findGitRoot(compDir); err == nil {
			wprotoWITDir := filepath.Join(gitRoot, "packages", "rust", "wproto", "wit")
			if _, err := os.Stat(filepath.Join(wprotoWITDir, "gftd-w", "w-extension.wit")); err == nil {
				resolvedWITDir = wprotoWITDir
				fmt.Fprintf(os.Stderr, "==> using wproto WIT dir: %s\n", resolvedWITDir)
			}
		}
		if resolvedWITDir == "" {
			return fmt.Errorf("extension build requires WIT dir but none found. Pass --wit-dir or set MAGATAMA_WIT_DIR")
		}
	}

	// If a WIT dir was resolved (T3 Container / Rust / extension), validate it exists
	// and check the WIT version. Otherwise (TS Native, the default), skip WIT entirely
	// — host capability surface lives in 00-contracts/lexicons/ai/gftd/host/ (Lexicon SSoT).
	if resolvedWITDir != "" {
		if _, err := os.Stat(resolvedWITDir); err != nil {
			return fmt.Errorf("WIT dir not found: %s", resolvedWITDir)
		}
		if !*extension {
			if err := validateWITVersion(resolvedWITDir); err != nil {
				return err
			}
		}
	}

	// Pre-flight: CORS guard — app-side CORS headers are forbidden.
	if err := validateNoCORSHeaders(compDir); err != nil {
		return err
	}
	if err := validateNoPdsHardcode(compDir); err != nil {
		return err
	}
	if err := validateMagatamaGovernanceImport(compDir); err != nil {
		return err
	}
	if err := validateProfile(compDir, cfg); err != nil {
		return err
	}
	if err := validateMagatamaRequired(compDir, cfg); err != nil {
		return err
	}

	// Validate Worker entry (src/app.ts with createWorkerExport from @gftd/magatama-host-sdk)
	entryPath := filepath.Join(compDir, "src", "app.ts")
	if _, err := os.Stat(entryPath); err != nil {
		return fmt.Errorf("worker entry not found: %s (expected src/app.ts with createWorkerExport())", entryPath)
	}

	// Svelte CSR build (Vite → svelte/build/) if svelte/ directory exists
	svelteDir := filepath.Join(compDir, "svelte")
	if !*noSvelte {
		if _, err := os.Stat(svelteDir); err == nil {
			fmt.Fprintf(os.Stderr, "==> pnpm install (svelte)\n")
			if err := runCmd(svelteDir, "pnpm", "install", "--frozen-lockfile"); err != nil {
				if err := runCmd(svelteDir, "pnpm", "install", "--no-frozen-lockfile"); err != nil {
					return fmt.Errorf("pnpm install: %w", err)
				}
			}
			if !*noCheck {
				fmt.Fprintf(os.Stderr, "==> svelte-check (type validation)\n")
				if err := runCmd(svelteDir, "pnpm", "exec", "svelte-check", "--fail-on-warnings"); err != nil {
					return fmt.Errorf("svelte-check: %w", err)
				}
			}
			fmt.Fprintf(os.Stderr, "==> vite build (Svelte CSR)\n")
			if err := runCmd(svelteDir, "pnpm", "build"); err != nil {
				return fmt.Errorf("vite build: %w", err)
			}
			// Validate: svelte/build/ must contain index.html after vite build
			buildIndex := filepath.Join(svelteDir, "build", "index.html")
			if _, err := os.Stat(buildIndex); err != nil {
				distIndex := filepath.Join(svelteDir, "dist", "index.html")
				if _, distErr := os.Stat(distIndex); distErr == nil {
					return fmt.Errorf("vite output went to svelte/dist/ instead of svelte/build/. Set outDir: 'build' in vite.config.ts")
				}
				return fmt.Errorf("svelte/build/index.html not found after vite build. Check vite.config.ts outDir")
			}
			// Warn: no CSS file (Tailwind requires app.css with @tailwind directives)
			buildAssets := filepath.Join(svelteDir, "build", "assets")
			if entries, err := os.ReadDir(buildAssets); err == nil {
				hasCSS := false
				for _, e := range entries {
					if strings.HasSuffix(e.Name(), ".css") {
						hasCSS = true
						break
					}
				}
				if !hasCSS {
					fmt.Fprintf(os.Stderr, "  warning: no CSS file in svelte/build/assets/ — add app.css with @tailwind directives and import it in main.ts\n")
				}
			}
			fmt.Fprintf(os.Stderr, "==> Svelte CSR → svelte/build/\n")
		}
	}

	buildScoreSummary := "deps score: skipped"
	if *depsScore {
		if *depsScoreTimeoutSec <= 0 {
			return fmt.Errorf("--deps-score-timeout-sec must be greater than 0")
		}
		fmt.Fprintf(os.Stderr, "==> evaluating deps score from %s\n", *depsScoreURL)
		report, err := evaluateDepsScore(*depsScoreURL, 5, time.Duration(*depsScoreTimeoutSec)*time.Second)
		if err != nil {
			// Fallback: remote deps.etzhayyim.com unavailable → warn and continue (Sql-based scoring available via `gftd deps sql`)
			fmt.Fprintf(os.Stderr, "==> deps score: remote evaluation failed (%v), continuing with warning\n", err)
			buildScoreSummary = "deps score: remote unavailable (use `gftd deps sql` for DID-based scoring)"
		} else {
			scoreSummary := formatDepsScoreSummary(report)
			fmt.Fprintf(os.Stderr, "==> deps score %.1f (%s)\n", report.Scoring.OverallScore, scoreSummary)
			buildScoreSummary = fmt.Sprintf("deps score: %.1f (%s)", report.Scoring.OverallScore, scoreSummary)
			if *depsScoreMin > 0 && report.Scoring.OverallScore < *depsScoreMin {
				return fmt.Errorf("deps score gate failed: got %.1f, required >= %.1f", report.Scoring.OverallScore, *depsScoreMin)
			}
		}
	}
	fmt.Fprintf(os.Stderr, "==> build summary: %s\n", buildScoreSummary)

	if err := runConfiguredHooks(cfg, compDir, hookOptions{
		Event:      "post_build",
		CachePurge: planCachePurge(cfg, compDir, ""),
	}); err != nil {
		return err
	}
	return nil
}

// findGitRoot walks up the directory tree to find the .git root.
func findGitRoot(start string) (string, error) {
	dir, err := filepath.Abs(start)
	if err != nil {
		return "", fmt.Errorf("resolve absolute path for %s: %w", start, err)
	}
	for {
		if _, err := os.Stat(filepath.Join(dir, ".git")); err == nil {
			return dir, nil
		}
		parent := filepath.Dir(dir)
		if parent == dir {
			return "", fmt.Errorf("no .git root found from %s", start)
		}
		dir = parent
	}
}

func runCmd(dir string, name string, args ...string) error {
	return runCmdEnv(dir, nil, name, args...)
}

// findMonoRoot walks up from dir to find pnpm-workspace.yaml (monorepo root).
func findMonoRoot(dir string) string {
	abs, _ := filepath.Abs(dir)
	for {
		if _, err := os.Stat(filepath.Join(abs, "pnpm-workspace.yaml")); err == nil {
			return abs
		}
		parent := filepath.Dir(abs)
		if parent == abs {
			return ""
		}
		abs = parent
	}
}

func runCmdEnv(dir string, env []string, name string, args ...string) error {
	tryRun := func(cmdName string) error {
		cmd := exec.Command(cmdName, args...)
		cmd.Dir = dir
		cmd.Stdout = os.Stdout
		cmd.Stderr = os.Stderr
		if env != nil {
			cmd.Env = env
		}
		setProcGroup(cmd)
		if err := cmd.Start(); err != nil {
			return err
		}
		trackChild(cmd)
		err := cmd.Wait()
		untrackChild(cmd)
		return err
	}

	err := tryRun(name)
	if err == nil {
		return nil
	}
	if name != "pnpm" {
		return err
	}
	if !strings.Contains(err.Error(), "no such file or directory") {
		return err
	}
	for _, candidate := range []string{"/opt/homebrew/bin/pnpm", "/usr/local/bin/pnpm"} {
		if candidate == name {
			continue
		}
		if fallbackErr := tryRun(candidate); fallbackErr == nil {
			return nil
		}
	}
	return err
}

func setEnv(env []string, key, value string) []string {
	prefix := key + "="
	for i, e := range env {
		if strings.HasPrefix(e, prefix) {
			env[i] = key + "=" + value
			return env
		}
	}
	return append(env, key+"="+value)
}

func getEnvPath() string {
	return os.Getenv("PATH")
}

func getEnvFromSlice(env []string, key string) string {
	prefix := key + "="
	for _, e := range env {
		if strings.HasPrefix(e, prefix) {
			return e[len(prefix):]
		}
	}
	return ""
}

// resolveCargoTargetDir returns the effective Cargo target dir for the given crate directory.
// Resolution order matches common Cargo usage: env override, nearest .cargo/config(.toml), local target/.
func resolveCargoTargetDir(crateDir string) (string, error) {
	if targetDir := strings.TrimSpace(os.Getenv("CARGO_TARGET_DIR")); targetDir != "" {
		if filepath.IsAbs(targetDir) {
			return targetDir, nil
		}
		return filepath.Clean(filepath.Join(crateDir, targetDir)), nil
	}

	configPath, err := findNearestCargoConfig(crateDir)
	if err != nil {
		return "", err
	}
	if configPath != "" {
		targetDir, err := readCargoTargetDir(configPath)
		if err != nil {
			return "", err
		}
		if targetDir != "" {
			if filepath.IsAbs(targetDir) {
				return targetDir, nil
			}
			return filepath.Clean(filepath.Join(filepath.Dir(filepath.Dir(configPath)), targetDir)), nil
		}
	}

	return filepath.Join(crateDir, "target"), nil
}

func findNearestCargoConfig(start string) (string, error) {
	dir := start
	for {
		for _, name := range []string{"config.toml", "config"} {
			candidate := filepath.Join(dir, ".cargo", name)
			if _, err := os.Stat(candidate); err == nil {
				return candidate, nil
			} else if err != nil && !os.IsNotExist(err) {
				return "", err
			}
		}

		parent := filepath.Dir(dir)
		if parent == dir {
			return "", nil
		}
		dir = parent
	}
}

func readCargoTargetDir(configPath string) (string, error) {
	data, err := os.ReadFile(configPath)
	if err != nil {
		return "", err
	}

	inBuild := false
	for _, rawLine := range strings.Split(string(data), "\n") {
		line := strings.TrimSpace(rawLine)
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if idx := strings.Index(line, "#"); idx >= 0 {
			line = strings.TrimSpace(line[:idx])
		}
		if line == "" {
			continue
		}
		if strings.HasPrefix(line, "[") {
			inBuild = line == "[build]"
			continue
		}
		if inBuild && strings.HasPrefix(line, "target-dir") {
			parts := strings.SplitN(line, "=", 2)
			if len(parts) != 2 {
				return "", fmt.Errorf("invalid target-dir entry in %s", configPath)
			}
			val := strings.TrimSpace(parts[1])
			val = strings.Trim(val, `"'`)
			return val, nil
		}
	}

	return "", nil
}

// validateProfile ensures magatama.jsonld has a profile section with required fields.
func validateProfile(compDir string, cfg *magatamaJSONLD) error {
	if cfg == nil {
		return nil
	}
	if cfg.Profile == nil {
		return fmt.Errorf("gftd: profile block is required in magatama.jsonld (add profile.displayName and profile.description)")
	}
	if cfg.Profile.DisplayName == "" {
		return fmt.Errorf("gftd: profile.displayName is required in magatama.jsonld")
	}
	if cfg.Profile.Description == "" {
		return fmt.Errorf("gftd: profile.description is required in magatama.jsonld")
	}
	// Force AI agent declaration + unofficial disclaimer
	cfg.Profile.IsBot = true
	if cfg.Profile.AgentType == "" {
		cfg.Profile.AgentType = "autonomous"
	}
	if cfg.Profile.Operator == "" {
		cfg.Profile.Operator = "amanomibashira"
	}
	// Append disclaimer to description if not already present
	disclaimer := " [AI Agent — unofficial, not affiliated with the real organization]"
	if !strings.Contains(cfg.Profile.Description, "unofficial") && !strings.Contains(cfg.Profile.Description, "AI Agent") {
		cfg.Profile.Description += disclaimer
	}
	if cfg.Profile.Avatar == "" && cfg.Profile.DisplayName != "" {
		initials := ""
		for i, w := range strings.Fields(cfg.Profile.DisplayName) {
			if i >= 2 {
				break
			}
			for _, r := range w {
				initials += string(r)
				break
			}
		}
		cfg.Profile.Avatar = initials
	}
	return nil
}

// validateMagatamaRequired ensures magatama.jsonld has all required blocks for
// PDS registration and deploy. Build fails if any are missing.
func validateMagatamaRequired(compDir string, cfg *magatamaJSONLD) error {
	if cfg == nil {
		return nil
	}
	var errs []string

	// governance block — RACI/RBAC role bindings for yoro profile governance display
	if cfg.Governance == nil {
		errs = append(errs, "governance block is required (add governance.roles for RACI/RBAC)")
	}

	// convoSystemPrompt — DM agent personality (Murakumo LLM system prompt)
	if cfg.ConvoSystemPrompt == "" {
		errs = append(errs, "convoSystemPrompt is required (DM agent conversation needs a system prompt)")
	}

	// profile.capabilities — capability tags for discovery
	if cfg.Profile != nil && len(cfg.Profile.Capabilities) == 0 {
		errs = append(errs, "profile.capabilities is required (add capability tags for capability discovery)")
	}

	// triggers.subscribeRepos.collections — reactive pipeline (ComAtprotoSyncSubscribeRepos)
	if cfg.Triggers == nil || cfg.Triggers.SubscribeRepos == nil || len(cfg.Triggers.SubscribeRepos.Collections) == 0 {
		errs = append(errs, "triggers.subscribeRepos.collections is required (reactive pipeline needs at least one collection)")
	}

	if len(errs) > 0 {
		return fmt.Errorf("gftd: magatama.jsonld missing required blocks:\n  - %s", strings.Join(errs, "\n  - "))
	}
	return nil
}

// validateWITVersion reads the WIT package version from magatama.wit and
// detects the WIT version from world.wit. Returns error if version cannot be parsed.
func validateWITVersion(witDir string) error {
	_, err := detectWITVersion(witDir)
	return err
}

// detectWITVersion reads the WIT package version from world.wit.
// Returns the semver string (e.g. "0.2.0") or error if not found.
func detectWITVersion(witDir string) (string, error) {
	witFile := filepath.Join(witDir, "world.wit")
	data, err := os.ReadFile(witFile)
	if err != nil {
		return "", fmt.Errorf("read WIT file: %w", err)
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "package magatama:runtime@") {
			ver := strings.TrimPrefix(line, "package magatama:runtime@")
			ver = strings.TrimSuffix(ver, ";")
			ver = strings.TrimSpace(ver)
			if ver == "" {
				return "", fmt.Errorf("empty version in %s", witFile)
			}
			return ver, nil
		}
	}
	return "", fmt.Errorf("cannot find 'package magatama:runtime@...' in %s", witFile)
}

var corsHeaderPattern = regexp.MustCompile(`Access-Control-Allow-(?:Headers|Origin|Methods)`)
var pdsHardcodePattern = regexp.MustCompile(`(?:appId|app_id)\s*[:=]\s*"pds"|mergeRecord\([^)]*"pds"\s*\)|\.sql\([^)]*"pds"\s*\)|\.mutate\([^)]*"pds"\s*\)`)

// validateNoCORSHeaders scans main.go for forbidden app-side CORS header literals.
// CORS is managed by Cloudflare Worker / Container routing.
func validateNoCORSHeaders(compDir string) error {
	mainGo := filepath.Join(compDir, "main.go")
	data, err := os.ReadFile(mainGo)
	if err != nil {
		return nil // no main.go = no check needed
	}
	if corsHeaderPattern.Match(data) {
		return fmt.Errorf(
			"cors guard: app-side Access-Control-Allow-* headers are forbidden in %s\n"+
				"CORS is managed in Envoy Gateway SecurityPolicy. Remove all CORS header literals from app code.",
			mainGo,
		)
	}
	return nil
}

// validateNoPdsHardcode scans TS/Go source files for hardcoded appId "pds" in
// Sql operations. appId must be repo-derived; "pds" is the shared namespace
// reserved for cross-app data (App registry, Profile).
func validateNoPdsHardcode(compDir string) error {
	for _, name := range []string{"main.go", "src/index.ts", "src/worker.ts"} {
		p := filepath.Join(compDir, name)
		data, err := os.ReadFile(p)
		if err != nil {
			continue
		}
		if pdsHardcodePattern.Match(data) {
			return fmt.Errorf(
				"pds-hardcode: appId 'pds' hardcoded in %s\n"+
					"Use repo-derived appId (extractAppId(repo)). 'pds' is shared namespace for cross-app data only.",
				p,
			)
		}
	}
	return nil
}

// validateMagatamaGovernanceImport ensures App components declare governance in
// their local WIT world. This keeps app-owned world.wit aligned with the
// mandatory governance import exposed by the shared magatama runtime.
func validateMagatamaGovernanceImport(compDir string) error {
	if _, err := os.Stat(filepath.Join(compDir, "magatama.jsonld")); err != nil {
		return nil
	}

	worldPath := filepath.Join(compDir, "wit", "world.wit")
	data, err := os.ReadFile(worldPath)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return fmt.Errorf("read app world.wit: %w", err)
	}

	world := string(data)
	if strings.Contains(world, "import magatama:agent/governance@1.0.0;") ||
		strings.Contains(world, "include magatama:runtime/magatama-component@1.0.0;") {
		return nil
	}

	return fmt.Errorf(
		"magatama governance guard: %s must import `magatama:agent/governance@1.0.0` or include `magatama:runtime/magatama-component@1.0.0`\n"+
			"App components must declare governance WIT explicitly so app-owned world definitions stay aligned with runtime governance enforcement.",
		worldPath,
	)
}
