#!/usr/bin/env python3
"""tsutae-factory-r0 — self-contained factory viewer generator.

Reads the scene + order JSON artifacts and writes a SINGLE self-contained
`tsutae-factory.htm` (no build, no WASM, no network — data inlined) that renders
the cleanroom top-down and animates two modes:

  ?mode=build    — replays construction.order.json (15 steps reveal elements 4D)
  ?mode=produce  — replays production.order.json (a device flows the 12 stations)

HONEST: this is a standalone 2.5-D canvas VISUALISATION of the data model, NOT the
kami-genesis physics WASM sim. The full physics crate (kami-app-tsutae-factory with
run_tsutae_factory_{produce,build}_v1) belongs in the kami-engine submodule
(ADR-2606011500) — see KAMI_APP_SPEC.md. This viewer needs neither the submodule
nor a Rust toolchain; it mirrors the documented self-contained-viz pattern
(watatsuna / shibuya).

Usage:  python3 viz_gen.py [scene_dir]   # writes <scene_dir>/tsutae-factory.htm
"""
import json
import sys
from pathlib import Path


def main():
    here = Path(__file__).resolve().parent
    sdir = Path(sys.argv[1]) if len(sys.argv) > 1 else here

    scene = json.loads((sdir / "factory.scene.json").read_text(encoding="utf-8"))
    constr = json.loads((sdir / "construction.order.json").read_text(encoding="utf-8"))
    prod = json.loads((sdir / "production.order.json").read_text(encoding="utf-8"))

    data = json.dumps({"scene": scene, "construction": constr, "production": prod},
                      ensure_ascii=False, separators=(",", ":"))

    html = _TEMPLATE.replace("/*__DATA__*/null", data)
    out = sdir / "tsutae-factory.htm"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.name} "
          f"({len(scene.get('machines', []))} machines, "
          f"{len(constr.get('steps', []))} build steps, "
          f"{len(prod.get('stations', []))} production stations, "
          f"{len(html)//1024} KB self-contained)")


