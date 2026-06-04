package main

import (
	"bufio"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
)

const (
	defaultWITWorld         = "magatama:runtime/magatama-component"
	defaultWASIAdapterVer   = "28.0.0"
	wASIAdapterURLTemplate  = "https://github.com/bytecodealliance/wasmtime/releases/download/v%s/wasi_snapshot_preview1.reactor.wasm"
	adapterCacheDir         = ".cache/etzhayyim/adapters"
)

func runBuild(args []string) error {
	fs := flag.NewFlagSet("build", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component source directory (default: current dir)")
	witDir := fs.String("wit-dir", "", "WIT definition directory (default: auto-detect from git root)")
	witWorld := fs.String("wit-world", defaultWITWorld, "WIT world identifier for component embed")
	adapterVer := fs.String("adapter-version", defaultWASIAdapterVer, "wasmtime WASI preview1 adapter version")
	adapterPath := fs.String("adapter", "", "path to wasi_snapshot_preview1.reactor.wasm (overrides --adapter-version)")
	output := fs.String("output", "", "output component .wasm (default: derived from magatama.toml component.path)")
	noSvelte := fs.Bool("no-svelte", false, "skip svelte/pnpm build even if svelte/ dir exists")
	noCheck := fs.Bool("no-check", false, "skip svelte-check type validation")
	extension := fs.Bool("extension", false, "build as W Protocol extension component (world: etzhayyim:w/w-extension)")
	tinygoRoot := fs.String("tinygo-root", "", "TinyGo SDK root (overrides system tinygo from PATH)")
	goRoot := fs.String("go-root", os.Getenv("GOROOT"), "Go SDK root (default: $GOROOT)")
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

	// Extension mode: override WIT world to etzhayyim:w/w-extension
	if *extension {
		*witWorld = "etzhayyim:w/w-extension"
		*noSvelte = true // Extensions don't have svelte frontends
		fmt.Fprintf(os.Stderr, "==> building W Protocol extension (world: %s)\n", *witWorld)
	}

	// Read etzhayyim.json for build defaults (optional — flags override)
	if cfg, err := readetzhayyimJSON(compDir); err == nil {
		if *witWorld == defaultWITWorld && cfg.WITWorld != "" {
			*witWorld = cfg.WITWorld
		}
		if *adapterVer == defaultWASIAdapterVer && cfg.WASIAdapterVersion != "" {
			*adapterVer = cfg.WASIAdapterVersion
		}
	}

	// Resolve output name from magatama.toml component.path if not given
	outputWasm := *output
	if outputWasm == "" {
		magatamaTOML := filepath.Join(compDir, "magatama.toml")
		if compPath, err := readMagatamaComponentPath(magatamaTOML); err == nil {
			outputWasm = filepath.Join(compDir, filepath.Base(compPath))
		} else {
			// Fall back: use directory basename + .wasm
			outputWasm = filepath.Join(compDir, filepath.Base(compDir)+".wasm")
		}
	}

	// Resolve WIT dir
	resolvedWITDir := *witDir
	if resolvedWITDir == "" {
		if env := os.Getenv("MAGATAMA_WIT_DIR"); env != "" {
			resolvedWITDir = env
		} else if gitRoot, err := findGitRoot(compDir); err == nil {
			resolvedWITDir = filepath.Join(gitRoot, "packages", "rust", "magatama", "wit")
		} else {
			return fmt.Errorf("cannot auto-detect WIT dir: not in a git repository. Use --wit-dir or set MAGATAMA_WIT_DIR")
		}
	}
	if _, err := os.Stat(resolvedWITDir); err != nil {
		return fmt.Errorf("WIT dir not found: %s", resolvedWITDir)
	}

	// Extension mode: WIT dir is the wproto WIT dir (contains w-extension world).
	// The magatama WIT dir doesn't contain extension worlds.
	if *extension && *witDir == "" {
		if gitRoot, err := findGitRoot(compDir); err == nil {
			wprotoWITDir := filepath.Join(gitRoot, "packages", "rust", "wproto", "wit")
			if _, err := os.Stat(filepath.Join(wprotoWITDir, "etzhayyim-w", "w-extension.wit")); err == nil {
				resolvedWITDir = wprotoWITDir
				fmt.Fprintf(os.Stderr, "==> using wproto WIT dir: %s\n", resolvedWITDir)
			}
		}
	}

	// Validate WIT version matches the deployed magatama-server.
	// Skip for extension builds — extensions use etzhayyim:w WIT, not magatama:runtime.
	if !*extension {
		if err := validateWITVersion(resolvedWITDir); err != nil {
			return err
		}
	}

	// Pre-flight: CORS guard — app-side CORS headers are forbidden.
	if err := validateNoCORSHeaders(compDir); err != nil {
		return err
	}

	// Resolve WASI adapter
	adapter := *adapterPath
	if adapter == "" {
		cached, err := ensureWASIAdapter(*adapterVer)
		if err != nil {
			return fmt.Errorf("WASI adapter: %w", err)
		}
		adapter = cached
	}

	// Check required tools
	for _, tool := range []string{"tinygo", "wasm-tools"} {
		if _, err := exec.LookPath(tool); err != nil {
			return fmt.Errorf("required tool not found: %s (run 'etzhayyim plugin install %s')", tool, tool)
		}
	}

	// Optional: svelte build
	svelteDir := filepath.Join(compDir, "svelte")
	if !*noSvelte {
		if _, err := os.Stat(svelteDir); err == nil {
			fmt.Fprintf(os.Stderr, "==> pnpm install (svelte)\n")
			if err := runCmd(svelteDir, "pnpm", "install", "--frozen-lockfile"); err != nil {
				return fmt.Errorf("pnpm install: %w", err)
			}
			// svelte-check: catch Connect gRPC proto errors at build time
			if !*noCheck {
				fmt.Fprintf(os.Stderr, "==> svelte-check (type validation)\n")
				if err := runCmd(svelteDir, "pnpm", "exec", "svelte-check", "--fail-on-warnings"); err != nil {
					return fmt.Errorf("svelte-check: %w", err)
				}
			}
			fmt.Fprintf(os.Stderr, "==> pnpm build (svelte)\n")
			if err := runCmd(svelteDir, "pnpm", "build"); err != nil {
				return fmt.Errorf("pnpm build: %w", err)
			}
		}
	}

	// Temp file paths
	name := strings.TrimSuffix(filepath.Base(outputWasm), ".wasm")
	buildDir := filepath.Join(compDir, "build")
	if err := os.MkdirAll(buildDir, 0o755); err != nil {
		return err
	}
	coreWasm := filepath.Join(buildDir, name+"_core.wasm")
	embeddedWasm := filepath.Join(buildDir, name+"_embedded.wasm")
	defer func() {
		os.Remove(coreWasm)
		os.Remove(embeddedWasm)
	}()

	// Step 1: TinyGo build → core WASM (WASI P1)
	fmt.Fprintf(os.Stderr, "==> tinygo build → %s\n", filepath.Base(coreWasm))
	tinygoArgs := []string{
		"build",
		"-target=wasip1",
		"-gc=leaking",
		"-buildmode=c-shared",
		"-no-debug",
		"-o", coreWasm,
		".",
	}
	tinygoEnv := os.Environ()
	if *tinygoRoot != "" {
		tinygoEnv = setEnv(tinygoEnv, "TINYGOROOT", *tinygoRoot)
		tinygoEnv = setEnv(tinygoEnv, "PATH", *tinygoRoot+"/bin:"+getEnvPath())
	}
	if *goRoot != "" {
		tinygoEnv = setEnv(tinygoEnv, "GOROOT", *goRoot)
		tinygoEnv = setEnv(tinygoEnv, "PATH", *goRoot+"/bin:"+getEnvFromSlice(tinygoEnv, "PATH"))
	}
	tinygoEnv = setEnv(tinygoEnv, "GOTOOLCHAIN", "auto")
	if err := runCmdEnv(compDir, tinygoEnv, "tinygo", tinygoArgs...); err != nil {
		return fmt.Errorf("tinygo build: %w", err)
	}

	// Step 2: wasm-tools component embed — attach WIT metadata
	fmt.Fprintf(os.Stderr, "==> wasm-tools component embed (world: %s)\n", *witWorld)
	if err := runCmd(compDir, "wasm-tools", "component", "embed",
		"-w", *witWorld,
		resolvedWITDir,
		coreWasm,
		"-o", embeddedWasm,
	); err != nil {
		return fmt.Errorf("wasm-tools component embed: %w", err)
	}

	// Step 3: wasm-tools component new — WASI P1 → P2 + Component format
	fmt.Fprintf(os.Stderr, "==> wasm-tools component new → %s\n", filepath.Base(outputWasm))
	componentNewArgs := []string{
		"component", "new",
		embeddedWasm,
		"--adapt", "wasi_snapshot_preview1=" + adapter,
	}
	componentNewArgs = append(componentNewArgs, "-o", outputWasm)
	if err := runCmd(compDir, "wasm-tools", componentNewArgs...); err != nil {
		return fmt.Errorf("wasm-tools component new: %w", err)
	}

	// Step 4: Validate component imports match current WIT (warning only).
	fmt.Fprintf(os.Stderr, "==> validating component WIT imports\n")
	if err := validateComponentImports(outputWasm, resolvedWITDir); err != nil {
		fmt.Fprintf(os.Stderr, "  warning: %v\n", err)
	}

	info, err := os.Stat(outputWasm)
	if err == nil {
		fmt.Fprintf(os.Stderr, "==> built %s (%d KB)\n", filepath.Base(outputWasm), info.Size()/1024)
	}
	return nil
}

// readMagatamaComponentPath parses [component].path from a magatama.toml file.
func readMagatamaComponentPath(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()

	inComponent := false
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "[component]" {
			inComponent = true
			continue
		}
		if strings.HasPrefix(line, "[") {
			inComponent = false
		}
		if inComponent && strings.HasPrefix(line, "path") {
			// path = "/app/foo.wasm"
			parts := strings.SplitN(line, "=", 2)
			if len(parts) == 2 {
				val := strings.TrimSpace(parts[1])
				val = strings.Trim(val, `"'`)
				return val, nil
			}
		}
	}
	return "", fmt.Errorf("component.path not found in %s", path)
}

