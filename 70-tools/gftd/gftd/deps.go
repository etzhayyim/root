package main

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"math"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/etzhayyim/root/70-tools/gftd/gftd/db"
)

var (
	nodesJSPathRegex = regexp.MustCompile(`_app/immutable/nodes/2\.[^"]+\.js`)
	moJSONRegex      = regexp.MustCompile(`Mo=JSON\.parse\('([\s\S]*?)'\),Bo=`)
)

type depsLinkEntry struct {
	Project     string `json:"project"`
	ComponentID string `json:"componentId"`
	Kind        string `json:"kind"`
	Ref         string `json:"ref"`
	Status      string `json:"status"`
}

type depsLinkerStatus struct {
	GeneratedAt string                `json:"generatedAt"`
	Components  []depsLinkerComponent `json:"components"`
	Links       []depsLinkEntry       `json:"links"`
	Summary     struct {
		TotalComponents int `json:"totalComponents"`
		TotalLinks      int `json:"totalLinks"`
		ResolvedLinks   int `json:"resolvedLinks"`
		UnresolvedLinks int `json:"unresolvedLinks"`
	} `json:"summary"`
}

type depsLinkerComponent struct {
	Project          string             `json:"project"`
	ComponentID      string             `json:"componentId"`
	Imports          []string           `json:"imports"`
	Exports          []string           `json:"exports"`
	InterfacePackage string             `json:"interfacePackage"`
	Provides         []depsProvideEntry `json:"provides"`
	Requires         []depsRequireEntry `json:"requires"`
	AppID            string             `json:"appId,omitempty"`
	AppName          string             `json:"appName,omitempty"`
	Runtime          string             `json:"runtime,omitempty"`
	RouteHosts       []string           `json:"routeHosts,omitempty"`
	RegisteredApp    bool               `json:"registeredApp,omitempty"`
	WorkerDeployed   bool               `json:"workerDeployed,omitempty"`
	WProtoScore      float64            `json:"wprotoIntegrationScore,omitempty"`
	WProtoSignals    []string           `json:"wprotoSignals,omitempty"`
}

type depsProvideEntry struct {
	Name               string `json:"name"`
	Tier               int    `json:"tier"`
	AllowedCallerTiers []int  `json:"allowedCallerTiers"`
	SameOrgOnly        bool   `json:"sameOrgOnly"`
}

type depsRequireEntry struct {
	Package           string `json:"package"`
	Interface         string `json:"interface"`
	Provider          string `json:"provider"`
	PreferredTiers    []int  `json:"preferredTiers"`
	AllowTierFallback bool   `json:"allowTierFallback"`
}

type depsGraphSnapshot struct {
	GeneratedAt      string                 `json:"generatedAt"`
	Summary          depsGraphSummary       `json:"summary"`
	Scorecard        *depsGraphScorecard    `json:"scorecard,omitempty"`
	LinkerStatus     depsLinkerStatus       `json:"linkerStatus"`
	RegisteredApps   []depsAppRegistryEntry `json:"registeredApps,omitempty"`
	DomainComponents []depsDomainComponent  `json:"domainComponents"`
	GovernanceLinks  []depsGovernanceLink   `json:"governanceLinks"`
}

type depsGraphSummary struct {
	TotalPackages             int     `json:"totalPackages"`
	TotalInterfaces           int     `json:"totalInterfaces"`
	TotalHostImpls            int     `json:"totalHostImpls"`
	TotalProjectComponents    int     `json:"totalProjectComponents"`
	TotalEdges                int     `json:"totalEdges"`
	RuntimeImports            int     `json:"runtimeImports"`
	RuntimeExports            int     `json:"runtimeExports"`
	TotalDomainDeps           int     `json:"totalDomainDeps"`
	TotalRbacBindings         int     `json:"totalRbacBindings"`
	TotalCapabilities         int     `json:"totalCapabilities"`
	TotalDomainComponents     int     `json:"totalDomainComponents"`
	TotalGovernanceLinks      int     `json:"totalGovernanceLinks"`
	TotalGovernedComponents   int     `json:"totalGovernedComponents"`
	TotalLinkerComponents     int     `json:"totalLinkerComponents"`
	TotalRegisteredApps       int     `json:"totalRegisteredApps"`
	TotalWorkerDeployedApps   int     `json:"totalWorkerDeployedApps"`
	TotalResolvedLinks        int     `json:"totalResolvedLinks"`
	TotalUnresolvedLinks      int     `json:"totalUnresolvedLinks"`
	TotalIsolatedComponents   int     `json:"totalIsolatedComponents"`
	GovernanceUnresolvedCount int     `json:"governanceUnresolvedCount"`
	WorkerDeployCoverageRate  float64 `json:"workerDeployCoverageRate"`
	WProtoIntegrationScore    float64 `json:"wprotoIntegrationScore"`
	IsolatedComponentsRate    float64 `json:"isolatedComponentsRate"`
	ExplicitRaciCoverageRate  float64 `json:"explicitRaciCoverageRate"`
	GovernanceCoverageRate    float64 `json:"governanceCoverageRate"`
	AppWITDefinitionScore     float64 `json:"appWitDefinitionScore"`
	DepsOverallScore          float64 `json:"depsOverallScore"`
}

type depsGraphScorecard struct {
	AppWITDefinitionCoverage  float64 `json:"appWitDefinitionCoverage"`
	WorkerRegisteredAppCount  int     `json:"workerRegisteredAppCount"`
	WorkerDeployedAppCount    int     `json:"workerDeployedAppCount"`
	WorkerDeployCoverageRate  float64 `json:"workerDeployCoverageRate"`
	WProtoIntegrationScore    float64 `json:"wprotoIntegrationScore"`
	IsolatedComponentsCount   int     `json:"isolatedComponentsCount"`
	IsolatedComponentsRate    float64 `json:"isolatedComponentsRate"`
	GovernanceCoverageRate    float64 `json:"governanceCoverageRate"`
	ExplicitRaciCoverageRate  float64 `json:"explicitRaciCoverageRate"`
	GovernanceUnresolvedCount int     `json:"governanceUnresolvedCount"`
}

type depsAppRegistryEntry struct {
	Project        string   `json:"project"`
	ComponentID    string   `json:"componentId"`
	AppID          string   `json:"appId,omitempty"`
	AppName        string   `json:"appName,omitempty"`
	Runtime        string   `json:"runtime,omitempty"`
	RegisteredApp  bool     `json:"registeredApp,omitempty"`
	WorkerDeployed bool     `json:"workerDeployed,omitempty"`
	RouteHosts     []string `json:"routeHosts,omitempty"`
	WProtoScore    float64  `json:"wprotoIntegrationScore,omitempty"`
	WProtoSignals  []string `json:"wprotoSignals,omitempty"`
}

type depsDomainComponent struct {
	ComponentID     string `json:"componentId"`
	CapabilityCount int    `json:"capabilityCount"`
	RbacCount       int    `json:"rbacCount"`
}

type depsGovernanceLink struct {
	Project     string `json:"project"`
	ComponentID string `json:"componentId"`
}

type depsQualityAudit struct {
	GeneratedAt           string                 `json:"generatedAt"`
	SourceGeneratedAt     string                 `json:"sourceGeneratedAt"`
	SourceSummary         depsGraphSummary       `json:"sourceSummary"`
	Totals                depsQualityAuditTotals `json:"totals"`
	TopProjects           []depsQualityProject   `json:"topProjects"`
	CriticalComponents    []depsQualityRecord    `json:"criticalComponents"`
	TopRiskComponents     []depsQualityRecord    `json:"topRiskComponents"`
	ISCOTopRiskComponents []depsQualityRecord    `json:"iscoTopRiskComponents"`
}

type depsQualityAuditTotals struct {
	TotalComponents             int `json:"totalComponents"`
	IsolatedComponents          int `json:"isolatedComponents"`
	CapabilityMissingComponents int `json:"capabilityMissingComponents"`
	RBACMissingComponents       int `json:"rbacMissingComponents"`
	GovernanceMissingComponents int `json:"governanceMissingComponents"`
	TripleMissingComponents     int `json:"tripleMissingComponents"`
	CriticalComponents          int `json:"criticalComponents"`
}

type depsQualityProject struct {
	Project                     string `json:"project"`
	TotalComponents             int    `json:"totalComponents"`
	IsolatedComponents          int    `json:"isolatedComponents"`
	CapabilityMissingComponents int    `json:"capabilityMissingComponents"`
	GovernanceMissingComponents int    `json:"governanceMissingComponents"`
	TripleMissingComponents     int    `json:"tripleMissingComponents"`
	CriticalComponents          int    `json:"criticalComponents"`
}

type depsQualityRecord struct {
	Project           string `json:"project"`
	ComponentID       string `json:"componentId"`
	Isolated          bool   `json:"isolated"`
	CapabilityCount   int    `json:"capabilityCount"`
	RbacCount         int    `json:"rbacCount"`
	GovernanceCount   int    `json:"governanceCount"`
	CapabilityMissing bool   `json:"capabilityMissing"`
	RbacMissing       bool   `json:"rbacMissing"`
	GovernanceMissing bool   `json:"governanceMissing"`
	Risk              int    `json:"risk"`
}

type depsNodeScore struct {
	Project         string `json:"project"`
	ComponentID     string `json:"component_id"`
	UnresolvedLinks int    `json:"unresolved_links"`
}

type depsGovernanceNode struct {
	Project                 string   `json:"project"`
	ComponentID             string   `json:"component_id"`
	UnresolvedGovernanceRef []string `json:"unresolved_governance_refs"`
}

type depsScoring struct {
	Model                    string                `json:"model"`
	OverallScore             float64               `json:"overall_score"`
	LinkBlendScore           float64               `json:"link_blend_score"`
	BuildLinkerScore         float64               `json:"build_linker_score"`
	RuntimeLinkerScore       float64               `json:"runtime_linker_score"`
	AppMeshScore             float64               `json:"app_mesh_score"`
	RuntimeHostScore         float64               `json:"runtime_host_score"`
	DoDAFV2Score             float64               `json:"dodaf_v2_score"`
	NISTCSFV2Score           float64               `json:"nist_csf_v2_score"`
	AppWITDefinitionScore    float64               `json:"app_wit_definition_score"`
	AppWITDefinitionCoverage float64               `json:"app_wit_definition_coverage"`
	ContractScore            float64               `json:"contract_score"`
	CapabilityExportScore    float64               `json:"capability_export_score"`
	DepsLinkScore            float64               `json:"deps_link_score"`
	ResourceFlowScore        float64               `json:"resource_flow_score"`
	DIVScore                 float64               `json:"div_score"`
	ShannonScore             float64               `json:"shannon_score"`
	ImportEntropyScore       float64               `json:"import_entropy_score"`
	DuplicateImportScore     float64               `json:"duplicate_import_score"`
	IsolationPenalty         float64               `json:"isolation_penalty"`
	UnadaptedPenalty         float64               `json:"unadapted_penalty"`
	BuildLinkerFactors       depsStageScoreFactors `json:"build_linker_factors"`
	RuntimeLinkerFactors     depsStageScoreFactors `json:"runtime_linker_factors"`
	AppMeshFactors           depsStageScoreFactors `json:"app_mesh_factors"`
	RuntimeHostFactors       depsStageScoreFactors `json:"runtime_host_factors"`
	ComplianceFactors        depsComplianceFactors `json:"compliance_factors"`
}

type depsStageScoreFactors struct {
	LinkCoverage             float64 `json:"link_coverage"`
	PolicyCoverage           float64 `json:"policy_coverage"`
	GovernanceHealth         float64 `json:"governance_health"`
	RBACCoverage             float64 `json:"rbac_coverage"`
	CapabilityCoverage       float64 `json:"capability_coverage"`
	AppWITDefinitionCoverage float64 `json:"app_wit_definition_coverage"`
	RuntimeImportHealth      float64 `json:"runtime_import_health"`
	IsolatedRate             float64 `json:"isolated_rate"`
	GovernanceCoverage       float64 `json:"governance_coverage"`
	RACICoverage             float64 `json:"raci_coverage"`
}

type depsComplianceFactors struct {
	DoDAFV2   float64 `json:"dodaf_v2"`
	NISTCSFV2 float64 `json:"nist_csf_v2"`
}

type depsScoreReport struct {
	EvaluatedAt               string               `json:"evaluated_at"`
	SourceURL                 string               `json:"source_url"`
	GeneratedAt               string               `json:"generated_at"`
	TotalLinks                int                  `json:"total_links"`
	ResolvedCount             int                  `json:"resolved_count"`
	UnresolvedCount           int                  `json:"unresolved_count"`
	LinkCoverageRate          float64              `json:"link_coverage_rate"`
	UnresolvedRate            float64              `json:"unresolved_rate"`
	UnresolvedByKind          map[string]int       `json:"unresolved_by_kind"`
	GovernanceUnresolvedCount int                  `json:"governance_unresolved_count"`
	GovernanceUnresolvedNodes []depsGovernanceNode `json:"governance_unresolved_nodes"`
	TopUnresolvedNodes        []depsNodeScore      `json:"top_unresolved_nodes"`
	WorkerRegisteredAppCount  int                  `json:"worker_registered_app_count,omitempty"`
	WorkerDeployedAppCount    int                  `json:"worker_deployed_app_count,omitempty"`
	WorkerDeployCoverage      float64              `json:"worker_deploy_coverage,omitempty"`
	WProtoIntegrationScore    float64              `json:"wproto_integration_score,omitempty"`
	IsolatedCount             int                  `json:"isolated_count"`
	IsolatedRate              float64              `json:"isolated_rate"`
	GovernanceCoverage        float64              `json:"governance_coverage"`
	RACICoverage              float64              `json:"raci_coverage"`
	ContractScore             float64              `json:"contract_score"`
	CapabilityExportScore     float64              `json:"capability_export_score"`
	DepsLinkScore             float64              `json:"deps_link_score"`
	ResourceFlowScore         float64              `json:"resource_flow_score"`
	DIVScore                  float64              `json:"div_score"`
	ShannonScore              float64              `json:"shannon_score"`
	ImportEntropyScore        float64              `json:"import_entropy_score"`
	DuplicateImportScore      float64              `json:"duplicate_import_score"`
	IsolationPenalty          float64              `json:"isolation_penalty"`
	UnadaptedPenalty          float64              `json:"unadapted_penalty"`
	Scoring                   depsScoring          `json:"scoring"`
	// LLM-actionable improvement hints
	Hints []depsHint `json:"hints,omitempty"`
}

