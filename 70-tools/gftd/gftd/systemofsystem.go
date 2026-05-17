package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

// --- systemofsystem data model ---

type sosSystem struct {
	ID           string            `json:"id"`
	Name         string            `json:"name,omitempty"`
	SystemType   string            `json:"system_type"` // control, runtime, infra, project, ops, data
	Layer        string            `json:"layer,omitempty"`
	Path         string            `json:"path,omitempty"`
	Apps         []string          `json:"apps,omitempty"`
	AppCount     int               `json:"app_count"`
	Deployed     int               `json:"deployed"`
	EdgeCount    int               `json:"edge_count"`
	Technologies []string          `json:"technologies,omitempty"`
	VersionHints map[string]string `json:"version_hints,omitempty"`
	Signals      []string          `json:"signals,omitempty"`
}

type sosInterface struct {
	From        string `json:"from"`
	To          string `json:"to"`
	Protocol    string `json:"protocol"` // workers_rpc, xrpc, http, subscribe_repos
	EdgeCount   int    `json:"edge_count"`
	Latency     string `json:"latency,omitempty"`
	Description string `json:"description,omitempty"`
}

type sosLayer struct {
	Name    string   `json:"name"`
	Systems []string `json:"systems"`
}

type sosStats struct {
	TotalSystems     int     `json:"total_systems"`
	TotalInterfaces  int     `json:"total_interfaces"`
	TotalApps        int     `json:"total_apps"`
	DeployedApps     int     `json:"deployed_apps"`
	OrphanApps       int     `json:"orphan_apps"`
	ProjectSystems   int     `json:"project_systems"`
	RepoSystems      int     `json:"repo_systems"`
	WorkflowCount    int     `json:"workflow_count"`
	PackageJSONCount int     `json:"package_json_count"`
	DockerfileCount  int     `json:"dockerfile_count"`
	CouplingScore    float64 `json:"coupling_score"`
	CohesionScore    float64 `json:"cohesion_score"`
}

type sosInventory struct {
	Lockfiles           []string                  `json:"lockfiles,omitempty"`
	RuntimeVersions     map[string]string         `json:"runtime_versions,omitempty"`
	PackageJSONCount    int                       `json:"package_json_count"`
	WorkflowCount       int                       `json:"workflow_count"`
	DockerfileCount     int                       `json:"dockerfile_count"`
	ReportFileCount     int                       `json:"report_file_count"`
	DeployStateFiles    int                       `json:"deploy_state_files"`
	ProjectPackageCount map[string]int            `json:"project_package_count,omitempty"`
	ProjectDockerCount  map[string]int            `json:"project_docker_count,omitempty"`
	ProjectRuntimeCount map[string]map[string]int `json:"project_runtime_count,omitempty"`
	ProjectUICount      map[string]map[string]int `json:"project_ui_count,omitempty"`
	WorkspacePackages   map[string]int            `json:"workspace_packages,omitempty"`
}

type sosReport struct {
	GeneratedAt string         `json:"generated_at"`
	Systems     []sosSystem    `json:"systems"`
	Interfaces  []sosInterface `json:"interfaces"`
	Layers      []sosLayer     `json:"layers"`
	Stats       sosStats       `json:"stats"`
	Inventory   sosInventory   `json:"inventory"`
}

type sosPackageJSON struct {
	Name            string            `json:"name"`
	PackageManager  string            `json:"packageManager"`
	Dependencies    map[string]string `json:"dependencies"`
	DevDependencies map[string]string `json:"devDependencies"`
}

// --- entry point ---

func runSystemOfSystem(args []string) error {
	if len(args) == 0 {
		printSoSUsage()
		return nil
	}
	switch args[0] {
	case "scan":
		return runSoSScan(args[1:])
	case "layers":
		return runSoSLayers(args[1:])
	case "interfaces":
		return runSoSInterfaces(args[1:])
	case "health":
		return runSoSHealth(args[1:])
	case "help", "--help", "-h":
		printSoSUsage()
		return nil
	default:
		return fmt.Errorf("unknown systemofsystem command: %s", args[0])
	}
}

