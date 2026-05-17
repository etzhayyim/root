package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"sort"
	"strings"
	"time"
)

// --- Minimize types ---

// entropyModule represents a module's entropy decomposition.
type entropyModule struct {
	App        string  `json:"app"`
	Project    string  `json:"project"`
	CouplingH  float64 `json:"coupling_entropy"`
	CohesionH  float64 `json:"cohesion_entropy"`
	NetEntropy float64 `json:"net_entropy"`
}

// entropyProposal represents a suggested reorganization to reduce entropy.
type entropyProposal struct {
	Action           string   `json:"action"`
	Targets          []string `json:"targets"`
	Reason           string   `json:"reason"`
	CurrentEntropy   float64  `json:"current_entropy"`
	PredictedEntropy float64  `json:"predicted_entropy"`
	Reduction        float64  `json:"reduction"`
	ReductionPct     float64  `json:"reduction_pct"`
}

// entropyReport is the full entropy minimization analysis output.
type entropyReport struct {
	GeneratedAt        string            `json:"generated_at"`
	TotalApps          int               `json:"total_apps"`
	SystemEntropy      float64           `json:"system_entropy"`
	CohesionEntropy    float64           `json:"cohesion_entropy"`
	Modules            []entropyModule   `json:"modules"`
	Proposals          []entropyProposal `json:"proposals"`
	PotentialReduction float64           `json:"potential_reduction"`
	Score              float64           `json:"score"`
}

// --- Minimize entry point ---

