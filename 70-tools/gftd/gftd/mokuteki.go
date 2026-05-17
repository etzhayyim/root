package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"os"
	"sort"
	"strings"
	"time"
)

// mokuteki (目的) — Purpose-driven 4-layer Shannon optimization evaluator.
// Objective function: Global Well-Becoming Generative Society.
//
// 4-Layer Framework:
//   Layer A (構造):     DSM, directed graph, hypergraph, category/type, Merkle DAG
//   Layer B (不確実性): BayesNet, Dynamic BayesNet, HMM/state-space, causal graph
//   Layer C (制御):     MDP/POMDP, constraint optimization, MPC, bandit/active sensing
//   Layer D (実装):     Event sourcing, immutable log, policy as code, typed schema, attestation
//
// Unified principle: DSM で依存構造を表現し、Bayes で不確実性を伝播させ、POMDP で観測と制御を最適化する。
//
// Each layer maps to Well-Becoming axes (Engagement, Competence, Contribution, Growth, Resilience)
// and produces a Kyu/Dan rank.

// --- Kyu/Dan rank ladder ---

type mokutekiRank struct {
	Name     string `json:"name"`
	Color    string `json:"color"`
	MinScore int    `json:"min_score"`
}

var mokutekiRankLadder = []mokutekiRank{
	{Name: "Dan 10", Color: "#000000", MinScore: 12000},
	{Name: "Dan 9", Color: "#000000", MinScore: 11000},
	{Name: "Dan 8", Color: "#000000", MinScore: 10000},
	{Name: "Dan 7", Color: "#000000", MinScore: 9000},
	{Name: "Dan 6", Color: "#000000", MinScore: 8000},
	{Name: "Dan 5", Color: "#000000", MinScore: 7000},
	{Name: "Dan 4", Color: "#000000", MinScore: 6000},
	{Name: "Dan 3", Color: "#000000", MinScore: 5000},
	{Name: "Dan 2", Color: "#000000", MinScore: 4000},
	{Name: "Dan 1", Color: "#000000", MinScore: 2000},
	{Name: "Kyu 1", Color: "#8B4513", MinScore: 1500},
	{Name: "Kyu 2", Color: "#3B82F6", MinScore: 1000},
	{Name: "Kyu 3", Color: "#22C55E", MinScore: 600},
	{Name: "Kyu 4", Color: "#FF8C00", MinScore: 300},
	{Name: "Kyu 5", Color: "#FFD700", MinScore: 100},
	{Name: "Kyu 6", Color: "#FFFFFF", MinScore: 0},
}

func resolveRank(score int) mokutekiRank {
	for _, r := range mokutekiRankLadder {
		if score >= r.MinScore {
			return r
		}
	}
	return mokutekiRankLadder[len(mokutekiRankLadder)-1]
}

// --- Report types ---

// mokutekiLayer represents one of the 4 architectural layers.
type mokutekiLayer struct {
	ID          string            `json:"id"`
	Name        string            `json:"name"`
	NameJP      string            `json:"name_jp"`
	Weight      float64           `json:"weight"`
	Score       float64           `json:"score"`       // 0-100
	Points      int               `json:"points"`
	Components  []mokutekiCheck   `json:"components"`
}

// mokutekiCheck represents one sub-check within a layer.
type mokutekiCheck struct {
	Name    string      `json:"name"`
	Score   float64     `json:"score"`   // 0-100
	Weight  float64     `json:"weight"`  // within layer
	Details string      `json:"details,omitempty"`
	Data    interface{} `json:"data,omitempty"` // rich sub-report (DSM, BayesNet, etc.)
}

// mokutekiAxis represents the Well-Becoming axis mapping (derived from layers).
type mokutekiAxis struct {
	Name    string  `json:"name"`
	Weight  float64 `json:"weight"`
	Score   float64 `json:"score"`
	Points  int     `json:"points"`
	Source  string  `json:"source"`
	Details string  `json:"details,omitempty"`
}

