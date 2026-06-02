#!/usr/bin/env python3
"""Generate BPMN dirs, lexicons, and migration seeds for remaining gov country actors.

Usage:
  python gen-gov-bpmn-batch.py [--dry-run]
"""
from __future__ import annotations

import json
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
DRY_RUN = "--dry-run" in sys.argv

COUNTRY_NAMES: dict[str, str] = {
    "alb": "Albania", "and": "Andorra", "are": "United Arab Emirates",
    "arg": "Argentina", "atg": "Antigua and Barbuda", "aus": "Australia",
    "aut": "Austria", "bel": "Belgium", "bgd": "Bangladesh", "bgr": "Bulgaria",
    "bhr": "Bahrain", "bih": "Bosnia and Herzegovina", "blr": "Belarus",
    "bol": "Bolivia", "bra": "Brazil", "brb": "Barbados", "brn": "Brunei",
    "bwa": "Botswana", "can": "Canada", "che": "Switzerland", "chl": "Chile",
    "chn": "China", "civ": "Côte d'Ivoire", "cmr": "Cameroon",
    "cod": "Democratic Republic of the Congo", "col": "Colombia",
    "cri": "Costa Rica", "cub": "Cuba", "cyp": "Cyprus",
    "cze": "Czech Republic", "deu": "Germany", "dma": "Dominica",
    "dnk": "Denmark", "dom": "Dominican Republic", "dza": "Algeria",
    "ecu": "Ecuador", "egy": "Egypt", "esp": "Spain", "est": "Estonia",
    "eth": "Ethiopia", "fin": "Finland", "fji": "Fiji", "fra": "France",
    "gbr": "United Kingdom", "geo": "Georgia", "gha": "Ghana",
    "grc": "Greece", "grd": "Grenada", "gtm": "Guatemala", "guy": "Guyana",
    "hnd": "Honduras", "hrv": "Croatia", "hti": "Haiti", "hun": "Hungary",
    "idn": "Indonesia", "ind": "India", "irl": "Ireland", "irn": "Iran",
    "irq": "Iraq", "isl": "Iceland", "ita": "Italy", "jam": "Jamaica",
    "jor": "Jordan", "jpn": "Japan", "kaz": "Kazakhstan", "ken": "Kenya",
    "kgz": "Kyrgyzstan", "khm": "Cambodia", "kwt": "Kuwait", "lao": "Laos",
    "lbn": "Lebanon", "lby": "Libya", "lka": "Sri Lanka", "ltu": "Lithuania",
    "lux": "Luxembourg", "lva": "Latvia", "mar": "Morocco",
    "mdg": "Madagascar", "mex": "Mexico", "mhl": "Marshall Islands",
    "mkd": "North Macedonia", "mlt": "Malta", "mmr": "Myanmar",
    "mne": "Montenegro", "mng": "Mongolia", "moz": "Mozambique",
    "mys": "Malaysia", "nga": "Nigeria", "nic": "Nicaragua",
    "nld": "Netherlands", "nor": "Norway", "npl": "Nepal",
    "nzl": "New Zealand", "omn": "Oman", "pak": "Pakistan", "pan": "Panama",
    "per": "Peru", "phl": "Philippines", "png": "Papua New Guinea",
    "pol": "Poland", "prt": "Portugal", "pry": "Paraguay",
    "pse": "Palestine", "qat": "Qatar", "rou": "Romania", "rwa": "Rwanda",
    "sau": "Saudi Arabia", "sdn": "Sudan", "sen": "Senegal",
    "sgp": "Singapore", "slv": "El Salvador", "srb": "Serbia",
    "ssd": "South Sudan", "sur": "Suriname", "svk": "Slovakia",
    "svn": "Slovenia", "swe": "Sweden", "tha": "Thailand",
    "tjk": "Tajikistan", "tkm": "Turkmenistan", "tls": "Timor-Leste",
    "tur": "Turkey", "tza": "Tanzania", "uga": "Uganda", "ukr": "Ukraine",
    "ury": "Uruguay", "uzb": "Uzbekistan", "ven": "Venezuela",
    "vnm": "Vietnam", "yem": "Yemen", "zmb": "Zambia", "zwe": "Zimbabwe",
}

