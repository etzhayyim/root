package main

import (
	"crypto/md5"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"io/fs"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"
	"sync/atomic"
	"time"
)

// Default base image for kotodama-server Cloudflare Containers.
// Update via --base-image flag or etzhayyim.json "base_image" field.
const defaultBaseImage = "ghcr.io/etzhayyim/kotodama-server:20260318-223437"

// Secrets Store ID shared by all kotodama Workers.
const secretsStoreID = "1824561668fe47cc9127d493961885af"

func runDeploy(args []string) error {
	fs := flag.NewFlagSet("deploy", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component source directory (default: current dir)")
	smokeURL := fs.String("smoke-url", "", "URL for smoke test health check after deploy")
	noSmoke := fs.Bool("no-smoke", false, "skip smoke test")
	noCheck := fs.Bool("no-check", false, "skip svelte-check type validation")
	baseImage := fs.String("base-image", "", "kotodama-server base image (default: "+defaultBaseImage+")")
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

	// Read etzhayyim.json for app metadata
	cfg, err := readetzhayyimJSON(compDir)
	if err != nil {
		return fmt.Errorf("etzhayyim.json required: %w", err)
	}

	// Native mode: separate path (Docker build → push → CF deploy)
	if cfg.Type == "native" {
		return deployNativeCF(cfg, compDir, *noSmoke, *smokeURL)
	}

	// KotodamaApp mode: direct CF Container deploy from source directory
	return deployCFDirect(cfg, compDir, *noSmoke, *noCheck, *smokeURL, *baseImage)
}

// etzhayyimJSON is the deployment envelope read from etzhayyim.json.
// Runtime config (triggers, pool, yata) lives in kotodama.toml — not duplicated here.
type etzhayyimJSON struct {
	// Required: component name
	Name string `json:"name"`
	// Required: app identifier (subdomain: {project}.etzhayyim.com or {nanoid}.etzhayyim.com)
	Nanoid string `json:"nanoid"`
	// Optional: project folder suffix = subdomain (e.g. "lawfirm" → lawfirm.etzhayyim.com)
	Project string `json:"project,omitempty"`
	// Optional: "native" for non-KotodamaApp containers
	Type string `json:"type,omitempty"`
	// Optional: Clerk org_id binding
	Org string `json:"org,omitempty"`
	// Optional: Dockerfile name (default: "Dockerfile.kotodama")
	Dockerfile string `json:"dockerfile,omitempty"`
	// Optional: kotodama-server base image override
	BaseImage string `json:"base_image,omitempty"`
	// Optional: health check path (default: "/health")
	HealthCheck string `json:"health_check,omitempty"`
	// Optional: WIT world identifier
	WITWorld string `json:"wit_world,omitempty"`
	// Optional: wasmtime WASI adapter version
	WASIAdapterVersion string `json:"wasi_adapter_version,omitempty"`
	// Optional: container sleep timeout (default: "2m")
	SleepAfter string `json:"sleep_after,omitempty"`
	// Optional: enable ISR mode (SvelteKit adapter-cloudflare SSR in Worker)
	ISR bool `json:"isr,omitempty"`
}

// AppID returns the subdomain / app identifier.
func (g *etzhayyimJSON) AppID() string {
	if g.Project != "" {
		return g.Project
	}
	return g.Nanoid
}

// readetzhayyimJSON reads and parses etzhayyim.json from the given directory.
func readetzhayyimJSON(dir string) (*etzhayyimJSON, error) {
	path := filepath.Join(dir, "etzhayyim.json")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var g etzhayyimJSON
	if err := json.Unmarshal(data, &g); err != nil {
		return nil, err
	}
	if g.Name == "" {
		return nil, fmt.Errorf("name not found in etzhayyim.json")
	}
	return &g, nil
}

// ImageRef returns the container image reference (without tag).
func (g *etzhayyimJSON) ImageRef() string {
	image := "ghcr.io/etzhayyim/" + g.Name
	if g.Nanoid != "" {
		image += "-" + g.Nanoid
	}
	return image
}

// renderTemplate reads a template file and replaces placeholders.
func renderTemplate(templatePath string, replacements map[string]string) (string, error) {
	data, err := os.ReadFile(templatePath)
	if err != nil {
		return "", fmt.Errorf("read template %s: %w", templatePath, err)
	}
	content := string(data)
	for placeholder, value := range replacements {
		content = strings.ReplaceAll(content, placeholder, value)
	}
	return content, nil
}

// ensureSymlink creates a symlink at dst pointing to src.
// Removes existing dst if it's a symlink or doesn't match.
func ensureSymlink(src, dst string) error {
	if target, err := os.Readlink(dst); err == nil {
		if target == src {
			return nil
		}
		os.Remove(dst)
	} else if _, err := os.Lstat(dst); err == nil {
		// dst exists but is not a symlink — skip (don't overwrite real files)
		return nil
	}
	return os.Symlink(src, dst)
}

// setupAppDir creates the per-app staging directory and symlinks shared files from the parent.
func setupAppDir(cfBaseDir, appID string) (string, error) {
	appDir := filepath.Join(cfBaseDir, appID)
	if err := os.MkdirAll(filepath.Join(appDir, "src"), 0o755); err != nil {
		return "", err
	}

	// Symlink shared node deps from parent
	for _, name := range []string{"node_modules", "package.json", "package-lock.json", "tsconfig.json"} {
		src := filepath.Join(cfBaseDir, name)
		if _, err := os.Stat(src); err != nil {
			continue
		}
		if err := ensureSymlink(src, filepath.Join(appDir, name)); err != nil {
			return "", fmt.Errorf("symlink %s: %w", name, err)
		}
	}

	return appDir, nil
}

// deployCFDirect deploys a KotodamaApp to Cloudflare Containers directly from source.
// Each app gets its own staging directory: infra/cloudflare-containers/{appID}/.
func deployCFDirect(cfg *etzhayyimJSON, compDir string, noSmoke, noCheck bool, smokeURL, baseImageFlag string) error {
	appID := cfg.AppID()
	if appID == "" {
		return fmt.Errorf("project or nanoid required in etzhayyim.json")
	}

	gitRoot, err := findGitRoot(compDir)
	if err != nil {
		return fmt.Errorf("cannot find git root: %w", err)
	}
	cfBaseDir := filepath.Join(gitRoot, "infra", "cloudflare-containers")
	templateDir := filepath.Join(cfBaseDir, "templates")

	// Pre-flight: WIT version consistency
	witDir := filepath.Join(gitRoot, "packages", "rust", "kotodama", "wit")
	if err := validateWITVersion(witDir); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "==> pre-flight: WIT version OK\n")

	fmt.Fprintf(os.Stderr, "==> deploying %s to Cloudflare Containers\n", appID)

	// Ensure npm dependencies in parent dir
	if err := runCmd(cfBaseDir, "npm", "install", "--silent"); err != nil {
		return fmt.Errorf("npm install: %w", err)
	}

	// Setup per-app directory with symlinked deps
	appDir, err := setupAppDir(cfBaseDir, appID)
	if err != nil {
		return fmt.Errorf("setup app dir: %w", err)
	}

	// Step 1: Copy component files from source directory
	fmt.Fprintf(os.Stderr, "--- copy component files ---\n")
	componentsDir := filepath.Join(appDir, "components", appID)
	if err := os.MkdirAll(componentsDir, 0o755); err != nil {
		return err
	}

	// component.wasm
	wasmSrc := filepath.Join(compDir, "component.wasm")
	if _, err := os.Stat(wasmSrc); err != nil {
		wasmSrc = filepath.Join(compDir, "build", "component.wasm")
		if _, err := os.Stat(wasmSrc); err != nil {
			return fmt.Errorf("component.wasm not found in %s or %s/build/", compDir, compDir)
		}
	}
	if err := copyFile(wasmSrc, filepath.Join(componentsDir, "component.wasm")); err != nil {
		return fmt.Errorf("copy component.wasm: %w", err)
	}
	info, _ := os.Stat(filepath.Join(componentsDir, "component.wasm"))
	fmt.Fprintf(os.Stderr, "    component.wasm: %d bytes\n", info.Size())

	// static assets (svelte/build/ or static/)
	_ = os.RemoveAll(filepath.Join(componentsDir, "static"))
	for _, staticSrc := range []string{
		filepath.Join(compDir, "svelte", "build"),
		filepath.Join(compDir, "static"),
	} {
		if fi, err := os.Stat(staticSrc); err == nil && fi.IsDir() {
			if err := runCmd(compDir, "cp", "-r", staticSrc, filepath.Join(componentsDir, "static")); err != nil {
				return fmt.Errorf("copy static: %w", err)
			}
			break
		}
	}

	// Resolve base image
	baseImage := defaultBaseImage
	if baseImageFlag != "" {
		baseImage = baseImageFlag
	} else if cfg.BaseImage != "" {
		baseImage = cfg.BaseImage
	}

	// Resolve org_id for CAS prefix (org-scoped graph).
	// Falls back to app_id for backward compat.
	orgID := cfg.Org
	if orgID == "" {
		orgID = appID
	}

	// Template replacements
	replacements := map[string]string{
		"__APP_ID__":           appID,
		"__ORG_ID__":           orgID,
		"__BASE_IMAGE__":       baseImage,
		"__SECRETS_STORE_ID__": secretsStoreID,
	}

	// ISR mode: use adapter-cloudflare templates
	isISR := cfg.ISR
	isrTemplateDir := filepath.Join(templateDir, "isr")

	// Step 1b: Copy extension WASM files (if any declared in kotodama.toml)
	if extFiles, err := copyExtensionFiles(compDir, componentsDir); err != nil {
		return fmt.Errorf("copy extensions: %w", err)
	} else if len(extFiles) > 0 {
		fmt.Fprintf(os.Stderr, "    extensions: %d files copied\n", len(extFiles))
	}

	// Step 1c (ISR): Build SvelteKit with adapter-cloudflare
	if isISR {
		fmt.Fprintf(os.Stderr, "--- ISR: build SvelteKit (adapter-cloudflare) ---\n")
		svelteDir := filepath.Join(compDir, "svelte")
		if _, err := os.Stat(svelteDir); err != nil {
			return fmt.Errorf("ISR mode requires svelte/ directory: %w", err)
		}
		// Clean build cache for fresh Tailwind + SvelteKit output
		os.RemoveAll(filepath.Join(svelteDir, ".svelte-kit"))
		os.RemoveAll(filepath.Join(svelteDir, "node_modules", ".vite"))
		// Install deps + check + build
		if err := runCmd(svelteDir, "pnpm", "install", "--frozen-lockfile"); err != nil {
			if err := runCmd(svelteDir, "pnpm", "install"); err != nil {
				return fmt.Errorf("pnpm install (svelte): %w", err)
			}
		}
		// svelte-kit sync: generate .svelte-kit/tsconfig.json (needed before svelte-check)
		_ = runCmd(svelteDir, "pnpm", "exec", "svelte-kit", "sync")
		// svelte-check: catch Connect gRPC proto errors before deploy
		if !noCheck {
			fmt.Fprintf(os.Stderr, "==> svelte-check (type validation)\n")
			if err := runCmd(svelteDir, "pnpm", "exec", "svelte-check", "--fail-on-warnings"); err != nil {
				return fmt.Errorf("svelte-check: %w", err)
			}
		}
		if err := runCmd(svelteDir, "pnpm", "build"); err != nil {
			return fmt.Errorf("pnpm build (svelte): %w", err)
		}
		// Copy SvelteKit build output to staging
		svelteBuildDir := filepath.Join(svelteDir, ".svelte-kit", "cloudflare")
		if _, err := os.Stat(svelteBuildDir); err != nil {
			return fmt.Errorf("SvelteKit build output not found at %s — check adapter-cloudflare config", svelteBuildDir)
		}
		// Clean staging completely
		svelteStaging := filepath.Join(appDir, "_svelte")
		_ = os.RemoveAll(svelteStaging)
		os.Remove(filepath.Join(appDir, "_svelte_worker.js"))
		os.Remove(filepath.Join(appDir, "_svelte_worker.js.map"))
		if err := runCmd(compDir, "cp", "-r", svelteBuildDir, svelteStaging); err != nil {
			return fmt.Errorf("copy SvelteKit build: %w", err)
		}
		// Move _worker.js OUT of _svelte/ (Assets dir) to prevent wrangler auto-routing.
		// Our src/worker.ts imports it as "../_svelte_worker.js".
		workerJS := filepath.Join(svelteStaging, "_worker.js")
		if _, err := os.Stat(workerJS); err == nil {
			if err := os.Rename(workerJS, filepath.Join(appDir, "_svelte_worker.js")); err != nil {
				return fmt.Errorf("move _worker.js: %w", err)
			}
			if mapFile := workerJS + ".map"; true {
				if _, err := os.Stat(mapFile); err == nil {
					os.Rename(mapFile, filepath.Join(appDir, "_svelte_worker.js.map"))
				}
			}
		}
		// Remove special Assets files that cause wrangler to capture all paths:
		// _routes.json (include:["/*"]), 404.html (SPA fallback), _headers (custom headers)
		for _, f := range []string{"_routes.json", "404.html", "_headers", "_redirects"} {
			os.Remove(filepath.Join(svelteStaging, f))
		}
		// Copy SvelteKit server output + manifest for unbundled adapters (adapter-cloudflare v7+).
		// _svelte_worker.js may import "../output/server/index.js" and "../cloudflare-tmp/manifest.js"
		// relative to its original location inside .svelte-kit/cloudflare/_worker.js.
		// After moving to appDir/_svelte_worker.js, these resolve to cfBaseDir/{output,cloudflare-tmp}.
		svelteKitDir := filepath.Join(svelteDir, ".svelte-kit")
		for _, sub := range []string{"output", "cloudflare-tmp"} {
			src := filepath.Join(svelteKitDir, sub)
			if _, err := os.Stat(src); err == nil {
				dst := filepath.Join(cfBaseDir, sub)
				_ = os.RemoveAll(dst)
				if err := runCmd(svelteDir, "cp", "-r", src, dst); err != nil {
					return fmt.Errorf("copy %s: %w", sub, err)
				}
			}
		}
		// Generate src/worker.ts (custom entry: DO class + ISR + SvelteKit import)
		workerTS, err := renderTemplate(filepath.Join(isrTemplateDir, "worker.ts"), replacements)
		if err != nil {
			return fmt.Errorf("render worker.ts: %w", err)
		}
		if err := os.MkdirAll(filepath.Join(appDir, "src"), 0o755); err != nil {
			return fmt.Errorf("mkdir src: %w", err)
		}
		if err := os.WriteFile(filepath.Join(appDir, "src", "worker.ts"), []byte(workerTS), 0o644); err != nil {
			return fmt.Errorf("write src/worker.ts: %w", err)
		}
		fmt.Fprintf(os.Stderr, "    SvelteKit → _svelte/ (assets) + _svelte_worker.js + src/worker.ts\n")
	}

	// Step 2: Generate kotodama.toml (CF Container format)
	fmt.Fprintf(os.Stderr, "--- generate kotodama.toml ---\n")
	if err := generateCFKotodamaToml(appDir, compDir, appID, isISR); err != nil {
		return fmt.Errorf("generate kotodama.toml: %w", err)
	}

	// Select template directory based on ISR mode
	activeTemplateDir := templateDir
	if isISR {
		activeTemplateDir = isrTemplateDir
	}

	// Step 3: Generate wrangler.jsonc from template
	fmt.Fprintf(os.Stderr, "--- generate wrangler.jsonc ---\n")
	wranglerContent, err := renderTemplate(filepath.Join(activeTemplateDir, "wrangler.jsonc"), replacements)
	if err != nil {
		return fmt.Errorf("render wrangler.jsonc: %w", err)
	}
	if err := os.WriteFile(filepath.Join(appDir, "wrangler.jsonc"), []byte(wranglerContent), 0o644); err != nil {
		return fmt.Errorf("write wrangler.jsonc: %w", err)
	}

	// Step 4: Generate src/index.ts (Standard mode only — ISR prepends DO class to _worker.js)
	if !isISR {
		fmt.Fprintf(os.Stderr, "--- generate src/index.ts ---\n")
		indexContent, err := renderTemplate(filepath.Join(activeTemplateDir, "index.ts"), replacements)
		if err != nil {
			return fmt.Errorf("render index.ts: %w", err)
		}
		if err := os.WriteFile(filepath.Join(appDir, "src", "index.ts"), []byte(indexContent), 0o644); err != nil {
			return fmt.Errorf("write src/index.ts: %w", err)
		}
	}

	// Step 5: Generate Dockerfile from template
	fmt.Fprintf(os.Stderr, "--- generate Dockerfile ---\n")
	dockerfileContent, err := renderTemplate(filepath.Join(activeTemplateDir, "Dockerfile"), replacements)
	if err != nil {
		return fmt.Errorf("render Dockerfile: %w", err)
	}
	if err := os.WriteFile(filepath.Join(appDir, "Dockerfile"), []byte(dockerfileContent), 0o644); err != nil {
		return fmt.Errorf("write Dockerfile: %w", err)
	}

	// Step 6: Upload static assets to R2 (standard mode only — ISR uses Workers Assets)
	if !isISR {
		staticDir := filepath.Join(componentsDir, "static")
		if fi, err := os.Stat(staticDir); err == nil && fi.IsDir() {
			fmt.Fprintf(os.Stderr, "--- upload static to R2 ---\n")
			r2Prefix := appID + "/static"
			if err := uploadDirToR2(appDir, "etzhayyim-graph", r2Prefix, staticDir); err != nil {
				fmt.Fprintf(os.Stderr, "R2 upload failed (non-fatal): %v\n", err)
			}
		}
	} else {
		fmt.Fprintf(os.Stderr, "--- ISR: static assets served via Workers Assets (skip R2 upload) ---\n")
	}

	// Step 7: Deploy from per-app directory
	fmt.Fprintf(os.Stderr, "--- deploy ---\n")
	if err := runCmd(appDir, "npx", "wrangler", "deploy"); err != nil {
		return fmt.Errorf("wrangler deploy: %w", err)
	}

	// Smoke test
	resolvedSmokeURL := smokeURL
	if resolvedSmokeURL == "" {
		healthPath := "/health"
		if cfg.HealthCheck != "" {
			healthPath = cfg.HealthCheck
		}
		resolvedSmokeURL = "https://" + appID + ".etzhayyim.com" + healthPath
	}
	if !noSmoke && resolvedSmokeURL != "" {
		if err := smokeTest(resolvedSmokeURL); err != nil {
			fmt.Fprintf(os.Stderr, "smoke test failed: %v\n", err)
		} else {
			fmt.Fprintf(os.Stderr, "==> smoke test passed: %s\n", resolvedSmokeURL)
		}
	}

	fmt.Fprintf(os.Stderr, "\n=== Done: %s ===\n", appID)
	fmt.Fprintf(os.Stderr, "  https://%s.etzhayyim.com/health\n", appID)
	fmt.Fprintf(os.Stderr, "  https://%s.etzhayyim.com/_worker/health (edge-only)\n", appID)
	return nil
}

