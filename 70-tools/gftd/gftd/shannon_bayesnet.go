package main

import (
	"container/heap"
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"os"
	"sort"
	"strings"
	"time"
)

// --- Edge type coupling weights ---

// shEdgeTypeWeight returns the coupling weight for a haisen edge type.
// Higher weight = stronger coupling = higher change propagation probability.
var shEdgeTypeWeights = map[string]float64{
	"invoke":          0.8,
	"writes":          0.5,
	"subscribe":       0.4,
	"reads":           0.3,
	"follow":          0.1,
	"service_binding": 0.6,
}

// --- BayesNet types ---

// bayesNode represents a module in the Bayesian change-propagation network.
type bayesNode struct {
	App        string  `json:"app"`
	FanIn      int     `json:"fan_in"`
	FanOut     int     `json:"fan_out"`
	Prior      float64 `json:"prior"`
	Redundancy float64 `json:"redundancy"`
}

// bayesEdge represents a directed edge with conditional change probability.
type bayesEdge struct {
	From        string   `json:"from"`
	To          string   `json:"to"`
	Strength    float64  `json:"strength"`
	Conditional float64  `json:"conditional"`
	EdgeTypes   []string `json:"edge_types"`
}

// bayesPath represents a high-risk change propagation path.
type bayesPath struct {
	Nodes       []string `json:"nodes"`
	Probability float64  `json:"probability"`
	Length      int      `json:"length"`
}

// bayesReport is the full Bayesian network analysis output.
type bayesReport struct {
	GeneratedAt   string      `json:"generated_at"`
	TotalApps     int         `json:"total_apps"`
	TotalEdges    int         `json:"total_edges"`
	Nodes         []bayesNode `json:"nodes"`
	Edges         []bayesEdge `json:"edges"`
	HighRiskPaths []bayesPath `json:"high_risk_paths"`
	MeanPropProb  float64     `json:"mean_propagation_probability"`
	MaxPropProb   float64     `json:"max_propagation_probability"`
	Score         float64     `json:"score"`
}

// --- Priority queue for Dijkstra ---

type bayesPQItem struct {
	app     string
	negLogP float64 // -log(probability) for min-heap
	path    []string
	index   int
}

type bayesPQ []*bayesPQItem

func (pq bayesPQ) Len() int            { return len(pq) }
func (pq bayesPQ) Less(i, j int) bool   { return pq[i].negLogP < pq[j].negLogP }
func (pq bayesPQ) Swap(i, j int)        { pq[i], pq[j] = pq[j], pq[i]; pq[i].index = i; pq[j].index = j }
func (pq *bayesPQ) Push(x interface{})  { item := x.(*bayesPQItem); item.index = len(*pq); *pq = append(*pq, item) }
func (pq *bayesPQ) Pop() interface{}    { old := *pq; n := len(old); item := old[n-1]; old[n-1] = nil; item.index = -1; *pq = old[:n-1]; return item }

// --- BayesNet entry point ---