type depsHint struct {
	Severity   string   `json:"severity"`   // error | warning | info
	Score      string   `json:"score"`      // which score this affects
	Impact     string   `json:"impact"`     // estimated score gain
	Message    string   `json:"message"`    // human/LLM-readable instruction
	Components []string `json:"components"` // affected component IDs (sample)
	Count      int      `json:"count"`      // total affected count
}

type depsUISummary struct {
	TotalDomainDeps          int
	TotalGovernanceLinks     int
	TotalResolvedLinks       int
	TotalUnresolvedLinks     int
	GovernanceUnresolved     int
	TotalRbacBindings        int
	TotalCapabilities        int
	TotalDomainComponents    int
	TotalGovernedComponents  int
	RuntimeImports           int
	TotalRegisteredApps      int
	TotalWorkerDeployedApps  int
	WorkerDeployCoverage     float64
	WProtoIntegrationScore   float64
	AppWITDefinitionScore    float64
	AppWITDefinitionCoverage float64
	IsolatedCount            int
	IsolatedRate             float64
	HasIsolated              bool
	GovernanceCoverage       float64
	HasGovernanceCoverage    bool
	RACICoverage             float64
	HasRACICoverage          bool
	HasWorkerDeployCoverage  bool
	HasWProtoIntegration     bool
}

type depsHookRefreshResult struct {
	Triggered bool   `json:"triggered"`
	HookURL   string `json:"hook_url"`
	Event     string `json:"event"`
	AppID     string `json:"app_id"`
	Status    string `json:"status"`
	Message   string `json:"message,omitempty"`
}

type depsAuditReport struct {
	Mode    string                `json:"mode"`
	Refresh depsHookRefreshResult `json:"refresh"`
	Score   *depsScoreReport      `json:"score"`
}

func runDeps(args []string) error {
	if len(args) == 0 {
		printDepsUsage()
		return nil
	}
	switch args[0] {
	case "audit":
		return runDepsAudit(args[1:])
	case "export":
		return runDepsExport(args[1:])
	case "score":
		return runDepsScore(args[1:])
	case "governance-wit":
		return runDepsGovernanceWIT(args[1:])
	case "sql":
		return runDepsSql(args[1:])
	case "mv":
		return runDepsMV(args[1:])
	case "graph":
		return runDepsGraph(args[1:])
	case "drift":
		return runDepsDrift(args[1:])
	case "kv-sync":
		return runDepsKVSync(args[1:])
	case "help", "--help", "-h":
		printDepsUsage()
		return nil
	default:
		return fmt.Errorf("unknown deps command: %s", args[0])
	}
}

func printDepsUsage() {
	fmt.Printf(`gftd deps — evaluate deps.etzhayyim.com linker status and scoring

USAGE:
  gftd deps audit [flags]
  gftd deps export [flags]
  gftd deps score [flags]
  gftd deps governance-wit [flags]
  gftd deps sql [flags]
  gftd deps mv [flags]
  gftd deps graph [flags]
  gftd deps drift [flags]

COMMANDS:
  audit              Trigger deps full-audit refresh and evaluate score in one command
  export             Generate/export graph + score + audit JSON for ai-gftd-project-deps
  score              Fetch deps.etzhayyim.com data and compute app-mesh/governance score
  governance-wit     Evaluate whether an App implements governance WIT dependencies appropriately
  sql             Evaluate DID-based deps scoring via Sql graph (Multi-DID runtime scoring)
  mv                 Generate/apply RisingWave MVs for deps live read models from vertex_/edge_ tables
  graph              Visualize layer DAG (--format=tree|mermaid|dot|open) — reads root deps.toml layer rules
  drift              Compare non-ignored repo files/dirs against deps.toml declarations

Run 'gftd deps <command> --help' for command-specific flags.
`)
}

// --- Sql-based DID scoring (Multi-DID runtime evaluation) ---

type depsSqlReport struct {
	EvaluatedAt       string               `json:"evaluatedAt"`
	PdsURL            string               `json:"pdsUrl"`
	TotalDIDs         int                  `json:"totalDids"`
	ActiveDIDs        int                  `json:"activeDids"`
	ContractScore     float64              `json:"contractScore"`
	CapabilityScore   float64              `json:"capabilityScore"`
	DepsLinkScore     float64              `json:"depsLinkScore"`
	ResourceFlowScore float64              `json:"resourceFlowScore"`
	IsolationPenalty  float64              `json:"isolationPenalty"`
	OverallScore      float64              `json:"overallScore"`
	DIDs              []depsSqlDIDEntry `json:"dids,omitempty"`
}

type depsSqlDIDEntry struct {
	DID             string   `json:"did"`
	Path            string   `json:"path"`
	Depth           int      `json:"depth"`
	Status          string   `json:"status"`
	HasContract     bool     `json:"hasContract"`
	CapabilityCount int      `json:"capabilityCount,omitempty"`
	Capabilities    []string `json:"capabilities,omitempty"`
	DepsCount       int      `json:"depsCount"`
	FlowCount       int      `json:"flowCount"`
}

