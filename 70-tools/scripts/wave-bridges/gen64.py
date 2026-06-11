#!/usr/bin/env python3
"""Wave 64 — scotus-docket / art-market-aml / humanitarian-corridor / gender-inclusion / recycled-content-verify.

Bridges Wave 63:
- scotus-docket ↔ tosArbitration.flagUnconscionability
- art-market-aml ↔ provenanceResearch.flagProvenanceGap
- humanitarian-corridor ↔ remittanceCorridor.flagCorridorStress
- gender-inclusion ↔ apprenticeshipReg.flagCompletionGap
- recycled-content-verify ↔ eprPackaging.flagEcomodulationGap
"""
import json
from pathlib import Path
REPO = Path("/Users/junkawasaki/github/etzhayyim/root")

ACTORS = [
  {
    "slug": "scotus-docket",
    "app": "scotusDocket",
    "methods": [
      {
        "name": "recordCertGrant",
        "desc": "SCOTUS / apex court cert grant (bridges tosArbitration.flagUnconscionability + federal-court-docket + civil-liability)",
        "fields": [
          ("certId", "string", True),
          ("court", "string", True, ["scotus","uk_supreme","in_supreme","au_high_court","ca_supreme","eu_cjeu","echr_grand","br_stf","sa_constitutional","icj","itlos","arbitral_uncitral"]),
          ("caseNumber", "string", True),
          ("questionPresented", "string", True, ["arbitration_preemption","preemption","first_amendment","equal_protection","administrative_deference","nondelegation","commerce_clause","takings","search_seizure","qualified_immunity","voting_rights","class_action","stare_decisis"]),
          ("unconscionabilityVid", "string", False, None, "bridges tosArbitration.flagUnconscionability"),
          ("grantedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagDoctrinalShift",
        "desc": "Overturn / major questions / Chevron shift (bridges tosArbitration.flagUnconscionability + treasuryRulemaking.flagChallenge + federal-court-docket)",
        "fields": [
          ("flagId", "string", True),
          ("certVid", "string", True, None, "bridges recordCertGrant"),
          ("shiftKind", "string", True, ["overturn_precedent","major_questions","chevron_retreat","nondelegation_revival","private_rights_of_action","implied_preemption","concurrent_jurisdiction","categorical_rule","balancing_test","textualism_narrowing"]),
          ("downstreamStatutesAffected", "integer", False),
          ("ruledAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "art-market-aml",
    "app": "artMarketAml",
    "methods": [
      {
        "name": "recordTransaction",
        "desc": "Art market transaction (EU 6AMLD / US BFAA — bridges provenanceResearch.flagProvenanceGap + sanctions-entry + beneficial-ownership)",
        "fields": [
          ("transactionId", "string", True),
          ("participantLei", "string", False),
          ("participantKind", "string", True, ["auction_house","dealer","gallery","freeport","private_sale","nft_platform","advisor","agent","shipper","conservator"]),
          ("transactionValueEur", "number", False),
          ("triggersKyc", "boolean", False, None, "≥10k EUR threshold"),
          ("provenanceGapVid", "string", False, None, "bridges provenanceResearch.flagProvenanceGap"),
          ("settledAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagMoneyLaundering",
        "desc": "Money laundering / sanctions evasion via art (bridges provenanceResearch.flagProvenanceGap + ofac-sanctions-sdn + beneficial-ownership)",
        "fields": [
          ("flagId", "string", True),
          ("transactionVid", "string", True, None, "bridges recordTransaction"),
          ("typology", "string", True, ["overvaluation","back_to_back","freeport_hiding","shell_lbo","nft_washtrading","fractionalization_opaque","consigner_chain_opaque","export_sanctions","forged_provenance","commingled_invest"]),
          ("suspectedValueEur", "number", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "humanitarian-corridor",
    "app": "humanitarianCorridor",
    "methods": [
      {
        "name": "recordCorridor",
        "desc": "Humanitarian corridor / UN OCHA access (bridges remittanceCorridor.flagCorridorStress + refugee-unhcr + ocha-funding)",
        "fields": [
          ("corridorId", "string", True),
          ("theater", "string", True, ["gaza_strip","lebanon","syria","yemen","sudan","ethiopia","somalia","dr_congo","mozambique","myanmar","ukraine","haiti","afghanistan","sahel","venezuela"]),
          ("mechanism", "string", True, ["cross_border","cross_line","humanitarian_pause","deconfliction","safe_passage","evacuation","airdrop","sea_corridor","civil_military"]),
          ("leadAgency", "string", True, ["ocha","wfp","unhcr","unicef","icrc","msf","red_crescent","savethechildren","care","mercy_corps"]),
          ("remittanceStressVid", "string", False, None, "bridges remittanceCorridor.flagCorridorStress"),
          ("openedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagAccessDenial",
        "desc": "Access denial / attack on aid workers / starvation siege (bridges remittanceCorridor.flagCorridorStress + refugee-unhcr + worker-grievance)",
        "fields": [
          ("flagId", "string", True),
          ("corridorVid", "string", True, None, "bridges recordCorridor"),
          ("denialKind", "string", True, ["parties_block","siege","checkpoint_extortion","aid_worker_attack","truck_convoy_intercept","deconfliction_violated","visa_denial","bureaucratic_delay","sanctions_self_block","weaponized_starvation"]),
          ("personsAffected", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "gender-inclusion",
    "app": "genderInclusion",
    "methods": [
      {
        "name": "recordPayGapDisclosure",
        "desc": "Gender pay gap / EU Pay Transparency Directive / UK GPG disclosure (bridges apprenticeshipReg.flagCompletionGap + labor-rights + gender-pay-gap)",
        "fields": [
          ("disclosureId", "string", True),
          ("employerLei", "string", False),
          ("regime", "string", True, ["eu_pay_transparency","uk_gpg","us_eeoc","ca_pay_equity","au_wgea","jp_act_women","kr_gender_equality","de_entgelttrans","fr_index_egalite","nl_gelijkheid"]),
          ("gapUnadjustedPct", "number", False),
          ("gapAdjustedPct", "number", False),
          ("completionGapVid", "string", False, None, "bridges apprenticeshipReg.flagCompletionGap"),
          ("disclosedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagHarassment",
        "desc": "ILO C190 harassment / #MeToo enforcement (bridges apprenticeshipReg.flagCompletionGap + worker-grievance + ilo-labor-rights)",
        "fields": [
          ("flagId", "string", True),
          ("disclosureVid", "string", True, None, "bridges recordPayGapDisclosure"),
          ("incidentKind", "string", True, ["sexual_harassment","hostile_work","retaliation","nda_silencing","quid_pro_quo","pregnancy_discrim","lactation","equal_pay_act","title_vii","ilo_c190_breach"]),
          ("complainantsCount", "integer", False),
          ("reportedAt", "string", True),
        ],
        "classify": None,
      },
    ],
  },
  {
    "slug": "recycled-content-verify",
    "app": "recycledContentVerify",
    "methods": [
      {
        "name": "recordAudit",
        "desc": "Recycled content audit / mass balance / ISO 14021 (bridges eprPackaging.flagEcomodulationGap + plastic-treaty + chemicals-management)",
        "fields": [
          ("auditId", "string", True),
          ("auditorLei", "string", False),
          ("productLine", "string", True),
          ("standard", "string", True, ["iso_14021","iso_14044","iso_22095","recyclass","apr_plastic","mass_balance","rci_ri_cert","pcr_scs","grs_textile","rcs_textile","rec_iso_20915"]),
          ("recycledPctClaimed", "number", True),
          ("recycledPctVerified", "number", False),
          ("ecomodGapVid", "string", False, None, "bridges eprPackaging.flagEcomodulationGap"),
          ("auditedAt", "string", True),
        ],
        "classify": None,
      },
      {
        "name": "flagFraud",
        "desc": "Recycled content fraud / mass balance misallocation (bridges eprPackaging.flagEcomodulationGap + enforcement-action + consumer-protection)",
        "fields": [
          ("flagId", "string", True),
          ("auditVid", "string", True, None, "bridges recordAudit"),
          ("fraudKind", "string", True, ["percentage_overstated","mass_balance_double_claim","chemical_recycling_gap","off_spec_blend","counterfeit_pellets","substitution_with_virgin","chain_of_custody_break","offset_abuse","certification_forged","unauthorized_logo"]),
          ("affectedSkuCount", "integer", False),
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
            if ftype == "integer" and any(k in col for k in ["size","years","count","hours","refusals","doses","shortfall","customers","beneficiar","units","tonnes","volume","persons","capacity","members","passed","impacted","workers","covered","premises","cases","issued","barrels","claimants","corridors","objects","investigators","sku","complainants","statutes","affected"]):
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
    out = Path(f"/tmp/wave13/w64_{i:02d}.sql")
    out.write_text(ddl)
    print(f"wrote {out}")
