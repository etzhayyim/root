#!/usr/bin/env python3
"""
codegen-wit-migrate.py — COFOG WIT linker migration for states project.

Generates component-registry.json and migrates:
  - wit/world.wit → COFOG world (etzhayyim-gov-*)
  - main.go → NewApp pattern (kuruma-style)
  - magatama.toml → [interfaces] section

Usage:
  python3 codegen-wit-migrate.py --registry-only       # Generate registry only
  python3 codegen-wit-migrate.py --dry-run              # Preview changes
  python3 codegen-wit-migrate.py --country jpn          # Migrate Japan only
  python3 codegen-wit-migrate.py --cofog 01             # Migrate COFOG 01 only
  python3 codegen-wit-migrate.py --batch-size 10        # Pilot batch
  python3 codegen-wit-migrate.py                        # Full migration
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

# ─── Constants ───────────────────────────────────────────────

WASM_DIR = Path(__file__).parent.parent / "wasm"
REGISTRY_PATH = Path(__file__).parent / "component-registry.json"
DIR_PREFIX = "etzhayyim-performer-sys-etzhayyim-actors-pba7d22f-org-gov-"

# International org prefixes (no country code)
INTL_ORGS = {
    "un", "nato", "eu", "g7", "g20", "asean", "au", "oas",
    "opec", "apec", "brics", "mercosur", "gcc", "saarc",
    "commonwealth", "osce", "csto", "sco", "arab-league",
    "iaea", "wto", "who", "imf", "world-bank", "icj",
    "interpol", "unesco", "unicef", "unhcr",
}

# COFOG mapping: gov function pattern → (cofog_code, cofog_name, world)
COFOG_MAP = [
    # COFOG 02 — Defence
    (r"(defense|military|joint-staff|armed-forces|army|navy|air-force|korean-peoples-army|mod-|national-guard)", "02", "defence", "etzhayyim-gov-defence"),
    # COFOG 03 — Public order and safety
    (r"(police|justice|prosecutor|supreme-court|law-enforcement|ministry-of-people-security|gendarmerie|carabinieri|judiciary|court-of-appeal|high-court|magistrate)", "03", "public-order-safety", "etzhayyim-gov-public-order"),
    # COFOG 04 — Economic affairs
    (r"(finance|trade|energy|transport|labor|commerce|treasury|central-bank|customs|tax|fazenda|hacienda|revenue|industry|agriculture|competition|budget|economic|procurement|monetary)", "04", "economic-affairs", "etzhayyim-gov-economic"),
    # COFOG 05 — Environmental protection
    (r"(environment|ecology|climate|forestry|water-resources|environmental)", "05", "environmental-protection", "etzhayyim-gov-environment"),
    # COFOG 06 — Housing
    (r"(housing|urban|construction|public-works|community)", "06", "housing-community", "etzhayyim-gov-housing"),
    # COFOG 07 — Health
    (r"(health|medical|pharmaceutical|public-health|sanitation)", "07", "health-services", "etzhayyim-gov-health"),
    # COFOG 09 — Education
    (r"(education|university|school|academic|science|research|culture)", "09", "education-services", "etzhayyim-gov-education"),
    # COFOG 01 — General public services (catch-all)
    (r".", "01", "general-public-services", "etzhayyim-gov-general"),
]

# org_tier derivation (searched in order, first match wins)
TIER_PATTERNS = [
    (r"dst-", "district"),
    (r"executive|cabinet|state-affairs|palacio|elysee|kremlin|white-house", "executive"),
    (r"ministry|minister|moj|mofa|mof|meti|mext|mhlw|mic|maff|mlit|mod|moe|mot|mol", "ministry"),
    (r"department|directorate|bureau|agency|authority|commission|committee|council|board|service|institute|center|centre", "department"),
]

# RBAC hierarchy per tier
RBAC = {
    "executive":     {"responsible": "gov-executive",        "accountable": "head-of-state",          "approval": ("DecisionClassA", 2, "high")},
    "ministry":      {"responsible": "gov-minister",         "accountable": "gov-executive",          "approval": ("DecisionClassB", 1, "medium")},
    "department":    {"responsible": "gov-director",         "accountable": "gov-minister",           "approval": ("DecisionClassC", 1, "low")},
    "office":        {"responsible": "gov-officer",          "accountable": "gov-director",           "approval": ("DecisionClassC", 1, "low")},
    "district":      {"responsible": "district-admin",       "accountable": "gov-director",           "approval": ("DecisionClassC", 1, "low")},
    "international": {"responsible": "intl-representative",  "accountable": "intl-secretary-general", "approval": ("DecisionClassB", 1, "medium")},
}


# ─── Registry Builder ───────────────────────────────────────

def parse_component_dir(dirname: str) -> dict[str, Any] | None:
    """Parse a component directory name into classification metadata."""
    short = dirname.removeprefix(DIR_PREFIX)
    if not short or short == dirname:
        return None

    # Check for international orgs (no country code)
    for org in INTL_ORGS:
        if short.startswith(org + "-") or short == org:
            return _classify(dirname, short, "intl", org, short)

    # Parse country code (first segment, 2-3 chars)
    parts = short.split("-", 1)
    if len(parts) < 2:
        return None

    country_code = parts[0]
    remainder = parts[1]

    # Special case: "0" country code (unknown/stateless)
    if country_code == "0":
        return _classify(dirname, short, "0", remainder, remainder)

    # Handle new-format dirs: etzhayyim-wasm-states-{cc}-{nanoid}
    if dirname.startswith("etzhayyim-wasm-states-"):
        wasm_parts = dirname.removeprefix("etzhayyim-wasm-states-").split("-", 1)
        if len(wasm_parts) == 2:
            return _classify(dirname, dirname, wasm_parts[0], "state-generic", dirname)
        return None

    # Standard: {cc}-{function}-{nanoid}
    return _classify(dirname, short, country_code, remainder, remainder)


def _classify(dirname: str, short: str, country_code: str, gov_function: str, full_remainder: str) -> dict[str, Any]:
    """Classify a component by COFOG, tier, and capabilities."""

    # Determine if district
    is_district = gov_function.startswith("dst-")

    # Extract nanoid (last segment if it looks like one)
    nanoid = ""
    func_parts = gov_function.rsplit("-", 1)
    if len(func_parts) == 2 and len(func_parts[1]) == 8 and func_parts[1].isalnum():
        nanoid = func_parts[1]
        gov_function_clean = func_parts[0]
    else:
        gov_function_clean = gov_function
        # For districts, extract nanoid differently
        if is_district:
            dst_parts = gov_function.split("-", 2)
            if len(dst_parts) >= 2:
                nanoid = dst_parts[1]  # numeric district ID

    # COFOG classification
    cofog_code = "01"
    cofog_name = "general-public-services"
    world = "etzhayyim-gov-general"

    # Numeric COFOG prefix (Japan-style: 01000000, 02000000, etc.)
    numeric_cofog = re.match(r"^(\d{2})\d{6}", gov_function_clean)
    NUMERIC_COFOG_MAP = {
        "01": ("01", "general-public-services", "etzhayyim-gov-general"),
        "02": ("01", "general-public-services", "etzhayyim-gov-general"),  # MIC (internal affairs)
        "03": ("03", "public-order-safety", "etzhayyim-gov-public-order"),  # MOJ
        "04": ("01", "general-public-services", "etzhayyim-gov-general"),  # MOFA
        "05": ("09", "education-services", "etzhayyim-gov-education"),  # MEXT
        "06": ("07", "health-services", "etzhayyim-gov-health"),  # MHLW
        "07": ("04", "economic-affairs", "etzhayyim-gov-economic"),  # MAFF
        "08": ("04", "economic-affairs", "etzhayyim-gov-economic"),  # METI
        "09": ("04", "economic-affairs", "etzhayyim-gov-economic"),  # MLIT
        "10": ("05", "environmental-protection", "etzhayyim-gov-environment"),  # MOE
        "11": ("02", "defence", "etzhayyim-gov-defence"),  # MOD
    }

    if is_district:
        cofog_code = "01.6"
        cofog_name = "district-administration"
        world = "etzhayyim-gov-district"
    elif country_code == "intl":
        cofog_code = "intl"
        cofog_name = "general-public-services"
        world = "etzhayyim-gov-international"
    elif numeric_cofog:
        prefix = numeric_cofog.group(1)
        if prefix in NUMERIC_COFOG_MAP:
            cofog_code, cofog_name, world = NUMERIC_COFOG_MAP[prefix]
        # else: default 01/general
    else:
        for pattern, code, name, w in COFOG_MAP:
            if re.search(pattern, gov_function_clean):
                cofog_code = code
                cofog_name = name
                world = w
                break

    # org_tier
    org_tier = "office"  # default
    if country_code == "intl":
        org_tier = "international"
    elif is_district:
        org_tier = "district"
    else:
        for pattern, tier in TIER_PATTERNS:
            if re.search(pattern, gov_function_clean):
                org_tier = tier
                break

    # Capability tags
    caps = ["government", cofog_name, country_code]
    if gov_function_clean and gov_function_clean not in caps:
        caps.append(gov_function_clean)
    if org_tier not in caps:
        caps.append(org_tier)

    return {
        "dir": dirname,
        "short": short,
        "country_code": country_code,
        "gov_function": gov_function_clean,
        "nanoid": nanoid,
        "cofog_code": cofog_code,
        "cofog_name": cofog_name,
        "world": world,
        "org_tier": org_tier,
        "capabilities": caps,
    }


def build_registry() -> list[dict[str, Any]]:
    """Scan wasm/ directory and build classification registry."""
    components = []
    if not WASM_DIR.exists():
        print(f"ERROR: {WASM_DIR} not found", file=sys.stderr)
        sys.exit(1)

    for entry in sorted(WASM_DIR.iterdir()):
        if not entry.is_dir():
            continue
        parsed = parse_component_dir(entry.name)
        if parsed:
            components.append(parsed)

    return components


def save_registry(components: list[dict[str, Any]]) -> None:
    """Save registry to JSON."""
    summary = {
        "total": len(components),
        "countries": len(set(c["country_code"] for c in components)),
        "cofog_distribution": {},
        "tier_distribution": {},
    }
    for c in components:
        summary["cofog_distribution"][c["cofog_code"]] = summary["cofog_distribution"].get(c["cofog_code"], 0) + 1
        summary["tier_distribution"][c["org_tier"]] = summary["tier_distribution"].get(c["org_tier"], 0) + 1

    registry = {"summary": summary, "components": components}
    REGISTRY_PATH.write_text(json.dumps(registry, indent=2, ensure_ascii=False) + "\n")
    print(f"Registry saved: {REGISTRY_PATH} ({len(components)} components)")
    print(f"  Countries: {summary['countries']}")
    print(f"  COFOG: {json.dumps(summary['cofog_distribution'])}")
    print(f"  Tiers: {json.dumps(summary['tier_distribution'])}")


# ─── Link Catalog ───────────────────────────────────────────

def linked_orgs_for_component(comp: dict[str, Any]) -> list[dict[str, str]]:
    """Return federation peers for the component's country and role."""
    cc = comp["country_code"]
    tier = comp["org_tier"]
    peers: list[dict[str, str]] = []

    if cc == "jpn":
        peers.extend([
            {
                "org_code": "jpn-01000000-cabinet-office",
                "org_name": "Cabinet Office",
                "org_name_local": "内閣府",
                "org_type": "executive",
                "endpoint": "https://jpn-01000000-cabinet-office.etzhayyim.com/api/grpc",
                "relationship": "national executive coordination",
                "scope": "national",
            },
            {
                "org_code": "jpn-04000000-mofa",
                "org_name": "Ministry of Foreign Affairs",
                "org_name_local": "外務省",
                "org_type": "ministry",
                "endpoint": "https://jpn-04000000-mofa.etzhayyim.com/api/grpc",
                "relationship": "cross-border diplomacy",
                "scope": "national",
            },
            {
                "org_code": "jpn-07000000-mhlw",
                "org_name": "Ministry of Health, Labour and Welfare",
                "org_name_local": "厚生労働省",
                "org_type": "ministry",
                "endpoint": "https://jpn-07000000-mhlw.etzhayyim.com/api/grpc",
                "relationship": "public health and welfare",
                "scope": "national",
            },
            {
                "org_code": "jpn-09000000-meti",
                "org_name": "Ministry of Economy, Trade and Industry",
                "org_name_local": "経済産業省",
                "org_type": "ministry",
                "endpoint": "https://jpn-09000000-meti.etzhayyim.com/api/grpc",
                "relationship": "economic and industrial coordination",
                "scope": "national",
            },
            {
                "org_code": "jpn-20200000-community-safety-bureau",
                "org_name": "Community Safety Bureau",
                "org_name_local": "生活安全局",
                "org_type": "bureau",
                "endpoint": "https://jpn-20200000-community-safety-bureau.etzhayyim.com/api/grpc",
                "relationship": "public safety coordination",
                "scope": "national",
            },
        ])
    elif cc == "ind":
        peers.extend([
            {
                "org_code": "ind-01000000-cabinet-secretariat",
                "org_name": "Cabinet Secretariat",
                "org_name_local": "कैबिनेट सचिवालय",
                "org_type": "executive",
                "endpoint": "https://ind-01000000-cabinet-secretariat.etzhayyim.com/api/grpc",
                "relationship": "national executive coordination",
                "scope": "national",
            },
            {
                "org_code": "ind-04000000-mha",
                "org_name": "Ministry of Home Affairs",
                "org_name_local": "गृह मंत्रालय",
                "org_type": "ministry",
                "endpoint": "https://ind-04000000-mha.etzhayyim.com/api/grpc",
                "relationship": "internal security and state coordination",
                "scope": "national",
            },
            {
                "org_code": "ind-04000000-mea",
                "org_name": "Ministry of External Affairs",
                "org_name_local": "विदेश मंत्रालय",
                "org_type": "ministry",
                "endpoint": "https://ind-04000000-mea.etzhayyim.com/api/grpc",
                "relationship": "diplomatic and cross-border coordination",
                "scope": "international",
            },
            {
                "org_code": "ind-07000000-mohfw",
                "org_name": "Ministry of Health and Family Welfare",
                "org_name_local": "स्वास्थ्य और परिवार कल्याण मंत्रालय",
                "org_type": "ministry",
                "endpoint": "https://ind-07000000-mohfw.etzhayyim.com/api/grpc",
                "relationship": "public health coordination",
                "scope": "national",
            },
            {
                "org_code": "ind-cbi",
                "org_name": "Central Bureau of Investigation",
                "org_name_local": "केंद्रीय अन्वेषण ब्यूरो",
                "org_type": "bureau",
                "endpoint": "https://ind-cbi.etzhayyim.com/api/grpc",
                "relationship": "investigation and law-enforcement coordination",
                "scope": "national",
            },
        ])

    if tier in {"executive", "ministry", "department", "district"} or cc in {"jpn", "ind"}:
        peers.extend([
            {
                "org_code": "intl-interpol",
                "org_name": "INTERPOL",
                "org_name_local": "国際刑事警察機構",
                "org_type": "international",
                "endpoint": "https://interpol.etzhayyim.com/api/grpc",
                "relationship": "international law-enforcement coordination",
                "scope": "international",
            },
            {
                "org_code": "intl-un",
                "org_name": "United Nations",
                "org_name_local": "国際連合" if cc == "jpn" else "संयुक्त राष्ट्र",
                "org_type": "international",
                "endpoint": "https://un.etzhayyim.com/api/grpc",
                "relationship": "multilateral policy coordination",
                "scope": "international",
            },
        ])

    # Deduplicate by org_code while preserving order.
    deduped: list[dict[str, str]] = []
    seen: set[str] = set()
    for peer in peers:
        code = peer["org_code"]
        if code in seen:
            continue
        seen.add(code)
        deduped.append(peer)
    return deduped


