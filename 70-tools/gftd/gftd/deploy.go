package main

import (
	"bufio"
	"encoding/base64"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"
)

const cloudflareAccountID = "4da88288dc30d9ee257f319d3c33ecf0"

// Secrets Store ID shared by all magatama Workers.
// Set via GFTD_SECRETS_STORE_ID environment variable.
var secretsStoreID = func() string {
	if v := os.Getenv("GFTD_SECRETS_STORE_ID"); v != "" {
		return v
	}
	return "1824561668fe47cc9127d493961885af"
}()

var defaultCloudflareTokenBackupPaths = []string{
	"/private/tmp/k8s-secrets-backup/spinkube--cloudflare-api-credentials.json",
	"/tmp/k8s-secret-backup/spinkube--cloudflare-api-credentials.json",
}

var wranglerOAuthTokenRe = regexp.MustCompile(`(?m)^oauth_token\s*=\s*"([^"]+)"\s*$`)

func runDeploy(args []string) error {
	fs := flag.NewFlagSet("deploy", flag.ContinueOnError)
	dir := fs.String("dir", ".", "component source directory (default: current dir)")
	pruneCDNImmutable := fs.Bool("prune-cdn-immutable", true, "best-effort cleanup of stale CDN _app/immutable assets after deploy")
	pruneCDNLookbackHours := fs.Int("prune-cdn-lookback-hours", 24*35, "lookback window in hours for CDN immutable cleanup")
	if err := fs.Parse(args); err != nil {
		if err == flag.ErrHelp {
			return nil
		}
		return err
	}

	compDir, err := filepath.Abs(*dir)
	if err != nil {
		return err
	}

	// Read magatama.jsonld for app metadata
	cfg, err := readMagatamaJSONLD(compDir)
	if err != nil {
		return fmt.Errorf("magatama.jsonld required: %w", err)
	}

	return deployWorker(cfg, compDir, deployWorkerOptions{
		PruneCDNImmutable:     *pruneCDNImmutable,
		PruneCDNLookbackHours: *pruneCDNLookbackHours,
	})
}

// magatamaJSONLD is the unified app manifest read from magatama.jsonld.
// Replaces both gftd.json (deploy envelope) and magatama.toml (runtime config).
type magatamaJSONLD struct {
	// JSON-LD identity
	Context string `json:"@context,omitempty"` // "https://etzhayyim.com/ns/magatama/v1"
	ID      string `json:"@id,omitempty"`      // DID: "did:web:vibes.etzhayyim.com"

	// DM2 performer type (required): "service" | "system" | "person" | "organization"
	PerformerType string `json:"performerType,omitempty"`

	// App identity (required)
	Name   string `json:"name"`
	Nanoid string `json:"nanoid"`

	// Profile (required for DID registration on the active PDS endpoint)
	Profile *profileConfig `json:"profile,omitempty"`

	// Governance (role → DID bindings for RACI/RBAC)
	Governance *governanceConfig `json:"governance,omitempty"`

	// App classification
	Project     string `json:"project,omitempty"`     // subdomain override
	RuntimeType string `json:"runtimeType,omitempty"` // "worker" (default)
	Framework   string `json:"framework,omitempty"`   // "ts-native" (唯一のフレームワーク — Hono via @gftd/magatama-host-sdk)
	UIType      string `json:"uiType,omitempty"`      // "appview" (self-hosted UI) | "yoro" (zero frontend, redirect)
	ContentMode string `json:"contentMode,omitempty"` // "timeline" (default) | "interactive" | "game"
	PlayUrl     string `json:"playUrl,omitempty"`     // static game page for ?embed=1 (e.g. "ketsu-game.htm")
	EmbedUrl    string `json:"embedUrl,omitempty"`    // alias for playUrl
	Org         string `json:"org,omitempty"`         // Clerk org_id binding

	// Component config (from magatama.toml [component])
	Component *componentConfig `json:"component,omitempty"`

	// Triggers (from magatama.toml [triggers])
	Triggers *triggerConfig `json:"triggers,omitempty"`

	// UI styling (from magatama.toml [ui])
	UI *uiConfig `json:"ui,omitempty"`

	// Space / channels (from magatama.toml [space])
	Space *spaceConfig `json:"space,omitempty"`

	// Game config (from magatama.toml [game])
	Game *gameConfig `json:"game,omitempty"`

	// Evolver config (from magatama.toml [evolver])
	Evolver *evolverConfig `json:"evolver,omitempty"`

	// Cross-app interfaces (from magatama.toml [interfaces])
	Interfaces *interfacesConfig `json:"interfaces,omitempty"`

	// W Protocol extensions (from magatama.toml [[extensions]])
	Extensions []extensionConfig `json:"extensions,omitempty"`

	// Build config
	Build *buildConfig `json:"build,omitempty"`

	// Desktop app packaging config
	Desktop *desktopConfig `json:"desktop,omitempty"`

	// Deploy config
	Deploy *deployConfig `json:"deploy,omitempty"`

	// Routing
	Routes []routeConfig `json:"routes,omitempty"`

	// Version lineage
	Version   string `json:"version,omitempty"`
	Template  string `json:"template,omitempty"`
	Source    string `json:"source,omitempty"`
	EvolvedAt string `json:"evolvedAt,omitempty"`

	// Hooks
	Hooks []gftdHook `json:"hooks,omitempty"`

	// Pool config
	Pool *poolConfig `json:"pool,omitempty"`

	// Static site config
	Static *staticSiteConfig `json:"static,omitempty"`

	// Convo system prompt — DM agent personality (Murakumo LLM uses this as system prompt)
	ConvoSystemPrompt string `json:"convoSystemPrompt,omitempty"`

	// Sub-DID auto-registration command name (e.g. "RegisterWriterProfiles", "RegisterEntityProfiles")
	// Called via XRPC after deploy to register sub-DIDs on PDS.
	SubDidCommand string `json:"subDidCommand,omitempty"`

	// NeedsBrowser opts the app into the HEADLESS_BROWSER binding in the
	// generated wrangler.jsonc. Pre ADR-0049 this was derived from a WIT
	// import of `magatama:browser/automation@1.0.0` in wit/world.wit; the
	// explicit flag is the surviving signal after WIT bindgen retirement.
	// Legacy WIT scan continues as a fallback in generateWorkerWrangler
	// until all manifests migrate.
	NeedsBrowser bool `json:"needsBrowser,omitempty"`
}

// profileConfig holds DID profile information for active PDS registration.
// Required in magatama.jsonld. gftd build fails if missing.
// All Apps are AI agents — this is declared in the profile for transparency.
type profileConfig struct {
	DisplayName  string   `json:"displayName"`            // Organization/app display name (required)
	Description  string   `json:"description"`            // One-line description (required)
	Handle       string   `json:"handle,omitempty"`       // Vanity actor handle (e.g. "lawfirm" → did:web:lawfirm.etzhayyim.com). When set, gftd deploy injects APP_ACTOR_HANDLE so host-sdk MCP registry loader (ADR-2604261000) can default actor_did to did:web:{handle}.etzhayyim.com. Falls back to component dir slug.
	Avatar       string   `json:"avatar,omitempty"`       // Avatar: emoji (🏛️), initials ("MOJ"), or URL
	Banner       string   `json:"banner,omitempty"`       // Banner: color hex (#1a2b3c), gradient, or URL
	Category     string   `json:"category,omitempty"`     // "government", "international", "religious", "ngo", "sport", "academic"
	Country      string   `json:"country,omitempty"`      // ISO-3166-1 alpha-3 (jpn, usa, deu)
	Jurisdiction string   `json:"jurisdiction,omitempty"` // Legal jurisdiction
	Contract     string   `json:"contract,omitempty"`     // Contract/legal basis name
	IsBot        bool     `json:"isBot"`                  // Always true — all Apps are AI agents
	AgentType    string   `json:"agentType,omitempty"`    // "autonomous", "semi-autonomous", "reactive" (default: "autonomous")
	Capabilities []string `json:"capabilities,omitempty"` // Capability tags for discovery
	Protocols    []string `json:"protocols,omitempty"`    // ["xrpc", "w-protocol"]
	Operator     string   `json:"operator,omitempty"`     // Operating entity (default: "amanomibashira" — religious voluntary association, blockchain-registered; not a 宗教法人法 上の登記宗教法人)
	SourceCode   string   `json:"sourceCode,omitempty"`   // Source repo URL for transparency
	Status       string   `json:"status,omitempty"`       // "online", "degraded", "offline", "maintenance"
	Version      string   `json:"version,omitempty"`      // Semantic version for hero section display
	Icon         string   `json:"icon,omitempty"`         // Emoji icon for compact hero section
	Accent       string   `json:"accent,omitempty"`       // Accent color hex for profile display
}

type governanceConfig struct {
	Raw          map[string]any
	RoleBindings []governanceRoleBinding
}

type governanceRoleBinding struct {
	Role        string `json:"role"`
	DID         string `json:"did"`
	Description string `json:"description,omitempty"`
}

func (g *governanceConfig) UnmarshalJSON(data []byte) error {
	var raw map[string]any
	if err := json.Unmarshal(data, &raw); err != nil {
		return err
	}
	g.Raw = raw
	g.RoleBindings = nil
	if roles, ok := raw["roles"].([]any); ok {
		for _, roleEntry := range roles {
			roleMap, ok := roleEntry.(map[string]any)
			if !ok {
				continue
			}
			role := strings.TrimSpace(fmt.Sprint(roleMap["role"]))
			did := strings.TrimSpace(fmt.Sprint(roleMap["did"]))
			if role == "" || did == "" || role == "<nil>" || did == "<nil>" {
				continue
			}
			g.RoleBindings = append(g.RoleBindings, governanceRoleBinding{
				Role:        role,
				DID:         did,
				Description: strings.TrimSpace(fmt.Sprint(roleMap["description"])),
			})
		}
	}
	return nil
}

func (g governanceConfig) MarshalJSON() ([]byte, error) {
	if g.Raw == nil {
		return []byte("null"), nil
	}
	return json.Marshal(g.Raw)
}

type componentConfig struct {
	Path           string                 `json:"path,omitempty"`
	Env            map[string]string      `json:"env,omitempty"`
	Compose        *composeConfig         `json:"compose,omitempty"`
	DurableObjects []durableObjectBinding `json:"durableObjects,omitempty"`
}