func printSoSUsage() {
	fmt.Print(`gftd systemofsystem — System-of-Systems overview (DoDAF SV-1)

USAGE:
  gftd systemofsystem <command> [flags]

COMMANDS:
  scan         Full SoS report → JSON (systems, interfaces, layers, stats)
  layers       Layer-by-layer summary (edge, infra, app, data)
  interfaces   System-to-system interface list
  health       Deploy state + orphan count + coupling/cohesion scores

4-LAYER MODEL:
  edge       account-level Workers (direct route *.etzhayyim.com)
  infra      pds, yata, yoro, repo, murakumo, maps
  app        account-level Workers (magatama-{nanoid})
  data       R2 (Lance fragments, git repos, CDN)

Run 'gftd systemofsystem <command> --help' for command-specific flags.
`)
}

// --- scan command ---

func runSoSScan(args []string) error {
	fs := flag.NewFlagSet("systemofsystem scan", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	report := sosBuildReport(wsRoot)

	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	return enc.Encode(report)
}

// --- layers command ---

func runSoSLayers(args []string) error {
	fs := flag.NewFlagSet("systemofsystem layers", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	report := sosBuildReport(wsRoot)

	for _, layer := range report.Layers {
		fmt.Printf("[%s]\n", layer.Name)
		for _, sys := range layer.Systems {
			// find system details
			for _, s := range report.Systems {
				if s.ID == sys {
					fmt.Printf("  %-20s  apps: %d  deployed: %d  edges: %d\n", s.ID, s.AppCount, s.Deployed, s.EdgeCount)
					break
				}
			}
		}
		fmt.Println()
	}
	return nil
}

// --- interfaces command ---

func runSoSInterfaces(args []string) error {
	fs := flag.NewFlagSet("systemofsystem interfaces", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	report := sosBuildReport(wsRoot)

	fmt.Printf("%-20s ──> %-20s  protocol: %-16s  edges: %s\n", "FROM", "TO", "PROTOCOL", "COUNT")
	fmt.Println(strings.Repeat("─", 80))
	for _, iface := range report.Interfaces {
		latency := ""
		if iface.Latency != "" {
			latency = " (" + iface.Latency + ")"
		}
		fmt.Printf("%-20s ──> %-20s  protocol: %-16s  edges: %d%s\n",
			iface.From, iface.To, iface.Protocol, iface.EdgeCount, latency)
	}
	return nil
}

// --- health command ---

func runSoSHealth(args []string) error {
	fs := flag.NewFlagSet("systemofsystem health", flag.ContinueOnError)
	wsDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveWSRoot(*wsDir)
	if err != nil {
		return err
	}

	report := sosBuildReport(wsRoot)
	s := report.Stats

	fmt.Printf("System-of-Systems Health\n")
	fmt.Println(strings.Repeat("─", 40))
	fmt.Printf("  systems:    %d\n", s.TotalSystems)
	fmt.Printf("  interfaces: %d\n", s.TotalInterfaces)
	fmt.Printf("  apps:       %d\n", s.TotalApps)
	fmt.Printf("  deployed:   %d\n", s.DeployedApps)
	fmt.Printf("  orphans:    %d\n", s.OrphanApps)
	fmt.Printf("  coupling:   %.1f (lower = better)\n", s.CouplingScore)
	fmt.Printf("  cohesion:   %.1f (higher = better)\n", s.CohesionScore)

	// Health verdict
	fmt.Println()
	if s.CouplingScore < 20 && s.CohesionScore > 60 {
		fmt.Println("  verdict: HEALTHY")
	} else if s.CouplingScore < 40 && s.CohesionScore > 40 {
		fmt.Println("  verdict: ACCEPTABLE")
	} else {
		fmt.Println("  verdict: NEEDS ATTENTION")
	}

	return nil
}

// --- core report builder ---

func sosBuildReport(wsRoot string) sosReport {
	report := sosReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
	}

	// 1. Get haisen graph
	hGraph := haisenScanWorkspace(wsRoot, true)

	// 2. Build systems from projects
	projectApps := make(map[string][]string) // project → nanoid list
	nanoidToProject := make(map[string]string)

	for _, app := range hGraph.Apps {
		project := app.Project
		if project == "" {
			project = "_unowned"
		}
		projectApps[project] = append(projectApps[project], app.Nanoid)
		nanoidToProject[app.Nanoid] = project
	}

	// 3. Load deploy state
	deployedApps := sosLoadDeployState(wsRoot)
	report.Inventory = sosScanInventory(wsRoot, hGraph.Apps)

	// 4. Build repo systems
	repoSystems := sosBuildRepoSystems(wsRoot, report.Inventory)

	// 5. Build infra systems (fixed)
	infraSystems := []sosSystem{
		{ID: "pds", Name: "PDS", SystemType: "infra", Layer: "infra", Technologies: []string{"xrpc", "worker"}},
		{ID: "yata", Name: "YATA", SystemType: "infra", Layer: "infra", Technologies: []string{"sql", "container"}},
		{ID: "yoro", Name: "Yoro", SystemType: "infra", Layer: "infra", Technologies: []string{"svelte", "container"}},
		{ID: "repo", Name: "Repo", SystemType: "infra", Layer: "infra", Technologies: []string{"worker", "git"}},
		{ID: "murakumo", Name: "Murakumo", SystemType: "infra", Layer: "infra", Technologies: []string{"worker", "inference"}},
		{ID: "maps", Name: "Maps", SystemType: "infra", Layer: "infra", Technologies: []string{"worker", "maps"}},
	}

	// 6. Build project systems
	var projectSystems []sosSystem
	for project, apps := range projectApps {
		deployed := 0
		for _, nanoid := range apps {
			if deployedApps[nanoid] {
				deployed++
			}
		}
		techs := sosProjectTechnologies(report.Inventory, project)
		projectSystems = append(projectSystems, sosSystem{
			ID:           project,
			Name:         project,
			SystemType:   "project",
			Layer:        "app",
			Path:         filepath.ToSlash(filepath.Join("projects", "ai-gftd-project-"+project)),
			Apps:         apps,
			AppCount:     len(apps),
			Deployed:     deployed,
			Technologies: techs,
		})
	}
	sort.Slice(projectSystems, func(i, j int) bool {
		return projectSystems[i].AppCount > projectSystems[j].AppCount
	})

	// Data layer systems
	dataSystems := []sosSystem{
		{ID: "r2_pipeline", Name: "R2 Pipeline", SystemType: "data", Layer: "data", Technologies: []string{"r2", "lance"}},
		{ID: "r2_graph", Name: "R2 Graph", SystemType: "data", Layer: "data", Technologies: []string{"r2", "graph"}},
		{ID: "r2_cdn", Name: "R2 CDN", SystemType: "data", Layer: "data", Technologies: []string{"r2", "cdn"}},
		{ID: "r2_git", Name: "R2 Git", SystemType: "data", Layer: "data", Technologies: []string{"r2", "git"}},
	}

	report.Systems = append(report.Systems, repoSystems...)
	report.Systems = append(report.Systems, infraSystems...)
	report.Systems = append(report.Systems, projectSystems...)
	report.Systems = append(report.Systems, dataSystems...)

	// 7. Build interfaces by aggregating haisen edges to system level
	ifaceMap := make(map[string]*sosInterface) // "from|to|protocol" → interface

	// Fixed infra interfaces
	addInfraInterface := func(from, to, proto, latency, desc string) {
		key := from + "|" + to + "|" + proto
		ifaceMap[key] = &sosInterface{From: from, To: to, Protocol: proto, EdgeCount: 1, Latency: latency, Description: desc}
	}
	addInfraInterface("pds", "yata", "workers_rpc", "~1ms", "query delegation")
	addInfraInterface("pds", "r2_pipeline", "http", "~10ms", "Lance append")
	addInfraInterface("yata", "r2_graph", "http", "~10ms", "graph snapshots")

	for _, iface := range sosBuildRepoInterfaces(report.Inventory, projectSystems) {
		key := iface.From + "|" + iface.To + "|" + iface.Protocol
		if existing, ok := ifaceMap[key]; ok {
			existing.EdgeCount += iface.EdgeCount
			if existing.Description == "" {
				existing.Description = iface.Description
			}
			if existing.Latency == "" {
				existing.Latency = iface.Latency
			}
			continue
		}
		copied := iface
		ifaceMap[key] = &copied
	}

	// Aggregate app edges to project level
	for _, e := range hGraph.Edges {
		fromProject := nanoidToProject[e.From]
		if fromProject == "" {
			fromProject = e.From
		}

		toProject := ""
		// Check if target is a nanoid
		if p, ok := nanoidToProject[e.To]; ok {
			toProject = p
		} else {
			// Collection or DID target → PDS (data gateway)
			toProject = "pds"
		}

		if fromProject == toProject {
			continue // intra-system, skip
		}

		proto := sosEdgeTypeToProtocol(e.EdgeType)
		key := fromProject + "|" + toProject + "|" + proto
		if iface, ok := ifaceMap[key]; ok {
			iface.EdgeCount++
		} else {
			ifaceMap[key] = &sosInterface{
				From:      fromProject,
				To:        toProject,
				Protocol:  proto,
				EdgeCount: 1,
			}
		}
	}

	for _, iface := range ifaceMap {
		report.Interfaces = append(report.Interfaces, *iface)
	}
	sort.Slice(report.Interfaces, func(i, j int) bool {
		return report.Interfaces[i].EdgeCount > report.Interfaces[j].EdgeCount
	})

	// 7. Compute edge counts per system
	sysEdgeCount := make(map[string]int)
	for _, iface := range report.Interfaces {
		sysEdgeCount[iface.From] += iface.EdgeCount
		sysEdgeCount[iface.To] += iface.EdgeCount
	}
	for i := range report.Systems {
		report.Systems[i].EdgeCount = sysEdgeCount[report.Systems[i].ID]
	}

	// 8. Build layers
	report.Layers = sosBuildLayers(report.Systems, projectSystems)

	// 9. Stats
	report.Stats.TotalSystems = len(report.Systems)
	report.Stats.TotalInterfaces = len(report.Interfaces)
	report.Stats.TotalApps = hGraph.Stats.TotalApps
	report.Stats.OrphanApps = hGraph.Stats.Orphans
	report.Stats.ProjectSystems = len(projectSystems)
	report.Stats.RepoSystems = len(repoSystems) + len(infraSystems) + len(dataSystems)
	report.Stats.WorkflowCount = report.Inventory.WorkflowCount
	report.Stats.PackageJSONCount = report.Inventory.PackageJSONCount
	report.Stats.DockerfileCount = report.Inventory.DockerfileCount

	totalDeployed := 0
	for _, s := range projectSystems {
		totalDeployed += s.Deployed
	}
	report.Stats.DeployedApps = totalDeployed

	// Coupling = shared collections / total unique collections
	report.Stats.CouplingScore = sosCouplingScore(hGraph)
	// Cohesion = intra-project edges / total edges
	report.Stats.CohesionScore = sosCohesionScore(hGraph, nanoidToProject)

	return report
}

func sosEdgeTypeToProtocol(edgeType string) string {
	switch edgeType {
	case "invoke":
		return "workers_rpc"
	case "writes", "reads":
		return "xrpc"
	case "subscribe":
		return "subscribe_repos"
	case "follow":
		return "xrpc"
	default:
		return "http"
	}
}

func sosLoadDeployState(wsRoot string) map[string]bool {
	deployed := make(map[string]bool)

	// Walk projects for .deploy-state.json
	projectsDir := filepath.Join(wsRoot, "projects")
	entries, err := os.ReadDir(projectsDir)
	if err != nil {
		return deployed
	}

	for _, entry := range entries {
		if !entry.IsDir() {
			continue
		}
		statePath := filepath.Join(projectsDir, entry.Name(), ".deploy-state.json")
		data, err := os.ReadFile(statePath)
		if err != nil {
			continue
		}
		var state deployState
		if err := json.Unmarshal(data, &state); err != nil {
			continue
		}
		for _, app := range state.Apps {
			if app.Nanoid != "" && app.LastDeployedAt != "" {
				deployed[app.Nanoid] = true
			}
		}
	}

	// Also check root .deploy-state.json
	rootState := filepath.Join(wsRoot, ".deploy-state.json")
	if data, err := os.ReadFile(rootState); err == nil {
		var state deployState
		if err := json.Unmarshal(data, &state); err == nil {
			for _, app := range state.Apps {
				if app.Nanoid != "" && app.LastDeployedAt != "" {
					deployed[app.Nanoid] = true
				}
			}
		}
	}

	return deployed
}

func sosScanInventory(wsRoot string, apps []haisenApp) sosInventory {
	inv := sosInventory{
		RuntimeVersions:     make(map[string]string),
		ProjectPackageCount: make(map[string]int),
		ProjectDockerCount:  make(map[string]int),
		ProjectRuntimeCount: make(map[string]map[string]int),
		ProjectUICount:      make(map[string]map[string]int),
		WorkspacePackages:   make(map[string]int),
	}

	projectSeen := make(map[string]bool)
	for _, app := range apps {
		if app.Project == "" {
			continue
		}
		projectSeen[app.Project] = true
		if app.RuntimeType != "" {
			if inv.ProjectRuntimeCount[app.Project] == nil {
				inv.ProjectRuntimeCount[app.Project] = make(map[string]int)
			}
			inv.ProjectRuntimeCount[app.Project][app.RuntimeType]++
		}
		if app.UIType != "" {
			if inv.ProjectUICount[app.Project] == nil {
				inv.ProjectUICount[app.Project] = make(map[string]int)
			}
			inv.ProjectUICount[app.Project][app.UIType]++
		}
	}

	_ = filepath.WalkDir(wsRoot, func(path string, d os.DirEntry, err error) error {
		if err != nil {
			return nil
		}
		rel, relErr := filepath.Rel(wsRoot, path)
		if relErr != nil {
			return nil
		}
		rel = filepath.ToSlash(rel)
		if rel == "." {
			return nil
		}
		if d.IsDir() && sosShouldSkipDir(rel, d.Name()) {
			return filepath.SkipDir
		}
		if d.IsDir() {
			return nil
		}

		base := d.Name()
		switch {
		case base == "package.json":
			inv.PackageJSONCount++
			project := haisenExtractProject(rel)
			if project != "" {
				inv.ProjectPackageCount[project]++
			}
			sosAccumulateWorkspacePackage(inv.WorkspacePackages, rel)
			sosMaybeReadPackageJSON(path, rel, &inv)
		case strings.HasPrefix(base, "Dockerfile"):
			inv.DockerfileCount++
			project := haisenExtractProject(rel)
			if project != "" {
				inv.ProjectDockerCount[project]++
			}
		case strings.HasPrefix(rel, ".github/workflows/") && (strings.HasSuffix(base, ".yml") || strings.HasSuffix(base, ".yaml")):
			inv.WorkflowCount++
		case strings.HasSuffix(base, ".deploy-state.json"):
			inv.DeployStateFiles++
		case strings.HasPrefix(rel, "reports/"):
			inv.ReportFileCount++
		}
		return nil
	})

	for _, lf := range []string{"pnpm-lock.yaml", "deno.lock", "go.mod", "package-lock.json", "bun.lockb"} {
		if _, err := os.Stat(filepath.Join(wsRoot, lf)); err == nil {
			inv.Lockfiles = append(inv.Lockfiles, lf)
		}
	}
	sort.Strings(inv.Lockfiles)

	for project := range projectSeen {
		if _, ok := inv.ProjectPackageCount[project]; !ok {
			inv.ProjectPackageCount[project] = 0
		}
		if _, ok := inv.ProjectDockerCount[project]; !ok {
			inv.ProjectDockerCount[project] = 0
		}
	}

	return inv
}

func sosShouldSkipDir(rel, base string) bool {
	switch base {
	case ".git", "node_modules", ".pnpm-store", ".turbo", ".nx", ".next", "dist", "coverage", "vendor", ".cargo-target":
		return true
	}
	if strings.HasPrefix(rel, ".artifacts/") || strings.HasPrefix(rel, "test-results/") {
		return true
	}
	return false
}

func sosAccumulateWorkspacePackage(buckets map[string]int, rel string) {
	switch {
	case strings.HasPrefix(rel, "20-actors/magatama/"), strings.HasPrefix(rel, "20-actors/magatama/"):
		buckets["magatama_runtime"]++
	case strings.HasPrefix(rel, "30-graph/"):
		buckets["packages_server"]++
	case strings.HasPrefix(rel, "40-engine/"):
		buckets["packages_engine"]++
	case strings.HasPrefix(rel, "40-engine/svelte/"):
		buckets["packages_svelte"]++
	case strings.HasPrefix(rel, "70-tools/gftd/"):
		buckets["gftd_cli"]++
	case strings.HasPrefix(rel, "50-infra/cloudflare/workers/"):
		buckets["cloudflare_workers"]++
	case strings.HasPrefix(rel, "50-infra/cloudflare/container/"):
		buckets["cloudflare_containers"]++
	}
}

func sosMaybeReadPackageJSON(path, rel string, inv *sosInventory) {
	data, err := os.ReadFile(path)
	if err != nil {
		return
	}
	var pkg sosPackageJSON
	if err := json.Unmarshal(data, &pkg); err != nil {
		return
	}
	if rel == "package.json" {
		if pkg.PackageManager != "" {
			inv.RuntimeVersions["packageManager"] = pkg.PackageManager
		}
		for name, version := range pkg.DevDependencies {
			switch name {
			case "nx", "vite", "wrangler", "@playwright/test", "esbuild":
				inv.RuntimeVersions[name] = version
			}
		}
	}
}

func sosBuildRepoSystems(wsRoot string, inv sosInventory) []sosSystem {
	var systems []sosSystem
	add := func(id, name, systemType, layer, relPath string, appCount int, techs []string, signals ...string) {
		system := sosSystem{
			ID:           id,
			Name:         name,
			SystemType:   systemType,
			Layer:        layer,
			AppCount:     appCount,
			Technologies: techs,
			Signals:      signals,
		}
		if relPath != "" {
			system.Path = relPath
		}
		switch id {
		case "workspace", "pnpm", "nx":
			system.VersionHints = map[string]string{}
			for k, v := range inv.RuntimeVersions {
				switch id {
				case "workspace":
					if k == "packageManager" {
						system.VersionHints[k] = v
					}
				case "pnpm":
					if k == "packageManager" {
						system.VersionHints[k] = v
					}
				case "nx":
					if k == "nx" {
						system.VersionHints[k] = v
					}
				}
			}
			if len(system.VersionHints) == 0 {
				system.VersionHints = nil
			}
		}
		systems = append(systems, system)
	}

	add("workspace", "Workspace", "control", "control", ".", inv.PackageJSONCount, []string{"monorepo", "pnpm", "go"}, "root")
	if _, err := os.Stat(filepath.Join(wsRoot, "pnpm-workspace.yaml")); err == nil {
		add("pnpm", "PNPM", "control", "control", "pnpm-workspace.yaml", inv.PackageJSONCount, []string{"pnpm", "lockfile"}, "package-manager")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "package.json")); err == nil {
		if _, ok := inv.RuntimeVersions["nx"]; ok {
			add("nx", "Nx", "control", "control", "package.json", inv.PackageJSONCount, []string{"task-graph", "build"}, "workspace-orchestration")
		}
	}
	if inv.WorkflowCount > 0 {
		add("github_actions", "GitHub Actions", "ops", "operations", ".github/workflows", inv.WorkflowCount, []string{"ci", "automation"}, "workflow")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "20-actors/magatama")); err == nil {
		add("magatama_runtime", "Magatama Runtime", "runtime", "runtime", "20-actors/magatama", inv.WorkspacePackages["magatama_runtime"], []string{"typescript", "wit", "worker-sdk"}, "sdk")
	} else if _, err := os.Stat(filepath.Join(wsRoot, "20-actors/magatama")); err == nil {
		add("magatama_runtime", "Magatama Runtime", "runtime", "runtime", "20-actors/magatama", inv.WorkspacePackages["magatama_runtime"], []string{"typescript", "wit", "worker-sdk"}, "sdk")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "30-graph")); err == nil {
		add("packages_server", "Graph Layer", "runtime", "runtime", "30-graph", inv.WorkspacePackages["packages_server"], []string{"server", "xrpc", "sql"}, "backend")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "40-engine")); err == nil {
		add("packages_engine", "Engine Layer", "runtime", "runtime", "40-engine", inv.WorkspacePackages["packages_engine"], []string{"rendering", "wasm"}, "engine")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "40-engine/svelte")); err == nil {
		add("packages_svelte", "Svelte Components", "runtime", "runtime", "40-engine/svelte", inv.WorkspacePackages["packages_svelte"], []string{"svelte", "ui"}, "ui")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "70-tools/gftd")); err == nil {
		add("gftd_cli", "gftd CLI", "control", "control", "70-tools/gftd", inv.WorkspacePackages["gftd_cli"], []string{"go", "cli"}, "deploy")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "50-infra/pulumi")); err == nil {
		add("pulumi", "Pulumi Infra", "infra", "infra", "50-infra/pulumi", 0, []string{"pulumi", "cloudflare"}, "infra-as-code")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "50-infra/cloudflare/workers")); err == nil {
		add("cloudflare_workers", "Cloudflare Workers", "infra", "infra", "50-infra/cloudflare/workers", inv.WorkspacePackages["cloudflare_workers"], []string{"cloudflare-workers"}, "worker-runtime")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "50-infra/cloudflare/container")); err == nil {
		add("cloudflare_containers", "Cloudflare Containers", "infra", "infra", "50-infra/cloudflare/container", inv.WorkspacePackages["cloudflare_containers"], []string{"cloudflare-containers", "docker"}, "container-runtime")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "docs/_registry")); err == nil {
		add("docs_registry", "Docs Registry", "ops", "operations", "docs/_registry", 0, []string{"jsonld", "registry"}, "documentation")
	}
	if _, err := os.Stat(filepath.Join(wsRoot, "reports")); err == nil {
		add("reports", "Reports", "ops", "operations", "reports", inv.ReportFileCount, []string{"analysis", "artifacts"}, "reporting")
	}
	if inv.DeployStateFiles > 0 {
		add("deploy_state", "Deploy State", "ops", "operations", ".deploy-state.json", inv.DeployStateFiles, []string{"deploy", "smoke"}, "deployment-state")
	}
	if inv.RuntimeVersions["@playwright/test"] != "" || inv.ReportFileCount > 0 {
		add("playwright_smoke", "Playwright Smoke", "ops", "operations", "reports", 0, []string{"playwright", "smoke-test"}, "verification")
	}
	if len(inv.Lockfiles) > 0 {
		add("pnpm_lock", "Lockfiles", "data", "data", inv.Lockfiles[0], len(inv.Lockfiles), []string{"lockfile"}, "versions")
	}

	sort.Slice(systems, func(i, j int) bool { return systems[i].ID < systems[j].ID })
	return systems
}

