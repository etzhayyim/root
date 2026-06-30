// Organism page hydration (same-origin, no inline). Fetches local JSON
// snapshots (organism/pulse/health/joucho/trajectory/sos) and renders the live
// body into #app. CSP: script-src 'self'; connect-src 'self'. Extracted from
// the former inline <script> in core.cljs organism-page-hiccup. ADR: did-web
// UIUX unification. The shell header/nav/footer live OUTSIDE #app and are not
// touched by this script.
(function(){
const esc=(s)=>String(s??"").replace(/[&<>"']/g,(c)=>({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[c]));
const n=(v)=>new Intl.NumberFormat("en-US").format(Number(v||0));
const app=document.getElementById("app");
Promise.all([
  fetch("./organism.json",{cache:"no-store"}).then((r)=>(r.ok?r.json():null)).catch(()=>null),
  fetch("./pulse.json",{cache:"no-store"}).then((r)=>(r.ok?r.json():null)).catch(()=>null),
  fetch("./health.json",{cache:"no-store"}).then((r)=>(r.ok?r.json():null)).catch(()=>null),
  fetch("./joucho.json",{cache:"no-store"}).then((r)=>(r.ok?r.json():null)).catch(()=>null),
  fetch("./trajectory.json",{cache:"no-store"}).then((r)=>(r.ok?r.json():null)).catch(()=>null),
  fetch("./sos.json",{cache:"no-store"}).then((r)=>(r.ok?r.json():null)).catch(()=>null)
]).then(([org,pulse,health,joucho,traj,sos])=>{
  const summary=org?.summary??{};
  const topPulse=Object.entries(pulse?.actors??{}).sort((a,b)=>(b[1]?.lastAt??0)-(a[1]?.lastAt??0)).slice(0,8).map(([actor,info])=>`<li class="org-tick"><span class="org-tactor">${esc(actor)}</span><span class="org-tsubj">${esc(info?.lastSubject??"")}</span><span class="org-tago">${n(info?.commits??0)} commits</span></li>`).join("");
  const trajCount=Array.isArray(traj?.points)?traj.points.length:(Array.isArray(traj)?traj.length:0);
  const jouchoLine=joucho?.narration??joucho?.text??joucho?.mood??"live mood snapshot";
  app.innerHTML=`<div class="org-hd"><h1>etzhayyim · organism</h1><div class="sub">artificial organism / live body loop</div><div class="org-live${health?.anyStale?" stale":""}"><span class="dot"></span>${health?.anyStale?"stale":"live"}</div></div>
<div class="org-pills"><div class="org-pill a"><b>${n(summary.alive??0)}</b> alive</div><div class="org-pill d"><b>${n(summary.dormant??0)}</b> dormant</div><div class="org-pill s"><b>${n(summary.stub??0)}</b> stub</div><div class="org-pill"><b>${n(summary.cells??0)}</b> cells</div></div>
<div class="org-cols"><div>
<div class="org-card"><h2>Present state</h2><div class="org-muted">last update: ${esc(org?.generatedAt??"unknown")}</div><div class="org-narr"><div class="org-narrtext">${esc(String(jouchoLine))}</div><div class="org-muted">trajectory points: ${n(trajCount)}</div></div><div class="org-legend"><span><i style="background:var(--alive)"></i>alive</span><span><i style="background:var(--dormant)"></i>dormant</span><span><i style="background:var(--stub)"></i>stub</span></div></div>
<div class="org-card"><h2>Live activity</h2><h3>recent actors</h3><ul class="org-ticks">${topPulse||"<li class='org-tick'><span class='org-tsubj'>no pulse data</span></li>"}</ul></div>
</div><div>
<div class="org-card"><h2>What this shows</h2><div class="org-wbline">body summary from <code>organism.json</code></div><ul class="org-ticks"><li class="org-tick"><span class="org-tsubj">heartbeat and mood from <code>pulse.json</code> / <code>joucho.json</code></span></li><li class="org-tick"><span class="org-tsubj">health watchdog: ${esc(health?.anyStale?"stale layer present":"all layers current")}</span></li><li class="org-tick"><span class="org-tsubj">system dynamics path: <a href="/system-dynamics">/system-dynamics</a></span></li><li class="org-tick"><span class="org-tsubj">live loop: <a href="/organism/">this page</a></span></li></ul></div>
<div class="org-card"><h2>System of systems</h2><div class="org-muted">${esc(sos?.title??sos?.name??"system graph")}</div><p class="org-hint">${esc(sos?.note??"The organism is rendered from local JSON snapshots. No external script is required.")}</p></div>
</div></div>`;
}).catch(()=>{
  app.innerHTML='<div class="org-hint">organism の読み込みに失敗しました。<a href="/system-dynamics">/system-dynamics</a> を開いてください。</div>';
});
})();
