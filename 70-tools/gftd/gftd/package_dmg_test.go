package main

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadAndSaveDesktopBuildPlan(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "desktop-plan.json")
	plan := &desktopBuildPlan{
		AppName:       "Disk Cleaner",
		AppBundlePath: "/tmp/Disk Cleaner.app",
	}
	if err := saveDesktopBuildPlan(path, plan); err != nil {
		t.Fatalf("saveDesktopBuildPlan: %v", err)
	}
	got, err := loadDesktopBuildPlan(path)
	if err != nil {
		t.Fatalf("loadDesktopBuildPlan: %v", err)
	}
	if got.AppName != plan.AppName || got.AppBundlePath != plan.AppBundlePath {
		t.Fatalf("got %+v", got)
	}
}

func TestRunPackageDMGSkipsSigningAndNotarizationWithoutCredentials(t *testing.T) {
	dir := t.TempDir()
	appDir := filepath.Join(dir, "dist-desktop", "Disk Cleaner.app")
	if err := os.MkdirAll(appDir, 0o755); err != nil {
		t.Fatalf("mkdir app: %v", err)
	}
	if err := saveDesktopBuildPlan(filepath.Join(dir, "dist-desktop", "desktop-plan.json"), &desktopBuildPlan{
		AppName:       "Disk Cleaner",
		AppBundlePath: appDir,
	}); err != nil {
		t.Fatalf("saveDesktopBuildPlan: %v", err)
	}

	calls := 0
	prev := packageDMGRunner
	packageDMGRunner = func(_ string, name string, args ...string) error {
		calls++
		if name != "hdiutil" {
			t.Fatalf("unexpected command %s %v", name, args)
		}
		out := args[len(args)-1]
		return os.WriteFile(out, []byte("dmg"), 0o644)
	}
	defer func() { packageDMGRunner = prev }()

	if err := runPackageDMG([]string{"--dir", dir, "--skip-build-desktop"}); err != nil {
		t.Fatalf("runPackageDMG: %v", err)
	}
	if calls != 1 {
		t.Fatalf("expected 1 command call, got %d", calls)
	}
}
