#!/usr/bin/env python3
"""Wave 61 — class-settlement / land-restitution / kyc-onboarding / coal-exit / maritime-spill.

Bridges Wave 60:
- class-settlement ↔ civilLiability.flagDispositiveRuling
- land-restitution ↔ fpicConsent.flagFpicViolation
- kyc-onboarding ↔ beneficialOwnership.flagUboDiscrepancy
- coal-exit ↔ exportCreditAgency.flagClimateCarveout
- maritime-spill ↔ shadowFleetInsurance.flagGapOrFraud
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "class-settlement",
    "app": "classSettlement",
    "methods": [
      {
        "name": "recordSettlement",
        "desc": "Class action settlement administration (bridges civilLiability.flagDispositiveRuling + enforcementAction + insurance-claim)",
        "fields": [
          ("settlementId", "string", True),
          ("caseKind", "string", True, ["securities_10b5","consumer_protection","antitrust","product_liability","environmental","wage_hour","data_breach","discrimination","opioid","pfas","erisa","biometric_bipa"]),
          ("classSize", "integer", False),
          ("rulingVid", "string", False, None, "bridges civilLiability.flagDispositiveRuling"),
          ("grossMusd", "number", False),
          ("cyPresMusd", "number", False),
          ("finalApprovedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagClaimRate",
        "desc": "Claim rate / cy pres / fairness concern (bridges civilLiability.flagDispositiveRuling + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("settlementVid", "string", True, None, "bridges recordSettlement"),
          ("concernKind", "string", True, ["low_claim_rate","excessive_fees","non_monetary_relief","reversionary","cy_pres_conflict","administrator_conflict","objector_blackmail","opt_out_wave","collateral_estoppel"]),
          ("claimRatePct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "land-restitution",
    "app": "landRestitution",
    "methods": [
      {
        "name": "recordClaim",
        "desc": "Historical land restitution claim (bridges fpicConsent.flagFpicViolation + indigenous-rights + land-tenure)",
        "fields": [
          ("claimId", "string", True),
          ("claimantCommunity", "string", True),
          ("countryIso3", "string", True),
          ("regimeKind", "string", True, ["native_title_au","nz_treaty_waitangi","ca_comprehensive_claim","za_restitution_land_rights","co_ruta_etnica","br_quilombola","pe_comunidad_nativa","ph_iprr","us_ira_eagle_act","no_finnmark","mx_ejido"]),
          ("areaHectares", "number", False),
          ("consentViolationVid", "string", False, None, "bridges fpicConsent.flagFpicViolation"),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRestitutionObstacle",
        "desc": "Restitution process obstacle / competing claim / state delay (bridges fpicConsent.flagFpicViolation + indigenous-rights + worker-grievance)",
        "fields": [
          ("flagId", "string", True),
          ("claimVid", "string", True, None, "bridges recordClaim"),
          ("obstacleKind", "string", True, ["state_delay","competing_claim","overlapping_title","third_party_interest","resource_concession","legal_fee_barrier","evidentiary_burden","statute_of_limitations","non_enforcement","intimidation"]),
          ("yearsPending", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "kyc-onboarding",
    "app": "kycOnboarding",
    "methods": [
      {
        "name": "recordCddCheck",
        "desc": "Bank CDD / EDD / sanctions screening onboarding (bridges beneficialOwnership.flagUboDiscrepancy + sanctions-screening + fatf-travel-rule)",
        "fields": [
          ("checkId", "string", True),
          ("institutionLei", "string", False),
          ("customerCategory", "string", True, ["natural_person","legal_entity","pep","shell_company","hnwi","correspondent","msb","pseu","trust","foundation"]),
          ("riskRating", "string", True, ["low","medium","high","unacceptable","enhanced"]),
          ("uboDiscrepancyVid", "string", False, None, "bridges beneficialOwnership.flagUboDiscrepancy"),
          ("screenedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSuspiciousActivity",
        "desc": "SAR / STR / watchlist hit / FinCEN alert (bridges beneficialOwnership.flagUboDiscrepancy + ofac-sanctions-sdn + fatf-travel-rule)",
        "fields": [
          ("sarId", "string", True),
          ("checkVid", "string", True, None, "bridges recordCddCheck"),
          ("activityKind", "string", True, ["structuring","rapid_movement","round_dollar","high_risk_jurisdiction","pep_without_eadd","shell_company_pattern","sudden_tx","dormant_reactivation","aml_typology_hit","sanctions_near_match"]),
          ("aggregateUsd", "number", False),
          ("filedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "coal-exit",
    "app": "coalExit",
    "methods": [
      {
        "name": "recordRetirement",
        "desc": "Coal plant retirement / JETP milestone (bridges exportCreditAgency.flagClimateCarveout + just-transition + power-node)",
        "fields": [
          ("retirementId", "string", True),
          ("plantOperatorLei", "string", False),
          ("countryIso3", "string", True),
          ("capacityMw", "number", True),
          ("coalType", "string", True, ["lignite","bituminous","subbituminous","anthracite","peat"]),
          ("mechanism", "string", True, ["jetp","ctap","pepi","direct_close","repower_gas","repower_renewable","bankruptcy","economic","end_of_life","early_retire_fund"]),
          ("climateCarveoutVid", "string", False, None, "bridges exportCreditAgency.flagClimateCarveout"),
          ("retiredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagJustTransition",
        "desc": "Just transition / stranded worker gap / community impact (bridges exportCreditAgency.flagClimateCarveout + just-transition + worker-grievance)",
        "fields": [
          ("flagId", "string", True),
          ("retirementVid", "string", True, None, "bridges recordRetirement"),
          ("issueKind", "string", True, ["stranded_worker_no_retrain","pension_shortfall","community_revenue_loss","supply_chain_shock","social_license","environmental_legacy","superfund","subsidence","water_remediation","public_finance_gap"]),
          ("affectedWorkers", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "maritime-spill",
    "app": "maritimeSpill",
    "methods": [
      {
        "name": "recordSpill",
        "desc": "Maritime oil spill / ITOPF / CLC / IOPC event (bridges shadowFleetInsurance.flagGapOrFraud + oil-gas + coastal-slr)",
        "fields": [
          ("spillId", "string", True),
          ("vesselImo", "string", False),
          ("spillKind", "string", True, ["crude_persistent","hfo","mgo_mdo","bunker","chemical_marpol_x","palm_oil","lng_flash","plastic_pellet","ore_tailings","containerized_chemicals"]),
          ("regionName", "string", True),
          ("volumeTonnes", "number", False),
          ("insuranceGapVid", "string", False, None, "bridges shadowFleetInsurance.flagGapOrFraud"),
          ("occurredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagClcInadequacy",
        "desc": "CLC / IOPC fund inadequacy / bunker convention gap (bridges shadowFleetInsurance.flagGapOrFraud + insurance-claim + coastal-slr)",
        "fields": [
          ("flagId", "string", True),
          ("spillVid", "string", True, None, "bridges recordSpill"),
          ("gapKind", "string", True, ["shipowner_limit_breach","iopc_supplementary","bunker_convention_gap","hns_convention_unratified","flag_state_uncooperative","insurer_insolvent","fraudulent_certificate","jurisdiction_forum_shop","sanction_freezes_payout"]),
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
            if ftype == "integer" and any(k in col for k in ["size","years","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels"]):
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
    out = Path(f"/tmp/wave13/w61_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
