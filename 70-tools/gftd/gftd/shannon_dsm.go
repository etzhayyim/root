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

// --- Shared Shannon helpers (used by dsm, bayesnet, bottleneck, minimize) ---

// shEntropy computes Shannon entropy H(X) = -Σ p(x) log2(p(x)) from a frequency map.
func shEntropy(counts map[string]int) float64 {
	total := 0
	for _, c := range counts {
		total += c
	}
	if total == 0 {
		return 0
	}
	h := 0.0
	for _, c := range counts {
		if c == 0 {
			continue
		}
		p := float64(c) / float64(total)
		h -= p * math.Log2(p)
	}
	return h
}

// shBuildAdjacency extracts a directed adjacency map from haisenGraph.
// Returns sorted app list and adj[from][to] = edge count.
func shBuildAdjacency(g haisenGraph) ([]string, map[string]map[string]int) {
	appSet := make(map[string]bool)
	adj := make(map[string]map[string]int)

	for _, e := range g.Edges {
		if e.From == "" || e.To == "" || e.From == e.To {
			continue
		}
		appSet[e.From] = true
		appSet[e.To] = true
		if adj[e.From] == nil {
			adj[e.From] = make(map[string]int)
		}
		adj[e.From][e.To]++
	}

	apps := make([]string, 0, len(appSet))
	for a := range appSet {
		apps = append(apps, a)
	}
	sort.Strings(apps)
	return apps, adj
}

// shBuildAdjacencyTyped extracts typed adjacency: adj[from][to][edgeType] = count.
func shBuildAdjacencyTyped(g haisenGraph) ([]string, map[string]map[string]map[string]int) {
	appSet := make(map[string]bool)
	adj := make(map[string]map[string]map[string]int)

	for _, e := range g.Edges {
		if e.From == "" || e.To == "" || e.From == e.To {
			continue
		}
		appSet[e.From] = true
		appSet[e.To] = true
		if adj[e.From] == nil {
			adj[e.From] = make(map[string]map[string]int)
		}
		if adj[e.From][e.To] == nil {
			adj[e.From][e.To] = make(map[string]int)
		}
		adj[e.From][e.To][e.EdgeType]++
	}

	apps := make([]string, 0, len(appSet))
	for a := range appSet {
		apps = append(apps, a)
	}
	sort.Strings(apps)
	return apps, adj
}

// shAppProject builds a map from app name to project name using haisenGraph.
func shAppProject(g haisenGraph) map[string]string {
	m := make(map[string]string)
	for _, a := range g.Apps {
		key := a.Name
		if key == "" {
			key = a.Nanoid
		}
		m[key] = a.Project
	}
	return m
}

// --- DSM types ---

// dsmEntry represents a non-zero cell in the DSM.
type dsmEntry struct {
	From  string   `json:"from"`
	To    string   `json:"to"`
	Count int      `json:"count"`
	Types []string `json:"types,omitempty"`
}

// dsmCluster represents a connected component in the dependency graph.
type dsmCluster struct {
	Name         string   `json:"name"`
	Members      []string `json:"members"`
	InternalDeps int      `json:"internal_deps"`
	ExternalDeps int      `json:"external_deps"`
}

// dsmCycle represents a detected dependency cycle.
type dsmCycle struct {
	Path   []string `json:"path"`
	Length int      `json:"length"`
}

// dsmReport is the full DSM analysis output.
type dsmReport struct {
	GeneratedAt string       `json:"generated_at"`
	Size        int          `json:"size"`
	Apps        []string     `json:"apps"`
	Matrix      [][]int      `json:"matrix"`
	Entries     []dsmEntry   `json:"entries,omitempty"`
	Clusters    []dsmCluster `json:"clusters"`
	Cycles      []dsmCycle   `json:"cycles"`
	Bandwidth   int          `json:"bandwidth"`
	Score       float64      `json:"score"`
}

// --- DSM entry point ---