// generateCFKotodamaToml transforms the app's kotodama.toml into a CF Container server config.
// When isISR is true, static_dir and spa settings are removed (Worker serves static via Assets binding).
func generateCFKotodamaToml(appDir, compDir, appID string, isISR bool) error {
	appToml, err := os.ReadFile(filepath.Join(compDir, "kotodama.toml"))
	if err != nil {
		return fmt.Errorf("read kotodama.toml: %w", err)
	}

	content := "mode = \"single-tenant\"\n\n" + string(appToml)

	// Rewrite component path for container filesystem
	content = strings.ReplaceAll(content, `path = "/wasm/component.wasm"`, fmt.Sprintf(`path = "/data/components/%s/component.wasm"`, appID))
	content = strings.ReplaceAll(content, `path = "/app/component.wasm"`, fmt.Sprintf(`path = "/data/components/%s/component.wasm"`, appID))
	content = strings.ReplaceAll(content, `path = "component.wasm"`, fmt.Sprintf(`path = "/data/components/%s/component.wasm"`, appID))
	if isISR {
		// ISR mode: Worker serves static via Assets binding — remove static_dir and spa from TOML
		for _, key := range []string{"static_dir", "spa"} {
			for {
				idx := strings.Index(content, key)
				if idx < 0 { break }
				lineEnd := strings.Index(content[idx:], "\n")
				if lineEnd < 0 { content = content[:idx]; break }
				content = content[:idx] + content[idx+lineEnd+1:]
			}
		}
	} else {
		content = strings.ReplaceAll(content, `static_dir = "/wasm/static"`, fmt.Sprintf(`static_dir = "/data/components/%s/static"`, appID))
		content = strings.ReplaceAll(content, `static_dir = "/app/static"`, fmt.Sprintf(`static_dir = "/data/components/%s/static"`, appID))
	}

	// Container disk paths
	content = strings.ReplaceAll(content, `graph_uri = "/data/graph"`, `graph_uri = "/data/yata/graph"`)

	// Remove obsolete lance_flush_interval_ms
	for _, obsolete := range []string{"lance_flush_interval_ms"} {
		for {
			idx := strings.Index(content, obsolete)
			if idx < 0 { break }
			lineEnd := strings.Index(content[idx:], "\n")
			if lineEnd < 0 { content = content[:idx]; break }
			content = content[:idx] + content[idx+lineEnd+1:]
		}
	}

	// Ensure fuse = false for S3 write-through (R2 persistence)
	if !strings.Contains(content, "fuse") {
		content = strings.Replace(content, "[yata]\n", "[yata]\nfuse = false\n", 1)
	}

	// Remove sections not supported by current kotodama-server
	for _, section := range []string{
		"[yata.s3]",              // R2 config via YATA_S3_* env vars
		"[triggers.at_firehose]", // abolished; events via yata-wrpc
		"[triggers.w_firehose]",  // runtime handles w_firehose internally
		"[w_protocol]",           // runtime handles w_protocol internally
	} {
		if idx := strings.Index(content, section); idx >= 0 {
			end := strings.Index(content[idx+len(section):], "\n[")
			if end < 0 {
				content = content[:idx]
			} else {
				content = content[:idx] + content[idx+len(section)+end:]
			}
		}
	}

	// Force pool.size = 1 for per-app sleep
	if idx := strings.Index(content, "size = "); idx >= 0 {
		lineEnd := strings.Index(content[idx:], "\n")
		if lineEnd >= 0 {
			content = content[:idx] + "size = 1" + content[idx+lineEnd:]
		}
	}

	// Rewrite extension component paths for Container filesystem.
	// "extensions/trade-ext.wasm" → "/data/components/{appID}/extensions/trade-ext.wasm"
	containerExtDir := fmt.Sprintf("/data/components/%s/extensions/", appID)
	lines := strings.Split(content, "\n")
	inExtBlock := false
	for i, line := range lines {
		trimmed := strings.TrimSpace(line)
		if trimmed == "[[extensions]]" {
			inExtBlock = true
			continue
		}
		if strings.HasPrefix(trimmed, "[") && trimmed != "[[extensions]]" {
			inExtBlock = false
		}
		if inExtBlock && strings.HasPrefix(trimmed, "component") {
			parts := strings.SplitN(trimmed, "=", 2)
			if len(parts) == 2 {
				val := strings.TrimSpace(parts[1])
				val = strings.Trim(val, `"'`)
				// Rewrite to container path
				newPath := containerExtDir + filepath.Base(val)
				lines[i] = fmt.Sprintf(`component = "%s"`, newPath)
			}
		}
	}
	content = strings.Join(lines, "\n")

	return os.WriteFile(filepath.Join(appDir, "kotodama.toml"), []byte(content), 0o644)
}