type durableObjectBinding struct {
	Name      string `json:"name"`          // binding name (env var)
	ClassName string `json:"className"`     // exported DO class name
	Tag       string `json:"tag,omitempty"` // migration tag (default v1)
}

type composeConfig struct {
	Signal string `json:"signal,omitempty"`
}

type triggerConfig struct {
	HTTP           *httpTrigger           `json:"http,omitempty"`
	SubscribeRepos *subscribeReposTrigger `json:"subscribeRepos,omitempty"`
}

type httpTrigger struct {
	Listen    string   `json:"listen,omitempty"`
	Routes    []string `json:"routes,omitempty"`
	StaticDir string   `json:"staticDir,omitempty"`
	SPA       bool     `json:"spa,omitempty"`
}

type subscribeReposTrigger struct {
	Collections []string `json:"collections,omitempty"`
}

type uiConfig struct {
	Accent    string            `json:"accent,omitempty"`
	Icon      string            `json:"icon,omitempty"`
	SSRRoutes map[string]string `json:"ssrRoutes,omitempty"`
}

type spaceConfig struct {
	Name              string       `json:"name,omitempty"`
	Description       string       `json:"description,omitempty"`
	JoinRule          string       `json:"joinRule,omitempty"`
	HistoryVisibility string       `json:"historyVisibility,omitempty"`
	Channels          []channelDef `json:"channels,omitempty"`
}

type channelDef struct {
	Name        string `json:"name"`
	Kind        string `json:"kind"`
	Description string `json:"description,omitempty"`
	Default     bool   `json:"default,omitempty"`
}

type gameConfig struct {
	Runtime string `json:"runtime,omitempty"`
	Entry   string `json:"entry,omitempty"`
}

type evolverConfig struct {
	MurakumoEndpoint      string  `json:"murakumoEndpoint,omitempty"`
	MurakumoModel         string  `json:"murakumoModel,omitempty"`
	CritiqueRounds        int     `json:"critiqueRounds,omitempty"`
	FitnessDropThreshold  float64 `json:"fitnessDropThreshold,omitempty"`
	ErrorRateThreshold    float64 `json:"errorRateThreshold,omitempty"`
	ObservationWindowSecs int     `json:"observationWindowSecs,omitempty"`
	DryRun                bool    `json:"dryRun,omitempty"`
}

type interfacesConfig struct {
	Package  string `json:"package,omitempty"`
	Provides []any  `json:"provides,omitempty"`
	Requires []any  `json:"requires,omitempty"`
}

type extensionConfig struct {
	Name      string   `json:"name,omitempty"`
	Package   string   `json:"package,omitempty"`
	Component string   `json:"component,omitempty"`
	Kinds     []string `json:"kinds,omitempty"`
}

type buildConfig struct {
	GuestLanguage      string `json:"guestLanguage,omitempty"`
	WITWorld           string `json:"witWorld,omitempty"`
	WASIAdapterVersion string `json:"wasiAdapterVersion,omitempty"`
}

type deployConfig struct {
	Dockerfile  string `json:"dockerfile,omitempty"`
	BaseImage   string `json:"baseImage,omitempty"`
	HealthCheck string `json:"healthCheck,omitempty"`
	SleepAfter  string `json:"sleepAfter,omitempty"`
}

type routeConfig struct {
	Host  string   `json:"host,omitempty"`
	TLS   bool     `json:"tls,omitempty"`
	Paths []string `json:"paths,omitempty"`
}

type poolConfig struct {
	Size int `json:"size,omitempty"`
}

type staticSiteConfig struct {
	Prefix string `json:"prefix,omitempty"`
}

// AppID returns the nanoid — the unique, canonical app identifier.
// Project name is a human-friendly alias resolved via DNS, not used as script name.
func (g *magatamaJSONLD) AppID() string {
	return g.Nanoid
}

// RuntimeOrDefault returns the runtime type, defaulting to "worker".
func (g *magatamaJSONLD) RuntimeOrDefault() string {
	if g.RuntimeType != "" {
		return g.RuntimeType
	}
	return "worker"
}

// UITypeOrDefault returns the UI type. Two canonical values:
//   - "appview" — self-hosted UI on own domain (Hono + Svelte CSR, /embed route)
//   - "yoro"    — redirect to yoro.etzhayyim.com/{did} profile (zero frontend, data-only apps)
func (g *magatamaJSONLD) UITypeOrDefault() string {
	if g.UIType == "" || g.UIType == "yoro" {
		return "yoro"
	}
	return "appview"
}

// validPerformerTypes is the set of allowed performerType values (DM2 performer taxonomy).
var validPerformerTypes = map[string]bool{
	"service":      true,
	"system":       true,
	"person":       true,
	"organization": true,
}

// PerformerTypeOrDefault returns the performer type, defaulting to "service".
func (g *magatamaJSONLD) PerformerTypeOrDefault() string {
	if g.PerformerType != "" {
		return g.PerformerType
	}
	return "service"
}

// validFrameworks is the set of allowed framework values.
// Standard architecture: ts-native (Hono via @gftd/magatama-host-sdk + Svelte CSR).
var validFrameworks = map[string]bool{
	"ts-native": true, // Default: @gftd/magatama-host-sdk (Hono router), entry: src/app.ts
}

// FrameworkOrDefault returns the framework, defaulting to "ts-native".
// Standard: ts-native uses Hono via @gftd/magatama-host-sdk, entry: src/app.ts.
func (g *magatamaJSONLD) FrameworkOrDefault() string {
	return "ts-native"
}

// FrameworkEntryPoint returns the Worker entry point: always src/app.ts.
func (g *magatamaJSONLD) FrameworkEntryPoint() string {
	return "src/app.ts"
}

// ComponentPath returns the component wasm path from the manifest (used by build_desktop).
func (g *magatamaJSONLD) ComponentPath() string {
	if g.Component != nil && g.Component.Path != "" {
		return g.Component.Path
	}
	return "component.wasm"
}

// UsesAutoCrud checks if the app.ts uses autoCrud() pattern (SDK handles CRUD + heartbeat + governance).
// When true, deploy-side governance parsing can be skipped (SDK registers at runtime via serveAsync).
func (g *magatamaJSONLD) UsesAutoCrud(compDir string) bool {
	appTs := filepath.Join(compDir, "src", "app.ts")
	data, err := os.ReadFile(appTs)
	if err != nil {
		return false
	}
	return strings.Contains(string(data), ".autoCrud(")
}

// actorHandleFromCfg derives the vanity actor handle for APP_ACTOR_HANDLE env
// injection (ADR-2604261000 step 5). The host-sdk MCP registry loader uses
// did:web:{handle}.etzhayyim.com as the default actor_did when mcpRegistry.actorDid
// is not set explicitly; this matches the keying that
// 70-tools/scripts/contract/sync-mcp-registry.py uses for vertex_mcp_tool_def
// rows (NSID 4th segment, e.g. "lawfirm" from ai.gftd.apps.lawfirm.*).
//
// Derivation order:
//  1. magatama.jsonld profile.handle (explicit)
//  2. Component dir slug — for ai-gftd-wasm-{slug}-{nanoid} or {slug}-{nanoid},
//     strip the trailing nanoid (matches cfg.Nanoid) and any "ai-gftd-wasm-"
//     prefix.
//  3. "" — caller skips injection; loader falls back to APP_NANOID.
func actorHandleFromCfg(cfg *magatamaJSONLD, compDir string) string {
	if cfg == nil {
		return ""
	}
	if cfg.Profile != nil && cfg.Profile.Handle != "" {
		return cfg.Profile.Handle
	}
	base := filepath.Base(compDir)
	nanoid := cfg.Nanoid
	if nanoid == "" || !strings.HasSuffix(base, "-"+nanoid) {
		return ""
	}
	slug := strings.TrimSuffix(base, "-"+nanoid)
	slug = strings.TrimPrefix(slug, "ai-gftd-wasm-")
	if slug == "" || slug == nanoid {
		return ""
	}
	return slug
}

// HealthCheckPath returns the health check path, defaulting to "/health".
func (g *magatamaJSONLD) HealthCheckPath() string {
	if g.Deploy != nil && g.Deploy.HealthCheck != "" {
		return g.Deploy.HealthCheck
	}
	return "/health"
}

// readMagatamaJSONLD reads and parses magatama.jsonld from the given directory.
func readMagatamaJSONLD(dir string) (*magatamaJSONLD, error) {
	path := filepath.Join(dir, "magatama.jsonld")
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var m magatamaJSONLD
	if err := json.Unmarshal(data, &m); err != nil {
		return nil, err
	}
	if m.Name == "" {
		return nil, fmt.Errorf("name not found in magatama.jsonld")
	}
	// Validate performerType if explicitly set
	if m.PerformerType != "" && !validPerformerTypes[m.PerformerType] {
		return nil, fmt.Errorf("invalid performerType %q in magatama.jsonld (must be service|system|person|organization)", m.PerformerType)
	}
	// Validate framework if explicitly set
	if m.Framework != "" && !validFrameworks[m.Framework] {
		return nil, fmt.Errorf("invalid framework %q in magatama.jsonld (must be ts-native)", m.Framework)
	}
	// Validate alpha-start naming (DID path ↔ Lexicon NSID correspondence).
	// Legacy apps may still use numeric-leading nanoids; allow temporary opt-out.
	if os.Getenv("GFTD_ALLOW_NON_ALPHA_SEGMENTS") != "1" {
		if errs := validateAlphaStartSegments(&m); len(errs) > 0 {
			return nil, fmt.Errorf("alpha-start naming violations in magatama.jsonld:\n  %s", strings.Join(errs, "\n  "))
		}
	}
	return &m, nil
}