func runShannonDSM(args []string) error {
	fs := flag.NewFlagSet("shannon dsm", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	topN := fs.Int("top", 10, "number of clusters to show")
	noReorder := fs.Bool("no-reorder", false, "skip Cuthill-McKee reordering")
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
	report := buildDSMReport(graph, *topN, *noReorder)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printDSMText(report)
	return nil
}

func buildDSMReport(g haisenGraph, topN int, noReorder bool) *dsmReport {
	apps, adj := shBuildAdjacency(g)
	n := len(apps)

	if n == 0 {
		return &dsmReport{
			GeneratedAt: time.Now().UTC().Format(time.RFC3339),
			Score:       100,
		}
	}

	// Build index
	idx := make(map[string]int, n)
	for i, a := range apps {
		idx[a] = i
	}

	// Build matrix
	matrix := make([][]int, n)
	for i := range matrix {
		matrix[i] = make([]int, n)
	}
	for from, targets := range adj {
		fi, ok := idx[from]
		if !ok {
			continue
		}
		for to, count := range targets {
			ti, ok := idx[to]
			if !ok {
				continue
			}
			matrix[fi][ti] = count
		}
	}

	// Cuthill-McKee reorder
	perm := make([]int, n)
	for i := range perm {
		perm[i] = i
	}
	if !noReorder && n > 2 {
		perm = dsmCuthillMcKee(matrix, n)
	}

	// Apply permutation
	reordered := make([]string, n)
	reorderedMatrix := make([][]int, n)
	for i := range reorderedMatrix {
		reorderedMatrix[i] = make([]int, n)
	}
	for i, pi := range perm {
		reordered[i] = apps[pi]
		for j, pj := range perm {
			reorderedMatrix[i][j] = matrix[pi][pj]
		}
	}

	// Collect non-zero entries
	var entries []dsmEntry
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			if reorderedMatrix[i][j] > 0 {
				entries = append(entries, dsmEntry{
					From:  reordered[i],
					To:    reordered[j],
					Count: reorderedMatrix[i][j],
				})
			}
		}
	}

	// Bandwidth
	bw := 0
	for i := 0; i < n; i++ {
		for j := 0; j < n; j++ {
			if reorderedMatrix[i][j] > 0 {
				d := i - j
				if d < 0 {
					d = -d
				}
				if d > bw {
					bw = d
				}
			}
		}
	}

	// Cycles
	cycles := dsmDetectCycles(reordered, adj)

	// Clusters (connected components on undirected version)
	clusters := dsmFindClusters(reordered, adj)
	sort.Slice(clusters, func(i, j int) bool {
		return len(clusters[i].Members) > len(clusters[j].Members)
	})
	if len(clusters) > topN {
		clusters = clusters[:topN]
	}

	// Score: lower bandwidth relative to N = better
	score := 100.0
	if n > 1 {
		score = 100.0 * (1.0 - float64(bw)/float64(n))
	}
	if score < 0 {
		score = 0
	}

	return &dsmReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Size:        n,
		Apps:        reordered,
		Matrix:      reorderedMatrix,
		Entries:     entries,
		Clusters:    clusters,
		Cycles:      cycles,
		Bandwidth:   bw,
		Score:       score,
	}
}

// dsmCuthillMcKee performs Reverse Cuthill-McKee reordering for bandwidth minimization.
// Returns a permutation array: result[new_index] = old_index.
func dsmCuthillMcKee(matrix [][]int, n int) []int {
	// Compute degree (undirected: count non-zero in row + col, deduplicated)
	degree := make([]int, n)
	for i := 0; i < n; i++ {
		neighbors := make(map[int]bool)
		for j := 0; j < n; j++ {
			if i != j && (matrix[i][j] > 0 || matrix[j][i] > 0) {
				neighbors[j] = true
			}
		}
		degree[i] = len(neighbors)
	}

	visited := make([]bool, n)
	var result []int

	for len(result) < n {
		// Find unvisited node with minimum degree
		start := -1
		minDeg := n + 1
		for i := 0; i < n; i++ {
			if !visited[i] && degree[i] < minDeg {
				minDeg = degree[i]
				start = i
			}
		}
		if start == -1 {
			break
		}

		// BFS from start
		queue := []int{start}
		visited[start] = true
		for len(queue) > 0 {
			node := queue[0]
			queue = queue[1:]
			result = append(result, node)

			// Collect unvisited neighbors, sort by degree ascending
			var neighbors []int
			for j := 0; j < n; j++ {
				if !visited[j] && (matrix[node][j] > 0 || matrix[j][node] > 0) {
					neighbors = append(neighbors, j)
				}
			}
			sort.Slice(neighbors, func(a, b int) bool {
				return degree[neighbors[a]] < degree[neighbors[b]]
			})
			for _, nb := range neighbors {
				if !visited[nb] {
					visited[nb] = true
					queue = append(queue, nb)
				}
			}
		}
	}

	// Reverse for RCM (Reverse Cuthill-McKee)
	for i, j := 0, len(result)-1; i < j; i, j = i+1, j-1 {
		result[i], result[j] = result[j], result[i]
	}

	return result
}

// dsmDetectCycles finds all simple cycles up to length 8 using DFS coloring.
func dsmDetectCycles(apps []string, adj map[string]map[string]int) []dsmCycle {
	const maxLen = 8
	const maxCycles = 50

	var cycles []dsmCycle
	seen := make(map[string]bool) // deduplicate cycle canonical forms

	// DFS per start node
	for _, start := range apps {
		if len(cycles) >= maxCycles {
			break
		}
		var dfs func(node string, path []string)
		dfs = func(node string, path []string) {
			if len(cycles) >= maxCycles {
				return
			}
			if len(path) > maxLen {
				return
			}
			for next := range adj[node] {
				if next == start && len(path) >= 2 {
					// Found cycle
					cyclePath := make([]string, len(path))
					copy(cyclePath, path)
					cyclePath = append(cyclePath, start)
					canon := dsmCanonCycle(cyclePath[:len(cyclePath)-1])
					if !seen[canon] {
						seen[canon] = true
						cycles = append(cycles, dsmCycle{
							Path:   cyclePath,
							Length: len(cyclePath) - 1,
						})
					}
					continue
				}
				// Check not already in path
				inPath := false
				for _, p := range path {
					if p == next {
						inPath = true
						break
					}
				}
				if !inPath {
					dfs(next, append(path, next))
				}
			}
		}
		dfs(start, []string{start})
	}

	sort.Slice(cycles, func(i, j int) bool {
		return cycles[i].Length < cycles[j].Length
	})
	return cycles
}