// mokutekiReport is the full 4-layer purpose-driven evaluation output.
type mokutekiReport struct {
	GeneratedAt string          `json:"generated_at"`
	Mokuteki    string          `json:"mokuteki"`
	Principle   string          `json:"principle"`
	TotalApps   int             `json:"total_apps"`
	TotalEdges  int             `json:"total_edges"`
	Layers      []mokutekiLayer `json:"layers"`
	Axes        []mokutekiAxis  `json:"axes"`
	TotalScore  int             `json:"total_score"`
	MaxScore    int             `json:"max_score"`
	Rank        mokutekiRank    `json:"rank"`
	Diagnosis   []string        `json:"diagnosis"`
}

// --- Entry point ---

func runMokuteki(args []string) error {
	// Subcommand dispatch
	if len(args) > 0 {
		switch args[0] {
		case "kashika":
			return runMokutekiKashika(args[1:])
		case "store":
			return runMokutekiStore(args[1:])
		case "query":
			return runMokutekiQuery(args[1:])
		case "history":
			return runMokutekiHistory(args[1:])
		case "help", "--help", "-h":
			printMokutekiUsage()
			return nil
		}
	}

	fs := flag.NewFlagSet("mokuteki", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			printMokutekiUsage()
			return nil
		}
		return err
	}

	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}

	report := buildMokutekiReport(wsRoot)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printMokutekiText(report)
	return nil
}

func printMokutekiUsage() {
	fmt.Print(`gftd mokuteki — Purpose-driven 4-layer Shannon optimization evaluator

MOKUTEKI (目的): Global Well-Becoming Generative Society
PRINCIPLE: DSMで依存構造を表現し、Bayesで不確実性を伝播させ、POMDPで観測と制御を最適化する

4-LAYER FRAMEWORK:
  Layer A (構造)      30%  DSM, directed graph, hypergraph, type system, Merkle DAG
  Layer B (不確実性)  25%  BayesNet, causal graph, change propagation, state-space
  Layer C (制御)      20%  POMDP observation, constraint optimization, bandit sensing
  Layer D (実装)      25%  Event sourcing, immutable log, policy as code, typed schema

WELL-BECOMING AXES (derived):
  Engagement   = Layer A connectivity + Layer D event sourcing
  Competence   = Layer A redundancy + Layer B uncertainty reduction
  Contribution = Layer B flow diversity + Layer C control optimality
  Growth       = Layer C entropy minimization + Layer A structural potential
  Resilience   = Layer B cycle-free + Layer D attestation coverage

USAGE:
  gftd mokuteki [flags]            Terminal text output
  gftd mokuteki --json             JSON output
  gftd mokuteki kashika            HTML visualization (browser auto-open)
  gftd mokuteki store              Evaluate + store as Parquet (Iceberg append-only)
  gftd mokuteki query [SQL]        Query historical data via DuckDB
  gftd mokuteki history            List stored snapshots

DATA STORE:
  data/mokuteki/                   Local Iceberg-like store
    snapshots/*.parquet            Per-evaluation Parquet files
    catalog.json                   Iceberg catalog (snapshot history)

FLAGS:
  --json              Output as JSON
  --workspace-dir DIR Workspace root (default: git root)
`)
}

func buildMokutekiReport(wsRoot string) *mokutekiReport {
	graph := haisenScanWorkspace(wsRoot, false)
	meta := sgScanAppMeta(wsRoot)

	totalApps := len(graph.Apps)
	totalEdges := len(graph.Edges)

	// === Layer A: 構造 (Structure) ===
	layerA := evalLayerA(wsRoot, graph)

	// === Layer B: 不確実性 (Uncertainty) ===
	layerB := evalLayerB(graph)

	// === Layer C: 制御 (Control) ===
	layerC := evalLayerC(graph)

	// === Layer D: 実装 (Implementation) ===
	layerD := evalLayerD(wsRoot, graph, meta)

	layers := []mokutekiLayer{layerA, layerB, layerC, layerD}

	// Compute per-layer points
	for i := range layers {
		layers[i].Points = int(layers[i].Score * layers[i].Weight * 120)
	}

	// Derive Well-Becoming axes from layers
	axes := deriveWellBeingAxes(layerA, layerB, layerC, layerD)

	// Total score
	totalScore := 0
	for _, l := range layers {
		totalScore += l.Points
	}
	maxScore := 12000
	rank := resolveRank(totalScore)

	diagnosis := mokutekiLayerDiagnosis(layers, axes, totalScore)

	return &mokutekiReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Mokuteki:    "Global Well-Becoming Generative Society",
		Principle:   "DSMで依存構造を表現し、Bayesで不確実性を伝播させ、POMDPで観測と制御を最適化する",
		TotalApps:   totalApps,
		TotalEdges:  totalEdges,
		Layers:      layers,
		Axes:        axes,
		TotalScore:  totalScore,
		MaxScore:    maxScore,
		Rank:        rank,
		Diagnosis:   diagnosis,
	}
}

