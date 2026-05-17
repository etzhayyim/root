package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var docsValidateNow = func() string { return "2026-03-20" }

type docsRegistry struct {
	Version   int                 `json:"version"`
	UpdatedAt string              `json:"updated_at"`
	Entries   []docsRegistryEntry `json:"entries"`
}

type docsRegistryEntry struct {
	ID               string   `json:"id"`
	Path             string   `json:"path"`
	Title            string   `json:"title"`
	Status           string   `json:"status"`
	DocType          string   `json:"doc_type"`
	Topic            string   `json:"topic"`
	Authoritative    bool     `json:"authoritative"`
	AuthoritativeFor []string `json:"authoritative_for"`
}

type docsGraph struct {
	Context map[string]any  `json:"@context"`
	Graph   []docsGraphNode `json:"@graph"`
}

type docsGraphNode struct {
	ID               string   `json:"id"`
	Type             string   `json:"type"`
	Title            string   `json:"title"`
	Status           string   `json:"status"`
	Topic            string   `json:"topic"`
	Authoritative    bool     `json:"authoritative"`
	AuthoritativeFor []string `json:"authoritativeFor"`
	Related          []string `json:"related"`
	Supersedes       []string `json:"supersedes"`
	SupersededBy     []string `json:"supersededBy"`
}

func runDocs(args []string) error {
	if len(args) == 0 {
		return errors.New("usage: gftd docs <validate>")
	}
	switch args[0] {
	case "validate":
		return runDocsValidate(args[1:])
	default:
		return fmt.Errorf("unknown docs subcommand: %s", args[0])
	}
}

func runDocsValidate(args []string) error {
	repoRoot, err := findGitRoot(".")
	if err != nil {
		return err
	}
	if len(args) > 0 {
		return fmt.Errorf("usage: gftd docs validate")
	}
	return validateDocsRegistry(repoRoot)
}

func validateDocsRegistry(repoRoot string) error {
	docsDir := filepath.Join(repoRoot, "docs")
	registryPath := filepath.Join(docsDir, "_registry", "docs.json")
	graphPath := filepath.Join(docsDir, "_registry", "graph.jsonld")
	requiredPaths := []string{
		registryPath,
		graphPath,
		filepath.Join(docsDir, "_registry", "schemas", "docs.schema.json"),
		filepath.Join(docsDir, "_registry", "schemas", "graph.schema.json"),
	}

	var errs []string
	for _, path := range requiredPaths {
		if _, err := os.Stat(path); err != nil {
			errs = append(errs, fmt.Sprintf("required file missing: %s", relPath(repoRoot, path)))
		}
	}
	if len(errs) > 0 {
		return docsValidationError(errs)
	}

	registry, err := readDocsRegistry(registryPath)
	if err != nil {
		return err
	}
	graph, err := readDocsGraph(graphPath)
	if err != nil {
		return err
	}

	byID := validateDocsRegistryShape(repoRoot, registry, &errs)
	validateDocsFrontMatter(repoRoot, byID, &errs)
	validateDocsGraph(byID, graph, &errs)

	if len(errs) > 0 {
		return docsValidationError(errs)
	}

	fmt.Println("docs registry validation passed")
	return nil
}

func readDocsRegistry(path string) (docsRegistry, error) {
	var registry docsRegistry
	data, err := os.ReadFile(path)
	if err != nil {
		return registry, fmt.Errorf("read docs registry: %w", err)
	}
	if err := json.Unmarshal(data, &registry); err != nil {
		return registry, fmt.Errorf("parse docs registry: %w", err)
	}
	return registry, nil
}

func readDocsGraph(path string) (docsGraph, error) {
	var graph docsGraph
	data, err := os.ReadFile(path)
	if err != nil {
		return graph, fmt.Errorf("read docs graph: %w", err)
	}
	if err := json.Unmarshal(data, &graph); err != nil {
		return graph, fmt.Errorf("parse docs graph: %w", err)
	}
	return graph, nil
}