func sosProjectTechnologies(inv sosInventory, project string) []string {
	set := make(map[string]bool)
	if inv.ProjectPackageCount[project] > 0 {
		set["package-json"] = true
	}
	if inv.ProjectDockerCount[project] > 0 {
		set["docker"] = true
	}
	for runtime, count := range inv.ProjectRuntimeCount[project] {
		if count > 0 && runtime != "" {
			set[runtime] = true
		}
	}
	for ui, count := range inv.ProjectUICount[project] {
		if count > 0 && ui != "" {
			set[ui] = true
		}
	}
	var techs []string
	for tech := range set {
		techs = append(techs, tech)
	}
	sort.Strings(techs)
	return techs
}

func sosBuildRepoInterfaces(inv sosInventory, projectSystems []sosSystem) []sosInterface {
	var out []sosInterface
	add := func(from, to, protocol string, edgeCount int, desc string) {
		if edgeCount <= 0 {
			edgeCount = 1
		}
		out = append(out, sosInterface{
			From:        from,
			To:          to,
			Protocol:    protocol,
			EdgeCount:   edgeCount,
			Description: desc,
		})
	}

	if inv.PackageJSONCount > 0 {
		add("workspace", "pnpm", "package_manager", inv.PackageJSONCount, "workspace manifests")
	}
	if _, ok := inv.RuntimeVersions["nx"]; ok {
		add("workspace", "nx", "task_graph", inv.PackageJSONCount, "workspace orchestration")
	}
	if inv.WorkflowCount > 0 {
		add("github_actions", "pnpm", "ci", inv.WorkflowCount, "install/build")
		add("github_actions", "nx", "ci", inv.WorkflowCount, "task execution")
		add("github_actions", "gftd_cli", "ci", inv.WorkflowCount, "deploy and audit")
		add("github_actions", "reports", "artifact", inv.WorkflowCount, "generated evidence")
	}
	add("gftd_cli", "cloudflare_workers", "deploy", 1, "worker deploy")
	add("gftd_cli", "cloudflare_containers", "deploy", 1, "container deploy")
	if inv.DeployStateFiles > 0 {
		add("gftd_cli", "deploy_state", "artifact", inv.DeployStateFiles, "deploy receipts")
	}
	add("magatama_runtime", "cloudflare_workers", "runtime_host", 1, "worker host sdk")
	add("packages_server", "pds", "service", 1, "xrpc handlers")
	add("packages_server", "yata", "service", 1, "query runtime")
	add("packages_engine", "reports", "render", 1, "graph rendering")
	if inv.ReportFileCount > 0 {
		add("playwright_smoke", "reports", "artifact", inv.ReportFileCount, "smoke evidence")
	}
	add("pulumi", "cloudflare_workers", "iac", 1, "worker infra")
	add("pulumi", "cloudflare_containers", "iac", 1, "container infra")
	add("pulumi", "r2_pipeline", "iac", 1, "storage infra")
	add("pulumi", "r2_graph", "iac", 1, "graph storage")
	add("pulumi", "r2_cdn", "iac", 1, "cdn storage")
	if len(inv.Lockfiles) > 0 {
		add("pnpm", "pnpm_lock", "lockfile", len(inv.Lockfiles), "version pinning")
	}

	for _, project := range projectSystems {
		if project.AppCount > 0 {
			add(project.ID, "magatama_runtime", "sdk", project.AppCount, "app host sdk")
		}
		if inv.ProjectPackageCount[project.ID] > 0 {
			add(project.ID, "pnpm", "package_manager", inv.ProjectPackageCount[project.ID], "project manifests")
		}
		if inv.ProjectDockerCount[project.ID] > 0 {
			add(project.ID, "cloudflare_containers", "container", inv.ProjectDockerCount[project.ID], "containerized workloads")
		}
		for runtime, count := range inv.ProjectRuntimeCount[project.ID] {
			switch runtime {
			case "worker":
				add(project.ID, "cloudflare_workers", "runtime", count, "worker workloads")
			case "container":
				add(project.ID, "cloudflare_containers", "runtime", count, "container workloads")
			case "desktop-wasm":
				add(project.ID, "packages_engine", "runtime", count, "desktop wasm workloads")
			}
		}
		if inv.ProjectUICount[project.ID]["appview"] > 0 || inv.ProjectUICount[project.ID]["game"] > 0 || inv.ProjectUICount[project.ID]["yoro"] > 0 {
			uiCount := inv.ProjectUICount[project.ID]["appview"] + inv.ProjectUICount[project.ID]["game"] + inv.ProjectUICount[project.ID]["yoro"]
			add(project.ID, "packages_svelte", "ui", uiCount, "ui surfaces")
			add(project.ID, "yoro", "ui", uiCount, "user-facing delivery")
		}
		if project.Deployed > 0 {
			add("deploy_state", project.ID, "state", project.Deployed, "recorded deployments")
		}
	}

	return out
}