// --- Layer A: 構造 (Structure) ---

func evalLayerA(wsRoot string, g haisenGraph) mokutekiLayer {
	apps, adj := shBuildAdjacency(g)

	// A1: DSM bandwidth (Cuthill-McKee optimality)
	dsmR := buildDSMReport(g, 10, false)
	a1 := mokutekiCheck{
		Name: "DSM bandwidth", Weight: 0.30, Score: dsmR.Score,
		Details: fmt.Sprintf("size=%d, bandwidth=%d, clusters=%d", dsmR.Size, dsmR.Bandwidth, len(dsmR.Clusters)),
		Data:    dsmR,
	}

	// A2: Graph connectivity (engagement)
	engagement := mokutekiEngagement(apps, adj, len(g.Apps))
	a2 := mokutekiCheck{
		Name: "Directed graph connectivity", Weight: 0.25, Score: engagement.score,
		Details: engagement.details,
	}

	// A3: Shannon redundancy (information efficiency)
	checks := runAllShannonChecks(wsRoot)
	shannonR := buildShannonReport(checks, 5)
	a3 := mokutekiCheck{
		Name: "Shannon redundancy", Weight: 0.25, Score: shannonR.OverallScore,
		Details: fmt.Sprintf("redundancy_rate=%.1f%%", shannonR.RedundancyRate*100),
	}

	// A4: Hypergraph — collection-mediated coupling (multi-app shared collections)
	hyperScore := mokutekiHypergraph(g)
	a4 := mokutekiCheck{
		Name: "Hypergraph coupling", Weight: 0.10, Score: hyperScore.score,
		Details: hyperScore.details,
	}

	// A5: Type system (WIT export coverage)
	typeScore := mokutekiTypeSystem(g)
	a5 := mokutekiCheck{
		Name: "Category/type system", Weight: 0.10, Score: typeScore.score,
		Details: typeScore.details,
	}

	components := []mokutekiCheck{a1, a2, a3, a4, a5}
	score := mokutekiWeightedScore(components)

	return mokutekiLayer{
		ID: "A", Name: "Structure", NameJP: "構造",
		Weight: 0.30, Score: score, Components: components,
	}
}

// --- Layer B: 不確実性 (Uncertainty) ---

func evalLayerB(g haisenGraph) mokutekiLayer {
	// B1: BayesNet — change propagation risk
	bayesR := buildBayesNetReport(g, 10, 6)
	b1 := mokutekiCheck{
		Name: "BayesNet propagation", Weight: 0.35, Score: bayesR.Score,
		Details: fmt.Sprintf("mean_P=%.3f, max_P=%.3f, risk_paths=%d", bayesR.MeanPropProb, bayesR.MaxPropProb, len(bayesR.HighRiskPaths)),
	}

	// B2: Causal graph — cycle-free DAG property
	apps, adj := shBuildAdjacency(g)
	cycles := dsmDetectCycles(apps, adj)
	cycleScore := 100.0
	if len(cycles) > 0 {
		penalty := 0.0
		for _, c := range cycles {
			if c.Length <= 3 {
				penalty += 15
			} else {
				penalty += 8
			}
		}
		cycleScore = math.Max(0, 100-penalty)
	}
	b2 := mokutekiCheck{
		Name: "Causal DAG acyclicity", Weight: 0.25, Score: cycleScore,
		Details: fmt.Sprintf("cycles=%d", len(cycles)),
	}

	// B3: Information bottleneck — uncertainty concentration
	bnR := buildBottleneckReport(g, 20, 1)
	b3 := mokutekiCheck{
		Name: "Information bottleneck", Weight: 0.25, Score: bnR.Score,
		Details: fmt.Sprintf("system_MI=%.3f bits, critical=%d", bnR.SystemMI, mokutekiCountSeverity(bnR.Bottlenecks, "critical")),
	}

	// B4: State-space entropy — edge type distribution
	edgeTypeCounts := make(map[string]int)
	for _, e := range g.Edges {
		edgeTypeCounts[e.EdgeType]++
	}
	flowH := shEntropy(edgeTypeCounts)
	maxH := math.Log2(math.Max(1, float64(len(edgeTypeCounts))))
	stateScore := 0.0
	if maxH > 0 {
		stateScore = (flowH / maxH) * 100 // higher diversity = better
	}
	b4 := mokutekiCheck{
		Name: "State-space diversity", Weight: 0.15, Score: stateScore,
		Details: fmt.Sprintf("flow_entropy=%.2f/%0.2f bits, types=%d", flowH, maxH, len(edgeTypeCounts)),
	}

	components := []mokutekiCheck{b1, b2, b3, b4}
	score := mokutekiWeightedScore(components)

	return mokutekiLayer{
		ID: "B", Name: "Uncertainty", NameJP: "不確実性",
		Weight: 0.25, Score: score, Components: components,
	}
}

