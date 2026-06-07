#!/usr/bin/env python3
"""sukashi 透かし — ad-tech supply-chain + fraud-network visualization payload + viewer.

ADR-2606071600. Reads the ad-tech supply-chain graph (the SAME seed analyze.py reads),
builds a force-graph NODE/EDGE payload that VISUALIZES the supply chain + the fraud
clusters, and emits:

  1. viz/ad-supply-chain.json — the viz payload (the data CONTRACT: {nodes, links, meta}).
  2. viz/ad-supply-chain.htm  — a SELF-CONTAINED viewer (payload inlined into the inline
     canvas force-graph template; opens via file://, no external CDN / no external fetch).

A fraud-PROTECTION + ad-tech TRANSPARENCY surface, NEVER a target-list and NEVER an
ad-buying / optimization tool (sukashi G2). Non-adjudicating (G4) — fraud nodes/edges are
flagged observations, not verdicts. Every fraud example is a FICTIONAL illustrative entity.

stdlib only. Usage:
    python3 viz/build_viz_data.py [seed.edn]
"""
from __future__ import annotations
import sys
import os
import json
import pathlib
from collections import defaultdict

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "methods"))
from sukashi_edn import load_edn, classify  # noqa: E402


def _kw(v):
    """':dsp' → 'dsp'; passthrough for non-keyword strings; '' for None."""
    if v is None:
        return ""
    return str(v).lstrip(":")


def build_payload(adtech, auth, creatives, delivery, fraud):
    # ── fraud-flag set: an entity is flagged if it is :synthesized OR is the subject
    #    of any :adfraud.signal (so it renders highlighted red). Signals' subjects can be
    #    an :adtech/id, :adcreative/id, or an :adauth.edge/id — collect them all.
    fraud_subjects = {f.get(":adfraud.signal/subject") for f in fraud}
    fraud_subjects.discard(None)

    # signals indexed by subject for tooltips
    signals_by_subject = defaultdict(list)
    for f in fraud:
        signals_by_subject[f.get(":adfraud.signal/subject")].append({
            "kind": _kw(f.get(":adfraud.signal/kind")),
            "confidence": f.get(":adfraud.signal/confidence"),
            "routed_to": _kw(f.get(":adfraud.signal/routed-to")),
        })

    def is_fraud(eid, rec):
        return (rec.get(":adtech/sourcing") == ":synthesized") or (eid in fraud_subjects)

    # ── NODES: one per ad-tech entity (grouped by role), plus one per creative ──
    nodes = []
    node_ids = set()

    for eid, rec in adtech.items():
        flagged = is_fraud(eid, rec)
        nodes.append({
            "id": eid,
            "label": rec.get(":adtech/name", eid),
            "group": _kw(rec.get(":adtech/role")),
            "kind": "adtech",
            "domain": rec.get(":adtech/domain"),
            "country": rec.get(":adtech/country"),
            "category": _kw(rec.get(":adtech/category")) or None,
            "sourcing": _kw(rec.get(":adtech/sourcing")),
            "fraud": flagged,
            "signals": signals_by_subject.get(eid, []),
        })
        node_ids.add(eid)

    # creative nodes (own group "creative") — flagged if synthesized or signal subject.
    cre_by_id = {}
    for c in creatives:
        cid = c.get(":adcreative/id")
        cre_by_id[cid] = c
        flagged = (c.get(":adcreative/sourcing") == ":synthesized") or (cid in fraud_subjects)
        nodes.append({
            "id": cid,
            "label": c.get(":adcreative/headline", cid),
            "group": "creative",
            "kind": "creative",
            "domain": c.get(":adcreative/landing-domain"),
            "category": _kw(c.get(":adcreative/category")) or None,
            "sourcing": _kw(c.get(":adcreative/sourcing")),
            "fraud": flagged,
            "signals": signals_by_subject.get(cid, []),
        })
        node_ids.add(cid)

    # ── EDGES ──
    links = []

    # 1. authorization edges (ads.txt / sellers.json): publisher → seller.
    #    Flagged `unconfirmed` (warning/dashed-red) when declared && !confirmed.
    unconfirmed = 0
    for e in auth:
        pub = e.get(":adauth.edge/publisher")
        sel = e.get(":adauth.edge/seller")
        if pub not in node_ids or sel not in node_ids:
            continue
        declared = bool(e.get(":adauth.edge/declared"))
        confirmed = bool(e.get(":adauth.edge/confirmed"))
        bad = declared and not confirmed
        if bad:
            unconfirmed += 1
        links.append({
            "source": pub,
            "target": sel,
            "type": "auth",
            "relationship": _kw(e.get(":adauth.edge/relationship")),
            "account_id": e.get(":adauth.edge/account-id"),
            "unconfirmed": bad,
        })

    # 2. delivery edges: creative → its serving advertiser/exchange (served-via),
    #    so a creative connects into the supply chain it rode.
    for c in creatives:
        cid = c.get(":adcreative/id")
        via = c.get(":adcreative/served-via")
        if via and via in node_ids:
            links.append({
                "source": cid,
                "target": via,
                "type": "served-via",
                "relationship": "served-via",
                "unconfirmed": False,
            })
        adv = c.get(":adcreative/advertiser")
        if adv and adv in node_ids:
            links.append({
                "source": adv,
                "target": cid,
                "type": "creative-of",
                "relationship": "creative-of",
                "unconfirmed": False,
            })

    # 3. shared-infra scam cluster: connect creatives that share a serving ASN.
    #    (delivery edges bind a creative → IP/ASN; co-located scam creatives = a candidate
    #    scam-ad network.) We draw a `shared-infra` link between each pair sharing an ASN.
    creatives_by_asn = defaultdict(list)
    for d in delivery:
        cid = d.get(":addelivery.edge/creative")
        asn = d.get(":addelivery.edge/asn")
        if cid in node_ids and asn:
            creatives_by_asn[asn].append((cid, d.get(":addelivery.edge/whois-org")))
    shared_infra = 0
    for asn, members in creatives_by_asn.items():
        cids = [m[0] for m in members]
        for i in range(len(cids)):
            for j in range(i + 1, len(cids)):
                links.append({
                    "source": cids[i],
                    "target": cids[j],
                    "type": "shared-infra",
                    "relationship": "shared-infra",
                    "asn": asn,
                    "whois_org": members[i][1],
                    "unconfirmed": False,
                })
                shared_infra += 1

    fraud_nodes = sum(1 for n in nodes if n["fraud"])
    meta = {
        "actor": "sukashi",
        "glyph": "透かし",
        "adr": "2606071600",
        "note": ("fraud-PROTECTION + ad-tech transparency map; NOT a target-list, "
                 "NOT an ad-buying tool (G2). Non-adjudicating (G4). Fraud examples "
                 "are FICTIONAL illustrative entities."),
        "counts": {
            "nodes": len(nodes),
            "adtech_nodes": len(adtech),
            "creative_nodes": len(creatives),
            "fraud_nodes": fraud_nodes,
            "links": len(links),
            "auth_edges": len(auth),
            "unconfirmed_edges": unconfirmed,
            "shared_infra_links": shared_infra,
            "fraud_signals": len(fraud),
        },
    }
    return {"nodes": nodes, "links": links, "meta": meta}


