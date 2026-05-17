package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

type depsGovernanceWITFinding struct {
	Severity string `json:"severity"`
	Code     string `json:"code"`
	Message  string `json:"message"`
}

type depsGovernanceWITWorld struct {
	Path               string   `json:"path"`
	Imports            []string `json:"imports"`
	HasRuntimeInclude  bool     `json:"hasRuntimeInclude"`
	HasGovernance      bool     `json:"hasGovernance"`
	HasRACI            bool     `json:"hasRaci"`
	HasRBAC            bool     `json:"hasRbac"`
	HasTraceability    bool     `json:"hasTraceability"`
	HasCapability      bool     `json:"hasCapability"`
	HasAgentGovernance bool     `json:"hasAgentGovernance"`
}

type depsGovernanceWITManifest struct {
	Path          string   `json:"path"`
	HasGovernance bool     `json:"hasGovernance"`
	NonDefault    bool     `json:"nonDefault"`
	RoleBindings  int      `json:"roleBindings"`
	Frameworks    []string `json:"frameworks,omitempty"`
}

type depsGovernanceWITImplementation struct {
	Runtime                string `json:"runtime"`
	Path                   string `json:"path"`
	CommandCount           int    `json:"commandCount"`
	HandleCount            int    `json:"handleCount"`
	ExplicitGovernedCount  int    `json:"explicitGovernedCount"`
	ApprovalCount          int    `json:"approvalCount"`
	TraceabilityCount      int    `json:"traceabilityCount"`
	AutoManifestRegistered bool   `json:"autoManifestRegistered"`
}

type depsGovernanceWITReport struct {
	EvaluatedAt    string                          `json:"evaluatedAt"`
	ComponentDir   string                          `json:"componentDir"`
	Score          float64                         `json:"score"`
	Verdict        string                          `json:"verdict"`
	World          depsGovernanceWITWorld          `json:"world"`
	Manifest       depsGovernanceWITManifest       `json:"manifest"`
	Implementation depsGovernanceWITImplementation `json:"implementation"`
	Findings       []depsGovernanceWITFinding      `json:"findings"`
}

var (
	depsWITImportRe         = regexp.MustCompile(`(?m)^\s*import\s+([^;]+);`)
	depsWITIncludeRe        = regexp.MustCompile(`(?m)^\s*include\s+([^;]+);`)
	depsTSCommandStartRe    = regexp.MustCompile(`\.command\(\s*["'][^"']+["']`)
	depsTSBuildRe           = regexp.MustCompile(`\.build\(`)
	depsGoCommandStartRe    = regexp.MustCompile(`app\.Command\(`)
	depsGoHandleStartRe     = regexp.MustCompile(`app\.(?:Handle|HandleStream)\(`)
	depsManifestDefaultJSON = `{"raci":"responsible","classification":"internal","complianceFrameworks":[]}`
)

func runDepsGovernanceWIT(args []string) error {
	fs := flag.NewFlagSet("deps governance-wit", flag.ContinueOnError)
	componentDir := fs.String("component-dir", ".", "App component directory")
	outFormat := fs.String("format", "text", "output format: text or json")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	report, err := evaluateGovernanceWIT(*componentDir)
	if err != nil {
		return err
	}

	switch strings.ToLower(strings.TrimSpace(*outFormat)) {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	case "text":
		printGovernanceWITText(report)
		if strings.EqualFold(report.Verdict, "not-suitable") {
			return fmt.Errorf("governance WIT verdict=%s", report.Verdict)
		}
		return nil
	default:
		return fmt.Errorf("unknown --format: %s", *outFormat)
	}
}