// --- Layer C: 制御 (Control) ---

func evalLayerC(g haisenGraph) mokutekiLayer {
	// C1: POMDP observation — observable state ratio
	c1 := mokutekiPOMDPObservation(g)

	// C2: Constraint optimization — entropy minimization potential
	c2 := mokutekiConstraintOpt(g)

	// C3: MPC — predictive control (multi-step lookahead via bayesnet paths)
	c3 := mokutekiMPC(g)

	// C4: Bandit — optimal next action (which app to improve for max gain)
	c4 := mokutekiBandit(g)

	components := []mokutekiCheck{c1, c2, c3, c4}
	score := mokutekiWeightedScore(components)

	return mokutekiLayer{
		ID: "C", Name: "Control", NameJP: "制御",
		Weight: 0.20, Score: score, Components: components,
	}
}

// --- Layer D: 実装 (Implementation) ---

func evalLayerD(wsRoot string, g haisenGraph, meta map[string]sgMetaResult) mokutekiLayer {
	// D1: Event sourcing — Design E compliance (subscribeRepos handlers)
	d1 := mokutekiEventSourcing(meta)

	// D2: Immutable log — AT Protocol commit stream presence
	d2 := mokutekiImmutableLog(meta)

	// D3: Policy as code — governance WIT coverage
	d3 := mokutekiPolicyAsCode(wsRoot)

	// D4: Typed schema — WIT contract + capability export coverage
	d4 := mokutekiTypedSchema(meta)

	// D5: Attestation — DID + profile + capability declaration
	d5 := mokutekiAttestation(meta)

	components := []mokutekiCheck{d1, d2, d3, d4, d5}
	score := mokutekiWeightedScore(components)

	return mokutekiLayer{
		ID: "D", Name: "Implementation", NameJP: "実装",
		Weight: 0.25, Score: score, Components: components,
	}
}

// --- Layer A helpers ---

func mokutekiEngagement(connectedApps []string, adj map[string]map[string]int, totalApps int) axisResult {
	if totalApps == 0 {
		return axisResult{score: 0, details: "no apps found"}
	}
	connectedCount := len(connectedApps)
	connectivityRate := float64(connectedCount) / float64(totalApps)
	density := 0.0
	if connectedCount > 1 {
		totalPossible := float64(connectedCount * (connectedCount - 1))
		actualEdges := 0
		for _, targets := range adj {
			actualEdges += len(targets)
		}
		density = float64(actualEdges) / totalPossible
	}
	densityCapped := math.Min(density*10, 1.0)
	score := connectivityRate*60 + densityCapped*40
	return axisResult{
		score:   math.Min(score, 100),
		details: fmt.Sprintf("connected=%d/%d (%.0f%%), density=%.4f", connectedCount, totalApps, connectivityRate*100, density),
	}
}