def linked_orgs_go_literal(comp: dict[str, Any]) -> str:
    """Render linked org catalog as a Go composite literal."""
    entries = []
    for peer in linked_orgs_for_component(comp):
        entries.append(
            "{"
            f'\"org_code\": \"{peer["org_code"]}\", '
            f'\"org_name\": \"{peer["org_name"]}\", '
            f'\"org_name_local\": \"{peer["org_name_local"]}\", '
            f'\"org_type\": \"{peer["org_type"]}\", '
            f'\"endpoint\": \"{peer["endpoint"]}\", '
            f'\"relationship\": \"{peer["relationship"]}\", '
            f'\"scope\": \"{peer["scope"]}\"'
            "}"
        )
    return ",\n\t\t\t".join(entries)


# ─── Code Generation ────────────────────────────────────────

def gen_world_wit(comp: dict[str, Any]) -> str:
    """Generate wit/world.wit content."""
    # Extract package name from existing world.wit if possible
    pkg_name = comp["short"]
    # Sanitize for WIT package name (alphanumeric + hyphens)
    pkg_name = re.sub(r"[^a-z0-9-]", "-", pkg_name.lower()).strip("-")

    return f"""package etzhayyim:gov-{pkg_name};

world component {{
    include etzhayyim:platform/{comp['world']}@0.1.0;
}}
"""