func sosBuildLayers(systems []sosSystem, projectSystems []sosSystem) []sosLayer {
	layerOrder := []string{"control", "runtime", "infra", "app", "operations", "data"}
	grouped := make(map[string][]string)
	for _, system := range systems {
		layer := system.Layer
		if layer == "" {
			layer = "unassigned"
		}
		grouped[layer] = append(grouped[layer], system.ID)
	}
	grouped["app"] = append(grouped["app"], "account_level_workers")
	for _, names := range grouped {
		sort.Strings(names)
	}

	var layers []sosLayer
	for _, layer := range layerOrder {
		if len(grouped[layer]) == 0 {
			continue
		}
		layers = append(layers, sosLayer{Name: layer, Systems: grouped[layer]})
	}
	return layers
}

func sosCouplingScore(hGraph haisenGraph) float64 {
	collApps := make(map[string]map[string]bool) // collection → set of apps
	for _, e := range hGraph.Edges {
		if e.EdgeType == "writes" || e.EdgeType == "reads" || e.EdgeType == "subscribe" {
			if collApps[e.To] == nil {
				collApps[e.To] = make(map[string]bool)
			}
			collApps[e.To][e.From] = true
		}
	}

	if len(collApps) == 0 {
		return 0
	}

	shared := 0
	for _, apps := range collApps {
		if len(apps) > 1 {
			shared++
		}
	}
	return float64(shared) / float64(len(collApps)) * 100
}

func sosCohesionScore(hGraph haisenGraph, nanoidToProject map[string]string) float64 {
	if len(hGraph.Edges) == 0 {
		return 100
	}

	intra := 0
	total := 0
	for _, e := range hGraph.Edges {
		fromProject := nanoidToProject[e.From]
		toProject := nanoidToProject[e.To]
		if fromProject == "" || toProject == "" {
			continue
		}
		total++
		if fromProject == toProject {
			intra++
		}
	}

	if total == 0 {
		return 100
	}
	return float64(intra) / float64(total) * 100
}