func evaluateGovernanceWIT(componentDir string) (*depsGovernanceWITReport, error) {
	absDir, err := filepath.Abs(componentDir)
	if err != nil {
		return nil, fmt.Errorf("resolve component dir: %w", err)
	}

	report := &depsGovernanceWITReport{
		EvaluatedAt:  time.Now().UTC().Format(time.RFC3339),
		ComponentDir: absDir,
	}

	world, worldData, worldErr := loadGovernanceWorld(absDir)
	if worldErr == nil {
		report.World = world
	} else {
		report.Findings = append(report.Findings, depsGovernanceWITFinding{
			Severity: "critical",
			Code:     "world_missing",
			Message:  worldErr.Error(),
		})
	}

	manifest, manifestErr := loadGovernanceManifest(absDir)
	if manifestErr == nil {
		report.Manifest = manifest
	} else {
		report.Findings = append(report.Findings, depsGovernanceWITFinding{
			Severity: "warning",
			Code:     "manifest_missing",
			Message:  manifestErr.Error(),
		})
	}

	impl, implErr := loadGovernanceImplementation(absDir)
	if implErr == nil {
		report.Implementation = impl
	} else {
		report.Findings = append(report.Findings, depsGovernanceWITFinding{
			Severity: "critical",
			Code:     "impl_missing",
			Message:  implErr.Error(),
		})
	}

	if worldErr == nil {
		if !report.World.HasGovernance {
			report.Findings = append(report.Findings, depsGovernanceWITFinding{
				Severity: "critical",
				Code:     "wit_governance_missing",
				Message:  "world.wit does not import magatama:governance/governance@1.0.0",
			})
		}
		for _, missing := range recommendedGovernanceImports(report.World) {
			report.Findings = append(report.Findings, depsGovernanceWITFinding{
				Severity: "warning",
				Code:     "wit_import_recommended",
				Message:  fmt.Sprintf("world.wit is missing recommended governance dependency %s", missing),
			})
		}
	}

	if manifestErr == nil && !report.Manifest.HasGovernance {
		report.Findings = append(report.Findings, depsGovernanceWITFinding{
			Severity: "warning",
			Code:     "manifest_governance_missing",
			Message:  "magatama.jsonld has no governance block",
		})
	}
	if manifestErr == nil && report.Manifest.HasGovernance && !report.Manifest.NonDefault {
		report.Findings = append(report.Findings, depsGovernanceWITFinding{
			Severity: "warning",
			Code:     "manifest_governance_default",
			Message:  "magatama.jsonld governance block is still the platform default template",
		})
	}

	if implErr == nil {
		if report.Implementation.CommandCount+report.Implementation.HandleCount == 0 {
			report.Findings = append(report.Findings, depsGovernanceWITFinding{
				Severity: "warning",
				Code:     "no_commands",
				Message:  "no commands or handlers were detected in the app implementation",
			})
		}
		if report.Implementation.CommandCount > 0 && report.Implementation.ExplicitGovernedCount == 0 {
			report.Findings = append(report.Findings, depsGovernanceWITFinding{
				Severity: "warning",
				Code:     "command_governance_implicit",
				Message:  "commands rely on SDK defaults; no explicit RACI/approval/traceability options were detected",
			})
		}
		if report.Implementation.Runtime == "ts" && !report.Implementation.AutoManifestRegistered {
			report.Findings = append(report.Findings, depsGovernanceWITFinding{
				Severity: "critical",
				Code:     "auto_manifest_missing",
				Message:  "TS app does not appear to register governance manifest via the host SDK",
			})
		}
	}

	report.Score = scoreGovernanceWIT(report, string(worldData))
	report.Verdict = verdictGovernanceWIT(report.Score, report.Findings)
	sort.Slice(report.Findings, func(i, j int) bool {
		return governanceSeverityRank(report.Findings[i].Severity) < governanceSeverityRank(report.Findings[j].Severity)
	})
	return report, nil
}

