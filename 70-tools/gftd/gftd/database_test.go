package main

import (
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"testing"
)

func TestResolveDatabaseURL(t *testing.T) {
	t.Setenv("DATABASE_URL", "")
	cases := []struct {
		name    string
		urlFlag string
		env     string
		envVar  string
		want    string
		wantErr bool
	}{
		{"url flag wins over env var", "postgres://flag", "local", "postgres://envvar", "postgres://flag", false},
		{"env var wins over preset", "", "prod", "postgres://envvar", "postgres://envvar", false},
		{"local preset", "", "local", "", rwLocalURL, false},
		{"prod preset", "", "prod", "", rwProdURL, false},
		{"unknown env rejected", "", "staging", "", "", true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			t.Setenv("DATABASE_URL", tc.envVar)
			got, err := resolveDatabaseURL(tc.urlFlag, tc.env)
			if tc.wantErr {
				if err == nil {
					t.Fatalf("want error, got %q", got)
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if got != tc.want {
				t.Fatalf("want %q, got %q", tc.want, got)
			}
		})
	}
}

func TestValidateMigratorArgs(t *testing.T) {
	cases := []struct {
		name    string
		args    []string
		wantErr bool
	}{
		{"empty ok", nil, false},
		{"latest ok", []string{"latest"}, false},
		{"up ok", []string{"up"}, false},
		{"down ok", []string{"down"}, false},
		{"list ok", []string{"list"}, false},
		{"to with target ok", []string{"to", "0005_vertex_gitrepo"}, false},
		{"to without target rejected", []string{"to"}, true},
		{"unknown subcommand rejected", []string{"reset"}, true},
		{"latest with extra args rejected", []string{"latest", "oops"}, true},
	}
	for _, tc := range cases {
		t.Run(tc.name, func(t *testing.T) {
			err := validateMigratorArgs(tc.args)
			if tc.wantErr && err == nil {
				t.Fatalf("want error, got nil")
			}
			if !tc.wantErr && err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
		})
	}
}

func TestRedactURL(t *testing.T) {
	cases := []struct {
		in, want string
	}{
		{"postgres://root:secret@host:4566/dev", "postgres://root@host:4566/dev"},
		{"postgres://root@host:4566/dev", "postgres://root@host:4566/dev"},
		{"postgres://root:pw@host/db", "postgres://root@host/db"},
		{"not-a-url", "not-a-url"},
		{"", ""},
	}
	for _, tc := range cases {
		t.Run(tc.in, func(t *testing.T) {
			got := redactURL(tc.in)
			if got != tc.want {
				t.Fatalf("redactURL(%q) = %q, want %q", tc.in, got, tc.want)
			}
		})
	}
}

// TestRunKyselyMigrate_ExecsNodeWithCorrectContext is the integration test:
// it stands up a fake monorepo layout in a temp dir, puts a `node` shim on
// PATH that captures argv + env + cwd, then invokes runKyselyMigrate and
// asserts the shim was called with the expected positional args, DATABASE_URL,
// and working directory. This exercises the real flag parsing, path
// resolution, findGitRoot walk, and runCmdEnv shell-out path.
func TestRunKyselyMigrate_ExecsNodeWithCorrectContext(t *testing.T) {
	if runtime.GOOS == "windows" {
		t.Skip("node shim uses /bin/sh; skip on windows")
	}

	tmp := t.TempDir()

	// Fake monorepo root: .git + 30-graph/graph-schema/scripts/migrate.ts
	mustMkdir(t, filepath.Join(tmp, ".git"))
	schemaDir := filepath.Join(tmp, graphSchemaRel, "scripts")
	mustMkdir(t, schemaDir)
	writeTestFile(t, filepath.Join(schemaDir, "migrate.ts"), "// fake runner\n")

	// node shim: captures argv + DATABASE_URL + PWD to a file we can read.
	shimDir := filepath.Join(tmp, "bin")
	mustMkdir(t, shimDir)
	capturePath := filepath.Join(tmp, "capture.txt")
	shim := `#!/bin/sh
{
  echo "PWD=$PWD"
  echo "DATABASE_URL=$DATABASE_URL"
  echo "ARGS=$*"
} > "` + capturePath + `"
exit 0
`
	nodePath := filepath.Join(shimDir, "node")
	writeTestFile(t, nodePath, shim)
	if err := os.Chmod(nodePath, 0o755); err != nil {
		t.Fatalf("chmod shim: %v", err)
	}

	// Put shim on PATH (front), chdir into the fake repo so findGitRoot(".") hits it.
	t.Setenv("PATH", shimDir+string(os.PathListSeparator)+os.Getenv("PATH"))
	t.Setenv("DATABASE_URL", "")
	origWD, err := os.Getwd()
	if err != nil {
		t.Fatalf("getwd: %v", err)
	}
	t.Cleanup(func() { _ = os.Chdir(origWD) })
	if err := os.Chdir(tmp); err != nil {
		t.Fatalf("chdir tmp: %v", err)
	}

	// Invoke with an explicit URL + `to <name>` to exercise arg pass-through.
	args := []string{"--url", "postgres://root:hunter2@fakehost:4566/dev", "to", "0005_vertex_gitrepo"}
	if err := runKyselyMigrate(args, []string{"latest"}); err != nil {
		t.Fatalf("runKyselyMigrate: %v", err)
	}

	capture, err := os.ReadFile(capturePath)
	if err != nil {
		t.Fatalf("read capture: %v", err)
	}
	got := string(capture)

	wantPWD := "PWD=" + filepath.Join(tmp, graphSchemaRel)
	if !strings.Contains(got, wantPWD) {
		// macOS /var vs /private/var symlink: also accept the evaluated form.
		evalPWD, _ := filepath.EvalSymlinks(filepath.Join(tmp, graphSchemaRel))
		if !strings.Contains(got, "PWD="+evalPWD) {
			t.Errorf("cwd mismatch:\nwant %s\n got %s", wantPWD, got)
		}
	}
	if !strings.Contains(got, "DATABASE_URL=postgres://root:hunter2@fakehost:4566/dev") {
		t.Errorf("DATABASE_URL not propagated:\n%s", got)
	}
	if !strings.Contains(got, "--loader=ts-node/esm") {
		t.Errorf("ts-node loader flag missing:\n%s", got)
	}
	if !strings.Contains(got, "scripts/migrate.ts to 0005_vertex_gitrepo") {
		t.Errorf("migrator args not forwarded:\n%s", got)
	}
}

func TestRunKyselyMigrate_RejectsUnknownSubcommand(t *testing.T) {
	tmp := t.TempDir()
	mustMkdir(t, filepath.Join(tmp, ".git"))
	mustMkdir(t, filepath.Join(tmp, graphSchemaRel, "scripts"))
	writeTestFile(t, filepath.Join(tmp, graphSchemaRel, "scripts", "migrate.ts"), "")

	origWD, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(origWD) })
	if err := os.Chdir(tmp); err != nil {
		t.Fatalf("chdir: %v", err)
	}
	t.Setenv("DATABASE_URL", "postgres://x")

	err := runKyselyMigrate([]string{"reset"}, []string{"latest"})
	if err == nil || !strings.Contains(err.Error(), "unknown migrator subcommand") {
		t.Fatalf("want unknown-subcommand error, got %v", err)
	}
}

func TestRunKyselyMigrate_MissingRunnerIsReported(t *testing.T) {
	tmp := t.TempDir()
	mustMkdir(t, filepath.Join(tmp, ".git"))
	// intentionally do NOT create scripts/migrate.ts

	origWD, _ := os.Getwd()
	t.Cleanup(func() { _ = os.Chdir(origWD) })
	if err := os.Chdir(tmp); err != nil {
		t.Fatalf("chdir: %v", err)
	}
	t.Setenv("DATABASE_URL", "postgres://x")

	err := runKyselyMigrate(nil, []string{"latest"})
	if err == nil || !strings.Contains(err.Error(), "kysely migrate runner not found") {
		t.Fatalf("want missing-runner error, got %v", err)
	}
}

func mustMkdir(t *testing.T, path string) {
	t.Helper()
	if err := os.MkdirAll(path, 0o755); err != nil {
		t.Fatalf("mkdir %s: %v", path, err)
	}
}
