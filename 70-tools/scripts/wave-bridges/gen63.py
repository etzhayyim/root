#!/usr/bin/env python3
"""Wave 63 — tos-arbitration / provenance-research / remittance-corridor / apprenticeship / epr-packaging.

Bridges Wave 62:
- tos-arbitration ↔ massArbitration.flagFeePushback
- provenance-research ↔ culturalRepatriation.flagDeaccessioning
- remittance-corridor ↔ correspondentBanking.flagDerisking
- apprenticeship-reg ↔ reskillingFund.flagOutcomeGap
- epr-packaging ↔ marineLitter.flagLiabilityGap
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "tos-arbitration",
    "app": "tosArbitration",
    "methods": [
      {
        "name": "recordClauseChange",
        "desc": "TOS arbitration clause / opt-out window change (bridges massArbitration.flagFeePushback + consumer-protection + antitrust-dma)",
        "fields": [
          ("changeId", "string", True),
          ("operatorLei", "string", False),
          ("platform", "string", True, ["rideshare","delivery","streaming","marketplace","fintech","social","crypto_exchange","telecom","airline","saas_enterprise","gaming","adtech"]),
          ("clauseKind", "string", True, ["mandatory_arb","class_waiver","carve_out","opt_out_window","severability","informal_negotiation","batch_arbitration_gate","delegation_clause","forum_selection","attorneys_fee"]),
          ("feePushbackVid", "string", False, None, "bridges massArbitration.flagFeePushback"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagUnconscionability",
        "desc": "Unconscionability / Concepcion / DirecTV challenge (bridges massArbitration.flagFeePushback + federal-court-docket + civil-liability)",
        "fields": [
          ("flagId", "string", True),
          ("changeVid", "string", True, None, "bridges recordClauseChange"),
          ("grounds", "string", True, ["procedural_unconsc","substantive_unconsc","concepcion_preempt","discover_bank","directv_effective_vindication","vacatur","public_policy","fair_hearing","arbitrary_delegation","inescapable_arb"]),
          ("rulingOutcome", "string", False, ["upheld_clause","struck_clause","severed","reformed","remanded","affirmed_on_appeal","scotus_cert_denied"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "provenance-research",
    "app": "provenanceResearch",
    "methods": [
      {
        "name": "recordDossier",
        "desc": "Museum provenance research dossier (bridges culturalRepatriation.flagDeaccessioning + cultural-heritage + intangible-heritage)",
        "fields": [
          ("dossierId", "string", True),
          ("holdingInstitutionLei", "string", False),
          ("objectCategory", "string", True, ["painting","sculpture","manuscript","artifact","textile","musical_instrument","ceremonial","indigenous_sacred","nazi_era","colonial_era","archaeological","ethnographic"]),
          ("gapPeriod", "string", False, ["pre_1800","1800_1900","1900_1933","nazi_era_1933_45","colonial_era","post_ww2","post_1970"]),
          ("deaccessioningVid", "string", False, None, "bridges culturalRepatriation.flagDeaccessioning"),
          ("investigatorCount", "integer", False),
          ("completedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagProvenanceGap",
        "desc": "Provenance gap / spoliation / stolen art flag (bridges culturalRepatriation.flagDeaccessioning + cultural-heritage + fpic-consent)",
        "fields": [
          ("flagId", "string", True),
          ("dossierVid", "string", True, None, "bridges recordDossier"),
          ("gapKind", "string", True, ["unknown_1933_45","forced_sale","escape_value","post_war_aryanized","colonial_looting","illicit_trade","limitation_trumps","indirect_chain","unclear_ownership_transfer","unsubstantiated_gift"]),
          ("confidenceTier", "string", False, ["low","medium","high","confirmed_illicit"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "remittance-corridor",
    "app": "remittanceCorridor",
    "methods": [
      {
        "name": "recordCorridorCost",
        "desc": "World Bank Remittance Prices / SDG 10.c corridor cost (bridges correspondentBanking.flagDerisking + fatf-travel-rule + fx-swap-lines)",
        "fields": [
          ("snapshotId", "string", True),
          ("sendingCountryIso3", "string", True),
          ("receivingCountryIso3", "string", True),
          ("instrumentKind", "string", True, ["mto","bank_wire","digital_wallet","mobile_money","crypto_p2p","prepaid_card","fintech_neobank","post_office","hawala","nostro_vostro"]),
          ("totalCostPct200usd", "number", False),
          ("fxMarginPct", "number", False),
          ("deriskingVid", "string", False, None, "bridges correspondentBanking.flagDerisking"),
          ("snapshotDate", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCorridorStress",
        "desc": "Corridor stress / consolidation / humanitarian shutdown (bridges correspondentBanking.flagDerisking + refugee-unhcr + humanitarian)",
        "fields": [
          ("flagId", "string", True),
          ("snapshotVid", "string", True, None, "bridges recordCorridorCost"),
          ("stressKind", "string", True, ["last_provider_exit","crypto_off_ramp_cut","humanitarian_freeze","sanctions_spillover","mto_concentration","high_cost_sustained","cbr_exit","fraud_surge","license_revocation","fatf_grey_list"]),
          ("affectedPersonsMillions", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "apprenticeship-reg",
    "app": "apprenticeshipReg",
    "methods": [
      {
        "name": "recordRegistration",
        "desc": "Registered Apprenticeship / IfA / BIBB / ESA registration (bridges reskillingFund.flagOutcomeGap + labour-mobility + credential-portability)",
        "fields": [
          ("registrationId", "string", True),
          ("registryKind", "string", True, ["us_ra","us_iraps","ca_red_seal","uk_ifa","de_bibb","au_australian_apprenticeships","eu_ears","nl_sbb","jp_ginou","in_ndp","fr_afpa"]),
          ("sectorCode", "string", True),
          ("countryIso3", "string", True),
          ("durationMo", "integer", False),
          ("outcomeGapVid", "string", False, None, "bridges reskillingFund.flagOutcomeGap"),
          ("registeredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCompletionGap",
        "desc": "Completion / retention / equity gap (bridges reskillingFund.flagOutcomeGap + gender-pay-gap + gig-worker)",
        "fields": [
          ("flagId", "string", True),
          ("registrationVid", "string", True, None, "bridges recordRegistration"),
          ("gapKind", "string", True, ["dropout","wage_progression","gender_underrepresented","racial_equity","migrant_barrier","disability_support","mentor_gap","cancelled_funding","employer_malpractice","harassment_reported"]),
          ("completionRatePct", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "epr-packaging",
    "app": "eprPackaging",
    "methods": [
      {
        "name": "recordScheme",
        "desc": "Extended Producer Responsibility packaging scheme (bridges marineLitter.flagLiabilityGap + plastic-treaty + weee-ewaste)",
        "fields": [
          ("schemeId", "string", True),
          ("prokindKind", "string", True, ["eu_ppwr","fr_loi_agec","de_vverpackg","jp_recycle","ca_province","us_state","chile_rep","colombia_refd","india_epr","korea_epr","thailand_epr"]),
          ("materialStream", "string", True, ["pet_bottle","hdpe","pp","multilayer","aluminium_can","steel_can","glass","paper_fibre","composite","textile","electronics","battery","tire"]),
          ("countryIso3", "string", True),
          ("producerFeeEurTonne", "number", False),
          ("eprLiabilityVid", "string", False, None, "bridges marineLitter.flagLiabilityGap"),
          ("effectiveAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagEcomodulationGap",
        "desc": "Eco-modulation / recyclability credit gap (bridges marineLitter.flagLiabilityGap + plastic-treaty + chemicals-management)",
        "fields": [
          ("flagId", "string", True),
          ("schemeVid", "string", True, None, "bridges recordScheme"),
          ("issueKind", "string", True, ["no_eco_modulation","penalties_too_low","insufficient_design_signal","free_rider","informal_sector_ignored","transboundary_loophole","recycled_content_fraud","bio_plastic_claim","chemical_recycling_gap","offset_abuse"]),
          ("estLeakageTonnes", "integer", False),
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
            if ftype == "integer" and any(k in col for k in ["size","years","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators"]):
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
    out = Path(f"/tmp/wave13/w63_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
