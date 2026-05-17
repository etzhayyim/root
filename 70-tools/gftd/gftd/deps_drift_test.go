package main

import (
	"os"
	"path/filepath"
	"reflect"
	"testing"
)

func TestCollectDepsDriftRespectsDepsIgnoreAndReportsDiffs(t *testing.T) {
	root := t.TempDir()

	writeDepsDriftFile(t, filepath.Join(root, ".depsignore"), "node_modules/\n*.log\n")
	writeDepsDriftFile(t, filepath.Join(root, "deps.toml"), `
[files."README.md"]
role = "doc"

[files."app/*.go"]
role = "code"

[files."LICENSE"]
role = "license"

[subdirs.app]
role = "service"

[subdirs.scripts]
role = "script"
`)
	writeDepsDriftFile(t, filepath.Join(root, "README.md"), "readme\n")
	writeDepsDriftFile(t, filepath.Join(root, "app", "main.go"), "package main\n")
	writeDepsDriftFile(t, filepath.Join(root, "docs", "guide.md"), "# guide\n")
	writeDepsDriftFile(t, filepath.Join(root, "node_modules", "leftpad", "index.js"), "ignored\n")
	writeDepsDriftFile(t, filepath.Join(root, "build.log"), "ignored\n")

	report, err := collectDepsDrift(root)
	if err != nil {
		t.Fatalf("collectDepsDrift(): %v", err)
	}

	if got, want := report.DepsFiles, []string{"deps.toml"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("DepsFiles = %v, want %v", got, want)
	}
	if got, want := report.UndeclaredFiles, []string{"docs/guide.md"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("UndeclaredFiles = %v, want %v", got, want)
	}
	if got, want := report.UndeclaredDirs, []string{"docs"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("UndeclaredDirs = %v, want %v", got, want)
	}
	if got, want := report.MissingFiles, []string{"LICENSE"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("MissingFiles = %v, want %v", got, want)
	}
	if got, want := report.MissingDirs, []string{"scripts"}; !reflect.DeepEqual(got, want) {
		t.Fatalf("MissingDirs = %v, want %v", got, want)
	}
}

func TestCollectDepsDriftTreatsDirectoryFileEntriesAsCoveredDirs(t *testing.T) {
	root := t.TempDir()

	writeDepsDriftFile(t, filepath.Join(root, ".depsignore"), "")
	writeDepsDriftFile(t, filepath.Join(root, "deps.toml"), `
[files."scripts"]
role = "tooling"
`)
	writeDepsDriftFile(t, filepath.Join(root, "scripts", "lint.sh"), "#!/bin/sh\n")

	report, err := collectDepsDrift(root)
	if err != nil {
		t.Fatalf("collectDepsDrift(): %v", err)
	}

	if len(report.MissingFiles) != 0 {
		t.Fatalf("MissingFiles = %v, want none", report.MissingFiles)
	}
	if len(report.UndeclaredFiles) != 0 {
		t.Fatalf("UndeclaredFiles = %v, want none", report.UndeclaredFiles)
	}
	if got, want := report.CoveredFiles, 1; got != want {
		t.Fatalf("CoveredFiles = %d, want %d", got, want)
	}
	if len(report.UndeclaredDirs) != 0 {
		t.Fatalf("UndeclaredDirs = %v, want none", report.UndeclaredDirs)
	}
}

func writeDepsDriftFile(t *testing.T, path, content string) {
	t.Helper()
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		t.Fatalf("MkdirAll(%s): %v", path, err)
	}
	if err := os.WriteFile(path, []byte(content), 0o644); err != nil {
		t.Fatalf("WriteFile(%s): %v", path, err)
	}
}
