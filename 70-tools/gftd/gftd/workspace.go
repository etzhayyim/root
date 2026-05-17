package main

import (
	"errors"
	"flag"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

func runWorkspace(args []string) error {
	if len(args) == 0 {
		printWorkspaceUsage()
		return nil
	}

	switch args[0] {
	case "sync":
		return runWorkspaceSync(args[1:])
	case "help", "--help", "-h":
		printWorkspaceUsage()
		return nil
	default:
		return fmt.Errorf("unknown workspace command: %s", args[0])
	}
}

func printWorkspaceUsage() {
	fmt.Printf(`gftd workspace — workspace-level utilities

USAGE:
  gftd workspace <command> [flags]

COMMANDS:
  sync               Sync workspace directory with a remote host via rsync over SSH

Run 'gftd workspace <command> --help' for command-specific flags.
`)
}

func runWorkspaceSync(args []string) error {
	fs := flag.NewFlagSet("workspace sync", flag.ContinueOnError)
	dir := fs.String("dir", ".", "local workspace directory (default: current dir)")
	host := fs.String("host", "", "remote SSH host in user@host form")
	remotePath := fs.String("remote-path", "", "absolute remote path for the workspace")
	direction := fs.String("direction", "push", "sync direction: push or pull")
	dryRun := fs.Bool("dry-run", false, "show changes without transferring data")
	noDelete := fs.Bool("no-delete", false, "do not delete files that are absent on the source side")
	includeEnv := fs.Bool("include-env", false, "include .env in sync")
	rsyncRSH := fs.String("rsync-rsh", "", "custom remote shell command, e.g. 'ssh -F ~/.ssh/config'")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	if *host == "" {
		return errors.New("--host is required")
	}
	if *remotePath == "" {
		return errors.New("--remote-path is required")
	}
	if !filepath.IsAbs(*remotePath) {
		return fmt.Errorf("--remote-path must be absolute: %s", *remotePath)
	}

	localDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}
	info, err := os.Stat(localDir)
	if err != nil {
		return fmt.Errorf("local workspace not accessible: %w", err)
	}
	if !info.IsDir() {
		return fmt.Errorf("local workspace is not a directory: %s", localDir)
	}

	if _, err := exec.LookPath("rsync"); err != nil {
		return errors.New("rsync not found in PATH")
	}
	if _, err := exec.LookPath("ssh"); err != nil {
		return errors.New("ssh not found in PATH")
	}

	resolvedDirection := strings.ToLower(strings.TrimSpace(*direction))
	if resolvedDirection != "push" && resolvedDirection != "pull" {
		return fmt.Errorf("--direction must be push or pull: %s", *direction)
	}

	gitRoot, err := findGitRoot(localDir)
	if err != nil {
		return fmt.Errorf("cannot find git root from %s: %w", localDir, err)
	}
	excludeFile := filepath.Join(gitRoot, ".rsync-exclude")

	sshCheckRSH := strings.TrimSpace(*rsyncRSH)
	if sshCheckRSH == "" {
		sshCheckRSH = "ssh"
	}

	if err := ensureWorkspaceSSH(*host, *remotePath, sshCheckRSH); err != nil {
		return err
	}

	rsyncArgs := []string{
		"--archive",
		"--human-readable",
		"--compress",
		"--itemize-changes",
		"--partial",
		"--protect-args",
	}
	if !*noDelete {
		rsyncArgs = append(rsyncArgs, "--delete")
	}
	if *dryRun {
		rsyncArgs = append(rsyncArgs, "--dry-run")
	}
	if *rsyncRSH != "" {
		rsyncArgs = append(rsyncArgs, "-e", *rsyncRSH)
	}
	if stat, err := os.Stat(excludeFile); err == nil && !stat.IsDir() {
		rsyncArgs = append(rsyncArgs, "--exclude-from", excludeFile)
	}
	if *includeEnv {
		rsyncArgs = append(rsyncArgs, "--include=.env")
	}

	localSrc := ensureTrailingSlash(localDir)
	remoteTarget := fmt.Sprintf("%s:%s/", *host, *remotePath)
	if resolvedDirection == "pull" {
		localDst := ensureTrailingSlash(localDir)
		return runCmd(gitRoot, "rsync", append(rsyncArgs, remoteTarget, localDst)...)
	}
	return runCmd(gitRoot, "rsync", append(rsyncArgs, localSrc, remoteTarget)...)
}

func ensureWorkspaceSSH(host, remotePath, rsh string) error {
	sshArgs, err := splitShellWords(rsh)
	if err != nil {
		return fmt.Errorf("parse --rsync-rsh: %w", err)
	}
	if len(sshArgs) == 0 {
		return errors.New("empty remote shell command")
	}

	if filepath.Base(sshArgs[0]) != "ssh" {
		return nil
	}

	sshArgs = append(sshArgs,
		"-o", "BatchMode=yes",
		"-o", "ConnectTimeout=5",
		host,
		fmt.Sprintf("mkdir -p %q", remotePath),
	)
	cmd := exec.Command(sshArgs[0], sshArgs[1:]...)
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("ssh connectivity check failed: %w", err)
	}
	return nil
}

func ensureTrailingSlash(path string) string {
	if strings.HasSuffix(path, string(os.PathSeparator)) {
		return path
	}
	return path + string(os.PathSeparator)
}

func splitShellWords(s string) ([]string, error) {
	var args []string
	var current strings.Builder
	var quote rune
	escaped := false

	for _, r := range s {
		switch {
		case escaped:
			current.WriteRune(r)
			escaped = false
		case r == '\\':
			escaped = true
		case quote != 0:
			if r == quote {
				quote = 0
			} else {
				current.WriteRune(r)
			}
		case r == '\'' || r == '"':
			quote = r
		case r == ' ' || r == '\t' || r == '\n':
			if current.Len() > 0 {
				args = append(args, current.String())
				current.Reset()
			}
		default:
			current.WriteRune(r)
		}
	}

	if escaped {
		return nil, errors.New("unterminated escape")
	}
	if quote != 0 {
		return nil, errors.New("unterminated quote")
	}
	if current.Len() > 0 {
		args = append(args, current.String())
	}
	return args, nil
}
