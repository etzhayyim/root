package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// domainAppReport holds per-app domain coverage metrics.
type domainAppReport struct {
	Project         string   `json:"project"`
	App             string   `json:"app"`
	Nanoid          string   `json:"nanoid"`
	DomainScore     int      `json:"domain_score"`
	Grade           string   `json:"grade"`
	Lines           int      `json:"lines"`
	SqlLabels    []string `json:"sql_labels"`
	CollectionKinds []string `json:"collection_kinds"`
	CustomCommands  []string `json:"custom_commands"`
	TemplateCmds    int      `json:"template_cmds"`
	BusinessRules   int      `json:"business_rules"`
	DataSources     int      `json:"data_sources"`
	DIDPaths        []string `json:"did_paths"`
	GovernanceUniq  bool     `json:"governance_unique"`
	HasWriterEntity bool     `json:"has_writer_entity"`
	Missing         []string `json:"missing,omitempty"`
}

var (
	reSqlLabel    = regexp.MustCompile(`(?:MATCH\s*\(\w:|Graph\(")(\w+)`)
	reCollectionKind = regexp.MustCompile(`ai\.gftd\.apps\.\w+\.(\w+)`)
	reTemplateCmds   = regexp.MustCompile(`function cmd_(?:list|get|search|create|wave|stats|export|describe|summarize|ingest|audit|health)_\w+|function cmd(?:Stats|ExportData|Describe|Summarize|Audit|Ingest|GetInfo|GetStatus)\b`)
	reCustomCmds     = regexp.MustCompile(`function cmd[A-Z]\w+|function cmd_[a-z]\w+`)
	reIfBranch       = regexp.MustCompile(`if\s*\(.+\)\s*\{`)
	reSwitchCase     = regexp.MustCompile(`\bswitch\b|\bcase\s+["']`)
	reTransform      = regexp.MustCompile(`\.map\(|\.filter\(|\.reduce\(|\.sort\(|\.forEach\(`)
	reRSSURL         = regexp.MustCompile(`https?://[^\s"]+\.(?:xml|rss|rdf|atom|json)`)
	reAPIURL         = regexp.MustCompile(`https?://(?:api\.|www\.)[^\s"]+`)
	reDIDPath        = regexp.MustCompile(`comAtprotoIdentityCreate\(\s*"([^"]+)"`)
	reWriterEntity   = regexp.MustCompile(`WriterEntity|writerDID|writer_did`)
	reDcInterface    = regexp.MustCompile(`(?m)^interface\s+\w+`)
	reConstArray     = regexp.MustCompile(`const\s+\w+(?:\s*:\s*\w+\[\])?\s*=\s*\[`)
	reNewMap         = regexp.MustCompile(`new Map`)

	genericLabels = map[string]bool{"Record": true, "n": true, "Entity": true}
	genericKinds  = map[string]bool{"record": true}
	defaultGov    = `{"raci":"responsible","classification":"internal","complianceFrameworks":[]}`
)