// mokutekiHypergraph evaluates collection-mediated coupling (hyperedges: N apps share 1 collection).
func mokutekiHypergraph(g haisenGraph) axisResult {
	// Count apps per collection (from write edges)
	collWriters := make(map[string]map[string]bool)
	for _, e := range g.Edges {
		if e.EdgeType == "writes" {
			if collWriters[e.To] == nil {
				collWriters[e.To] = make(map[string]bool)
			}
			collWriters[e.To][e.From] = true
		}
	}
	// Score: fewer multi-writer collections = better (less hidden coupling)
	multiWriter := 0
	for _, writers := range collWriters {
		if len(writers) > 1 {
			multiWriter++
		}
	}
	total := len(collWriters)
	score := 100.0
	if total > 0 {
		score = 100.0 * (1.0 - float64(multiWriter)/float64(total))
	}
	return axisResult{
		score:   score,
		details: fmt.Sprintf("collections=%d, multi_writer=%d", total, multiWriter),
	}
}

// mokutekiTypeSystem evaluates WIT type coverage from haisenGraph app metadata.
func mokutekiTypeSystem(g haisenGraph) axisResult {
	total := len(g.Apps)
	if total == 0 {
		return axisResult{score: 0, details: "no apps"}
	}
	withCollections := 0
	for _, a := range g.Apps {
		if len(a.Collections) > 0 {
			withCollections++
		}
	}
	score := float64(withCollections) / float64(total) * 100
	return axisResult{
		score:   score,
		details: fmt.Sprintf("typed=%d/%d", withCollections, total),
	}
}

// --- Layer B helpers ---

func mokutekiCountSeverity(bottlenecks []bottleneckModule, severity string) int {
	count := 0
	for _, b := range bottlenecks {
		if b.Severity == severity {
			count++
		}
	}
	return count
}

// --- Layer C helpers (mokuteki_control.go) ---

// mokutekiPOMDPObservation evaluates the fraction of apps with observable state.
// An app is "observable" if it has subscribeRepos collections (inputs) AND
// outbound edges (outputs). Partial observability = apps with only one direction.
func mokutekiPOMDPObservation(g haisenGraph) mokutekiCheck {
	_, adjTyped := shBuildAdjacencyTyped(g)

	// Build inbound/outbound sets
	inbound := make(map[string]bool)
	outbound := make(map[string]bool)
	for from, targets := range adjTyped {
		outbound[from] = true
		for to := range targets {
			inbound[to] = true
		}
	}

	total := len(g.Apps)
	if total == 0 {
		return mokutekiCheck{Name: "POMDP observation", Weight: 0.30, Score: 0, Details: "no apps"}
	}

	fullyObservable := 0
	partiallyObservable := 0
	for _, a := range g.Apps {
		key := a.Name
		if key == "" {
			key = a.Nanoid
		}
		hasIn := inbound[key]
		hasOut := outbound[key]
		if hasIn && hasOut {
			fullyObservable++
		} else if hasIn || hasOut {
			partiallyObservable++
		}
	}

	// Score: full observable = 100%, partial = 50%, hidden = 0%
	score := (float64(fullyObservable) + float64(partiallyObservable)*0.5) / float64(total) * 100

	return mokutekiCheck{
		Name: "POMDP observation", Weight: 0.30, Score: score,
		Details: fmt.Sprintf("fully=%d, partial=%d, hidden=%d", fullyObservable, partiallyObservable, total-fullyObservable-partiallyObservable),
	}
}

// mokutekiConstraintOpt evaluates how close the system is to entropy-optimal configuration.
func mokutekiConstraintOpt(g haisenGraph) mokutekiCheck {
	minR := buildMinimizeReport(g, 20, 2.0)

	if minR.SystemEntropy == 0 {
		return mokutekiCheck{Name: "Constraint optimization", Weight: 0.25, Score: 100, Details: "trivial graph"}
	}

	reductionRatio := minR.PotentialReduction / minR.SystemEntropy
	if reductionRatio > 1 {
		reductionRatio = 1
	}
	score := (1.0 - reductionRatio) * 100

	return mokutekiCheck{
		Name: "Constraint optimization", Weight: 0.25, Score: score,
		Details: fmt.Sprintf("system_H=%.2f, reducible=%.2f (%.0f%%)", minR.SystemEntropy, minR.PotentialReduction, reductionRatio*100),
	}
}

