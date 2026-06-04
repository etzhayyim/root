#!/usr/bin/env python3
"""Generate L1 government organization components for countries with weak org coverage."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
WASM_DIR = ROOT / "projects/etzhayyim-project-states/wasm"
DIR_PREFIX = "etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-org-gov-"

L1_ORGS = [
    {
        "slug": "executive",
        "label": "Executive Office",
        "description": "Coordinates the head of government, cabinet, and national executive decisions.",
        "type": "executive",
        "suffix": "e3x4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "finance",
        "label": "Ministry of Finance",
        "description": "Manages treasury, budget, taxation, and public finance policy.",
        "type": "economic-affairs",
        "suffix": "f3n4",
        "world": "etzhayyim-gov-economic",
    },
    {
        "slug": "foreign",
        "label": "Ministry of Foreign Affairs",
        "description": "Leads foreign policy, diplomacy, and treaty relations.",
        "type": "general-public-services",
        "suffix": "f3a4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "interior",
        "label": "Ministry of Interior",
        "description": "Oversees internal administration, civil protection, and home affairs.",
        "type": "general-public-services",
        "suffix": "i3n4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "justice",
        "label": "Ministry of Justice",
        "description": "Administers justice policy, legal affairs, and rule-of-law operations.",
        "type": "public-order-safety",
        "suffix": "j3u4",
        "world": "etzhayyim-gov-public-order",
    },
    {
        "slug": "leg-lower",
        "label": "Lower House of Parliament",
        "description": "Represents the primary legislative chamber of the national parliament.",
        "type": "general-public-services",
        "suffix": "l3l4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "leg-upper",
        "label": "Upper House of Parliament",
        "description": "Represents the secondary legislative chamber or senate of the national parliament.",
        "type": "general-public-services",
        "suffix": "l3u4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "supreme-court",
        "label": "Supreme Court",
        "description": "Serves as the highest national court for final judicial review.",
        "type": "public-order-safety",
        "suffix": "s3c4",
        "world": "etzhayyim-gov-public-order",
    },
    {
        "slug": "prosecutor",
        "label": "Office of the Prosecutor General",
        "description": "Leads national prosecution and state representation in criminal matters.",
        "type": "public-order-safety",
        "suffix": "p3g4",
        "world": "etzhayyim-gov-public-order",
    },
    {
        "slug": "police",
        "label": "National Police",
        "description": "Provides national policing, law enforcement, and public safety operations.",
        "type": "public-order-safety",
        "suffix": "p3o4",
        "world": "etzhayyim-gov-public-order",
    },
    {
        "slug": "defense",
        "label": "Ministry of Defence",
        "description": "Sets defence policy and oversees military administration.",
        "type": "defence",
        "suffix": "d3e4",
        "world": "etzhayyim-gov-defence",
    },
    {
        "slug": "joint-staff",
        "label": "Joint Staff Headquarters",
        "description": "Coordinates operational command across the armed forces.",
        "type": "defence",
        "suffix": "j3s4",
        "world": "etzhayyim-gov-defence",
    },
    {
        "slug": "election",
        "label": "Election Commission",
        "description": "Administers national elections, ballots, and electoral oversight.",
        "type": "general-public-services",
        "suffix": "e3c4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "audit",
        "label": "National Audit Office",
        "description": "Audits public finances, compliance, and state accountability.",
        "type": "general-public-services",
        "suffix": "a3d4",
        "world": "etzhayyim-gov-general",
    },
    {
        "slug": "state-generic",
        "label": "State Administration",
        "description": "Provides a generic state administration facade for cross-government coordination.",
        "type": "general-public-services",
        "suffix": "s3g4",
        "world": "etzhayyim-gov-general",
    },
]


def parse_existing() -> dict[str, dict[str, set[str] | int]]:
    countries: dict[str, dict[str, set[str] | int]] = {}
    for entry in sorted(WASM_DIR.iterdir()):
        if not entry.is_dir() or not entry.name.startswith(DIR_PREFIX):
            continue
        short = entry.name.removeprefix(DIR_PREFIX)
        parts = short.split("-")
        if len(parts) < 2:
            continue
        iso = parts[0]
        if not re.fullmatch(r"[a-z]{3}", iso):
            continue
        countries.setdefault(iso, {"total": 0, "dst": 0, "orgs": set()})
        countries[iso]["total"] = int(countries[iso]["total"]) + 1
        if "-dst-" in entry.name:
            countries[iso]["dst"] = int(countries[iso]["dst"]) + 1
        else:
            org_slug = short[len(iso) + 1 :]
            countries[iso]["orgs"].add(org_slug)
    return countries


def nanoid_prefix(iso: str) -> str:
    return f"{iso[0]}1{iso[-1]}2"


def module_name(dirname: str) -> str:
    return "github.com/etzhayyim-ai/" + dirname.removeprefix("etzhayyim-")


def component_name(short: str) -> str:
    return "gov-" + short + "-component"


def jsonld_name(iso: str, slug: str) -> str:
    return f"{iso}-{slug}.jsonld"


def adapter_service_path(short: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", short)
    return f"/etzhayyim.{cleaned}.v1.Service"


def go_module(dirname: str) -> str:
    return f"""module {module_name(dirname)}

