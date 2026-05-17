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

// --- Bottleneck types ---

// bottleneckModule represents a module's information bottleneck analysis.
type bottleneckModule struct {
	App             string         `json:"app"`
	FanIn           int            `json:"fan_in"`
	FanOut          int            `json:"fan_out"`
	BottleneckScore float64        `json:"bottleneck_score"`
	InboundApps     []string       `json:"inbound_apps"`
	OutboundApps    []string       `json:"outbound_apps"`
	InboundTypes    map[string]int `json:"inbound_types"`
	OutboundTypes   map[string]int `json:"outbound_types"`
	MutualInfo      float64        `json:"mutual_information"`
	Severity        string         `json:"severity"`
}

// bottleneckReport is the full information bottleneck analysis output.
type bottleneckReport struct {
	GeneratedAt string             `json:"generated_at"`
	TotalApps   int                `json:"total_apps"`
	Bottlenecks []bottleneckModule `json:"bottlenecks"`
	SystemMI    float64            `json:"system_mutual_information"`
	Score       float64            `json:"score"`
}

// --- Bottleneck entry point ---

func runShannonBottleneck(args []string) error {
	fs := flag.NewFlagSet("shannon bottleneck", flag.ContinueOnError)
	workspaceDir := fs.String("workspace-dir", "", "workspace root (default: git root)")
	jsonOut := fs.Bool("json", false, "output as JSON")
	topN := fs.Int("top", 15, "number of bottlenecks to show")
	minFan := fs.Int("min-fan", 2, "minimum fan-in or fan-out to consider")
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
	report := buildBottleneckReport(graph, *topN, *minFan)

	if *jsonOut {
		enc := json.NewEncoder(os.Stdout)
		enc.SetIndent("", "  ")
		return enc.Encode(report)
	}

	printBottleneckText(report)
	return nil
}

