#!/usr/bin/env python3
import argparse
import json
import random
import re
import string
import subprocess
import unicodedata
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WASM_ROOT = PROJECT_ROOT / "wasm"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Generate ADM2 multi-agent components (grpc+mcp+messaging+kv)."
    )
    p.add_argument(
        "--targets",
        default=str(PROJECT_ROOT / "tmp" / "260303-adm2-pilot-10-targets.jsonl"),
        help="JSONL file from adm2 target selection",
    )
    p.add_argument("--limit", type=int, default=0, help="Max components to generate (0=all)")
    p.add_argument("--go-mod-tidy", action="store_true", help="Run go mod tidy per generated component")
    return p.parse_args()


def nanoid8() -> str:
    chars = string.ascii_lowercase + string.digits
    return "".join(random.choice(chars) for _ in range(8))


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value or "unknown"


def esc_go(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def safe_component_slug(slug: str) -> str:
    return re.sub(r"-dst-([0-9]+)", lambda m: f"-dst-n{m.group(1)}", slug)


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def render_main_go(
    slug: str,
    entity_name: str,
    country_code_l: str,
    country_name: str,
    component_nanoid: str,
) -> str:
    component_name = f"{slug}-component"
    division_id = slug.split("-dst-", 1)[-1]
    escaped_entity = esc_go(entity_name)
    escaped_country = esc_go(country_name)
    escaped_div = esc_go(division_id)
    escaped_slug = esc_go(slug)

    return f'''package main

import (
\t"encoding/json"
\t"fmt"
\t"net/http"
\t"strings"
\t"sync"
\t"time"

\tspinhttp "github.com/spinframework/spin-go-sdk/v2/http"
\t"github.com/spinframework/spin-go-sdk/v2/kv"
)

const (
\tcomponentName   = "{component_name}"
\tentityName      = "{escaped_entity}"
\tcountryCode     = "{country_code_l}"
\tcountryName     = "{escaped_country}"
\tcomponentNanoID = "{component_nanoid}"
\tbucketName      = "default"
)

type divisionInfo struct {{
\tID           string `json:"id"`
\tName         string `json:"name"`
\tType         string `json:"type"`
\tPopulation   int64  `json:"population"`
\tHeadquarters string `json:"headquarters"`
}}

type componentMessage struct {{
\tID        string `json:"id"`
\tFrom      string `json:"from"`
\tBody      string `json:"body"`
\tCreatedAt string `json:"createdAt"`
}}

type stateStore struct {{
\tkv *kv.Store
\tmu sync.RWMutex
}}

var (
\tstoreOnce sync.Once
\tstoreInst *stateStore
\tstoreErr  error
)

func getStore() (*stateStore, error) {{
\tstoreOnce.Do(func() {{
\t\tkvs, err := kv.OpenStore(bucketName)
\t\tif err != nil {{
\t\t\tstoreErr = err
\t\t\treturn
\t\t}}
\t\tstoreInst = &stateStore{{kv: kvs}}
\t\tstoreErr = storeInst.seedData()
\t}})
\treturn storeInst, storeErr
}}

func (s *stateStore) seedData() error {{
\tconst key = "division:default"
\texists, err := s.kv.Exists(key)
\tif err != nil {{
\t\treturn err
\t}}
\tif exists {{
\t\treturn nil
\t}}
\tinfo := divisionInfo{{
\t\tID:           "{escaped_div}",
\t\tName:         entityName,
\t\tType:         "Administrative Unit (ADM2)",
\t\tPopulation:   0,
\t\tHeadquarters: "Unknown",
\t}}
\tpayload, err := json.Marshal(info)
\tif err != nil {{
\t\treturn err
\t}}
\treturn s.kv.Set(key, payload)
}}

func (s *stateStore) getDefaultDivision() (divisionInfo, error) {{
\ts.mu.RLock()
\tdefer s.mu.RUnlock()
\tpayload, err := s.kv.Get("division:default")
\tif err != nil {{
\t\treturn divisionInfo{{}}, err
\t}}
\tvar info divisionInfo
\tif err := json.Unmarshal(payload, &info); err != nil {{
\t\treturn divisionInfo{{}}, err
\t}}
\treturn info, nil
}}

func (s *stateStore) appendMessage(msg componentMessage) error {{
\tkey := "messages:" + msg.ID
\tpayload, err := json.Marshal(msg)
\tif err != nil {{
\t\treturn err
\t}}
\treturn s.kv.Set(key, payload)
}}

func init() {{
\tspinhttp.Handle(handleRequest)
}}

func handleRequest(w http.ResponseWriter, r *http.Request) {{
\torigin := r.Header.Get("Origin")
\tif origin != "" && (strings.HasSuffix(origin, ".etzhayyim.com") || strings.HasPrefix(origin, "http://localhost:")) {{
\t\tw.Header().Set("Access-Control-Allow-Origin", origin)
\t\tw.Header().Set("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
\t\tw.Header().Set("Access-Control-Allow-Headers", "Content-Type")
\t}}
\tif r.Method == http.MethodOptions {{
\t\tw.WriteHeader(http.StatusNoContent)
\t\treturn
\t}}

\tpath := normalizePath(r.URL.Path)
\tswitch {{
\tcase path == "/healthz" && r.Method == http.MethodGet:
\t\trespondJSON(w, http.StatusOK, map[string]any{{"status": "ok"}})
\t\treturn
\tcase path == "/.well-known/agent.json" && r.Method == http.MethodGet:
\t\trespondJSON(w, http.StatusOK, agentManifest())
\t\treturn
\tcase path == "/api/messages" && r.Method == http.MethodGet:
\t\trespondJSON(w, http.StatusOK, agentProfile())
\t\treturn
\tcase path == "/api/messages/send" && r.Method == http.MethodPost:
\t\thandleMessage(w, r)
\t\treturn
\tcase path == "/api/grpc" && r.Method == http.MethodPost:
\t\thandleMCP(w, r)
\t\treturn
\tdefault:
\t\trespondJSON(w, http.StatusOK, getOrganizationInfo())
\t\treturn
\t}}
}}

func normalizePath(path string) string {{
\tif len(path) > 9 && path[0] == '/' && path[9] == '/' {{
\t\treturn path[9:]
\t}}
\treturn path
}}

func handleMCP(w http.ResponseWriter, r *http.Request) {{
\tvar req struct {{
\t\tJSONRPC string          `json:"jsonrpc"`
\t\tMethod  string          `json:"method"`
\t\tParams  json.RawMessage `json:"params"`
\t\tID      any             `json:"id"`
\t}}
\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
\t\tsendMCPError(w, -32700, "Parse error", req.ID)
\t\treturn
\t}}

\tswitch req.Method {{
\tcase "initialize":
\t\tsendMCPResult(w, req.ID, map[string]any{{
\t\t\t"protocolVersion": "2024-11-05",
\t\t\t"serverInfo":      map[string]any{{"name": componentName, "version": "0.1.0"}},
\t\t}})
\tcase "listTools":
\t\tsendMCPResult(w, req.ID, map[string]any{{
\t\t\t"tools": []map[string]any{{
\t\t\t\t{{
\t\t\t\t\t"name":        "get_division_info",
\t\t\t\t\t"description": "Get ADM2 division metadata from KV store",
\t\t\t\t\t"inputSchema": map[string]any{{"type": "object", "properties": map[string]any{{}}}},
\t\t\t\t}},
\t\t\t\t{{
\t\t\t\t\t"name":        "get_agent_profile",
\t\t\t\t\t"description": "Get agent profile and supported protocols",
\t\t\t\t\t"inputSchema": map[string]any{{"type": "object", "properties": map[string]any{{}}}},
\t\t\t\t}},
\t\t\t\t{{
\t\t\t\t\t"name":        "send_message",
\t\t\t\t\t"description": "Send a message and persist to KV",
\t\t\t\t\t"inputSchema": map[string]any{{
\t\t\t\t\t\t"type": "object",
\t\t\t\t\t\t"properties": map[string]any{{
\t\t\t\t\t\t\t"from": map[string]any{{"type": "string"}},
\t\t\t\t\t\t\t"body": map[string]any{{"type": "string"}},
\t\t\t\t\t\t}},
\t\t\t\t\t\t"required": []string{{"from", "body"}},
\t\t\t\t\t}},
\t\t\t\t}},
\t\t\t}},
\t\t}})
\tcase "callTool":
\t\thandleCallTool(w, req.ID, req.Params)
\tdefault:
\t\tsendMCPError(w, -32601, "Method not found", req.ID)
\t}}
}}

func handleCallTool(w http.ResponseWriter, id any, paramsRaw json.RawMessage) {{
\tvar p struct {{
\t\tName      string          `json:"name"`
\t\tArguments json.RawMessage `json:"arguments"`
\t}}
\t_ = json.Unmarshal(paramsRaw, &p)

\ts, err := getStore()
\tif err != nil {{
\t\tsendMCPError(w, -32000, "Storage error", id)
\t\treturn
\t}}

\tswitch p.Name {{
\tcase "get_division_info":
\t\tinfo, err := s.getDefaultDivision()
\t\tif err != nil {{
\t\t\tsendMCPError(w, -32000, "Storage read error", id)
\t\t\treturn
\t\t}}
\t\tsendMCPResult(w, id, map[string]any{{
\t\t\t"content": []map[string]any{{{{"type": "text", "text": toJSON(info)}}}},
\t\t}})
\tcase "get_agent_profile":
\t\tsendMCPResult(w, id, map[string]any{{
\t\t\t"content": []map[string]any{{{{"type": "text", "text": toJSON(agentProfile())}}}},
\t\t}})
\tcase "send_message":
\t\tvar args struct {{
\t\t\tFrom string `json:"from"`
\t\t\tBody string `json:"body"`
\t\t}}
\t\tif err := json.Unmarshal(p.Arguments, &args); err != nil {{
\t\t\tsendMCPError(w, -32602, "Invalid params", id)
\t\t\treturn
\t\t}}
\t\tmsg := componentMessage{{
\t\t\tID:        fmt.Sprintf("%d", time.Now().UnixNano()),
\t\t\tFrom:      strings.TrimSpace(args.From),
\t\t\tBody:      strings.TrimSpace(args.Body),
\t\t\tCreatedAt: time.Now().UTC().Format(time.RFC3339),
\t\t}}
\t\tif msg.From == "" || msg.Body == "" {{
\t\t\tsendMCPError(w, -32602, "from/body required", id)
\t\t\treturn
\t\t}}
\t\tif err := s.appendMessage(msg); err != nil {{
\t\t\tsendMCPError(w, -32000, "Storage write error", id)
\t\t\treturn
\t\t}}
\t\tsendMCPResult(w, id, map[string]any{{
\t\t\t"content": []map[string]any{{{{"type": "text", "text": toJSON(map[string]any{{"accepted": true, "messageId": msg.ID}})}}}},
\t\t}})
\tdefault:
\t\tsendMCPError(w, -32601, "Tool not found", id)
\t}}
}}

func handleMessage(w http.ResponseWriter, r *http.Request) {{
\ts, err := getStore()
\tif err != nil {{
\t\trespondJSON(w, http.StatusInternalServerError, map[string]any{{"error": "storage unavailable"}})
\t\treturn
\t}}

\tvar req struct {{
\t\tFrom string `json:"from"`
\t\tBody string `json:"body"`
\t}}
\tif err := json.NewDecoder(r.Body).Decode(&req); err != nil {{
\t\trespondJSON(w, http.StatusBadRequest, map[string]any{{"error": "invalid json"}})
\t\treturn
\t}}
\tif strings.TrimSpace(req.From) == "" || strings.TrimSpace(req.Body) == "" {{
\t\trespondJSON(w, http.StatusBadRequest, map[string]any{{"error": "from/body required"}})
\t\treturn
\t}}

\tmsg := componentMessage{{
\t\tID:        fmt.Sprintf("%d", time.Now().UnixNano()),
\t\tFrom:      strings.TrimSpace(req.From),
\t\tBody:      strings.TrimSpace(req.Body),
\t\tCreatedAt: time.Now().UTC().Format(time.RFC3339),
\t}}
\tif err := s.appendMessage(msg); err != nil {{
\t\trespondJSON(w, http.StatusInternalServerError, map[string]any{{"error": "storage write failed"}})
\t\treturn
\t}}

\trespondJSON(w, http.StatusAccepted, map[string]any{{
\t\t"status":      "accepted",
\t\t"messageId":   msg.ID,
\t\t"storedInKV":  true,
\t\t"receiverSlug": "{escaped_slug}",
\t}})
}}

func respondJSON(w http.ResponseWriter, code int, body any) {{
\tw.Header().Set("Content-Type", "application/json")
\tw.WriteHeader(code)
\t_ = json.NewEncoder(w).Encode(body)
}}

func sendMCPResult(w http.ResponseWriter, id any, result any) {{
\trespondJSON(w, http.StatusOK, map[string]any{{"jsonrpc": "2.0", "result": result, "id": id}})
}}

func sendMCPError(w http.ResponseWriter, code int, msg string, id any) {{
\trespondJSON(w, http.StatusOK, map[string]any{{"jsonrpc": "2.0", "error": map[string]any{{"code": code, "message": msg}}, "id": id}})
}}

func toJSON(v any) string {{
\tb, _ := json.MarshalIndent(v, "", "  ")
\treturn string(b)
}}

func agentProfile() map[string]any {{
\treturn map[string]any{{
\t\t"name":               componentName,
\t\t"description":        "ADM2 government messaging endpoint",
\t\t"url":                "https://" + componentNanoID + ".etzhayyim.com/api/grpc",
\t\t"messageEndpoint":    "https://" + componentNanoID + ".etzhayyim.com/api/messages/send",
\t\t"supportedProtocols": []string{{"mcp/1.0", "grpc"}},
\t\t"skills": []map[string]any{{
\t\t\t{{"name": "get_division_info", "description": "Read division profile from KV"}},
\t\t\t{{"name": "send_message", "description": "Persist message to KV"}},
\t\t}},
\t}}
}}

func agentManifest() map[string]any {{
\treturn map[string]any{{
\t\t"name":        "@etzhayyim-project-states/{escaped_slug}-agent",
\t\t"description": "Agent manifest for {escaped_slug}",
\t\t"url":         "https://" + componentNanoID + ".etzhayyim.com/api/grpc",
\t\t"version":     "1.0.0",
\t\t"provider": map[string]any{{
\t\t\t"service": "etzhayyim",
\t\t\t"url":     "https://kyber-services.etzhayyim.com",
\t\t}},
\t\t"supportedProtocols": []string{{"mcp/1.0", "grpc"}},
\t\t"skills": []map[string]any{{
\t\t\t{{"name": "get_division_info", "description": "Get administrative division profile"}},
\t\t\t{{"name": "send_message", "description": "Send a message to this ADM2 agent"}},
\t\t\t{{"name": "health", "description": "Get health and metadata"}},
\t\t}},
\t}}
}}

func getOrganizationInfo() map[string]any {{
\treturn map[string]any{{
\t\t"name":        entityName,
\t\t"country":     countryName,
\t\t"countryCode": countryCode,
\t\t"component":   componentName,
\t\t"nanoid":      componentNanoID,
\t\t"type":        "government-adm2-district",
\t\t"endpoints": map[string]string{{
\t\t\t"grpc":     "https://" + componentNanoID + ".etzhayyim.com/api/grpc",
\t\t\t"messages": "https://" + componentNanoID + ".etzhayyim.com/api/messages/send",
\t\t}},
\t\t"protocol":    "MCP JSON-RPC 2.0",
\t\t"description": "ADM2 municipal interface for " + countryName,
\t\t"capabilities": []map[string]any{{
\t\t\t{{"id": "regional-administration", "name": "Regional Administration"}},
\t\t\t{{"id": "policy-implementation", "name": "Policy Implementation"}},
\t\t\t{{"id": "multi-agent-collaboration", "name": "Multi-agent Collaboration"}},
\t\t}},
\t}}
}}

func main() {{}}
'''


def render_spin_toml(slug: str) -> str:
    safe_slug = safe_component_slug(slug)
    component_id = f"{safe_slug}-component"
    wasm_name = f"build/{component_id.replace('-', '_')}_s.wasm"
    return f'''spin_manifest_version = 2

[application]
name = "{component_id}"
version = "0.1.0"

[[trigger.http]]
component = "{component_id}"
route = "/..."

[component."{component_id}"]
source = "{wasm_name}"
allowed_outbound_hosts = ["http://*", "https://*"]
key_value_stores = ["default"]

[component."{component_id}".build]
command = "TINYGOROOT=$HOME/sdk/tinygo-0.35.0 GOTOOLCHAIN=local GOROOT=$HOME/sdk/go1.23.6 PATH=$HOME/sdk/go1.23.6/bin:$HOME/sdk/tinygo-0.35.0/bin:$PATH tinygo build -target=wasip1 -gc=leaking -buildmode=c-shared -no-debug -o {wasm_name} ."
watch = ["**/*.go", "go.mod"]
'''


def render_go_mod(slug: str) -> str:
    return f'''module github.com/etzhayyim-ai/performer-sys-etzhayyim-actors-pba7d22f-{slug}

go 1.23

require github.com/spinframework/spin-go-sdk/v2 v2.2.1
'''


def render_world_wit(slug: str) -> str:
    return f'''package etzhayyim:{slug};

world component {{
    include etzhayyim:platform/etzhayyim-mcp@0.1.0;
    import wasi:keyvalue/store@0.2.0-draft;
}}
'''


def render_spinapp_yaml(slug: str) -> str:
    spin_name = f"{slug}-spin"
    label_name = spin_name[:63].rstrip("-")
    return f'''apiVersion: core.spinkube.dev/v1alpha1
kind: SpinApp
metadata:
  name: {spin_name}
  namespace: spinkube
  labels:
    app.kubernetes.io/name: {label_name}
    app.kubernetes.io/managed-by: adm2-multi-agent-generator
spec:
  image: ghcr.io/etzhayyim/{slug}-component:spinkube-0.1.0
  replicas: 1
  executor: containerd-shim-spin-nats
  imagePullSecrets:
    - name: ghcr-pull-secret
'''


def render_jsonld(entity_name: str, iso_u: str, nanoid: str) -> str:
    payload = {
        "@context": "https://schema.org/",
        "@type": "GovernmentOrganization",
        "name": entity_name,
        "description": f"ADM2 municipal interface with grpc/mcp/messaging for {entity_name}.",
        "identifier": nanoid,
        "address": {"@type": "PostalAddress", "addressCountry": iso_u},
        "url": f"https://{nanoid}.etzhayyim.com",
        "mainEntityOfPage": f"https://{nanoid}.etzhayyim.com/api/grpc",
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def render_agent_json(slug: str, nanoid: str) -> str:
    payload = {
        "name": f"@etzhayyim-project-states/{slug}-agent",
        "description": f"Agent manifest for {slug}.",
        "url": f"https://{nanoid}.etzhayyim.com/api/grpc",
        "version": "1.0.0",
        "provider": {"service": "etzhayyim", "url": "https://kyber-services.etzhayyim.com"},
        "supportedProtocols": ["mcp/1.0", "grpc"],
        "skills": [
            {"name": "get_division_info", "description": "Read ADM2 division metadata"},
            {"name": "send_message", "description": "Persist and relay messages"},
            {"name": "health", "description": "Get health/metadata for this performer"},
            {"name": slug, "description": "ADM2 municipal government performer"},
        ],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def main() -> int:
    args = parse_args()
    targets_path = Path(args.targets)
    if not targets_path.is_absolute():
        targets_path = PROJECT_ROOT / targets_path
    if not targets_path.exists():
        raise SystemExit(f"targets not found: {targets_path}")

    targets = []
    for line in targets_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        targets.append(json.loads(line))

    generated = 0
    skipped = 0
    for row in targets:
        if args.limit > 0 and generated >= args.limit:
            break

        slug = row.get("suggested_slug", "").strip()
        if not slug or "-dst-" not in slug:
            skipped += 1
            print(f"skip invalid slug: {slug!r}")
            continue

        iso_u = (row.get("iso") or "").upper()
        iso_l = iso_u.lower()
        country = (row.get("country") or iso_u).strip()
        shape_name = (row.get("pilot_shape_name") or row.get("shape_name") or slug).strip()
        entity_name = f"{shape_name} Municipal Government"

        component_dir = WASM_ROOT / f"etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-{slug}"
        if component_dir.exists():
            skipped += 1
            print(f"skip exists: {component_dir.name}")
            continue

        nanoid = nanoid8()

        write(component_dir / "main.go", render_main_go(slug, entity_name, iso_l, country, nanoid))
        write(component_dir / "go.mod", render_go_mod(slug))
        write(component_dir / "spin.toml", render_spin_toml(slug))
        write(component_dir / "wit" / "world.wit", render_world_wit(slug))
        write(component_dir / "k8s" / "spinapp.yaml", render_spinapp_yaml(slug))
        write(component_dir / f"{slug}.jsonld", render_jsonld(entity_name, iso_u, nanoid))
        write(component_dir / "agent.json", render_agent_json(slug, nanoid))

        if args.go_mod_tidy:
            subprocess.run(["go", "mod", "tidy"], cwd=component_dir, check=False)

        generated += 1
        print(f"generated[{generated}]: {component_dir.name}")

    print(f"summary generated={generated} skipped={skipped} targets={len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