// validateAlphaStartSegments checks that all naming segments start with alpha (a-z/A-Z).
// This ensures DID path ↔ Lexicon NSID structural correspondence (docs/260324-did-path-lexicon-correspondence.md).
func validateAlphaStartSegments(m *magatamaJSONLD) []string {
	var errs []string
	check := func(context, segment string) {
		if segment == "" {
			return
		}
		if len(segment) > 0 && !isAlpha(segment[0]) {
			errs = append(errs, fmt.Sprintf("%s: segment %q starts with non-alpha character (must start with a-z/A-Z)", context, segment))
		}
	}

	// nanoid
	check("nanoid", m.Nanoid)

	// name
	check("name", m.Name)

	// @id DID path segments
	if m.ID != "" {
		// did:web:legal-entity.etzhayyim.com:jpn:kabushiki-kaisha → segments after host
		if strings.HasPrefix(m.ID, "did:web:") {
			parts := strings.Split(m.ID, ":")
			// parts[0]="did", parts[1]="web", parts[2]=host, parts[3..]=path segments
			for i := 3; i < len(parts); i++ {
				check(fmt.Sprintf("@id DID path[%d]", i-3), parts[i])
			}
		}
	}

	// subscribeRepos collection segments
	if m.Triggers != nil && m.Triggers.SubscribeRepos != nil {
		sr := m.Triggers.SubscribeRepos
		for _, coll := range sr.Collections {
			segments := strings.Split(coll, ".")
			for _, seg := range segments {
				check(fmt.Sprintf("subscribeRepos collection %q", coll), seg)
			}
		}
	}

	// project
	check("project", m.Project)

	return errs
}