func loadGovernanceWorld(componentDir string) (depsGovernanceWITWorld, []byte, error) {
	path := filepath.Join(componentDir, "wit", "world.wit")
	data, err := os.ReadFile(path)
	if err != nil {
		return depsGovernanceWITWorld{}, nil, fmt.Errorf("read %s: %w", path, err)
	}
	importMatches := depsWITImportRe.FindAllStringSubmatch(string(data), -1)
	includeMatches := depsWITIncludeRe.FindAllStringSubmatch(string(data), -1)
	imports := make([]string, 0, len(importMatches))
	has := map[string]bool{}
	for _, m := range importMatches {
		name := strings.TrimSpace(m[1])
		imports = append(imports, name)
		has[name] = true
	}
	hasRuntimeInclude := false
	for _, m := range includeMatches {
		if strings.TrimSpace(m[1]) == "magatama:runtime/magatama-component@1.0.0" {
			hasRuntimeInclude = true
			break
		}
	}
	sort.Strings(imports)
	return depsGovernanceWITWorld{
		Path:               path,
		Imports:            imports,
		HasRuntimeInclude:  hasRuntimeInclude,
		HasGovernance:      hasRuntimeInclude || has["magatama:governance/governance@1.0.0"],
		HasRACI:            hasRuntimeInclude || has["magatama:governance/raci@1.0.0"],
		HasRBAC:            hasRuntimeInclude || has["magatama:governance/rbac@1.0.0"],
		HasTraceability:    hasRuntimeInclude || has["magatama:governance/traceability@1.0.0"],
		HasCapability:      hasRuntimeInclude || has["magatama:identity/capability@1.0.0"],
		HasAgentGovernance: hasRuntimeInclude || has["magatama:agent/governance@1.0.0"],
	}, data, nil
}

func loadGovernanceManifest(componentDir string) (depsGovernanceWITManifest, error) {
	path := filepath.Join(componentDir, "magatama.jsonld")
	data, err := os.ReadFile(path)
	if err != nil {
		return depsGovernanceWITManifest{}, fmt.Errorf("read %s: %w", path, err)
	}
	var doc map[string]any
	if err := json.Unmarshal(data, &doc); err != nil {
		return depsGovernanceWITManifest{}, fmt.Errorf("parse %s: %w", path, err)
	}
	report := depsGovernanceWITManifest{Path: path}
	gov, ok := doc["governance"]
	if !ok {
		return report, nil
	}
	report.HasGovernance = true
	if govJSON, err := json.Marshal(gov); err == nil {
		report.NonDefault = string(govJSON) != depsManifestDefaultJSON
	}
	if govMap, ok := gov.(map[string]any); ok {
		if roles, ok := govMap["roles"].([]any); ok {
			report.RoleBindings = len(roles)
		}
		if frameworks, ok := govMap["complianceFrameworks"].([]any); ok {
			for _, item := range frameworks {
				if s, ok := item.(string); ok && s != "" {
					report.Frameworks = append(report.Frameworks, s)
				}
			}
		}
	}
	sort.Strings(report.Frameworks)
	return report, nil
}

func loadGovernanceImplementation(componentDir string) (depsGovernanceWITImplementation, error) {
	tsPath := filepath.Join(componentDir, "src", "app.ts")
	if data, err := os.ReadFile(tsPath); err == nil {
		return evaluateTSGovernance(tsPath, string(data)), nil
	}
	goPath := filepath.Join(componentDir, "main.go")
	if data, err := os.ReadFile(goPath); err == nil {
		return evaluateGoGovernance(goPath, string(data)), nil
	}
	return depsGovernanceWITImplementation{}, fmt.Errorf("no src/app.ts or main.go found under %s", componentDir)
}

func evaluateTSGovernance(path, src string) depsGovernanceWITImplementation {
	commands, governed, approvals, traceability := evaluateCommandBlocks(src, depsTSCommandStartRe, depsTSBuildRe,
		[]string{"responsible(", "accountable(", "consulted(", "informed("},
		[]string{"requireApproval("},
		[]string{"withBPMNTask(", "withOCELEvent("},
	)
	return depsGovernanceWITImplementation{
		Runtime:                "ts",
		Path:                   path,
		CommandCount:           commands,
		ExplicitGovernedCount:  governed,
		ApprovalCount:          approvals,
		TraceabilityCount:      traceability,
		AutoManifestRegistered: strings.Contains(src, ".serve()") || strings.Contains(src, ".build()"),
	}
}