go 1.23

require (
\tgithub.com/etzhayyim/magatama-go v0.0.0
\tgithub.com/etzhayyim/signal-client v0.0.0-00010101000000-000000000000
)

require go.bytecodealliance.org/cm v0.3.0 // indirect

replace github.com/etzhayyim/signal-client => ../../../../packages/go/signal-client
replace github.com/etzhayyim/magatama-go => ../../../../packages/rust/magatama/magatama-go
"""


def go_sum() -> str:
    return """github.com/julienschmidt/httprouter v1.3.0 h1:U0609e9tgbseu3rBINet9P48AI/D3oJs4dN7jwJOQ1U=
github.com/julienschmidt/httprouter v1.3.0/go.mod h1:JR6WtHb+2LUe8TCKY3cZOxFyyO8IZAc4RVcycCCAKdM=
github.com/spinframework/spin-go-sdk/v2 v2.2.1 h1:ceAbRU+D3xmyZ8ScDLeFoT763ikFIUEmSjgsrD11v8k=
github.com/spinframework/spin-go-sdk/v2 v2.2.1/go.mod h1:vocVZB4qlTG8C5yoliKIAJCuv4x7sqK0GmVkWeD9N/A=
go.bytecodealliance.org/cm v0.3.0 h1:VhV+4vjZPUGCozCg9+up+FNL3YU6XR+XKghk7kQ0vFc=
go.bytecodealliance.org/cm v0.3.0/go.mod h1:JD5vtVNZv7sBoQQkvBvAAVKJPhR/bqBH7yYXTItMfZI=
"""


def magatama_toml(short: str) -> str:
    name = component_name(short)
    return f"""# {name} — magatama runtime config

[component]
path = "component.wasm"

[component.env]

[triggers.http]
listen = "0.0.0.0:8080"
routes = ["/api/grpc/...", "/health", "/healthz", "/readyz", "/..."]

[yata]
data_dir = "/data/yata"

[pool]
size = 1
"""


def world_wit(world: str, short: str) -> str:
    pkg = re.sub(r"[^a-z0-9-]", "-", short)
    return f"""package etzhayyim:gov-{pkg};

world component {{
    include etzhayyim:platform/{world}@0.1.0;
}}
"""


def jsonld(iso: str, nanoid: str, label: str, description: str) -> str:
    return json.dumps(
        {
            "@context": "https://schema.org/",
            "@type": "GovernmentOrganization",
            "name": label,
            "description": description,
            "identifier": nanoid,
            "address": {"@type": "PostalAddress", "addressCountry": iso.upper()},
            "url": f"https://{nanoid}.etzhayyim.com",
            "mainEntityOfPage": f"https://{nanoid}.etzhayyim.com/api/mcp",
        },
        indent=2,
        ensure_ascii=False,
    ) + "\n"


def main_go(short: str, iso: str, nanoid: str, label: str, org_type: str) -> str:
    service_path = adapter_service_path(short)
    component = component_name(short)
    return f"""//go:build tinygo || wasip1 || wasip2

package main

import (
\t"encoding/json"
\t"fmt"
\t"net/http"
\t"time"

\tmagatama "github.com/etzhayyim/magatama-go"
)

const (
\tcomponentName   = "{component}"
\tentityName      = "{label}"
\tcountryCode     = "{iso}"
\tcomponentNanoID = "{nanoid}"
\tdivisionType    = "{org_type}"
)

var seeded bool

func ensureSeed() {{
\tif seeded {{
\t\treturn
\t}}
\tseeded = true
\t_ = seedDivision()
}}

func seedDivision() error {{
\trows, err := magatama.CypherQueryMap(
\t\t"MATCH (n:GovDivision {{nanoid: $nanoid}}) RETURN n.name AS name",
\t\tmap[string]any{{"nanoid": componentNanoID}},
\t)
\tif err != nil {{
\t\treturn err
\t}}
\tif len(rows) > 0 {{
\t\treturn nil
\t}}
\treturn magatama.CypherExec(
\t\t"CREATE (n:GovDivision {{nanoid: $nanoid, name: $name, division_type: $type, population: 0, headquarters: '', country_code: $cc, entity_name: $en, org_id: 'anon', user_id: 'anon', actor_id: ''}})",
\t\tmap[string]any{{"nanoid": componentNanoID, "name": entityName, "type": divisionType, "cc": countryCode, "en": entityName}},
\t)
\t}}

