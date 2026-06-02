#!/usr/bin/env python3
"""Wave 62 — mass-arbitration / cultural-repatriation / correspondent-banking / reskilling-fund / marine-litter.

Bridges Wave 61:
- mass-arbitration ↔ classSettlement.flagClaimRate
- cultural-repatriation ↔ landRestitution.flagRestitutionObstacle
- correspondent-banking ↔ kycOnboarding.flagSuspiciousActivity
- reskilling-fund ↔ coalExit.flagJustTransition
- marine-litter ↔ maritimeSpill.flagClcInadequacy
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "mass-arbitration",
    "app": "massArbitration",
    "methods": [
      {
        "name": "recordDemandBatch",
        "desc": "Mass arbitration demand batch (AAA / JAMS / FairClaims — bridges classSettlement.flagClaimRate + consumer-protection + enforcement-action)",
        "fields": [
          ("batchId", "string", True),
          ("respondentLei", "string", False),
          ("forum", "string", True, ["aaa","jams","fair_claims","ftc_smg","int_arbitration","cpr","pam","trust_arb","adr_chambers"]),
          ("industry", "string", True, ["telecom","rideshare","gigecon","streaming","fintech","ecommerce","crypto","insurance","consumer_finance","food_delivery","daycare"]),
          ("claimantCount", "integer", True),
          ("claimRateVid", "string", False, None, "bridges classSettlement.flagClaimRate"),
          ("filingFeeMusd", "number", False),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFeePushback",
        "desc": "Respondent fee pushback / carve-out attempt (bridges classSettlement.flagClaimRate + civil-liability + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("batchVid", "string", True, None, "bridges recordDemandBatch"),
          ("pushbackKind", "string", True, ["refuse_fee","lose_lose_judgment","tos_update_rule","bellwether_trial","fee_shifting","consolidation_attempt","court_motion","severance_argument","sanctions_motion"]),
          ("outcome", "string", False, ["fees_paid","court_compelled","waiver_tos","bellwether_loss","bellwether_win","remand_class","settlement_reached"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "cultural-repatriation",
    "app": "culturalRepatriation",
    "methods": [
      {
        "name": "recordClaim",
        "desc": "Cultural heritage repatriation claim (NAGPRA / UNESCO 1970 / UNIDROIT — bridges landRestitution.flagRestitutionObstacle + cultural-heritage + intangible-heritage)",
        "fields": [
          ("claimId", "string", True),
          ("holdingInstitutionLei", "string", False),
          ("regimeKind", "string", True, ["nagpra","unesco_1970","unidroit_1995","washington_principles","benin_bronzes","fr_loi_2024","nl_pinto","bg_loi","terezin_declaration","vatican_sacred"]),
          ("objectCategory", "string", True, ["human_remains","funerary","sacred_object","patrimonial","artwork_colonial","religious_ritual","archaeological","manuscript","natural_history","multiple"]),
          ("claimantCountryIso3", "string", True),
          ("restitutionObstacleVid", "string", False, None, "bridges landRestitution.flagRestitutionObstacle"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDeaccessioning",
        "desc": "Deaccessioning / repatriation refusal / partial loan (bridges landRestitution.flagRestitutionObstacle + cultural-heritage + fpic-consent)",
        "fields": [
          ("flagId", "string", True),
          ("claimVid", "string", True, None, "bridges recordClaim"),
          ("concernKind", "string", True, ["refused_provenance","loan_not_return","redacted_inventory","statute_barred","trust_ownership","colonial_legality_claim","museum_board_opposition","conservation_dispute","duplicates_sent"]),
          ("objectCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "correspondent-banking",
    "app": "correspondentBanking",
    "methods": [
      {
        "name": "recordNostroRelation",
        "desc": "Correspondent / Nostro-Vostro banking relation (bridges kycOnboarding.flagSuspiciousActivity + swift-institution + fatf-travel-rule)",
        "fields": [
          ("relationId", "string", True),
          ("correspondentLei", "string", False),
          ("respondentLei", "string", False),
          ("respondentCountryIso3", "string", True),
          ("relationKind", "string", True, ["nostro","vostro","payable_through","cpa","rentabilization","nested","fx_clearing","trade_finance","securities_settle"]),
          ("sarVid", "string", False, None, "bridges kycOnboarding.flagSuspiciousActivity"),
          ("onboardedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDerisking",
        "desc": "De-risking / wire transparency gap / SWIFT GPI outlier (bridges kycOnboarding.flagSuspiciousActivity + fatf-travel-rule + debt-transparency)",
        "fields": [
          ("flagId", "string", True),
          ("relationVid", "string", True, None, "bridges recordNostroRelation"),
          ("issueKind", "string", True, ["wholesale_derisking","remittance_corridor_close","cbr_discontinued","fintech_sponsor_exit","sanctions_over_comply","msb_unbanked","humanitarian_corridor","mm_forex_gap","gpi_non_compliant","hidden_intermediary"]),
          ("affectedCorridorsCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "reskilling-fund",
    "app": "reskillingFund",
    "methods": [
      {
        "name": "recordProgram",
        "desc": "Workforce reskilling program (JETP social fund / EU JTF / state trust — bridges coalExit.flagJustTransition + just-transition + labour-mobility)",
        "fields": [
          ("programId", "string", True),
          ("fundingSource", "string", True, ["jetp_indonesia","jetp_vietnam","jetp_senegal","jetp_south_africa","eu_just_transition_fund","us_appalachian","de_kohleausstieg","pl_terra","uk_coalfields","au_rti_fund","sk_coal_phase"]),
          ("countryIso3", "string", True),
          ("targetWorkers", "integer", True),
          ("programKind", "string", True, ["reskill","upskill","relocation_support","pension_bridge","community_diversify","apprenticeship","smb_startup_grant","green_job","care_economy","tourism"]),
          ("justTransitionVid", "string", False, None, "bridges coalExit.flagJustTransition"),
          ("launchedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagOutcomeGap",
        "desc": "Reskilling outcome / placement gap / gender-disparity (bridges coalExit.flagJustTransition + just-transition + worker-grievance)",
        "fields": [
          ("flagId", "string", True),
          ("programVid", "string", True, None, "bridges recordProgram"),
          ("gapKind", "string", True, ["low_placement_rate","age_bias","gender_disparity","migrant_exclusion","skills_mismatch","certification_unrecognized","wage_drop","community_exodus","completion_rate","regional_imbalance"]),
          ("placementRatePct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "marine-litter",
    "app": "marineLitter",
    "methods": [
      {
        "name": "recordLitterEvent",
        "desc": "Marine litter / ALDFG / pellet spill event (UNEA plastic treaty / GPML / ghost gear — bridges maritimeSpill.flagClcInadequacy + fisheries-iuu + biodiversity-gbf)",
        "fields": [
          ("eventId", "string", True),
          ("regionName", "string", True),
          ("litterKind", "string", True, ["aldfg_ghost_gear","plastic_pellet_spill","container_loss","urban_debris","fishing_line","micro_bead","tire_dust","ppe_debris","coastal_trash","river_plume","deep_sea_trawl"]),
          ("estMassTonnes", "number", False),
          ("spillVid", "string", False, None, "bridges maritimeSpill.flagClcInadequacy"),
          ("detectedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagLiabilityGap",
        "desc": "Plastic treaty / EPR liability gap / ALDFG funding shortfall (bridges maritimeSpill.flagClcInadequacy + plastic-treaty + chemicals-management)",
        "fields": [
          ("flagId", "string", True),
          ("eventVid", "string", True, None, "bridges recordLitterEvent"),
          ("gapKind", "string", True, ["no_producer_responsibility","orphan_gear","treaty_text_gap","monitoring_sparse","financial_mechanism_missing","traceability_obligation","polluter_pays_failure","recycling_infra_absent","transboundary_flow_unclear","upstream_waste"]),
          ("unrecoveredBusd", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
]


def snake(s):
    out = []
    for ch in s:
        if ch.isupper(): out.append("_"+ch.lower())
        else: out.append(ch)
    return "".join(out).lstrip("_")


def build_ddl_cols(methods):
    seen = {"vertex_id"}
    cols = [("vertex_id","varchar","PRIMARY KEY")]
    for m in methods:
        for f in m["fields"]:
            name = f[0]; ftype = f[1]
            col = snake(name)
            if col in seen: continue
            seen.add(col)
            if ftype == "integer" and any(k in col for k in ["size","years","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects"]):
                sql_t = "bigint"
            else:
                sql_t = {"string":"varchar","integer":"int","number":"double precision","boolean":"boolean"}.get(ftype,"varchar")
            cols.append((col, sql_t, ""))
        if m.get("classify"):
            cname = m["classify"][0]
            col = snake(cname) if any(c.isupper() for c in cname) else cname
            if col not in seen:
                seen.add(col); cols.append((col, "varchar", ""))
    for c in [("status","varchar",""),("created_at","varchar",""),("owner_did","varchar",""),("sensitivity_ord","int",""),("org_id","varchar",""),("user_id","varchar",""),("actor_id","varchar","")]:
        if c[0] not in seen:
            cols.append(c); seen.add(c[0])
    return cols


def gen_lexicon(actor, method):
    nsid = f"com.etzhayyim.apps.{actor['app']}.{method['name']}"
    props={}; required=[]
    for f in method["fields"]:
        name,ftype,req=f[0],f[1],f[2]
        enum=f[3] if len(f)>3 else None
        desc=f[4] if len(f)>4 else None
        p={"type":ftype}
        if enum: p["enum"]=enum
        if desc: p["description"]=desc
        if ftype=="string" and name.endswith("At"): p["format"]="datetime"
        props[name]=p
        if req: required.append(name)
    out_props={"ok":{"type":"boolean"},"vertexId":{"type":"string"},"instanceKey":{"type":"integer"},"error":{"type":"string"}}
    if method.get("classify"):
        col,_,enum=method["classify"]
        out_props[col]={"type":"string","enum":enum}
    return {"lexicon":1,"id":nsid,"defs":{"main":{"type":"procedure","description":method["desc"],
        "input":{"encoding":"application/json","schema":{"type":"object","required":required,"properties":props}},
        "output":{"encoding":"application/json","schema":{"type":"object","properties":out_props}}}}}


def gen_bpmn(actor, method):
    slug=actor["slug"]
    table=f"vertex_open_{slug.replace('-','_')}"
    proc_id=f"open_{slug.replace('-','_')}_{snake(method['name'])}"
    action=f"open.{actor['app']}.{method['name']}"
    vparts=["vertex_id: vertexId"]
    for f in method["fields"]:
        name=f[0]; col=snake(name)
        vparts.append(f"{col}: {name}")
    if method.get("classify"):
        col,expr,_=method["classify"]
        sc = snake(col) if any(c.isupper() for c in col) else col
        vparts.append(f"{sc}: {expr}")
    vparts+=['status: "active"','created_at: string(now())','owner_did: callerDid','sensitivity_ord: 1','org_id: callerDid','user_id: callerDid',f'actor_id: "sys.bpmn.open-{slug}"']
    feel="{"+", ".join(vparts)+"}"
    x=feel.replace("&","&amp;").replace('"',"&quot;").replace("<","&lt;").replace(">","&gt;")
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL" xmlns:zeebe="http://camunda.org/schema/zeebe/1.0" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" id="Definitions_{proc_id}" targetNamespace="https://etzhayyim.com/bpmn/open-{slug}" exporter="hand-written" exporterVersion="1.0">
  <bpmn:process id="{proc_id}" name="{method['name']}" isExecutable="true">
    <bpmn:startEvent id="Start"><bpmn:outgoing>Flow_S</bpmn:outgoing></bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_S" sourceRef="Start" targetRef="Task_Save"/>
    <bpmn:serviceTask id="Task_Save" name="save">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.db.insert"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;{table}&quot;" target="table"/><zeebe:input source="={x}" target="values"/><zeebe:input source="=&quot;ignore&quot;" target="onConflict"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_S</bpmn:incoming><bpmn:outgoing>Flow_A</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_A" sourceRef="Task_Save" targetRef="Task_Audit"/>
    <bpmn:serviceTask id="Task_Audit" name="audit">
      <bpmn:extensionElements><zeebe:taskDefinition type="generic.audit.emit"/>
        <zeebe:ioMapping><zeebe:input source="=&quot;did:web:open-{slug}.etzhayyim.com&quot;" target="actor"/><zeebe:input source="=&quot;{action}&quot;" target="action"/><zeebe:input source="={{vertexId: vertexId}}" target="payload"/></zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_A</bpmn:incoming><bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Audit" targetRef="End"/>
    <bpmn:endEvent id="End"><bpmn:incoming>Flow_End</bpmn:incoming></bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>"""


def gen_ddl(actor):
    slug=actor["slug"]; table=f"vertex_open_{slug.replace('-','_')}"
    cols=build_ddl_cols(actor["methods"])
    body=",\n  ".join(f"{c[0]} {c[1]}{' '+c[2] if c[2] else ''}" for c in cols)
    return f"CREATE TABLE IF NOT EXISTS {table} (\n  {body}\n);\n"


for i, a in enumerate(ACTORS, start=1):
    bd=REPO/f"00-contracts/bpmn/com/etzhayyim/open-{a['slug']}"
    ld=REPO/f"00-contracts/lexicons/com/etzhayyim/apps/{a['app']}"
    bd.mkdir(parents=True,exist_ok=True); ld.mkdir(parents=True,exist_ok=True)
    for m in a["methods"]:
        (ld/f"{m['name']}.json").write_text(json.dumps(gen_lexicon(a,m),indent=2,ensure_ascii=False))
        (bd/f"{m['name']}.bpmn").write_text(gen_bpmn(a,m))
    ddl = gen_ddl(a)
    out = Path(f"/tmp/wave13/w62_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