func evaluateGoGovernance(path, src string) depsGovernanceWITImplementation {
	commands, governed, approvals, traceability := evaluateCommandBlocks(src, depsGoCommandStartRe, nil,
		[]string{"magatama.Responsible(", "magatama.Accountable(", "magatama.Consulted(", "magatama.Informed("},
		[]string{"RequireApproval("},
		[]string{"WithBPMNTask(", "WithOCELEvent("},
	)
	handles, governedHandles, approvalHandles, traceHandles := evaluateCommandBlocks(src, depsGoHandleStartRe, nil,
		[]string{"magatama.RequireCallerRole(", "magatama.RequirePermission(", "magatama.RequireContract(", "magatama.RequireTrustLevel(", "magatama.RequireConsent(", "magatama.RequireSameOrg(", "magatama.RequireContractParty("},
		[]string{"RequireApproval("},
		[]string{"WithBPMNTask(", "WithOCELEvent("},
	)
	return depsGovernanceWITImplementation{
		Runtime:                "go",
		Path:                   path,
		CommandCount:           commands,
		HandleCount:            handles,
		ExplicitGovernedCount:  governed + governedHandles,
		ApprovalCount:          approvals + approvalHandles,
		TraceabilityCount:      traceability + traceHandles,
		AutoManifestRegistered: strings.Contains(src, ".Serve()"),
	}
}

func evaluateCommandBlocks(src string, startRe, tailRe *regexp.Regexp, governanceMarkers, approvalMarkers, traceabilityMarkers []string) (count, governed, approvals, traceability int) {
	starts := startRe.FindAllStringIndex(src, -1)
	if len(starts) == 0 {
		return 0, 0, 0, 0
	}
	limit := len(src)
	tailIdx := -1
	if tailRe != nil {
		if loc := tailRe.FindStringIndex(src); loc != nil {
			tailIdx = loc[0]
		}
	}
	for i, loc := range starts {
		start := loc[0]
		end := limit
		if i+1 < len(starts) {
			end = starts[i+1][0]
		}
		if tailIdx >= 0 && tailIdx > start && tailIdx < end {
			end = tailIdx
		}
		block := src[start:end]
		count++
		hasGov := containsAny(block, governanceMarkers...) || containsAny(block, approvalMarkers...) || containsAny(block, traceabilityMarkers...)
		if hasGov {
			governed++
		}
		if containsAny(block, approvalMarkers...) {
			approvals++
		}
		if containsAny(block, traceabilityMarkers...) {
			traceability++
		}
	}
	return count, governed, approvals, traceability
}

// isPureComputeComponent returns true for Pattern C components (pure-compute,
// no magatama host runtime) that are explicitly exempt from governance scoring.
func isPureComputeComponent(worldSrc string) bool {
	lower := strings.ToLower(worldSrc)
	hasPureComputeMarker := strings.Contains(lower, "no magatama imports") ||
		strings.Contains(lower, "pattern c") ||
		strings.Contains(lower, "pure-compute") ||
		strings.Contains(lower, "pure compute")
	hasMagatama := strings.Contains(lower, "magatama:")
	return hasPureComputeMarker && !hasMagatama
}

func scoreGovernanceWIT(report *depsGovernanceWITReport, worldSrc string) float64 {
	// Pattern C pure-compute components are exempt from governance scoring.
	if isPureComputeComponent(worldSrc) {
		return 100
	}
	score := 0.0
	if report.World.HasGovernance {
		score += 20
	}
	if report.World.HasRACI {
		score += 10
	}
	if report.World.HasRBAC {
		score += 10
	}
	if report.World.HasTraceability {
		score += 10
	}
	if report.World.HasCapability {
		score += 5
	}
	if report.World.HasAgentGovernance {
		score += 5
	}
	if report.Manifest.HasGovernance {
		score += 10
	}
	if report.Manifest.NonDefault {
		score += 10
	}
	if report.Manifest.RoleBindings > 0 {
		score += 5
	}

	totalOps := report.Implementation.CommandCount + report.Implementation.HandleCount
	if totalOps > 0 {
		score += 5
		score += 10 * float64(report.Implementation.ExplicitGovernedCount) / float64(totalOps)
	}
	if report.Implementation.ApprovalCount > 0 {
		score += 5
	}
	if report.Implementation.TraceabilityCount > 0 {
		score += 5
	}
	if report.Implementation.AutoManifestRegistered {
		score += 5
	}
	if strings.Contains(worldSrc, "include magatama:runtime/magatama-component@1.0.0;") {
		score += 5
	}
	if score > 100 {
		score = 100
	}
	return round1(score)
}