func runDepsSql(args []string) error {
	fs := flag.NewFlagSet("deps sql", flag.ContinueOnError)
	pdsURL := fs.String("pds-url", defaultPDSURL, "legacy field kept for report compatibility")
	outFormat := fs.String("format", "text", "output format: text or json")
	filterDID := fs.String("filter", "", "filter DIDs by prefix (e.g. did:web:isic-c)")
	timeoutSec := fs.Int("timeout-sec", 15, "database timeout in seconds")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	ctx, cancel := context.WithTimeout(context.Background(), time.Duration(*timeoutSec)*time.Second)
	defer cancel()
	componentRows, err := queryDepsComponentRows(ctx, *filterDID)
	if err != nil {
		return err
	}

	var dids []depsSqlDIDEntry
	withContract := 0
	withCapability := 0
	withDeps := 0
	withFlows := 0
	isolated := 0

	for _, row := range componentRows {
		did := row.DID
		path := ""
		depth := 0
		status := "active"
		capabilityCount := row.CapabilityVertexCount + row.CapabilityEdgeCount
		hasContract := row.GovernanceVertexCount+row.GovernanceEdgeCount > 0
		if hasContract {
			withContract++
		}
		if capabilityCount > 0 {
			withCapability++
		}
		if row.DependencyEdgeCount > 0 {
			withDeps++
		}
		if row.ResourceFlowCount > 0 {
			withFlows++
		}
		if row.Isolated {
			isolated++
		}

		dids = append(dids, depsSqlDIDEntry{
			DID:             did,
			Path:            path,
			Depth:           depth,
			Status:          status,
			HasContract:     hasContract,
			CapabilityCount: capabilityCount,
			DepsCount:       row.DependencyEdgeCount,
			FlowCount:       row.ResourceFlowCount,
		})
	}

	total := len(dids)
	if total == 0 {
		total = 1
	}
	contractScore := round1(100 * float64(withContract) / float64(total))
	capabilityScore := round1(100 * float64(withCapability) / float64(total))
	depsLinkScore := round1(100 * float64(withDeps) / float64(total))
	resourceFlowScore := round1(100 * float64(withFlows) / float64(total))
	isolationPenalty := round1(100 * float64(isolated) / float64(total))

	overall := 0.25*contractScore +
		0.25*capabilityScore +
		0.25*depsLinkScore +
		0.25*resourceFlowScore -
		0.20*isolationPenalty
	if overall < 0 {
		overall = 0
	}
	overall = round1(overall)

	report := depsSqlReport{
		EvaluatedAt:       time.Now().UTC().Format(time.RFC3339),
		PdsURL:            *pdsURL,
		TotalDIDs:         len(dids),
		ActiveDIDs:        len(dids),
		ContractScore:     contractScore,
		CapabilityScore:   capabilityScore,
		DepsLinkScore:     depsLinkScore,
		ResourceFlowScore: resourceFlowScore,
		IsolationPenalty:  isolationPenalty,
		OverallScore:      overall,
		DIDs:              dids,
	}

	if *outFormat == "json" {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	// Text output
	fmt.Printf("=== DID-based SQL Deps Scoring ===\n")
	fmt.Printf("Source:            %s\n", *pdsURL)
	fmt.Printf("Total DIDs:        %d\n", report.TotalDIDs)
	fmt.Printf("Contract Score:    %.1f%%  (%d/%d DIDs with :BOUND_BY → :Contract)\n", contractScore, withContract, len(dids))
	fmt.Printf("Capability Score:  %.1f%%  (%d/%d DIDs with :HAS_CAPABILITY)\n", capabilityScore, withCapability, len(dids))
	fmt.Printf("Deps Link Score:   %.1f%%  (%d/%d DIDs with :DEPENDS_ON)\n", depsLinkScore, withDeps, len(dids))
	fmt.Printf("Resource Flow:     %.1f%%  (%d/%d DIDs with resource flow edges)\n", resourceFlowScore, withFlows, len(dids))
	fmt.Printf("Isolation Penalty: %.1f%%  (%d/%d DIDs isolated)\n", isolationPenalty, isolated, len(dids))
	fmt.Printf("Overall Score:     %.1f\n", overall)
	fmt.Printf("\nModel: overall = 25%%*contract + 25%%*capability + 25%%*deps_link + 25%%*resource_flow - 20%%*isolation\n")
	if len(dids) > 0 && len(dids) <= 50 {
		fmt.Printf("\n--- DIDs ---\n")
		for _, d := range dids {
			contract := "✗"
			if d.HasContract {
				contract = "✓"
			}
			fmt.Printf("  %s  contract=%s caps=%d deps=%d flows=%d\n", d.DID, contract, d.CapabilityCount, d.DepsCount, d.FlowCount)
		}
	}
	return nil
}

type depsComponentLiveRow struct {
	DID                   string
	CapabilityVertexCount int
	CapabilityEdgeCount   int
	GovernanceVertexCount int
	GovernanceEdgeCount   int
	DependencyEdgeCount   int
	ResourceFlowCount     int
	Isolated              bool
}

func queryDepsComponentRows(ctx context.Context, filterDID string) ([]depsComponentLiveRow, error) {
	baseSQL := `
SELECT component_did,
       capability_vertex_count,
       capability_edge_count,
       governance_vertex_count,
       governance_edge_count,
       dependency_edge_count,
       resource_flow_count,
       isolated
FROM mv_deps_component_live`
	args := []any{}
	if strings.TrimSpace(filterDID) != "" {
		baseSQL += "\nWHERE component_did LIKE $1"
		args = append(args, strings.TrimSpace(filterDID)+"%")
	}
	baseSQL += "\nORDER BY component_did"

	res, err := db.RawQuery(ctx, baseSQL, args...)
	if err != nil {
		return nil, fmt.Errorf("query mv_deps_component_live: %w", err)
	}
	rows := make([]depsComponentLiveRow, 0, len(res.Rows))
	for _, row := range res.Rows {
		rows = append(rows, depsComponentLiveRow{
			DID:                   parseStringLike(row["component_did"]),
			CapabilityVertexCount: int(parseFloatLike(row["capability_vertex_count"])),
			CapabilityEdgeCount:   int(parseFloatLike(row["capability_edge_count"])),
			GovernanceVertexCount: int(parseFloatLike(row["governance_vertex_count"])),
			GovernanceEdgeCount:   int(parseFloatLike(row["governance_edge_count"])),
			DependencyEdgeCount:   int(parseFloatLike(row["dependency_edge_count"])),
			ResourceFlowCount:     int(parseFloatLike(row["resource_flow_count"])),
			Isolated:              parseBoolLike(row["isolated"]),
		})
	}
	return rows, nil
}

func parseBoolLike(v any) bool {
	switch t := v.(type) {
	case bool:
		return t
	case *bool:
		return t != nil && *t
	case string:
		return strings.EqualFold(strings.TrimSpace(t), "true") || strings.TrimSpace(t) == "1"
	case []byte:
		s := strings.TrimSpace(string(t))
		return strings.EqualFold(s, "true") || s == "1"
	default:
		return parseFloatLike(v) != 0
	}
}

func runDepsAudit(args []string) error {
	fs := flag.NewFlagSet("deps audit", flag.ContinueOnError)
	baseURL := fs.String("url", "https://deps.etzhayyim.com/", "deps base URL")
	outFormat := fs.String("format", "text", "output format: text or json")
	topN := fs.Int("top", 15, "number of top unresolved nodes to output")
	timeoutSec := fs.Int("timeout-sec", 20, "HTTP timeout in seconds")
	fullAudit := fs.Bool("full-audit", true, "trigger manual_refresh before score evaluation")
	event := fs.String("event", "manual_refresh", "hook event to trigger before scoring")
	appID := fs.String("app-id", "deps", "app_id included in manual hook payload")
	waitSec := fs.Int("wait-sec", 2, "seconds to wait after manual refresh before fetching score")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *topN <= 0 {
		return errors.New("--top must be greater than 0")
	}
	if *timeoutSec <= 0 {
		return errors.New("--timeout-sec must be greater than 0")
	}
	if *waitSec < 0 {
		return errors.New("--wait-sec must be >= 0")
	}

	refresh := depsHookRefreshResult{
		Triggered: false,
		Status:    "skipped",
		Event:     *event,
		AppID:     *appID,
	}
	client := &http.Client{Timeout: time.Duration(*timeoutSec) * time.Second}
	if *fullAudit {
		refreshed, err := triggerDepsManualRefresh(client, *baseURL, *event, *appID)
		if err != nil {
			return err
		}
		refresh = refreshed
		if *waitSec > 0 {
			time.Sleep(time.Duration(*waitSec) * time.Second)
		}
	}

	report, err := evaluateDepsScore(*baseURL, *topN, time.Duration(*timeoutSec)*time.Second)
	if err != nil {
		return err
	}

	audit := depsAuditReport{
		Mode:    "full-audit",
		Refresh: refresh,
		Score:   report,
	}
	if !*fullAudit {
		audit.Mode = "score-only"
	}

	switch strings.ToLower(strings.TrimSpace(*outFormat)) {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(audit)
	case "text":
		fmt.Printf("deps_audit:\n")
		fmt.Printf("  mode: %s\n", audit.Mode)
		fmt.Printf("  refresh_status: %s\n", audit.Refresh.Status)
		if audit.Refresh.HookURL != "" {
			fmt.Printf("  refresh_hook_url: %s\n", audit.Refresh.HookURL)
		}
		if audit.Refresh.Message != "" {
			fmt.Printf("  refresh_message: %s\n", audit.Refresh.Message)
		}
		printDepsScoreText(report)
		return nil
	default:
		return fmt.Errorf("unknown --format: %s", *outFormat)
	}
}

func runDepsExport(args []string) error {
	fs := flag.NewFlagSet("deps export", flag.ContinueOnError)
	projectDir := fs.String("project-dir", ".", "deps visualizer project directory")
	outDir := fs.String("out-dir", "src/lib/data", "output directory for exported JSON files")
	graphPath := fs.String("graph-path", "src/lib/data/wit-graph.json", "graph JSON path")
	scoreName := fs.String("score-name", "deps-score.json", "score JSON file name")
	auditName := fs.String("audit-name", "deps-audit.json", "audit JSON file name")
	appsName := fs.String("apps-name", "deps-apps.json", "registered apps JSON file name")
	qualityAuditName := fs.String("quality-audit-name", "wit-quality-audit.json", "detailed quality audit JSON file name")
	qualityPlanName := fs.String("quality-plan-name", "wit-quality-improvement-plan.md", "quality improvement plan markdown file name")
	sourceURL := fs.String("source-url", "/api/deps/graph", "source URL to embed in exported score/audit")
	topN := fs.Int("top", 15, "number of top unresolved nodes to include")
	refreshGraph := fs.Bool("refresh-graph", true, "refresh graph JSON before export")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *topN <= 0 {
		return errors.New("--top must be greater than 0")
	}

	root, err := filepath.Abs(*projectDir)
	if err != nil {
		return fmt.Errorf("resolve --project-dir: %w", err)
	}
	graphFile := resolveDepsPath(root, *graphPath)
	outputDir := resolveDepsPath(root, *outDir)
	scoreFile := filepath.Join(outputDir, filepath.Base(*scoreName))
	auditFile := filepath.Join(outputDir, filepath.Base(*auditName))
	appsFile := filepath.Join(outputDir, filepath.Base(*appsName))
	qualityAuditFile := filepath.Join(outputDir, filepath.Base(*qualityAuditName))
	qualityPlanFile := filepath.Join(outputDir, filepath.Base(*qualityPlanName))

	if *refreshGraph {
		if err := runDepsGraphGenerator(root); err != nil {
			return err
		}
	}
	graph, err := loadDepsGraphSnapshot(graphFile)
	if err != nil {
		return err
	}
	report, err := evaluateDepsScoreFromGraph(*sourceURL, *topN, graph)
	if err != nil {
		return err
	}
	audit := depsAuditReport{
		Mode: "export",
		Refresh: depsHookRefreshResult{
			Triggered: false,
			Status:    "skipped",
			Event:     "export",
			AppID:     "deps",
		},
		Score: report,
	}
	qualityAudit := buildDepsQualityAudit(graph)
	appRegistry := buildDepsAppRegistry(graph)

	if err := os.MkdirAll(outputDir, 0o755); err != nil {
		return fmt.Errorf("mkdir %s: %w", outputDir, err)
	}
	if err := writeDepsJSON(scoreFile, report); err != nil {
		return err
	}
	if err := writeDepsJSON(auditFile, audit); err != nil {
		return err
	}
	if err := writeDepsJSON(appsFile, appRegistry); err != nil {
		return err
	}
	if err := writeDepsJSON(qualityAuditFile, qualityAudit); err != nil {
		return err
	}
	if err := os.WriteFile(qualityPlanFile, []byte(makeDepsQualityPlanMarkdown(qualityAudit)), 0o644); err != nil {
		return fmt.Errorf("write %s: %w", qualityPlanFile, err)
	}

	fmt.Printf("deps_export:\n")
	fmt.Printf("  graph: %s\n", graphFile)
	fmt.Printf("  score: %s\n", scoreFile)
	fmt.Printf("  audit: %s\n", auditFile)
	fmt.Printf("  apps: %s\n", appsFile)
	fmt.Printf("  quality_audit: %s\n", qualityAuditFile)
	fmt.Printf("  quality_plan: %s\n", qualityPlanFile)
	fmt.Printf("  summary: %s\n", formatDepsScoreSummary(report))
	if len(report.Hints) > 0 {
		fmt.Printf("  hints: %d issues found\n", len(report.Hints))
		for _, h := range report.Hints {
			fmt.Printf("    [%s] %s: %s (count=%d)\n", h.Severity, h.Score, h.Impact, h.Count)
		}
	}
	return depsCheckErrors(report)
}

func triggerDepsManualRefresh(client *http.Client, baseURL, event, appID string) (depsHookRefreshResult, error) {
	hookURL, err := resolveURL(baseURL, "/api/hooks/component")
	if err != nil {
		return depsHookRefreshResult{}, err
	}
	body := map[string]any{
		"schema": "gftd:wproto/hook-envelope@v1",
		"event":  event,
		"app": map[string]any{
			"app_id": appID,
		},
	}
	buf, err := json.Marshal(body)
	if err != nil {
		return depsHookRefreshResult{}, fmt.Errorf("marshal manual refresh payload: %w", err)
	}
	req, err := http.NewRequest(http.MethodPost, hookURL, bytes.NewReader(buf))
	if err != nil {
		return depsHookRefreshResult{}, fmt.Errorf("create manual refresh request: %w", err)
	}
	req.Header.Set("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		return depsHookRefreshResult{}, fmt.Errorf("post manual refresh hook: %w", err)
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(io.LimitReader(resp.Body, 2048))
	result := depsHookRefreshResult{
		Triggered: true,
		HookURL:   hookURL,
		Event:     event,
		AppID:     appID,
		Status:    "accepted",
	}
	if len(respBody) > 0 {
		result.Message = string(respBody)
	}
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		result.Status = "failed"
		return result, fmt.Errorf("manual refresh hook failed: %s", strings.TrimSpace(string(respBody)))
	}
	return result, nil
}

func runDepsScore(args []string) error {
	fs := flag.NewFlagSet("deps score", flag.ContinueOnError)
	baseURL := fs.String("url", "https://deps.etzhayyim.com/", "deps base URL")
	outFormat := fs.String("format", "text", "output format: text or json")
	topN := fs.Int("top", 15, "number of top unresolved nodes to output")
	timeoutSec := fs.Int("timeout-sec", 20, "HTTP timeout in seconds")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}
	if *topN <= 0 {
		return errors.New("--top must be greater than 0")
	}
	if *timeoutSec <= 0 {
		return errors.New("--timeout-sec must be greater than 0")
	}

	report, err := evaluateDepsScore(*baseURL, *topN, time.Duration(*timeoutSec)*time.Second)
	if err != nil {
		return err
	}

	switch strings.ToLower(strings.TrimSpace(*outFormat)) {
	case "json":
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	case "text":
		printDepsScoreText(report)
		return depsCheckErrors(report)
	default:
		return fmt.Errorf("unknown --format: %s", *outFormat)
	}
}

func evaluateDepsScore(base string, topN int, timeout time.Duration) (*depsScoreReport, error) {
	client := &http.Client{Timeout: timeout}
	if graph, err := fetchDepsGraphSnapshot(client, base); err == nil {
		return evaluateDepsScoreFromGraph(base, topN, graph)
	}

	html, err := fetchText(client, base)
	if err != nil {
		return nil, fmt.Errorf("fetch deps page: %w", err)
	}

	nodesPath := nodesJSPathRegex.FindString(html)
	if nodesPath == "" {
		return nil, errors.New("could not locate nodes JS path from deps page")
	}
	nodesURL, err := resolveURL(base, nodesPath)
	if err != nil {
		return nil, err
	}

	js, err := fetchText(client, nodesURL)
	if err != nil {
		return nil, fmt.Errorf("fetch nodes JS: %w", err)
	}
	var status depsLinkerStatus
	m := moJSONRegex.FindStringSubmatch(js)
	if len(m) >= 2 {
		jsonText, err := decodeJSSingleQuoted(m[1])
		if err != nil {
			return nil, fmt.Errorf("decode linker status JSON: %w", err)
		}
		if err := json.Unmarshal([]byte(jsonText), &status); err != nil {
			return nil, fmt.Errorf("parse linker status JSON: %w", err)
		}
	}
	uiSummary := parseDepsUISummary(html)
	if parsedStatus, err := extractLinkerStatusFromNodeJS(js); err == nil {
		if status.GeneratedAt == "" {
			status.GeneratedAt = parsedStatus.GeneratedAt
		}
		if len(status.Links) == 0 && len(parsedStatus.Links) > 0 {
			status.Links = parsedStatus.Links
		}
		if status.Summary.TotalLinks == 0 && parsedStatus.Summary.TotalLinks > 0 {
			status.Summary.TotalComponents = parsedStatus.Summary.TotalComponents
			status.Summary.TotalLinks = parsedStatus.Summary.TotalLinks
			status.Summary.ResolvedLinks = parsedStatus.Summary.ResolvedLinks
			status.Summary.UnresolvedLinks = parsedStatus.Summary.UnresolvedLinks
		}
	}
	if len(status.Links) == 0 && status.Summary.TotalLinks == 0 {
		return nil, errors.New("could not locate linker status JSON in nodes JS")
	}
	return buildDepsScoreReport(base, topN, status, uiSummary), nil
}

func evaluateDepsScoreFromGraph(base string, topN int, graph *depsGraphSnapshot) (*depsScoreReport, error) {
	if graph == nil {
		return nil, errors.New("nil deps graph snapshot")
	}

	status := depsLinkerStatus{
		GeneratedAt: graph.GeneratedAt,
		Components:  graph.LinkerStatus.Components,
		Links:       graph.LinkerStatus.Links,
		Summary:     graph.LinkerStatus.Summary,
	}
	if status.Summary.TotalLinks == 0 {
		status.Summary.TotalLinks = graph.Summary.TotalResolvedLinks + graph.Summary.TotalUnresolvedLinks
	}
	if status.Summary.TotalComponents == 0 {
		status.Summary.TotalComponents = graph.Summary.TotalLinkerComponents
	}
	if status.Summary.ResolvedLinks == 0 {
		status.Summary.ResolvedLinks = graph.Summary.TotalResolvedLinks
	}
	if status.Summary.UnresolvedLinks == 0 {
		status.Summary.UnresolvedLinks = graph.Summary.TotalUnresolvedLinks
	}

	uiSummary := depsUISummary{
		TotalDomainDeps:          graph.Summary.TotalDomainDeps,
		TotalGovernanceLinks:     graph.Summary.TotalGovernanceLinks,
		TotalResolvedLinks:       graph.Summary.TotalResolvedLinks,
		TotalUnresolvedLinks:     graph.Summary.TotalUnresolvedLinks,
		GovernanceUnresolved:     graph.Summary.GovernanceUnresolvedCount,
		TotalRbacBindings:        graph.Summary.TotalRbacBindings,
		TotalCapabilities:        graph.Summary.TotalCapabilities,
		TotalDomainComponents:    graph.Summary.TotalDomainComponents,
		TotalGovernedComponents:  graph.Summary.TotalGovernedComponents,
		RuntimeImports:           graph.Summary.RuntimeImports,
		TotalRegisteredApps:      graph.Summary.TotalRegisteredApps,
		TotalWorkerDeployedApps:  graph.Summary.TotalWorkerDeployedApps,
		WorkerDeployCoverage:     graph.Summary.WorkerDeployCoverageRate,
		WProtoIntegrationScore:   graph.Summary.WProtoIntegrationScore,
		AppWITDefinitionScore:    graph.Summary.AppWITDefinitionScore,
		AppWITDefinitionCoverage: 0,
		IsolatedCount:            graph.Summary.TotalIsolatedComponents,
		IsolatedRate:             graph.Summary.IsolatedComponentsRate,
		GovernanceCoverage:       graph.Summary.GovernanceCoverageRate,
		RACICoverage:             graph.Summary.ExplicitRaciCoverageRate,
		HasIsolated:              true,
		HasGovernanceCoverage:    true,
		HasRACICoverage:          true,
		HasWorkerDeployCoverage:  graph.Summary.WorkerDeployCoverageRate > 0 || graph.Summary.TotalRegisteredApps > 0,
		HasWProtoIntegration:     graph.Summary.WProtoIntegrationScore > 0 || graph.Summary.TotalRegisteredApps > 0,
	}
	if graph.Scorecard != nil {
		uiSummary.AppWITDefinitionCoverage = graph.Scorecard.AppWITDefinitionCoverage
		if graph.Scorecard.WorkerRegisteredAppCount > 0 {
			uiSummary.TotalRegisteredApps = graph.Scorecard.WorkerRegisteredAppCount
		}
		if graph.Scorecard.WorkerDeployedAppCount > 0 {
			uiSummary.TotalWorkerDeployedApps = graph.Scorecard.WorkerDeployedAppCount
		}
		if graph.Scorecard.WorkerDeployCoverageRate > 0 {
			uiSummary.WorkerDeployCoverage = graph.Scorecard.WorkerDeployCoverageRate
		}
		if graph.Scorecard.WProtoIntegrationScore > 0 {
			uiSummary.WProtoIntegrationScore = graph.Scorecard.WProtoIntegrationScore
		}
		if graph.Scorecard.IsolatedComponentsCount > 0 {
			uiSummary.IsolatedCount = graph.Scorecard.IsolatedComponentsCount
		}
		if graph.Scorecard.IsolatedComponentsRate > 0 {
			uiSummary.IsolatedRate = graph.Scorecard.IsolatedComponentsRate
		}
		if graph.Scorecard.GovernanceCoverageRate > 0 {
			uiSummary.GovernanceCoverage = graph.Scorecard.GovernanceCoverageRate
		}
		if graph.Scorecard.ExplicitRaciCoverageRate > 0 {
			uiSummary.RACICoverage = graph.Scorecard.ExplicitRaciCoverageRate
		}
		if graph.Scorecard.GovernanceUnresolvedCount > 0 {
			uiSummary.GovernanceUnresolved = graph.Scorecard.GovernanceUnresolvedCount
		}
	}

	return buildDepsScoreReport(base, topN, status, uiSummary), nil
}

