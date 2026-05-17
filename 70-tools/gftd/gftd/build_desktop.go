package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

const desktopHostManifestRel = "20-actors/magatama/hosts/magatama-desktop-host/Cargo.toml"

type desktopConfig struct {
	BundleID string            `json:"bundleId,omitempty"`
	Category string            `json:"category,omitempty"`
	MinMacOS string            `json:"minMacOS,omitempty"`
	Window   *desktopWindow    `json:"window,omitempty"`
	DMG      *desktopDMGConfig `json:"dmg,omitempty"`
}

type desktopWindow struct {
	Title  string `json:"title,omitempty"`
	Width  int    `json:"width,omitempty"`
	Height int    `json:"height,omitempty"`
}

type desktopDMGConfig struct {
	Background string `json:"background,omitempty"`
}

type desktopHostConfig struct {
	AppName             string  `json:"app_name"`
	RuntimeMode         string  `json:"runtime_mode"`
	GuestRelativePath   string  `json:"guest_relative_path"`
	StartupRelativePath *string `json:"startup_relative_path,omitempty"`
	BundleID            *string `json:"bundle_id,omitempty"`
}

func (g *magatamaJSONLD) DesktopOrDefault() *desktopConfig {
	if g.Desktop != nil {
		return g.Desktop
	}
	return &desktopConfig{}
}

func (g *magatamaJSONLD) DesktopRuntimeMode() string {
	rt := g.RuntimeOrDefault()
	if strings.HasPrefix(rt, "desktop") {
		return rt
	}
	if rt == "worker" {
		return "desktop-wasm"
	}
	return rt
}

func (g *magatamaJSONLD) BundleIDOrDefault() string {
	if g.Desktop != nil && g.Desktop.BundleID != "" {
		return g.Desktop.BundleID
	}
	appID := g.AppID()
	if appID == "" {
		appID = "app"
	}
	return "jp.co.gftd." + appID
}

func runBuildDesktop(args []string) error {
	fs := flag.NewFlagSet("build-desktop", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component source directory")
	output := fs.String("output", "", "output directory for staged desktop bundle (default: <dir>/dist-desktop)")
	skipGuest := fs.Bool("skip-guest-build", false, "skip guest app build and package existing artifact only")
	skipHost := fs.Bool("skip-host-build", false, "skip desktop host cargo build and reuse existing binary")
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

	cfg, err := readMagatamaJSONLD(compDir)
	if err != nil {
		return fmt.Errorf("magatama.jsonld required: %w", err)
	}

	runtimeMode := cfg.DesktopRuntimeMode()
	if runtimeMode != "desktop-wasm" && runtimeMode != "desktop-ts" {
		return fmt.Errorf("build-desktop requires runtimeType desktop-wasm or desktop-ts, got %q", cfg.RuntimeOrDefault())
	}

	if !*skipGuest {
		if err := ensureDesktopGuestBuilt(compDir, cfg); err != nil {
			return err
		}
	}

	hostBinary, err := resolveDesktopHostBinary(compDir, *skipHost)
	if err != nil {
		return err
	}

	outDir := *output
	if outDir == "" {
		outDir = filepath.Join(compDir, "dist-desktop")
	}
	if err := os.RemoveAll(outDir); err != nil {
		return err
	}
	if err := os.MkdirAll(outDir, 0o755); err != nil {
		return err
	}

	plan, err := stageDesktopApp(compDir, outDir, cfg, hostBinary)
	if err != nil {
		return err
	}

	planPath := filepath.Join(outDir, "desktop-plan.json")
	planJSON, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		return err
	}
	if err := os.WriteFile(planPath, planJSON, 0o644); err != nil {
		return err
	}

	fmt.Fprintf(os.Stderr, "==> staged desktop app: %s\n", plan.AppBundlePath)
	fmt.Fprintf(os.Stderr, "==> desktop host binary: %s\n", hostBinary)
	fmt.Fprintf(os.Stderr, "==> desktop plan: %s\n", planPath)
	fmt.Fprintf(os.Stderr, "==> next: gftd package-dmg --dir %s\n", compDir)
	return nil
}

type desktopBuildPlan struct {
	AppName        string `json:"appName"`
	RuntimeMode    string `json:"runtimeMode"`
	AppBundlePath  string `json:"appBundlePath"`
	GuestPath      string `json:"guestPath"`
	BundleID       string `json:"bundleId"`
	HostConfigPath string `json:"hostConfigPath"`
	DMGPath        string `json:"dmgPath,omitempty"`
}