// mokutekiMPC evaluates multi-step predictive control quality.
// Uses bayesnet path depth as a proxy: longer predictable paths = better MPC horizon.
func mokutekiMPC(g haisenGraph) mokutekiCheck {
	bayesR := buildBayesNetReport(g, 20, 6)

	if len(bayesR.HighRiskPaths) == 0 {
		return mokutekiCheck{Name: "MPC lookahead", Weight: 0.20, Score: 100, Details: "no risk paths (fully predictable)"}
	}

	// Average path confidence (higher probability = more predictable)
	totalP := 0.0
	maxLen := 0
	for _, p := range bayesR.HighRiskPaths {
		totalP += p.Probability
		if p.Length > maxLen {
			maxLen = p.Length
		}
	}
	avgP := totalP / float64(len(bayesR.HighRiskPaths))

	// High average confidence of risk paths = system is predictable but risky
	// We want: predictable (good for MPC) but low risk (inversely scored)
	// Score: predictability (0.5) + risk-absence (0.5)
	predictability := math.Min(avgP*2, 1.0) * 50 // higher P = more predictable
	riskAbsence := (1.0 - bayesR.MeanPropProb) * 50

	score := predictability + riskAbsence

	return mokutekiCheck{
		Name: "MPC lookahead", Weight: 0.20, Score: math.Min(score, 100),
		Details: fmt.Sprintf("risk_paths=%d, max_depth=%d, avg_P=%.3f", len(bayesR.HighRiskPaths), maxLen, avgP),
	}
}

// mokutekiBandit evaluates optimal next-action identification.
// Score = how concentrated the improvement potential is (few high-value targets = efficient bandit).
func mokutekiBandit(g haisenGraph) mokutekiCheck {
	minR := buildMinimizeReport(g, 10, 2.0)

	if len(minR.Proposals) == 0 {
		return mokutekiCheck{Name: "Bandit sensing", Weight: 0.25, Score: 100, Details: "no improvement proposals needed"}
	}

	// Concentration: top proposal's reduction / total potential
	topReduction := minR.Proposals[0].Reduction
	totalReduction := 0.0
	for _, p := range minR.Proposals {
		totalReduction += p.Reduction
	}

	concentration := 0.0
	if totalReduction > 0 {
		concentration = topReduction / totalReduction
	}

	// High concentration = easy to identify next action = good for bandit
	score := concentration * 100

	return mokutekiCheck{
		Name: "Bandit sensing", Weight: 0.25, Score: score,
		Details: fmt.Sprintf("proposals=%d, top_reduction=%.2f/%.2f (%.0f%%)", len(minR.Proposals), topReduction, totalReduction, concentration*100),
	}
}

// --- Layer D helpers ---

// mokutekiEventSourcing checks Design E compliance: apps with subscribeRepos triggers.
func mokutekiEventSourcing(meta map[string]sgMetaResult) mokutekiCheck {
	total := len(meta)
	if total == 0 {
		return mokutekiCheck{Name: "Event sourcing (Design E)", Weight: 0.25, Score: 0, Details: "no apps"}
	}
	withTriggers := 0
	for _, m := range meta {
		if len(m.Collections) > 0 {
			withTriggers++
		}
	}
	score := float64(withTriggers) / float64(total) * 100
	return mokutekiCheck{
		Name: "Event sourcing (Design E)", Weight: 0.25, Score: score,
		Details: fmt.Sprintf("reactive=%d/%d", withTriggers, total),
	}
}

// mokutekiImmutableLog checks AT Protocol immutable log presence (DID + records).
func mokutekiImmutableLog(meta map[string]sgMetaResult) mokutekiCheck {
	total := len(meta)
	if total == 0 {
		return mokutekiCheck{Name: "Immutable log (AT Protocol)", Weight: 0.20, Score: 0, Details: "no apps"}
	}
	withDID := 0
	for _, m := range meta {
		if m.DID != "" {
			withDID++
		}
	}
	score := float64(withDID) / float64(total) * 100
	return mokutekiCheck{
		Name: "Immutable log (AT Protocol)", Weight: 0.20, Score: score,
		Details: fmt.Sprintf("with_DID=%d/%d", withDID, total),
	}
}

