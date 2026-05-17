// projector.go — gftd projector: project lifecycle + blocker tracking CLI.
//
// Uses the projector.* MCP tools / XRPC methods backed by:
//   - vertex_project_props (lifecycle_state, progress_permille)
//   - vertex_projector_blocker (per-project blockers)
//   - mv_projector_project_status (aggregated status MV)
//   - LangGraph projector_lifecycle graph (state transitions)
//   - Pregel BSP blocker propagation (dependency graph)
//
// Examples:
//
//	gftd projector create --name "Vultr A16 GPU deployment" --org default
//	gftd projector status --id proj:1234:abc
//	gftd projector update --id proj:1234:abc --progress 500 --state active
//	gftd projector blocker add --project proj:1234:abc --title "Vultr product gate" --type system
//	gftd projector blocker resolve --id blk:5678:def
//	gftd projector list --state blocked
package main

import (
	"bytes"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"strings"
)

const projectorMCPBase = "https://atproto.etzhayyim.com"

func runProjector(args []string) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: gftd projector <create|status|update|blocker|list> [flags]")
	}
	switch args[0] {
	case "create":
		return runProjectorCreate(args[1:])
	case "status", "get":
		return runProjectorStatus(args[1:])
	case "update":
		return runProjectorUpdate(args[1:])
	case "blocker":
		if len(args) < 2 {
			return fmt.Errorf("usage: gftd projector blocker <add|resolve> [flags]")
		}
		switch args[1] {
		case "add":
			return runProjectorBlockerAdd(args[2:])
		case "resolve":
			return runProjectorBlockerResolve(args[2:])
		default:
			return fmt.Errorf("unknown blocker subcommand: %s", args[1])
		}
	case "list":
		return runProjectorList(args[1:])
	default:
		return fmt.Errorf("unknown projector subcommand: %s\navailable: create, status, update, blocker add/resolve, list", args[0])
	}
}

func projectorMCPCall(toolName string, arguments map[string]any) (map[string]any, error) {
	payload := map[string]any{
		"jsonrpc": "2.0",
		"id":      1,
		"method":  "tools/call",
		"params": map[string]any{
			"name":      toolName,
			"arguments": arguments,
		},
	}
	body, err := json.Marshal(payload)
	if err != nil {
		return nil, err
	}

	req, err := http.NewRequest("POST", projectorMCPBase+"/mcp", bytes.NewReader(body))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Content-Type", "application/json")
	if tok := os.Getenv("GFTD_AGENT_TOKEN"); tok != "" {
		req.Header.Set("Authorization", "Bearer "+tok)
	}

	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return nil, fmt.Errorf("MCP request failed: %w", err)
	}
	defer resp.Body.Close()

	raw, err := io.ReadAll(resp.Body)
	if err != nil {
		return nil, err
	}

	var rpcResp map[string]any
	if err := json.Unmarshal(raw, &rpcResp); err != nil {
		return nil, fmt.Errorf("response parse error: %w\nraw: %s", err, string(raw))
	}

	if errVal, ok := rpcResp["error"]; ok {
		return nil, fmt.Errorf("MCP error: %v", errVal)
	}

	result, _ := rpcResp["result"].(map[string]any)
	if result == nil {
		return rpcResp, nil
	}

	// Unwrap content[0].text if present
	if content, ok := result["content"].([]any); ok && len(content) > 0 {
		if first, ok := content[0].(map[string]any); ok {
			if text, ok := first["text"].(string); ok {
				var inner map[string]any
				if json.Unmarshal([]byte(text), &inner) == nil {
					return inner, nil
				}
			}
		}
	}
	return result, nil
}

func printProjectorResult(result map[string]any) {
	out, _ := json.MarshalIndent(result, "", "  ")
	fmt.Println(string(out))
}

// ── create ──────────────────────────────────────────────────────────────────

func runProjectorCreate(args []string) error {
	fs := flag.NewFlagSet("projector create", flag.ContinueOnError)
	name := fs.String("name", "", "Project name (required)")
	description := fs.String("desc", "", "Project description")
	orgID := fs.String("org", "default", "org_id")
	parentID := fs.String("parent", "", "Parent project vertex_id")
	targetDate := fs.String("due", "", "Target date ISO 8601 (e.g. 2026-06-30)")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *name == "" {
		return fmt.Errorf("--name is required")
	}

	arguments := map[string]any{"name": *name, "orgId": *orgID}
	if *description != "" {
		arguments["description"] = *description
	}
	if *parentID != "" {
		arguments["parentId"] = *parentID
	}
	if *targetDate != "" {
		arguments["targetDate"] = *targetDate
	}

	result, err := projectorMCPCall("projector.create_project", arguments)
	if err != nil {
		return err
	}
	printProjectorResult(result)
	return nil
}

// ── status ───────────────────────────────────────────────────────────────────

