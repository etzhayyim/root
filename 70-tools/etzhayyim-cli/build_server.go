package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"time"
)

const (
	defaultServerImage = "ghcr.io/etzhayyim/kotodama-server"
	defaultTarget      = "x86_64-unknown-linux-gnu"
)

func runBuildServer(args []string) error {
	fs := flag.NewFlagSet("build-server", flag.ContinueOnError)
	image := fs.String("image", defaultServerImage, "docker image name")
	tag := fs.String("tag", "", "image tag (default: timestamped)")
	push := fs.Bool("push", false, "push image after build")
	target := fs.String("target", defaultTarget, "Rust cross-compile target triple")
	witVersion := fs.String("wit-version", "", "override WIT package version (e.g. 0.1.0) for backward compat; restored after build")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	// Locate packages/rust directory (build context root)
	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("cannot get working directory: %w", err)
	}
	gitRoot, err := findGitRoot(cwd)
	if err != nil {
		return fmt.Errorf("cannot find git root: %w", err)
	}
	rustDir := filepath.Join(gitRoot, "packages", "rust")
	kotodamaDir := filepath.Join(rustDir, "kotodama")

	if _, err := os.Stat(kotodamaDir); err != nil {
		return fmt.Errorf("kotodama workspace not found at %s", kotodamaDir)
	}

	// Resolve tag — always timestamped (never `latest`)
	resolvedTag := *tag
	if resolvedTag == "" {
		resolvedTag = time.Now().Format("20060102-150405")
	}
	fullImage := *image + ":" + resolvedTag

	// WIT version override: temporarily patch kotodama.wit, restore after build.
	witFile := filepath.Join(kotodamaDir, "wit", "kotodama.wit")
	if *witVersion != "" {
		origBytes, err := os.ReadFile(witFile)
		if err != nil {
			return fmt.Errorf("read WIT file: %w", err)
		}
		defer func() {
			os.WriteFile(witFile, origBytes, 0644)
			fmt.Fprintf(os.Stderr, "==> WIT version restored\n")
		}()
		patched := replaceWITVersion(string(origBytes), *witVersion)
		if err := os.WriteFile(witFile, []byte(patched), 0644); err != nil {
			return fmt.Errorf("patch WIT file: %w", err)
		}
		fmt.Fprintf(os.Stderr, "==> WIT version overridden to %s (will restore after build)\n", *witVersion)
	}

	return buildServerZigbuild(kotodamaDir, rustDir, fullImage, *target, *push)
}

// buildServerZigbuild uses `cargo zigbuild` to natively cross-compile for amd64, then builds a minimal Docker image.
func buildServerZigbuild(kotodamaDir, rustDir, fullImage, target string, push bool) error {
	// Step 1: cargo zigbuild (sccache enabled via env)
	fmt.Fprintf(os.Stderr, "==> RUSTC_WRAPPER=sccache cargo zigbuild --release --target %s -p kotodama-server\n", target)
	os.Setenv("RUSTC_WRAPPER", "sccache")
	if err := runCmd(kotodamaDir, "cargo", "zigbuild",
		"--release",
		"--target", target,
		"-p", "kotodama-server",
	); err != nil {
		return fmt.Errorf("cargo zigbuild failed: %w", err)
	}

	// Step 2: Locate binary
	binaryPath := filepath.Join(kotodamaDir, "target", target, "release", "kotodama-server")
	if _, err := os.Stat(binaryPath); err != nil {
		return fmt.Errorf("binary not found at %s", binaryPath)
	}
	info, _ := os.Stat(binaryPath)
	fmt.Fprintf(os.Stderr, "==> binary: %s (%.1f MB)\n", binaryPath, float64(info.Size())/(1024*1024))

	// Step 3: Docker build with Dockerfile (expects binary at fixed path)
	dockerfilePath := filepath.Join(kotodamaDir, "kotodama-server", "Dockerfile")
	if _, err := os.Stat(dockerfilePath); err != nil {
		return fmt.Errorf("Dockerfile not found: %s", dockerfilePath)
	}

	fmt.Fprintf(os.Stderr, "==> docker build %s (from pre-built binary)\n", fullImage)
	buildArgs := []string{
		"buildx", "build",
		"--platform", "linux/amd64",
		"-f", dockerfilePath,
		"-t", fullImage,
	}
	if push {
		buildArgs = append(buildArgs, "--push")
	} else {
		buildArgs = append(buildArgs, "--load")
	}
	buildArgs = append(buildArgs, ".")

	if err := runCmd(rustDir, "docker", buildArgs...); err != nil {
		return fmt.Errorf("docker build: %w", err)
	}

	fmt.Fprintf(os.Stderr, "==> built %s\n", fullImage)
	return nil
}

var witVersionRe = regexp.MustCompile(`package kotodama:runtime@\d+\.\d+\.\d+;`)

func replaceWITVersion(content, version string) string {
	return witVersionRe.ReplaceAllString(content, "package kotodama:runtime@"+version+";")
}