func runShannonBayesNet(args []string) error {
	fs := flag.NewFlagSet("shannon bayesnet", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	topN := fs.Int("top", 10, "number of high-risk paths to show")
	maxDepth := fs.Int("max-depth", 6, "maximum path length for risk analysis")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	wsRoot, err := resolveShannonRoot(*workspaceDir)
	if err != nil {
		return err
	}

	graph := haisenScanWorkspace(wsRoot, false)
	report := buildBayesNetReport(graph, *topN, *maxDepth)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printBayesNetText(report)
	return nil
}

func buildBayesNetReport(g haisenGraph, topN, maxDepth int) *bayesReport {
	apps, adjTyped := shBuildAdjacencyTyped(g)
	n := len(apps)

	if n == 0 {
		return &bayesReport{
			GeneratedAt: time.Now().UTC().Format(time.RFC3339),
			Score:       100,
		}
	}

	// Compute fan-in, fan-out per app
	fanIn := make(map[string]int)
	fanOut := make(map[string]int)
	for from, targets := range adjTyped {
		for to := range targets {
			fanOut[from]++
			fanIn[to]++
		}
	}

	maxFanOut := 1
	for _, fo := range fanOut {
		if fo > maxFanOut {
			maxFanOut = fo
		}
	}

	// Build nodes with priors
	nodes := make([]bayesNode, 0, n)
	for _, app := range apps {
		prior := float64(fanOut[app]) / float64(maxFanOut)
		nodes = append(nodes, bayesNode{
			App:    app,
			FanIn:  fanIn[app],
			FanOut: fanOut[app],
			Prior:  prior,
		})
	}

	// Build edges with coupling strength and conditional probability
	var edges []bayesEdge
	edgeAdj := make(map[string][]bayesEdge) // from → edges for path search

	for from, targets := range adjTyped {
		for to, types := range targets {
			// Compute coupling strength from edge type weights
			strength := 0.0
			var edgeTypes []string
			for t, count := range types {
				w, ok := shEdgeTypeWeights[t]
				if !ok {
					w = 0.2
				}
				strength += w * float64(count)
				edgeTypes = append(edgeTypes, t)
			}
			// Normalize to [0, 1]
			if strength > 1.0 {
				strength = 1.0 - 1.0/(1.0+strength) // sigmoid-like saturation
			}

			// Conditional probability = coupling strength
			conditional := strength

			sort.Strings(edgeTypes)
			edge := bayesEdge{
				From:        from,
				To:          to,
				Strength:    strength,
				Conditional: conditional,
				EdgeTypes:   edgeTypes,
			}
			edges = append(edges, edge)
			edgeAdj[from] = append(edgeAdj[from], edge)
		}
	}

	// Find high-risk paths using modified Dijkstra on -log(P)
	// We want paths with maximum probability product = minimum -log sum
	highRiskPaths := bayesFindHighRiskPaths(apps, edgeAdj, topN, maxDepth)

	// Compute mean and max propagation probability
	meanP, maxP := 0.0, 0.0
	if len(edges) > 0 {
		for _, e := range edges {
			meanP += e.Conditional
			if e.Conditional > maxP {
				maxP = e.Conditional
			}
		}
		meanP /= float64(len(edges))
	}

	// Sort edges by conditional descending
	sort.Slice(edges, func(i, j int) bool {
		return edges[i].Conditional > edges[j].Conditional
	})

	// Score: lower mean propagation = better
	score := 100.0 * (1.0 - meanP)
	if score < 0 {
		score = 0
	}

	return &bayesReport{
		GeneratedAt:   time.Now().UTC().Format(time.RFC3339),
		TotalApps:     n,
		TotalEdges:    len(edges),
		Nodes:         nodes,
		Edges:         edges,
		HighRiskPaths: highRiskPaths,
		MeanPropProb:  meanP,
		MaxPropProb:   maxP,
		Score:         score,
	}
}

// bayesFindHighRiskPaths finds the top-N highest probability multi-hop paths.
// Uses Dijkstra on -log(P) from each source, collecting paths of length >= 2.
func bayesFindHighRiskPaths(apps []string, edgeAdj map[string][]bayesEdge, topN, maxDepth int) []bayesPath {
	var allPaths []bayesPath

	for _, source := range apps {
		paths := bayesDijkstraFrom(source, edgeAdj, maxDepth)
		allPaths = append(allPaths, paths...)
	}

	// Sort by probability descending
	sort.Slice(allPaths, func(i, j int) bool {
		return allPaths[i].Probability > allPaths[j].Probability
	})

	if len(allPaths) > topN {
		allPaths = allPaths[:topN]
	}
	return allPaths
}

// bayesDijkstraFrom runs Dijkstra from a single source, returning paths of length >= 2.
func bayesDijkstraFrom(source string, edgeAdj map[string][]bayesEdge, maxDepth int) []bayesPath {
	pq := &bayesPQ{}
	heap.Init(pq)

	heap.Push(pq, &bayesPQItem{
		app:     source,
		negLogP: 0,
		path:    []string{source},
	})

	visited := make(map[string]bool)
	var paths []bayesPath
	const maxPathsPerSource = 5

	for pq.Len() > 0 && len(paths) < maxPathsPerSource {
		item := heap.Pop(pq).(*bayesPQItem)

		if visited[item.app] && len(item.path) > 1 {
			continue
		}
		visited[item.app] = true

		// Record path if length >= 2
		if len(item.path) >= 3 {
			prob := math.Exp(-item.negLogP)
			if prob > 0.01 { // only include paths with > 1% probability
				pathCopy := make([]string, len(item.path))
				copy(pathCopy, item.path)
				paths = append(paths, bayesPath{
					Nodes:       pathCopy,
					Probability: prob,
					Length:      len(pathCopy) - 1,
				})
			}
		}

		if len(item.path) > maxDepth {
			continue
		}

		// Expand neighbors
		for _, edge := range edgeAdj[item.app] {
			if edge.Conditional <= 0 {
				continue
			}
			// Check not in current path (avoid cycles)
			inPath := false
			for _, p := range item.path {
				if p == edge.To {
					inPath = true
					break
				}
			}
			if inPath {
				continue
			}

			newNegLogP := item.negLogP + (-math.Log(edge.Conditional))
			newPath := make([]string, len(item.path)+1)
			copy(newPath, item.path)
			newPath[len(item.path)] = edge.To

			heap.Push(pq, &bayesPQItem{
				app:     edge.To,
				negLogP: newNegLogP,
				path:    newPath,
			})
		}
	}

	return paths
}

func printBayesNetText(r *bayesReport) {
	fmt.Printf("shannon bayesnet:\n")
	fmt.Printf("  generated_at: %s\n", r.GeneratedAt)
	fmt.Printf("  total_apps: %d\n", r.TotalApps)
	fmt.Printf("  total_edges: %d\n", r.TotalEdges)
	fmt.Printf("  mean_propagation: %.3f\n", r.MeanPropProb)
	fmt.Printf("  max_propagation: %.3f\n", r.MaxPropProb)
	fmt.Printf("  score: %.1f\n", r.Score)

	if len(r.HighRiskPaths) > 0 {
		fmt.Printf("\n  high-risk paths:\n")
		for i, p := range r.HighRiskPaths {
			fmt.Printf("    %d. [P=%.3f, len=%d] %s\n",
				i+1, p.Probability, p.Length, strings.Join(p.Nodes, " → "))
		}
	}

	// Top coupled edges
	maxEdges := 10
	if len(r.Edges) < maxEdges {
		maxEdges = len(r.Edges)
	}
	if maxEdges > 0 {
		fmt.Printf("\n  strongest couplings:\n")
		for i := 0; i < maxEdges; i++ {
			e := r.Edges[i]
			fmt.Printf("    %s → %s (P=%.3f, types=%s)\n",
				e.From, e.To, e.Conditional, strings.Join(e.EdgeTypes, ","))
		}
	}
}