func runProjectorStatus(args []string) error {
	fs := flag.NewFlagSet("projector status", flag.ContinueOnError)
	id := fs.String("id", "", "Project vertex_id (required)")
	summarize := fs.Bool("summarize", false, "Include LLM summary")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *id == "" && fs.NArg() > 0 {
		*id = fs.Arg(0)
	}
	if *id == "" {
		return fmt.Errorf("--id is required")
	}

	result, err := projectorMCPCall("projector.get_status", map[string]any{
		"projectId": *id,
		"summarize": *summarize,
	})
	if err != nil {
		return err
	}

	// Pretty-print key fields
	fmt.Printf("Project:  %s\n", result["name"])
	fmt.Printf("State:    %s\n", result["lifecycleState"])
	if pp, ok := result["progressPermille"].(float64); ok {
		fmt.Printf("Progress: %.1f%%\n", pp/10.0)
	}
	if obc, ok := result["openBlockerCount"].(float64); ok && obc > 0 {
		fmt.Printf("Blockers: %.0f open\n", obc)
	}
	if td, ok := result["targetDate"].(string); ok && td != "" {
		fmt.Printf("Due:      %s\n", td)
	}
	if sum, ok := result["summary"].(string); ok && sum != "" {
		fmt.Printf("Summary:  %s\n", sum)
	}
	return nil
}

// ── update ───────────────────────────────────────────────────────────────────

func runProjectorUpdate(args []string) error {
	fs := flag.NewFlagSet("projector update", flag.ContinueOnError)
	id := fs.String("id", "", "Project vertex_id (required)")
	progress := fs.Int("progress", -1, "Progress permille 0-1000")
	state := fs.String("state", "", "lifecycle_state: planning|active|blocked|done")
	targetDate := fs.String("due", "", "Target date ISO 8601")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *id == "" {
		return fmt.Errorf("--id is required")
	}

	arguments := map[string]any{"projectId": *id}
	if *progress >= 0 {
		arguments["progressPermille"] = *progress
	}
	if *state != "" {
		arguments["lifecycleState"] = *state
	}
	if *targetDate != "" {
		arguments["targetDate"] = *targetDate
	}

	result, err := projectorMCPCall("projector.update_status", arguments)
	if err != nil {
		return err
	}
	printProjectorResult(result)
	return nil
}

// ── blocker add ──────────────────────────────────────────────────────────────

func runProjectorBlockerAdd(args []string) error {
	fs := flag.NewFlagSet("projector blocker add", flag.ContinueOnError)
	project := fs.String("project", "", "Project vertex_id (required)")
	title := fs.String("title", "", "Blocker title (required)")
	description := fs.String("desc", "", "Blocker description")
	blockerType := fs.String("type", "technical", "Blocker type: financial|personnel|approval|system|external|technical")
	severity := fs.String("severity", "medium", "Severity: low|medium|high|critical")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *project == "" || *title == "" {
		return fmt.Errorf("--project and --title are required")
	}

	arguments := map[string]any{
		"projectId":   *project,
		"title":       *title,
		"blockerType": *blockerType,
		"severity":    *severity,
	}
	if *description != "" {
		arguments["description"] = *description
	}

	result, err := projectorMCPCall("projector.add_blocker", arguments)
	if err != nil {
		return err
	}
	printProjectorResult(result)
	return nil
}

// ── blocker resolve ───────────────────────────────────────────────────────────

func runProjectorBlockerResolve(args []string) error {
	fs := flag.NewFlagSet("projector blocker resolve", flag.ContinueOnError)
	id := fs.String("id", "", "Blocker vertex_id (required)")
	resolution := fs.String("resolution", "", "How the blocker was resolved")
	if err := fs.Parse(args); err != nil {
		return err
	}
	if *id == "" && fs.NArg() > 0 {
		*id = fs.Arg(0)
	}
	if *id == "" {
		return fmt.Errorf("--id is required")
	}

	arguments := map[string]any{"blockerId": *id}
	if *resolution != "" {
		arguments["resolution"] = *resolution
	}

	result, err := projectorMCPCall("projector.resolve_blocker", arguments)
	if err != nil {
		return err
	}
	printProjectorResult(result)
	return nil
}

// ── list ──────────────────────────────────────────────────────────────────────

func runProjectorList(args []string) error {
	fs := flag.NewFlagSet("projector list", flag.ContinueOnError)
	orgID := fs.String("org", "", "Filter by org_id")
	state := fs.String("state", "", "Filter by lifecycle_state")
	limit := fs.Int("limit", 50, "Max results (1-100)")
	jsonOut := fs.Bool("json", false, "Output raw JSON")
	if err := fs.Parse(args); err != nil {
		return err
	}

	arguments := map[string]any{"limit": *limit}
	if *orgID != "" {
		arguments["orgId"] = *orgID
	}
	if *state != "" {
		arguments["lifecycleState"] = *state
	}

	result, err := projectorMCPCall("projector.list_projects", arguments)
	if err != nil {
		return err
	}

	if *jsonOut {
		printProjectorResult(result)
		return nil
	}

	projects, _ := result["projects"].([]any)
	if len(projects) == 0 {
		fmt.Println("no projects found")
		return nil
	}

	fmt.Printf("%-12s %-10s %8s %8s  %s\n", "STATE", "PROGRESS", "BLOCKERS", "DUE", "NAME")
	fmt.Println(strings.Repeat("-", 72))
	for _, p := range projects {
		proj, ok := p.(map[string]any)
		if !ok {
			continue
		}
		st, _ := proj["lifecycleState"].(string)
		name, _ := proj["name"].(string)
		pp, _ := proj["progressPermille"].(float64)
		obc, _ := proj["openBlockerCount"].(float64)
		td, _ := proj["targetDate"].(string)
		if td == "" {
			td = "-"
		}
		fmt.Printf("%-12s %7.1f%% %8.0f  %8s  %s\n", st, pp/10.0, obc, td, name)
	}
	return nil
}