# Countries with ingestOfficialSources (already done; kept here for completeness)
WITH_INGEST = {"ago", "hkg", "kor", "prk", "rus", "zaf"}

# Already done
ALREADY_DONE = {"afg", "ago", "hkg", "kor", "prk", "rus", "usa", "zaf"}


def nsid_prefix(cc: str) -> str:
    return f"gov{cc[0].upper()}{cc[1:]}"


def write_file(path: str, content: str) -> None:
    if DRY_RUN:
        print(f"  [dry-run] would write: {path}")
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)


def bpmn_heartbeat(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
    id="Definitions_gov_{c}_heartbeat_tick"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_heartbeat_tick" name="{p} heartbeat tick" isExecutable="true">
    <bpmn:startEvent id="ManualStart" name="manual dispatch">
      <bpmn:outgoing>Flow_Manual_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:startEvent id="Start" name="15 minute tick">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
      <bpmn:timerEventDefinition id="Timer_15m">
        <bpmn:timeCycle xsi:type="bpmn:tFormalExpression">R/PT15M</bpmn:timeCycle>
      </bpmn:timerEventDefinition>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Manual_Task" sourceRef="ManualStart" targetRef="Task_Tick"/>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Tick"/>
    <bpmn:serviceTask id="Task_Tick" name="heartbeat tick">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.heartbeatTick"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=seeded" target="seeded"/>
          <zeebe:output source="=registered" target="registered"/>
          <zeebe:output source="=followed" target="followed"/>
          <zeebe:output source="=wetUpdated" target="wetUpdated"/>
          <zeebe:output source="=shinkaPosted" target="shinkaPosted"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Manual_Task</bpmn:incoming>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Tick" targetRef="End"/>
    <bpmn:endEvent id="End" name="done">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_shinka(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_shinka"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_shinka" name="{p} shinka" isExecutable="true">
    <bpmn:startEvent id="Start" name="shinka requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Shinka"/>
    <bpmn:serviceTask id="Task_Shinka" name="shinka">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.shinka"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=posted" target="posted"/>
          <zeebe:output source="=touched" target="touched"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Shinka" targetRef="End"/>
    <bpmn:endEvent id="End" name="posted">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_seed_orgs(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_seed_orgs"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_seed_orgs" name="{p} seed orgs" isExecutable="true">
    <bpmn:startEvent id="Start" name="seed requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Seed"/>
    <bpmn:serviceTask id="Task_Seed" name="seed orgs">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.seedOrgs"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=seeded" target="seeded"/>
          <zeebe:output source="=remaining" target="remaining"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Seed" targetRef="End"/>
    <bpmn:endEvent id="End" name="seeded">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_register_dids(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_register_dids"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_register_dids" name="{p} register DIDs" isExecutable="true">
    <bpmn:startEvent id="Start" name="registration requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Register"/>
    <bpmn:serviceTask id="Task_Register" name="register DIDs">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.registerDIDs"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=registered" target="registered"/>
          <zeebe:output source="=dids" target="dids"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Register" targetRef="End"/>
    <bpmn:endEvent id="End" name="registered">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_follow_site_deps(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_follow_site_deps"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_follow_site_deps" name="{p} follow site deps" isExecutable="true">
    <bpmn:startEvent id="Start" name="follow requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Follow"/>
    <bpmn:serviceTask id="Task_Follow" name="follow site deps">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.followSiteDeps"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=followed" target="followed"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Follow" targetRef="End"/>
    <bpmn:endEvent id="End" name="followed">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_resolve_org_path(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_resolve_org_path"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_resolve_org_path" name="{p} resolve org path" isExecutable="true">
    <bpmn:startEvent id="Start" name="resolve requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Resolve"/>
    <bpmn:serviceTask id="Task_Resolve" name="resolve org path">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.resolveOrgPath"/>
        <zeebe:ioMapping>
          <zeebe:output source="=did" target="did"/>
          <zeebe:output source="=name" target="name"/>
          <zeebe:output source="=nameEn" target="nameEn"/>
          <zeebe:output source="=website" target="website"/>
          <zeebe:output source="=error" target="error"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Resolve" targetRef="End"/>
    <bpmn:endEvent id="End" name="resolved">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_list_orgs(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_list_orgs"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_list_orgs" name="{p} list orgs" isExecutable="true">
    <bpmn:startEvent id="Start" name="list requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_List"/>
    <bpmn:serviceTask id="Task_List" name="list orgs">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.listOrgs"/>
        <zeebe:ioMapping>
          <zeebe:output source="=orgs" target="orgs"/>
          <zeebe:output source="=total" target="total"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_List" targetRef="End"/>
    <bpmn:endEvent id="End" name="listed">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_sync_wet_updates(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_sync_wet_updates"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_sync_wet_updates" name="{p} sync wet updates" isExecutable="true">
    <bpmn:startEvent id="Start" name="sync requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Sync"/>
    <bpmn:serviceTask id="Task_Sync" name="sync wet updates">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.syncWetUpdates"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=checked" target="checked"/>
          <zeebe:output source="=updated" target="updated"/>
          <zeebe:output source="=posted" target="posted"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Sync" targetRef="End"/>
    <bpmn:endEvent id="End" name="synced">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def bpmn_ingest_official_sources(cc: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<bpmn:definitions
    xmlns:bpmn="http://www.omg.org/spec/BPMN/20100524/MODEL"
    xmlns:zeebe="http://camunda.org/schema/zeebe/1.0"
    id="Definitions_gov_{c}_ingest_official_sources"
    targetNamespace="https://etzhayyim.com/bpmn/{p}"
    exporter="hand-written"
    exporterVersion="1.0">
  <bpmn:process id="gov_{c}_ingest_official_sources" name="{p} ingest official sources" isExecutable="true">
    <bpmn:startEvent id="Start" name="ingest requested">
      <bpmn:outgoing>Flow_Task</bpmn:outgoing>
    </bpmn:startEvent>
    <bpmn:sequenceFlow id="Flow_Task" sourceRef="Start" targetRef="Task_Ingest"/>
    <bpmn:serviceTask id="Task_Ingest" name="ingest official sources">
      <bpmn:extensionElements>
        <zeebe:taskDefinition type="xrpc.com.etzhayyim.{p}.ingestOfficialSources"/>
        <zeebe:ioMapping>
          <zeebe:output source="=ok" target="ok"/>
          <zeebe:output source="=enqueued" target="enqueued"/>
          <zeebe:output source="=targets" target="targets"/>
          <zeebe:output source="=processed" target="processed"/>
          <zeebe:output source="=processStatus" target="processStatus"/>
        </zeebe:ioMapping>
      </bpmn:extensionElements>
      <bpmn:incoming>Flow_Task</bpmn:incoming>
      <bpmn:outgoing>Flow_End</bpmn:outgoing>
    </bpmn:serviceTask>
    <bpmn:sequenceFlow id="Flow_End" sourceRef="Task_Ingest" targetRef="End"/>
    <bpmn:endEvent id="End" name="ingest queued">
      <bpmn:incoming>Flow_End</bpmn:incoming>
    </bpmn:endEvent>
  </bpmn:process>
</bpmn:definitions>
"""


def lexicon_heartbeat_tick(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.heartbeatTick",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Run the {country_name} government actor scheduled maintenance loop through Zeebe.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "seedLimit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 30},
                            "registerLimit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                            "followLimit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 15},
                            "ingestLimit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
                            "shinkaLimit": {"type": "integer", "minimum": 1, "maximum": 5, "default": 1},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "seeded": {"type": "integer"},
                            "registered": {"type": "integer"},
                            "followed": {"type": "integer"},
                            "wetUpdated": {"type": "integer"},
                            "shinkaPosted": {"type": "integer"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_shinka(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.shinka",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Post a periodic graph-visible {country_name} government organization update.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 5, "default": 1},
                            "postUpdates": {"type": "boolean", "default": True},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "posted": {"type": "integer"},
                            "touched": {"type": "integer"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_seed_orgs(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.seedOrgs",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Seed initial {country_name} government organization records into the graph.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 200, "default": 50},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "seeded": {"type": "integer"},
                            "remaining": {"type": "integer"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_register_dids(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.registerDIDs",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Register DIDs for {country_name} government organizations.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "registered": {"type": "integer"},
                            "dids": {"type": "array", "items": {"type": "string"}},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_follow_site_deps(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.followSiteDeps",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Follow site dependency actors for {country_name} government.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 15},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "followed": {"type": "integer"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_resolve_org_path(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.resolveOrgPath",
        "defs": {
            "main": {
                "type": "query",
                "description": f"Resolve a {country_name} government organization path to its graph record.",
                "parameters": {
                    "type": "params",
                    "properties": {
                        "path": {"type": "string"},
                        "lang": {"type": "string"},
                    },
                    "required": ["path"],
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "did": {"type": "string"},
                            "name": {"type": "string"},
                            "nameEn": {"type": "string"},
                            "website": {"type": "string"},
                            "error": {"type": "string"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_list_orgs(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.listOrgs",
        "defs": {
            "main": {
                "type": "query",
                "description": f"List {country_name} government organization graph records.",
                "parameters": {
                    "type": "params",
                    "properties": {
                        "limit": {"type": "integer", "minimum": 1, "maximum": 100, "default": 50},
                        "offset": {"type": "integer", "minimum": 0, "default": 0},
                        "q": {"type": "string"},
                    },
                    "required": [],
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "orgs": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "did": {"type": "string"},
                                        "name": {"type": "string"},
                                        "website": {"type": "string"},
                                    },
                                    "required": [],
                                },
                            },
                            "total": {"type": "integer"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_sync_wet_updates(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.syncWetUpdates",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Sync recent {country_name} government organization changes to graph.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 10},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "checked": {"type": "integer"},
                            "updated": {"type": "integer"},
                            "posted": {"type": "integer"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def lexicon_ingest_official_sources(cc: str, country_name: str) -> dict:
    p = nsid_prefix(cc)
    return {
        "lexicon": 1,
        "id": f"com.etzhayyim.{p}.ingestOfficialSources",
        "defs": {
            "main": {
                "type": "procedure",
                "description": f"Ingest official {country_name} government data sources into the graph.",
                "input": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "limit": {"type": "integer", "minimum": 1, "maximum": 50, "default": 5},
                        },
                        "required": [],
                    },
                },
                "output": {
                    "encoding": "application/json",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "ok": {"type": "boolean"},
                            "enqueued": {"type": "integer"},
                            "targets": {"type": "integer"},
                            "processed": {"type": "integer"},
                            "processStatus": {"type": "string"},
                        },
                        "required": [],
                    },
                },
            }
        },
    }


def generate_migration(cc: str, country_name: str, has_ingest: bool, timestamp: str) -> str:
    p = nsid_prefix(cc)
    c = cc.lower()
    owner_did = f"did:web:{c}-state.etzhayyim.com"
    actor_host = f"{c}-state.etzhayyim.com"
    actor_tag = f"sys.bpmn.seed.gov-{c}"
    created_at = f"2026-05-07T{timestamp[8:10]}:{timestamp[10:12]}:{timestamp[12:14]}Z"

    seeds_base = [
        (f"gov-{c}-seedOrgs-v1", f"com.etzhayyim.{p}.seedOrgs", f"gov_{c}_seed_orgs", f"govDir/seedOrgs.bpmn", 90_000),
        (f"gov-{c}-registerDIDs-v1", f"com.etzhayyim.{p}.registerDIDs", f"gov_{c}_register_dids", f"govDir/registerDIDs.bpmn", 90_000),
        (f"gov-{c}-followSiteDeps-v1", f"com.etzhayyim.{p}.followSiteDeps", f"gov_{c}_follow_site_deps", f"govDir/followSiteDeps.bpmn", 90_000),
    ]
    if has_ingest:
        seeds_base.append((f"gov-{c}-ingestOfficialSources-v1", f"com.etzhayyim.{p}.ingestOfficialSources", f"gov_{c}_ingest_official_sources", f"govDir/ingestOfficialSources.bpmn", 180_000))
    seeds_base += [
        (f"gov-{c}-resolveOrgPath-v1", f"com.etzhayyim.{p}.resolveOrgPath", f"gov_{c}_resolve_org_path", f"govDir/resolveOrgPath.bpmn", 60_000),
        (f"gov-{c}-listOrgs-v1", f"com.etzhayyim.{p}.listOrgs", f"gov_{c}_list_orgs", f"govDir/listOrgs.bpmn", 60_000),
        (f"gov-{c}-syncWetUpdates-v1", f"com.etzhayyim.{p}.syncWetUpdates", f"gov_{c}_sync_wet_updates", f"govDir/syncWetUpdates.bpmn", 180_000),
        (f"gov-{c}-shinka-v1", f"com.etzhayyim.{p}.shinka", f"gov_{c}_shinka", f"govDir/shinka.bpmn", 180_000),
        (f"gov-{c}-heartbeatTick-v1", f"com.etzhayyim.{p}.heartbeatTick", f"gov_{c}_heartbeat_tick", f"govDir/heartbeatTick.bpmn", 180_000),
    ]

    gov_dir = f"gov{c[0].upper()}{c[1:]}"

    seeds_str = ""
    for (vid, nsid, proc_id, src_tmpl, timeout) in seeds_base:
        src = src_tmpl.replace("govDir", f"00-contracts/bpmn/com/etzhayyim/{gov_dir}")
        seeds_str += f"""  {{
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/{vid}",
    nsid: "{nsid}",
    bpmnProcessId: "{proc_id}",
    sourcePath: "{src}",
    resultTimeoutMs: {timeout:_},
  }},
"""

    # kebab seeds (same list but with kebab vertex IDs and process IDs)
    kebab_map = {
        "seedOrgs": "seed-orgs", "registerDIDs": "register-dids",
        "followSiteDeps": "follow-site-deps", "ingestOfficialSources": "ingest-official-sources",
        "resolveOrgPath": "resolve-org-path", "listOrgs": "list-orgs",
        "syncWetUpdates": "sync-wet-updates", "shinka": "shinka",
        "heartbeatTick": "heartbeat-tick",
    }
    proc_kebab_map = {
        "seedOrgs": "seed_orgs", "registerDIDs": "register_dids",
        "followSiteDeps": "follow_site_deps", "ingestOfficialSources": "ingest_official_sources",
        "resolveOrgPath": "resolve_org_path", "listOrgs": "list_orgs",
        "syncWetUpdates": "sync_wet_updates", "shinka": "shinka",
        "heartbeatTick": "heartbeat_tick",
    }
    for (vid, nsid, proc_id, src_tmpl, timeout) in seeds_base:
        method = nsid.split(".")[-1]
        if method not in kebab_map:
            continue
        k_vid = f"gov-{c}-{kebab_map[method]}-v1"
        if k_vid == vid:
            continue  # shinka has no distinct kebab
        k_proc = f"gov_{c}_{proc_kebab_map[method]}"
        src = src_tmpl.replace("govDir", f"00-contracts/bpmn/com/etzhayyim/{gov_dir}")
        seeds_str += f"""  {{
    vertexId: "at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.processDef/{k_vid}",
    nsid: "{nsid}",
    bpmnProcessId: "{k_proc}",
    sourcePath: "{src}",
    resultTimeoutMs: {timeout:_},
  }},
"""

    return f"""import {{ createHash }} from "node:crypto";
import {{ readFileSync }} from "node:fs";
import * as path from "node:path";
import {{ fileURLToPath }} from "node:url";
import type {{ Kysely }} from "kysely";
import {{ sql }} from "kysely";

type ProcessSeed = {{
  vertexId: string;
  nsid: string;
  bpmnProcessId: string;
  sourcePath: string;
  resultTimeoutMs: number;
}};

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const repoRoot = path.resolve(__dirname, "..", "..", "..");
const createdAt = "{created_at}";
const ownerDid = "{owner_did}";
const actorHost = "{actor_host}";
const actorTag = "{actor_tag}";
const writeTableAllowlist = [
  "vertex_gov_org",
  "vertex_gov_actor_manifest",
  "edge_gov_org_site_dependency",
].join(",");

const seeds: ProcessSeed[] = [
{seeds_str}];

function readContract(relPath: string): string {{
  return readFileSync(path.resolve(repoRoot, relPath), "utf8");
}}

function lexiconPath(nsid: string): string {{
  return `00-contracts/lexicons/${{nsid.replaceAll(".", "/") }}.json`;
}}

function mcpVertexId(nsid: string): string {{
  return `at://${{ownerDid}}/com.etzhayyim.mcp.toolDef/${{nsid.replaceAll(".", "-")}}`;
}}

function bindingVertexId(nsid: string): string {{
  return `at://did:web:bpmn.etzhayyim.com/com.etzhayyim.apps.bpmn.binding/${{nsid.replaceAll(".", "-")}}-v1`;
}}

function stableStringify(value: unknown): string {{
  if (value === null || typeof value !== "object") return JSON.stringify(value);
  if (Array.isArray(value)) return `[${{(value as unknown[]).map((item) => stableStringify(item)).join(",")}}]`;
  const record = value as Record<string, unknown>;
  return `{{${{Object.keys(record)
    .sort()
    .map((key) => `${{JSON.stringify(key)}}:${{stableStringify(record[key])}}`)
    .join(",")}}}}`;
}}

function readLexiconTool(seed: ProcessSeed): {{
  lexiconType: string;
  description: string;
  inputSchema: string;
  outputSchema: string;
  schemaHash: string;
  sourcePath: string;
}} {{
  const sourcePath = lexiconPath(seed.nsid);
  const raw = readContract(sourcePath);
  const doc = JSON.parse(raw) as {{
    defs?: {{
      main?: {{
        type?: string;
        description?: string;
        parameters?: unknown;
        input?: {{ schema?: unknown }};
        output?: {{ schema?: unknown }};
      }};
    }};
  }};
  const main = doc.defs?.main ?? {{}};
  const lexiconType = main.type ?? "procedure";
  const input = lexiconType === "query" ? main.parameters ?? {{}} : main.input?.schema ?? {{}};
  const output = main.output?.schema ?? {{}};
  const description = main.description ?? "";
  const inputSchema = stableStringify(input);
  const outputSchema = stableStringify(output);
  const schemaHash = createHash("sha256")
    .update(`${{description}}\\0${{inputSchema}}\\0${{outputSchema}}`)
    .digest("hex")
    .slice(0, 16);
  return {{ lexiconType, description, inputSchema, outputSchema, schemaHash, sourcePath }};
}}

async function insertProcessDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {{
  const xml = readContract(seed.sourcePath);
  const xmlByteSize = Buffer.byteLength(xml, "utf8");
  await sql`
    INSERT INTO vertex_bpmn_process_def (
      vertex_id, owner_did, bpmn_process_id, version, xml, xml_byte_size,
      source_path, status, created_at, sensitivity_ord, org_id, user_id, actor_id
    )
    SELECT
      ${{seed.vertexId}}, ${{ownerDid}}, ${{seed.bpmnProcessId}}, 1,
      ${{xml}}, CAST(${{xmlByteSize}} AS integer), ${{seed.sourcePath}}, 'active',
      ${{createdAt}}, 1, ${{ownerDid}}, ${{ownerDid}}, ${{actorTag}}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_process_def WHERE vertex_id = ${{seed.vertexId}}
    )
  `.execute(db);
}}

async function insertBinding(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {{
  const vertexId = bindingVertexId(seed.nsid);
  await sql`
    INSERT INTO vertex_bpmn_lexicon_binding (
      vertex_id, owner_did, nsid, bpmn_process_id, bpmn_version,
      result_timeout_ms, status, created_at, sensitivity_ord, org_id, user_id,
      actor_id, write_table_allowlist
    )
    SELECT
      ${{vertexId}}, ${{ownerDid}}, ${{seed.nsid}}, ${{seed.bpmnProcessId}}, 1,
      CAST(${{seed.resultTimeoutMs}} AS integer), 'active', ${{createdAt}}, 1,
      ${{ownerDid}}, ${{ownerDid}}, ${{actorTag}}, ${{writeTableAllowlist}}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${{vertexId}}
    )
  `.execute(db);
}}

async function insertMcpToolDef(db: Kysely<unknown>, seed: ProcessSeed): Promise<void> {{
  const tool = readLexiconTool(seed);
  const vertexId = mcpVertexId(seed.nsid);
  await sql`
    INSERT INTO vertex_mcp_tool_def (
      vertex_id, nsid, actor_did, actor_host, lexicon_type, description,
      input_schema, output_schema, lxm_scope, visibility, version, enabled,
      source_path, schema_hash, owner_did, sensitivity_ord, org_id, user_id,
      actor_id, created_at
    )
    SELECT
      ${{vertexId}}, ${{seed.nsid}}, ${{ownerDid}}, ${{actorHost}}, ${{tool.lexiconType}},
      ${{tool.description}}, ${{tool.inputSchema}}, ${{tool.outputSchema}}, ${{seed.nsid}},
      'public', 1, TRUE, ${{tool.sourcePath}}, ${{tool.schemaHash}}, ${{ownerDid}}, 1,
      ${{ownerDid}}, ${{ownerDid}}, ${{actorTag}}, ${{createdAt}}
    WHERE NOT EXISTS (
      SELECT 1 FROM vertex_mcp_tool_def WHERE vertex_id = ${{vertexId}}
    )
  `.execute(db);
}}

export async function up(db: Kysely<unknown>): Promise<void> {{
  for (const seed of seeds) await insertProcessDef(db, seed);
  for (const seed of seeds) await insertBinding(db, seed);
  for (const seed of seeds) await insertMcpToolDef(db, seed);
}}

export async function down(db: Kysely<unknown>): Promise<void> {{
  for (const seed of seeds) {{
    await sql`DELETE FROM vertex_mcp_tool_def WHERE vertex_id = ${{mcpVertexId(seed.nsid)}}`.execute(db);
  }}
  for (const seed of seeds) {{
    await sql`DELETE FROM vertex_bpmn_lexicon_binding WHERE vertex_id = ${{bindingVertexId(seed.nsid)}}`.execute(db);
  }}
  for (const seed of seeds) {{
    await sql`DELETE FROM vertex_bpmn_process_def WHERE vertex_id = ${{seed.vertexId}}`.execute(db);
  }}
}}
"""


def main() -> None:
    # Countries to process (skip already done and fetch_proxy)
    all_ccs = sorted(COUNTRY_NAMES.keys())
    remaining = [cc for cc in all_ccs if cc not in ALREADY_DONE]

    print(f"Generating files for {len(remaining)} countries...")

    routing_entries = []
    migration_index = 0

    for cc in remaining:
        country_name = COUNTRY_NAMES[cc]
        p = nsid_prefix(cc)
        has_ingest = cc in WITH_INGEST

        # Base hour/minute for timestamp (start at 14:00:00)
        base_min = 14 * 60 + migration_index
        hh = base_min // 60
        mm = base_min % 60
        ts_body = f"2026050714{hh:02d}{mm:02d}00"  # but we want YYYYMMDDHHMMSS
        # Actually format: 20260507HHMMSS
        ts = f"20260507{hh:02d}{mm:02d}00"

        # 1. BPMN files
        bpmn_dir = os.path.join(REPO_ROOT, f"00-contracts/bpmn/com/etzhayyim/{p}")
        write_file(os.path.join(bpmn_dir, "heartbeatTick.bpmn"), bpmn_heartbeat(cc))
        write_file(os.path.join(bpmn_dir, "shinka.bpmn"), bpmn_shinka(cc))
        write_file(os.path.join(bpmn_dir, "seedOrgs.bpmn"), bpmn_seed_orgs(cc))
        write_file(os.path.join(bpmn_dir, "registerDIDs.bpmn"), bpmn_register_dids(cc))
        write_file(os.path.join(bpmn_dir, "followSiteDeps.bpmn"), bpmn_follow_site_deps(cc))
        write_file(os.path.join(bpmn_dir, "resolveOrgPath.bpmn"), bpmn_resolve_org_path(cc))
        write_file(os.path.join(bpmn_dir, "listOrgs.bpmn"), bpmn_list_orgs(cc))
        write_file(os.path.join(bpmn_dir, "syncWetUpdates.bpmn"), bpmn_sync_wet_updates(cc))
        if has_ingest:
            write_file(os.path.join(bpmn_dir, "ingestOfficialSources.bpmn"), bpmn_ingest_official_sources(cc))

        # 2. Lexicon JSON files
        lex_dir = os.path.join(REPO_ROOT, f"00-contracts/lexicons/com/etzhayyim/{p}")
        for name, content in [
            ("heartbeatTick.json", lexicon_heartbeat_tick(cc, country_name)),
            ("shinka.json", lexicon_shinka(cc, country_name)),
            ("seedOrgs.json", lexicon_seed_orgs(cc, country_name)),
            ("registerDIDs.json", lexicon_register_dids(cc, country_name)),
            ("followSiteDeps.json", lexicon_follow_site_deps(cc, country_name)),
            ("resolveOrgPath.json", lexicon_resolve_org_path(cc, country_name)),
            ("listOrgs.json", lexicon_list_orgs(cc, country_name)),
            ("syncWetUpdates.json", lexicon_sync_wet_updates(cc, country_name)),
        ]:
            write_file(os.path.join(lex_dir, name), json.dumps(content, indent=2, ensure_ascii=False) + "\n")
        if has_ingest:
            write_file(
                os.path.join(lex_dir, "ingestOfficialSources.json"),
                json.dumps(lexicon_ingest_official_sources(cc, country_name), indent=2, ensure_ascii=False) + "\n",
            )

        # 3. Migration file
        mig_path = os.path.join(
            REPO_ROOT,
            f"30-graph/graph-schema/migrations/{ts}_seed_gov_{cc}_bpmn_mcp_registry.ts",
        )
        write_file(mig_path, generate_migration(cc, country_name, has_ingest, ts))

        # 4. Routing entry
        routing_entries.append(
            f'  {{ prefix: "com.etzhayyim.{p}.", target: {{ kind: "http", actor: "{cc}-state.etzhayyim.com" }},\n'
            f'    trust: "internal", fallback: "local", owner: "gov{cc.capitalize()} BPMN-as-actor (ADR-0056, 2026-05-07)" }},'
        )

        migration_index += 1

    # Print routing entries for manual insertion
    routing_file = os.path.join(REPO_ROOT, "70-tools/scripts/contract/gov-routing-entries.txt")
    write_file(routing_file, "\n".join(routing_entries) + "\n")

    if not DRY_RUN:
        print(f"Generated {len(remaining)} countries")
        print(f"Routing entries written to: 70-tools/scripts/contract/gov-routing-entries.txt")
    else:
        print(f"[dry-run] Would generate {len(remaining)} countries")


if __name__ == "__main__":
    main()