// findGitRoot walks up the directory tree to find the .git root.
func findGitRoot(start string) (string, error) {
	dir := start
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

// ensureWASIAdapter downloads the WASI preview1 reactor adapter if not cached.
func ensureWASIAdapter(version string) (string, error) {
	home, err := os.UserHomeDir()
	if err != nil {
		return "", err
	}
	cacheDir := filepath.Join(home, adapterCacheDir, "v"+version)
	adapterFile := filepath.Join(cacheDir, "wasi_snapshot_preview1.reactor.wasm")
	if _, err := os.Stat(adapterFile); err == nil {
		return adapterFile, nil
	}
	if err := os.MkdirAll(cacheDir, 0o755); err != nil {
		return "", err
	}
	url := fmt.Sprintf(wASIAdapterURLTemplate, version)
	fmt.Fprintf(os.Stderr, "==> downloading WASI adapter v%s\n", version)
	resp, err := http.Get(url) //nolint:noctx
	if err != nil {
		return "", fmt.Errorf("download adapter: %w", err)
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return "", fmt.Errorf("download adapter: HTTP %d from %s", resp.StatusCode, url)
	}
	f, err := os.Create(adapterFile)
	if err != nil {
		return "", err
	}
	defer f.Close()
	if _, err := io.Copy(f, resp.Body); err != nil {
		return "", err
	}
	return adapterFile, nil
}

func runCmd(dir string, name string, args ...string) error {
	return runCmdEnv(dir, nil, name, args...)
}

func runCmdEnv(dir string, env []string, name string, args ...string) error {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if env != nil {
		cmd.Env = env
	}
	return cmd.Run()
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

// witVersionTagPrefix returns a short tag prefix like "wit02" from semver "0.2.0".
func witVersionTagPrefix(semver string) string {
	parts := strings.SplitN(semver, ".", 3)
	if len(parts) < 2 {
		return "wit" + strings.ReplaceAll(semver, ".", "")
	}
	return fmt.Sprintf("wit%s%s", parts[0], parts[1])
}

var corsHeaderPattern = regexp.MustCompile(`Access-Control-Allow-(?:Headers|Origin|Methods)`)

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

// validateComponentImports checks that all magatama:* imports in the component
// are present in the current WIT directory. WASI imports (wasi:*) are ignored
// as they are provided by the wasmtime WASI linker, not the magatama host.
func validateComponentImports(componentWasm, witDir string) error {
	// Extract component's imports via `wasm-tools component wit`
	compOut, err := exec.Command("wasm-tools", "component", "wit", componentWasm).Output()
	if err != nil {
		return fmt.Errorf("failed to extract component WIT: %w", err)
	}
	// Extract WIT directory's available interfaces
	witOut, err := exec.Command("wasm-tools", "component", "wit", witDir).Output()
	if err != nil {
		return fmt.Errorf("failed to parse WIT directory: %w", err)
	}

	// Parse "import <iface>" lines from component (e.g. "import magatama:runtime/cypher@0.2.0;")
	importRe := regexp.MustCompile(`(?m)^\s*import\s+(\S+)`)
	compImports := importRe.FindAllStringSubmatch(string(compOut), -1)

	// Build set of interface names from WIT directory (e.g. "  interface cypher {" → "cypher")
	// Multi-package output indents interfaces inside package blocks, so allow leading whitespace.
	ifaceRe := regexp.MustCompile(`(?m)^\s*interface\s+(\S+)\s*\{`)
	witIfaceMatches := ifaceRe.FindAllStringSubmatch(string(witOut), -1)
	witIfaceSet := make(map[string]bool, len(witIfaceMatches))
	for _, m := range witIfaceMatches {
		witIfaceSet[m[1]] = true
	}

	var missing []string
	for _, m := range compImports {
		iface := strings.TrimSuffix(m[1], ";")
		// Skip WASI imports — provided by wasmtime, not by magatama host
		if strings.HasPrefix(iface, "wasi:") {
			continue
		}
		// Extract short name: "magatama:runtime/cypher@0.2.0" → "cypher"
		shortName := iface
		if idx := strings.LastIndex(shortName, "/"); idx >= 0 {
			shortName = shortName[idx+1:]
		}
		if idx := strings.Index(shortName, "@"); idx >= 0 {
			shortName = shortName[:idx]
		}
		if !witIfaceSet[shortName] {
			missing = append(missing, iface)
		}
	}

	if len(missing) > 0 {
		return fmt.Errorf(
			"WIT import mismatch: component imports %d interface(s) not in current WIT:\n  %s\n"+
				"This component was likely built with an older/newer WIT version.\n"+
				"Fix: rebuild with `etzhayyim build` using current WIT.",
			len(missing), strings.Join(missing, "\n  "))
	}
	return nil
}