func validateDocsRegistryShape(repoRoot string, registry docsRegistry, errs *[]string) map[string]docsRegistryEntry {
	if registry.Version < 1 {
		*errs = append(*errs, "docs registry version must be >= 1")
	}
	if !isDate(registry.UpdatedAt) {
		*errs = append(*errs, fmt.Sprintf("docs registry updated_at has invalid format: %q", registry.UpdatedAt))
	}

	allowedStatus := map[string]struct{}{"active": {}, "deprecated": {}, "superseded": {}, "proposed": {}}
	allowedDocTypes := map[string]struct{}{"explanation": {}, "reference": {}, "how-to": {}, "tutorial": {}, "adr": {}}

	byID := make(map[string]docsRegistryEntry, len(registry.Entries))
	authoritativeTopics := map[string]string{}
	for _, entry := range registry.Entries {
		if entry.ID == "" {
			*errs = append(*errs, "registry entry has empty id")
			continue
		}
		if _, exists := byID[entry.ID]; exists {
			*errs = append(*errs, fmt.Sprintf("duplicate registry id: %s", entry.ID))
			continue
		}
		byID[entry.ID] = entry

		if entry.Path == "" || !strings.HasSuffix(entry.Path, ".md") {
			*errs = append(*errs, fmt.Sprintf("registry entry %s has invalid path: %s", entry.ID, entry.Path))
		} else if _, err := os.Stat(filepath.Join(repoRoot, entry.Path)); err != nil {
			*errs = append(*errs, fmt.Sprintf("registry entry %s points to missing file: %s", entry.ID, entry.Path))
		}

		if entry.Title == "" {
			*errs = append(*errs, fmt.Sprintf("registry entry %s has empty title", entry.ID))
		}
		if _, ok := allowedStatus[entry.Status]; !ok {
			*errs = append(*errs, fmt.Sprintf("registry entry %s has invalid status: %s", entry.ID, entry.Status))
		}
		if _, ok := allowedDocTypes[entry.DocType]; !ok {
			*errs = append(*errs, fmt.Sprintf("registry entry %s has invalid doc_type: %s", entry.ID, entry.DocType))
		}
		if entry.Topic == "" {
			*errs = append(*errs, fmt.Sprintf("registry entry %s has empty topic", entry.ID))
		}
		if entry.Authoritative {
			if prev, exists := authoritativeTopics[entry.Topic]; exists {
				*errs = append(*errs, fmt.Sprintf("topic %q has more than one authoritative doc: %s, %s", entry.Topic, prev, entry.ID))
			} else {
				authoritativeTopics[entry.Topic] = entry.ID
			}
		}
	}
	return byID
}

func validateDocsFrontMatter(repoRoot string, byID map[string]docsRegistryEntry, errs *[]string) {
	for _, entry := range byID {
		path := filepath.Join(repoRoot, entry.Path)
		fm, err := parseFrontMatter(path)
		if err != nil {
			*errs = append(*errs, fmt.Sprintf("%s: %v", entry.Path, err))
			continue
		}

		required := []string{"id", "title", "status", "doc_type", "topic", "authoritative", "last_verified"}
		for _, key := range required {
			if _, ok := fm[key]; !ok {
				*errs = append(*errs, fmt.Sprintf("%s: missing front matter key %q", entry.Path, key))
			}
		}

		matchFrontMatterValue(entry.Path, "id", fm["id"], entry.ID, errs)
		matchFrontMatterValue(entry.Path, "title", fm["title"], entry.Title, errs)
		matchFrontMatterValue(entry.Path, "status", fm["status"], entry.Status, errs)
		matchFrontMatterValue(entry.Path, "doc_type", fm["doc_type"], entry.DocType, errs)
		matchFrontMatterValue(entry.Path, "topic", fm["topic"], entry.Topic, errs)
		matchFrontMatterValue(entry.Path, "authoritative", fm["authoritative"], entry.Authoritative, errs)

		lastVerified, _ := fm["last_verified"].(string)
		if !isDate(lastVerified) {
			*errs = append(*errs, fmt.Sprintf("%s: front matter last_verified has invalid format: %v", entry.Path, fm["last_verified"]))
		}

		if !equalStringSlices(asStringSlice(fm["authoritative_for"]), entry.AuthoritativeFor) {
			*errs = append(*errs, fmt.Sprintf("%s: front matter authoritative_for does not match registry", entry.Path))
		}
	}
}

func validateDocsGraph(byID map[string]docsRegistryEntry, graph docsGraph, errs *[]string) {
	if graph.Context == nil {
		*errs = append(*errs, "graph.jsonld missing @context")
	}
	graphByID := make(map[string]docsGraphNode, len(graph.Graph))
	expectedNodeIDs := make(map[string]struct{}, len(byID))
	for id := range byID {
		expectedNodeIDs["doc:"+id] = struct{}{}
	}

	for _, node := range graph.Graph {
		if !strings.HasPrefix(node.ID, "doc:") {
			*errs = append(*errs, fmt.Sprintf("graph node has invalid id: %s", node.ID))
			continue
		}
		if _, exists := graphByID[node.ID]; exists {
			*errs = append(*errs, fmt.Sprintf("duplicate graph node id: %s", node.ID))
			continue
		}
		graphByID[node.ID] = node
		docID := strings.TrimPrefix(node.ID, "doc:")
		entry, ok := byID[docID]
		if !ok {
			*errs = append(*errs, fmt.Sprintf("graph node %s has no matching registry entry", node.ID))
			continue
		}
		if node.Title != entry.Title {
			*errs = append(*errs, fmt.Sprintf("graph node %s title does not match registry", node.ID))
		}
		if node.Status != entry.Status {
			*errs = append(*errs, fmt.Sprintf("graph node %s status does not match registry", node.ID))
		}
		if node.Topic != entry.Topic {
			*errs = append(*errs, fmt.Sprintf("graph node %s topic does not match registry", node.ID))
		}
		if node.Authoritative != entry.Authoritative {
			*errs = append(*errs, fmt.Sprintf("graph node %s authoritative does not match registry", node.ID))
		}
		if !equalStringSlices(node.AuthoritativeFor, entry.AuthoritativeFor) {
			*errs = append(*errs, fmt.Sprintf("graph node %s authoritativeFor does not match registry", node.ID))
		}
		validateGraphRefs(node.ID, "related", node.Related, expectedNodeIDs, errs)
		validateGraphRefs(node.ID, "supersedes", node.Supersedes, expectedNodeIDs, errs)
		validateGraphRefs(node.ID, "supersededBy", node.SupersededBy, expectedNodeIDs, errs)
	}

	for id := range expectedNodeIDs {
		if _, ok := graphByID[id]; !ok {
			*errs = append(*errs, fmt.Sprintf("registry entry missing graph node: %s", id))
		}
	}
}

