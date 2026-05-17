package main

import (
	"bufio"
	"encoding/json"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

func runMigrateManifest(args []string) error {
	fs := flag.NewFlagSet("migrate-manifest", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component directory (or parent directory with --batch)")
	batch := fs.Bool("batch", false, "migrate all subdirectories containing gftd.json")
	dryRun := fs.Bool("dry-run", false, "show what would be generated without writing")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	absDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}

	if *batch {
		return migrateBatch(absDir, *dryRun)
	}
	return migrateSingle(absDir, *dryRun)
}

func migrateBatch(parentDir string, dryRun bool) error {
	entries, err := os.ReadDir(parentDir)
	if err != nil {
		return err
	}
	var count int
	for _, e := range entries {
		if !e.IsDir() {
			continue
		}
		appDir := filepath.Join(parentDir, e.Name())
		if _, err := os.Stat(filepath.Join(appDir, "gftd.json")); err != nil {
			continue
		}
		if err := migrateSingle(appDir, dryRun); err != nil {
			fmt.Fprintf(os.Stderr, "  FAIL %s: %v\n", e.Name(), err)
			continue
		}
		count++
	}
	fmt.Fprintf(os.Stderr, "==> migrated %d apps\n", count)
	return nil
}

func migrateSingle(compDir string, dryRun bool) error {
	// Check if already migrated
	if _, err := os.Stat(filepath.Join(compDir, "magatama.jsonld")); err == nil {
		fmt.Fprintf(os.Stderr, "  skip %s (magatama.jsonld already exists)\n", filepath.Base(compDir))
		return nil
	}

	// Read gftd.json
	gftdPath := filepath.Join(compDir, "gftd.json")
	gftdData, err := os.ReadFile(gftdPath)
	if err != nil {
		return fmt.Errorf("read gftd.json: %w", err)
	}
	var gftd struct {
		Schema             string     `json:"$schema"`
		Name               string     `json:"name"`
		Nanoid             string     `json:"nanoid"`
		Project            string     `json:"project"`
		Type               string     `json:"type"`
		Org                string     `json:"org"`
		Dockerfile         string     `json:"dockerfile"`
		BaseImage          string     `json:"base_image"`
		HealthCheck        string     `json:"health_check"`
		WITWorld           string     `json:"wit_world"`
		GuestLanguage      string     `json:"guest_language"`
		WASIAdapterVersion string     `json:"wasi_adapter_version"`
		SleepAfter         string     `json:"sleep_after"`
		Runtime            string     `json:"runtime"`
		Hooks              []gftdHook `json:"hooks"`
		Version            string     `json:"version"`
		Template           string     `json:"template"`
		Source             string     `json:"source"`
		EvolvedAt          string     `json:"evolved_at"`
		DOStore            string     `json:"do_store"`
		Routes             []routeConfig `json:"routes"`
	}
	if err := json.Unmarshal(gftdData, &gftd); err != nil {
		return fmt.Errorf("parse gftd.json: %w", err)
	}

	// Build magatama.jsonld
	m := &magatamaJSONLD{
		Context: "https://etzhayyim.com/ns/magatama/v1",
		PerformerType: "service", // default, can be overridden
		Name:    gftd.Name,
		Nanoid:  gftd.Nanoid,
		Project: gftd.Project,
		Org:     gftd.Org,
		Routes:  gftd.Routes,
		Version: gftd.Version,
		Template: gftd.Template,
		Source:   gftd.Source,
		Hooks:   gftd.Hooks,
	}

	// Set DID from routes or project
	host := ""
	if len(gftd.Routes) > 0 {
		host = gftd.Routes[0].Host
	}
	if host == "" && gftd.Project != "" {
		host = gftd.Project + ".etzhayyim.com"
	} else if host == "" {
		host = gftd.Nanoid + ".etzhayyim.com"
	}
	m.ID = "did:web:" + host

	// Runtime type
	rt := gftd.Runtime
	if rt == "" {
		rt = "worker"
	}
	m.RuntimeType = rt

	// Build config
	if gftd.WITWorld != "" || gftd.GuestLanguage != "" || gftd.WASIAdapterVersion != "" {
		m.Build = &buildConfig{
			WITWorld:           gftd.WITWorld,
			GuestLanguage:      gftd.GuestLanguage,
			WASIAdapterVersion: gftd.WASIAdapterVersion,
		}
	}

	// Deploy config
	if gftd.Dockerfile != "" || gftd.BaseImage != "" || gftd.HealthCheck != "" || gftd.SleepAfter != "" {
		m.Deploy = &deployConfig{
			Dockerfile:  gftd.Dockerfile,
			BaseImage:   gftd.BaseImage,
			HealthCheck: gftd.HealthCheck,
			SleepAfter:  gftd.SleepAfter,
		}
	}

	if gftd.EvolvedAt != "" {
		m.EvolvedAt = gftd.EvolvedAt
	}

	// Parse magatama.toml if it exists
	tomlPath := filepath.Join(compDir, "magatama.toml")
	if tomlData, err := os.ReadFile(tomlPath); err == nil {
		parseLegacyTOML(string(tomlData), m)
	}

	data, err := json.MarshalIndent(m, "", "  ")
	if err != nil {
		return err
	}

	if dryRun {
		fmt.Printf("--- %s/magatama.jsonld ---\n%s\n", filepath.Base(compDir), string(data))
		return nil
	}

	outPath := filepath.Join(compDir, "magatama.jsonld")
	if err := os.WriteFile(outPath, append(data, '\n'), 0o644); err != nil {
		return err
	}
	fmt.Fprintf(os.Stderr, "  migrated %s\n", filepath.Base(compDir))
	return nil
}

// parseLegacyTOML parses magatama.toml line-by-line and populates the manifest.
func parseLegacyTOML(content string, m *magatamaJSONLD) {
	section := ""
	var channels []channelDef
	var currentChannel *channelDef

	for _, line := range strings.Split(content, "\n") {
		trimmed := strings.TrimSpace(line)
		if trimmed == "" || strings.HasPrefix(trimmed, "#") {
			continue
		}

		if strings.HasPrefix(trimmed, "[") {
			if currentChannel != nil {
				channels = append(channels, *currentChannel)
				currentChannel = nil
			}
			switch trimmed {
			case "[component]":
				section = "component"
				if m.Component == nil {
					m.Component = &componentConfig{}
				}
			case "[component.env]":
				section = "component.env"
				if m.Component == nil {
					m.Component = &componentConfig{}
				}
				if m.Component.Env == nil {
					m.Component.Env = map[string]string{}
				}
			case "[component.compose]":
				section = "component.compose"
			case "[triggers.http]":
				section = "triggers.http"
				if m.Triggers == nil {
					m.Triggers = &triggerConfig{}
				}
				if m.Triggers.HTTP == nil {
					m.Triggers.HTTP = &httpTrigger{}
				}
			case "[triggers.w_commit]":
				section = "triggers.w_commit"
				if m.Triggers == nil {
					m.Triggers = &triggerConfig{}
				}
				if m.Triggers.SubscribeRepos == nil {
					m.Triggers.SubscribeRepos = &subscribeReposTrigger{}
				}
			case "[ui]":
				section = "ui"
				if m.UI == nil {
					m.UI = &uiConfig{}
				}
			case "[ui.ssr_routes]":
				section = "ui.ssr_routes"
				if m.UI == nil {
					m.UI = &uiConfig{}
				}
				if m.UI.SSRRoutes == nil {
					m.UI.SSRRoutes = map[string]string{}
				}
			case "[game]":
				section = "game"
				if m.Game == nil {
					m.Game = &gameConfig{}
				}
			case "[space]":
				section = "space"
				if m.Space == nil {
					m.Space = &spaceConfig{}
				}
			case "[[space.channels]]":
				section = "space.channels"
				if m.Space == nil {
					m.Space = &spaceConfig{}
				}
				currentChannel = &channelDef{Kind: "public"}
			case "[evolver]":
				section = "evolver"
				if m.Evolver == nil {
					m.Evolver = &evolverConfig{}
				}
			case "[pool]":
				section = "pool"
				if m.Pool == nil {
					m.Pool = &poolConfig{}
				}
			case "[[extensions]]":
				section = "extensions"
				m.Extensions = append(m.Extensions, extensionConfig{})
			case "[interfaces]":
				section = "interfaces"
				if m.Interfaces == nil {
					m.Interfaces = &interfacesConfig{}
				}
			default:
				section = ""
			}
			continue
		}

		parts := strings.SplitN(trimmed, "=", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		val := strings.TrimSpace(parts[1])
		if idx := strings.Index(val, " #"); idx >= 0 {
			val = strings.TrimSpace(val[:idx])
		}
		val = strings.Trim(val, `"'`)

		switch section {
		case "component":
			if key == "path" {
				m.Component.Path = val
			}
		case "component.env":
			m.Component.Env[key] = val
		case "component.compose":
			if key == "signal" {
				if m.Component == nil {
					m.Component = &componentConfig{}
				}
				m.Component.Compose = &composeConfig{Signal: val}
			}
		case "triggers.http":
			switch key {
			case "listen":
				m.Triggers.HTTP.Listen = val
			case "routes":
				m.Triggers.HTTP.Routes = parseTOMLArray(val)
			case "static_dir":
				m.Triggers.HTTP.StaticDir = val
			case "spa":
				m.Triggers.HTTP.SPA = val == "true"
			}
		case "triggers.w_commit":
			if key == "collections" {
				m.Triggers.SubscribeRepos.Collections = parseTOMLArray(val)
			}
		case "ui":
			switch key {
			case "mode":
				switch val {
				case "custom":
					m.UIType = "appview"
				case "full":
					m.UIType = "appview"
				default:
					m.UIType = val
				}
			case "accent":
				m.UI.Accent = val
			case "icon":
				m.UI.Icon = val
			}
		case "ui.ssr_routes":
			m.UI.SSRRoutes[key] = val
		case "game":
			switch key {
			case "runtime":
				m.Game.Runtime = val
			case "entry":
				m.Game.Entry = val
			}
		case "space":
			switch key {
			case "name":
				m.Space.Name = val
			case "description":
				m.Space.Description = val
			case "join_rule":
				m.Space.JoinRule = val
			case "history_visibility":
				m.Space.HistoryVisibility = val
			}
		case "space.channels":
			if currentChannel != nil {
				switch key {
				case "name":
					currentChannel.Name = val
				case "kind":
					currentChannel.Kind = val
				case "description":
					currentChannel.Description = val
				case "default":
					currentChannel.Default = val == "true"
				}
			}
		case "evolver":
			switch key {
			case "murakumo_endpoint":
				m.Evolver.MurakumoEndpoint = val
			case "murakumo_model":
				m.Evolver.MurakumoModel = val
			}
		case "extensions":
			if len(m.Extensions) > 0 {
				ext := &m.Extensions[len(m.Extensions)-1]
				switch key {
				case "name":
					ext.Name = val
				case "package":
					ext.Package = val
				case "component":
					ext.Component = val
				case "kinds":
					ext.Kinds = parseTOMLArray(val)
				}
			}
		case "interfaces":
			if key == "package" {
				m.Interfaces.Package = val
			}
		}
	}

	if currentChannel != nil {
		channels = append(channels, *currentChannel)
	}
	if len(channels) > 0 && m.Space != nil {
		m.Space.Channels = channels
	}
}

// parseTOMLArray parses a simple TOML array like ["a", "b", "c"].
func parseTOMLArray(s string) []string {
	s = strings.TrimSpace(s)
	// Handle multi-line arrays by reading all lines until ]
	if !strings.Contains(s, "]") {
		return nil
	}
	s = strings.TrimPrefix(s, "[")
	s = strings.TrimSuffix(s, "]")
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	var result []string
	scanner := bufio.NewScanner(strings.NewReader(s))
	scanner.Split(func(data []byte, atEOF bool) (advance int, token []byte, err error) {
		// Split on commas, respecting quotes
		for i := 0; i < len(data); i++ {
			if data[i] == ',' {
				return i + 1, data[:i], nil
			}
		}
		if atEOF && len(data) > 0 {
			return len(data), data, nil
		}
		return 0, nil, nil
	})
	for scanner.Scan() {
		item := strings.TrimSpace(scanner.Text())
		item = strings.Trim(item, `"'`)
		item = strings.TrimSuffix(item, ",")
		item = strings.TrimSpace(item)
		if item != "" {
			result = append(result, item)
		}
	}
	return result
}