type shannonMetricsResult struct {
	ShannonScore         float64
	ImportEntropyScore   float64
	DuplicateImportScore float64
}

// calcShannonMetrics measures Shannon redundancy across WIT import namespaces.
// Import Entropy: how evenly imports are distributed across namespaces (higher = less redundant).
// Duplicate Import Detection: ratio of unique import sets to total components (higher = fewer dupes).
func calcShannonMetrics(status depsLinkerStatus) shannonMetricsResult {
	if len(status.Components) == 0 {
		return shannonMetricsResult{}
	}

	// (a) Import Entropy: namespace frequency across all components
	nsFreq := map[string]int{}
	totalNSImports := 0
	// (b) Duplicate Import Detection: hash each component's sorted import list
	importSetHashes := map[string]int{}

	for _, comp := range status.Components {
		for _, imp := range comp.Imports {
			ns := extractWITNamespace(imp)
			if ns != "" {
				nsFreq[ns]++
				totalNSImports++
			}
		}
		// Build sorted import list hash for duplicate detection
		sorted := make([]string, len(comp.Imports))
		copy(sorted, comp.Imports)
		sort.Strings(sorted)
		key := strings.Join(sorted, "\x00")
		importSetHashes[key]++
	}

	// (a) Shannon entropy H = -Σ(p_i * log2(p_i)), normalized to 0-100
	importEntropyScore := 0.0
	numUniqueNS := len(nsFreq)
	if numUniqueNS > 1 && totalNSImports > 0 {
		entropy := 0.0
		for _, count := range nsFreq {
			p := float64(count) / float64(totalNSImports)
			if p > 0 {
				entropy -= p * math.Log2(p)
			}
		}
		hMax := math.Log2(float64(numUniqueNS))
		if hMax > 0 {
			importEntropyScore = (entropy / hMax) * 100.0
		}
	} else if numUniqueNS == 1 {
		// Single namespace = no diversity
		importEntropyScore = 0.0
	}

	// (b) Duplicate import: unique sets / total components * 100
	duplicateImportScore := 0.0
	uniqueSets := len(importSetHashes)
	totalComps := len(status.Components)
	if totalComps > 0 {
		duplicateImportScore = (float64(uniqueSets) / float64(totalComps)) * 100.0
	}

	// (c) Combined: 60% entropy + 40% duplicate
	shannonScore := 0.60*importEntropyScore + 0.40*duplicateImportScore

	return shannonMetricsResult{
		ShannonScore:         shannonScore,
		ImportEntropyScore:   importEntropyScore,
		DuplicateImportScore: duplicateImportScore,
	}
}

// extractWITNamespace extracts the package namespace from a WIT import string.
// e.g. "magatama:core/types" -> "magatama:core", "gftd:handotai/article" -> "gftd:handotai",
// "wasi:http/handler" -> "wasi:http"
func extractWITNamespace(imp string) string {
	// WIT imports have format "namespace:package/interface"
	slashIdx := strings.Index(imp, "/")
	if slashIdx > 0 {
		return imp[:slashIdx]
	}
	// No slash — use full string if it contains ":"
	if strings.Contains(imp, ":") {
		return imp
	}
	return ""
}