_TEMPLATE = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>TSUTAE 伝え — handheld cleanroom factory (R0, self-contained viewer)</title>
<style>
  html,body{margin:0;height:100%;background:#0d0f12;color:#e6e8ea;
    font-family:-apple-system,Segoe UI,Roboto,sans-serif;overflow:hidden}
  #gc{width:100vw;height:100vh;display:block;cursor:grab}
  #gc:active{cursor:grabbing}
  #hud{position:fixed;top:12px;left:12px;max-width:50ch;padding:12px 14px;
    background:rgba(20,24,30,.86);border:1px solid #2a2f37;border-radius:12px;
    font-size:13px;line-height:1.5}
  #hud b{color:#ffd23f}.ok{color:#5fd38a}.warn{color:#ff9f43}
  #bar{position:fixed;bottom:12px;left:12px;right:12px;display:flex;gap:8px;
    align-items:center;font-size:12px}
  button{background:#2a2f37;color:#e6e8ea;border:1px solid #3a414c;border-radius:8px;
    padding:6px 12px;cursor:pointer;font-size:12px}
  button.on{background:#ffd23f;color:#161a1f;border-color:#ffd23f}
  #tl{flex:1;height:8px;background:#2a2f37;border-radius:4px;position:relative;overflow:hidden}
  #tlf{position:absolute;left:0;top:0;bottom:0;background:#5fd38a;width:0%}
  #cap{min-width:34ch;color:#b9c0c9}
  kbd{background:#2a2f37;border-radius:5px;padding:1px 6px}
</style>
</head>
<body>
<canvas id="gc"></canvas>
<div id="hud">
  <div><b>TSUTAE 伝え</b> — handheld cleanroom factory R0
    <span class="ok" id="mode">build</span></div>
  <div id="sub">≤200g open-SoC handheld · Class-100k SMT line · ADR-2605261300</div>
  <div id="info" style="margin-top:6px"></div>
  <div style="margin-top:6px;color:#8a929c">drag=pan · wheel=zoom ·
    <kbd>B</kbd> build · <kbd>P</kbd> produce · <kbd>space</kbd> pause</div>
  <div style="margin-top:4px;color:#6b7280;font-size:11px">standalone canvas viewer
    (not the kami-genesis WASM physics sim — see KAMI_APP_SPEC.md)</div>
</div>
<div id="bar">
  <button id="bBuild" class="on">建設 build</button>
  <button id="bProd">生産 produce</button>
  <button id="bPause">⏸</button>
  <div id="tl"><div id="tlf"></div></div>
  <div id="cap"></div>
</div>
<script>
const DATA = /*__DATA__*/null;
const cv = document.getElementById('gc'), cx = cv.getContext('2d');
const scene = DATA.scene, BUILD = DATA.construction.steps, PROD = DATA.production.stations;
let mode = (new URLSearchParams(location.search).get('mode')) || 'build';
let paused = false, t = 0;

// ── world→screen transform (fit scene bbox, with pan/zoom) ──
const bb = scene.site_bbox_m || scene.bbox_m;
let view = {s:1, ox:0, oy:0};
function fit(){
  const w=cv.width=innerWidth, h=cv.height=innerHeight;
  const ww=bb[2]-bb[0], wh=bb[3]-bb[1];
  view.s = Math.min(w/ww, h/wh)*0.86;
  view.ox = w/2 - ((bb[0]+bb[2])/2)*view.s;
  view.oy = h/2 + ((bb[1]+bb[3])/2)*view.s;  // flip y (z-up world → screen down)
}
function X(wx){return view.ox + wx*view.s}
function Y(wy){return view.oy - wy*view.s}
addEventListener('resize', fit); fit();

// ── pan / zoom ──
let drag=null;
cv.addEventListener('mousedown',e=>drag={x:e.clientX,y:e.clientY,ox:view.ox,oy:view.oy});
addEventListener('mouseup',()=>drag=null);
addEventListener('mousemove',e=>{if(drag){view.ox=drag.ox+(e.clientX-drag.x);view.oy=drag.oy+(e.clientY-drag.y);}});
cv.addEventListener('wheel',e=>{e.preventDefault();const k=e.deltaY<0?1.1:0.9;
  const mx=e.clientX,my=e.clientY;
  view.ox=mx-(mx-view.ox)*k; view.oy=my-(my-view.oy)*k; view.s*=k;},{passive:false});

// ── element lookup by id (for build reveal) ──
const REVEAL = {};  // element id → reveal-fraction 0..1
function rect(r,fill,stroke,a){cx.globalAlpha=a??1;cx.fillStyle=fill;
  cx.fillRect(X(r[0]),Y(r[3]),(r[2]-r[0])*view.s,(r[3]-r[1])*view.s);
  if(stroke){cx.strokeStyle=stroke;cx.lineWidth=1;cx.strokeRect(X(r[0]),Y(r[3]),(r[2]-r[0])*view.s,(r[3]-r[1])*view.s);}
  cx.globalAlpha=1;}
function rev(id){return REVEAL[id]??(mode==='produce'?1:0);}

function drawScene(){
  // site
  (scene.site_pavements||[]).forEach(p=>rect(p.rect,'#1a1e25'));
  (scene.site_greens||[]).forEach(p=>rect(p.rect,'#16241a'));
  // floor + zones
  if(rev('floor')>0) rect(scene.bbox_m,'#171b21',null,0.6*rev('floor'));
  (scene.zones||[]).forEach(z=>{const c=z.tint;const col=`rgb(${c.map(v=>Math.round(v*255)).join(',')})`;
    rect(z.rect,col,null,0.30*rev('zone_smt'>=0?1:1)); // zones revealed with floor coat
    cx.fillStyle='#cfd6df';cx.font='11px sans-serif';
    cx.fillText(z.label, X(z.rect[0])+6, Y(z.rect[3])+16);});
  // utilities
  (scene.utilities||[]).forEach(u=>{const a=rev(u.id);if(a<=0)return;
    cx.globalAlpha=0.5*a;cx.strokeStyle=u.kind.includes('elec')?'#ffd23f':u.kind.includes('fire')?'#ff6b6b':u.kind.includes('air')||u.kind.includes('nitro')?'#5fd3d3':'#6ba3ff';
    cx.lineWidth=2;cx.beginPath();u.path.forEach((p,i)=>i?cx.lineTo(X(p[0]),Y(p[1])):cx.moveTo(X(p[0]),Y(p[1])));cx.stroke();cx.globalAlpha=1;});
  // conveyor
  (scene.conveyors||[]).forEach(c=>{const a=rev(c.id);if(a<=0)return;
    cx.globalAlpha=a;cx.strokeStyle='#4a90d9';cx.lineWidth=Math.max(2,c.width*view.s);
    cx.beginPath();c.path.forEach((p,i)=>i?cx.lineTo(X(p[0]),Y(p[1])):cx.moveTo(X(p[0]),Y(p[1])));cx.stroke();cx.globalAlpha=1;});
  // machines
  (scene.machines||[]).forEach(m=>{const a=rev(m.id);if(a<=0)return;
    rect(m.aabb,'#2f3845','#4a5566',a);
    if(view.s>3){cx.globalAlpha=a;cx.fillStyle='#9aa3ad';cx.font='9px sans-serif';
      cx.fillText(m.id,X(m.aabb[0])+2,Y(m.aabb[3])+10);cx.globalAlpha=1;}});
  // walls + columns
  (scene.walls||[]).forEach(w=>{if(rev(w.id)>0)rect(w.aabb,'#3a414c',null,rev(w.id));});
  (scene.columns||[]).forEach(c=>{const a=rev(c.id);if(a<=0)return;
    cx.globalAlpha=a;cx.fillStyle='#525a66';
    cx.fillRect(X(c.x-c.w/2),Y(c.y+c.w/2),c.w*view.s,c.w*view.s);cx.globalAlpha=1;});
  // cells (robots)
  (scene.cells||[]).forEach(c=>{const a=rev(c.id);if(a<=0)return;
    cx.globalAlpha=a;cx.fillStyle='#ffd23f';cx.beginPath();
    cx.arc(X(c.pos[0]),Y(c.pos[1]),Math.max(4,0.7*view.s),0,7);cx.fill();cx.globalAlpha=1;});
  // fixtures (lighting points)
  (scene.fixtures||[]).forEach(f=>{const a=rev(f.id);if(a<=0)return;
    (f.points||[]).forEach(p=>{cx.globalAlpha=0.5*a;cx.fillStyle='#5fd38a';
      cx.fillRect(X(p[0])-1,Y(p[1])-1,2,2);cx.globalAlpha=1;});});
}

// ── BUILD animation: each step reveals its elements over its duration ──
let buildTotal = BUILD.reduce((s,st)=>s+(st.duration||st['duration-d']||5),0);
function tickBuild(dt){
  t += dt*0.6; // days/sec
  let acc=0, curr=null;
  for(const st of BUILD){
    const d = st.duration||st['duration-d']||5;
    const local = Math.max(0, Math.min(1,(t-acc)/d));
    (st.reveals||[]).forEach(id=>REVEAL[id]=Math.max(REVEAL[id]||0,local));
    if(t>=acc && t<acc+d) curr=st;
    acc+=d;
  }
  const pct = Math.min(100, 100*t/buildTotal);
  document.getElementById('tlf').style.width=pct+'%';
  document.getElementById('cap').textContent = curr?`step ${curr.seq}/${BUILD.length}: ${curr.name}`:`build complete (${buildTotal} 工期日)`;
  document.getElementById('info').innerHTML = curr?`<b>建設:</b> ${curr.name}`:`<span class="ok">通電・通水・試運転 完了</span>`;
  if(t>buildTotal+4){t=0;for(const k in REVEAL)delete REVEAL[k];}
}

// ── PRODUCE animation: a device marker flows the stations ──
let prodTotal = PROD.reduce((s,st)=>s+(st.cycle_s||10),0);
let dev = {i:0, p:0};
function tickProduce(dt){
  for(const id in scene) {} // all revealed in produce mode (rev() returns 1)
  const st = PROD[dev.i], next = PROD[(dev.i+1)%PROD.length];
  dev.p += dt*60/(st.cycle_s||10);
  if(dev.p>=1){dev.p=0;dev.i=(dev.i+1)%PROD.length;}
  const a=PROD[dev.i], b=PROD[(dev.i+1)%PROD.length];
  const wx=a.x+(b.x-a.x)*dev.p, wy=a.y+(b.y-a.y)*dev.p;
  drawScene();
  // device marker
  cx.fillStyle='#ff6b6b';cx.beginPath();cx.arc(X(wx),Y(wy),Math.max(5,0.9*view.s),0,7);cx.fill();
  cx.strokeStyle='#fff';cx.lineWidth=1.5;cx.stroke();
  document.getElementById('tlf').style.width=(100*dev.i/PROD.length)+'%';
  document.getElementById('cap').textContent=`station ${a.seq}/${PROD.length}: ${a.name} (${a.cycle_s}s)`;
  document.getElementById('info').innerHTML=`<b>生産:</b> ${a.name}` + (a.cell?` · <span class="ok">${a.cell}</span>`:'');
}

function frame(ts){
  cx.clearRect(0,0,cv.width,cv.height);
  document.getElementById('mode').textContent=mode;
  if(mode==='produce'){ if(!paused) tickProduce(0.016); else drawScene(); }
  else { drawScene(); if(!paused) tickBuild(0.016); }
  requestAnimationFrame(frame);
}
function setMode(m){mode=m;t=0;dev={i:0,p:0};for(const k in REVEAL)delete REVEAL[k];
  document.getElementById('bBuild').classList.toggle('on',m==='build');
  document.getElementById('bProd').classList.toggle('on',m==='produce');}
document.getElementById('bBuild').onclick=()=>setMode('build');
document.getElementById('bProd').onclick=()=>setMode('produce');
document.getElementById('bPause').onclick=()=>paused=!paused;
addEventListener('keydown',e=>{if(e.key==='b')setMode('build');if(e.key==='p')setMode('produce');
  if(e.key===' '){e.preventDefault();paused=!paused;}});
setMode(mode);
requestAnimationFrame(frame);
</script>
</body>
</html>
"""


if __name__ == "__main__":
    main()