func validateGraphRefs(nodeID, field string, refs []string, expected map[string]struct{}, errs *[]string) {
	for _, ref := range refs {
		if _, ok := expected[ref]; !ok {
			*errs = append(*errs, fmt.Sprintf("graph node %s %s references unknown target %s", nodeID, field, ref))
		}
	}
}

func parseFrontMatter(path string) (map[string]any, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, fmt.Errorf("read front matter: %w", err)
	}
	lines := strings.Split(string(data), "\n")
	if len(lines) == 0 || strings.TrimSpace(lines[0]) != "---" {
		return nil, errors.New("missing YAML front matter opening delimiter")
	}
	end := -1
	for i := 1; i < len(lines); i++ {
		if strings.TrimSpace(lines[i]) == "---" {
			end = i
			break
		}
	}
	if end == -1 {
		return nil, errors.New("missing YAML front matter closing delimiter")
	}

	result := map[string]any{}
	for i := 1; i < end; {
		line := lines[i]
		trimmed := strings.TrimSpace(line)
		if trimmed == "" {
			i++
			continue
		}
		if strings.HasPrefix(trimmed, "- ") {
			return nil, fmt.Errorf("unexpected list item without key: %s", trimmed)
		}
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			return nil, fmt.Errorf("invalid front matter line: %s", trimmed)
		}
		key := strings.TrimSpace(parts[0])
		raw := strings.TrimSpace(parts[1])
		if raw != "" {
			result[key] = parseFrontMatterScalar(raw)
			i++
			continue
		}
		var list []string
		i++
		for i < end {
			child := lines[i]
			childTrimmed := strings.TrimSpace(child)
			if childTrimmed == "" {
				i++
				continue
			}
			if !strings.HasPrefix(child, "  - ") {
				break
			}
			list = append(list, strings.TrimSpace(strings.TrimPrefix(child, "  - ")))
			i++
		}
		result[key] = list
	}
	return result, nil
}

func parseFrontMatterScalar(raw string) any {
	switch raw {
	case "true":
		return true
	case "false":
		return false
	case "[]":
		return []string{}
	}
	if len(raw) >= 2 {
		if (raw[0] == '"' && raw[len(raw)-1] == '"') || (raw[0] == '\'' && raw[len(raw)-1] == '\'') {
			return raw[1 : len(raw)-1]
		}
	}
	return raw
}

func matchFrontMatterValue(path, key string, got any, want any, errs *[]string) {
	if got != want {
		*errs = append(*errs, fmt.Sprintf("%s: front matter %q=%v does not match registry value %v", path, key, got, want))
	}
}

func asStringSlice(v any) []string {
	items, ok := v.([]string)
	if ok {
		return items
	}
	if raw, ok := v.([]any); ok {
		out := make([]string, 0, len(raw))
		for _, item := range raw {
			if s, ok := item.(string); ok {
				out = append(out, s)
			}
		}
		return out
	}
	return nil
}

func equalStringSlices(a, b []string) bool {
	if len(a) != len(b) {
		return false
	}
	for i := range a {
		if a[i] != b[i] {
			return false
		}
	}
	return true
}

func isDate(v string) bool {
	if len(v) != len("2006-01-02") {
		return false
	}
	for i, r := range v {
		switch i {
		case 4, 7:
			if r != '-' {
				return false
			}
		default:
			if r < '0' || r > '9' {
				return false
			}
		}
	}
	return true
}

func docsValidationError(errs []string) error {
	sort.Strings(errs)
	return errors.New(strings.Join(errs, "\n"))
}

func relPath(root, target string) string {
	rel, err := filepath.Rel(root, target)
	if err != nil {
		return target
	}
	return rel
}
