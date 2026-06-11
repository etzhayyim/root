package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"runtime"
	"strings"
)

// pluginDef describes a manageable tool.
type pluginDef struct {
	Name        string
	Description string
	// latestURL returns the GitHub releases API URL to query for the latest version.
	latestURL string
	// urlTemplate is a Go format string: (version, os, arch) → download URL.
	// Special: use fetchURL() for complex logic.
	fetchURL func(version, goos, goarch string) string
	// installDir is the subdirectory under ~/.cache/etzhayyim/plugins/<name>/
	installBin string
}

var plugins = []pluginDef{
	{
		Name:        "wasm-tools",
		Description: "WebAssembly component toolchain (embed/new/print)",
		latestURL:   "https://api.github.com/repos/bytecodealliance/wasm-tools/releases/latest",
		fetchURL: func(version, goos, goarch string) string {
			// map go arch names to wasm-tools release names
			arch := goarch
			if arch == "amd64" {
				arch = "x86_64"
			} else if arch == "arm64" {
				arch = "aarch64"
			}
			os_ := goos
			if os_ == "darwin" {
				os_ = "macos"
			}
			return fmt.Sprintf(
				"https://github.com/bytecodealliance/wasm-tools/releases/download/v%s/wasm-tools-%s-%s-%s.tar.gz",
				version, version, arch, os_,
			)
		},
		installBin: "wasm-tools",
	},
}

func runPlugin(args []string) error {
	if len(args) == 0 {
		printPluginUsage()
		return nil
	}
	switch args[0] {
	case "list", "ls":
		return runPluginList()
	case "install":
		return runPluginInstall(args[1:])
	case "upgrade":
		return runPluginUpgrade(args[1:])
	case "help", "--help", "-h":
		printPluginUsage()
		return nil
	default:
		return fmt.Errorf("unknown plugin command: %s", args[0])
	}
}

func printPluginUsage() {
	fmt.Print(`etzhayyim plugin — manage build tools

USAGE:
  etzhayyim plugin list
  etzhayyim plugin install <name> [--version <ver>]
  etzhayyim plugin upgrade <name>

AVAILABLE PLUGINS:
`)
	for _, p := range plugins {
		fmt.Printf("  %-20s %s\n", p.Name, p.Description)
	}
	fmt.Print(`
  tinygo   (managed separately — see https://tinygo.org/getting-started/install/)
  wrangler (managed separately — npm install -g wrangler)

WASI adapters are cached automatically in ~/.cache/etzhayyim/adapters/
`)
}

func runPluginList() error {
	fmt.Println("PLUGIN              VERSION   PATH")
	fmt.Println("------              -------   ----")
	for _, p := range plugins {
		installed, ver := pluginStatus(p)
		if installed {
			fmt.Printf("%-20s %-9s %s\n", p.Name, ver, pluginBinPath(p))
		} else {
			fmt.Printf("%-20s %-9s (not installed)\n", p.Name, "-")
		}
	}
	// Also show system tools
	for _, tool := range []string{"tinygo", "docker", "wrangler"} {
		path, err := exec.LookPath(tool)
		if err != nil {
			fmt.Printf("%-20s %-9s (not found in PATH)\n", tool, "-")
		} else {
			fmt.Printf("%-20s %-9s %s\n", tool, systemToolVersion(tool), path)
		}
	}
	return nil
}

func runPluginInstall(args []string) error {
	fs := flag.NewFlagSet("plugin install", flag.ContinueOnError)
	version := fs.String("version", "", "specific version to install (default: latest)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if fs.NArg() == 0 {
		return fmt.Errorf("usage: etzhayyim plugin install <name> [--version <ver>]")
	}
	name := fs.Arg(0)
	p, ok := findPlugin(name)
	if !ok {
		return fmt.Errorf("unknown plugin: %s\nRun 'etzhayyim plugin list' to see available plugins", name)
	}

	ver := *version
	if ver == "" {
		var err error
		ver, err = fetchLatestVersion(p)
		if err != nil {
			return fmt.Errorf("fetch latest version for %s: %w", name, err)
		}
	}

	return installPlugin(p, ver)
}

func runPluginUpgrade(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: etzhayyim plugin upgrade <name>")
	}
	name := args[0]
	p, ok := findPlugin(name)
	if !ok {
		return fmt.Errorf("unknown plugin: %s", name)
	}
	latest, err := fetchLatestVersion(p)
	if err != nil {
		return fmt.Errorf("fetch latest version: %w", err)
	}
	installed, current := pluginStatus(p)
	if installed && current == latest {
		fmt.Printf("%s is already at latest version %s\n", name, latest)
		return nil
	}
	return installPlugin(p, latest)
}

