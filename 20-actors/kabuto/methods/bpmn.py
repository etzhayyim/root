#!/usr/bin/env python3
"""kabuto 兜 — per-company BPMN 2.0 process-model emitter.

ADR-2606022000. Emits GENERIC, well-formed BPMN 2.0 XML workflow templates for
each seeded company (a procurement template + a disclosure template), anchors
each as a content hash (kotoba-CID stand-in for R0), and writes the queryable
:company.process/* datoms (with the computed bpmn-cid) back into the Datom log.

HONEST (G5): these are :synthesized GENERIC templates — they describe a plausible
public procurement / disclosure workflow, NOT a company's actual internal process.
They give the supply-chain graph an executable process layer (BPMN is a first-class
substrate primitive — see 00-contracts/lexicons/.../bpmn). The BPMN XML validates
against the OMG BPMN 2.0 namespace; render it in bpmn-js (yoro already bundles it).

stdlib only. Usage:
    python3 bpmn.py [seed.edn] [--out OUTDIR]
"""
from __future__ import annotations
import sys
import os
import hashlib
import pathlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from kabuto_edn import load_edn, classify, edn_str  # noqa: E402

BPMN_NS = "http://www.omg.org/spec/BPMN/20100524/MODEL"

# (kind, process-name, [task labels]) generic templates
TEMPLATES = {
    ":procurement": ("Supplier procurement",
                     ["Identify supply need", "Issue RFQ to qualified suppliers",
                      "Evaluate bids (cost / capacity / ESG)", "Award & onboard supplier",
                      "Place purchase order", "Receive & inspect goods"]),
    ":disclosure": ("Supply-chain disclosure",
                    ["Collect supplier list", "Run human-rights / ESG due diligence",
                     "Aggregate findings (aggregate-first)", "Publish public disclosure report"]),
}