func buildDepsScoreReport(base string, topN int, status depsLinkerStatus, uiSummary depsUISummary) *depsScoreReport {
	unresolved := make([]depsLinkEntry, 0, len(status.Links))
	resolved := make([]depsLinkEntry, 0, len(status.Links))
	for _, link := range status.Links {
		if link.Status == "unresolved" {
			unresolved = append(unresolved, link)
		} else if link.Status == "resolved" {
			resolved = append(resolved, link)
		}
	}

	unresolvedByKind := map[string]int{}
	componentUnresolved := map[string]int{}
	govRefsByNode := map[string]map[string]struct{}{}
	govUnresolvedCount := 0

	for _, link := range unresolved {
		unresolvedByKind[link.Kind]++
		nodeKey := link.Project + "::" + link.ComponentID
		componentUnresolved[nodeKey]++

		if strings.Contains(strings.ToLower(link.Ref), "governance") || strings.Contains(strings.ToLower(link.Kind), "governance") {
			govUnresolvedCount++
			if _, ok := govRefsByNode[nodeKey]; !ok {
				govRefsByNode[nodeKey] = map[string]struct{}{}
			}
			govRefsByNode[nodeKey][link.Ref] = struct{}{}
		}
	}

	topNodes := make([]depsNodeScore, 0, len(componentUnresolved))
	for key, count := range componentUnresolved {
		project, comp := splitNodeKey(key)
		topNodes = append(topNodes, depsNodeScore{
			Project:         project,
			ComponentID:     comp,
			UnresolvedLinks: count,
		})
	}
	sort.Slice(topNodes, func(i, j int) bool {
		if topNodes[i].UnresolvedLinks != topNodes[j].UnresolvedLinks {
			return topNodes[i].UnresolvedLinks > topNodes[j].UnresolvedLinks
		}
		if topNodes[i].Project != topNodes[j].Project {
			return topNodes[i].Project < topNodes[j].Project
		}
		return topNodes[i].ComponentID < topNodes[j].ComponentID
	})
	if len(topNodes) > topN {
		topNodes = topNodes[:topN]
	}

	govNodes := make([]depsGovernanceNode, 0, len(govRefsByNode))
	for key, refsSet := range govRefsByNode {
		project, comp := splitNodeKey(key)
		refs := make([]string, 0, len(refsSet))
		for ref := range refsSet {
			refs = append(refs, ref)
		}
		sort.Strings(refs)
		govNodes = append(govNodes, depsGovernanceNode{
			Project:                 project,
			ComponentID:             comp,
			UnresolvedGovernanceRef: refs,
		})
	}
	sort.Slice(govNodes, func(i, j int) bool {
		if len(govNodes[i].UnresolvedGovernanceRef) != len(govNodes[j].UnresolvedGovernanceRef) {
			return len(govNodes[i].UnresolvedGovernanceRef) > len(govNodes[j].UnresolvedGovernanceRef)
		}
		if govNodes[i].Project != govNodes[j].Project {
			return govNodes[i].Project < govNodes[j].Project
		}
		return govNodes[i].ComponentID < govNodes[j].ComponentID
	})

	totalLinks := len(status.Links)
	if totalLinks == 0 {
		totalLinks = status.Summary.TotalLinks
	}
	resolvedCount := len(resolved)
	if resolvedCount == 0 && status.Summary.ResolvedLinks > 0 {
		resolvedCount = status.Summary.ResolvedLinks
	}
	if resolvedCount == 0 && uiSummary.TotalResolvedLinks > 0 {
		resolvedCount = uiSummary.TotalResolvedLinks
	}
	unresolvedCount := len(unresolved)
	if unresolvedCount == 0 && status.Summary.UnresolvedLinks > 0 {
		unresolvedCount = status.Summary.UnresolvedLinks
	}
	if unresolvedCount == 0 && uiSummary.TotalUnresolvedLinks > 0 {
		unresolvedCount = uiSummary.TotalUnresolvedLinks
	}
	if govUnresolvedCount == 0 {
		govUnresolvedCount = uiSummary.GovernanceUnresolved
	}

	totalAppMeshLinks := 0
	resolvedAppMeshLinks := 0
	totalRuntimeHostLinks := 0
	resolvedRuntimeHostLinks := 0
	for _, link := range status.Links {
		if isRuntimeHostRef(link.Ref) {
			totalRuntimeHostLinks++
			if link.Status == "resolved" {
				resolvedRuntimeHostLinks++
			}
			continue
		}
		totalAppMeshLinks++
		if link.Status == "resolved" {
			resolvedAppMeshLinks++
		}
	}

	linkCoverageRate := ratio(resolvedCount, totalLinks)
	unresolvedRate := ratio(unresolvedCount, totalLinks)
	appMeshCoverageRate := ratio(resolvedAppMeshLinks, totalAppMeshLinks)
	appMeshUnresolvedRate := ratio(totalAppMeshLinks-resolvedAppMeshLinks, totalAppMeshLinks)
	runtimeHostCoverageRate := ratio(resolvedRuntimeHostLinks, totalRuntimeHostLinks)
	domainComponents := maxInt(uiSummary.TotalDomainComponents, status.Summary.TotalComponents)
	governedComponents := uiSummary.TotalGovernedComponents
	totalGovernanceLinks := uiSummary.TotalGovernanceLinks
	totalDomainDeps := uiSummary.TotalDomainDeps
	totalRbacBindings := uiSummary.TotalRbacBindings
	totalCapabilities := uiSummary.TotalCapabilities
	runtimeImports := uiSummary.RuntimeImports
	appWITDefinitionScoreRatio := cap01(uiSummary.AppWITDefinitionScore / 100.0)
	appWITDefinitionCoverage := cap01(uiSummary.AppWITDefinitionCoverage)
	hasAppWITDefinition := appWITDefinitionScoreRatio > 0 || appWITDefinitionCoverage > 0
	isolatedCount := uiSummary.IsolatedCount
	isolatedRate := cap01(uiSummary.IsolatedRate)
	if uiSummary.HasIsolated && isolatedRate == 0 && isolatedCount > 0 {
		isolatedRate = ratio(isolatedCount, maxInt(domainComponents, 1))
	}
	governanceCoverage := cap01(uiSummary.GovernanceCoverage)
	raciCoverage := cap01(uiSummary.RACICoverage)
	isolationPenalty := 0.0
	unadaptedPenalty := 0.0
	hasPenaltyInput := false
	if uiSummary.HasIsolated {
		isolationPenalty = isolatedRate
		hasPenaltyInput = true
	}
	unadaptedDeficits := 0.0
	unadaptedCount := 0
	if uiSummary.HasGovernanceCoverage {
		unadaptedDeficits += 1 - governanceCoverage
		unadaptedCount++
		hasPenaltyInput = true
	}
	if uiSummary.HasRACICoverage {
		unadaptedDeficits += 1 - raciCoverage
		unadaptedCount++
		hasPenaltyInput = true
	}
	if unadaptedCount > 0 {
		unadaptedPenalty = unadaptedDeficits / float64(unadaptedCount)
	}

	policyCoverage := ratio(governedComponents, domainComponents)
	governanceLinkCoverage := cap01(ratio(totalGovernanceLinks, maxInt(totalDomainDeps, 1)))
	governanceHealth := 1 - cap01(float64(govUnresolvedCount)/25.0)
	rbacCoverage := cap01(float64(totalRbacBindings) / math.Max(1, float64(maxInt(governedComponents, 1))/40.0))
	capabilityCoverage := cap01(float64(totalCapabilities) / math.Max(1, float64(maxInt(domainComponents, 1))/8.0))
	runtimeImportHealth := cap01(float64(runtimeImports) / 50.0)

	buildLinkerScore := 0.0
	if hasAppWITDefinition {
		buildLinkerScore = 100 * (0.25*policyCoverage +
			0.20*governanceLinkCoverage +
			0.20*capabilityCoverage +
			0.10*rbacCoverage +
			0.10*governanceHealth +
			0.15*appWITDefinitionCoverage)
	} else {
		buildLinkerScore = 100 * (0.30*policyCoverage +
			0.20*governanceLinkCoverage +
			0.20*capabilityCoverage +
			0.15*rbacCoverage +
			0.15*governanceHealth)
	}
	runtimeLinkerScore := 100 * (0.55*linkCoverageRate +
		0.20*governanceHealth +
		0.15*runtimeImportHealth +
		0.10*(1-cap01(unresolvedRate*1.1)))
	appMeshScore := 100 * (0.70*appMeshCoverageRate +
		0.20*governanceHealth +
		0.10*(1-cap01(appMeshUnresolvedRate*1.1)))
	runtimeHostScore := 100 * (0.60*runtimeHostCoverageRate +
		0.25*runtimeImportHealth +
		0.15*governanceHealth)
	linkBlendScore := 0.50*buildLinkerScore + 0.20*runtimeLinkerScore + 0.30*appMeshScore
	// Contract/Capability scoring: evaluate WIT export/import quality.
	// Count COMPONENTS (not lines) that have at least one contract import / capability export.
	contractImportCount := 0
	capabilityExportCount := 0
	depsLinkResolvedCount := 0
	depsLinkTotalCount := 0
	for _, comp := range status.Components {
		hasContract := false
		hasCapability := false
		for _, imp := range comp.Imports {
			if strings.Contains(imp, "contract/agreement") || strings.Contains(imp, "contract/registry") {
				hasContract = true
			}
			// Domain deps (non-runtime, non-wasi imports)
			if !isRuntimeHostRef(imp) && !strings.HasPrefix(imp, "wasi:") && !strings.HasPrefix(imp, "magatama:") {
				depsLinkTotalCount++
			}
		}
		for _, exp := range comp.Exports {
			if !strings.HasPrefix(exp, "magatama:") && !strings.HasPrefix(exp, "wasi:") {
				hasCapability = true
			}
		}
		if hasContract {
			contractImportCount++
		}
		if hasCapability {
			capabilityExportCount++
		}
	}
	for _, link := range status.Links {
		if !isRuntimeHostRef(link.Ref) && !strings.HasPrefix(link.Ref, "wasi:") && !strings.HasPrefix(link.Ref, "magatama:") {
			if link.Status == "resolved" {
				depsLinkResolvedCount++
			}
		}
	}
	contractScore := cap01(float64(contractImportCount) / math.Max(1, float64(len(status.Components))))
	capabilityExportScore := cap01(float64(capabilityExportCount) / math.Max(1, float64(len(status.Components))))
	depsLinkScore := cap01(ratio(depsLinkResolvedCount, maxInt(depsLinkTotalCount, 1)))
	// Resource-flow scoring: evaluate gov-resource-flow WIT coverage.
	// Components that import or export gftd:gov-resource-flow/* get credit.
	resourceFlowCount := 0
	for _, comp := range status.Components {
		hasRF := false
		for _, imp := range comp.Imports {
			if strings.Contains(imp, "gov-resource-flow/") || strings.Contains(imp, "resource-flow/") {
				hasRF = true
				break
			}
		}
		if !hasRF {
			for _, exp := range comp.Exports {
				if strings.Contains(exp, "gov-resource-flow/") || strings.Contains(exp, "resource-flow/") {
					hasRF = true
					break
				}
			}
		}
		if hasRF {
			resourceFlowCount++
		}
	}
	resourceFlowScore := cap01(float64(resourceFlowCount) / math.Max(1, float64(len(status.Components))))
	// DIV scoring: evaluate magatama:div WIT coverage (information, documents, materiel).
	divCount := 0
	for _, comp := range status.Components {
		hasDIV := false
		for _, imp := range comp.Imports {
			if strings.Contains(imp, "div/information") || strings.Contains(imp, "div/documents") || strings.Contains(imp, "div/materiel") {
				hasDIV = true
				break
			}
		}
		if hasDIV {
			divCount++
		}
	}
	divScore := cap01(float64(divCount) / math.Max(1, float64(len(status.Components))))

	// Shannon redundancy metrics
	shannonMetrics := calcShannonMetrics(status)
	shannonScore := shannonMetrics.ShannonScore / 100.0 // normalize to 0-1 for formula

	dodafV2Score := 100 * (0.15*policyCoverage +
		0.15*governanceLinkCoverage +
		0.15*governanceHealth +
		0.10*capabilityCoverage +
		0.15*contractScore +
		0.10*capabilityExportScore +
		0.10*resourceFlowScore +
		0.10*divScore)
	nistCSFV2Score := 100 * (0.35*rbacCoverage +
		0.30*governanceHealth +
		0.20*capabilityCoverage +
		0.15*linkCoverageRate)
	overallScore := 0.0
	model := ""
	if hasAppWITDefinition {
		overallScore = 0.40*linkBlendScore +
			0.10*dodafV2Score +
			0.10*nistCSFV2Score +
			0.05*(appWITDefinitionScoreRatio*100.0) +
			0.05*(contractScore*100.0) +
			0.05*(capabilityExportScore*100.0) +
			0.10*(depsLinkScore*100.0) +
			0.05*(resourceFlowScore*100.0) +
			0.05*(divScore*100.0) +
			0.05*(shannonScore*100.0)
		model = "overall = 40%*link_blend + 10%*dodaf_v2 + 10%*nist_csf_v2 + 5%*app_wit + 5%*contract + 5%*capability_export + 10%*deps_link + 5%*resource_flow + 5%*div + 5%*shannon; shannon = 60%*import_entropy + 40%*duplicate_import; div = magatama:div WIT coverage (DIV-3 information/documents/materiel)"
	} else {
		overallScore = 0.45*linkBlendScore +
			0.10*dodafV2Score +
			0.10*nistCSFV2Score +
			0.05*(contractScore*100.0) +
			0.05*(capabilityExportScore*100.0) +
			0.10*(depsLinkScore*100.0) +
			0.05*(resourceFlowScore*100.0) +
			0.05*(divScore*100.0) +
			0.05*(shannonScore*100.0)
		model = "overall = 45%*link_blend + 10%*dodaf_v2 + 10%*nist_csf_v2 + 5%*contract + 5%*capability_export + 10%*deps_link + 5%*resource_flow + 5%*div + 5%*shannon; shannon = 60%*import_entropy + 40%*duplicate_import"
	}
	if hasPenaltyInput {
		penaltyScore := 100 * (0.60*isolationPenalty + 0.40*unadaptedPenalty)
		overallScore -= penaltyScore
		if overallScore < 0 {
			overallScore = 0
		}
		model += "; badge penalty = 60%*isolation + 40%*unadapted deficits, applied only when badge data is present"
	}

	buildLinkerScore = round1(buildLinkerScore)
	runtimeLinkerScore = round1(runtimeLinkerScore)
	appMeshScore = round1(appMeshScore)
	runtimeHostScore = round1(runtimeHostScore)
	linkBlendScore = round1(linkBlendScore)
	dodafV2Score = round1(dodafV2Score)
	nistCSFV2Score = round1(nistCSFV2Score)
	overallScore = round1(overallScore)
	contractScore = round1(100 * contractScore)
	capabilityExportScore = round1(100 * capabilityExportScore)
	depsLinkScore = round1(100 * depsLinkScore)
	resourceFlowScore = round1(100 * resourceFlowScore)
	divScore = round1(100 * divScore)
	shannonScoreRounded := round1(shannonMetrics.ShannonScore)
	importEntropyScore := round1(shannonMetrics.ImportEntropyScore)
	duplicateImportScore := round1(shannonMetrics.DuplicateImportScore)
	isolationPenalty = round1(100 * isolationPenalty)
	unadaptedPenalty = round1(100 * unadaptedPenalty)

	// Generate LLM-actionable improvement hints
	hints := generateDepsHints(status, len(status.Components),
		contractImportCount, capabilityExportCount,
		resourceFlowCount, divCount,
		depsLinkResolvedCount, depsLinkTotalCount,
		isolatedCount, unresolvedCount,
		contractScore, capabilityExportScore, depsLinkScore,
		resourceFlowScore, divScore, isolationPenalty)

	return &depsScoreReport{
		EvaluatedAt:               time.Now().UTC().Format(time.RFC3339),
		SourceURL:                 base,
		GeneratedAt:               status.GeneratedAt,
		TotalLinks:                totalLinks,
		ResolvedCount:             resolvedCount,
		UnresolvedCount:           unresolvedCount,
		LinkCoverageRate:          round4(linkCoverageRate),
		UnresolvedRate:            round4(unresolvedRate),
		UnresolvedByKind:          unresolvedByKind,
		GovernanceUnresolvedCount: govUnresolvedCount,
		GovernanceUnresolvedNodes: govNodes,
		TopUnresolvedNodes:        topNodes,
		WorkerRegisteredAppCount:  uiSummary.TotalRegisteredApps,
		WorkerDeployedAppCount:    uiSummary.TotalWorkerDeployedApps,
		WorkerDeployCoverage:      round4(uiSummary.WorkerDeployCoverage),
		WProtoIntegrationScore:    round1(uiSummary.WProtoIntegrationScore),
		IsolatedCount:             isolatedCount,
		IsolatedRate:              round4(isolatedRate),
		GovernanceCoverage:        round4(governanceCoverage),
		RACICoverage:              round4(raciCoverage),
		ContractScore:             contractScore,
		CapabilityExportScore:     capabilityExportScore,
		DepsLinkScore:             depsLinkScore,
		ResourceFlowScore:         resourceFlowScore,
		DIVScore:                  divScore,
		ShannonScore:              shannonScoreRounded,
		ImportEntropyScore:        importEntropyScore,
		DuplicateImportScore:      duplicateImportScore,
		IsolationPenalty:          isolationPenalty,
		UnadaptedPenalty:          unadaptedPenalty,
		Scoring: depsScoring{
			Model:                    model,
			OverallScore:             overallScore,
			LinkBlendScore:           linkBlendScore,
			BuildLinkerScore:         buildLinkerScore,
			RuntimeLinkerScore:       runtimeLinkerScore,
			AppMeshScore:             appMeshScore,
			RuntimeHostScore:         runtimeHostScore,
			DoDAFV2Score:             dodafV2Score,
			NISTCSFV2Score:           nistCSFV2Score,
			AppWITDefinitionScore:    round1(appWITDefinitionScoreRatio * 100.0),
			AppWITDefinitionCoverage: round4(appWITDefinitionCoverage),
			ContractScore:            contractScore,
			CapabilityExportScore:    capabilityExportScore,
			DepsLinkScore:            depsLinkScore,
			ResourceFlowScore:        resourceFlowScore,
			DIVScore:                 divScore,
			ShannonScore:             shannonScoreRounded,
			ImportEntropyScore:       importEntropyScore,
			DuplicateImportScore:     duplicateImportScore,
			IsolationPenalty:         isolationPenalty,
			UnadaptedPenalty:         unadaptedPenalty,
			BuildLinkerFactors: depsStageScoreFactors{
				LinkCoverage:             round4(governanceLinkCoverage),
				PolicyCoverage:           round4(policyCoverage),
				GovernanceHealth:         round4(governanceHealth),
				RBACCoverage:             round4(rbacCoverage),
				CapabilityCoverage:       round4(capabilityCoverage),
				AppWITDefinitionCoverage: round4(appWITDefinitionCoverage),
				IsolatedRate:             round4(isolatedRate),
				GovernanceCoverage:       round4(governanceCoverage),
				RACICoverage:             round4(raciCoverage),
			},
			RuntimeLinkerFactors: depsStageScoreFactors{
				LinkCoverage:        round4(linkCoverageRate),
				GovernanceHealth:    round4(governanceHealth),
				RuntimeImportHealth: round4(runtimeImportHealth),
				RBACCoverage:        round4(rbacCoverage),
				CapabilityCoverage:  round4(capabilityCoverage),
			},
			AppMeshFactors: depsStageScoreFactors{
				LinkCoverage:       round4(appMeshCoverageRate),
				GovernanceHealth:   round4(governanceHealth),
				GovernanceCoverage: round4(governanceCoverage),
				RACICoverage:       round4(raciCoverage),
				IsolatedRate:       round4(isolatedRate),
			},
			RuntimeHostFactors: depsStageScoreFactors{
				LinkCoverage:        round4(runtimeHostCoverageRate),
				GovernanceHealth:    round4(governanceHealth),
				RuntimeImportHealth: round4(runtimeImportHealth),
			},
			ComplianceFactors: depsComplianceFactors{
				DoDAFV2:   round4(dodafV2Score / 100),
				NISTCSFV2: round4(nistCSFV2Score / 100),
			},
		},
		Hints: hints,
	}
}

func depsCheckErrors(report *depsScoreReport) error {
	if report == nil {
		return nil
	}
	var errs []string
	for _, h := range report.Hints {
		if h.Severity == "error" {
			errs = append(errs, fmt.Sprintf("[%s] %s: %d components — %s", h.Severity, h.Score, h.Count, h.Impact))
		}
	}
	if len(errs) == 0 {
		return nil
	}
	msg := fmt.Sprintf("deps linker: %d error(s) found\n", len(errs))
	for _, e := range errs {
		msg += "  " + e + "\n"
	}
	msg += "Run `gftd deps export --format json` for component-level details and fix instructions."
	return errors.New(msg)
}