// mokutekiPolicyAsCode checks governance WIT import coverage.
func mokutekiPolicyAsCode(wsRoot string) mokutekiCheck {
	meta := sgScanAppMeta(wsRoot)
	total := len(meta)
	if total == 0 {
		return mokutekiCheck{Name: "Policy as code (governance)", Weight: 0.15, Score: 0, Details: "no apps"}
	}
	withGov := 0
	for _, m := range meta {
		for _, imp := range m.WITImports {
			if strings.Contains(imp, "contract") || strings.Contains(imp, "governance") {
				withGov++
				break
			}
		}
	}
	score := float64(withGov) / float64(total) * 100
	return mokutekiCheck{
		Name: "Policy as code (governance)", Weight: 0.15, Score: score,
		Details: fmt.Sprintf("with_governance=%d/%d", withGov, total),
	}
}

// mokutekiTypedSchema checks WIT capability export coverage.
func mokutekiTypedSchema(meta map[string]sgMetaResult) mokutekiCheck {
	total := len(meta)
	if total == 0 {
		return mokutekiCheck{Name: "Typed schema (WIT)", Weight: 0.20, Score: 0, Details: "no apps"}
	}
	withExports := 0
	for _, m := range meta {
		if len(m.WITExports) > 0 {
			withExports++
		}
	}
	score := float64(withExports) / float64(total) * 100
	return mokutekiCheck{
		Name: "Typed schema (WIT)", Weight: 0.20, Score: score,
		Details: fmt.Sprintf("with_exports=%d/%d", withExports, total),
	}
}

// mokutekiAttestation checks DID identity + profile declaration coverage.
func mokutekiAttestation(meta map[string]sgMetaResult) mokutekiCheck {
	total := len(meta)
	if total == 0 {
		return mokutekiCheck{Name: "Attestation (DID+profile)", Weight: 0.20, Score: 0, Details: "no apps"}
	}
	attested := 0
	for _, m := range meta {
		if m.DID != "" && m.DisplayName != "" {
			attested++
		}
	}
	score := float64(attested) / float64(total) * 100
	return mokutekiCheck{
		Name: "Attestation (DID+profile)", Weight: 0.20, Score: score,
		Details: fmt.Sprintf("attested=%d/%d", attested, total),
	}
}

// --- Well-Being axis derivation ---

func deriveWellBeingAxes(a, b, c, d mokutekiLayer) []mokutekiAxis {
	// Each Well-Being axis draws from multiple layers
	engagement := a.Score*0.5 + d.Score*0.5
	competence := a.Score*0.6 + b.Score*0.4
	contribution := b.Score*0.4 + c.Score*0.6
	growth := c.Score*0.5 + a.Score*0.5
	resilience := b.Score*0.5 + d.Score*0.5

	axes := []mokutekiAxis{
		{Name: "Engagement (参与)", Weight: 0.25, Score: engagement, Source: "Layer A + D"},
		{Name: "Competence (能力)", Weight: 0.25, Score: competence, Source: "Layer A + B"},
		{Name: "Contribution (貢献)", Weight: 0.20, Score: contribution, Source: "Layer B + C"},
		{Name: "Growth (成長)", Weight: 0.20, Score: growth, Source: "Layer C + A"},
		{Name: "Resilience (回復)", Weight: 0.10, Score: resilience, Source: "Layer B + D"},
	}
	for i := range axes {
		axes[i].Points = int(axes[i].Score * axes[i].Weight * 120)
	}
	return axes
}

// --- Scoring helpers ---

type axisResult struct {
	score   float64
	details string
}

func mokutekiWeightedScore(checks []mokutekiCheck) float64 {
	sum := 0.0
	for _, c := range checks {
		sum += c.Score * c.Weight
	}
	return sum
}

// --- Diagnosis ---