func buildBottleneckReport(g haisenGraph, topN, minFan int) *bottleneckReport {
	apps, adjTyped := shBuildAdjacencyTyped(g)
	n := len(apps)

	if n == 0 {
		return &bottleneckReport{
			GeneratedAt: time.Now().UTC().Format(time.RFC3339),
			Score:       100,
		}
	}

	// Compute per-app fan-in, fan-out, and typed distributions
	type appStats struct {
		inboundApps  map[string]bool
		outboundApps map[string]bool
		inTypes      map[string]int
		outTypes     map[string]int
	}

	stats := make(map[string]*appStats)
	for _, a := range apps {
		stats[a] = &appStats{
			inboundApps:  make(map[string]bool),
			outboundApps: make(map[string]bool),
			inTypes:      make(map[string]int),
			outTypes:     make(map[string]int),
		}
	}

	for from, targets := range adjTyped {
		for to, types := range targets {
			if stats[from] != nil {
				stats[from].outboundApps[to] = true
				for t, c := range types {
					stats[from].outTypes[t] += c
				}
			}
			if stats[to] != nil {
				stats[to].inboundApps[from] = true
				for t, c := range types {
					stats[to].inTypes[t] += c
				}
			}
		}
	}

	// Find max fan for normalization
	maxFan := 1.0
	for _, s := range stats {
		fi := float64(len(s.inboundApps))
		fo := float64(len(s.outboundApps))
		if fi > maxFan {
			maxFan = fi
		}
		if fo > maxFan {
			maxFan = fo
		}
	}

	// Build bottleneck modules
	var modules []bottleneckModule
	criticalHighCount := 0

	for _, app := range apps {
		s := stats[app]
		fanIn := len(s.inboundApps)
		fanOut := len(s.outboundApps)

		if fanIn < minFan && fanOut < minFan {
			continue
		}

		// Bottleneck score = geometric mean of fan-in and fan-out, normalized
		bScore := math.Sqrt(float64(fanIn)*float64(fanOut)) / maxFan
		if bScore > 1.0 {
			bScore = 1.0
		}

		// Mutual information approximation: MI ≈ H(in) + H(out) - H(in,out)
		hIn := shEntropy(s.inTypes)
		hOut := shEntropy(s.outTypes)
		// Joint: combine in and out type distributions with prefix
		joint := make(map[string]int)
		for t, c := range s.inTypes {
			joint["in:"+t] += c
		}
		for t, c := range s.outTypes {
			joint["out:"+t] += c
		}
		hJoint := shEntropy(joint)
		mi := hIn + hOut - hJoint
		if mi < 0 {
			mi = 0
		}

		// Severity classification
		severity := "low"
		if bScore >= 0.7 && fanIn >= 5 && fanOut >= 5 {
			severity = "critical"
		} else if bScore >= 0.5 {
			severity = "high"
		} else if bScore >= 0.3 {
			severity = "medium"
		}

		if severity == "critical" || severity == "high" {
			criticalHighCount++
		}

		inApps := make([]string, 0, len(s.inboundApps))
		for a := range s.inboundApps {
			inApps = append(inApps, a)
		}
		sort.Strings(inApps)

		outApps := make([]string, 0, len(s.outboundApps))
		for a := range s.outboundApps {
			outApps = append(outApps, a)
		}
		sort.Strings(outApps)

		modules = append(modules, bottleneckModule{
			App:             app,
			FanIn:           fanIn,
			FanOut:          fanOut,
			BottleneckScore: bScore,
			InboundApps:     inApps,
			OutboundApps:    outApps,
			InboundTypes:    s.inTypes,
			OutboundTypes:   s.outTypes,
			MutualInfo:      mi,
			Severity:        severity,
		})
	}

	// Sort by bottleneck score descending
	sort.Slice(modules, func(i, j int) bool {
		return modules[i].BottleneckScore > modules[j].BottleneckScore
	})
	if len(modules) > topN {
		modules = modules[:topN]
	}

	// System MI = sum of all module MI
	systemMI := 0.0
	for _, m := range modules {
		systemMI += m.MutualInfo
	}

	// Score: fewer critical/high bottlenecks = better
	score := 100.0
	if n > 0 {
		score = 100.0 * (1.0 - float64(criticalHighCount)/float64(n))
	}
	if score < 0 {
		score = 0
	}

	return &bottleneckReport{
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		TotalApps:   n,
		Bottlenecks: modules,
		SystemMI:    systemMI,
		Score:       score,
	}
}

func printBottleneckText(r *bottleneckReport) {
	fmt.Printf("shannon bottleneck:\n")
	fmt.Printf("  generated_at: %s\n", r.GeneratedAt)
	fmt.Printf("  total_apps: %d\n", r.TotalApps)
	fmt.Printf("  system_mi: %.3f bits\n", r.SystemMI)
	fmt.Printf("  score: %.1f\n", r.Score)

	if len(r.Bottlenecks) > 0 {
		fmt.Printf("\n  bottlenecks:\n")
		for _, b := range r.Bottlenecks {
			severityBadge := strings.ToUpper(b.Severity)
			fmt.Printf("    [%s] %s (score=%.2f, fan_in=%d, fan_out=%d, MI=%.3f)\n",
				severityBadge, b.App, b.BottleneckScore, b.FanIn, b.FanOut, b.MutualInfo)
			if len(b.InboundApps) <= 5 {
				fmt.Printf("      inbound: %s\n", strings.Join(b.InboundApps, ", "))
			} else {
				fmt.Printf("      inbound: %s ... (+%d)\n",
					strings.Join(b.InboundApps[:5], ", "), len(b.InboundApps)-5)
			}
			if len(b.OutboundApps) <= 5 {
				fmt.Printf("      outbound: %s\n", strings.Join(b.OutboundApps, ", "))
			} else {
				fmt.Printf("      outbound: %s ... (+%d)\n",
					strings.Join(b.OutboundApps[:5], ", "), len(b.OutboundApps)-5)
			}
		}
	}
}