func generateDepsHints(status depsLinkerStatus, totalComponents int,
	contractCount, capabilityCount, resourceFlowCount, divCount int,
	depsLinkResolved, depsLinkTotal int,
	isolatedCount, unresolvedCount int,
	contractScore, capabilityScore, depsLinkScore float64,
	resourceFlowScore, divScore, isolationPenalty float64,
) []depsHint {
	var hints []depsHint
	maxSample := 10

	// Collect per-component deficiencies
	var noContract, noCapability, noResourceFlow, noDIV []string
	staleImports := map[string][]string{} // component → stale import refs

	for _, comp := range status.Components {
		cid := comp.Project + "/" + comp.ComponentID
		hasContract := false
		hasCapability := false
		hasRF := false
		hasDIV := false

		for _, imp := range comp.Imports {
			if strings.Contains(imp, "contract/agreement") || strings.Contains(imp, "contract/registry") {
				hasContract = true
			}
			if strings.Contains(imp, "gov-resource-flow/") || strings.Contains(imp, "resource-flow/") {
				hasRF = true
			}
			if strings.Contains(imp, "div/information") || strings.Contains(imp, "div/documents") || strings.Contains(imp, "div/materiel") {
				hasDIV = true
			}
			// Detect stale imports (old namespaces that are unresolvable)
			if strings.Contains(imp, "gftd:resource-flow/resource-flow@0.1.0") ||
				strings.Contains(imp, "gftd:platform/") {
				staleImports[cid] = append(staleImports[cid], imp)
			}
		}
		for _, exp := range comp.Exports {
			if !strings.HasPrefix(exp, "magatama:") && !strings.HasPrefix(exp, "wasi:") {
				hasCapability = true
			}
		}

		if !hasContract {
			noContract = append(noContract, cid)
		}
		if !hasCapability {
			noCapability = append(noCapability, cid)
		}
		if !hasRF {
			noResourceFlow = append(noResourceFlow, cid)
		}
		if !hasDIV {
			noDIV = append(noDIV, cid)
		}
	}

	sample := func(items []string) []string {
		if len(items) <= maxSample {
			return items
		}
		return items[:maxSample]
	}

	// === Contract hints ===
	if len(noContract) > 0 {
		gain := fmt.Sprintf("contract_score %.1f → %.1f (+%.1f)", contractScore, 100.0, 100.0-contractScore)
		severity := "error" // contract import is mandatory — always error
		hints = append(hints, depsHint{
			Severity:   severity,
			Score:      "contract_score",
			Impact:     gain,
			Count:      len(noContract),
			Components: sample(noContract),
			Message: fmt.Sprintf(
				"%d components are missing `import magatama:contract/agreement@1.0.0;` in world.wit. "+
					"Each app must import contract/agreement — the legal/contractual basis for the app. "+
					"Read the app's CLAUDE.md to determine the appropriate contract-category "+
					"(statute for government, international-standard for UN classifications, charter for orgs, "+
					"service-agreement for SaaS, employment for workforce). "+
					"DO NOT bulk-add the same contract to all apps — analyze each domain individually.",
				len(noContract)),
		})
	}

	// === Capability export hints ===
	if len(noCapability) > 0 {
		gain := fmt.Sprintf("capability_export_score %.1f → %.1f (+%.1f)", capabilityScore, 100.0, 100.0-capabilityScore)
		severity := "error" // capability export is mandatory — always error
		hints = append(hints, depsHint{
			Severity:   severity,
			Score:      "capability_export_score",
			Impact:     gain,
			Count:      len(noCapability),
			Components: sample(noCapability),
			Message: fmt.Sprintf(
				"%d components have no domain capability export in world.wit. "+
					"Each app must `export gftd:{domain}/{capability}@1.0.0;` reflecting what the app actually provides. "+
					"The export interface must be defined in `projects/{project}/wit/{domain}/package.wit`. "+
					"Generic exports like `/capability` are discouraged — use domain-specific names "+
					"(e.g., gftd:gov-jpn-moj/criminal-affairs, gftd:isic-c/manufacturing-10). "+
					"DO NOT bulk-add generic exports — analyze each app's business function.",
				len(noCapability)),
		})
	}

	// === Resource flow hints ===
	if len(noResourceFlow) > 0 && resourceFlowScore < 95 {
		hints = append(hints, depsHint{
			Severity:   "info",
			Score:      "resource_flow_score",
			Impact:     fmt.Sprintf("resource_flow_score %.1f → higher", resourceFlowScore),
			Count:      len(noResourceFlow),
			Components: sample(noResourceFlow),
			Message: fmt.Sprintf(
				"%d components have no resource-flow WIT coverage. "+
					"Only add resource-flow imports where domain-appropriate: "+
					"government apps → magatama:gov-resource-flow/{personnel,assets,budget}; "+
					"industry apps → gftd:isic-resource-flow/{labor,materials,capital,products}; "+
					"workforce apps → gftd:isco-workforce-flow/{mobility,compensation,skills}. "+
					"Apps without resource tracking (SaaS tools, UI-only) should NOT import resource-flow. "+
					"Use magatama: prefix for resource-flow imports to avoid deps_link_score penalty.",
				len(noResourceFlow)),
		})
	}

	// === DIV hints ===
	if len(noDIV) > 0 && divScore < 95 {
		hints = append(hints, depsHint{
			Severity:   "info",
			Score:      "div_score",
			Impact:     fmt.Sprintf("div_score %.1f → higher", divScore),
			Count:      len(noDIV),
			Components: sample(noDIV),
			Message: fmt.Sprintf(
				"%d components have no magatama:div/* imports. "+
					"Add selectively: div/information for knowledge/profile management, "+
					"div/documents for legal/policy/report management, "+
					"div/materiel for physical asset/equipment management. "+
					"Not all apps need all three — analyze the app's data model.",
				len(noDIV)),
		})
	}

	// === deps_link hints (stale imports) ===
	if len(staleImports) > 0 {
		staleKeys := make([]string, 0, len(staleImports))
		for k := range staleImports {
			staleKeys = append(staleKeys, k)
		}
		sort.Strings(staleKeys)
		hints = append(hints, depsHint{
			Severity:   "error",
			Score:      "deps_link_score",
			Impact:     "removing stale imports reduces unresolved count and improves deps_link_score",
			Count:      len(staleImports),
			Components: sample(staleKeys),
			Message: fmt.Sprintf(
				"%d components have stale/unresolvable gftd:* imports (e.g., gftd:resource-flow/resource-flow@0.1.0, gftd:platform/*). "+
					"These old namespace imports create unresolved deps and directly reduce deps_link_score. "+
					"Remove them from world.wit. If the import was providing functionality, migrate to the correct namespace "+
					"(e.g., gftd:resource-flow@0.1.0 → magatama:gov-resource-flow@1.0.0 for government apps).",
				len(staleImports)),
		})
	}

	// === deps_link general unresolved ===
	if unresolvedCount > 0 && depsLinkScore < 80 {
		hints = append(hints, depsHint{
			Severity: "warning",
			Score:    "deps_link_score",
			Impact:   fmt.Sprintf("deps_link_score %.1f — %d unresolved domain deps", depsLinkScore, unresolvedCount),
			Count:    unresolvedCount,
			Message: fmt.Sprintf(
				"%d domain dependency imports (gftd:*) are unresolved — no component exports a matching interface. "+
					"Options: (1) add provider components that export the interface, "+
					"(2) remove imports that are no longer needed, "+
					"(3) use magatama: prefix for shared platform imports (exempt from deps_link). "+
					"Check `top_unresolved_nodes` for the worst offenders.",
				unresolvedCount),
		})
	}

	// === Isolation penalty ===
	if isolatedCount > 0 && isolationPenalty > 5 {
		hints = append(hints, depsHint{
			Severity: "warning",
			Score:    "overall_score (penalty)",
			Impact:   fmt.Sprintf("isolation_penalty=%.1f — reducing isolated components removes this penalty", isolationPenalty),
			Count:    isolatedCount,
			Message: fmt.Sprintf(
				"%d components are isolated (no domain deps or exports). "+
					"Add at least one domain capability export and one contract import to connect them to the dependency graph. "+
					"Read the component's main.go and magatama.jsonld to determine appropriate WIT declarations.",
				isolatedCount),
		})
	}

	// Sort by severity: error first, then warning, then info
	sort.SliceStable(hints, func(i, j int) bool {
		order := map[string]int{"error": 0, "warning": 1, "info": 2}
		return order[hints[i].Severity] < order[hints[j].Severity]
	})

	return hints
}

func fetchDepsGraphSnapshot(client *http.Client, base string) (*depsGraphSnapshot, error) {
	graphURL, err := resolveURL(base, "/api/deps/graph")
	if err != nil {
		return nil, err
	}
	body, err := fetchText(client, graphURL)
	if err != nil {
		return nil, err
	}
	var graph depsGraphSnapshot
	if err := json.Unmarshal([]byte(body), &graph); err != nil {
		return nil, fmt.Errorf("parse deps graph JSON: %w", err)
	}
	if graph.GeneratedAt == "" || len(graph.LinkerStatus.Links) == 0 {
		return nil, errors.New("deps graph JSON missing generatedAt or linkerStatus.links")
	}
	return &graph, nil
}

func loadDepsGraphSnapshot(path string) (*depsGraphSnapshot, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read graph JSON %s: %w", path, err)
	}
	var graph depsGraphSnapshot
	if err := json.Unmarshal(data, &graph); err != nil {
		return nil, fmt.Errorf("parse graph JSON %s: %w", path, err)
	}
	if graph.GeneratedAt == "" || len(graph.LinkerStatus.Links) == 0 {
		return nil, fmt.Errorf("graph JSON %s missing generatedAt or linkerStatus.links", path)
	}
	return &graph, nil
}

func runDepsGraphGenerator(projectDir string) error {
	scriptPath := filepath.Join(projectDir, "scripts", "generate-wit-deps-graph.mjs")
	if _, err := os.Stat(scriptPath); err != nil {
		return fmt.Errorf("graph generator not found: %s", scriptPath)
	}
	if _, err := exec.LookPath("node"); err != nil {
		return fmt.Errorf("required tool not found: node")
	}
	cmd := exec.Command("node", "scripts/generate-wit-deps-graph.mjs")
	cmd.Dir = projectDir
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	if err := cmd.Run(); err != nil {
		return fmt.Errorf("generate deps graph: %w", err)
	}
	return nil
}

func writeDepsJSON(path string, value any) error {
	data, err := json.MarshalIndent(value, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal %s: %w", path, err)
	}
	data = append(data, '\n')
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write %s: %w", path, err)
	}
	return nil
}

func buildDepsAppRegistry(graph *depsGraphSnapshot) []depsAppRegistryEntry {
	if graph == nil {
		return nil
	}

	rows := make([]depsAppRegistryEntry, 0)
	if len(graph.RegisteredApps) > 0 {
		rows = append(rows, graph.RegisteredApps...)
	} else {
		for _, component := range graph.LinkerStatus.Components {
			if !component.RegisteredApp {
				continue
			}
			rows = append(rows, depsAppRegistryEntry{
				Project:        component.Project,
				ComponentID:    component.ComponentID,
				AppID:          component.AppID,
				AppName:        component.AppName,
				Runtime:        component.Runtime,
				RegisteredApp:  component.RegisteredApp,
				WorkerDeployed: component.WorkerDeployed,
				RouteHosts:     append([]string(nil), component.RouteHosts...),
				WProtoScore:    component.WProtoScore,
				WProtoSignals:  append([]string(nil), component.WProtoSignals...),
			})
		}
	}

	sort.Slice(rows, func(i, j int) bool {
		if rows[i].WorkerDeployed != rows[j].WorkerDeployed {
			return rows[i].WorkerDeployed
		}
		if rows[i].WProtoScore != rows[j].WProtoScore {
			return rows[i].WProtoScore > rows[j].WProtoScore
		}
		if rows[i].Project != rows[j].Project {
			return rows[i].Project < rows[j].Project
		}
		return rows[i].ComponentID < rows[j].ComponentID
	})
	return rows
}

func resolveDepsPath(root, value string) string {
	if filepath.IsAbs(value) {
		return value
	}
	return filepath.Join(root, value)
}

func buildDepsQualityAudit(graph *depsGraphSnapshot) depsQualityAudit {
	capabilityRbacByComponentID := map[string]depsDomainComponent{}
	for _, row := range graph.DomainComponents {
		current := capabilityRbacByComponentID[row.ComponentID]
		if row.CapabilityCount > current.CapabilityCount {
			current.CapabilityCount = row.CapabilityCount
		}
		if row.RbacCount > current.RbacCount {
			current.RbacCount = row.RbacCount
		}
		capabilityRbacByComponentID[row.ComponentID] = current
	}

	governanceByKey := map[string]int{}
	for _, link := range graph.GovernanceLinks {
		key := link.Project + "::" + link.ComponentID
		governanceByKey[key]++
	}

	records := make([]depsQualityRecord, 0, len(graph.LinkerStatus.Components))
	for _, comp := range graph.LinkerStatus.Components {
		key := comp.Project + "::" + comp.ComponentID
		capRbac := capabilityRbacByComponentID[comp.ComponentID]
		governanceCount := governanceByKey[key]
		isolated := isIsolatedDepsLinkerComponent(comp)
		capabilityMissing := capRbac.CapabilityCount == 0
		rbacMissing := capRbac.RbacCount == 0
		governanceMissing := governanceCount == 0

		risk := 0
		if isolated {
			risk += 50
		}
		if capabilityMissing {
			risk += 20
		}
		if rbacMissing {
			risk += 15
		}
		if governanceMissing {
			risk += 15
		}
		if capabilityMissing && rbacMissing && governanceMissing {
			risk += 10
		}

		records = append(records, depsQualityRecord{
			Project:           comp.Project,
			ComponentID:       comp.ComponentID,
			Isolated:          isolated,
			CapabilityCount:   capRbac.CapabilityCount,
			RbacCount:         capRbac.RbacCount,
			GovernanceCount:   governanceCount,
			CapabilityMissing: capabilityMissing,
			RbacMissing:       rbacMissing,
			GovernanceMissing: governanceMissing,
			Risk:              risk,
		})
	}

	sort.Slice(records, func(i, j int) bool {
		if records[i].Risk != records[j].Risk {
			return records[i].Risk > records[j].Risk
		}
		if records[i].Project != records[j].Project {
			return records[i].Project < records[j].Project
		}
		return records[i].ComponentID < records[j].ComponentID
	})

	totals := depsQualityAuditTotals{}
	byProject := map[string]depsQualityProject{}
	iscoRows := make([]depsQualityRecord, 0)
	for _, r := range records {
		totals.TotalComponents++
		if r.Isolated {
			totals.IsolatedComponents++
		}
		if r.CapabilityMissing {
			totals.CapabilityMissingComponents++
		}
		if r.RbacMissing {
			totals.RBACMissingComponents++
		}
		if r.GovernanceMissing {
			totals.GovernanceMissingComponents++
		}
		if r.CapabilityMissing && r.RbacMissing && r.GovernanceMissing {
			totals.TripleMissingComponents++
		}
		if r.Risk >= 100 {
			totals.CriticalComponents++
		}

		cur := byProject[r.Project]
		cur.Project = r.Project
		cur.TotalComponents++
		if r.Isolated {
			cur.IsolatedComponents++
		}
		if r.CapabilityMissing {
			cur.CapabilityMissingComponents++
		}
		if r.GovernanceMissing {
			cur.GovernanceMissingComponents++
		}
		if r.CapabilityMissing && r.RbacMissing && r.GovernanceMissing {
			cur.TripleMissingComponents++
		}
		if r.Risk >= 100 {
			cur.CriticalComponents++
		}
		byProject[r.Project] = cur

		if r.Project == "ai-gftd-project-open-isco" {
			iscoRows = append(iscoRows, r)
		}
	}

	topProjects := make([]depsQualityProject, 0, len(byProject))
	for _, row := range byProject {
		topProjects = append(topProjects, row)
	}
	sort.Slice(topProjects, func(i, j int) bool {
		if topProjects[i].CriticalComponents != topProjects[j].CriticalComponents {
			return topProjects[i].CriticalComponents > topProjects[j].CriticalComponents
		}
		if topProjects[i].TripleMissingComponents != topProjects[j].TripleMissingComponents {
			return topProjects[i].TripleMissingComponents > topProjects[j].TripleMissingComponents
		}
		if topProjects[i].IsolatedComponents != topProjects[j].IsolatedComponents {
			return topProjects[i].IsolatedComponents > topProjects[j].IsolatedComponents
		}
		return topProjects[i].Project < topProjects[j].Project
	})

	return depsQualityAudit{
		GeneratedAt:           time.Now().UTC().Format(time.RFC3339),
		SourceGeneratedAt:     graph.GeneratedAt,
		SourceSummary:         graph.Summary,
		Totals:                totals,
		TopProjects:           limitQualityProjects(topProjects, 20),
		CriticalComponents:    filterCriticalQualityRecords(records, 200),
		TopRiskComponents:     limitQualityRecords(records, 200),
		ISCOTopRiskComponents: limitQualityRecords(iscoRows, 100),
	}
}

