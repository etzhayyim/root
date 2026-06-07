#!/usr/bin/env python3
"""
Promote a curated clean-room cohort from L3 (Advanced) to L4 (Production).

L4 adds, on top of the L3 CRUD surface, the production features the ADR's §6
flagged as the remaining gap:
  * list PAGINATION (limit + starting_after cursor, returns has_more)
  * FILTERING by any field via query params
  * relationship EXPANSION (?expand=<field>) for *Id reference fields
  * stronger VALIDATION (required + type coercion + unknown-field rejection)
  * a runnable CONTRACT TEST (tests/test_<platform>_contract.py) that verifies
    the API contract statically (stdlib unittest — no WASM runtime needed)

Curated cohort = the marquee platforms that carry a real, hand-curated resource
model (PLATFORM_OVERRIDES in deepen_actors.py), so the L4 depth sits on
faithful resource shapes rather than generic ones. Broadening L4 to the long
tail is gated on the Autonomous Reverse-Engineering Loop (per-API doc fidelity).

Idempotent. Reuses the exact domain models from deepen_actors.py.
"""

import os
import re
import importlib.util

TOOLS_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(TOOLS_DIR)
ACTORS_DIR = os.path.join(ROOT, "20-actors")

_spec = importlib.util.spec_from_file_location(
    "deepen_actors", os.path.join(TOOLS_DIR, "deepen_actors.py"))
deepen = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(deepen)

# Curated L4 cohort: every platform with a hand-curated override model.
L4_COHORT = sorted(deepen.PLATFORM_OVERRIDES.keys())

# Preferred per-category representatives (well-known platform per domain) so the
# L4 reference implementation for each domain is a recognizable one.
PREFERRED_REP = {
    "crm_sales": "salesforce", "erp_finance": "sap", "iaas_cloud": "aws",
    "office_productivity": "notion", "devops_ci": "github", "ehr_health": "epic-systems",
    "ecommerce": "shopify", "payments": "stripe", "data_analytics": "snowflake",
    "design_tools": "figma", "ai_ml": "openai", "martech": "mailchimp",
    "security_iam": "crowdstrike", "hrtech": "workday", "devtools_apm": "datadog",
    "headless_ec_logistics": "contentful", "fintech_web3": "coinbase", "comms_social": "slack",
    "cx_survey": "zendesk", "vertical_saas": "servicenow", "lowcode_ipaas": "zapier",
    "rpa": "uipath", "modern_data_stack": "fivetran", "iot_edge": "samsara",
    "regtech_privacy": "vanta", "aec_govtech": "autodesk", "media_video_cms": "cloudinary",
    "event_npo_creator": "eventbrite", "core_banking_insurtech": "mambu",
    "devsecops_serverless": "supabase", "enterprise_commerce_spend": "coupa",
    "dpg_india_stack": "aadhaar", "us_federal": "irs", "uk_eu_egov": "hmrc",
    "japan_apac_egov": "mynumber", "intl_orgs_central_banks": "worldbank",
    "open_banking_finreg": "openbankinguk", "customs_trade_logistics": "uscbp",
    "public_health_env_ip": "cdc", "public_safety_law": "interpol",
    "transit_smart_cities": "gtfs", "fin_market_hft": "fixprotocol", "web3_rpc": "alchemy",
    "telecom_satellite": "starlink", "healthcare_fhir_bio": "hl7_fhir",
    "energy_grid_utilities": "opc_ua", "travel_aviation_hospitality": "amadeus_gds",
    "os_kernel": "posix", "ai_ml_infra_chips": "nvidia_nvml", "cyber_threat_intel": "virustotal",
    "manufacturing_plm_robotics": "ros_robotics", "isa_quantum": "riscv_isa",
    "internet_routing": "bgp_routing", "mobility_auto_ev": "can_bus",
    "space_ocean_earth": "ais_marine", "agritech_food": "johndeere_api",
    "meta_knowledge_publishing": "crossref", "deep_logistics_supply": "gs1_epcis",
    "materials_bio_chemical": "cas_registry", "energy_commodities": "platts_api",
    "physical_benchmarks_classifications": "hs_codes_customs",
    "superapp": "grab", "delivery_logistics": "doordash", "ride_hailing": "didi_chuxing",
    "mainframe": "ibm_zos", "scada": "siemens_simatic", "pharmacy_rx": "express_scripts",
    "real_estate": "reso_web_api", "gaming_backend": "playfab",
    "legal_ediscovery": "relativity_ediscovery", "bci_neuro": "openbci", "synbio": "benchling",
    "xr_spatial": "openxr", "drone_robotics": "px4_autopilot", "agent_protocol": "langchain",
    "qkd": "id_quantique", "fusion_energy": "iter_data",
}