// r2Manifest maps R2 keys to their MD5 hex hashes for incremental upload.
type r2Manifest map[string]string

const r2ManifestKey = "__deploy_manifest.json"

// loadR2Manifest fetches the previous deploy manifest from R2.
func loadR2Manifest(workDir, bucket, prefix string) r2Manifest {
	key := prefix + "/" + r2ManifestKey
	cmd := exec.Command("npx", "wrangler", "r2", "object", "get", bucket+"/"+key, "--pipe")
	cmd.Dir = workDir
	out, err := cmd.Output()
	if err != nil {
		return r2Manifest{} // first deploy or manifest missing
	}
	var m r2Manifest
	if err := json.Unmarshal(out, &m); err != nil {
		return r2Manifest{}
	}
	return m
}

// saveR2Manifest writes the deploy manifest to R2.
func saveR2Manifest(workDir, bucket, prefix string, m r2Manifest) error {
	data, err := json.Marshal(m)
	if err != nil {
		return err
	}
	tmpFile := filepath.Join(os.TempDir(), "r2-manifest-"+prefix+".json")
	if err := os.WriteFile(tmpFile, data, 0o644); err != nil {
		return err
	}
	defer os.Remove(tmpFile)
	key := prefix + "/" + r2ManifestKey
	return runCmd(workDir, "npx", "wrangler", "r2", "object", "put", bucket+"/"+key, "--file", tmpFile, "--remote")
}