func mokutekiLayerDiagnosis(layers []mokutekiLayer, axes []mokutekiAxis, totalScore int) []string {
	var diag []string

	// Diagnose layers
	for _, l := range layers {
		if l.Score < 30 {
			diag = append(diag, fmt.Sprintf("[CRITICAL] Layer %s (%s): %.0f/100", l.ID, l.NameJP, l.Score))
		} else if l.Score < 60 {
			diag = append(diag, fmt.Sprintf("[IMPROVE] Layer %s (%s): %.0f/100", l.ID, l.NameJP, l.Score))
		}
		// Diagnose weakest component within layer
		for _, c := range l.Components {
			if c.Score < 30 && c.Weight >= 0.15 {
				diag = append(diag, fmt.Sprintf("  └ %s: %.0f/100 — %s", c.Name, c.Score, c.Details))
			}
		}
	}

	// Diagnose weakest Well-Being axes
	sorted := make([]mokutekiAxis, len(axes))
	copy(sorted, axes)
	sort.Slice(sorted, func(i, j int) bool {
		return sorted[i].Score < sorted[j].Score
	})
	for _, a := range sorted {
		if a.Score < 50 {
			diag = append(diag, fmt.Sprintf("[WELLBEING] %s: %.0f/100 ← %s", a.Name, a.Score, a.Source))
		}
	}

	// Next rank
	rank := resolveRank(totalScore)
	nextRank := mokutekiNextRank(totalScore)
	if nextRank != "" {
		diag = append(diag, fmt.Sprintf("[NEXT] %s → %s (need %d pts)", rank.Name, nextRank, mokutekiPointsToNext(totalScore)))
	}

	if len(diag) == 0 {
		diag = append(diag, "all layers aligned with mokuteki")
	}
	return diag
}

func mokutekiNextRank(score int) string {
	for i := len(mokutekiRankLadder) - 1; i >= 0; i-- {
		if score < mokutekiRankLadder[i].MinScore {
			return mokutekiRankLadder[i].Name
		}
	}
	return ""
}

func mokutekiPointsToNext(score int) int {
	for i := len(mokutekiRankLadder) - 1; i >= 0; i-- {
		if score < mokutekiRankLadder[i].MinScore {
			return mokutekiRankLadder[i].MinScore - score
		}
	}
	return 0
}

// --- Text output ---

func printMokutekiText(r *mokutekiReport) {
	fmt.Printf("mokuteki (目的): %s\n", r.Mokuteki)
	fmt.Printf("  principle: %s\n", r.Principle)
	fmt.Printf("  apps: %d, edges: %d\n", r.TotalApps, r.TotalEdges)
	fmt.Println()

	// Rank display
	fmt.Printf("  ╔══════════════════════════════════════╗\n")
	fmt.Printf("  ║  RANK: %-10s  SCORE: %5d/%d  ║\n", r.Rank.Name, r.TotalScore, r.MaxScore)
	fmt.Printf("  ╚══════════════════════════════════════╝\n")
	fmt.Println()

	// Layers
	fmt.Printf("  layers:\n")
	for _, l := range r.Layers {
		bar := mokutekiBar(l.Score)
		fmt.Printf("    Layer %s %-15s %s %5.1f  (%d pts, ×%.0f%%)\n",
			l.ID, l.NameJP, bar, l.Score, l.Points, l.Weight*100)
		for _, c := range l.Components {
			marker := "  "
			if c.Score < 30 {
				marker = "!!"
			} else if c.Score < 60 {
				marker = "! "
			}
			fmt.Printf("      %s %-28s %5.1f (×%.0f%%)\n", marker, c.Name, c.Score, c.Weight*100)
		}
	}
	fmt.Println()

	// Well-Being axes
	fmt.Printf("  well-becoming:\n")
	for _, a := range r.Axes {
		bar := mokutekiBar(a.Score)
		fmt.Printf("    %-24s %s %5.1f  (%d pts)\n", a.Name, bar, a.Score, a.Points)
	}
	fmt.Println()

	// Diagnosis
	if len(r.Diagnosis) > 0 {
		fmt.Printf("  diagnosis:\n")
		for _, d := range r.Diagnosis {
			fmt.Printf("    %s\n", d)
		}
	}
}

func mokutekiBar(score float64) string {
	width := 20
	filled := int(score / 100 * float64(width))
	if filled > width {
		filled = width
	}
	return "[" + strings.Repeat("█", filled) + strings.Repeat("░", width-filled) + "]"
}