func ensureDesktopGuestBuilt(compDir string, cfg *magatamaJSONLD) error {
	svelteDir := filepath.Join(compDir, "svelte")
	if _, err := os.Stat(filepath.Join(svelteDir, "package.json")); err == nil {
		if err := runCmd(svelteDir, "pnpm", "install", "--frozen-lockfile"); err != nil {
			if err := runCmd(svelteDir, "pnpm", "install", "--no-frozen-lockfile"); err != nil {
				return fmt.Errorf("desktop svelte pnpm install: %w", err)
			}
		}
		if err := runCmd(svelteDir, "pnpm", "build"); err != nil {
			return fmt.Errorf("desktop svelte pnpm build: %w", err)
		}
	}

	switch cfg.DesktopRuntimeMode() {
	case "desktop-wasm":
		componentPath := resolveDesktopGuestSource(compDir, cfg)
		if _, err := os.Stat(componentPath); err != nil {
			if err := runBuild([]string{"--dir", compDir, "--no-svelte"}); err != nil {
				return fmt.Errorf("guest build: %w", err)
			}
		}
	case "desktop-ts":
		// web assets are handled above
	}
	return nil
}

func stageDesktopApp(compDir, outDir string, cfg *magatamaJSONLD, hostBinary string) (*desktopBuildPlan, error) {
	appName := desktopAppDisplayName(cfg)
	appDir := filepath.Join(outDir, appName+".app")
	contentsDir := filepath.Join(appDir, "Contents")
	macOSDir := filepath.Join(contentsDir, "MacOS")
	resourcesDir := filepath.Join(contentsDir, "Resources")
	if err := os.MkdirAll(macOSDir, 0o755); err != nil {
		return nil, err
	}
	if err := os.MkdirAll(resourcesDir, 0o755); err != nil {
		return nil, err
	}

	var guestSource string
	var guestTarget string
	switch cfg.DesktopRuntimeMode() {
	case "desktop-wasm":
		guestSource = resolveDesktopGuestSource(compDir, cfg)
		guestTarget = filepath.Join(resourcesDir, filepath.Base(cfg.ComponentPath()))
	case "desktop-ts":
		guestSource = filepath.Join(compDir, "svelte", "build")
		guestTarget = filepath.Join(resourcesDir, "web")
	}
	if guestSource != "" {
		if info, err := os.Stat(guestSource); err == nil {
			if info.IsDir() {
				if err := copyDir(guestSource, guestTarget); err != nil {
					return nil, fmt.Errorf("copy desktop guest dir: %w", err)
				}
			} else {
				if err := copyFile(guestSource, guestTarget); err != nil {
					return nil, fmt.Errorf("copy desktop guest: %w", err)
				}
			}
		} else {
			return nil, fmt.Errorf("desktop guest artifact not found: %s", guestSource)
		}
	}

	if webSource := resolveDesktopWebSource(compDir); webSource != "" {
		webTarget := filepath.Join(resourcesDir, "web")
		if err := copyDir(webSource, webTarget); err != nil {
			return nil, fmt.Errorf("copy desktop web assets: %w", err)
		}
	}

	if guestAssetDir := filepath.Join(compDir, "assets", "guest"); dirExists(guestAssetDir) {
		if err := copyDir(guestAssetDir, filepath.Join(resourcesDir, "guest")); err != nil {
			return nil, fmt.Errorf("copy desktop guest assets: %w", err)
		}
	}

	guestAPISource := filepath.Join(compDir, "assets", "guest-api.json")
	if _, err := os.Stat(guestAPISource); err == nil {
		if err := copyFile(guestAPISource, filepath.Join(resourcesDir, "guest-api.json")); err != nil {
			return nil, fmt.Errorf("copy guest-api.json: %w", err)
		}
	}

	executableName := sanitizeDesktopExecutableName(appName)
	executablePath := filepath.Join(macOSDir, executableName)
	if err := copyFile(hostBinary, executablePath); err != nil {
		return nil, fmt.Errorf("copy desktop host binary: %w", err)
	}
	if err := os.Chmod(executablePath, 0o755); err != nil {
		return nil, fmt.Errorf("chmod desktop host binary: %w", err)
	}

	hostCfg, err := writeDesktopHostConfig(filepath.Join(resourcesDir, "host-config.json"), cfg, appName, guestTarget, resourcesDir)
	if err != nil {
		return nil, err
	}
	if err := writeDesktopInfoPlist(filepath.Join(contentsDir, "Info.plist"), cfg, appName); err != nil {
		return nil, err
	}

	iconSource := filepath.Join(compDir, "assets", "icon.icns")
	if _, err := os.Stat(iconSource); err == nil {
		if err := copyFile(iconSource, filepath.Join(resourcesDir, "icon.icns")); err != nil {
			return nil, fmt.Errorf("copy icon.icns: %w", err)
		}
	}

	return &desktopBuildPlan{
		AppName:        appName,
		RuntimeMode:    cfg.DesktopRuntimeMode(),
		AppBundlePath:  appDir,
		GuestPath:      guestTarget,
		BundleID:       cfg.BundleIDOrDefault(),
		HostConfigPath: hostCfg,
	}, nil
}

