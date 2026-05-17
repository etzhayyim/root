package main

import (
	"encoding/json"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// --- Layer 1: WIT + magatama.jsonld metadata extraction ---

// sgMetaResult holds metadata extracted from WIT and magatama.jsonld.
type sgMetaResult struct {
	// From magatama.jsonld
	DID           string   `json:"did"`
	PerformerType string   `json:"performer_type"`
	Name          string   `json:"name"`
	NanoID        string   `json:"nanoid"`
	UIType        string   `json:"ui_type"`
	RuntimeType   string   `json:"runtime_type"`
	Sensitivity   string   `json:"sensitivity,omitempty"`
	Collections   []string `json:"collections,omitempty"`   // triggers.subscribeRepos.collections
	Requires      []string `json:"requires,omitempty"`      // interfaces.requires
	GuestLanguage string   `json:"guest_language,omitempty"`
	DisplayName   string   `json:"display_name,omitempty"`
	Description   string   `json:"description,omitempty"`

	// From world.wit
	WITPackage string   `json:"wit_package,omitempty"`
	WITImports []string `json:"wit_imports,omitempty"`
	WITExports []string `json:"wit_exports,omitempty"`
	WITInclude []string `json:"wit_include,omitempty"`
}

// --- magatama.jsonld parsing (reuses magatamaJSONLD from deploy.go) ---

func sgParseJSONLD(path string) sgMetaResult {
	var result sgMetaResult

	data, err := os.ReadFile(path)
	if err != nil {
		return result
	}

	var jld magatamaJSONLD
	if err := json.Unmarshal(data, &jld); err != nil {
		return result
	}

	result.DID = jld.ID
	result.PerformerType = jld.PerformerType
	result.Name = jld.Name
	result.NanoID = jld.Nanoid
	result.UIType = jld.UIType
	result.RuntimeType = jld.RuntimeType

	if jld.Triggers != nil && jld.Triggers.SubscribeRepos != nil {
		result.Collections = jld.Triggers.SubscribeRepos.Collections
	}
	if jld.Interfaces != nil {
		for _, r := range jld.Interfaces.Requires {
			if s, ok := r.(string); ok {
				result.Requires = append(result.Requires, s)
			}
		}
	}
	if jld.Build != nil {
		result.GuestLanguage = jld.Build.GuestLanguage
	}
	if jld.Profile != nil {
		result.DisplayName = jld.Profile.DisplayName
		result.Description = jld.Profile.Description
	}

	return result
}

// --- WIT world.wit parsing ---

var (
	witImportRe    = regexp.MustCompile(`(?m)^\s*import\s+(\S+)`)
	witExportRe    = regexp.MustCompile(`(?m)^\s*export\s+(\S+)`)
	sgWITPackageRe = regexp.MustCompile(`^\s*package\s+([\w:/-]+)`)
	sgWITIncludeRe = regexp.MustCompile(`^\s*include\s+([\w:/@.-]+)`)
)

func sgParseWIT(path string) sgMetaResult {
	var result sgMetaResult

	data, err := os.ReadFile(path)
	if err != nil {
		return result
	}

	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)

		if strings.HasPrefix(line, "//") || strings.HasPrefix(line, "/*") {
			continue
		}

		if m := sgWITPackageRe.FindStringSubmatch(line); m != nil {
			result.WITPackage = strings.TrimSuffix(m[1], ";")
		}
		if m := witImportRe.FindStringSubmatch(line); m != nil {
			result.WITImports = append(result.WITImports, strings.TrimSuffix(m[1], ";"))
		}
		if m := witExportRe.FindStringSubmatch(line); m != nil {
			result.WITExports = append(result.WITExports, strings.TrimSuffix(m[1], ";"))
		}
		if m := sgWITIncludeRe.FindStringSubmatch(line); m != nil {
			result.WITInclude = append(result.WITInclude, strings.TrimSuffix(m[1], ";"))
		}
	}

	return result
}

// --- Discovery: find magatama.jsonld and world.wit for a given source file ---

func sgFindMeta(wsRoot, relPath string) (jsonldPath, witPath string) {
	dir := filepath.Dir(filepath.Join(wsRoot, relPath))

	for {
		jPath := filepath.Join(dir, "magatama.jsonld")
		if _, err := os.Stat(jPath); err == nil {
			jsonldPath = jPath
		}

		wPath := filepath.Join(dir, "wit", "world.wit")
		if _, err := os.Stat(wPath); err == nil {
			witPath = wPath
		}

		if jsonldPath != "" || witPath != "" {
			return
		}

		parent := filepath.Dir(dir)
		if parent == dir || !strings.HasPrefix(parent, wsRoot) {
			break
		}
		dir = parent
	}
	return
}

// sgMergeMetaIntoNode merges Layer 1 metadata into a source node.
func sgMergeMetaIntoNode(node *sgSourceNode, meta sgMetaResult) {
	if node.AppDID == "" && meta.DID != "" {
		node.AppDID = meta.DID
	}
	if node.Sensitivity == "" && meta.Sensitivity != "" {
		node.Sensitivity = meta.Sensitivity
	}

	// WIT imports as dependencies
	for _, imp := range meta.WITImports {
		node.Imports = sgMergeStrings(node.Imports, []string{imp})
	}

	// subscribeRepos collections as reads (the app reacts to these)
	for _, coll := range meta.Collections {
		node.Reads = sgMergeStrings(node.Reads, []string{"subscribeRepos:" + coll})
	}

	// interfaces.requires as imports
	for _, req := range meta.Requires {
		node.Imports = sgMergeStrings(node.Imports, []string{req})
	}
}

// sgScanAppMeta scans all magatama.jsonld files in the workspace.
func sgScanAppMeta(wsRoot string) map[string]sgMetaResult {
	results := make(map[string]sgMetaResult)

	projectsDir := filepath.Join(wsRoot, "60-apps")
	projEntries, _ := os.ReadDir(projectsDir)
	for _, pe := range projEntries {
		if !pe.IsDir() || !strings.HasPrefix(pe.Name(), "ai-gftd-project-") {
			continue
		}
		wasmDir := filepath.Join(projectsDir, pe.Name(), "wasm")
		wasmEntries, err := os.ReadDir(wasmDir)
		if err != nil {
			continue
		}
		for _, we := range wasmEntries {
			if !we.IsDir() {
				continue
			}
			appDir := filepath.Join(wasmDir, we.Name())

			jPath := filepath.Join(appDir, "magatama.jsonld")
			wPath := filepath.Join(appDir, "wit", "world.wit")

			var meta sgMetaResult

			if _, err := os.Stat(jPath); err == nil {
				meta = sgParseJSONLD(jPath)
			}
			if _, err := os.Stat(wPath); err == nil {
				witMeta := sgParseWIT(wPath)
				meta.WITPackage = witMeta.WITPackage
				meta.WITImports = witMeta.WITImports
				meta.WITExports = witMeta.WITExports
				meta.WITInclude = witMeta.WITInclude
			}

			if meta.DID != "" || meta.WITPackage != "" {
				rel, _ := filepath.Rel(wsRoot, appDir)
				results[rel] = meta
			}
		}
	}

	return results
}