func runShannonMinimize(args []string) error {
	fs := flag.NewFlagSet("shannon minimize", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	topN := fs.Int("top", 15, "number of proposals to show")
	threshold := fs.Float64("threshold", 2.0, "entropy threshold for split proposals (bits)")
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
	report := buildMinimizeReport(graph, *topN, *threshold)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printMinimizeText(report)
	return nil
}

func buildMinimizeReport(g haisenGraph, topN int, threshold float64) *entropyReport {
	apps, adj := shBuildAdjacency(g)
	appProj := shAppProject(g)
	n := len(apps)

	if n == 0 {
		return &entropyReport{
			GeneratedAt: time.Now().UTC().Format(time.RFC3339),
			Score:       100,
		}
	}

	// Per-app coupling entropy (distribution of outbound targets)
	modules := make([]entropyModule, 0, n)
	totalCoupling := 0.0
	totalCohesion := 0.0

	for _, app := range apps {
		targets := adj[app]
		proj := appProj[app]

		// Coupling entropy: distribution of outbound target apps
		couplingCounts := make(map[string]int)
		for to, count := range targets {
			couplingCounts[to] = count
		}
		couplingH := shEntropy(couplingCounts)

		// Cohesion entropy: distribution of intra-project edges only
		cohesionCounts := make(map[string]int)
		for to, count := range targets {
			toProj := appProj[to]
			if toProj == proj && proj != "" {
				cohesionCounts[to] = count
			}
		}
		cohesionH := shEntropy(cohesionCounts)

		netH := couplingH - cohesionH

		modules = append(modules, entropyModule{
			App:        app,
			Project:    proj,
			CouplingH:  couplingH,
			CohesionH:  cohesionH,
			NetEntropy: netH,
		})

		totalCoupling += couplingH
		totalCohesion += cohesionH
	}

	// Sort modules by net entropy descending (worst first)
	sort.Slice(modules, func(i, j int) bool {
		return modules[i].NetEntropy > modules[j].NetEntropy
	})

	// Generate proposals
	var proposals []entropyProposal

	// 1. Merge proposals: find same-project pairs with high mutual coupling
	proposals = append(proposals, minimizeMergeProposals(apps, adj, appProj)...)

	// 2. Split proposals: apps with coupling entropy above threshold
	proposals = append(proposals, minimizeSplitProposals(apps, adj, threshold)...)

	// 3. Move proposals: apps where >70% of edges go to another project
	proposals = append(proposals, minimizeMoveProposals(apps, adj, appProj)...)

	// Sort proposals by reduction descending
	sort.Slice(proposals, func(i, j int) bool {
		return proposals[i].Reduction > proposals[j].Reduction
	})
	if len(proposals) > topN {
		proposals = proposals[:topN]
	}

	// Potential reduction
	potentialReduction := 0.0
	for _, p := range proposals {
		potentialReduction += p.Reduction
	}

	// Score: high cohesion relative to total = good
	score := 50.0
	total := totalCoupling + totalCohesion
	if total > 0 {
		score = 100.0 * totalCohesion / total
	}
	if score > 100 {
		score = 100
	}

	return &entropyReport{
		GeneratedAt:        time.Now().UTC().Format(time.RFC3339),
		TotalApps:          n,
		SystemEntropy:      totalCoupling,
		CohesionEntropy:    totalCohesion,
		Modules:            modules,
		Proposals:          proposals,
		PotentialReduction: potentialReduction,
		Score:              score,
	}
}

// minimizeMergeProposals finds same-project pairs with high mutual coupling.
func minimizeMergeProposals(apps []string, adj map[string]map[string]int, appProj map[string]string) []entropyProposal {
	var proposals []entropyProposal
	checked := make(map[string]bool)

	for _, a := range apps {
		projA := appProj[a]
		if projA == "" {
			continue
		}
		for _, b := range apps {
			if a >= b {
				continue
			}
			key := a + "|" + b
			if checked[key] {
				continue
			}
			checked[key] = true

			projB := appProj[b]
			if projA != projB {
				continue
			}

			// Mutual coupling: edges A→B + B→A
			abCount := adj[a][b]
			baCount := 0
			if adj[b] != nil {
				baCount = adj[b][a]
			}
			mutual := abCount + baCount
			if mutual < 2 {
				continue
			}

			// Current entropy of A and B separately
			hA := shEntropy(adj[a])
			hB := shEntropy(adj[b])
			currentH := hA + hB

			// Predicted entropy after merge: combine outbound edges
			merged := make(map[string]int)
			for to, c := range adj[a] {
				if to != b {
					merged[to] += c
				}
			}
			for to, c := range adj[b] {
				if to != a {
					merged[to] += c
				}
			}
			predictedH := shEntropy(merged)

			reduction := currentH - predictedH
			if reduction <= 0 {
				continue
			}

			pct := 0.0
			if currentH > 0 {
				pct = reduction / currentH * 100
			}

			proposals = append(proposals, entropyProposal{
				Action:           "merge",
				Targets:          []string{a, b},
				Reason:           fmt.Sprintf("high mutual coupling (%d edges) in project %s", mutual, projA),
				CurrentEntropy:   currentH,
				PredictedEntropy: predictedH,
				Reduction:        reduction,
				ReductionPct:     pct,
			})
		}
	}
	return proposals
}

// minimizeSplitProposals finds apps with coupling entropy above threshold.
func minimizeSplitProposals(apps []string, adj map[string]map[string]int, threshold float64) []entropyProposal {
	var proposals []entropyProposal

	for _, app := range apps {
		targets := adj[app]
		if len(targets) < 3 {
			continue
		}

		h := shEntropy(targets)
		if h < threshold {
			continue
		}

		// Group targets by magnitude: high-count vs low-count
		type targetCount struct {
			name  string
			count int
		}
		var sorted []targetCount
		for to, c := range targets {
			sorted = append(sorted, targetCount{to, c})
		}
		sort.Slice(sorted, func(i, j int) bool {
			return sorted[i].count > sorted[j].count
		})

		// Split at median: weighted entropy comparison
		mid := len(sorted) / 2
		group1 := make(map[string]int)
		group2 := make(map[string]int)
		n1, n2 := 0, 0
		for i, tc := range sorted {
			if i < mid {
				group1[tc.name] = tc.count
				n1 += tc.count
			} else {
				group2[tc.name] = tc.count
				n2 += tc.count
			}
		}

		totalN := n1 + n2
		if totalN == 0 {
			continue
		}
		h1 := shEntropy(group1)
		h2 := shEntropy(group2)
		// Weighted average entropy of the two sub-groups
		predictedH := (float64(n1)*h1 + float64(n2)*h2) / float64(totalN)
		reduction := h - predictedH

		if reduction <= 0 {
			continue
		}

		pct := 0.0
		if h > 0 {
			pct = reduction / h * 100
		}

		proposals = append(proposals, entropyProposal{
			Action:           "split",
			Targets:          []string{app},
			Reason:           fmt.Sprintf("high coupling entropy (%.2f bits, %d targets)", h, len(targets)),
			CurrentEntropy:   h,
			PredictedEntropy: predictedH,
			Reduction:        reduction,
			ReductionPct:     pct,
		})
	}
	return proposals
}

// minimizeMoveProposals finds apps where >70% of edges go to another project.
func minimizeMoveProposals(apps []string, adj map[string]map[string]int, appProj map[string]string) []entropyProposal {
	var proposals []entropyProposal

	for _, app := range apps {
		targets := adj[app]
		if len(targets) < 2 {
			continue
		}

		myProj := appProj[app]
		if myProj == "" {
			continue
		}

		// Count edges per target project
		projEdges := make(map[string]int)
		totalEdges := 0
		for to, c := range targets {
			proj := appProj[to]
			if proj != "" {
				projEdges[proj] += c
			}
			totalEdges += c
		}

		if totalEdges == 0 {
			continue
		}

		// Find the project with most edges (excluding own project)
		bestProj := ""
		bestCount := 0
		for proj, count := range projEdges {
			if proj != myProj && count > bestCount {
				bestCount = count
				bestProj = proj
			}
		}

		if bestProj == "" {
			continue
		}

		crossRatio := float64(bestCount) / float64(totalEdges)
		if crossRatio < 0.7 {
			continue
		}

		// Estimate entropy reduction: moving removes cross-project edges
		currentCounts := make(map[string]int)
		for to, c := range targets {
			currentCounts[to] = c
		}
		currentH := shEntropy(currentCounts)

		// After move, edges to bestProj become intra-project (still exist but reduce coupling)
		// Simplified: entropy decreases proportional to edges that become internal
		predictedH := currentH * (1.0 - crossRatio*0.5)
		reduction := currentH - predictedH

		if reduction <= 0 {
			continue
		}

		pct := 0.0
		if currentH > 0 {
			pct = reduction / currentH * 100
		}

		proposals = append(proposals, entropyProposal{
			Action:           "move",
			Targets:          []string{app},
			Reason:           fmt.Sprintf("%.0f%% of edges go to project %s (current: %s)", crossRatio*100, bestProj, myProj),
			CurrentEntropy:   currentH,
			PredictedEntropy: predictedH,
			Reduction:        reduction,
			ReductionPct:     pct,
		})
	}
	return proposals
}

func printMinimizeText(r *entropyReport) {
	fmt.Printf("shannon minimize:\n")
	fmt.Printf("  generated_at: %s\n", r.GeneratedAt)
	fmt.Printf("  total_apps: %d\n", r.TotalApps)
	fmt.Printf("  system_entropy: %.3f bits (coupling)\n", r.SystemEntropy)
	fmt.Printf("  cohesion_entropy: %.3f bits\n", r.CohesionEntropy)
	fmt.Printf("  potential_reduction: %.3f bits\n", r.PotentialReduction)
	fmt.Printf("  score: %.1f\n", r.Score)

	// Top entropy modules
	maxShow := 10
	if len(r.Modules) < maxShow {
		maxShow = len(r.Modules)
	}
	if maxShow > 0 {
		fmt.Printf("\n  highest entropy modules:\n")
		for i := 0; i < maxShow; i++ {
			m := r.Modules[i]
			fmt.Printf("    %s (coupling=%.2f, cohesion=%.2f, net=%.2f) [%s]\n",
				m.App, m.CouplingH, m.CohesionH, m.NetEntropy, m.Project)
		}
	}

	if len(r.Proposals) > 0 {
		fmt.Printf("\n  proposals:\n")
		for i, p := range r.Proposals {
			fmt.Printf("    %d. [%s] %s\n", i+1, strings.ToUpper(p.Action), strings.Join(p.Targets, " + "))
			fmt.Printf("       reason: %s\n", p.Reason)
			fmt.Printf("       entropy: %.2f → %.2f (−%.2f, −%.0f%%)\n",
				p.CurrentEntropy, p.PredictedEntropy, p.Reduction, p.ReductionPct)
		}
	}
}