// fileMD5 computes the MD5 hex digest of a file.
func fileMD5(path string) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	sum := md5.Sum(data)
	return hex.EncodeToString(sum[:]), nil
}

// r2UploadJob represents a single file to upload to R2.
type r2UploadJob struct {
	key       string
	localPath string
}

// uploadDirToR2 incrementally uploads a local directory to an R2 bucket.
// Uses a manifest to skip unchanged files (compared by MD5 hash).
// Uploads are parallelized (up to 16 concurrent wrangler processes).
func uploadDirToR2(workDir, bucket, prefix, localDir string) error {
	prev := loadR2Manifest(workDir, bucket, prefix)
	next := make(r2Manifest)
	var mu sync.Mutex

	var jobs []r2UploadJob
	var skipped int

	// Phase 1: scan files and compute hashes (fast, local I/O only)
	err := filepath.WalkDir(localDir, func(path string, d fs.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return err
		}
		rel, err := filepath.Rel(localDir, path)
		if err != nil {
			return err
		}
		key := prefix + "/" + rel

		hash, err := fileMD5(path)
		if err != nil {
			return err
		}

		mu.Lock()
		next[key] = hash
		mu.Unlock()

		if prevHash, ok := prev[key]; ok && prevHash == hash {
			skipped++
			return nil
		}

		jobs = append(jobs, r2UploadJob{key: key, localPath: path})
		return nil
	})
	if err != nil {
		return err
	}

	fmt.Fprintf(os.Stderr, "    R2 diff: %d to upload, %d unchanged (skipped)\n", len(jobs), skipped)

	if len(jobs) == 0 {
		return nil
	}

	// Phase 2: parallel upload changed files (8 concurrent, retry on 429)
	const concurrency = 8
	const maxRetries = 3
	var uploaded atomic.Int64
	var failed atomic.Int64

	sem := make(chan struct{}, concurrency)
	var wg sync.WaitGroup

	for _, job := range jobs {
		wg.Add(1)
		sem <- struct{}{}
		go func(j r2UploadJob) {
			defer wg.Done()
			defer func() { <-sem }()

			var err error
			for attempt := range maxRetries {
				if attempt > 0 {
					time.Sleep(time.Duration(attempt*2) * time.Second) // backoff: 2s, 4s
				}
				err = runCmd(workDir, "npx", "wrangler", "r2", "object", "put", bucket+"/"+j.key, "--file", j.localPath, "--remote")
				if err == nil {
					break
				}
			}
			if err != nil {
				failed.Add(1)
				fmt.Fprintf(os.Stderr, "    R2 FAIL %s (after %d retries)\n", j.key, maxRetries)
				return
			}
			n := uploaded.Add(1)
			if n%100 == 0 || n == int64(len(jobs)) {
				fmt.Fprintf(os.Stderr, "    R2 progress: %d/%d uploaded\n", n, len(jobs))
			}
		}(job)
	}
	wg.Wait()

	if f := failed.Load(); f > 0 {
		return fmt.Errorf("R2 upload: %d files failed", f)
	}

	fmt.Fprintf(os.Stderr, "    R2 upload: %d uploaded, %d skipped (unchanged)\n", len(jobs), skipped)

	// Save manifest for next deploy
	if err := saveR2Manifest(workDir, bucket, prefix, next); err != nil {
		fmt.Fprintf(os.Stderr, "    manifest save failed (non-fatal): %v\n", err)
	}

	return nil
}

