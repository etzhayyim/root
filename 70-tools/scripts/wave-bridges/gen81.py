#!/usr/bin/env python3
"""Wave 81 — ransomware-pay / dpa-authority / language-endangerment / offshore-rmb / sox-404-icfr.

Bridges Wave 80:
- ransomware-pay ↔ kevCatalog.flagRemediationLag
- dpa-authority ↔ schremsChallenge.flagRemedy
- language-endangerment ↔ intangibleSafeguard.flagSafeguardingRisk
- offshore-rmb ↔ bisTriennial.flagShift
- sox-404-icfr ↔ restatementEvent.flagStockImpact
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "ransomware-pay",
    "app": "ransomwarePay",
    "methods": [
      {
        "name": "recordPayment",
        "desc": "Ransomware payment / demand / negotiation record (bridges kevCatalog.flagRemediationLag + cyber-incident-ioc + ofac-sanctions-sdn)",
        "fields": [
          ("paymentId", "string", True),
          ("victimLei", "string", False),
          ("threatActorDesignator", "string", True),
          ("demandCrypto", "string", True, ["btc","xmr","eth","usdt","bch","dash","ltc","zec","stealth","mixer_tornado","wrapped"]),
          ("paymentUsd", "number", False),
          ("kevLagVid", "string", False, None, "bridges kevCatalog.flagRemediationLag"),
          ("paidAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagSanctionsHit",
        "desc": "OFAC SDN match / sanctions risk / CFI IEEPA (bridges kevCatalog.flagRemediationLag + ofac-sanctions-sdn + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("paymentVid", "string", True, None, "bridges recordPayment"),
          ("riskKind", "string", True, ["sdn_match_actor","sanctioned_jurisdiction","mixer_chain","sdn_wallet","sibling_wallet","intermediary","fintech_off_ramp","dual_national","iran_cyber","russia_cyber","north_korea_cyber","lazarus","conti_legacy"]),
          ("ofacCaseRef", "string", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "dpa-authority",
    "app": "dpaAuthority",
    "methods": [
      {
        "name": "recordAction",
        "desc": "Data Protection Authority (DPA / CNIL / DPC / ICO) enforcement action (bridges schremsChallenge.flagRemedy + enforcementAction + consumer-protection)",
        "fields": [
          ("actionId", "string", True),
          ("dpa", "string", True, ["cnil_fr","dpc_ie","ico_uk","bfdi_de","aepd_es","garante_it","edps","dsk_nl","dpa_gr","paad_hellenic","apd_dpa_nl","ppcc_jp","pdp_sg","nppa_kr","tst_pl","cnpd_lu"]),
          ("actionKind", "string", True, ["investigation","corrective","fine","ban_processing","representation_order","cross_border_coop","one_stop_shop","dual_lsa","public_reprimand","dpia_required"]),
          ("subjectLei", "string", False),
          ("remedyVid", "string", False, None, "bridges schremsChallenge.flagRemedy"),
          ("issuedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCrossBorderGap",
        "desc": "One-stop-shop / lead-supervisor dispute / dual-filing gap (bridges schremsChallenge.flagRemedy + federal-court-docket + privacy-act)",
        "fields": [
          ("flagId", "string", True),
          ("actionVid", "string", True, None, "bridges recordAction"),
          ("gapKind", "string", True, ["oss_bottleneck","lead_disagreement","double_jeopardy","edpb_binding_decision","member_state_divergence","carve_out_abuse","non_eu_reach","representative_bypass","scope_dispute","transfer_consequence"]),
          ("daysOpen", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "language-endangerment",
    "app": "languageEndangerment",
    "methods": [
      {
        "name": "recordStatus",
        "desc": "UNESCO Atlas / Ethnologue language endangerment status (bridges intangibleSafeguard.flagSafeguardingRisk + cultural-heritage + fpic-consent)",
        "fields": [
          ("statusId", "string", True),
          ("languageName", "string", True),
          ("iso639_3", "string", False),
          ("regionIso3", "string", True),
          ("vitalityTier", "string", True, ["safe","vulnerable","definitely_endangered","severely_endangered","critically_endangered","extinct","awakening","dormant","reclaiming"]),
          ("speakersLiving", "integer", False),
          ("safeguardRiskVid", "string", False, None, "bridges intangibleSafeguard.flagSafeguardingRisk"),
          ("assessedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagRevitalization",
        "desc": "Revitalization program / barriers / intergenerational transfer (bridges intangibleSafeguard.flagSafeguardingRisk + cultural-heritage + education-module)",
        "fields": [
          ("flagId", "string", True),
          ("statusVid", "string", True, None, "bridges recordStatus"),
          ("barrierKind", "string", True, ["no_funding","school_monolingual","intergenerational_transfer","urbanization","migration","diglossia","media_absent","literacy_low","no_orthography","textbook_absent","teacher_training"]),
          ("activeProgramCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "offshore-rmb",
    "app": "offshoreRmb",
    "methods": [
      {
        "name": "recordClearing",
        "desc": "Offshore RMB / CNH clearing bank / CIPS (bridges bisTriennial.flagShift + swift-institution + fx-swap-lines)",
        "fields": [
          ("clearingId", "string", True),
          ("clearingBankLei", "string", False),
          ("jurisdiction", "string", True, ["hk","sg","uk","fr","ca","au","ch","my","th","lu","kz","ru","br","sa","pk","ngn","rmb_oil"]),
          ("productKind", "string", True, ["cnh_spot","cnh_ndf","cnh_cross_currency","cnh_bond","dim_sum","panda_bond","bond_connect","rmb_account","rmb_loan","rmb_qfii_rqfii","cips_settlement","mbridge"]),
          ("shiftVid", "string", False, None, "bridges bisTriennial.flagShift"),
          ("dailyVolumeBrmb", "number", False),
          ("asOfDate", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagPolicyDivergence",
        "desc": "Offshore / onshore divergence / liquidity stress (bridges bisTriennial.flagShift + fx-swap-lines + stablecoin-reserves)",
        "fields": [
          ("flagId", "string", True),
          ("clearingVid", "string", True, None, "bridges recordClearing"),
          ("concernKind", "string", True, ["cnh_cny_spread","offshore_liquidity_squeeze","fixing_intervention","ciph_capacity","counter_cycling","state_bank_front","non_delivery_risk","swift_replace_attempt","sanctions_carve_out","repo_stress"]),
          ("spreadPips", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sox-404-icfr",
    "app": "sox404Icfr",
    "methods": [
      {
        "name": "recordAttestation",
        "desc": "SOX §404 ICFR management/auditor attestation (bridges restatementEvent.flagStockImpact + audit-firm-oversight + enforcement-action)",
        "fields": [
          ("attestationId", "string", True),
          ("filerLei", "string", False),
          ("attestationKind", "string", True, ["management_assessment","auditor_attestation","non_accelerated_exempt","smaller_reporting","emerging_growth","dual_reporting","combined_ia_404"]),
          ("materialWeakness", "boolean", False),
          ("stockImpactVid", "string", False, None, "bridges restatementEvent.flagStockImpact"),
          ("periodEnd", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagWeaknessRemediation",
        "desc": "Material weakness remediation / repeat issue / benchmark (bridges restatementEvent.flagStockImpact + audit-firm-oversight + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("attestationVid", "string", True, None, "bridges recordAttestation"),
          ("issueKind", "string", True, ["segregation_duties","inadequate_controls","inventory_valuation","revenue_recognition","tax_provision","itgc","access_controls","change_mgmt","data_backup","complex_transactions","m_a_integration","crypto_custody"]),
          ("consecutiveYears", "integer", False),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","subjects","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents","countries","detections","dark","embargo","bearers","periods","speakers","programs","consecutive"]):
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
    out = Path(f"/tmp/wave13/w81_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