func isAlpha(b byte) bool {
	return (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z')
}

// ensureSymlink creates a symlink at dst pointing to src.
// Removes existing dst if it's a symlink or doesn't match.
// smokeTest does a simple HTTP GET health check with retries.
func smokeTest(url string) error {
	const maxRetries = 6
	const retryDelay = 10 * time.Second

	fmt.Fprintf(os.Stderr, "==> smoke test: %s\n", url)
	for i := range maxRetries {
		if i > 0 {
			time.Sleep(retryDelay)
		}
		resp, err := http.Get(url) //nolint:noctx
		if err != nil {
			fmt.Fprintf(os.Stderr, "    attempt %d: %v\n", i+1, err)
			continue
		}
		resp.Body.Close()
		if resp.StatusCode == http.StatusOK {
			return nil
		}
		fmt.Fprintf(os.Stderr, "    attempt %d: HTTP %d\n", i+1, resp.StatusCode)
	}
	return fmt.Errorf("smoke test failed after %d attempts", maxRetries)
}

// postDeployQualityCheck validates the deployed app's WASM
// status, and UI mode contract. It runs after the smoke test and prints warnings
// for any quality issues that could cause UI rendering failures.
// Errors are warnings only — they do not fail the deploy.
// registerProfileToYata MERGEs App + Profile nodes into yata via PDS Sql.
// This is the authoritative registration — guest-side identity.register is a sync no-op
// because WASM _initialize cannot perform async IO.
func registerProfileToYata(cfg *magatamaJSONLD, appID string, compDirs ...string) {
	token := resolveGFTDToken()
	if token == "" {
		fmt.Fprintf(os.Stderr, "  error: no auth token — profile registration requires authentication. Run: gftd auth login\n")
		os.Exit(1)
	}

	displayName := appID
	description := ""
	performerType := cfg.PerformerTypeOrDefault()
	contentMode := cfg.ContentMode
	if contentMode == "" {
		contentMode = "timeline"
	}
	if cfg.Profile != nil {
		if cfg.Profile.DisplayName != "" {
			displayName = cfg.Profile.DisplayName
		}
		if cfg.Profile.Description != "" {
			description = cfg.Profile.Description
		}
	}
	nanoid := cfg.Nanoid
	if nanoid == "" {
		nanoid = appID
	}
	did := preferredAppDID(cfg, nanoid, appID)

	// Register Profile + App via dedicated XRPC (Clerk JWT accepted)
	// PDS MERGE → yata Sql (PascalCase: Profile, App)
	var capabilities []string
	var profileIcon, profileAccent, profileVersion, profileContract string
	if cfg.Profile != nil {
		capabilities = cfg.Profile.Capabilities
		profileIcon = cfg.Profile.Icon
		profileAccent = cfg.Profile.Accent
		profileVersion = cfg.Profile.Version
		profileContract = cfg.Profile.Contract
	}
	// Compute embedUrl from uiType + nanoid
	uiType := cfg.UIType
	var embedUrl string
	if uiType == "appview" || uiType == "iframe" || uiType == "game" {
		embedUrl = "https://" + nanoid + ".etzhayyim.com/?embed=1"
	}
	// Override for infra apps that serve their own embed endpoint
	if cfg.EmbedUrl != "" {
		embedUrl = cfg.EmbedUrl
	}

	// ADR-0049: WIT bindgen is a dead path. Governance-graph `witImports`
	// / `witExports` fields are retired — registerApp receives empty
	// arrays so the PDS graph stops accumulating stale entries, while the
	// column shape stays stable for any legacy consumers.
	// The runtime-affecting WIT use (HEADLESS_BROWSER binding) stays in
	// generateWorkerWrangler below and now prefers cfg.NeedsBrowser.

	// Governance block for yata graph
	var governancePayload any
	if cfg.Governance != nil {
		governancePayload = cfg.Governance
	}

	regPayload, _ := json.Marshal(map[string]any{
		"nanoid":            nanoid,
		"displayName":       displayName,
		"description":       description,
		"did":               did,
		"performerType":     performerType,
		"contentMode":       contentMode,
		"sensitivity":       "public",
		"capabilities":      capabilities,
		"icon":              profileIcon,
		"accent":            profileAccent,
		"version":           profileVersion,
		"uiType":            uiType,
		"embedUrl":          embedUrl,
		"contract":          profileContract,
		"witImports":        []string{}, // retired per ADR-0049
		"witExports":        []string{}, // retired per ADR-0049
		"convoSystemPrompt": cfg.ConvoSystemPrompt,
		"governance":        governancePayload,
	})
	regReq, err := http.NewRequest("POST", resolvePDSBaseURL()+"/xrpc/com.atproto.admin.registerApp", strings.NewReader(string(regPayload)))
	if err == nil {
		regReq.Header.Set("Content-Type", "application/json")
		regReq.Header.Set("Authorization", "Bearer "+token)
		resp, err := http.DefaultClient.Do(regReq)
		if err != nil {
			fmt.Fprintf(os.Stderr, "  warning: app profile registration failed: %v\n", err)
		} else {
			if resp.StatusCode >= 400 {
				respBody, _ := io.ReadAll(resp.Body)
				fmt.Fprintf(os.Stderr, "  warning: app profile registration HTTP %d: %s\n", resp.StatusCode, string(respBody))
			}
			resp.Body.Close()
		}
	}
	fmt.Fprintf(os.Stderr, "==> App + Profile registered in yata (nanoid=%s, displayName=%s)\n", nanoid, displayName)

	// Register governance manifest from source command declarations.
	// ADR-0049: WIT bindgen retired — pass the primary compDir directly
	// (no longer a WIT-specific path).
	compDirForGovernance := ""
	if len(compDirs) > 0 {
		compDirForGovernance = compDirs[0]
	}
	registerGovernanceFromSource(token, nanoid, compDirForGovernance, cfg)

	// Post deploy announce — social post via app.bsky.feed.post
	postDeployAnnounce(token, did, displayName, nanoid, cfg)

	// ADR-0074 Phase 2-A.4 — emit immutable on-chain deploy receipt to
	// DeployRegistry on the gftd private chain (260425). Best-effort: the
	// deploy is already complete by here, this just publishes provenance.
	if compDirForGovernance != "" {
		recordDeployToChain(cfg, appID, compDirForGovernance)
	}
}

// registerGovernanceFromSource extracts RACI/RBAC from source and registers via XRPC.
// For TS autoCrud apps, SDK handles governance registration at runtime via serveAsync().
// For explicit sdk.app.command() apps, parses src/app.ts command declarations.
// Also registers role → DID bindings from magatama.jsonld governance.roles.
func registerGovernanceFromSource(token, nanoid, compDir string, cfg *magatamaJSONLD) {
	if token == "" || nanoid == "" {
		return
	}
	registerRoleBindings := func() {
		if cfg == nil || cfg.Governance == nil || len(cfg.Governance.RoleBindings) == 0 {
			return
		}
		rolePayload, _ := json.Marshal(map[string]any{
			"appNanoid": nanoid,
			"roles":     cfg.Governance.RoleBindings,
		})
		roleReq, err := http.NewRequest("POST", resolvePDSBaseURL()+"/xrpc/ai.gftd.governance.registerRoleBindings", strings.NewReader(string(rolePayload)))
		if err != nil {
			return
		}
		roleReq.Header.Set("Content-Type", "application/json")
		roleReq.Header.Set("Authorization", "Bearer "+token)
		roleResp, err := http.DefaultClient.Do(roleReq)
		if err != nil {
			fmt.Fprintf(os.Stderr, "  warning: role binding registration failed: %v\n", err)
			return
		}
		defer roleResp.Body.Close()
		if roleResp.StatusCode >= 400 {
			body, _ := io.ReadAll(roleResp.Body)
			fmt.Fprintf(os.Stderr, "  warning: role binding HTTP %d: %s\n", roleResp.StatusCode, string(body))
			return
		}
		fmt.Fprintf(os.Stderr, "==> role → DID bindings registered (%d bindings)\n", len(cfg.Governance.RoleBindings))
	}

	// TS autoCrud apps: SDK handles governance via serveAsync() at runtime.
	// Deploy-side parsing is redundant — skip source governance extraction.
	if cfg != nil && cfg.UsesAutoCrud(compDir) {
		fmt.Fprintf(os.Stderr, "==> autoCrud detected: governance registered by SDK at runtime (skipping source parsing)\n")
		registerRoleBindings()
		return
	}

	// TS apps with explicit sdk.app.command(): extract governance from app.ts
	appTsPath := filepath.Join(compDir, "src", "app.ts")
	if compDir == "" {
		appTsPath = filepath.Join("src", "app.ts")
	}

	data, err := os.ReadFile(appTsPath)
	if err != nil {
		registerRoleBindings()
		return
	}
	src := string(data)

	// Extract governance policies from command declarations
	type raciEntry struct {
		Role  string `json:"role"`
		Kind  string `json:"kind"`
		Value string `json:"value"`
	}
	type approvalEntry struct {
		DecisionClass int    `json:"decisionClass"`
		MinApprovers  int    `json:"minApprovers"`
		RiskTier      string `json:"riskTier"`
	}
	type policyEntry struct {
		Command       string         `json:"command"`
		RACI          []raciEntry    `json:"raci"`
		Approval      *approvalEntry `json:"approval,omitempty"`
		BPMNTaskID    string         `json:"bpmnTaskId,omitempty"`
		OCELEventType string         `json:"ocelEventType,omitempty"`
	}

	var policies []policyEntry
	lines := strings.Split(src, "\n")
	var currentCmd string
	var currentRaci []raciEntry
	var currentApproval *approvalEntry
	var currentBPMN, currentOCEL string

	flushCmd := func() {
		if currentCmd != "" && (len(currentRaci) > 0 || currentApproval != nil || currentBPMN != "" || currentOCEL != "") {
			policies = append(policies, policyEntry{
				Command: currentCmd, RACI: currentRaci, Approval: currentApproval,
				BPMNTaskID: currentBPMN, OCELEventType: currentOCEL,
			})
		}
		currentCmd = ""
		currentRaci = nil
		currentApproval = nil
		currentBPMN = ""
		currentOCEL = ""
	}

	for _, line := range lines {
		trimmed := strings.TrimSpace(line)
		// Detect command declarations:
		// Go: app.Command("", "RegisterEntity", ...)
		// TS: .command("ai.gftd.apps.domain.method", ...)  or  sdk.app.command(...)
		if strings.Contains(trimmed, "app.Command(") || strings.Contains(trimmed, ".command(") {
			flushCmd()
			if strings.Contains(trimmed, "app.Command(") {
				// Go pattern: app.Command("", "RegisterEntity", ...)
				parts := strings.SplitN(trimmed, ",", 3)
				if len(parts) >= 2 {
					name := strings.TrimSpace(parts[1])
					name = strings.Trim(name, "\" ")
					currentCmd = name
				}
			} else {
				// TS pattern: .command("ai.gftd.apps.domain.method", ...)
				re := regexp.MustCompile(`\.command\(\s*"([^"]+)"`)
				if m := re.FindStringSubmatch(trimmed); len(m) > 1 {
					currentCmd = m[1]
				}
			}
		}
		// Responsible/Accountable/Consulted/Informed
		// Go: magatama.Responsible(magatama.AssigneeOrgRole, "value")
		// TS: responsible(AssigneeKind.OrgRole, "value")
		for _, role := range []string{"Responsible", "Accountable", "Consulted", "Informed"} {
			goPattern := "magatama." + role + "("
			tsPattern := strings.ToLower(role[:1]) + role[1:] + "("
			matchIdx := -1
			matchLen := 0
			if idx := strings.Index(trimmed, goPattern); idx >= 0 {
				matchIdx = idx
				matchLen = len(goPattern)
			} else if idx := strings.Index(trimmed, tsPattern); idx >= 0 {
				matchIdx = idx
				matchLen = len(tsPattern)
			}
			if matchIdx >= 0 {
				rest := trimmed[matchIdx+matchLen:]
				rest = strings.TrimSuffix(rest, "),")
				rest = strings.TrimSuffix(rest, ")")
				args := strings.SplitN(rest, ",", 2)
				kind := "org-role"
				if strings.Contains(args[0], "AssigneeDID") || strings.Contains(args[0], "Did") {
					kind = "did"
				} else if strings.Contains(args[0], "AssigneeTeam") || strings.Contains(args[0], "Team") {
					kind = "team"
				}
				value := ""
				if len(args) > 1 {
					value = strings.TrimSpace(args[1])
					value = strings.Trim(value, "\" '`")
				}
				currentRaci = append(currentRaci, raciEntry{
					Role: strings.ToLower(role), Kind: kind, Value: value,
				})
			}
		}
		// RequireApproval (Go: magatama.RequireApproval, TS: requireApproval)
		if strings.Contains(trimmed, "RequireApproval(") || strings.Contains(trimmed, "requireApproval(") {
			// Go: magatama.RequireApproval(magatama.DecisionClassC, 1, "low"),
			// TS: requireApproval(DecisionClass.C, 1, "low"),
			idx := strings.Index(trimmed, "RequireApproval(")
			matchToken := "RequireApproval("
			if idx < 0 {
				idx = strings.Index(trimmed, "requireApproval(")
				matchToken = "requireApproval("
			}
			rest := trimmed[idx+len(matchToken):]
			rest = strings.TrimSuffix(rest, "),")
			rest = strings.TrimSuffix(rest, ")")
			args := strings.Split(rest, ",")
			dc := 2 // default C
			if strings.Contains(args[0], "ClassA") {
				dc = 0
			} else if strings.Contains(args[0], "ClassB") {
				dc = 1
			} else if strings.Contains(args[0], "ClassD") {
				dc = 3
			}
			minApprovers := 1
			if len(args) > 1 {
				fmt.Sscanf(strings.TrimSpace(args[1]), "%d", &minApprovers)
			}
			riskTier := "low"
			if len(args) > 2 {
				riskTier = strings.Trim(strings.TrimSpace(args[2]), "\" ")
			}
			currentApproval = &approvalEntry{DecisionClass: dc, MinApprovers: minApprovers, RiskTier: riskTier}
		}
		// WithBPMNTask (Go: WithBPMNTask, TS: withBPMNTask)
		for _, pat := range []string{"WithBPMNTask(\"", "withBPMNTask(\""} {
			if idx := strings.Index(trimmed, pat); idx >= 0 {
				rest := trimmed[idx+len(pat):]
				if end := strings.Index(rest, "\""); end > 0 {
					currentBPMN = rest[:end]
				}
				break
			}
		}
		// WithOCELEvent (Go: WithOCELEvent, TS: withOCELEvent)
		for _, pat := range []string{"WithOCELEvent(\"", "withOCELEvent(\""} {
			if idx := strings.Index(trimmed, pat); idx >= 0 {
				rest := trimmed[idx+len(pat):]
				if end := strings.Index(rest, "\""); end > 0 {
					currentOCEL = rest[:end]
				}
				break
			}
		}
	}
	flushCmd()

	if len(policies) == 0 {
		registerRoleBindings()
		return
	}

	manifest := map[string]any{"appId": nanoid, "policies": policies}
	manifestJSON, _ := json.Marshal(manifest)
	payload, _ := json.Marshal(map[string]any{"manifestJson": string(manifestJSON)})

	req, err := http.NewRequest("POST", resolvePDSBaseURL()+"/xrpc/ai.gftd.governance.registerManifest", strings.NewReader(string(payload)))
	if err != nil {
		return
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  warning: governance manifest registration failed: %v\n", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode >= 400 {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "  warning: governance manifest HTTP %d: %s\n", resp.StatusCode, string(body))
		return
	}
	fmt.Fprintf(os.Stderr, "==> governance manifest registered (%d commands with RACI/RBAC)\n", len(policies))
	registerRoleBindings()
}

// extractWITGovernance reads world.wit to extract governance-relevant imports and exports.
func extractWITGovernance(compDir string) (imports []string, exports []string) {
	// Find world.wit — try compDir first, then CWD
	witPath := filepath.Join("wit", "world.wit")
	if compDir != "" {
		candidate := filepath.Join(compDir, "wit", "world.wit")
		if _, err := os.Stat(candidate); err == nil {
			witPath = candidate
		}
	}
	data, err := os.ReadFile(witPath)
	if err != nil {
		return nil, nil
	}
	for _, line := range strings.Split(string(data), "\n") {
		line = strings.TrimSpace(line)
		if strings.HasPrefix(line, "import ") {
			// e.g. "import magatama:contract/agreement@1.0.0;"
			wit := strings.TrimSuffix(strings.TrimPrefix(line, "import "), ";")
			wit = strings.TrimSpace(wit)
			if wit != "" {
				imports = append(imports, wit)
			}
		} else if strings.HasPrefix(line, "export ") {
			// e.g. "export gftd:ubo/ubo-analysis@1.0.0;"
			wit := strings.TrimSuffix(strings.TrimPrefix(line, "export "), ";")
			wit = strings.TrimSpace(wit)
			if wit != "" {
				exports = append(exports, wit)
			}
		}
	}
	return imports, exports
}

// registerToSyncRegistry adds app to R2 sync-registry so PDS cron sends heartbeats.
func registerToSyncRegistry(cfg *magatamaJSONLD, appID string) {
	token := resolveGFTDToken()
	if token == "" {
		return
	}
	nanoid := cfg.Nanoid
	if nanoid == "" {
		nanoid = appID
	}
	displayName := appID
	if cfg.Profile != nil && cfg.Profile.DisplayName != "" {
		displayName = cfg.Profile.DisplayName
	}
	did := preferredAppDID(cfg, nanoid, appID)
	payload := fmt.Sprintf(`{"nanoid":%q,"did":%q,"displayName":%q,"deployedAt":%q}`,
		nanoid, did, displayName, time.Now().UTC().Format(time.RFC3339))
	req, err := http.NewRequest("POST", resolvePDSBaseURL()+"/xrpc/ai.gftd.pds.registerSyncApp", strings.NewReader(payload))
	if err != nil {
		return
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("Authorization", "Bearer "+token)
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  warning: sync-registry: %v\n", err)
		return
	}
	defer resp.Body.Close()
	if resp.StatusCode == 200 {
		fmt.Fprintf(os.Stderr, "  sync-registry: registered %s\n", nanoid)
	} else {
		body, _ := io.ReadAll(resp.Body)
		fmt.Fprintf(os.Stderr, "  warning: sync-registry %d: %s\n", resp.StatusCode, string(body))
	}
}

func preferredAppDID(cfg *magatamaJSONLD, nanoid, appID string) string {
	if cfg != nil {
		id := strings.TrimSpace(cfg.ID)
		if strings.HasPrefix(id, "did:web:") {
			return id
		}
	}
	if strings.TrimSpace(nanoid) != "" {
		return "did:web:" + strings.TrimSpace(nanoid) + ".etzhayyim.com"
	}
	return "did:web:" + strings.TrimSpace(appID) + ".etzhayyim.com"
}

func postDeployAnnounce(token, did, displayName, nanoid string, cfg *magatamaJSONLD) {
	// Trigger app's own heartbeat — the app posts via its own DID (write buffer → PDS XRPC).
	// This also triggers social evolution init + identity/capability registration flush.
	heartbeatURL := fmt.Sprintf("https://%s.etzhayyim.com/_heartbeat", nanoid)
	req, err := http.NewRequest("POST", heartbeatURL, strings.NewReader("{}"))
	if err != nil {
		return
	}
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "  deploy announce: heartbeat failed (%v)\n", err)
		return
	}
	defer resp.Body.Close()
	respBody, _ := io.ReadAll(resp.Body)
	if resp.StatusCode < 300 {
		fmt.Fprintf(os.Stderr, "==> deploy announce: heartbeat triggered (write buffer flush → social post)\n")
	} else {
		fmt.Fprintf(os.Stderr, "  deploy announce: heartbeat HTTP %d %s\n", resp.StatusCode, string(respBody)[:min(200, len(respBody))])
	}
}

