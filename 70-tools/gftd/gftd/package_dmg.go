package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
)

var packageDMGRunner = runCmd

func runPackageDMG(args []string) error {
	fs := flag.NewFlagSet("package-dmg", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component source directory")
	stagingDir := fs.String("staging-dir", "", "staged desktop bundle directory (default: <dir>/dist-desktop)")
	output := fs.String("output", "", "output dmg path (default: <dir>/dist-desktop/<AppName>.dmg)")
	skipBuild := fs.Bool("skip-build-desktop", false, "skip build-desktop and package existing staged app")
	signIdentity := fs.String("sign-identity", os.Getenv("GFTD_CODESIGN_IDENTITY"), "codesign identity (or $GFTD_CODESIGN_IDENTITY)")
	appleID := fs.String("apple-id", os.Getenv("APPLE_ID"), "Apple ID for notarization (or $APPLE_ID)")
	applePassword := fs.String("apple-password", os.Getenv("APPLE_APP_PASSWORD"), "App-specific password for notarization (or $APPLE_APP_PASSWORD)")
	teamID := fs.String("team-id", os.Getenv("APPLE_TEAM_ID"), "Apple Team ID for notarization (or $APPLE_TEAM_ID)")
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
	distDir := *stagingDir
	if distDir == "" {
		distDir = filepath.Join(compDir, "dist-desktop")
	}
	if !*skipBuild {
		if err := runBuildDesktop([]string{"--dir", compDir, "--output", distDir}); err != nil {
			return err
		}
	}

	plan, err := loadDesktopBuildPlan(filepath.Join(distDir, "desktop-plan.json"))
	if err != nil {
		return err
	}

	if *signIdentity != "" {
		fmt.Fprintf(os.Stderr, "==> codesign %s\n", plan.AppBundlePath)
		if err := packageDMGRunner(compDir, "codesign", "--force", "--deep", "--sign", *signIdentity, plan.AppBundlePath); err != nil {
			return fmt.Errorf("codesign: %w", err)
		}
	} else {
		fmt.Fprintf(os.Stderr, "==> codesign skipped (no signing identity)\n")
	}

	if *appleID != "" && *applePassword != "" && *teamID != "" && *signIdentity != "" {
		fmt.Fprintf(os.Stderr, "==> notarytool submit %s\n", plan.AppBundlePath)
		if err := packageDMGRunner(compDir, "xcrun", "notarytool", "submit", plan.AppBundlePath,
			"--apple-id", *appleID,
			"--password", *applePassword,
			"--team-id", *teamID,
			"--wait",
		); err != nil {
			return fmt.Errorf("notarytool submit: %w", err)
		}
		fmt.Fprintf(os.Stderr, "==> stapler staple %s\n", plan.AppBundlePath)
		if err := packageDMGRunner(compDir, "xcrun", "stapler", "staple", plan.AppBundlePath); err != nil {
			return fmt.Errorf("stapler: %w", err)
		}
	} else {
		fmt.Fprintf(os.Stderr, "==> notarization skipped (set sign identity + APPLE_ID + APPLE_APP_PASSWORD + APPLE_TEAM_ID)\n")
	}

	dmgPath := *output
	if dmgPath == "" {
		dmgPath = filepath.Join(distDir, plan.AppName+".dmg")
	}
	if err := os.RemoveAll(dmgPath); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "==> hdiutil create %s\n", dmgPath)
	if err := packageDMGRunner(compDir, "hdiutil", "create",
		"-volname", plan.AppName,
		"-srcfolder", plan.AppBundlePath,
		"-ov",
		"-format", "UDZO",
		dmgPath,
	); err != nil {
		return fmt.Errorf("hdiutil create: %w", err)
	}

	plan.DMGPath = dmgPath
	if err := saveDesktopBuildPlan(filepath.Join(distDir, "desktop-plan.json"), plan); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "==> packaged dmg: %s\n", dmgPath)
	return nil
}

func loadDesktopBuildPlan(path string) (*desktopBuildPlan, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read desktop plan: %w", err)
	}
	var plan desktopBuildPlan
	if err := json.Unmarshal(data, &plan); err != nil {
		return nil, fmt.Errorf("parse desktop plan: %w", err)
	}
	if plan.AppBundlePath == "" {
		return nil, fmt.Errorf("desktop plan missing appBundlePath: %s", path)
	}
	return &plan, nil
}

func saveDesktopBuildPlan(path string, plan *desktopBuildPlan) error {
	data, err := json.MarshalIndent(plan, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal desktop plan: %w", err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write desktop plan: %w", err)
	}
	return nil
}
