package main

import (
	"crypto/md5"
	"encoding/hex"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"time"
)

const (
	defaultServerImage = "ghcr.io/etzhayyim/magatama-server"
	defaultTarget      = "x86_64-unknown-linux-gnu"
)

func runBuildContainer(args []string) error {
	fs := flag.NewFlagSet("build-container", flag.ContinueOnError)
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

	// Locate 20-actors/magatama directory (build context root)
	cwd, err := os.Getwd()
	if err != nil {
		return fmt.Errorf("cannot get working directory: %w", err)
	}
	gitRoot, err := findGitRoot(cwd)
	if err != nil {
		return fmt.Errorf("cannot find git root: %w", err)
	}
	rustDir := filepath.Join(gitRoot, "20-actors")
	magatamaDir := filepath.Join(rustDir, "magatama")

	if _, err := os.Stat(magatamaDir); err != nil {
		return fmt.Errorf("magatama workspace not found at %s", magatamaDir)
	}

	// Resolve tag — always timestamped (never `latest`)
	resolvedTag := *tag
	if resolvedTag == "" {
		resolvedTag = time.Now().Format("20060102-150405")
	}
	fullImage := *image + ":" + resolvedTag

	// WIT version override: temporarily patch magatama.wit, restore after build.
	witFile := filepath.Join(magatamaDir, "wit", "magatama.wit")
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

	return buildContainerZigbuild(magatamaDir, rustDir, fullImage, *target, *push)
}

// buildContainerZigbuild uses `cargo zigbuild` to natively cross-compile for amd64, then builds a minimal Docker image.
func buildContainerZigbuild(magatamaDir, rustDir, fullImage, target string, push bool) error {
	// Step 1: cargo zigbuild (sccache enabled via env)
	fmt.Fprintf(os.Stderr, "==> RUSTC_WRAPPER=sccache cargo zigbuild --release --target %s -p magatama-server\n", target)
	os.Setenv("RUSTC_WRAPPER", "sccache")
	if err := runCmd(magatamaDir, "cargo", "zigbuild",
		"--release",
		"--target", target,
		"-p", "magatama-server",
	); err != nil {
		return fmt.Errorf("cargo zigbuild failed: %w", err)
	}

	// Step 2: Locate binary — check .cargo-target/ (repo shared) first, then magatama/target/
	gitRoot := filepath.Dir(rustDir)
	candidatePaths := []string{
		filepath.Join(gitRoot, ".cargo-target", target, "release", "magatama-server"),
		filepath.Join(magatamaDir, "target", target, "release", "magatama-server"),
	}
	var binaryPath string
	for _, p := range candidatePaths {
		if _, err := os.Stat(p); err == nil {
			binaryPath = p
			break
		}
	}
	if binaryPath == "" {
		return fmt.Errorf("binary not found at any of: %v", candidatePaths)
	}

	// Copy to expected Docker COPY path if needed (Dockerfile expects magatama/target/)
	expectedPath := filepath.Join(magatamaDir, "target", target, "release", "magatama-server")
	if binaryPath != expectedPath {
		if err := os.MkdirAll(filepath.Dir(expectedPath), 0755); err != nil {
			return fmt.Errorf("mkdir for binary copy: %w", err)
		}
		src, err := os.ReadFile(binaryPath)
		if err != nil {
			return fmt.Errorf("read binary: %w", err)
		}
		if err := os.WriteFile(expectedPath, src, 0755); err != nil {
			return fmt.Errorf("copy binary: %w", err)
		}
		fmt.Fprintf(os.Stderr, "==> copied binary from %s → %s\n", binaryPath, expectedPath)
		binaryPath = expectedPath
	}

	info, _ := os.Stat(binaryPath)
	fmt.Fprintf(os.Stderr, "==> binary: %s (%.1f MB)\n", binaryPath, float64(info.Size())/(1024*1024))

	// Print binary hash for verification
	hashBytes, _ := os.ReadFile(binaryPath)
	if len(hashBytes) > 0 {
		h := md5Hash(hashBytes)
		fmt.Fprintf(os.Stderr, "==> binary hash: %s\n", h)
	}

	// Step 3: Docker build with Dockerfile (expects binary at fixed path)
	dockerfilePath := filepath.Join(magatamaDir, "magatama-server", "Dockerfile")
	if _, err := os.Stat(dockerfilePath); err != nil {
		return fmt.Errorf("Dockerfile not found: %s", dockerfilePath)
	}

	builder := os.Getenv("BUILDKIT_BUILDER")
	if builder == "" {
		builder = "gftd-vke"
	}
	cacheRef := os.Getenv("BUILDKIT_CACHE_REF")
	if cacheRef == "" {
		cacheRef = "ghcr.io/etzhayyim/build-cache:magatama-server"
	}

	fmt.Fprintf(os.Stderr, "==> docker buildx remote build %s (builder=%s, cache=%s, from pre-built binary)\n", fullImage, builder, cacheRef)
	buildArgs := []string{
		"buildx", "build",
		"--builder", builder,
		"--platform", "linux/amd64",
		"--cache-from", "type=registry,ref=" + cacheRef,
		"--cache-to", "type=registry,ref=" + cacheRef + ",mode=max",
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

var witVersionRe = regexp.MustCompile(`package magatama:runtime@\d+\.\d+\.\d+;`)

func replaceWITVersion(content, version string) string {
	return witVersionRe.ReplaceAllString(content, "package magatama:runtime@"+version+";")
}

func md5Hash(data []byte) string {
	h := md5.Sum(data)
	return hex.EncodeToString(h[:])
}