def per_category_cohort(depth=1):
    """Up to `depth` representative platforms per category model (existing dirs).
    depth=1 → preferred rep per domain; depth>1 widens the production cohort."""
    cats = deepen.parse_platform_categories()
    by_cat = {}
    for plat, key in cats.items():
        by_cat.setdefault(key, []).append(plat)
    reps = []
    for key, plats in by_cat.items():
        pref = PREFERRED_REP.get(key)
        ordered = ([pref] if (pref and pref in plats) else []) + sorted(plats)
        seen = []
        for pick in ordered:
            if pick in seen:
                continue
            if os.path.isdir(os.path.join(ACTORS_DIR, f"{pick}-compat")):
                reps.append(pick)
                seen.append(pick)
            if len(seen) >= depth:
                break
    return sorted(set(reps) | set(L4_COHORT))


def _snake(name):
    return re.sub(r"(?<!^)(?=[A-Z])", "_", name).lower()


def _pluralize(name):
    return deepen._pluralize(name)


def _coerce_expr(ftype, varexpr):
    if ftype == "integer":
        return f"_as_int({varexpr})"
    if ftype == "float":
        return f"_as_float({varexpr})"
    if ftype == "boolean":
        return f"_as_bool({varexpr})"
    return f"{varexpr}"


def _ref_entity(field, model):
    """customerId -> Customer if that entity exists in the model."""
    if not field.endswith("Id"):
        return None
    base = field[:-2]
    cand = base[0].upper() + base[1:]
    return cand if cand in model else None