func postDeployQualityCheck(cfg *magatamaJSONLD, compDir string) {
	appID := cfg.AppID()
	baseURL := "https://" + appID + ".etzhayyim.com"
	var warnings []string

	// 2. /_app/meta — Version lineage + UI mode
	if body, status, err := httpGetJSON(baseURL + "/_app/meta"); err == nil && status == 200 {
		var meta map[string]any
		if json.Unmarshal(body, &meta) == nil {
			if v, _ := meta["version"].(string); v == "" {
				warnings = append(warnings, "/_app/meta: version is empty (set version in gftd.json)")
			}
			if sha, _ := meta["deploy_sha"].(string); sha == "" {
				warnings = append(warnings, "/_app/meta: deploy_sha is empty (version lineage broken)")
			}
		}
	}

	// 4. Validate magatama.jsonld ui.ssrRoutes — talk/vibes/provider should NOT have app-specific handlers
	if manifestCfg, err := readMagatamaJSONLD(compDir); err == nil && manifestCfg.UI != nil {
		for key := range manifestCfg.UI.SSRRoutes {
			switch key {
			case "talk":
				warnings = append(warnings, "magatama.jsonld: ui.ssrRoutes.talk has app-specific handler (should be AppShell v2 shared W Protocol chat)")
			case "vibes":
				warnings = append(warnings, "magatama.jsonld: ui.ssrRoutes.vibes has app-specific handler (should be Space public channels)")
			case "provider":
				warnings = append(warnings, "magatama.jsonld: ui.ssrRoutes.provider has app-specific handler (should be murakumo LLM shared)")
			}
		}
	}

	if len(warnings) == 0 {
		fmt.Fprintf(os.Stderr, "==> quality check passed (%s)\n", appID)
	} else {
		fmt.Fprintf(os.Stderr, "==> quality check: %d warning(s) for %s\n", len(warnings), appID)
		for _, w := range warnings {
			fmt.Fprintf(os.Stderr, "    ⚠ %s\n", w)
		}
	}
}

// httpGetJSON performs an HTTP GET and returns (body, statusCode, error).
// The response body is fully read and closed before returning.
func httpGetJSON(url string) ([]byte, int, error) {
	resp, err := http.Get(url) //nolint:noctx
	if err != nil {
		return nil, 0, err
	}
	body := make([]byte, 0, 4096)
	buf := make([]byte, 4096)
	for {
		n, readErr := resp.Body.Read(buf)
		if n > 0 {
			body = append(body, buf[:n]...)
		}
		if readErr != nil {
			break
		}
	}
	resp.Body.Close()
	return body, resp.StatusCode, nil
}

func planCachePurge(cfg *magatamaJSONLD, compDir, smokeURL string) hookCachePurge {
	return hookCachePurge{
		URLs:     cachePurgeURLs(cfg, compDir, smokeURL),
		Status:   "planned",
		Message:  "cache purge targets planned",
		Provider: "cloudflare",
	}
}

func purgeCacheTargets(cfg *magatamaJSONLD, compDir, smokeURL string) hookCachePurge {
	result := planCachePurge(cfg, compDir, smokeURL)
	result.Attempted = true
	result.Status = "skipped"

	if len(result.URLs) == 0 {
		result.Message = "no cache purge targets resolved"
		return result
	}

	token, provider := resolveCloudflareToken()
	result.Provider = provider
	if token == "" {
		result.Message = "no Cloudflare API token available for purge"
		return result
	}

	zoneID, err := resolveCloudflareZoneID(token, "etzhayyim.com")
	if err != nil {
		result.Status = "failed"
		result.Message = err.Error()
		return result
	}
	result.ZoneID = zoneID

	if err := cloudflarePurgeURLs(token, zoneID, result.URLs); err != nil {
		result.Status = "failed"
		result.Message = err.Error()
		return result
	}

	result.Status = "purged"
	result.Message = fmt.Sprintf("purged %d urls", len(result.URLs))
	result.PurgedAt = time.Now().UTC().Format(time.RFC3339)
	return result
}

func cachePurgeURLs(cfg *magatamaJSONLD, compDir, smokeURL string) []string {
	if cfg == nil {
		return nil
	}
	appID := cfg.AppID()
	if appID == "" {
		return nil
	}
	baseURL := fmt.Sprintf("https://%s.etzhayyim.com", appID)
	uiMode, _, _, _, _, _, _ := parseAppConfig(compDir)
	if uiMode == "" {
		uiMode = cfg.UITypeOrDefault()
	}
	urls := []string{
		baseURL + "/",
	}
	if smokeURL != "" {
		urls = append(urls, smokeURL)
	}
	if uiMode == "webcomponent" {
		urls = append(urls,
			baseURL+"/_app/meta",
		)
	}
	seen := make(map[string]struct{}, len(urls))
	deduped := make([]string, 0, len(urls))
	for _, u := range urls {
		if u == "" {
			continue
		}
		if _, ok := seen[u]; ok {
			continue
		}
		seen[u] = struct{}{}
		deduped = append(deduped, u)
	}
	return deduped
}

func resolveCloudflareToken() (string, string) {
	for _, key := range []string{"CLOUDFLARE_API_TOKEN", "CF_API_TOKEN", "GFTD_CLOUDFLARE_API_TOKEN"} {
		if v := strings.TrimSpace(os.Getenv(key)); v != "" {
			return v, key
		}
	}
	for _, key := range []string{"CLOUDFLARE_API_TOKEN_FILE", "GFTD_CLOUDFLARE_API_TOKEN_FILE"} {
		if path := strings.TrimSpace(os.Getenv(key)); path != "" {
			if token := loadCloudflareTokenFile(path); token != "" {
				return token, key
			}
		}
	}
	// Prefer wrangler OAuth token (has secrets store scope) over backup file tokens.
	home, err := os.UserHomeDir()
	if err == nil {
		configPath := filepath.Join(home, "Library", "Preferences", ".wrangler", "config", "default.toml")
		if data, err := os.ReadFile(configPath); err == nil {
			if match := wranglerOAuthTokenRe.FindStringSubmatch(string(data)); len(match) == 2 {
				return match[1], "wrangler_oauth"
			}
		}
	}
	for _, path := range defaultCloudflareTokenBackupPaths {
		if token := loadCloudflareTokenFile(path); token != "" {
			return token, path
		}
	}
	return "", ""
}

func loadCloudflareTokenFile(path string) string {
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	trimmed := strings.TrimSpace(string(data))
	if trimmed == "" {
		return ""
	}
	if !strings.HasPrefix(trimmed, "{") {
		return trimmed
	}
	var payload struct {
		Data map[string]string `json:"data"`
	}
	if err := json.Unmarshal(data, &payload); err != nil {
		return ""
	}
	encoded := strings.TrimSpace(payload.Data["CLOUDFLARE_API_TOKEN"])
	if encoded == "" {
		return ""
	}
	decoded, err := base64.StdEncoding.DecodeString(encoded)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(string(decoded))
}

func resolveCloudflareZoneID(token, zoneName string) (string, error) {
	req, err := http.NewRequest(http.MethodGet, "https://api.cloudflare.com/client/v4/zones?name="+zoneName, nil)
	if err != nil {
		return "", err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return "", err
	}
	defer resp.Body.Close()
	var payload struct {
		Success bool `json:"success"`
		Errors  []struct {
			Message string `json:"message"`
		} `json:"errors"`
		Result []struct {
			ID string `json:"id"`
		} `json:"result"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return "", err
	}
	if !payload.Success {
		if len(payload.Errors) > 0 {
			return "", fmt.Errorf("cloudflare zone lookup: %s", payload.Errors[0].Message)
		}
		return "", fmt.Errorf("cloudflare zone lookup failed")
	}
	if len(payload.Result) == 0 || payload.Result[0].ID == "" {
		return "", fmt.Errorf("cloudflare zone lookup: zone %q not found", zoneName)
	}
	return payload.Result[0].ID, nil
}

func cloudflarePurgeURLs(token, zoneID string, urls []string) error {
	body, err := json.Marshal(map[string]any{"files": urls})
	if err != nil {
		return err
	}
	req, err := http.NewRequest(http.MethodPost, "https://api.cloudflare.com/client/v4/zones/"+zoneID+"/purge_cache", strings.NewReader(string(body)))
	if err != nil {
		return err
	}
	req.Header.Set("Authorization", "Bearer "+token)
	req.Header.Set("Content-Type", "application/json")
	resp, err := http.DefaultClient.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	var payload struct {
		Success bool `json:"success"`
		Errors  []struct {
			Message string `json:"message"`
		} `json:"errors"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return err
	}
	if !payload.Success {
		if len(payload.Errors) > 0 {
			return fmt.Errorf("cloudflare purge: %s", payload.Errors[0].Message)
		}
		return fmt.Errorf("cloudflare purge failed")
	}
	return nil
}

// parseAppConfig reads UI and game config from magatama.jsonld via the manifest struct.
// Returns (uiMode, displayName, accent, icon, ssrRoutesJSON, gameRuntime, gameEntry).
func parseAppConfig(compDir string) (string, string, string, string, string, string, string) {
	cfg, err := readMagatamaJSONLD(compDir)
	if err != nil {
		return "appview", "", "", "", "{}", "", ""
	}
	return parseAppConfigFromManifest(cfg)
}