func findPlugin(name string) (pluginDef, bool) {
	for _, p := range plugins {
		if p.Name == name {
			return p, true
		}
	}
	return pluginDef{}, false
}

func pluginCacheDir(p pluginDef) string {
	home, _ := os.UserHomeDir()
	return filepath.Join(home, ".cache", "etzhayyim", "plugins", p.Name)
}

func pluginBinPath(p pluginDef) string {
	return filepath.Join(pluginCacheDir(p), p.installBin)
}

func pluginStatus(p pluginDef) (installed bool, version string) {
	binPath := pluginBinPath(p)
	if _, err := os.Stat(binPath); err != nil {
		return false, ""
	}
	// Try to get version
	out, err := exec.Command(binPath, "--version").Output()
	if err != nil {
		return true, "unknown"
	}
	v := strings.TrimSpace(string(out))
	// Strip binary name prefix (e.g. "wasm-tools 1.2.3" → "1.2.3")
	parts := strings.Fields(v)
	if len(parts) >= 2 {
		return true, parts[len(parts)-1]
	}
	return true, v
}

type githubRelease struct {
	TagName string `json:"tag_name"`
}

func fetchLatestVersion(p pluginDef) (string, error) {
	resp, err := http.Get(p.latestURL) //nolint:noctx
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var rel githubRelease
	if err := json.NewDecoder(resp.Body).Decode(&rel); err != nil {
		return "", err
	}
	// Strip leading "v"
	ver := strings.TrimPrefix(rel.TagName, "v")
	return ver, nil
}

func installPlugin(p pluginDef, version string) error {
	goos := runtime.GOOS
	goarch := runtime.GOARCH
	url := p.fetchURL(version, goos, goarch)

	cacheDir := pluginCacheDir(p)
	if err := os.MkdirAll(cacheDir, 0o755); err != nil {
		return err
	}

	fmt.Fprintf(os.Stderr, "==> downloading %s v%s\n", p.Name, version)
	fmt.Fprintf(os.Stderr, "    %s\n", url)

	// Download to temp file
	tmpFile := filepath.Join(cacheDir, p.Name+"-"+version+".tar.gz")
	if err := downloadFile(url, tmpFile); err != nil {
		return fmt.Errorf("download: %w", err)
	}
	defer os.Remove(tmpFile)

	// Extract tar.gz
	fmt.Fprintf(os.Stderr, "==> extracting %s\n", p.Name)
	extractDir := filepath.Join(cacheDir, "tmp-"+version)
	if err := os.MkdirAll(extractDir, 0o755); err != nil {
		return err
	}
	defer os.RemoveAll(extractDir)

	if err := runCmd(cacheDir, "tar", "-xzf", tmpFile, "-C", extractDir, "--strip-components=1"); err != nil {
		return fmt.Errorf("extract: %w", err)
	}

	// Copy binary
	srcBin := filepath.Join(extractDir, p.installBin)
	dstBin := pluginBinPath(p)
	if err := copyExec(srcBin, dstBin); err != nil {
		return fmt.Errorf("install binary: %w", err)
	}

	fmt.Fprintf(os.Stderr, "==> installed %s v%s → %s\n", p.Name, version, dstBin)
	fmt.Fprintf(os.Stderr, "    add to PATH: export PATH=\"%s:$PATH\"\n", pluginCacheDir(p))
	return nil
}

func downloadFile(url, dest string) error {
	resp, err := http.Get(url) //nolint:noctx
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("HTTP %d from %s", resp.StatusCode, url)
	}
	f, err := os.Create(dest)
	if err != nil {
		return err
	}
	defer f.Close()
	_, err = io.Copy(f, resp.Body)
	return err
}

func copyExec(src, dst string) error {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()
	out, err := os.OpenFile(dst, os.O_CREATE|os.O_WRONLY|os.O_TRUNC, 0o755)
	if err != nil {
		return err
	}
	defer out.Close()
	_, err = io.Copy(out, in)
	return err
}

func systemToolVersion(tool string) string {
	var cmd *exec.Cmd
	switch tool {
	case "tinygo":
		cmd = exec.Command(tool, "version")
	case "docker":
		cmd = exec.Command(tool, "--version")
	case "wrangler":
		cmd = exec.Command("npx", "wrangler", "--version")
	default:
		cmd = exec.Command(tool, "--version")
	}
	out, err := cmd.Output()
	if err != nil {
		return "?"
	}
	line := strings.SplitN(strings.TrimSpace(string(out)), "\n", 2)[0]
	parts := strings.Fields(line)
	if len(parts) >= 2 {
		return parts[len(parts)-1]
	}
	return "?"
}