func isIsolatedDepsLinkerComponent(comp depsLinkerComponent) bool {
	return len(comp.Imports)+len(comp.Exports)+len(comp.Provides)+len(comp.Requires) == 0
}

func limitQualityProjects(in []depsQualityProject, n int) []depsQualityProject {
	if len(in) <= n {
		return in
	}
	return in[:n]
}

func limitQualityRecords(in []depsQualityRecord, n int) []depsQualityRecord {
	if len(in) <= n {
		return in
	}
	return in[:n]
}

func filterCriticalQualityRecords(in []depsQualityRecord, n int) []depsQualityRecord {
	out := make([]depsQualityRecord, 0, n)
	for _, row := range in {
		if row.Risk < 100 {
			continue
		}
		out = append(out, row)
		if len(out) >= n {
			break
		}
	}
	return out
}

func makeDepsQualityPlanMarkdown(audit depsQualityAudit) string {
	var b strings.Builder
	b.WriteString("# WIT/WASM Quality Improvement Plan\n\n")
	b.WriteString(fmt.Sprintf("- Generated: %s\n", audit.GeneratedAt))
	b.WriteString(fmt.Sprintf("- Source graph generatedAt: %s\n\n", audit.SourceGeneratedAt))
	b.WriteString("## Global Findings\n\n")
	b.WriteString(fmt.Sprintf("- total components: %d\n", audit.Totals.TotalComponents))
	b.WriteString(fmt.Sprintf("- isolated components: %d\n", audit.Totals.IsolatedComponents))
	b.WriteString(fmt.Sprintf("- capability missing: %d\n", audit.Totals.CapabilityMissingComponents))
	b.WriteString(fmt.Sprintf("- RBAC missing: %d\n", audit.Totals.RBACMissingComponents))
	b.WriteString(fmt.Sprintf("- governance missing: %d\n", audit.Totals.GovernanceMissingComponents))
	b.WriteString(fmt.Sprintf("- capability+RBAC+governance all missing: %d\n", audit.Totals.TripleMissingComponents))
	b.WriteString(fmt.Sprintf("- critical components (risk>=100): %d\n\n", audit.Totals.CriticalComponents))
	b.WriteString("## P0 Target Projects (by critical count)\n\n")
	b.WriteString("| project | critical | triple-missing | isolated | total |\n")
	b.WriteString("| --- | ---: | ---: | ---: | ---: |\n")
	for _, p := range limitQualityProjects(audit.TopProjects, 15) {
		b.WriteString(fmt.Sprintf("| %s | %d | %d | %d | %d |\n", p.Project, p.CriticalComponents, p.TripleMissingComponents, p.IsolatedComponents, p.TotalComponents))
	}
	b.WriteString("\n## P0 Critical Components (Top 30)\n\n")
	b.WriteString("| project | componentId | risk | isolated | cap | rbac | gov |\n")
	b.WriteString("| --- | --- | ---: | ---: | ---: | ---: | ---: |\n")
	for _, c := range limitQualityRecords(audit.CriticalComponents, 30) {
		isolated := "no"
		if c.Isolated {
			isolated = "yes"
		}
		b.WriteString(fmt.Sprintf("| %s | %s | %d | %s | %d | %d | %d |\n", c.Project, c.ComponentID, c.Risk, isolated, c.CapabilityCount, c.RbacCount, c.GovernanceCount))
	}
	b.WriteString("\n## ISCO Focus (Top 30 by risk)\n\n")
	b.WriteString("| componentId | risk | isolated | cap | rbac | gov |\n")
	b.WriteString("| --- | ---: | ---: | ---: | ---: | ---: |\n")
	for _, c := range limitQualityRecords(audit.ISCOTopRiskComponents, 30) {
		isolated := "no"
		if c.Isolated {
			isolated = "yes"
		}
		b.WriteString(fmt.Sprintf("| %s | %d | %s | %d | %d | %d |\n", c.ComponentID, c.Risk, isolated, c.CapabilityCount, c.RbacCount, c.GovernanceCount))
	}
	b.WriteString("\n## Improvement Plan\n\n")
	b.WriteString("1. P0 (1-2 weeks): Add capability tags and Responsible/Accountable/RequireApproval metadata to all critical components, starting from the top 3 projects.\n")
	b.WriteString("2. P1 (2-4 weeks): Remove isolation by wiring command/query links for components that are isolated but should participate in runtime/domain graph.\n")
	b.WriteString("3. P2 (continuous): Add per-project CI gate to fail when new component has cap=0 or gov=0 without explicit allowlist.\n")
	b.WriteString("4. P2 (continuous): Regenerate full-audit weekly and track trend of isolated/triple-missing/critical counts.\n\n")
	return b.String()
}