// parseAppConfigFromManifest extracts UI/game config from the manifest struct.
func parseAppConfigFromManifest(cfg *magatamaJSONLD) (string, string, string, string, string, string, string) {
	uiMode := cfg.UITypeOrDefault()

	displayName := ""
	accent := ""
	icon := ""
	ssrRoutesJSON := "{}"
	gameRuntime := ""
	gameEntry := ""

	if cfg.UI != nil {
		accent = cfg.UI.Accent
		icon = cfg.UI.Icon
		if len(cfg.UI.SSRRoutes) > 0 {
			b, _ := json.Marshal(cfg.UI.SSRRoutes)
			ssrRoutesJSON = string(b)
		}
	}

	if cfg.Space != nil {
		if displayName == "" {
			displayName = cfg.Space.Name
		}
	}

	if cfg.Game != nil {
		gameRuntime = cfg.Game.Runtime
		gameEntry = cfg.Game.Entry
	}

	return uiMode, displayName, accent, icon, ssrRoutesJSON, gameRuntime, gameEntry
}

// copyFile copies a file from src to dst.
func copyDir(src, dst string) error {
	return filepath.Walk(src, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		rel, _ := filepath.Rel(src, path)
		target := filepath.Join(dst, rel)
		if info.IsDir() {
			return os.MkdirAll(target, 0o755)
		}
		return copyFile(path, target)
	})
}

func copyFile(src, dst string) error {
	data, err := os.ReadFile(src)
	if err != nil {
		return err
	}
	return os.WriteFile(dst, data, 0o644)
}