func verdictGovernanceWIT(score float64, findings []depsGovernanceWITFinding) string {
	for _, f := range findings {
		if f.Severity == "critical" {
			if score >= 70 {
				return "acceptable-with-critical-gaps"
			}
			return "not-suitable"
		}
	}
	switch {
	case score >= 85:
		return "suitable"
	case score >= 70:
		return "acceptable"
	case score >= 50:
		return "weak"
	default:
		return "not-suitable"
	}
}

func printGovernanceWITText(report *depsGovernanceWITReport) {
	fmt.Printf("governance_wit:\n")
	fmt.Printf("  component_dir: %s\n", report.ComponentDir)
	fmt.Printf("  evaluated_at: %s\n", report.EvaluatedAt)
	fmt.Printf("  verdict: %s\n", report.Verdict)
	fmt.Printf("  score: %.1f\n", report.Score)
	fmt.Printf("  runtime: %s\n", report.Implementation.Runtime)
	fmt.Printf("  world_path: %s\n", report.World.Path)
	fmt.Printf("  implementation_path: %s\n", report.Implementation.Path)
	fmt.Printf("  manifest_path: %s\n", report.Manifest.Path)
	fmt.Printf("  wit_imports: governance=%t raci=%t rbac=%t traceability=%t capability=%t agent_governance=%t\n",
		report.World.HasGovernance, report.World.HasRACI, report.World.HasRBAC, report.World.HasTraceability, report.World.HasCapability, report.World.HasAgentGovernance)
	fmt.Printf("  manifest: has_governance=%t non_default=%t role_bindings=%d\n",
		report.Manifest.HasGovernance, report.Manifest.NonDefault, report.Manifest.RoleBindings)
	fmt.Printf("  implementation: commands=%d handles=%d explicit_governed=%d approvals=%d traceability=%d auto_manifest=%t\n",
		report.Implementation.CommandCount, report.Implementation.HandleCount, report.Implementation.ExplicitGovernedCount,
		report.Implementation.ApprovalCount, report.Implementation.TraceabilityCount, report.Implementation.AutoManifestRegistered)
	if len(report.Findings) > 0 {
		fmt.Printf("  findings:\n")
		for _, finding := range report.Findings {
			fmt.Printf("    - [%s] %s: %s\n", finding.Severity, finding.Code, finding.Message)
		}
	}
}

func recommendedGovernanceImports(world depsGovernanceWITWorld) []string {
	if world.HasRuntimeInclude {
		return nil
	}
	var missing []string
	if !world.HasRACI {
		missing = append(missing, "magatama:governance/raci@1.0.0")
	}
	if !world.HasRBAC {
		missing = append(missing, "magatama:governance/rbac@1.0.0")
	}
	if !world.HasTraceability {
		missing = append(missing, "magatama:governance/traceability@1.0.0")
	}
	if !world.HasCapability {
		missing = append(missing, "magatama:identity/capability@1.0.0")
	}
	return missing
}

func containsAny(s string, needles ...string) bool {
	for _, needle := range needles {
		if needle != "" && strings.Contains(s, needle) {
			return true
		}
	}
	return false
}

func governanceSeverityRank(severity string) int {
	switch severity {
	case "critical":
		return 0
	case "warning":
		return 1
	default:
		return 2
	}
}