// collectAndScoreDomainApps walks all app.ts files and returns per-app domain reports.
// Single walk, shared by checkDomainCoverage and gftd kaizen.
func collectAndScoreDomainApps(wsRoot string) []domainAppReport {
	projectsDir := filepath.Join(wsRoot, "60-apps")
	if _, err := os.Stat(projectsDir); err != nil {
		// fallback: legacy "projects/" path
		projectsDir = filepath.Join(wsRoot, "projects")
		if _, err2 := os.Stat(projectsDir); err2 != nil {
			return nil
		}
	}

	var apps []domainAppReport
	_ = filepath.WalkDir(projectsDir, func(path string, d os.DirEntry, err error) error {
		if err != nil || d.IsDir() {
			return nil
		}
		if d.Name() != "app.ts" || !strings.Contains(path, "/src/app.ts") {
			return nil
		}

		appDir := filepath.Dir(filepath.Dir(path))
		dirname := filepath.Base(appDir)

		// Infer project name
		project := ""
		for _, seg := range strings.Split(appDir, string(os.PathSeparator)) {
			if strings.HasPrefix(seg, "ai-gftd-project-") {
				project = strings.TrimPrefix(seg, "ai-gftd-project-")
				break
			}
		}

		data, readErr := os.ReadFile(path)
		if readErr != nil {
			return nil
		}
		content := string(data)
		lines := len(strings.Split(strings.TrimSpace(content), "\n"))

		// --- Sql labels (unique, non-generic) ---
		labelMatches := reSqlLabel.FindAllStringSubmatch(content, -1)
		labelSet := map[string]bool{}
		for _, m := range labelMatches {
			if !genericLabels[m[1]] {
				labelSet[m[1]] = true
			}
		}
		var labels []string
		for l := range labelSet {
			labels = append(labels, l)
		}

		// --- Collection kinds (non-generic) ---
		kindMatches := reCollectionKind.FindAllStringSubmatch(content, -1)
		kindSet := map[string]bool{}
		for _, m := range kindMatches {
			if !genericKinds[m[1]] {
				kindSet[m[1]] = true
			}
		}
		var kinds []string
		for k := range kindSet {
			kinds = append(kinds, k)
		}

		// --- Commands: template vs custom ---
		templateCmds := reTemplateCmds.FindAllString(content, -1)
		allCmds := reCustomCmds.FindAllString(content, -1)
		templateSet := map[string]bool{}
		for _, c := range templateCmds {
			templateSet[c] = true
		}
		var customCmds []string
		for _, c := range allCmds {
			if !templateSet[c] {
				customCmds = append(customCmds, c)
			}
		}

		// --- Business rules ---
		businessRules := len(reIfBranch.FindAllString(content, -1))
		if reSwitchCase.MatchString(content) {
			businessRules += 5
		}
		businessRules += len(reTransform.FindAllString(content, -1))

		// --- Data sources ---
		dataSources := len(reRSSURL.FindAllString(content, -1))
		dataSources += len(reAPIURL.FindAllString(content, -1))

		// --- DID paths ---
		didMatches := reDIDPath.FindAllStringSubmatch(content, -1)
		var didPaths []string
		for _, m := range didMatches {
			didPaths = append(didPaths, m[1])
		}

		// --- Governance uniqueness ---
		govUniq := false
		jsonldPath := filepath.Join(appDir, "magatama.jsonld")
		nanoid := ""
		if jsonData, err := os.ReadFile(jsonldPath); err == nil {
			var jd map[string]interface{}
			if json.Unmarshal(jsonData, &jd) == nil {
				if n, ok := jd["nanoid"].(string); ok {
					nanoid = n
				}
				if gov, ok := jd["governance"]; ok {
					govJSON, _ := json.Marshal(gov)
					govUniq = string(govJSON) != defaultGov
				}
			}
		}

		// --- Writer entity ---
		hasWriter := reWriterEntity.MatchString(content)

		// --- Interfaces & data structures ---
		customInterfaces := len(reDcInterface.FindAllString(content, -1))
		constArrays := len(reConstArray.FindAllString(content, -1))
		constMaps := len(reNewMap.FindAllString(content, -1))

		// === Domain Score (0-100) ===
		score := 0
		// Graph model (30 pts max)
		score += min(len(labels)*10, 30)
		// Collection kinds (20 pts max)
		score += min(len(kinds)*10, 20)
		// Custom commands (15 pts max)
		score += min(len(customCmds)*5, 15)
		// Business logic depth (15 pts max)
		score += min(businessRules, 15)
		// Data structures (10 pts max)
		score += min((customInterfaces+constArrays+constMaps)*3, 10)
		// External data sources (5 pts max)
		score += min(dataSources*3, 5)
		// Governance specificity (5 pts)
		if govUniq {
			score += 5
		}
		// DID paths (5 pts max)
		score += min(len(didPaths)*3, 5)
		// Writer entity (3 pts)
		if hasWriter {
			score += 3
		}

		// Penalty: template-only (no custom commands, no custom labels)
		if len(customCmds) == 0 && len(labels) == 0 && len(kinds) == 0 {
			score = max(score-20, 0)
		}
		if score > 100 {
			score = 100
		}

		// Grade
		grade := "F"
		switch {
		case score >= 70:
			grade = "S"
		case score >= 50:
			grade = "A"
		case score >= 30:
			grade = "B"
		case score >= 15:
			grade = "C"
		default:
			grade = "D"
		}

		// Missing features
		var missing []string
		if len(labels) == 0 {
			missing = append(missing, "graph_labels")
		}
		if len(kinds) == 0 {
			missing = append(missing, "collection_kinds")
		}
		if len(customCmds) == 0 {
			missing = append(missing, "custom_commands")
		}
		if !govUniq {
			missing = append(missing, "governance")
		}
		if businessRules < 5 {
			missing = append(missing, "business_rules")
		}

		apps = append(apps, domainAppReport{
			Project:         project,
			App:             dirname,
			Nanoid:          nanoid,
			DomainScore:     score,
			Grade:           grade,
			Lines:           lines,
			SqlLabels:    labels,
			CollectionKinds: kinds,
			CustomCommands:  customCmds,
			TemplateCmds:    len(templateCmds),
			BusinessRules:   businessRules,
			DataSources:     dataSources,
			DIDPaths:        didPaths,
			GovernanceUniq:  govUniq,
			HasWriterEntity: hasWriter,
			Missing:         missing,
		})
		return nil
	})

	return apps
}

func checkDomainCoverage(wsRoot string) codeQualityCheck {
	check := codeQualityCheck{
		Name:      "domain_coverage",
		Tool:      "domain-coverage (built-in)",
		Available: true,
	}

	apps := collectAndScoreDomainApps(wsRoot)
	if len(apps) == 0 {
		check.Score = 100
		check.Details = "no apps found"
		return check
	}

	totalScore := 0
	gradeCount := map[string]int{}
	withLabels, withKinds, withCustom, withGov := 0, 0, 0, 0
	for _, a := range apps {
		totalScore += a.DomainScore
		gradeCount[a.Grade]++
		if len(a.SqlLabels) > 0 {
			withLabels++
		}
		if len(a.CollectionKinds) > 0 {
			withKinds++
		}
		if len(a.CustomCommands) > 0 {
			withCustom++
		}
		if a.GovernanceUniq {
			withGov++
		}
	}

	avgScore := float64(totalScore) / float64(len(apps))
	check.Score = cqCap(avgScore)
	check.Issues = len(apps) - gradeCount["S"] - gradeCount["A"]
	check.Details = fmt.Sprintf("%d apps, avg=%.1f, S:%d A:%d B:%d C:%d D:%d | labels:%d/%d kinds:%d/%d custom_cmds:%d/%d gov_unique:%d/%d",
		len(apps), avgScore,
		gradeCount["S"], gradeCount["A"], gradeCount["B"], gradeCount["C"], gradeCount["D"],
		withLabels, len(apps), withKinds, len(apps), withCustom, len(apps), withGov, len(apps))
	return check
}