def main_py_l4(platform, ns, model):
    out = []
    A = out.append
    A('"""')
    A(f"Py Kotodama WASM entrypoint for the {platform.capitalize()} clean-room actor (L4).")
    A("")
    A("L4 production surface: CRUD + pagination + filtering + relationship")
    A("expansion + validation, over a Datomic-backed Kotoba schema.")
    A("Generated by 70-tools/promote_l4.py (ADR 260607 deepening phase, L4 cohort).")
    A("No proprietary code or credentials; resource shapes only.")
    A('"""')
    A("from kotodama import Runtime")
    A("from kotoba import load_schema")
    A("from datomic import DatomicClient")
    A("import uuid")
    A("import datetime")
    A("")
    A(f'schema = load_schema("../schema/{platform}.kotoba")')
    A("db = DatomicClient.connect()")
    A(f'app = Runtime("{platform}-compat")')
    A("")
    A("DEFAULT_LIMIT = 20")
    A("MAX_LIMIT = 100")
    A("")
    A("")
    A("def now():")
    A("    return datetime.datetime.utcnow().isoformat()")
    A("")
    A("")
    A("def new_id(prefix):")
    A('    return f"{prefix}_" + uuid.uuid4().hex[:16]')
    A("")
    A("")
    A("def _as_int(v):")
    A("    try:\n        return int(v)\n    except (TypeError, ValueError):\n        return 0")
    A("")
    A("")
    A("def _as_float(v):")
    A("    try:\n        return float(v)\n    except (TypeError, ValueError):\n        return 0.0")
    A("")
    A("")
    A("def _as_bool(v):")
    A('    return str(v).lower() in ("1", "true", "yes", "on") if v is not None else False')
    A("")
    A("")
    A("def _persist(entity, rec):")
    A('    """Transact a record into Datomic as namespaced EAVT facts."""')
    A("    facts = {}")
    A("    for k, v in rec.items():")
    A(f'        facts[f"{ns}.{{entity}}/{{k}}"] = v')
    A("    db.transact([facts])")
    A("    return rec")
    A("")
    A("")
    A("def _query(entity, eid=None):")
    A(f'    pattern = {{"entity": f"{ns}.{{entity}}"}}')
    A("    if eid is not None:")
    A('        pattern["id"] = eid')
    A("    return db.query(pattern)")
    A("")
    A("")
    A("def _require(data, fields):")
    A("    missing = [f for f in fields if not data.get(f)]")
    A("    if missing:")
    A('        return {"error": {"message": "Missing required fields: " + ", ".join(missing),')
    A('                          "type": "invalid_request_error"}}')
    A("    return None")
    A("")
    A("")
    A("def _reject_unknown(data, allowed):")
    A('    """Reject body fields not in the entity schema (strict validation)."""')
    A("    extra = [k for k in data if k not in allowed]")
    A("    if extra:")
    A('        return {"error": {"message": "Unknown fields: " + ", ".join(extra),')
    A('                          "type": "invalid_request_error"}}')
    A("    return None")
    A("")
    A("")
    A("def _apply_filters(rows, params, fields):")
    A('    """Filter rows by any schema field present in the query params."""')
    A("    out = rows")
    A("    for f in fields:")
    A("        if f in params and params[f] not in (None, \"\"):")
    A("            want = str(params[f])")
    A("            out = [r for r in out if str(r.get(f)) == want]")
    A("    return out")
    A("")
    A("")
    A("def _paginate(rows, params):")
    A('    """Cursor pagination: limit + starting_after (an id). Returns (page, has_more)."""')
    A("    limit = min(max(_as_int(params.get(\"limit\")) or DEFAULT_LIMIT, 1), MAX_LIMIT)")
    A("    start = params.get(\"starting_after\")")
    A("    if start is not None:")
    A("        ids = [r.get(\"id\") for r in rows]")
    A("        if start in ids:")
    A("            rows = rows[ids.index(start) + 1:]")
    A("    page = rows[:limit]")
    A("    return page, len(rows) > limit")
    A("")
    A("")
    A("def _expand(rec, params, refs):")
    A('    """?expand=<field> inlines a referenced entity (rec[field+\"_obj\"])."""')
    A("    want = (params.get(\"expand\") or \"\").split(\",\")")
    A("    for field, ent in refs.items():")
    A("        if field in want and rec.get(field):")
    A("            rows = _query(ent, rec[field])")
    A('            rec[field + "_obj"] = rows[0] if rows else None')
    A("    return rec")
    A("")

    for ent, fields in model.items():
        plural = _pluralize(ent)
        route = f"/v1/{plural.lower()}"
        prefix = f"{re.sub(r'[^a-z0-9]', '', platform.lower())[:8]}_{ent[:3].lower()}"
        required = deepen._required_fields(fields)
        allowed = list(fields.keys())
        refs = {f: _ref_entity(f, model) for f in fields if _ref_entity(f, model)}
        # CREATE
        A("")
        A(f'@app.route("{route}", methods=["POST"])')
        A(f"def create_{_snake(ent)}(request):")
        A(f'    """Create a {ent}."""')
        A("    data = request.json or request.form or {}")
        A(f"    err = _reject_unknown(data, {allowed!r})")
        A("    if err:\n        return err, 400")
        if required:
            A(f"    err = _require(data, {required!r})")
            A("    if err:\n        return err, 400")
        A(f'    rec = {{"id": new_id("{prefix}")}}')
        for fname, ftype in fields.items():
            A(f'    rec["{fname}"] = {_coerce_expr(ftype, f"data.get({fname!r})")}')
        A('    rec["createdAt"] = now()')
        A('    rec["updatedAt"] = rec["createdAt"]')
        A(f'    _persist("{ent}", rec)')
        A("    return rec, 201")
        # LIST (pagination + filtering)
        A("")
        A(f'@app.route("{route}", methods=["GET"])')
        A(f"def list_{_snake(plural)}(request):")
        A(f'    """List {plural} with filtering + cursor pagination."""')
        A("    params = request.query or {}")
        A(f'    rows = _query("{ent}")')
        A(f"    rows = _apply_filters(rows, params, {allowed!r})")
        A("    page, has_more = _paginate(rows, params)")
        A('    return {"object": "list", "data": page, "has_more": has_more,')
        A('            "count": len(page), "total": len(rows)}, 200')
        # GET (+ expansion)
        A("")
        A(f'@app.route("{route}/<eid>", methods=["GET"])')
        A(f"def get_{_snake(ent)}(request, eid):")
        A(f'    """Retrieve a {ent} by id (supports ?expand=)."""')
        A(f'    rows = _query("{ent}", eid)')
        A("    if not rows:")
        A('        return {"error": {"message": "Not found", "type": "not_found"}}, 404')
        A("    rec = rows[0]")
        if refs:
            A(f"    rec = _expand(rec, request.query or {{}}, {refs!r})")
        A("    return rec, 200")
        # UPDATE
        A("")
        A(f'@app.route("{route}/<eid>", methods=["POST", "PATCH"])')
        A(f"def update_{_snake(ent)}(request, eid):")
        A(f'    """Update a {ent}."""')
        A(f'    rows = _query("{ent}", eid)')
        A("    if not rows:")
        A('        return {"error": {"message": "Not found", "type": "not_found"}}, 404')
        A("    data = request.json or request.form or {}")
        A(f"    err = _reject_unknown(data, {allowed!r})")
        A("    if err:\n        return err, 400")
        A("    rec = rows[0]")
        A("    for k, v in data.items():")
        A('        if k not in ("id", "createdAt"):')
        A("            rec[k] = v")
        A('    rec["updatedAt"] = now()')
        A(f'    _persist("{ent}", rec)')
        A("    return rec, 200")
        # DELETE
        A("")
        A(f'@app.route("{route}/<eid>", methods=["DELETE"])')
        A(f"def delete_{_snake(ent)}(request, eid):")
        A(f'    """Delete a {ent}."""')
        A(f'    rows = _query("{ent}", eid)')
        A("    if not rows:")
        A('        return {"error": {"message": "Not found", "type": "not_found"}}, 404')
        A(f'    db.retract({{"entity": f"{ns}.{ent}", "id": eid}})')
        A('    return {"id": eid, "deleted": True}, 200')

    A("")
    A('@app.route("/healthz", methods=["GET"])')
    A("def healthz(request):")
    A(f'    return {{"status": "ok", "actor": "{platform}-compat", "tier": "L4",')
    A(f'            "entities": {list(model.keys())!r}}}, 200')
    A("")
    A("")
    A('if __name__ == "__main__":')
    A("    app.start()")
    return "\n".join(out) + "\n"


