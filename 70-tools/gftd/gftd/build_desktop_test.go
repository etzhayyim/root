package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func TestStageDesktopAppCreatesBundle(t *testing.T) {
	dir := t.TempDir()
	writeTestFile(t, filepath.Join(dir, "magatama.jsonld"), `{
  "@context": "https://etzhayyim.com/ns/magatama/v1",
  "name": "disk-cleaner",
  "nanoid": "dcscan01",
  "runtimeType": "desktop-wasm",
  "component": { "path": "build/component.wasm" },
  "desktop": {
    "bundleId": "jp.co.gftd.disk-cleaner",
    "window": { "title": "Disk Cleaner" }
  }
}`)
	writeTestFile(t, filepath.Join(dir, "build", "component.wasm"), "wasm")

	cfg, err := readMagatamaJSONLD(dir)
	if err != nil {
		t.Fatalf("readMagatamaJSONLD: %v", err)
	}

	hostBinary := filepath.Join(dir, "magatama-desktop-host")
	writeTestFile(t, hostBinary, "host")

	outDir := filepath.Join(dir, "dist-desktop")
	plan, err := stageDesktopApp(dir, outDir, cfg, hostBinary)
	if err != nil {
		t.Fatalf("stageDesktopApp: %v", err)
	}

	if _, err := os.Stat(filepath.Join(plan.AppBundlePath, "Contents", "Info.plist")); err != nil {
		t.Fatalf("missing Info.plist: %v", err)
	}
	if _, err := os.Stat(filepath.Join(plan.AppBundlePath, "Contents", "Resources", "component.wasm")); err != nil {
		t.Fatalf("missing staged guest: %v", err)
	}
	if _, err := os.Stat(filepath.Join(plan.AppBundlePath, "Contents", "MacOS", "Disk_Cleaner")); err != nil {
		t.Fatalf("missing host binary: %v", err)
	}
}

func TestSanitizeDesktopExecutableName(t *testing.T) {
	got := sanitizeDesktopExecutableName("Disk Cleaner Preview")
	if got != "Disk_Cleaner_Preview" {
		t.Fatalf("got %q", got)
	}
}

func TestBundleIDOrDefault(t *testing.T) {
	cfg := &magatamaJSONLD{Nanoid: "abc123"}
	if got := cfg.BundleIDOrDefault(); got != "jp.co.gftd.abc123" {
		t.Fatalf("got %q", got)
	}
}

func TestWriteDesktopHostConfigMentionsGuestPath(t *testing.T) {
	dir := t.TempDir()
	cfg := &magatamaJSONLD{Name: "demo", Nanoid: "demo1", RuntimeType: "desktop-wasm"}
	resourcesDir := filepath.Join(dir, "Demo.app", "Contents", "Resources")
	if err := os.MkdirAll(resourcesDir, 0o755); err != nil {
		t.Fatalf("mkdir: %v", err)
	}
	target := filepath.Join(resourcesDir, "host-config.json")
	guest := filepath.Join(resourcesDir, "component.wasm")
	if _, err := writeDesktopHostConfig(target, cfg, "Demo", guest, resourcesDir); err != nil {
		t.Fatalf("writeDesktopHostConfig: %v", err)
	}
	data, err := os.ReadFile(target)
	if err != nil {
		t.Fatalf("read host config: %v", err)
	}
	var decoded map[string]any
	if err := json.Unmarshal(data, &decoded); err != nil {
		t.Fatalf("unmarshal host config: %v", err)
	}
	if decoded["guest_relative_path"] != "component.wasm" {
		t.Fatalf("host config missing guest path: %s", string(data))
	}
}