// smokeTest does a simple HTTP GET health check with retries.
func smokeTest(url string) error {
	const maxRetries = 6
	const retryDelay = 10 * time.Second

	fmt.Fprintf(os.Stderr, "==> smoke test: %s\n", url)
	for i := range maxRetries {
		if i > 0 {
			time.Sleep(retryDelay)
		}
		resp, err := http.Get(url) //nolint:noctx
		if err != nil {
			fmt.Fprintf(os.Stderr, "    attempt %d: %v\n", i+1, err)
			continue
		}
		resp.Body.Close()
		if resp.StatusCode == http.StatusOK {
			return nil
		}
		fmt.Fprintf(os.Stderr, "    attempt %d: HTTP %d\n", i+1, resp.StatusCode)
	}
	return fmt.Errorf("smoke test failed after %d attempts", maxRetries)
}

// copyExtensionFiles copies extension WASM files from source directory to Container staging.
// Reads [[extensions]] from kotodama.toml and copies each component WASM file.
func copyExtensionFiles(compDir, componentsDir string) ([]string, error) {
	tomlPath := filepath.Join(compDir, "kotodama.toml")
	data, err := os.ReadFile(tomlPath)
	if err != nil {
		return nil, nil // no kotodama.toml = no extensions
	}

	// Simple parse: find all 'component = "..."' lines under [[extensions]]
	var copied []string
	inExtensions := false
	for _, line := range strings.Split(string(data), "\n") {
		trimmed := strings.TrimSpace(line)
		if trimmed == "[[extensions]]" {
			inExtensions = true
			continue
		}
		if strings.HasPrefix(trimmed, "[") && trimmed != "[[extensions]]" {
			inExtensions = false
		}
		if inExtensions && strings.HasPrefix(trimmed, "component") {
			parts := strings.SplitN(trimmed, "=", 2)
			if len(parts) != 2 {
				continue
			}
			path := strings.TrimSpace(parts[1])
			path = strings.Trim(path, `"'`)

			// Resolve relative to compDir
			srcPath := filepath.Join(compDir, path)
			if _, err := os.Stat(srcPath); err != nil {
				fmt.Fprintf(os.Stderr, "    extension %s not found (skipping)\n", path)
				continue
			}

			// Create extensions/ subdirectory in components
			extDir := filepath.Join(componentsDir, "extensions")
			if err := os.MkdirAll(extDir, 0o755); err != nil {
				return nil, err
			}

			dstPath := filepath.Join(extDir, filepath.Base(path))
			if err := copyFile(srcPath, dstPath); err != nil {
				return nil, fmt.Errorf("copy extension %s: %w", path, err)
			}
			copied = append(copied, path)
		}
	}
	return copied, nil
}