def contract_test(platform, ns, model):
    """Runnable stdlib-unittest contract test (no WASM runtime needed)."""
    entities = list(model.keys())
    plurals = {ent: _pluralize(ent).lower() for ent in entities}
    t = []
    A = t.append
    A('"""')
    A(f"Contract test for the {platform}-compat L4 actor.")
    A("Static API-contract verification (stdlib unittest; no WASM runtime).")
    A("Generated by 70-tools/promote_l4.py.")
    A('"""')
    A("import ast")
    A("import os")
    A("import re")
    A("import unittest")
    A("")
    A("HERE = os.path.dirname(os.path.abspath(__file__))")
    A("ACTOR = os.path.dirname(HERE)")
    A('MAIN = os.path.join(ACTOR, "src", "main.py")')
    A(f'SCHEMA = os.path.join(ACTOR, "schema", "{platform}.kotoba")')
    A(f"ENTITIES = {entities!r}")
    A(f"PLURALS = {plurals!r}")
    A("")
    A("")
    A(f"class {_classname(platform)}Contract(unittest.TestCase):")
    A("    @classmethod")
    A("    def setUpClass(cls):")
    A('        with open(MAIN, encoding="utf-8") as f:')
    A("            cls.src = f.read()")
    A("        cls.tree = ast.parse(cls.src)")
    A('        with open(SCHEMA, encoding="utf-8") as f:')
    A("            cls.schema = f.read()")
    A("")
    A("    def test_compiles(self):")
    A("        self.assertIsInstance(self.tree, ast.Module)")
    A("")
    A("    def test_schema_has_all_entities(self):")
    A("        for ent in ENTITIES:")
    A('            self.assertRegex(self.schema, r"entity\\s+" + ent + r"\\s*\\{",')
    A('                             f"schema missing entity {ent}")')
    A("")
    A("    def test_full_crud_per_entity(self):")
    A("        for ent, plural in PLURALS.items():")
    A('            base = "/v1/" + plural')
    A("            for needle in (")
    A('                f\'@app.route("{base}", methods=["POST"])\',')
    A('                f\'@app.route("{base}", methods=["GET"])\',')
    A('                f\'@app.route("{base}/<eid>", methods=["GET"])\',')
    A('                f\'@app.route("{base}/<eid>", methods=["DELETE"])\',')
    A("            ):")
    A("                self.assertIn(needle, self.src, f\"missing route: {needle}\")")
    A("")
    A("    def test_list_has_pagination(self):")
    A('        self.assertIn("_paginate(", self.src)')
    A('        self.assertIn("has_more", self.src)')
    A('        self.assertIn("starting_after", self.src)')
    A("")
    A("    def test_list_has_filtering(self):")
    A('        self.assertIn("_apply_filters(", self.src)')
    A("")
    A("    def test_validation_present(self):")
    A('        self.assertIn("_reject_unknown(", self.src)')
    A('        self.assertIn("_require(", self.src)')
    A("")
    A("    def test_healthz(self):")
    A('        self.assertIn(\'"tier": "L4"\', self.src)')
    A("")
    A("    def test_no_proprietary_imports(self):")
    A("        for bad in (\"requests\", \"openai\", \"stripe\", \"boto3\"):")
    A('            self.assertNotIn("import " + bad, self.src)')
    A("")
    A("")
    A('if __name__ == "__main__":')
    A("    unittest.main()")
    return "\n".join(t) + "\n"