def _xml_escape(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def build_bpmn(process_id: str, name: str, company_name: str, tasks: list[str]) -> str:
    """Return well-formed BPMN 2.0 XML: start → tasks (sequence) → end.

    Emits a full BPMNDI (diagram-interchange) section with a deterministic
    left-to-right layout, so the file renders directly in any BPMN viewer
    (bpmn-js needs DI coordinates — it does NOT auto-layout). The chain is
    strictly linear, so the layout is a single horizontal lane.
    """
    start = f"{process_id}_start"
    end = f"{process_id}_end"
    task_ids = [f"{process_id}_t{i}" for i in range(len(tasks))]
    seq = [start] + task_ids + [end]
    kinds = ["event"] + ["task"] * len(tasks) + ["event"]

    # ── geometry: lay the chain out left → right on one horizontal lane ──
    CY, GAP = 120, 60            # vertical centre-line, horizontal gap between nodes
    geom = {}                    # id -> (x, y, w, h)
    x = 160
    for nid, kind in zip(seq, kinds):
        w, h = (100, 80) if kind == "task" else (36, 36)
        geom[nid] = (x, CY - h // 2, w, h)
        x += w + GAP

    # ── semantic model ──
    nodes = [f'      <startEvent id="{start}" name="Start"/>']
    for tid, label in zip(task_ids, tasks):
        nodes.append(f'      <task id="{tid}" name="{_xml_escape(label)}"/>')
    nodes.append(f'      <endEvent id="{end}" name="Done"/>')

    flows, flow_pairs = [], []
    for i in range(len(seq) - 1):
        fid = f"{process_id}_f{i}"
        flows.append(
            f'      <sequenceFlow id="{fid}" sourceRef="{seq[i]}" targetRef="{seq[i+1]}"/>')
        flow_pairs.append((fid, seq[i], seq[i + 1]))

    # ── diagram interchange (BPMNDI) ──
    di = [f'    <bpmndi:BPMNPlane id="plane_{process_id}" bpmnElement="{process_id}">']
    for nid in seq:
        gx, gy, gw, gh = geom[nid]
        di.append(
            f'      <bpmndi:BPMNShape id="{nid}_di" bpmnElement="{nid}">'
            f'<omgdc:Bounds x="{gx}" y="{gy}" width="{gw}" height="{gh}"/>'
            f'</bpmndi:BPMNShape>')
    for fid, s, t in flow_pairs:
        sx, sy, sw, sh = geom[s]
        tx, ty, tw, th = geom[t]
        di.append(
            f'      <bpmndi:BPMNEdge id="{fid}_di" bpmnElement="{fid}">'
            f'<omgdi:waypoint x="{sx + sw}" y="{sy + sh // 2}"/>'
            f'<omgdi:waypoint x="{tx}" y="{ty + th // 2}"/>'
            f'</bpmndi:BPMNEdge>')
    di.append('    </bpmndi:BPMNPlane>')

    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<definitions xmlns="{BPMN_NS}" '
        'xmlns:bpmndi="http://www.omg.org/spec/BPMN/20100524/DI" '
        'xmlns:omgdc="http://www.omg.org/spec/DD/20100524/DC" '
        'xmlns:omgdi="http://www.omg.org/spec/DD/20100524/DI" '
        f'targetNamespace="https://etzhayyim.com/ns/kabuto/bpmn" '
        f'id="def_{process_id}">\n'
        f'  <!-- kabuto 兜 generic :synthesized template for {_xml_escape(company_name)} '
        f'(ADR-2606022000). NOT the company\'s actual internal process. -->\n'
        f'  <process id="{process_id}" name="{_xml_escape(name)} — {_xml_escape(company_name)}" '
        f'isExecutable="false">\n'
        + "\n".join(nodes) + "\n"
        + "\n".join(flows) + "\n"
        '  </process>\n'
        f'  <bpmndi:BPMNDiagram id="di_{process_id}">\n'
        + "\n".join(di) + "\n"
        '  </bpmndi:BPMNDiagram>\n'
        '</definitions>\n'
    )


def content_cid(data: str) -> str:
    """Deterministic content hash standing in for a kotoba-CID at R0."""
    return "cid.sha256:" + hashlib.sha256(data.encode("utf-8")).hexdigest()[:32]


def main(argv):
    here = pathlib.Path(__file__).resolve().parent.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith('--') \
        else here / "data" / "seed-public-companies.kotoba.edn"
    outdir = here / "out"
    if "--out" in argv:
        outdir = pathlib.Path(argv[argv.index("--out") + 1])
    bpmndir = outdir / "bpmn"
    bpmndir.mkdir(parents=True, exist_ok=True)

    rows = load_edn(seed)
    companies, _addr, _contact, _edges, processes = classify(rows)

    # Which (company, kind) pairs to emit: the explicit :company.process seeds +
    # a procurement template for every company (so the whole graph is covered).
    want = set()
    for p in processes:
        want.add((p[':company.process/company'], p.get(':company.process/kind', ':procurement')))
    for cid in companies:
        want.add((cid, ':procurement'))

    emitted = []
    for cid, kind in sorted(want):
        name, tasks = TEMPLATES.get(kind, TEMPLATES[':procurement'])
        cname = companies.get(cid, {}).get(':company/name', cid)
        slug = cid.replace("org.corp.", "").replace(".", "_")
        proc_id = f"proc_{slug}_{kind.lstrip(':')}"
        xml = build_bpmn(proc_id, name, cname, tasks)
        fname = bpmndir / f"{slug}.{kind.lstrip(':')}.bpmn"
        fname.write_text(xml, encoding="utf-8")
        cid_hash = content_cid(xml)
        emitted.append((f"proc.{cid}.{kind.lstrip(':')}", cid, name, kind, cid_hash))

    # write back the :company.process datoms with computed bpmn-cid
    L = [";; kabuto — BPMN process datoms with computed content CIDs (ADR-2606022000).",
         ";; :synthesized generic templates (G5); bpmn XML under out/bpmn/. NOT actual processes.",
         "["]
    for pid, cid, name, kind, cid_hash in emitted:
        L.append(f' {{:company.process/id {edn_str(pid)} '
                 f':company.process/company {edn_str(cid)} '
                 f':company.process/name {edn_str(name)} '
                 f':company.process/kind {kind} '
                 f':company.process/bpmn-cid {edn_str(cid_hash)} '
                 f':company.process/sourcing :synthesized}}')
    L.append("]")
    (outdir / "processes.kotoba.edn").write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"kabuto.bpmn: wrote {len(emitted)} BPMN files → {bpmndir}")
    print(f"kabuto.bpmn: wrote {outdir/'processes.kotoba.edn'} ({len(emitted)} process datoms)")


if __name__ == "__main__":
    main(sys.argv)