func logOrgEvent(eventType string, detail map[string]any) {{
\tnow := time.Now().UTC().Format(time.RFC3339)
\tdetailJSON := "{{}}"
\tif detail != nil {{
\t\tb, _ := json.Marshal(detail)
\t\tdetailJSON = string(b)
\t}}
\t_ = magatama.CypherExec(
\t\t"CREATE (e:OrgEvent {{event_id: $eid, org_nanoid: $nanoid, event_type: $et, timestamp: $ts, country_code: $cc, detail_json: $detail, org_id: 'anon', user_id: 'anon', actor_id: $actor}})",
\t\tmap[string]any{{"eid": componentNanoID + ":" + now, "nanoid": componentNanoID, "et": eventType, "ts": now, "cc": countryCode, "detail": detailJSON, "actor": componentNanoID}},
\t)
}}

func init() {{
\tadapter := magatama.NewAdapter("{service_path}")
\tregisterMethods(adapter)
\tmagatama.Handle(func(w http.ResponseWriter, r *http.Request) {{
\t\tensureSeed()
\t\tif magatama.HandleCORS(w, r) {{
\t\t\treturn
\t\t}}
\t\tadapter.ServeHTTP(w, r)
\t}})
}}

func main() {{}}

func registerMethods(a *magatama.Adapter) {{
\ta.Register(magatama.Method{{
\t\tName:        "GetOrganizationInfo",
\t\tDescription: "Get information about this government organization",
\t\tInputSchema: map[string]any{{"type": "object", "properties": map[string]any{{}}}},
\t\tHandler: func(args map[string]any) (any, error) {{
\t\t\treturn map[string]any{{
\t\t\t\t"id": componentNanoID,
\t\t\t\t"name": entityName,
\t\t\t\t"countryCode": countryCode,
\t\t\t\t"type": divisionType,
\t\t\t\t"endpoint": "https://" + componentNanoID + ".etzhayyim.com/api/grpc",
\t\t\t}}, nil
\t\t}},
\t}})
\ta.Register(magatama.Method{{
\t\tName:        "GetDivisionInfo",
\t\tDescription: "Get default division info for this organization",
\t\tInputSchema: map[string]any{{"type": "object", "properties": map[string]any{{}}}},
\t\tHandler: func(args map[string]any) (any, error) {{
\t\t\trows, err := magatama.CypherQueryMap(
\t\t\t\t"MATCH (n:GovDivision {{nanoid: $nanoid}}) RETURN n.name AS name, n.division_type AS type, n.population AS population, n.headquarters AS headquarters",
\t\t\t\tmap[string]any{{"nanoid": componentNanoID}},
\t\t\t)
\t\t\tif err != nil {{
\t\t\t\treturn nil, err
\t\t\t}}
\t\t\tif len(rows) == 0 {{
\t\t\t\treturn nil, fmt.Errorf("division not found")
\t\t\t}}
\t\t\treturn rows[0], nil
\t\t}},
\t}})
\ta.Register(magatama.Method{{
\t\tName:        "GetEvents",
\t\tDescription: "Get recent events for this organization",
\t\tInputSchema: map[string]any{{"type": "object", "properties": map[string]any{{"limit": map[string]any{{"type": "integer"}}}}}},
\t\tHandler: func(args map[string]any) (any, error) {{
\t\t\tlimit := 50
\t\t\tif l, ok := args["limit"].(float64); ok && l > 0 {{
\t\t\t\tlimit = int(l)
\t\t\t}}
\t\t\trows, err := magatama.CypherQueryMap(
\t\t\t\tfmt.Sprintf("MATCH (e:OrgEvent {{org_nanoid: $nanoid}}) RETURN e.event_id AS event_id, e.event_type AS event_type, e.timestamp AS timestamp ORDER BY e.timestamp DESC LIMIT %d", limit),
\t\t\t\tmap[string]any{{"nanoid": componentNanoID}},
\t\t\t)
\t\t\tif err != nil {{
\t\t\t\treturn nil, err
\t\t\t}}
\t\t\treturn map[string]any{{"events": rows, "total": len(rows)}}, nil
\t\t}},
\t}})
\ta.Register(magatama.Method{{
\t\tName:        "ReceiveMessage",
\t\tDescription: "Receive a message from another government organization",
\t\tInputSchema: map[string]any{{"type": "object", "properties": map[string]any{{"from": map[string]any{{"type": "string"}}, "subject": map[string]any{{"type": "string"}}, "body": map[string]any{{"type": "string"}}}}}},
\t\tHandler: func(args map[string]any) (any, error) {{
\t\t\tfrom, _ := args["from"].(string)
\t\t\tsubject, _ := args["subject"].(string)
\t\t\tlogOrgEvent("message_received", map[string]any{{"from": from, "subject": subject}})
\t\t\treturn map[string]any{{"status": "received"}}, nil
\t\t}},
\t}})
\ta.Register(magatama.Method{{
\t\tName:        "SendMessage",
\t\tDescription: "Send a message to another government organization via cross-actor",
\t\tInputSchema: map[string]any{{"type": "object", "properties": map[string]any{{"to_org_id": map[string]any{{"type": "string"}}, "subject": map[string]any{{"type": "string"}}, "body": map[string]any{{"type": "string"}}}}, "required": []any{{"to_org_id", "subject"}}}},
\t\tHandler: func(args map[string]any) (any, error) {{
\t\t\ttoOrg, _ := args["to_org_id"].(string)
\t\t\tsubject, _ := args["subject"].(string)
\t\t\tbody, _ := args["body"].(string)
\t\t\tif toOrg == "" || subject == "" {{
\t\t\t\treturn nil, fmt.Errorf("to_org_id and subject are required")
\t\t\t}}
\t\t\tmsgJSON, _ := json.Marshal(map[string]any{{"from": componentNanoID, "to": toOrg, "subject": subject, "body": body, "type": "org.message"}})
\t\t\tresult, err := magatama.Say(toOrg, "ReceiveMessage", string(msgJSON))
\t\t\tif err != nil {{
\t\t\t\treturn nil, err
\t\t\t}}
\t\t\tlogOrgEvent("message_sent", map[string]any{{"to_org": toOrg, "subject": subject}})
\t\t\treturn map[string]any{{"status": "sent", "to": toOrg, "result": result}}, nil
\t\t}},
\t}})
}}
"""


def mkdir_component(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)
    (path / "wit").mkdir(parents=True, exist_ok=True)


def write_component(path: Path, dirname: str, iso: str, spec: dict[str, str]) -> None:
    short = dirname.removeprefix(DIR_PREFIX)
    nanoid = nanoid_prefix(iso) + spec["suffix"]
    mkdir_component(path)
    (path / "go.mod").write_text(go_module(dirname), encoding="utf-8")
    (path / "go.sum").write_text(go_sum(), encoding="utf-8")
    (path / "magatama.toml").write_text(magatama_toml(short), encoding="utf-8")
    (path / "main.go").write_text(main_go(short, iso, nanoid, spec["label"], spec["type"]), encoding="utf-8")
    (path / "wit" / "world.wit").write_text(world_wit(spec["world"], short), encoding="utf-8")
    (path / jsonld_name(iso, spec["slug"])).write_text(
        jsonld(iso, nanoid, spec["label"], spec["description"]),
        encoding="utf-8",
    )


def target_countries(existing: dict[str, dict[str, set[str] | int]], explicit: list[str], limit: int) -> list[str]:
    if explicit:
        return explicit
    only_dst = []
    for iso, info in existing.items():
        orgs = info["orgs"]
        if info["dst"] and not orgs:
            only_dst.append((int(info["dst"]), iso))
    only_dst.sort(key=lambda item: (-item[0], item[1]))
    countries = [iso for _, iso in only_dst]
    if limit > 0:
        countries = countries[:limit]
    return countries


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate missing L1 org components for weak-coverage countries")
    parser.add_argument("--countries", type=str, default="", help="Comma-separated ISO3 country codes")
    parser.add_argument("--limit", type=int, default=0, help="Auto-select up to N only-dst countries")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created")
    args = parser.parse_args()

    existing = parse_existing()
    explicit = [item.strip().lower() for item in args.countries.split(",") if item.strip()]
    countries = target_countries(existing, explicit, args.limit)
    if not countries:
        print("No countries selected")
        return 0

    created: list[str] = []
    skipped: list[str] = []
    for iso in countries:
        info = existing.get(iso, {"orgs": set(), "dst": 0, "total": 0})
        orgs = set(info["orgs"])
        for spec in L1_ORGS:
            dirname = f"{DIR_PREFIX}{iso}-{spec['slug']}-{nanoid_prefix(iso)}{spec['suffix']}"
            short = dirname.removeprefix(DIR_PREFIX)
            if any(org == short[len(iso) + 1 :] for org in orgs):
                skipped.append(dirname)
                continue
            path = WASM_DIR / dirname
            if path.exists():
                skipped.append(dirname)
                continue
            if args.dry_run:
                created.append(dirname)
                continue
            write_component(path, dirname, iso, spec)
            created.append(dirname)

    print(json.dumps({"countries": countries, "created": len(created), "skipped": len(skipped)}, indent=2))
    for name in created:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