func desktopAppDisplayName(cfg *magatamaJSONLD) string {
	if cfg.Desktop != nil && cfg.Desktop.Window != nil && cfg.Desktop.Window.Title != "" {
		return cfg.Desktop.Window.Title
	}
	if cfg.Profile != nil && cfg.Profile.DisplayName != "" {
		return cfg.Profile.DisplayName
	}
	return cfg.Name
}

func sanitizeDesktopExecutableName(name string) string {
	var b strings.Builder
	lastUnderscore := false
	for _, ch := range name {
		if (ch >= 'a' && ch <= 'z') || (ch >= 'A' && ch <= 'Z') || (ch >= '0' && ch <= '9') {
			b.WriteRune(ch)
			lastUnderscore = false
			continue
		}
		if !lastUnderscore {
			b.WriteByte('_')
			lastUnderscore = true
		}
	}
	out := strings.Trim(b.String(), "_")
	if out == "" {
		return "MagatamaDesktopApp"
	}
	return out
}

func writeDesktopInfoPlist(path string, cfg *magatamaJSONLD, appName string) error {
	minMacOS := "14.0"
	if cfg.Desktop != nil && cfg.Desktop.MinMacOS != "" {
		minMacOS = cfg.Desktop.MinMacOS
	}
	plist := fmt.Sprintf(`<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleDevelopmentRegion</key>
  <string>en</string>
  <key>CFBundleExecutable</key>
  <string>%s</string>
  <key>CFBundleIdentifier</key>
  <string>%s</string>
  <key>CFBundleName</key>
  <string>%s</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>0.1.0</string>
  <key>CFBundleVersion</key>
  <string>1</string>
  <key>LSMinimumSystemVersion</key>
  <string>%s</string>
</dict>
</plist>
`, sanitizeDesktopExecutableName(appName), cfg.BundleIDOrDefault(), appName, minMacOS)
	return os.WriteFile(path, []byte(plist), 0o644)
}

func writeDesktopHostConfig(path string, cfg *magatamaJSONLD, appName, guestTarget, resourcesDir string) (string, error) {
	guestRel, err := filepath.Rel(resourcesDir, guestTarget)
	if err != nil {
		return "", fmt.Errorf("resolve guest relative path: %w", err)
	}
	var startup *string
	if _, err := os.Stat(filepath.Join(resourcesDir, "web", "index.html")); err == nil {
		s := "web/index.html"
		startup = &s
	}
	bundleID := cfg.BundleIDOrDefault()
	hostCfg := desktopHostConfig{
		AppName:             appName,
		RuntimeMode:         cfg.DesktopRuntimeMode(),
		GuestRelativePath:   filepath.ToSlash(guestRel),
		StartupRelativePath: startup,
		BundleID:            &bundleID,
	}
	data, err := json.MarshalIndent(hostCfg, "", "  ")
	if err != nil {
		return "", fmt.Errorf("marshal host config: %w", err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return "", fmt.Errorf("write host config: %w", err)
	}
	return path, nil
}

func resolveDesktopGuestSource(compDir string, cfg *magatamaJSONLD) string {
	componentPath := filepath.Join(compDir, cfg.ComponentPath())
	if _, err := os.Stat(componentPath); err == nil {
		return componentPath
	}
	return filepath.Join(compDir, filepath.Base(cfg.ComponentPath()))
}

func resolveDesktopWebSource(compDir string) string {
	for _, rel := range []string{
		filepath.Join("svelte", "build"),
		filepath.Join("svelte", "dist"),
	} {
		path := filepath.Join(compDir, rel)
		if dirExists(path) {
			return path
		}
	}
	return ""
}

func dirExists(path string) bool {
	info, err := os.Stat(path)
	return err == nil && info.IsDir()
}

func resolveDesktopHostBinary(compDir string, skipBuild bool) (string, error) {
	gitRoot, err := findGitRoot(compDir)
	if err != nil {
		return "", err
	}
	manifest := filepath.Join(gitRoot, desktopHostManifestRel)
	if _, err := os.Stat(manifest); err != nil {
		return "", fmt.Errorf("desktop host manifest not found: %s", manifest)
	}
	if !skipBuild {
		if _, err := exec.LookPath("cargo"); err != nil {
			return "", fmt.Errorf("required tool not found: cargo (install Rust toolchain)")
		}
		fmt.Fprintf(os.Stderr, "==> cargo build --release (magatama-desktop-host)\n")
		if err := runCmd(gitRoot, "cargo", "build", "--release", "--manifest-path", manifest); err != nil {
			return "", fmt.Errorf("build desktop host: %w", err)
		}
	}
	targetDir, err := resolveCargoTargetDir(filepath.Dir(manifest))
	if err != nil {
		return "", fmt.Errorf("resolve desktop host cargo target dir: %w", err)
	}
	binary := filepath.Join(targetDir, "release", "magatama-desktop-host")
	if _, err := os.Stat(binary); err != nil {
		return "", fmt.Errorf("desktop host binary not found: %s", binary)
	}
	return binary, nil
}