func printDepsScoreText(report *depsScoreReport) {
	fmt.Printf("deps_score:\n")
	fmt.Printf("  source_url: %s\n", report.SourceURL)
	if report.GeneratedAt != "" {
		fmt.Printf("  generated_at: %s\n", report.GeneratedAt)
	}
	fmt.Printf("  evaluated_at: %s\n", report.EvaluatedAt)
	fmt.Printf("  total_links: %d\n", report.TotalLinks)
	fmt.Printf("  resolved: %d\n", report.ResolvedCount)
	fmt.Printf("  unresolved: %d\n", report.UnresolvedCount)
	fmt.Printf("  link_coverage_rate: %.4f\n", report.LinkCoverageRate)
	fmt.Printf("  unresolved_rate: %.4f\n", report.UnresolvedRate)
	fmt.Printf("  governance_unresolved_count: %d\n", report.GovernanceUnresolvedCount)
	fmt.Printf("  worker_registered_app_count: %d\n", report.WorkerRegisteredAppCount)
	fmt.Printf("  worker_deployed_app_count: %d\n", report.WorkerDeployedAppCount)
	fmt.Printf("  worker_deploy_coverage: %.4f\n", report.WorkerDeployCoverage)
	fmt.Printf("  wproto_integration_score: %.1f\n", report.WProtoIntegrationScore)
	fmt.Printf("  isolated_count: %d\n", report.IsolatedCount)
	fmt.Printf("  isolated_rate: %.4f\n", report.IsolatedRate)
	fmt.Printf("  governance_coverage: %.4f\n", report.GovernanceCoverage)
	fmt.Printf("  raci_coverage: %.4f\n", report.RACICoverage)
	fmt.Printf("  isolation_penalty: %.1f\n", report.IsolationPenalty)
	fmt.Printf("  unadapted_penalty: %.1f\n", report.UnadaptedPenalty)
	fmt.Printf("  build_linker_score: %.1f  # build-time linker/governance stage\n", report.Scoring.BuildLinkerScore)
	fmt.Printf("  runtime_linker_score: %.1f  # runtime link stage (all runtime-resolvable refs)\n", report.Scoring.RuntimeLinkerScore)
	fmt.Printf("  app_mesh_score: %.1f  # app-to-app provider/export coverage\n", report.Scoring.AppMeshScore)
	fmt.Printf("  runtime_host_score: %.1f  # wasi/magatama host coverage\n", report.Scoring.RuntimeHostScore)
	fmt.Printf("  link_blend_score: %.1f  # 50%% build_linker + 20%% runtime_linker + 30%% app_mesh\n", report.Scoring.LinkBlendScore)
	fmt.Printf("  dodaf_v2_score: %.1f\n", report.Scoring.DoDAFV2Score)
	fmt.Printf("  nist_csf_v2_score: %.1f\n", report.Scoring.NISTCSFV2Score)
	fmt.Printf("  app_wit_definition_score: %.1f\n", report.Scoring.AppWITDefinitionScore)
	fmt.Printf("  app_wit_definition_coverage: %.4f\n", report.Scoring.AppWITDefinitionCoverage)
	fmt.Printf("  contract_score: %.1f  # magatama:contract import coverage\n", report.ContractScore)
	fmt.Printf("  capability_export_score: %.1f  # domain capability export coverage\n", report.CapabilityExportScore)
	fmt.Printf("  deps_link_score: %.1f  # domain import resolution rate\n", report.DepsLinkScore)
	fmt.Printf("  resource_flow_score: %.1f  # gov-resource-flow WIT coverage (ヒトモノカネ)\n", report.ResourceFlowScore)
	fmt.Printf("  div_score: %.1f  # magatama:div WIT coverage (DIV-3 information/documents/materiel)\n", report.DIVScore)
	fmt.Printf("  shannon_score: %.1f  # Shannon redundancy (60%% import_entropy + 40%% duplicate_import)\n", report.ShannonScore)
	fmt.Printf("    import_entropy: %.1f\n", report.ImportEntropyScore)
	fmt.Printf("    duplicate_import: %.1f\n", report.DuplicateImportScore)
	fmt.Printf("  overall_score: %.1f\n", report.Scoring.OverallScore)
	fmt.Printf("  scoring_model: %s\n", report.Scoring.Model)
	fmt.Printf("  build_linker_factors:  # app_mesh factors\n")
	fmt.Printf("    policy_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.PolicyCoverage)
	fmt.Printf("    governance_health: %.4f\n", report.Scoring.BuildLinkerFactors.GovernanceHealth)
	fmt.Printf("    governance_link_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.LinkCoverage)
	fmt.Printf("    rbac_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.RBACCoverage)
	fmt.Printf("    capability_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.CapabilityCoverage)
	fmt.Printf("    app_wit_definition_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.AppWITDefinitionCoverage)
	fmt.Printf("    isolated_rate: %.4f\n", report.Scoring.BuildLinkerFactors.IsolatedRate)
	fmt.Printf("    governance_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.GovernanceCoverage)
	fmt.Printf("    raci_coverage: %.4f\n", report.Scoring.BuildLinkerFactors.RACICoverage)
	fmt.Printf("  runtime_linker_factors:  # runtime host-link factors\n")
	fmt.Printf("    link_coverage: %.4f\n", report.Scoring.RuntimeLinkerFactors.LinkCoverage)
	fmt.Printf("    governance_health: %.4f\n", report.Scoring.RuntimeLinkerFactors.GovernanceHealth)
	fmt.Printf("    runtime_import_health: %.4f\n", report.Scoring.RuntimeLinkerFactors.RuntimeImportHealth)
	fmt.Printf("  app_mesh_factors:\n")
	fmt.Printf("    link_coverage: %.4f\n", report.Scoring.AppMeshFactors.LinkCoverage)
	fmt.Printf("    governance_health: %.4f\n", report.Scoring.AppMeshFactors.GovernanceHealth)
	fmt.Printf("    governance_coverage: %.4f\n", report.Scoring.AppMeshFactors.GovernanceCoverage)
	fmt.Printf("    raci_coverage: %.4f\n", report.Scoring.AppMeshFactors.RACICoverage)
	fmt.Printf("    isolated_rate: %.4f\n", report.Scoring.AppMeshFactors.IsolatedRate)
	fmt.Printf("  runtime_host_factors:\n")
	fmt.Printf("    link_coverage: %.4f\n", report.Scoring.RuntimeHostFactors.LinkCoverage)
	fmt.Printf("    governance_health: %.4f\n", report.Scoring.RuntimeHostFactors.GovernanceHealth)
	fmt.Printf("    runtime_import_health: %.4f\n", report.Scoring.RuntimeHostFactors.RuntimeImportHealth)
	fmt.Printf("  unresolved_by_kind:\n")

	kinds := make([]string, 0, len(report.UnresolvedByKind))
	for kind := range report.UnresolvedByKind {
		kinds = append(kinds, kind)
	}
	sort.Strings(kinds)
	for _, kind := range kinds {
		fmt.Printf("    %s: %d\n", kind, report.UnresolvedByKind[kind])
	}

	if len(report.GovernanceUnresolvedNodes) > 0 {
		fmt.Printf("  governance_unresolved_nodes:\n")
		for _, node := range report.GovernanceUnresolvedNodes {
			fmt.Printf("    - %s / %s\n", node.Project, node.ComponentID)
			for _, ref := range node.UnresolvedGovernanceRef {
				fmt.Printf("      * %s\n", ref)
			}
		}
	}

	if len(report.TopUnresolvedNodes) > 0 {
		fmt.Printf("  top_unresolved_nodes:\n")
		for _, node := range report.TopUnresolvedNodes {
			fmt.Printf("    - %s / %s: %d\n", node.Project, node.ComponentID, node.UnresolvedLinks)
		}
	}

	if len(report.Hints) > 0 {
		fmt.Printf("  hints:\n")
		for _, h := range report.Hints {
			fmt.Printf("    - severity: %s\n", h.Severity)
			fmt.Printf("      score: %s\n", h.Score)
			fmt.Printf("      impact: %s\n", h.Impact)
			fmt.Printf("      count: %d\n", h.Count)
			fmt.Printf("      message: |\n")
			for _, line := range strings.Split(h.Message, ". ") {
				fmt.Printf("        %s.\n", strings.TrimSuffix(line, "."))
			}
			if len(h.Components) > 0 {
				fmt.Printf("      components:\n")
				for _, c := range h.Components {
					fmt.Printf("        - %s\n", c)
				}
				if h.Count > len(h.Components) {
					fmt.Printf("        ... and %d more\n", h.Count-len(h.Components))
				}
			}
		}
	} else {
		fmt.Printf("  hints: (run `gftd deps export` for local component-level hints)\n")
	}
}

func fetchText(client *http.Client, rawURL string) (string, error) {
	req, err := http.NewRequest(http.MethodGet, rawURL, nil)
	if err != nil {
		return "", err
	}
	resp, err := client.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return "", fmt.Errorf("unexpected status: %s", resp.Status)
	}
	body, err := io.ReadAll(resp.Body)
	if err != nil {
		return "", err
	}
	return string(body), nil
}

func resolveURL(base, ref string) (string, error) {
	b, err := url.Parse(base)
	if err != nil {
		return "", fmt.Errorf("parse --url: %w", err)
	}
	r, err := url.Parse(ref)
	if err != nil {
		return "", fmt.Errorf("parse relative URL: %w", err)
	}
	return b.ResolveReference(r).String(), nil
}

func decodeJSSingleQuoted(in string) (string, error) {
	var b strings.Builder
	b.Grow(len(in))
	for i := 0; i < len(in); i++ {
		ch := in[i]
		if ch != '\\' {
			b.WriteByte(ch)
			continue
		}
		i++
		if i >= len(in) {
			return "", errors.New("trailing escape")
		}
		esc := in[i]
		switch esc {
		case 'n':
			b.WriteByte('\n')
		case 'r':
			b.WriteByte('\r')
		case 't':
			b.WriteByte('\t')
		case 'b':
			b.WriteByte('\b')
		case 'f':
			b.WriteByte('\f')
		case 'v':
			b.WriteByte('\v')
		case '0':
			b.WriteByte(0)
		case '\\':
			b.WriteByte('\\')
		case '\'':
			b.WriteByte('\'')
		case '"':
			b.WriteByte('"')
		case 'x':
			if i+2 >= len(in) {
				return "", errors.New("short \\x escape")
			}
			h, ok := parseHexByte(in[i+1 : i+3])
			if !ok {
				return "", errors.New("invalid \\x escape")
			}
			b.WriteByte(h)
			i += 2
		case 'u':
			if i+4 >= len(in) {
				return "", errors.New("short \\u escape")
			}
			r, ok := parseHexRune(in[i+1 : i+5])
			if !ok {
				return "", errors.New("invalid \\u escape")
			}
			b.WriteRune(r)
			i += 4
		default:
			b.WriteByte(esc)
		}
	}
	return b.String(), nil
}

func parseHexByte(s string) (byte, bool) {
	if len(s) != 2 {
		return 0, false
	}
	var v byte
	for i := 0; i < 2; i++ {
		n, ok := hexNibble(s[i])
		if !ok {
			return 0, false
		}
		v = v<<4 | n
	}
	return v, true
}

func parseHexRune(s string) (rune, bool) {
	if len(s) != 4 {
		return 0, false
	}
	var v rune
	for i := 0; i < 4; i++ {
		n, ok := hexNibble(s[i])
		if !ok {
			return 0, false
		}
		v = v<<4 | rune(n)
	}
	return v, true
}

func hexNibble(c byte) (byte, bool) {
	switch {
	case c >= '0' && c <= '9':
		return c - '0', true
	case c >= 'a' && c <= 'f':
		return c - 'a' + 10, true
	case c >= 'A' && c <= 'F':
		return c - 'A' + 10, true
	default:
		return 0, false
	}
}

func splitNodeKey(key string) (project, component string) {
	parts := strings.SplitN(key, "::", 2)
	if len(parts) == 2 {
		return parts[0], parts[1]
	}
	return key, ""
}

func extractLinkerStatusFromNodeJS(js string) (*depsLinkerStatus, error) {
	const needle = "JSON.parse('"
	for pos := 0; pos < len(js); {
		idx := strings.Index(js[pos:], needle)
		if idx < 0 {
			break
		}
		start := pos + idx + len(needle)
		escaped, end, err := readJSSingleQuotedLiteral(js, start)
		if err != nil {
			pos = start
			continue
		}
		pos = end
		decoded, err := decodeJSSingleQuoted(escaped)
		if err != nil || !json.Valid([]byte(decoded)) {
			continue
		}
		var candidate depsLinkerStatus
		if err := json.Unmarshal([]byte(decoded), &candidate); err != nil {
			continue
		}
		if candidate.Summary.TotalLinks > 0 && len(candidate.Links) > 0 {
			return &candidate, nil
		}
	}
	return nil, errors.New("could not locate linker status JSON payload in nodes JS")
}

func readJSSingleQuotedLiteral(in string, start int) (string, int, error) {
	var b strings.Builder
	escaped := false
	for i := start; i < len(in); i++ {
		ch := in[i]
		if ch == '\'' && !escaped {
			return b.String(), i + 1, nil
		}
		if ch == '\\' && !escaped {
			escaped = true
			b.WriteByte(ch)
			continue
		}
		escaped = false
		b.WriteByte(ch)
	}
	return "", start, errors.New("unterminated single-quoted JS string")
}

func cap01(v float64) float64 {
	if v < 0 {
		return 0
	}
	if v > 1 {
		return 1
	}
	return v
}

func round1(v float64) float64 {
	return math.Round(v*10) / 10
}

func maxInt(a, b int) int {
	if a >= b {
		return a
	}
	return b
}

func parseDepsUISummary(html string) depsUISummary {
	isolatedCount, isolatedRate, hasIsolated := findCountAndRateBadge(html,
		"isolated",
		"isolated badge",
		"isolated count",
		"unadapted",
		"isolation",
	)
	governanceCoverage, hasGovernanceCoverage := findCoverageBadge(html,
		"governance coverage",
		"governance-coverage",
		"coverage (governance)",
	)
	raciCoverage, hasRACICoverage := findCoverageBadge(html,
		"explicit RACI coverage",
		"RACI coverage",
		"raci coverage",
		"raci-coverage",
		"explicit-raci-coverage",
	)
	return depsUISummary{
		TotalDomainDeps:          findIntBadge(html, `(\d+)\s+domain deps`),
		TotalGovernanceLinks:     findIntBadge(html, `(\d+)\s+governance links`),
		TotalResolvedLinks:       findIntBadge(html, `(\d+)\s+linked`),
		TotalUnresolvedLinks:     findIntBadge(html, `(\d+)\s+unlinked`),
		GovernanceUnresolved:     findIntBadge(html, `(\d+)\s+governance-unresolved`),
		TotalRbacBindings:        findIntBadge(html, `(\d+)\s+RBAC bindings`),
		TotalCapabilities:        findIntBadge(html, `(\d+)\s+capabilities`),
		TotalDomainComponents:    findIntBadge(html, `(\d+)\s+domain components`),
		TotalGovernedComponents:  findIntBadge(html, `(\d+)\s+governed components`),
		RuntimeImports:           findIntBadge(html, `(\d+)\s+linker imports`),
		AppWITDefinitionScore:    findFloatBadge(html, `app-wit\s+([0-9]+(?:\.[0-9]+)?)`),
		AppWITDefinitionCoverage: findFloatBadge(html, `app-wit-coverage\s+([0-9]+(?:\.[0-9]+)?)`),
		IsolatedCount:            isolatedCount,
		IsolatedRate:             isolatedRate,
		HasIsolated:              hasIsolated,
		GovernanceCoverage:       governanceCoverage,
		HasGovernanceCoverage:    hasGovernanceCoverage,
		RACICoverage:             raciCoverage,
		HasRACICoverage:          hasRACICoverage,
	}
}

func findIntBadge(text, pattern string) int {
	re := regexp.MustCompile(pattern)
	m := re.FindStringSubmatch(text)
	if len(m) < 2 {
		return 0
	}
	var v int
	_, _ = fmt.Sscanf(m[1], "%d", &v)
	return v
}

func findFloatBadge(text, pattern string) float64 {
	re := regexp.MustCompile(pattern)
	m := re.FindStringSubmatch(text)
	if len(m) < 2 {
		return 0
	}
	var v float64
	_, _ = fmt.Sscanf(m[1], "%f", &v)
	return v
}

func findCountAndRateBadge(text string, labels ...string) (int, float64, bool) {
	normalizedText := strings.ToLower(text)
	for _, label := range labels {
		for _, pattern := range []string{
			`(\d+)` + `(?:[:=\-()]|\s)*` + badgePattern(label) + `(?:[^0-9]+(\d+(?:\.\d+)?)\s*(%?))?`,
			badgePattern(label) + `(?:[:=\-()]|\s)*(\d+)(?:[^0-9]+(\d+(?:\.\d+)?)\s*(%?))?`,
		} {
			re := regexp.MustCompile(pattern)
			m := re.FindStringSubmatch(normalizedText)
			if len(m) < 2 {
				continue
			}
			count := 0
			_, _ = fmt.Sscanf(m[1], "%d", &count)
			rate := 0.0
			if len(m) >= 4 && m[2] != "" {
				rateValue, _ := parseFloatBadgeValue(m[2])
				rate = normalizeRatioValue(rateValue, m[3] == "%")
			}
			return count, rate, true
		}
	}
	return 0, 0, false
}

func findCoverageBadge(text string, labels ...string) (float64, bool) {
	normalizedText := strings.ToLower(text)
	for _, label := range labels {
		for _, pattern := range []string{
			`(\d+(?:\.\d+)?)(%?)` + `(?:[:=\-()]|\s)*` + badgePattern(label),
			badgePattern(label) + `(?:[:=\-()]|\s)*(\d+(?:\.\d+)?)(%?)`,
		} {
			re := regexp.MustCompile(pattern)
			m := re.FindStringSubmatch(normalizedText)
			if len(m) < 2 {
				continue
			}
			value, _ := parseFloatBadgeValue(m[1])
			return normalizeRatioValue(value, len(m) >= 3 && m[2] == "%"), true
		}
	}
	return 0, false
}

func badgePattern(label string) string {
	parts := strings.Fields(strings.ToLower(strings.TrimSpace(label)))
	if len(parts) == 0 {
		return ``
	}
	for i, part := range parts {
		parts[i] = regexp.QuoteMeta(part)
	}
	return strings.Join(parts, `[[:space:]_-]+`)
}

func parseFloatBadgeValue(s string) (float64, error) {
	var v float64
	_, err := fmt.Sscanf(s, "%f", &v)
	return v, err
}

func normalizeRatioValue(v float64, percent bool) float64 {
	if percent || v > 1 {
		return cap01(v / 100.0)
	}
	return cap01(v)
}

func isRuntimeHostRef(ref string) bool {
	return strings.HasPrefix(ref, "wasi:") || strings.HasPrefix(ref, "magatama:")
}

func formatDepsScoreSummary(report *depsScoreReport) string {
	return fmt.Sprintf(
		"build=%.1f runtime=%.1f app-mesh=%.1f runtime-host=%.1f link-blend=%.1f dodaf-v2=%.1f nist-csf-v2=%.1f app-wit=%.1f app-wit-coverage=%.4f contract=%.1f capability-export=%.1f deps-link=%.1f resource-flow=%.1f div=%.1f shannon=%.1f import-entropy=%.1f duplicate-import=%.1f coverage=%.4f unresolved=%d governance-unresolved=%d worker-registered=%d worker-deployed=%d worker-coverage=%.4f wproto-score=%.1f isolated=%d isolated-rate=%.4f governance-coverage=%.4f raci-coverage=%.4f isolation-penalty=%.1f unadapted-penalty=%.1f",
		report.Scoring.BuildLinkerScore,
		report.Scoring.RuntimeLinkerScore,
		report.Scoring.AppMeshScore,
		report.Scoring.RuntimeHostScore,
		report.Scoring.LinkBlendScore,
		report.Scoring.DoDAFV2Score,
		report.Scoring.NISTCSFV2Score,
		report.Scoring.AppWITDefinitionScore,
		report.Scoring.AppWITDefinitionCoverage,
		report.ContractScore,
		report.CapabilityExportScore,
		report.DepsLinkScore,
		report.ResourceFlowScore,
		report.DIVScore,
		report.ShannonScore,
		report.ImportEntropyScore,
		report.DuplicateImportScore,
		report.LinkCoverageRate,
		report.UnresolvedCount,
		report.GovernanceUnresolvedCount,
		report.WorkerRegisteredAppCount,
		report.WorkerDeployedAppCount,
		report.WorkerDeployCoverage,
		report.WProtoIntegrationScore,
		report.IsolatedCount,
		report.IsolatedRate,
		report.GovernanceCoverage,
		report.RACICoverage,
		report.IsolationPenalty,
		report.UnadaptedPenalty,
	)
}

func ratio(a, b int) float64 {
	if b == 0 {
		return 0
	}
	return float64(a) / float64(b)
}

func round4(v float64) float64 {
	return math.Round(v*10000) / 10000
}
