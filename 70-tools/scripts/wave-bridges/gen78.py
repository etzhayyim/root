#!/usr/bin/env python3
"""Wave 78 — zero-day-broker / data-localization / heritage-accessibility / xccy-basis / sps-standard-iso.

Bridges Wave 77:
- zero-day-broker ↔ spywareExport.flagMisuse
- data-localization ↔ internetShutdown.flagEconomicImpact
- heritage-accessibility ↔ universalDesign.flagImplementationShortfall
- xccy-basis ↔ treasuryMarketStress.flagFedIntervention
- sps-standard-iso ↔ codexStandard.flagNonHarmonization
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "zero-day-broker",
    "app": "zeroDayBroker",
    "methods": [
      {
        "name": "recordAcquisition",
        "desc": "Zero-day broker acquisition / bounty payout (bridges spywareExport.flagMisuse + cyber-vuln-cve + cyber-threat-actor)",
        "fields": [
          ("acquisitionId", "string", True),
          ("brokerLei", "string", False),
          ("brokerKind", "string", True, ["zdi","zerodium","crowdfense","vigilant_phoenix","inner_zero","tor_broker","nso_internal","government_direct","bug_bounty_premium","marketplace_dark"]),
          ("targetPlatform", "string", True, ["ios_kernel","ios_userspace","ios_chain","android_kernel","android_chain","chrome","edge","firefox","outlook","whatsapp","signal","ms_azure","aws","exchange_server","linux_kernel","macos_kernel","router","smart_tv","printer"]),
          ("spywareVid", "string", False, None, "bridges spywareExport.flagMisuse"),
          ("payoutMusd", "number", False),
          ("acquiredAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagVendorPatchLag",
        "desc": "Patch lag / exploit used in wild / supply chain (bridges spywareExport.flagMisuse + cyber-vuln-patch + cyber-incident-ioc)",
        "fields": [
          ("flagId", "string", True),
          ("acquisitionVid", "string", True, None, "bridges recordAcquisition"),
          ("issueKind", "string", True, ["patch_gap_days","zero_click_itw","broker_disclosure_breach","unfixed_dependency","post_patch_itw","long_tail_unpatched","device_abandonware","citizen_lab_report","itw_before_broker_disclose","re_exploit"]),
          ("daysTillPatch", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "data-localization",
    "app": "dataLocalization",
    "methods": [
      {
        "name": "recordRequirement",
        "desc": "Data localization / sovereignty requirement (bridges internetShutdown.flagEconomicImpact + data-adequacy + cross-border-data)",
        "fields": [
          ("requirementId", "string", True),
          ("countryIso3", "string", True),
          ("regime", "string", True, ["ru_sovereign","cn_dsl_pipl","in_dpdp","id_dps_law","vn_cyber","sa_pdpl","uae_data_law","ke_data_prot","ng_ndpa","br_lgpd_transfer","eu_data_act","chile_pdp"]),
          ("dataCategory", "string", True, ["personal","financial","health","critical_infrastructure","government","iot_sensor","telecom_metadata","biometric","ai_training","genomic","child","payment","geospatial","national_security"]),
          ("shutdownImpactVid", "string", False, None, "bridges internetShutdown.flagEconomicImpact"),
          ("enforcedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFragmentation",
        "desc": "Fragmentation / conflict / extraterritorial reach (bridges internetShutdown.flagEconomicImpact + data-adequacy + crypto-derivatives)",
        "fields": [
          ("flagId", "string", True),
          ("requirementVid", "string", True, None, "bridges recordRequirement"),
          ("concernKind", "string", True, ["conflict_with_gdpr","conflict_cloud_act","transfer_mechanism_lacking","ridiculous_fines","foreign_state_disclosure","data_mirroring_waste","multi_jurisdiction","fintech_disrupt","research_hamper","msme_hit","ai_training_blocked"]),
          ("estBusdImpact", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "heritage-accessibility",
    "app": "heritageAccessibility",
    "methods": [
      {
        "name": "recordRetrofit",
        "desc": "Heritage-building / listed-monument accessibility retrofit (bridges universalDesign.flagImplementationShortfall + cultural-heritage + cultural-repatriation)",
        "fields": [
          ("retrofitId", "string", True),
          ("siteId", "string", True),
          ("heritageKind", "string", True, ["world_heritage","national_listed","religious_structure","castle_fortress","vernacular_housing","industrial","archaeological","cemetery","liturgical","ceremonial","botanic_garden"]),
          ("retrofitKind", "string", True, ["ramp","elevator","tactile_paving","audio_guide","screen_reader_signage","reserved_parking","sensory_rooms","service_dog","video_relay_guide","bsl_british_sign","mobile_app_companion"]),
          ("shortfallVid", "string", False, None, "bridges universalDesign.flagImplementationShortfall"),
          ("completedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagConservationConflict",
        "desc": "Conservation authority conflict / structural risk / exemption (bridges universalDesign.flagImplementationShortfall + cultural-heritage + fpic-consent)",
        "fields": [
          ("flagId", "string", True),
          ("retrofitVid", "string", True, None, "bridges recordRetrofit"),
          ("conflictKind", "string", True, ["conservation_board_refused","structural_load_risk","architectural_intrusion","religious_objection","community_objection","budget_shortfall","planning_permission","heritage_listing_downgrade","tourist_degrade"]),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "xccy-basis",
    "app": "xccyBasis",
    "methods": [
      {
        "name": "recordBasisPoint",
        "desc": "Cross-currency basis swap snapshot (bridges treasuryMarketStress.flagFedIntervention + fx-swap-lines + stablecoin-reserves)",
        "fields": [
          ("snapshotId", "string", True),
          ("pair", "string", True, ["usd_eur","usd_jpy","usd_cny","usd_cad","usd_gbp","eur_jpy","usd_brl","usd_mxn","usd_krw","usd_inr","usd_zar","usd_try"]),
          ("tenor", "string", True, ["1m","3m","6m","1y","2y","5y","10y","30y","ois_spread","sabr_smile","forward_start"]),
          ("basisBps", "number", False),
          ("stressVid", "string", False, None, "bridges treasuryMarketStress.flagFedIntervention"),
          ("asOfTime", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagBlowout",
        "desc": "Basis blowout / funding squeeze (bridges treasuryMarketStress.flagFedIntervention + liquidity-facility + nbfi-stress)",
        "fields": [
          ("flagId", "string", True),
          ("snapshotVid", "string", True, None, "bridges recordBasisPoint"),
          ("regime", "string", True, ["fed_restraint","dollar_shortage","japanese_qe_side_effect","year_end_squeeze","offshore_cny_stress","em_stress","qe_tapering","repo_spike","stigma_borrowing","fima_non_activation","currency_war"]),
          ("peakBasisBps", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "sps-standard-iso",
    "app": "spsStandardIso",
    "methods": [
      {
        "name": "recordStandard",
        "desc": "SPS / ISO traceability standard (ISO 22005 / GlobalGAP / GFSI — bridges codexStandard.flagNonHarmonization + seafood-traceability + rasff-food-safety)",
        "fields": [
          ("standardId", "string", True),
          ("body", "string", True, ["iso_22005","iso_22000","gfsi","globalgap","brc","ifs","fssc_22000","sqf","aspac","gsp_good_supply_practice"]),
          ("domain", "string", True, ["feed","crop","livestock","aquaculture","processed_food","packaging","cold_chain","retail","distribution","waste_handling","lab_accreditation"]),
          ("harmonizationVid", "string", False, None, "bridges codexStandard.flagNonHarmonization"),
          ("publishedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagCertificationSleight",
        "desc": "Certification sleight / equivalence / audit mill (bridges codexStandard.flagNonHarmonization + food-fraud + enforcement-action)",
        "fields": [
          ("flagId", "string", True),
          ("standardVid", "string", True, None, "bridges recordStandard"),
          ("issueKind", "string", True, ["audit_mill","non_equivalent_mutual","cert_forgery","double_dipping","benchmarking_reduction","skipped_re_cert","post_shipment_downgrade","scope_creep","private_public_divergence","ngo_vs_industry"]),
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
            if ftype == "integer" and any(k in col for k in ["size","months","years","days","count","recommendations","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","population","children","excluded","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","casualties","leaked","tco2e","affected","notch","bps","pages","sentence","devices","incidents","countries","detections","dark"]):
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
    out = Path(f"/tmp/wave13/w78_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