// dsmCanonCycle returns a canonical string for a cycle (rotation-independent).
func dsmCanonCycle(path []string) string {
	if len(path) == 0 {
		return ""
	}
	// Find minimum rotation
	minIdx := 0
	for i := 1; i < len(path); i++ {
		if path[i] < path[minIdx] {
			minIdx = i
		}
	}
	rotated := make([]string, len(path))
	for i := range path {
		rotated[i] = path[(i+minIdx)%len(path)]
	}
	return strings.Join(rotated, "→")
}

// dsmFindClusters finds connected components (undirected).
func dsmFindClusters(apps []string, adj map[string]map[string]int) []dsmCluster {
	// Build undirected neighbor map
	neighbors := make(map[string]map[string]bool)
	for from, targets := range adj {
		for to := range targets {
			if neighbors[from] == nil {
				neighbors[from] = make(map[string]bool)
			}
			if neighbors[to] == nil {
				neighbors[to] = make(map[string]bool)
			}
			neighbors[from][to] = true
			neighbors[to][from] = true
		}
	}

	visited := make(map[string]bool)
	var clusters []dsmCluster

	for _, start := range apps {
		if visited[start] {
			continue
		}
		// BFS
		var members []string
		queue := []string{start}
		visited[start] = true
		for len(queue) > 0 {
			node := queue[0]
			queue = queue[1:]
			members = append(members, node)
			for nb := range neighbors[node] {
				if !visited[nb] {
					visited[nb] = true
					queue = append(queue, nb)
				}
			}
		}
		sort.Strings(members)

		memberSet := make(map[string]bool)
		for _, m := range members {
			memberSet[m] = true
		}

		internal, external := 0, 0
		for _, m := range members {
			for to, count := range adj[m] {
				if memberSet[to] {
					internal += count
				} else {
					external += count
				}
			}
		}

		clusters = append(clusters, dsmCluster{
			Name:         fmt.Sprintf("cluster-%d", len(clusters)+1),
			Members:      members,
			InternalDeps: internal,
			ExternalDeps: external,
		})
	}
	return clusters
}

func printDSMText(r *dsmReport) {
	fmt.Printf("shannon dsm:\n")
	fmt.Printf("  generated_at: %s\n", r.GeneratedAt)
	fmt.Printf("  size: %d × %d\n", r.Size, r.Size)
	fmt.Printf("  bandwidth: %d\n", r.Bandwidth)
	fmt.Printf("  score: %.1f\n", r.Score)

	// Print compact matrix (max 40 apps)
	displayN := r.Size
	if displayN > 40 {
		displayN = 40
	}
	if displayN > 0 && displayN <= 40 {
		fmt.Printf("\n  matrix (%d apps):\n", displayN)
		// Abbreviated names (first 8 chars)
		names := make([]string, displayN)
		for i := 0; i < displayN; i++ {
			n := r.Apps[i]
			if len(n) > 8 {
				n = n[:8]
			}
			names[i] = n
		}
		// Header
		fmt.Printf("  %8s ", "")
		for i := 0; i < displayN; i++ {
			fmt.Printf("%s ", string(names[i][0]))
		}
		fmt.Println()
		// Rows
		for i := 0; i < displayN; i++ {
			fmt.Printf("  %8s ", names[i])
			for j := 0; j < displayN; j++ {
				v := r.Matrix[i][j]
				if i == j {
					fmt.Print("· ")
				} else if v > 0 {
					fmt.Print("+ ")
				} else {
					fmt.Print(". ")
				}
			}
			fmt.Println()
		}
	}

	if len(r.Clusters) > 0 {
		fmt.Printf("\n  clusters: %d\n", len(r.Clusters))
		for _, c := range r.Clusters {
			fmt.Printf("    %s (%d members, %d internal, %d external)\n",
				c.Name, len(c.Members), c.InternalDeps, c.ExternalDeps)
			if len(c.Members) <= 10 {
				fmt.Printf("      members: %s\n", strings.Join(c.Members, ", "))
			}
		}
	}

	if len(r.Cycles) > 0 {
		fmt.Printf("\n  cycles: %d\n", len(r.Cycles))
		maxShow := 10
		if len(r.Cycles) < maxShow {
			maxShow = len(r.Cycles)
		}
		for i := 0; i < maxShow; i++ {
			fmt.Printf("    [len=%d] %s\n", r.Cycles[i].Length, strings.Join(r.Cycles[i].Path, " → "))
		}
		if len(r.Cycles) > maxShow {
			fmt.Printf("    ... and %d more\n", len(r.Cycles)-maxShow)
		}
	}
}