// gitShortSHA returns the short git commit SHA from the given directory.
func gitShortSHA(dir string) (string, error) {
	cmd := exec.Command("git", "rev-parse", "--short", "HEAD")
	cmd.Dir = dir
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

var appIdTSRe = regexp.MustCompile(`(?:const|let|var)\s+appId\s*=\s*"([^"]+)"`)

// extractNanoidFromAppTS extracts appId from src/app.ts (used by set_profiles).
func extractNanoidFromAppTS(dir string) string {
	return extractFieldFromFile(filepath.Join(dir, "src", "app.ts"), appIdTSRe)
}

func extractFieldFromFile(path string, re *regexp.Regexp) string {
	f, err := os.Open(path)
	if err != nil {
		return ""
	}
	defer f.Close()
	scanner := bufio.NewScanner(f)
	for scanner.Scan() {
		if m := re.FindStringSubmatch(scanner.Text()); len(m) == 2 {
			return m[1]
		}
	}
	return ""
}

// deployState tracks per-app deploy metadata (used by systemofsystem for deploy status).
type deployState struct {
	Version int                       `json:"version"`
	Apps    map[string]deployAppState `json:"apps"`
}

type deployAppState struct {
	Nanoid         string              `json:"nanoid"`
	AppVersion     string              `json:"app_version,omitempty"`
	LastDeployedAt string              `json:"last_deployed_at,omitempty"`
	LastDeploySHA  string              `json:"last_deploy_sha,omitempty"`
	WASMHash       string              `json:"wasm_hash,omitempty"`
	History        []deployHistoryItem `json:"history,omitempty"`
}

type deployHistoryItem struct {
	Version    string `json:"version"`
	SHA        string `json:"sha"`
	DeployedAt string `json:"deployed_at"`
	WASMHash   string `json:"wasm_hash,omitempty"`
}

// deployWorker deploys an App as a Cloudflare Worker.
// Generates wrangler.jsonc with correct bindings, then runs `npx wrangler deploy`.
type deployWorkerOptions struct {
	PruneCDNImmutable     bool
	PruneCDNLookbackHours int
}

type cdnImmutablePruneResult struct {
	Scanned int
	Deleted int
}

func deployWorker(cfg *magatamaJSONLD, compDir string, opts deployWorkerOptions) error {
	appID := cfg.AppID()
	if appID == "" {
		return fmt.Errorf("nanoid required in magatama.jsonld")
	}
	if cfg.Nanoid != "" && cfg.Nanoid != appID {
		appID = cfg.Nanoid
	}

	fmt.Fprintf(os.Stderr, "==> deploying %s\n", appID)

	// Ensure svelte/build/ exists for Workers Assets (even if empty)
	if cfg.UITypeOrDefault() != "yoro" {
		os.MkdirAll(filepath.Join(compDir, "svelte", "build"), 0o755)
	}

	// Generate wrangler.jsonc with routes, R2, services, secrets
	var versionMeta *appVersionMeta
	sha, _ := gitShortSHA(compDir)
	if cfg.Version != "" || cfg.Template != "" || cfg.Source != "" {
		versionMeta = &appVersionMeta{
			Version:   cfg.Version,
			Template:  cfg.Template,
			Source:    cfg.Source,
			DeploySHA: sha,
			DeployAt:  time.Now().UTC().Format(time.RFC3339),
		}
	}
	// ADR-0049: HEADLESS_BROWSER trigger migrated to magatama.jsonld
	// `"needsBrowser": true`. Legacy WIT scan kept as fallback for
	// unmigrated manifests; both paths feed generateWorkerWrangler.
	witImports, _ := extractWITGovernance(compDir)
	if cfg.NeedsBrowser {
		witImports = append(witImports, "magatama:browser/automation@1.0.0")
	}
	wranglerJSON := generateWorkerWrangler(appID, secretsStoreID, versionMeta, cfg, compDir, witImports)
	wranglerPath := filepath.Join(compDir, "wrangler.jsonc")
	if err := os.WriteFile(wranglerPath, []byte(wranglerJSON), 0o644); err != nil {
		return fmt.Errorf("write wrangler.jsonc: %w", err)
	}

	// Deploy via wrangler
	if err := runCmd(compDir, "npx", "wrangler", "deploy"); err != nil {
		return fmt.Errorf("wrangler deploy: %w", err)
	}
	if opts.PruneCDNImmutable {
		result, err := pruneCDNImmutableAssets(cfg, compDir, time.Duration(opts.PruneCDNLookbackHours)*time.Hour)
		if err != nil {
			fmt.Fprintf(os.Stderr, "  warning: CDN immutable prune skipped: %v\n", err)
		} else if result.Scanned > 0 {
			fmt.Fprintf(os.Stderr, "  CDN immutable prune: deleted %d stale objects (scanned %d recent objects)\n", result.Deleted, result.Scanned)
		}
	}

	fmt.Fprintf(os.Stderr, "==> deployed magatama-%s\n", appID)
	fmt.Fprintf(os.Stderr, "  https://%s.etzhayyim.com/health\n", appID)
	return nil
}

func pruneCDNImmutableAssets(cfg *magatamaJSONLD, compDir string, lookback time.Duration) (cdnImmutablePruneResult, error) {
	if cfg == nil || cfg.UITypeOrDefault() == "yoro" {
		return cdnImmutablePruneResult{}, nil
	}
	currentKeys, err := currentImmutableAssetKeys(cfg, compDir)
	if err != nil {
		return cdnImmutablePruneResult{}, err
	}
	if len(currentKeys) == 0 {
		return cdnImmutablePruneResult{}, nil
	}
	token, _ := resolveCloudflareToken()
	if token == "" {
		return cdnImmutablePruneResult{}, fmt.Errorf("no Cloudflare API token available")
	}
	if lookback <= 0 {
		lookback = 24 * 35 * time.Hour
	}
	recentKeys, err := fetchRecentR2PutObjectNames(token, cloudflareAccountID, "ai-gftd-cdn", time.Now().UTC().Add(-lookback), time.Now().UTC(), 5000)
	if err != nil {
		return cdnImmutablePruneResult{}, err
	}
	staleKeys := staleImmutableKeys(recentKeys, currentKeys)
	if len(staleKeys) == 0 {
		return cdnImmutablePruneResult{Scanned: len(recentKeys)}, nil
	}
	env := append([]string{}, os.Environ()...)
	env = setEnv(env, "CLOUDFLARE_API_TOKEN", token)
	deleted := 0
	for _, key := range staleKeys {
		if err := runCmdEnv(compDir, env, "npx", "wrangler", "r2", "object", "delete", "ai-gftd-cdn/"+key); err != nil {
			return cdnImmutablePruneResult{Scanned: len(recentKeys), Deleted: deleted}, err
		}
		deleted++
	}
	return cdnImmutablePruneResult{Scanned: len(recentKeys), Deleted: deleted}, nil
}

func currentImmutableAssetKeys(cfg *magatamaJSONLD, compDir string) (map[string]struct{}, error) {
	immutableDir := filepath.Join(compDir, "svelte", "build", "_app", "immutable")
	if st, err := os.Stat(immutableDir); err != nil {
		if os.IsNotExist(err) {
			return map[string]struct{}{}, nil
		}
		return nil, err
	} else if !st.IsDir() {
		return map[string]struct{}{}, nil
	}
	keys := make(map[string]struct{})
	hosts := staticAssetHosts(cfg)
	err := filepath.WalkDir(immutableDir, func(path string, d os.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if d.IsDir() {
			return nil
		}
		rel, err := filepath.Rel(immutableDir, path)
		if err != nil {
			return err
		}
		rel = filepath.ToSlash(rel)
		for _, host := range hosts {
			keys[host+"/_app/immutable/"+rel] = struct{}{}
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	return keys, nil
}

func staticAssetHosts(cfg *magatamaJSONLD) []string {
	if cfg == nil {
		return nil
	}
	appID := strings.TrimSpace(cfg.AppID())
	if appID == "" {
		return nil
	}
	hosts := []string{appID + ".etzhayyim.com"}
	// Only add project vanity host when app name matches project name
	// (prevents multi-app projects like states from all claiming states.etzhayyim.com)
	if project := strings.TrimSpace(cfg.Project); project != "" && project != appID && cfg.Name == project {
		hosts = append(hosts, project+".etzhayyim.com")
	}
	sort.Strings(hosts)
	return hosts
}

func staleImmutableKeys(recentKeys []string, currentKeys map[string]struct{}) []string {
	seen := make(map[string]struct{}, len(recentKeys))
	stale := make([]string, 0)
	for _, key := range recentKeys {
		if !strings.Contains(key, "/_app/immutable/") {
			continue
		}
		if _, ok := seen[key]; ok {
			continue
		}
		seen[key] = struct{}{}
		if _, ok := currentKeys[key]; ok {
			continue
		}
		stale = append(stale, key)
	}
	sort.Strings(stale)
	return stale
}

func fetchRecentR2PutObjectNames(apiToken, accountID, bucketName string, from, to time.Time, limit int) ([]string, error) {
	query := `query($accountTag: string!, $bucketName: string!, $datetime_geq: Time!, $datetime_leq: Time!, $limit: int!) {
  viewer {
    accounts(filter: { accountTag: $accountTag }) {
      r2OperationsAdaptiveGroups(
        limit: $limit
        filter: {
          bucketName: $bucketName
          datetime_geq: $datetime_geq
          datetime_leq: $datetime_leq
          actionType: "PutObject"
        }
        orderBy: [dimensions_objectName_ASC]
      ) {
        dimensions {
          objectName
        }
      }
    }
  }
}`
	body, err := json.Marshal(map[string]any{
		"query": query,
		"variables": map[string]any{
			"accountTag":   accountID,
			"bucketName":   bucketName,
			"datetime_geq": from.Format(time.RFC3339),
			"datetime_leq": to.Format(time.RFC3339),
			"limit":        limit,
		},
	})
	if err != nil {
		return nil, err
	}
	req, err := http.NewRequest(http.MethodPost, "https://api.cloudflare.com/client/v4/graphql", strings.NewReader(string(body)))
	if err != nil {
		return nil, err
	}
	req.Header.Set("Authorization", "Bearer "+apiToken)
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", "gftd-deploy/1.0")
	resp, err := (&http.Client{Timeout: 30 * time.Second}).Do(req)
	if err != nil {
		return nil, err
	}
	defer resp.Body.Close()
	if resp.StatusCode != 200 {
		msg, _ := io.ReadAll(resp.Body)
		return nil, fmt.Errorf("Cloudflare GraphQL %d: %s", resp.StatusCode, strings.TrimSpace(string(msg)))
	}
	var payload struct {
		Data struct {
			Viewer struct {
				Accounts []struct {
					R2OperationsAdaptiveGroups []struct {
						Dimensions struct {
							ObjectName string `json:"objectName"`
						} `json:"dimensions"`
					} `json:"r2OperationsAdaptiveGroups"`
				} `json:"accounts"`
			} `json:"viewer"`
		} `json:"data"`
		Errors []struct {
			Message string `json:"message"`
		} `json:"errors"`
	}
	if err := json.NewDecoder(resp.Body).Decode(&payload); err != nil {
		return nil, err
	}
	if len(payload.Errors) > 0 {
		return nil, fmt.Errorf("Cloudflare GraphQL: %s", payload.Errors[0].Message)
	}
	if len(payload.Data.Viewer.Accounts) == 0 {
		return nil, nil
	}
	names := make([]string, 0, len(payload.Data.Viewer.Accounts[0].R2OperationsAdaptiveGroups))
	for _, row := range payload.Data.Viewer.Accounts[0].R2OperationsAdaptiveGroups {
		name := strings.TrimSpace(row.Dimensions.ObjectName)
		if name == "" {
			continue
		}
		names = append(names, name)
	}
	return names, nil
}

// appVersionMeta holds version/lineage metadata injected into Worker vars.
type appVersionMeta struct {
	Version   string
	Template  string
	Source    string
	DeploySHA string
	DeployAt  string
}

// wranglerSharedSecrets returns the canonical list of secrets store bindings.
// All Workers share the same set — single source of truth.
var wranglerSharedSecrets = []struct{ binding, secretName string }{
	{"SS_YATA_S3_KEY_ID", "yata_s3_key_id"},
	{"SS_YATA_S3_SECRET_KEY", "yata_s3_secret_key"},
	{"SS_OPENROUTER_API_KEY", "openrouter_api_key"},
	{"SS_PUBLIC_CLERK_PUBLISHABLE_KEY", "public_clerk_publishable_key"},
	{"SS_CLERK_SECRET_KEY", "clerk_secret_key"},
	{"SS_SIGNING_KEY", "signing_key"},
	{"SS_HUME_API_KEY", "hume_api_key"},
	{"SS_HUME_SECRET_KEY", "hume_secret_key"},
	{"SS_HIGGSFIELD_API_KEY", "higgsfield_api_key"},
	{"SS_HIGGSFIELD_API_SECRET", "higgsfield_api_secret"},
	{"SS_RUNWAY_API_KEY", "runway_api_key"},
	{"SS_EPIDEMIC_SOUND_JWT_1", "epidemic_sound_jwt_1"},
	{"SS_EPIDEMIC_SOUND_JWT_2", "epidemic_sound_jwt_2"},
	{"SS_TURN_KEY_ID", "turn_key_id"},
	{"SS_TURN_KEY_API_TOKEN", "turn_key_api_token"},
	{"SS_CLOUDFLARE_REGISTRAR_API_TOKEN", "cloudflare_registrar_api_token"},
	// yuubin (Web ゆうびん browser automation — login credentials)
	{"SS_WEBYUBIN_USERNAME", "webyubin_username"},
	{"SS_WEBYUBIN_PASSWORD", "webyubin_password"},
	{"SS_WEBYUBIN_PAYMENT_CARD_LAST4", "webyubin_payment_card_last4"},
	// microsoft.etzhayyim.com (Azure app Mail.Send/Mail.ReadWrite — app-only client credentials)
	// Keychain SSoT: gftd.m365 / CLIENT_SECRET. Same Azure app as kaisya-gftd-bot (client 9ad011ba-…).
	// Host-SDK createHostSDK auto-wires createM365Capability when this + M365_TENANT_ID + M365_CLIENT_ID env are all present.
	{"SS_M365_CLIENT_SECRET", "m365_client_secret"},
	// dispatcher.etzhayyim.com internal-trust shared secret (BPMN proxy path).
	// Workers that proxy XRPC to bpmn-dispatcher (animeka, mangaka, open-ossekai, etc.) must
	// attach `x-internal-trust: <this>` header. Reading code: `internalTrustHeader(sdk)` helper
	// pattern, e.g. 60-apps/ai-gftd-project-animeka/.../src/app.ts proxyStage().
	{"DISPATCHER_INTERNAL_SECRET", "dispatcher_internal_secret"},
	// kaisya.etzhayyim.com service-to-service shared secret.
	// microsoft agent → kaisya createTask XRPC. Auth: Authorization: Bearer <key>.
	{"KAISYA_SERVICE_KEY", "kaisya_service_key"},
}

// wranglerConfig holds parameters for wrangler.jsonc generation.
type wranglerConfig struct {
	Name           string                 // Worker name (without "magatama-" prefix)
	Main           string                 // entry point override (default: "src/app.ts")
	Assets         string                 // assets JSON block (empty = no assets)
	Vars           map[string]string      // Worker env vars
	Routes         []string               // route patterns (e.g. "appid.etzhayyim.com/*")
	CompatFlags    []string               // compatibility_flags
	NeedsBrowser   bool                   // include browser binding
	DurableObjects []durableObjectBinding // DO bindings (SQLite backend) + migrations
}

// buildWranglerJSON generates wrangler.jsonc from a wranglerConfig.
// Single source for both single-app and merged Worker configs.
func buildWranglerJSON(wc wranglerConfig) string {
	ssID := secretsStoreID

	// compatibility_flags
	flags := wc.CompatFlags
	if len(flags) == 0 {
		flags = []string{"nodejs_compat", "nodejs_als"}
	}
	flagsJSON, _ := json.Marshal(flags)

	// vars block
	vars := ""
	if len(wc.Vars) > 0 {
		var entries []string
		for k, v := range wc.Vars {
			entries = append(entries, fmt.Sprintf("    %q: %q", k, v))
		}
		sort.Strings(entries)
		vars = "\n  \"vars\": {\n" + strings.Join(entries, ",\n") + "\n  },"
	}

	// secrets
	var secretEntries []string
	for _, s := range wranglerSharedSecrets {
		secretEntries = append(secretEntries, fmt.Sprintf(
			`    { "binding": %q, "store_id": %q, "secret_name": %q }`,
			s.binding, ssID, s.secretName))
	}

	// routes (dedup — CF rejects duplicate patterns with "route already exists")
	var routeEntries []string
	seenRoutes := make(map[string]bool, len(wc.Routes))
	for _, rp := range wc.Routes {
		if rp == "" || seenRoutes[rp] {
			continue
		}
		seenRoutes[rp] = true
		routeEntries = append(routeEntries, fmt.Sprintf(`    { "pattern": %q, "zone_name": "etzhayyim.com" }`, rp))
	}

	// browser binding
	browserBinding := ""
	if wc.NeedsBrowser {
		browserBinding = "\n  \"browser\": { \"binding\": \"HEADLESS_BROWSER\" },"
	}

	// durable_objects + migrations block
	doBlock := ""
	if len(wc.DurableObjects) > 0 {
		var bindings []string
		var newClasses []string
		tag := "v1"
		for _, d := range wc.DurableObjects {
			bindings = append(bindings, fmt.Sprintf(`    { "name": %q, "class_name": %q }`, d.Name, d.ClassName))
			newClasses = append(newClasses, fmt.Sprintf("%q", d.ClassName))
			if d.Tag != "" {
				tag = d.Tag
			}
		}
		doBlock = fmt.Sprintf("\n  \"durable_objects\": {\n    \"bindings\": [\n%s\n    ]\n  },\n  \"migrations\": [\n    { \"tag\": %q, \"new_sqlite_classes\": [%s] }\n  ],",
			strings.Join(bindings, ",\n"), tag, strings.Join(newClasses, ","))
	}

	// ADR-0012: Apps go Path B (Hyperdrive direct via createKyselyDb).
	// GRAPH_QUERY_SERVICE binding is PDS-only and intentionally omitted
	// from app wrangler.jsonc.
	pdsService := strings.TrimSpace(os.Getenv("GFTD_PDS_SERVICE"))
	if pdsService == "" {
		pdsService = "ai-gftd-pds-2603241700"
	}

	mainEntry := wc.Main
	if mainEntry == "" {
		mainEntry = "src/app.ts"
	}

	// Resolve host-sdk alias relative to repo root (20-actors/).
	hostSDKPath := ""
	if root, err := findGitRoot("."); err == nil {
		candidate := filepath.Join(root, "20-actors", "magatama", "sdk", "magatama-host-sdk", "src", "index.ts")
		if _, err := os.Stat(candidate); err == nil {
			hostSDKPath = candidate
		}
	}
	aliasBlock := ""
	if hostSDKPath != "" {
		// Resolve pg package path for Hyperdrive dialect (required by @gftd/magatama-host-sdk)
		pgAlias := ""
		// hostSDKPath ends with .../20-actors/magatama/sdk/magatama-host-sdk/src/index.ts
		// Walk up to repo root (6 levels: index.ts → src → magatama-host-sdk → sdk → magatama → 20-actors → repo)
		root := filepath.Dir(filepath.Dir(filepath.Dir(filepath.Dir(filepath.Dir(filepath.Dir(hostSDKPath))))))
		pgCandidates := []string{
			filepath.Join(root, "node_modules", "pg", "lib", "index.js"),
		}
		// Also find pg via glob for any pnpm version
		matches, _ := filepath.Glob(filepath.Join(root, "node_modules", ".pnpm", "pg@*", "node_modules", "pg", "lib", "index.js"))
		pgCandidates = append(pgCandidates, matches...)
		for _, p := range pgCandidates {
			if _, err := os.Stat(p); err == nil {
				pgAlias = fmt.Sprintf(", \"pg\": %q", p)
				break
			}
		}
		// Resolve @gftd/xrpc subpath aliases (xrpc-client.ts imports @gftd/xrpc/{transport,auth,error,nsid})
		xrpcAlias := ""
		xrpcDir := filepath.Join(root, "10-protocol", "xrpc", "src")
		if _, err := os.Stat(xrpcDir); err == nil {
			xrpcSubpaths := []string{"transport", "auth", "error", "nsid", "encode"}
			for _, sub := range xrpcSubpaths {
				xrpcAlias += fmt.Sprintf(", \"@gftd/xrpc/%s\": %q", sub, filepath.Join(xrpcDir, sub+".ts"))
			}
		}
		// Resolve @cloudflare/puppeteer if present in workspace (optional, only used by browser-automation actors).
		// Exports ESM entry at lib/esm/puppeteer/puppeteer-cloudflare.js (prefer ESM for CF Worker).
		puppeteerAlias := ""
		puppeteerMatches, _ := filepath.Glob(filepath.Join(root, "node_modules", ".pnpm", "@cloudflare+puppeteer@*", "node_modules", "@cloudflare", "puppeteer"))
		for _, p := range puppeteerMatches {
			candidates := []string{
				filepath.Join(p, "lib", "esm", "puppeteer", "puppeteer-cloudflare.js"),
				filepath.Join(p, "lib", "cjs", "puppeteer", "puppeteer-cloudflare.js"),
			}
			for _, c := range candidates {
				if _, err := os.Stat(c); err == nil {
					puppeteerAlias = fmt.Sprintf(", \"@cloudflare/puppeteer\": %q", c)
					break
				}
			}
			if puppeteerAlias != "" {
				break
			}
		}
		aliasBlock = fmt.Sprintf("\n  \"alias\": { \"@gftd/magatama-host-sdk\": %q%s%s%s },", hostSDKPath, pgAlias, xrpcAlias, puppeteerAlias)
	}

	return fmt.Sprintf(`{
  "name": "magatama-%s",
  "main": %q,
  "compatibility_date": "2025-03-17",
  "compatibility_flags": %s,%s%s%s
  "r2_buckets": [
    { "binding": "YATA_R2", "bucket_name": "ai-gftd-cache" },
    { "binding": "CACHE_R2", "bucket_name": "ai-gftd-cache" }
  ],
  "hyperdrive": [
    { "binding": "HYPERDRIVE", "id": "e84c0a2babe44fc7b74818e394b4b896" }
  ],
  "services": [
    { "binding": "PDS_SERVICE", "service": "%s" },
    { "binding": "PDS_RPC", "service": "%s", "entrypoint": "PdsRPC" },
    { "binding": "MURAKUMO_SERVICE", "service": "ai-gftd-murakumo-2603241700" },
    { "binding": "COMFYUI_SERVICE", "service": "ai-gftd-comfyui-2604221600" }
  ],
  "secrets_store_secrets": [
%s
  ],
  "rules": [
    { "type": "CompiledWasm", "globs": ["**/*.wasm"] }
  ],%s%s
  "routes": [
%s
  ]
}
`, wc.Name, mainEntry, string(flagsJSON), aliasBlock, wc.Assets, vars,
		pdsService, pdsService,
		strings.Join(secretEntries, ",\n"),
		browserBinding,
		doBlock,
		strings.Join(routeEntries, ",\n"))
}

// generateWorkerWrangler creates a wrangler.jsonc for Worker mode.
// Architecture: src/app.ts (Hono via magatama-host-sdk) + svelte/build/ (Workers Assets).
func generateWorkerWrangler(appID string, _ string, meta *appVersionMeta, cfg *magatamaJSONLD, compDir string, neededImports ...[]string) string {
	wc := wranglerConfig{
		Name:   appID,
		Main:   "src/app.ts",
		Vars:   map[string]string{},
		Routes: []string{appID + ".etzhayyim.com/*"},
	}

	// Add vanity domain route: prefer explicit routes from magatama.jsonld, fall back to project name
	if cfg != nil && len(cfg.Routes) > 0 && cfg.Routes[0].Host != "" {
		// Use explicit host(s) from magatama.jsonld routes
		for _, r := range cfg.Routes {
			if r.Host != "" {
				wc.Routes = append(wc.Routes, r.Host+"/*")
			}
		}
	} else if cfg != nil && cfg.Project != "" && cfg.Project != appID && cfg.Name == cfg.Project {
		// Fall back to project-based vanity route only when app name matches project
		// (prevents multi-app projects like states from all claiming the same vanity route)
		wc.Routes = append(wc.Routes, cfg.Project+".etzhayyim.com/*")
	}

	// Browser automation detection
	if len(neededImports) > 0 {
		for _, imp := range neededImports[0] {
			if imp == "magatama:browser/automation@1.0.0" {
				wc.NeedsBrowser = true
				break
			}
		}
	}

	// Durable Object bindings from magatama.jsonld `component.durableObjects`
	if cfg != nil && cfg.Component != nil && len(cfg.Component.DurableObjects) > 0 {
		wc.DurableObjects = cfg.Component.DurableObjects
	}

	// Assets block — Svelte CSR build output (skip for yoro = zero UI)
	if cfg.UITypeOrDefault() != "yoro" {
		wc.Assets = `
  "assets": {
    "directory": "./svelte/build",
    "binding": "ASSETS",
    "html_handling": "auto-trailing-slash",
    "not_found_handling": "single-page-application"
  },`
	}

	// Inject component.env
	if cfg != nil && cfg.Component != nil {
		for k, v := range cfg.Component.Env {
			wc.Vars[k] = v
		}
	}
	// Version metadata
	if meta != nil {
		wc.Vars["APP_VERSION"] = meta.Version
		wc.Vars["APP_TEMPLATE"] = meta.Template
		wc.Vars["APP_SOURCE"] = meta.Source
		wc.Vars["APP_DEPLOY_SHA"] = meta.DeploySHA
		wc.Vars["APP_DEPLOY_AT"] = meta.DeployAt
	}
	// magatama.jsonld metadata for /_app/meta
	if cfg != nil {
		wc.Vars["APP_NANOID"] = cfg.Nanoid
		wc.Vars["APP_FRAMEWORK"] = cfg.FrameworkOrDefault()
		if cfg.Profile != nil {
			wc.Vars["APP_DISPLAY_NAME"] = cfg.Profile.DisplayName
			wc.Vars["APP_DESCRIPTION"] = cfg.Profile.Description
		}
		// ADR-2604261000 Step 5: APP_ACTOR_HANDLE for MCP registry actor_did default.
		// host-sdk mcp-registry-loader keys vertex_mcp_tool_def rows by
		// did:web:{actorSlug}.etzhayyim.com (NSID 4th segment). When mcpRegistry is
		// enabled but actorDid not set explicitly, the loader prefers
		// did:web:{APP_ACTOR_HANDLE}.etzhayyim.com over did:web:{APP_NANOID}.etzhayyim.com.
		// Derivation order:
		//   1. magatama.jsonld profile.handle
		//   2. component dir slug from `ai-gftd-wasm-{slug}-{nanoid}`
		//   3. (omit env — loader falls back to APP_NANOID)
		if h := actorHandleFromCfg(cfg, compDir); h != "" {
			wc.Vars["APP_ACTOR_HANDLE"] = h
		}
		rawUI := cfg.UIType
		if rawUI == "" {
			rawUI = "appview"
		}
		wc.Vars["APP_UI_TYPE"] = rawUI
		wc.Vars["APP_PERFORMER_TYPE"] = cfg.PerformerType
		// autoCrud detection: SDK handles CRUD + heartbeat + governance at runtime
		if cfg.UsesAutoCrud(compDir) {
			wc.Vars["APP_AUTO_CRUD"] = "true"
		}
		if cfg.Profile != nil {
			if capsJSON, err := json.Marshal(cfg.Profile.Capabilities); err == nil {
				wc.Vars["APP_CAPABILITIES"] = string(capsJSON)
			}
		}
		if rawUI == "iframe" || rawUI == "game" || rawUI == "fullapp" || rawUI == "full" || rawUI == "appview" {
			eurl := "https://" + cfg.Nanoid + ".etzhayyim.com/?embed=1"
			if cfg.EmbedUrl != "" {
				eurl = cfg.EmbedUrl
			}
			wc.Vars["APP_EMBED_URL"] = eurl
		}
	}
	// interfaces.requires
	if cfg != nil && cfg.Interfaces != nil && len(cfg.Interfaces.Requires) > 0 {
		reqJSON, _ := json.Marshal(cfg.Interfaces.Requires)
		wc.Vars["INTERFACES_REQUIRES"] = string(reqJSON)
	}
	// Signing public key
	if v := os.Getenv("GFTD_SIGNING_PUBLIC_KEY"); v != "" {
		wc.Vars["SIGNING_PUBLIC_KEY"] = v
	} else if v := os.Getenv("SIGNING_PUBLIC_KEY"); v != "" {
		wc.Vars["SIGNING_PUBLIC_KEY"] = v
	}

	return buildWranglerJSON(wc)
}
