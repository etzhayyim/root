package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"time"
)

type gftdHook struct {
	Name       string            `json:"name,omitempty"`
	Kind       string            `json:"kind,omitempty"`
	Events     []string          `json:"events,omitempty"`
	URL        string            `json:"url,omitempty"`
	Method     string            `json:"method,omitempty"`
	Headers    map[string]string `json:"headers,omitempty"`
	AuthEnv    string            `json:"auth_env,omitempty"`
	AuthScheme string            `json:"auth_scheme,omitempty"`
	TimeoutSec int               `json:"timeout_sec,omitempty"`
	Disabled   bool              `json:"disabled,omitempty"`
}

type hookOptions struct {
	Event      string
	SmokeURL   string
	CachePurge hookCachePurge `json:"cache_purge,omitempty"`
}

type hookEnvelope struct {
	Schema      string         `json:"schema"`
	GeneratedAt string         `json:"generated_at"`
	Event       string         `json:"event"`
	App         hookApp        `json:"app"`
	Artifacts   hookArtifacts  `json:"artifacts"`
	Context     hookContext    `json:"context"`
	Cache       hookCachePurge `json:"cache,omitempty"`
}

type hookApp struct {
	Name      string `json:"name"`
	Nanoid    string `json:"nanoid,omitempty"`
	Project   string `json:"project,omitempty"`
	AppID     string `json:"app_id"`
	Org       string `json:"org,omitempty"`
	Runtime   string `json:"runtime,omitempty"`
	Type      string `json:"type,omitempty"`
	SourceDir string `json:"source_dir"`
}

type hookArtifacts struct {
	SmokeURL string `json:"smoke_url,omitempty"`
}

type hookContext struct {
	GitRoot        string `json:"git_root,omitempty"`
	RelativeDir    string `json:"relative_dir,omitempty"`
	MagatamaJSONLD bool   `json:"magatama_jsonld"`
}

type hookCachePurge struct {
	URLs      []string `json:"urls,omitempty"`
	Status    string   `json:"status,omitempty"`
	Message   string   `json:"message,omitempty"`
	PurgedAt  string   `json:"purged_at,omitempty"`
	Provider  string   `json:"provider,omitempty"`
	ZoneID    string   `json:"zone_id,omitempty"`
	Attempted bool     `json:"attempted,omitempty"`
}

func runConfiguredHooks(cfg *magatamaJSONLD, compDir string, opts hookOptions) error {
	if cfg == nil || len(cfg.Hooks) == 0 {
		return nil
	}

	envelope, err := buildHookEnvelope(cfg, compDir, opts)
	if err != nil {
		return err
	}

	for _, hook := range cfg.Hooks {
		if hook.Disabled {
			continue
		}
		if !hookWantsEvent(hook, opts.Event) {
			continue
		}
		if err := dispatchHook(hook, envelope); err != nil {
			return err
		}
	}

	return nil
}

func hookWantsEvent(hook gftdHook, event string) bool {
	if len(hook.Events) == 0 {
		return true
	}
	for _, candidate := range hook.Events {
		if candidate == event {
			return true
		}
	}
	return false
}

func buildHookEnvelope(cfg *magatamaJSONLD, compDir string, opts hookOptions) (*hookEnvelope, error) {
	appID := cfg.AppID()
	envelope := &hookEnvelope{
		Schema:      "gftd:wproto/hook-envelope@v1",
		GeneratedAt: time.Now().UTC().Format(time.RFC3339),
		Event:       opts.Event,
		App: hookApp{
			Name:      cfg.Name,
			Nanoid:    cfg.Nanoid,
			Project:   cfg.Project,
			AppID:     appID,
			Org:       cfg.Org,
			Runtime:   cfg.RuntimeOrDefault(),
			Type:      cfg.RuntimeType,
			SourceDir: compDir,
		},
		Artifacts: hookArtifacts{
			SmokeURL: opts.SmokeURL,
		},
		Context: hookContext{
			MagatamaJSONLD: fileExists(filepath.Join(compDir, "magatama.jsonld")),
		},
		Cache: opts.CachePurge,
	}

	if gitRoot, err := findGitRoot(compDir); err == nil {
		envelope.Context.GitRoot = gitRoot
		if rel, err := filepath.Rel(gitRoot, compDir); err == nil {
			envelope.Context.RelativeDir = rel
		}
	}

	return envelope, nil
}

func fileExists(path string) bool {
	_, err := os.Stat(path)
	return err == nil
}

func fileSHA256(path string) (string, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", err
	}
	defer f.Close()
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", err
	}
	return hex.EncodeToString(h.Sum(nil)), nil
}

func dispatchHook(hook gftdHook, envelope *hookEnvelope) error {
	kind := hook.Kind
	if kind == "" {
		kind = "http"
	}
	switch kind {
	case "http":
		return dispatchHTTPHook(hook, envelope)
	default:
		return fmt.Errorf("unsupported hook kind %q", hook.Kind)
	}
}

func dispatchHTTPHook(hook gftdHook, envelope *hookEnvelope) error {
	if hook.URL == "" {
		return fmt.Errorf("hook %q: url is required", hook.Name)
	}

	method := hook.Method
	if method == "" {
		method = http.MethodPost
	}

	body, err := json.Marshal(envelope)
	if err != nil {
		return fmt.Errorf("hook %q: marshal payload: %w", hook.Name, err)
	}

	timeout := time.Duration(hook.TimeoutSec) * time.Second
	if timeout <= 0 {
		timeout = 15 * time.Second
	}
	client := &http.Client{Timeout: timeout}

	req, err := http.NewRequest(method, hook.URL, bytes.NewReader(body))
	if err != nil {
		return fmt.Errorf("hook %q: build request: %w", hook.Name, err)
	}
	req.Header.Set("Content-Type", "application/json")
	for k, v := range hook.Headers {
		req.Header.Set(k, v)
	}
	if hook.AuthEnv != "" {
		token := os.Getenv(hook.AuthEnv)
		if token == "" {
			return fmt.Errorf("hook %q: auth env %q is empty", hook.Name, hook.AuthEnv)
		}
		scheme := hook.AuthScheme
		if scheme == "" {
			scheme = "Bearer"
		}
		req.Header.Set("Authorization", scheme+" "+token)
	}

	resp, err := client.Do(req)
	if err != nil {
		return fmt.Errorf("hook %q: request failed: %w", hook.Name, err)
	}
	defer resp.Body.Close()

	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		return fmt.Errorf("hook %q: unexpected HTTP %d from %s", hook.Name, resp.StatusCode, hook.URL)
	}

	fmt.Fprintf(os.Stderr, "==> hook %s: %s %s\n", hook.NameOrDefault(), method, hook.URL)
	return nil
}

func (h gftdHook) NameOrDefault() string {
	if h.Name != "" {
		return h.Name
	}
	if h.Kind != "" {
		return h.Kind
	}
	return "hook"
}