// copyFile copies a file from src to dst.
func copyFile(src, dst string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, data, 0o644)
}

// cmdOutput runs a command and returns its stdout.
func cmdOutput(dir string, name string, args ...string) (string, error) {
	cmd := exec.Command(name, args...)
	cmd.Dir = dir
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return string(out), nil
}

// gitShortSHA returns the short git commit SHA from the given directory.
func gitShortSHA(dir string) (string, error) {
	cmd := exec.Command("git", "rev-parse", "--short", "HEAD")
	cmd.Dir = dir
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

// deployNativeCF deploys a native (non-KotodamaApp) container to Cloudflare Containers.
func deployNativeCF(cfg *etzhayyimJSON, compDir string, noSmoke bool, smokeURL string) error {
	appID := cfg.AppID()
	workerName := cfg.Name
	if workerName == "" {
		workerName = appID
	}

	gitRoot, err := findGitRoot(compDir)
	if err != nil {
		return fmt.Errorf("cannot find git root: %w", err)
	}
	cfBaseDir := filepath.Join(gitRoot, "infra", "cloudflare-containers")

	fmt.Fprintf(os.Stderr, "==> deploying native container %s to Cloudflare Containers\n", appID)

	sleepAfter := "10m"
	if cfg.SleepAfter != "" {
		sleepAfter = cfg.SleepAfter
	}

	// Ensure npm dependencies in parent dir
	if err := runCmd(cfBaseDir, "npm", "install", "--silent"); err != nil {
		return fmt.Errorf("npm install: %w", err)
	}

	// Setup per-app directory with symlinked deps
	appDir, err := setupAppDir(cfBaseDir, appID)
	if err != nil {
		return fmt.Errorf("setup app dir: %w", err)
	}

	// Resolve Docker image tag
	tag := time.Now().Format("20060102-150405")
	fullImage := cfg.ImageRef() + ":" + tag

	// Docker build
	dockerfileName := cfg.Dockerfile
	if dockerfileName == "" {
		dockerfileName = "Dockerfile.kotodama"
	}
	dockerfilePath := filepath.Join(compDir, dockerfileName)
	fmt.Fprintf(os.Stderr, "==> docker build %s\n", fullImage)
	if err := runCmd(compDir, "docker", "build", "-f", dockerfilePath, "-t", fullImage, "."); err != nil {
		return fmt.Errorf("docker build: %w", err)
	}

	// Docker push
	fmt.Fprintf(os.Stderr, "==> docker push %s\n", fullImage)
	if err := runCmd(compDir, "docker", "push", fullImage); err != nil {
		return fmt.Errorf("docker push: %w", err)
	}

	// Generate Dockerfile (just FROM the pre-built image)
	dockerfileContent := fmt.Sprintf("FROM %s\nEXPOSE 8080\n", fullImage)
	if err := os.WriteFile(filepath.Join(appDir, "Dockerfile"), []byte(dockerfileContent), 0o644); err != nil {
		return fmt.Errorf("write Dockerfile: %w", err)
	}

	// Generate wrangler.jsonc (no R2, no YATA for native)
	wranglerContent := fmt.Sprintf(`{
  "name": "%s",
  "main": "src/index.ts",
  "compatibility_date": "2025-03-17",
  "compatibility_flags": ["nodejs_compat"],
  "containers": [
    {
      "class_name": "NativeContainer",
      "image": "./Dockerfile",
      "instance_type": "standard",
      "max_instances": 1
    }
  ],
  "durable_objects": {
    "bindings": [
      {
        "name": "CONTAINER",
        "class_name": "NativeContainer"
      }
    ]
  },
  "migrations": [
    {
      "tag": "v1",
      "new_sqlite_classes": ["NativeContainer"]
    }
  ],
  "routes": [
    {
      "pattern": "%s.etzhayyim.com/*",
      "zone_name": "etzhayyim.com"
    }
  ]
}
`, workerName, appID)
	if err := os.WriteFile(filepath.Join(appDir, "wrangler.jsonc"), []byte(wranglerContent), 0o644); err != nil {
		return fmt.Errorf("write wrangler.jsonc: %w", err)
	}

	// Generate src/index.ts
	indexContent := generateNativeIndexTS(appID, workerName, sleepAfter)
	if err := os.WriteFile(filepath.Join(appDir, "src", "index.ts"), []byte(indexContent), 0o644); err != nil {
		return fmt.Errorf("write src/index.ts: %w", err)
	}

	// Deploy from per-app directory
	if err := runCmd(appDir, "npx", "wrangler", "deploy"); err != nil {
		return fmt.Errorf("wrangler deploy: %w", err)
	}

	// Smoke test
	resolvedSmokeURL := smokeURL
	if resolvedSmokeURL == "" {
		healthPath := "/health"
		if cfg.HealthCheck != "" {
			healthPath = cfg.HealthCheck
		}
		resolvedSmokeURL = "https://" + appID + ".etzhayyim.com" + healthPath
	}
	if !noSmoke && resolvedSmokeURL != "" {
		if err := smokeTest(resolvedSmokeURL); err != nil {
			fmt.Fprintf(os.Stderr, "smoke test failed: %v\n", err)
		} else {
			fmt.Fprintf(os.Stderr, "==> smoke test passed: %s\n", resolvedSmokeURL)
		}
	}

	fmt.Fprintf(os.Stderr, "==> deployed native container %s\n", workerName)
	return nil
}

// generateNativeIndexTS generates a minimal CF Worker entry point for native containers.
func generateNativeIndexTS(appID, workerName, sleepAfter string) string {
	return fmt.Sprintf(`/**
 * Cloudflare Container — %[2]s (native).
 * Generated by etzhayyim deploy. Do not edit manually.
 */

import { Container } from "@cloudflare/containers";

interface Env {
  CONTAINER: DurableObjectNamespace<NativeContainer>;
}

export class NativeContainer extends Container<Env> {
  defaultPort = 8080;
  sleepAfter = "%[3]s";
  enableInternet = true;

  override onStart(): void {
    console.log("%[2]s container started");
  }

  override onStop(): void {
    console.log("%[2]s container stopped");
  }

  override onError(error: unknown): void {
    console.error("%[2]s container error:", error);
  }
}

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === "/_worker/health") {
      return new Response("ok", { status: 200 });
    }

    try {
      const container = env.CONTAINER.getByName("%[1]s");
      return await container.fetch(request);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Unknown error";
      return new Response(
        JSON.stringify({ error: "container_error", message }),
        {
          status: 502,
          headers: { "Content-Type": "application/json" },
        }
      );
    }
  },
};
`, appID, workerName, sleepAfter)
}