def gen_main_go(comp: dict[str, Any]) -> str:
    """Generate main.go content (NewApp pattern)."""
    cc = comp["country_code"]
    func_name = comp["gov_function"]
    nanoid = comp["nanoid"] or "00000000"
    org_tier = comp["org_tier"]
    cofog_name = comp["cofog_name"]
    caps = comp["capabilities"]

    rbac = RBAC.get(org_tier, RBAC["office"])
    responsible = rbac["responsible"]
    accountable = rbac["accountable"]
    approval_class, approval_count, approval_priority = rbac["approval"]

    # Build entity name from function
    entity_name = func_name.replace("-", " ").title()

    # Capability tags as Go string literal
    cap_tags = ", ".join(f'"{c}"' for c in caps)

    # Determine if district
    is_district = comp["cofog_code"] == "01.6"
    linked_orgs_literal = linked_orgs_go_literal(comp)

    return f'''//go:build tinygo || wasip1 || wasip2

package main

import (
\t"encoding/json"
\t"fmt"
\t"time"

\tmagatama "github.com/etzhayyim/magatama-go"
)

const (
\tcomponentNanoID = "{nanoid}"
\tcountryCode     = "{cc}"
\tgovFunction     = "{func_name}"
\tentityName      = "{entity_name}"
)

var app = magatama.NewApp(magatama.AppDef{{
\tID:          componentNanoID,
\tName:        "gov-" + countryCode + "-" + govFunction,
\tDescription: entityName,
}})

func init() {{
\tapp.Command("GetOrganizationInfo", cmdGetOrgInfo,
\t\tmagatama.AsAgentTool("Get organization metadata"),
\t\tmagatama.WithCapabilityTags({cap_tags}),
\t\tmagatama.Responsible(magatama.AssigneeOrgRole, "{responsible}"),
\t\tmagatama.Accountable(magatama.AssigneeOrgRole, "{accountable}"),
\t)
\tapp.Command("SendMessage", cmdSendMessage,
\t\tmagatama.AsAgentTool("Send inter-government message"),
\t\tmagatama.WithCapabilityTags("government", "messaging", countryCode),
\t\tmagatama.RequireApproval(magatama.{approval_class}, {approval_count}, "{approval_priority}"),
\t)
\tapp.Command("ReceiveMessage", cmdReceiveMessage,
\t\tmagatama.AsAgentTool("Receive message from government org"),
\t\tmagatama.WithCapabilityTags("government", "messaging", countryCode),
\t)
\tapp.Query("GetDivisionInfo", qryGetDivision)
\tapp.Query("GetEvents", qryGetEvents)
\tapp.Serve()
}}

func main() {{}}

// ── helpers ──────────────────────────────────────────────────

func sa(args map[string]any, key string) string {{
\tv, ok := args[key]
\tif !ok || v == nil {{
\t\treturn ""
\t}}
\tif s, ok := v.(string); ok {{
\t\treturn s
\t}}
\treturn fmt.Sprintf("%v", v)
}}

func ia(args map[string]any, key string, def int) int {{
\tv, ok := args[key]
\tif !ok {{
\t\treturn def
\t}}
\tif n, ok := v.(float64); ok {{
\t\treturn int(n)
\t}}
\treturn def
}}

// ── commands ─────────────────────────────────────────────────

func cmdGetOrgInfo(args map[string]any) (any, error) {{
\treturn map[string]any{{
\t\t"name":        entityName,
\t\t"countryCode": countryCode,
\t\t"govFunction": govFunction,
\t\t"nanoid":      componentNanoID,
\t\t"type":        "government",
\t\t"endpoint":    "https://" + componentNanoID + ".etzhayyim.com/api/grpc",
\t\t"linked_orgs": []map[string]any{{{linked_orgs_literal}}},
\t\t"capabilities": []string{{{cap_tags}}},
\t}}, nil
}}

func cmdSendMessage(args map[string]any) (any, error) {{
\ttoOrg := sa(args, "to_org_id")
\tsubject := sa(args, "subject")
\tbody := sa(args, "body")
\tif toOrg == "" || subject == "" {{
\t\treturn nil, fmt.Errorf("to_org_id and subject are required")
\t}}
\tmsgJSON, _ := json.Marshal(map[string]any{{
\t\t"from": componentNanoID, "to": toOrg,
\t\t"subject": subject, "body": body, "type": "org.message",
\t}})
\tresult, err := magatama.Say(toOrg, "ReceiveMessage", string(msgJSON))
\tif err != nil {{
\t\treturn nil, err
\t}}
\tlogOrgEvent("message_sent", map[string]any{{"to_org": toOrg, "subject": subject}})
\treturn map[string]any{{"status": "sent", "to": toOrg, "result": result}}, nil
}}

func cmdReceiveMessage(args map[string]any) (any, error) {{
\tfrom := sa(args, "from")
\tsubject := sa(args, "subject")
\tlogOrgEvent("message_received", map[string]any{{"from": from, "subject": subject}})
\treturn map[string]any{{"status": "received"}}, nil
}}

// ── queries ──────────────────────────────────────────────────

func qryGetDivision(args map[string]any) (any, error) {{
\trows, err := magatama.CypherQueryMap(
\t\t"MATCH (n:GovDivision {{nanoid: $nanoid}}) RETURN n.name AS name, n.division_type AS type, n.population AS population, n.headquarters AS headquarters",
\t\tmap[string]any{{"nanoid": componentNanoID}},
\t)
\tif err != nil {{
\t\treturn nil, err
\t}}
\tif len(rows) == 0 {{
\t\t_ = magatama.CypherExec(
\t\t\t"CREATE (n:GovDivision {{nanoid: $nanoid, name: $name, division_type: $type, population: 0, headquarters: $hq, country_code: $cc, org_id: \'anon\', user_id: \'anon\', actor_id: \'\'}})",
\t\t\tmap[string]any{{"nanoid": componentNanoID, "name": entityName, "type": "{cofog_name}", "hq": "", "cc": countryCode}},
\t\t)
\t\treturn map[string]any{{"id": componentNanoID, "name": entityName, "type": "{cofog_name}"}}, nil
\t}}
\treturn rows[0], nil
}}

func qryGetEvents(args map[string]any) (any, error) {{
\tlimit := ia(args, "limit", 50)
\trows, err := magatama.CypherQueryMap(
\t\tfmt.Sprintf("MATCH (e:OrgEvent {{org_nanoid: $nanoid}}) RETURN e.event_id AS event_id, e.event_type AS event_type, e.timestamp AS timestamp ORDER BY e.timestamp DESC LIMIT %d", limit),
\t\tmap[string]any{{"nanoid": componentNanoID}},
\t)
\tif err != nil {{
\t\treturn nil, err
\t}}
\treturn map[string]any{{"events": rows, "total": len(rows)}}, nil
}}

// ── event logging ────────────────────────────────────────────

func logOrgEvent(eventType string, detail map[string]any) {{
\tnow := time.Now().UTC().Format(time.RFC3339)
\tdetailJSON := "{{}}"
\tif detail != nil {{
\t\tb, _ := json.Marshal(detail)
\t\tdetailJSON = string(b)
\t}}
\t_ = magatama.CypherExec(
\t\t"CREATE (e:OrgEvent {{event_id: $eid, org_nanoid: $nanoid, event_type: $et, timestamp: $ts, country_code: $cc, detail_json: $detail, org_id: \'anon\', user_id: \'anon\', actor_id: $actor}})",
\t\tmap[string]any{{
\t\t\t"eid": componentNanoID + ":" + now, "nanoid": componentNanoID,
\t\t\t"et": eventType, "ts": now, "cc": countryCode,
\t\t\t"detail": detailJSON, "actor": componentNanoID,
\t\t}},
\t)
}}
'''