def main(argv):
    here = pathlib.Path(__file__).resolve().parent
    root = here.parent
    seed = pathlib.Path(argv[1]) if len(argv) > 1 and not argv[1].startswith("--") \
        else root / "data" / "seed-ad-supply-chain.kotoba.edn"

    rows = load_edn(seed)
    adtech, auth, creatives, delivery, fraud = classify(rows)
    payload = build_payload(adtech, auth, creatives, delivery, fraud)

    (here / "ad-supply-chain.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    template = HTML_TEMPLATE
    html = template.replace("__SUKASHI_DATA__", json.dumps(payload, ensure_ascii=False))
    (here / "ad-supply-chain.htm").write_text(html, encoding="utf-8")

    c = payload["meta"]["counts"]
    print(f"sukashi.viz: {c['nodes']} nodes ({c['adtech_nodes']} ad-tech + "
          f"{c['creative_nodes']} creative, {c['fraud_nodes']} fraud-flagged), "
          f"{c['links']} links ({c['unconfirmed_edges']} unconfirmed auth, "
          f"{c['shared_infra_links']} shared-infra) → "
          f"{here/'ad-supply-chain.json'} + {here/'ad-supply-chain.htm'}")


# ── SELF-CONTAINED viewer template (inline canvas force-graph, no external CDN) ──
# Mirrors kabuto/viz/_template.htm structure: inline JSON payload + hand-rolled canvas
# force simulation. __SUKASHI_DATA__ is replaced with the payload JSON by main().
HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>sukashi 透かし — ad-tech supply-chain + fraud-network map</title>
<!--
  sukashi 透かし viewer (ADR-2606071600). A fraud-PROTECTION + ad-tech TRANSPARENCY
  surface, NEVER a target-list and NEVER an ad-buying / optimization tool (G2).
  Non-adjudicating (G4) — fraud nodes/edges are flagged OBSERVATIONS, not verdicts.
  Every fraud example is a CLEARLY-FICTIONAL illustrative entity (RFC-2606 .example/.test
  domains, RFC-5737 documentation IP ranges). SELF-CONTAINED: payload inlined, no external
  fetch / no CDN — opens offline via file://.
-->
<style>
  :root { color-scheme: dark; }
  body { margin:0; background:#0b0e14; color:#cdd6f4; font:13px/1.5 ui-sans-serif,system-ui,sans-serif; }
  header { padding:10px 14px; border-bottom:1px solid #1e2330; }
  h1 { font-size:15px; margin:0 0 2px; }
  .sub { color:#7f8aa3; font-size:11px; }
  .warn { color:#fab387; font-size:11px; margin-top:4px; max-width:1000px; }
  #bar { display:flex; gap:8px; align-items:center; margin-top:6px; flex-wrap:wrap; }
  #q { flex:0 0 280px; background:#11151f; border:1px solid #1e2330; color:#cdd6f4;
       border-radius:6px; padding:4px 8px; font:12px ui-sans-serif,system-ui,sans-serif; }
  #q:focus { outline:none; border-color:#89b4fa; }
  #legend { display:flex; gap:10px; align-items:center; flex-wrap:wrap; font-size:11px; color:#9399b2; }
  #legend .lg { display:inline-flex; align-items:center; gap:4px; }
  #legend .sw { display:inline-block; width:10px; height:10px; border-radius:50%; }
  #legend .ln { display:inline-block; width:18px; height:0; border-top:2px solid #fab387; }
  #legend .ln.dash { border-top:2px dashed #f38ba8; }
  #wrap { display:flex; height:calc(100vh - 140px); }
  canvas { flex:1; display:block; cursor:grab; }
  #side { width:320px; border-left:1px solid #1e2330; padding:12px; overflow:auto; }
  #side h2 { font-size:13px; margin:0 0 6px; }
  .kv { margin:2px 0; } .k { color:#7f8aa3; }
  .pill { display:inline-block; padding:1px 6px; border-radius:8px; background:#1e2330; margin:1px 2px 1px 0; font-size:11px; }
  .pill.fraud { background:#3a1c22; color:#f38ba8; }
  table { width:100%; border-collapse:collapse; font-size:11px; }
  td { padding:2px 4px; border-bottom:1px solid #161b26; }
  #results { margin-top:4px; }
  #results .row { padding:2px 0; cursor:pointer; border-bottom:1px solid #161b26; }
  #results .row:hover { color:#89b4fa; }
  a { color:#89b4fa; }
</style>
</head>
<body>
<header>
  <h1>sukashi 透かし — ad-tech supply-chain + fraud-network map</h1>
  <div class="sub">aggregate-first · fraud-protection + transparency · sourcing <span class="pill">:representative</span> · ADR-2606071600</div>
  <div class="warn">Fraud-PROTECTION + transparency map — NOT a target-list, NOT an ad-buying tool (sukashi G2). Non-adjudicating (G4). Fraud examples are FICTIONAL illustrative entities.</div>
  <div id="bar">
    <input id="q" type="search" placeholder="search entity / role / domain / country …" autocomplete="off"/>
    <span id="legend"></span>
  </div>
</header>
<div id="wrap">
  <canvas id="cv"></canvas>
  <div id="side">
    <h2>Fraud-flagged entities</h2>
    <table id="fraudtab"></table>
    <h2 style="margin-top:14px">Selected</h2>
    <div id="sel" class="sub">click a node</div>
  </div>
</div>
<script id="data" type="application/json">__SUKASHI_DATA__</script>
<script>
const DATA = JSON.parse(document.getElementById('data').textContent);
const cv = document.getElementById('cv'), ctx = cv.getContext('2d');

// role → color (grouped by :adtech/role + creative). Fraud overrides to red at draw time.
const ROLE_COLORS = {
  advertiser:'#f9e2af', dsp:'#89b4fa', 'ad-exchange':'#94e2d5', ssp:'#74c7ec',
  'ad-network':'#cba6f7', publisher:'#a6e3a1', verification:'#b4befe', creative:'#f5c2e7'
};
const FRAUD_COLOR = '#f38ba8';
function color(g){ return ROLE_COLORS[(g||'').replace(/^:/,'')] || '#9399b2'; }

// ─── legend ──────────────────────────────────────────────────────────────────
(function legend(){
  const el = document.getElementById('legend'); const parts = [];
  for (const [g,c] of Object.entries(ROLE_COLORS))
    parts.push('<span class="lg"><span class="sw" style="background:'+c+'"></span>'+g+'</span>');
  parts.push('<span class="lg"><span class="sw" style="background:'+FRAUD_COLOR+'"></span>red = fraud-flagged</span>');
  parts.push('<span class="lg"><span class="ln dash"></span>dashed = unconfirmed / unauthorized edge</span>');
  el.innerHTML = parts.join('');
})();

// ─── scene ───────────────────────────────────────────────────────────────────
let nodes=[], links=[], idx=new Map(), SEL=null, MATCH=null;

function buildScene(view){
  nodes = view.nodes.map((n,i)=>({ ...n,
    x: Math.cos(i)*320 + (innerWidth*0.5-160), y: Math.sin(i*1.7)*260 + innerHeight*0.40,
    vx:0, vy:0, deg:0 }));
  idx = new Map(nodes.map(n=>[n.id,n]));
  links = view.links.map(e=>({
      s:idx.get(e.source), t:idx.get(e.target),
      type:e.type, rel:e.relationship, unconfirmed:!!e.unconfirmed, asn:e.asn
    })).filter(l=>l.s&&l.t);
  for(const l of links){ l.s.deg++; l.t.deg++; }

  const ft = document.getElementById('fraudtab'); ft.innerHTML='';
  view.nodes.filter(n=>n.fraud).forEach(n=>{
    const tr=document.createElement('tr');
    tr.style.cursor='pointer';
    tr.innerHTML='<td><span style="color:'+FRAUD_COLOR+'">●</span> '+
      (n.label.length>30?n.label.slice(0,28)+'…':n.label)+'</td>'+
      '<td style="text-align:right" class="k">'+(n.group||'')+'</td>';
    tr.onclick=()=>{ const nn=idx.get(n.id); if(nn) showSelected(nn); };
    ft.appendChild(tr);
  });
}

function resize(){ cv.width = cv.clientWidth; cv.height = cv.clientHeight; }
window.addEventListener('resize', resize); resize();

function step(){
  for(let i=0;i<nodes.length;i++){ for(let j=i+1;j<nodes.length;j++){
    const a=nodes[i],b=nodes[j]; let dx=a.x-b.x,dy=a.y-b.y; let d2=dx*dx+dy*dy+0.01;
    const f=1100/d2; const d=Math.sqrt(d2); dx/=d;dy/=d; a.vx+=dx*f;a.vy+=dy*f;b.vx-=dx*f;b.vy-=dy*f;
  }}
  for(const l of links){ let dx=l.t.x-l.s.x,dy=l.t.y-l.s.y; const d=Math.sqrt(dx*dx+dy*dy)+0.01;
    const rest = l.type==='shared-infra' ? 70 : 130;
    const f=(d-rest)*0.012; dx/=d;dy/=d; l.s.vx+=dx*f;l.s.vy+=dy*f;l.t.vx-=dx*f;l.t.vy-=dy*f; }
  for(const n of nodes){ n.vx+=(cv.width/2-n.x)*0.0008; n.vy+=(cv.height/2-n.y)*0.0008;
    n.x+=n.vx*=0.85; n.y+=n.vy*=0.85; }
}

function draw(){
  ctx.clearRect(0,0,cv.width,cv.height);
  for(const l of links){
    let stroke, w;
    if(l.unconfirmed){ stroke='rgba(243,139,168,0.85)'; w=1.6; }       // dashed red warning
    else if(l.type==='shared-infra'){ stroke='rgba(243,139,168,0.40)'; w=1.4; }
    else if(l.type==='served-via'){ stroke='rgba(245,194,231,0.30)'; w=1.0; }
    else if(l.type==='creative-of'){ stroke='rgba(148,226,213,0.28)'; w=0.9; }
    else { stroke='rgba(120,130,160,0.30)'; w=1.0; }                   // confirmed auth
    ctx.strokeStyle=stroke; ctx.lineWidth=w;
    ctx.setLineDash(l.unconfirmed ? [5,4] : []);
    ctx.beginPath(); ctx.moveTo(l.s.x,l.s.y); ctx.lineTo(l.t.x,l.t.y); ctx.stroke();
  }
  ctx.setLineDash([]);
  for(const n of nodes){ const r=4+Math.sqrt(n.deg)*2.0; const hit = MATCH && MATCH.has(n.id);
    ctx.fillStyle = n.fraud ? FRAUD_COLOR : color(n.group);
    ctx.globalAlpha = (MATCH ? (hit?1:0.12) : (SEL && SEL!==n ? 0.5 : 1));
    ctx.beginPath(); ctx.arc(n.x,n.y,r,0,7); ctx.fill();
    if(n.fraud){ ctx.strokeStyle=FRAUD_COLOR; ctx.lineWidth=1.4;
      ctx.beginPath(); ctx.arc(n.x,n.y,r+2.5,0,7); ctx.stroke(); }
    if(hit){ ctx.strokeStyle='#f9e2af'; ctx.lineWidth=1.5; ctx.beginPath(); ctx.arc(n.x,n.y,r+4,0,7); ctx.stroke(); }
    if(n.deg>=3||n===SEL||hit||n.fraud){ ctx.globalAlpha=1; ctx.fillStyle='#cdd6f4'; ctx.font='10px sans-serif';
      const t=(n.label||n.id); ctx.fillText(t.length>26?t.slice(0,24)+'…':t, n.x+r+2, n.y+3); }
    ctx.globalAlpha=1; }
}
function loop(){ step(); draw(); requestAnimationFrame(loop); }

function showSelected(best){
  SEL=best;
  let sig='';
  if(best.signals && best.signals.length){
    sig = '<div class="kv"><span class="k">fraud signals</span></div>' +
      best.signals.map(s=>'<div class="kv"><span class="pill fraud">'+s.kind+'</span> '+
        'conf '+(s.confidence!=null?s.confidence:'—')+' → '+(s.routed_to||'—')+'</div>').join('');
  }
  document.getElementById('sel').innerHTML =
    '<div class="kv"><b>'+best.label+'</b>'+(best.fraud?' <span class="pill fraud">fraud-flagged</span>':'')+'</div>'+
    '<div class="kv"><span class="k">id</span> '+best.id+'</div>'+
    '<div class="kv"><span class="k">role</span> <span class="pill">'+(best.group||'')+'</span></div>'+
    (best.domain?'<div class="kv"><span class="k">domain</span> '+best.domain+'</div>':'')+
    (best.country?'<div class="kv"><span class="k">country</span> '+best.country+'</div>':'')+
    (best.category?'<div class="kv"><span class="k">category</span> <span class="pill">'+best.category+'</span></div>':'')+
    '<div class="kv"><span class="k">sourcing</span> '+(best.sourcing||'—')+'</div>'+
    '<div class="kv"><span class="k">degree</span> '+best.deg+'</div>'+
    sig;
}
cv.addEventListener('click', ev=>{
  const r=cv.getBoundingClientRect(), mx=ev.clientX-r.left, my=ev.clientY-r.top;
  let best=null,bd=1e9; for(const n of nodes){ const d=(n.x-mx)**2+(n.y-my)**2; if(d<bd){bd=d;best=n;} }
  if(bd>500) return; showSelected(best);
});

// ─── search ──────────────────────────────────────────────────────────────────
const qbox = document.getElementById('q');
qbox.addEventListener('input', ()=>{
  const ql = qbox.value.trim().toLowerCase();
  if(!ql){ MATCH=null; document.getElementById('sel').innerHTML='click a node'; return; }
  const hits = nodes.filter(n=>[n.label,n.group,n.domain,n.country,n.id,n.category]
    .some(f=>(f||'').toLowerCase().includes(ql)));
  MATCH = new Set(hits.map(n=>n.id));
  const side = document.getElementById('sel');
  side.innerHTML = '<div class="kv k">'+hits.length+' match(es)</div><div id="results"></div>';
  const res = side.querySelector('#results');
  hits.slice(0,40).forEach(n=>{ const d=document.createElement('div'); d.className='row';
    d.innerHTML='<span style="color:'+(n.fraud?FRAUD_COLOR:color(n.group))+'">●</span> '+n.label+
      ' <span class="k">'+(n.group||'')+'</span>';
    d.onclick=()=>showSelected(n); res.appendChild(d); });
});

// ─── boot ────────────────────────────────────────────────────────────────────
buildScene(DATA);
loop();
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main(sys.argv)