def _classname(platform):
    name = "".join(p.capitalize() for p in re.split(r"[^a-z0-9]", platform.lower()) if p)
    if not name or name[0].isdigit():
        name = "A" + name           # valid Python identifier (e.g. 8th_wall)
    return name


def promote(cohort=None):
    cohort = cohort or L4_COHORT
    done = []
    for platform in cohort:
        adir = os.path.join(ACTORS_DIR, f"{platform}-compat")
        if not os.path.isdir(adir):
            continue
        model = deepen.PLATFORM_OVERRIDES.get(platform) or deepen.CATEGORY_MODELS.get(
            deepen.parse_platform_categories().get(platform))
        if not model:
            continue
        ns = re.sub(r"[^a-z0-9_]", "_", platform.lower())
        with open(os.path.join(adir, "src", "main.py"), "w") as f:
            f.write(main_py_l4(platform, ns, model))
        tdir = os.path.join(adir, "tests")
        os.makedirs(tdir, exist_ok=True)
        with open(os.path.join(tdir, f"test_{re.sub(r'[^a-z0-9]', '_', platform.lower())}_contract.py"), "w") as f:
            f.write(contract_test(platform, ns, model))
        done.append(platform)
    print(f"Promoted {len(done)} actors to L4: {', '.join(done)}")
    return done


if __name__ == "__main__":
    import sys
    argv = sys.argv[1:]
    if argv and argv[0] == "--all":
        cohort = sorted(d[:-len("-compat")].strip()
                        for d in os.listdir(ACTORS_DIR) if d.endswith("-compat"))
        promote(cohort)
    elif argv and argv[0] == "--per-category":
        depth = int(argv[1]) if len(argv) > 1 and argv[1].isdigit() else 1
        promote(per_category_cohort(depth))
    else:
        promote(argv or None)