def gen_magatama_toml(comp: dict[str, Any]) -> str:
    """Generate magatama.toml with [interfaces] section."""
    func_name = comp["gov_function"]
    cofog_name = comp["cofog_name"]
    cc = comp["country_code"]
    world = comp["world"]
    linked_orgs = linked_orgs_for_component(comp)
    linked_org_tags = ["government", "federation", cc, comp["cofog_name"]]
    if comp["org_tier"] not in linked_org_tags:
        linked_org_tags.append(comp["org_tier"])
    linked_org_tags_str = ", ".join(f'"{t}"' for t in linked_org_tags)

    # Determine which COFOG interface this component exports
    export_interface = cofog_name
    provides_functions = []

    if cofog_name == "general-public-services":
        provides_functions = ["get-org-info", "list-policies", "submit-inquiry", "receive-directive"]
    elif cofog_name == "defence":
        provides_functions = ["get-readiness", "report-assessment", "request-coordination"]
    elif cofog_name == "public-order-safety":
        provides_functions = ["file-incident", "get-statistics", "request-cooperation"]
    elif cofog_name == "economic-affairs":
        provides_functions = ["get-indicators", "register-trade-agreement", "submit-budget", "get-fiscal-report"]
    elif cofog_name == "environmental-protection":
        provides_functions = ["submit-assessment", "get-compliance-status", "report-violation"]
    elif cofog_name == "housing-community":
        provides_functions = ["list-projects", "submit-proposal", "get-amenities-status"]
    elif cofog_name == "health-services":
        provides_functions = ["get-overview", "report-statistics", "request-resources"]
    elif cofog_name == "education-services":
        provides_functions = ["get-overview", "report-statistics", "submit-curriculum"]
    elif cofog_name == "district-administration":
        provides_functions = ["get-district-info", "list-local-services", "submit-report-to-national", "receive-national-directive"]

    provides_str = ", ".join(f'{{ name = "{f}" }}' for f in provides_functions)
    tags_str = ", ".join(f'"{t}"' for t in ["government", cofog_name, cc])

    return f"""# gov-{cc}-{func_name} — magatama runtime config

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

[interfaces]
package = "etzhayyim:cofog@0.1.0"

[[interfaces.provides]]
name = "organization-directory"
functions = [
  {{ name = "get-organization-info", params = "", returns = "result<list<u8>, string>" }},
  {{ name = "list-linked-organizations", params = "", returns = "result<list<u8>, string>" }},
  {{ name = "send-inter-org-message", params = "to_org_code: string, subject: string, body: string", returns = "result<list<u8>, string>" }},
  {{ name = "receive-inter-org-message", params = "from_org_code: string, subject: string, body: string", returns = "result<list<u8>, string>" }},
]
tags = [{linked_org_tags_str}]
phase = "operational"
tier = 1
skill_prompt = "Use for {cc.upper()} government {cofog_name.replace('-', ' ')} federation lookup and inter-org coordination"

[[interfaces.provides]]
name = "{export_interface}"
functions = [{provides_str}]
tags = [{tags_str}]
skill_prompt = "Use for {cc.upper()} government {cofog_name.replace('-', ' ')} operations"

[[interfaces.requires]]
package = "etzhayyim:cofog@0.1.0"
interface = "gov-messaging"
functions = ["send-message", "receive-message"]
"""


def migrate_component(comp: dict[str, Any], dry_run: bool = False) -> bool:
    """Migrate a single component's world.wit, main.go, and magatama.toml."""
    comp_dir = WASM_DIR / comp["dir"]
    if not comp_dir.exists():
        print(f"  SKIP: {comp['dir']} (not found)")
        return False

    wit_path = comp_dir / "wit" / "world.wit"
    main_path = comp_dir / "main.go"
    toml_path = comp_dir / "magatama.toml"

    new_wit = gen_world_wit(comp)
    new_main = gen_main_go(comp)
    new_toml = gen_magatama_toml(comp)

    if dry_run:
        print(f"  DRY-RUN: {comp['short']}")
        print(f"    world: {comp['world']} (COFOG {comp['cofog_code']})")
        print(f"    tier: {comp['org_tier']}")
        print(f"    caps: {comp['capabilities']}")
        return True

    # Write files
    wit_path.parent.mkdir(parents=True, exist_ok=True)
    wit_path.write_text(new_wit)
    main_path.write_text(new_main)
    toml_path.write_text(new_toml)

    print(f"  MIGRATED: {comp['short']} → {comp['world']}")
    return True


# ─── Main ────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="COFOG WIT linker migration")
    parser.add_argument("--registry-only", action="store_true", help="Generate registry only, no migration")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without writing")
    parser.add_argument("--country", type=str, help="Filter by country code (e.g. jpn)")
    parser.add_argument("--cofog", type=str, help="Filter by COFOG code (e.g. 01, 04)")
    parser.add_argument("--batch-size", type=int, default=0, help="Limit number of components to migrate")
    parser.add_argument("--tier", type=str, help="Filter by org tier (executive, ministry, etc.)")
    args = parser.parse_args()

    # Build registry
    print("Building component registry...")
    components = build_registry()
    save_registry(components)

    if args.registry_only:
        return

    # Apply filters
    filtered = components
    if args.country:
        filtered = [c for c in filtered if c["country_code"] == args.country]
        print(f"Filtered to country={args.country}: {len(filtered)} components")
    if args.cofog:
        filtered = [c for c in filtered if c["cofog_code"] == args.cofog]
        print(f"Filtered to COFOG={args.cofog}: {len(filtered)} components")
    if args.tier:
        filtered = [c for c in filtered if c["org_tier"] == args.tier]
        print(f"Filtered to tier={args.tier}: {len(filtered)} components")
    if args.batch_size > 0:
        filtered = filtered[:args.batch_size]
        print(f"Batch limited to {args.batch_size} components")

    # Migrate
    print(f"\nMigrating {len(filtered)} components...")
    success = 0
    for comp in filtered:
        if migrate_component(comp, dry_run=args.dry_run):
            success += 1

    print(f"\nDone: {success}/{len(filtered)} {'previewed' if args.dry_run else 'migrated'}")


if __name__ == "__main__":
    main()
