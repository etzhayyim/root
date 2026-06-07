/**
 * Chat HTML served at `/`. Token placeholder `__MURAKUMO_CHAT_TOKEN__` is
 * substituted by the Worker with an ephemeral HMAC chat-anon token (1h TTL)
 * bound to MURAKUMO_CHAT_SECRET.
 *
 * Model list mirrors judah LiteLLM model_list (ansible roles/litellm/defaults).
 */

// LiteLLM router model aliases (see /v1/model/info). Default = gemma3:1b (fastest).
const FLEET_MODELS: { id: string; label: string }[] = [
  { id: "gemma3-1b",  label: "gemma3:1b (default, 815MB Q4)" },
  { id: "gemma4-e4b", label: "gemma4:e4b (8B Q4)" },
  { id: "qwen3.5-9b", label: "qwen3.5:9b (9B Q4)" },
];
const DEFAULT_MODEL = "gemma3-1b";
const MODEL_OPTIONS = FLEET_MODELS
  .map((m) => `<option value="${m.id}"${m.id === DEFAULT_MODEL ? " selected" : ""}>${m.label}</option>`)
  .join("\n");

export const CHAT_HTML = `<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover"/>
<title>Murakumo Chat</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
html,body{height:100%;background:#0a0a0a;color:#f5f5f5;font-family:system-ui,-apple-system,sans-serif}
.app{display:flex;flex-direction:column;height:100dvh;max-width:600px;margin:0 auto}
.hdr{display:flex;align-items:center;justify-content:space-between;padding:8px 16px;border-bottom:1px solid #2a2a2a;gap:8px}
.hdr .logo{display:flex;align-items:center;gap:8px;flex-shrink:0}
.hdr .logo .icon{width:28px;height:28px;border-radius:8px;background:#06b6d4;display:flex;align-items:center;justify-content:center;font-weight:900;font-size:11px;color:#fff}
.hdr .title{font-size:14px;font-weight:700}
.hdr select{background:#1a1a1a;color:#fff;border:1px solid #2a2a2a;border-radius:8px;padding:4px 8px;font-size:12px}
.hdr-right{display:flex;align-items:center;gap:8px}
.gpu-toggle{display:flex;align-items:center;gap:6px;cursor:pointer;user-select:none}
.gpu-toggle .label{font-size:11px;color:#888}
.gpu-toggle .sw{position:relative;width:36px;height:20px;background:#333;border-radius:10px;transition:background .2s}
.gpu-toggle .sw::after{content:'';position:absolute;top:2px;left:2px;width:16px;height:16px;background:#666;border-radius:50%;transition:transform .2s,background .2s}
.gpu-toggle.on .sw{background:#06b6d4}
.gpu-toggle.on .sw::after{transform:translateX(16px);background:#fff}
.gpu-status{font-size:10px;color:#555;white-space:nowrap}
.gpu-status.connected{color:#06b6d4}
.gpu-status.working{color:#f59e0b}
.gpu-status.err{color:#ef4444}
.msgs{flex:1;overflow-y:auto;padding:12px 16px;display:flex;flex-direction:column;gap:10px}
.msg{max-width:85%;padding:10px 14px;border-radius:16px;font-size:14px;line-height:1.5;white-space:pre-wrap;word-break:break-word}
.msg.user{align-self:flex-end;background:#06b6d4;color:#fff}
.msg.assistant{align-self:flex-start;background:#1a1a1a;border:1px solid #2a2a2a}
.msg .cursor{display:inline-block;width:6px;height:16px;background:#06b6d4;animation:blink 1s infinite}
@keyframes blink{50%{opacity:0}}
.empty{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-align:center;padding:20px}
.empty h2{font-size:18px;font-weight:700}
.empty p{font-size:13px;color:#666}
.suggestions{display:flex;flex-wrap:wrap;justify-content:center;gap:6px;margin-top:8px}
.suggestions button{background:#1a1a1a;border:1px solid #2a2a2a;color:#a0a0a0;padding:6px 12px;border-radius:999px;font-size:12px;cursor:pointer}
.suggestions button:active{background:#222}
.input-row{display:flex;gap:8px;padding:12px 16px;border-top:1px solid #2a2a2a}
.input-row textarea{flex:1;resize:none;background:#1a1a1a;color:#fff;border:1px solid #2a2a2a;border-radius:12px;padding:10px 12px;font-size:14px;font-family:inherit;outline:none}
.input-row textarea:focus{border-color:rgba(6,182,212,0.5)}
.input-row button{width:40px;height:40px;border-radius:12px;background:#06b6d4;color:#fff;border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;flex-shrink:0}
.input-row button:disabled{opacity:0.3}
.dots{display:flex;gap:4px;padding:10px 14px;align-self:flex-start}
.dots span{width:8px;height:8px;border-radius:50%;background:#06b6d4;animation:bounce 1.4s infinite}
.dots span:nth-child(2){animation-delay:.15s}
.dots span:nth-child(3){animation-delay:.3s}
@keyframes bounce{0%,80%,100%{transform:translateY(0)}40%{transform:translateY(-6px)}}
.gpu-bar{padding:6px 16px;border-top:1px solid #2a2a2a;font-size:11px;color:#666;display:none;align-items:center;gap:8px}
.gpu-bar.visible{display:flex}
.gpu-bar .stat{color:#06b6d4;font-weight:600}
/* reasoning_content (qwen3 <think>) rendered inline, muted + italic so the
   final answer stands out. Collapsible on tap. */
.think{display:block;margin-bottom:8px;padding:6px 10px;border-left:2px solid #6b7280;background:rgba(107,114,128,0.08);border-radius:4px;font-size:12px;color:#9ca3af;font-style:italic;white-space:pre-wrap;max-height:140px;overflow-y:auto;cursor:pointer;line-height:1.4}
.think.collapsed{max-height:20px;overflow:hidden}
.think::before{content:"◇ think ";color:#a855f7;font-style:normal;font-weight:700;font-size:10px;letter-spacing:0.3px}
.fleet-pill{display:flex;align-items:center;gap:6px;padding:4px 10px;border:1px solid #2a2a2a;border-radius:999px;background:#111;cursor:pointer;font-size:11px;color:#a0a0a0;user-select:none;transition:border-color .15s}
.fleet-pill:hover{border-color:#3a3a3a}
.fleet-pill .dot{width:8px;height:8px;border-radius:50%;background:#555;flex-shrink:0;transition:background .3s}
.fleet-pill .dot.ok{background:#10b981;box-shadow:0 0 6px rgba(16,185,129,0.6)}
.fleet-pill .dot.warn{background:#f59e0b;box-shadow:0 0 6px rgba(245,158,11,0.6)}
.fleet-pill .dot.err{background:#ef4444;box-shadow:0 0 6px rgba(239,68,68,0.6)}
.fleet-pill .dot.stale{background:#6b7280;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{opacity:1}50%{opacity:0.4}}
.fleet-pill .summary{font-weight:600;color:#e5e5e5}
.fleet-overlay{position:fixed;inset:0;background:rgba(0,0,0,0.65);backdrop-filter:blur(4px);display:none;align-items:flex-start;justify-content:center;padding:40px 16px 16px;z-index:100;overflow-y:auto}
.fleet-overlay.visible{display:flex}
.fleet-panel{width:100%;max-width:560px;background:#0f0f0f;border:1px solid #2a2a2a;border-radius:16px;padding:16px;color:#e5e5e5}
.fleet-panel .ph{display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;padding-bottom:10px;border-bottom:1px solid #2a2a2a}
.fleet-panel .ph h3{font-size:15px;font-weight:700}
.fleet-panel .close{background:transparent;border:none;color:#888;font-size:18px;cursor:pointer;width:28px;height:28px;border-radius:6px}
.fleet-panel .close:hover{background:#1a1a1a;color:#fff}
.tier-card{background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;padding:10px 12px;margin-bottom:10px}
.tier-card .th{display:flex;align-items:center;justify-content:space-between;margin-bottom:6px}
.tier-card .tn{font-size:12px;font-weight:700;color:#06b6d4;letter-spacing:0.3px}
.tier-card .ts{font-size:11px;padding:2px 8px;border-radius:999px;font-weight:600}
.tier-card .ts.ok{background:rgba(16,185,129,0.15);color:#10b981}
.tier-card .ts.warn{background:rgba(245,158,11,0.15);color:#f59e0b}
.tier-card .ts.err{background:rgba(239,68,68,0.15);color:#ef4444}
.tier-card .tm{display:grid;grid-template-columns:repeat(2,1fr);gap:6px 12px;font-size:11px;color:#888}
.tier-card .tm .k{color:#6b7280}
.tier-card .tm .v{color:#e5e5e5;font-variant-numeric:tabular-nums;font-weight:500}
.node-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(90px,1fr));gap:6px;margin-top:8px}
.node-chip{padding:6px 8px;border-radius:8px;background:#0a0a0a;border:1px solid #2a2a2a;font-size:10px;text-align:center;color:#a0a0a0}
.node-chip.ok{border-color:rgba(16,185,129,0.4);color:#10b981}
.node-chip.err{border-color:rgba(239,68,68,0.4);color:#ef4444;background:rgba(239,68,68,0.05)}
.node-chip .nn{font-weight:700;font-size:11px;letter-spacing:0.2px}
.health-bar{height:6px;border-radius:3px;background:#2a2a2a;overflow:hidden;margin-top:4px}
.health-bar .fill{height:100%;background:linear-gradient(90deg,#ef4444,#f59e0b 50%,#10b981);transition:width .4s ease}
.fleet-meta{margin-top:10px;font-size:10px;color:#555;text-align:center;font-variant-numeric:tabular-nums}
</style>
</head>
<body>
<div class="app">
<div class="hdr">
<div class="logo"><div class="icon">M</div><span class="title">Murakumo</span></div>
<div class="hdr-right">
<div class="fleet-pill" id="fleetPill" onclick="toggleFleetPanel()" title="Fleet status">
<span class="dot stale" id="fleetDot"></span>
<span class="summary" id="fleetSummary">…</span>
</div>
<select id="model">
${MODEL_OPTIONS}
</select>
</div>
</div>
<div class="fleet-overlay" id="fleetOverlay" onclick="if(event.target===this)toggleFleetPanel()">
<div class="fleet-panel">
<div class="ph">
<h3>Fleet Status</h3>
<button class="close" onclick="toggleFleetPanel()" aria-label="Close">×</button>
</div>
<div id="fleetBody">Loading…</div>
<div class="fleet-meta" id="fleetMeta"></div>
</div>
</div>
<div class="msgs" id="msgs">
<div class="empty" id="empty">
<div style="width:48px;height:48px;border-radius:16px;background:rgba(6,182,212,0.15);display:flex;align-items:center;justify-content:center"><span style="font-size:22px;font-weight:900;color:#06b6d4">M</span></div>
<h2>Murakumo LLM</h2>
<p>Distributed native MLX inference: Mac Mini M4 fleet</p>
<div class="suggestions">
<button onclick="ask('What is WebGPU?')">What is WebGPU?</button>
<button onclick="ask('Explain Rust in one sentence')">Explain Rust</button>
<button onclick="ask('Write a haiku about AI')">Haiku about AI</button>
</div>
</div>
</div>
<div class="gpu-bar" id="gpuBar">
GPU: <span class="stat" id="gpuTier">--</span> |
Tasks: <span class="stat" id="gpuTasks">0</span> |
GPU time: <span class="stat" id="gpuTime">0ms</span>
</div>
<div class="input-row">
<textarea id="input" rows="1" placeholder="Message Murakumo..." onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();send()}"></textarea>
<button onclick="send()" id="btn" aria-label="Send">
<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M22 2L11 13M22 2l-7 20-4-9-9-4 20-7z"/></svg>
</button>
</div>
</div>
<script>
// ---- Chat API ----
var API="/v1/chat/completions";
var TOKEN="__MURAKUMO_CHAT_TOKEN__";
var chatMsgs=[],loading=false;
function $(id){return document.getElementById(id)}
function ask(t){$("input").value=t;send()}
function addMsg(role,content){
var d=document.createElement("div");d.className="msg "+role;d.textContent=content;
$("msgs").appendChild(d);$("msgs").scrollTop=$("msgs").scrollHeight;return d;
}
async function send(){
var t=$("input").value.trim();if(!t||loading)return;
$("input").value="";loading=true;$("btn").disabled=true;
var e=$("empty");if(e)e.remove();
chatMsgs.push({role:"user",content:t});addMsg("user",t);
var dots=document.createElement("div");dots.className="dots";
dots.innerHTML="<span></span><span></span><span></span>";$("msgs").appendChild(dots);
$("msgs").scrollTop=$("msgs").scrollHeight;
try{
var r=await fetch(API,{method:"POST",
headers:{"Content-Type":"application/json","Authorization":"Bearer "+TOKEN},
body:JSON.stringify({model:$("model").value,messages:chatMsgs,max_tokens:512,temperature:0.7,stream:true})});
dots.remove();
if(!r.ok){var err=await r.json().catch(function(){return{}});addMsg("assistant","Error: "+(err.error?.message||err.message||r.statusText));return}
var reader=r.body.getReader(),dec=new TextDecoder();
var buf="",full="",think="",el=addMsg("assistant","");
function esc(s){return String(s).replace(/[&<>]/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;"}[c]})}
function render(){
var h="";
if(think)h+='<div class="think" onclick="this.classList.toggle(\\'collapsed\\')">'+esc(think)+'</div>';
h+=esc(full)+'<span class="cursor"></span>';
el.innerHTML=h;
$("msgs").scrollTop=$("msgs").scrollHeight;
}
while(true){var chunk=await reader.read();if(chunk.done)break;
buf+=dec.decode(chunk.value,{stream:true});var lines=buf.split("\\n");buf=lines.pop()||"";
for(var i=0;i<lines.length;i++){var s=lines[i].trim();
// Skip keepalive SSE comments (proxy heartbeat) — they start with ':'.
if(!s||s.startsWith(":"))continue;
if(!s.startsWith("data: "))continue;
var p=s.slice(6);if(p==="[DONE]")continue;
try{var j=JSON.parse(p),d=j.choices&&j.choices[0]&&j.choices[0].delta?j.choices[0].delta:{};
// qwen3 etc surface reasoning as delta.reasoning_content (separate from content).
// Preserve it so the think trace is visible (keep think intact per user request).
if(typeof d.reasoning_content==="string")think+=d.reasoning_content;
if(typeof d.content==="string")full+=d.content;
render();
}catch (_err) { void _err; }}}
// Finalize: strip cursor, keep think panel.
var finalH="";
if(think)finalH+='<div class="think collapsed" onclick="this.classList.toggle(\\'collapsed\\')">'+esc(think)+'</div>';
finalH+=esc(full||"(empty)");
el.innerHTML=finalH;
chatMsgs.push({role:"assistant",content:full});
}catch(e2){dots.remove();addMsg("assistant","Network error: "+e2.message)}
finally{loading=false;$("btn").disabled=false;$("msgs").scrollTop=$("msgs").scrollHeight}
}

// ---- Browser GPU Contribute ----
var gpuEnabled=false,ws=null,engine=null,heartbeatTimer=null;
var sessionId=null,gpuTier="g0",tasksDone=0,totalGpuMs=0;

function setGpuStatus(text,cls){
var el=$("gpuStatus");el.textContent=text;el.className="gpu-status"+(cls?" "+cls:"");
}
function updateGpuBar(){
$("gpuTier").textContent=gpuTier;
$("gpuTasks").textContent=tasksDone;
$("gpuTime").textContent=totalGpuMs<1000?totalGpuMs+"ms":(totalGpuMs/1000).toFixed(1)+"s";
}

async function toggleGPU(){
gpuEnabled=!gpuEnabled;
$("gpuToggle").classList.toggle("on",gpuEnabled);
$("gpuBar").classList.toggle("visible",gpuEnabled);
if(gpuEnabled){await startGPU()}else{stopGPU()}
}

async function startGPU(){
setGpuStatus("loading WASM...","");
try{
if(!navigator.gpu){setGpuStatus("WebGPU not supported","err");gpuEnabled=false;$("gpuToggle").classList.remove("on");return}
var adapter=await navigator.gpu.requestAdapter();
if(!adapter){setGpuStatus("no GPU adapter","err");gpuEnabled=false;$("gpuToggle").classList.remove("on");return}

// Load kotodama-inference WASM
var wasmBytes=await fetch("/gpu/inference.wasm").then(function(r){return r.arrayBuffer()});
var mod=await import("/gpu/inference.js");
await mod.default(wasmBytes);
engine=await mod.BrowserInferenceWorker.create();
var capJson=engine.probeCapabilities();
var cap=JSON.parse(capJson);
gpuTier=cap.gpuTier||"g1";
setGpuStatus("connecting...","");

// Connect WebSocket
var proto=location.protocol==="https:"?"wss:":"ws:";
ws=new WebSocket(proto+"//"+location.host+"/ws");
ws.onopen=function(){
var regEnv=engine.buildRegisterEnvelope();
ws.send(regEnv);
setGpuStatus("registering...","");
};
ws.onmessage=function(ev){
try{var env=JSON.parse(ev.data);handleWsMsg(env)}catch(e){console.warn("ws parse",e)}
};
ws.onerror=function(){setGpuStatus("ws error","err")};
ws.onclose=function(){
setGpuStatus("disconnected","");
clearInterval(heartbeatTimer);heartbeatTimer=null;
if(gpuEnabled)setTimeout(function(){if(gpuEnabled)startGPU()},3000);
};
}catch(e){
console.error("GPU init failed:",e);
setGpuStatus(e.message||"init failed","err");
gpuEnabled=false;$("gpuToggle").classList.remove("on");
}
}

function stopGPU(){
clearInterval(heartbeatTimer);heartbeatTimer=null;
if(ws){try{ws.send(JSON.stringify({type:"bye"}));ws.close()}catch (_err) { void _err; }ws=null}
engine=null;sessionId=null;
setGpuStatus("","");
$("gpuBar").classList.remove("visible");
}

function handleWsMsg(env){
switch(env.type){
case "registered":
sessionId=env.registered.sessionId;
gpuTier=env.registered.gpuTier||gpuTier;
var hbSec=env.registered.heartbeatIntervalSec||15;
setGpuStatus("idle ("+gpuTier+")","connected");
updateGpuBar();
// Background: load model weights from R2 (non-blocking)
if(engine&&!engine.hasModel()){
setGpuStatus("loading model...","connected");
fetch("/gpu/models/hayate-v5/model.safetensors").then(function(wr){
if(!wr.ok){console.warn("model fetch:",wr.status);setGpuStatus("idle ("+gpuTier+")","connected");return}
return wr.arrayBuffer();
}).then(function(ab){
if(!ab)return;
var info=engine.loadWeights(new Uint8Array(ab));
console.log("model loaded:",info);
setGpuStatus("model ready ("+gpuTier+")","connected");
}).catch(function(we){console.warn("weight load:",we);setGpuStatus("idle ("+gpuTier+")","connected")});
}
clearInterval(heartbeatTimer);
heartbeatTimer=setInterval(sendHeartbeat,hbSec*1000);
break;
case "heartbeatAck":break;
case "taskPush":
if(env.taskPush)executeTask(env.taskPush);
break;
case "taskCancel":
setGpuStatus("idle ("+gpuTier+")","connected");
break;
case "error":
console.warn("server error:",env.error);
setGpuStatus("error: "+(env.error?env.error.message:"unknown"),"err");
break;
}
}

function sendHeartbeat(){
if(!ws||ws.readyState!==1)return;
var hpct=0;
if(performance.memory)hpct=Math.round(performance.memory.usedJSHeapSize/performance.memory.jsHeapSizeLimit*100);
ws.send(JSON.stringify({
type:"heartbeat",
heartbeat:{sessionId:sessionId,visibility:document.visibilityState,heapPct:hpct,shardMemoryMb:0,warmShards:[]}
}));
}

// ---- Fleet Status (LiteLLM proxy → 10 Mac Mini Ollama backends) ----
var fleetPollTimer=null,fleetPanelOpen=false,fleetLastMeta=null;
function toggleFleetPanel(){
fleetPanelOpen=!fleetPanelOpen;
$("fleetOverlay").classList.toggle("visible",fleetPanelOpen);
if(fleetPanelOpen)renderFleetPanel(fleetLastMeta);
}
function healthClass(pct){return pct>=80?"ok":pct>=40?"warn":"err"}
function fmtAgo(ms){
if(ms<0||!isFinite(ms))return "—";
if(ms<60000)return Math.floor(ms/1000)+"s ago";
if(ms<3600000)return Math.floor(ms/60000)+"m ago";
return Math.floor(ms/3600000)+"h ago";
}
function esc(s){return String(s).replace(/[&<>"']/g,function(c){return {"&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;"}[c]})}
function renderFleetPill(meta){
var dot=$("fleetDot"),sum=$("fleetSummary");
if(!meta||!meta.fleet){dot.className="dot stale";sum.textContent="offline";return}
var f=meta.fleet,pct=f.healthPct||0;
dot.className="dot "+healthClass(pct);
var lite=f.litellm||{};
var liteTxt=lite.reachable?"litellm ok":"litellm down";
sum.textContent=(f.nodesHealthy||0)+"/"+(f.nodesTotal||0)+" · "+liteTxt;
}
function renderFleetPanel(meta){
var body=$("fleetBody"),metaEl=$("fleetMeta");
if(!meta||!meta.fleet){body.innerHTML='<div style="padding:20px;text-align:center;color:#666">No fleet data available</div>';metaEl.textContent="";return}
var f=meta.fleet,lite=f.litellm||{},nodes=f.nodes||[];
var liteStatus=lite.reachable?"ok":"err";
var liteLabel=lite.reachable?"reachable":"down";
var pct=f.healthPct||0;
var fleetStatus=healthClass(pct);
var fleetLabel=pct>=80?"healthy":pct>=40?"degraded":pct>0?"critical":"down";
var html="";
html+='<div class="tier-card">';
html+='<div class="th"><span class="tn">LITELLM ROUTER</span><span class="ts '+liteStatus+'">'+liteLabel+'</span></div>';
html+='<div class="tm">';
html+='<span class="k">Endpoint</span><span class="v">judah:4000</span>';
html+='<span class="k">Latency</span><span class="v">'+(lite.latencyMs!=null?lite.latencyMs+"ms":"—")+'</span>';
if(lite.error){html+='<span class="k">Error</span><span class="v" style="color:#ef4444;font-size:10px">'+esc(String(lite.error).slice(0,80))+'</span>'}
html+='</div></div>';
html+='<div class="tier-card">';
html+='<div class="th"><span class="tn">OLLAMA FLEET · 10 MAC MINI M4</span><span class="ts '+fleetStatus+'">'+fleetLabel+'</span></div>';
html+='<div class="health-bar"><div class="fill" style="width:'+pct+'%"></div></div>';
html+='<div class="tm" style="margin-top:8px">';
html+='<span class="k">Healthy</span><span class="v">'+(f.nodesHealthy||0)+'/'+(f.nodesTotal||0)+' ('+pct+'%)</span>';
html+='<span class="k">Routing</span><span class="v">simple-shuffle</span>';
html+='</div>';
var chips="";
for(var i=0;i<nodes.length;i++){
var n=nodes[i],cls=n.healthy?"ok":"err",label=n.healthy?(n.model?esc(String(n.model).slice(0,10)):"ok"):"down";
chips+='<div class="node-chip '+cls+'" title="'+esc(n.ip||"")+(n.error?" — "+esc(String(n.error).slice(0,60)):"")+'"><div class="nn">'+esc(n.name)+'</div>'+label+'</div>';
}
if(chips)html+='<div class="node-grid">'+chips+'</div>';
html+='</div>';
body.innerHTML=html;
var staleSec=f.staleMs!=null?Math.floor(f.staleMs/1000):null;
metaEl.textContent="last probe "+(f.lastCheck?fmtAgo(Date.now()-new Date(f.lastCheck).getTime()):"—")+(staleSec!=null?" · "+staleSec+"s stale":"")+" · cron every 5m";
}
async function fetchFleet(){
try{
var r=await fetch("/_app/meta",{cache:"no-store"});
if(!r.ok)throw new Error("http "+r.status);
var meta=await r.json();
fleetLastMeta=meta;
renderFleetPill(meta);
if(fleetPanelOpen)renderFleetPanel(meta);
}catch(e){
var dot=$("fleetDot"),sum=$("fleetSummary");
dot.className="dot stale";sum.textContent="offline";
}
}
fetchFleet();
fleetPollTimer=setInterval(fetchFleet,10000);
document.addEventListener("keydown",function(e){if(e.key==="Escape"&&fleetPanelOpen)toggleFleetPanel()});

async function executeTask(task){
if(!engine){
ws.send(JSON.stringify({type:"taskFailed",taskFailed:{
leaseId:task.leaseId,taskId:task.taskId,reason:"noEngine",error:"engine not initialized"
}}));
return;
}
setGpuStatus("computing...","working");
try{
// Load weights from artifactKeys if provided and model not yet loaded
if(!engine.hasModel()&&task.artifactKeys&&task.artifactKeys.length>0){
setGpuStatus("loading weights...","working");
for(var ai=0;ai<task.artifactKeys.length;ai++){
var wResp=await fetch("/gpu/"+task.artifactKeys[ai]);
if(wResp.ok){
var wBytes=new Uint8Array(await wResp.arrayBuffer());
engine.loadWeights(wBytes);
console.log("loaded weights from artifact:",task.artifactKeys[ai]);
break;
}
}
setGpuStatus("computing...","working");
}
var taskParams={};
try{taskParams=JSON.parse(task.params||"{}")}catch (_err) { void _err; }
var t0=performance.now();

if(taskParams.prompt&&engine.hasModel()){
// Full LLM inference in browser: tokenize → forward → sample → decode
var prompt=taskParams.prompt||"";
var maxTok=taskParams.maxTokens||64;
// Simple char-level tokenization (GPT-2 tokenizer not available in browser)
// Map chars to token IDs in vocab range [0, 50256]
var tokenIds=[];
for(var ci=0;ci<Math.min(prompt.length,512);ci++){
tokenIds.push(prompt.charCodeAt(ci)%50257);
}
if(tokenIds.length===0)tokenIds=[0];
var logits=await engine.inferenceForward(new Uint32Array(tokenIds));
// Sample from last token logits: greedy argmax
var vocabSize=50257;
var lastLogits=logits.slice((tokenIds.length-1)*vocabSize,tokenIds.length*vocabSize);
var generated=[];
for(var gi=0;gi<Math.min(maxTok,64);gi++){
var maxIdx=0,maxVal=-Infinity;
for(var vi=0;vi<lastLogits.length;vi++){
if(lastLogits[vi]>maxVal){maxVal=lastLogits[vi];maxIdx=vi;}
}
generated.push(maxIdx);
// Next token forward (autoregressive)
tokenIds.push(maxIdx);
logits=await engine.inferenceForward(new Uint32Array(tokenIds));
lastLogits=logits.slice((tokenIds.length-1)*vocabSize,tokenIds.length*vocabSize);
}
// Decode token IDs back to chars
var genText=generated.map(function(tid){return String.fromCharCode(tid%128)}).join("");
var gpuMs=Math.round(performance.now()-t0);
var output=JSON.stringify({response:genText,model:"hayate-v5",tokens:generated.length,gpuTimeMs:gpuMs});
ws.send(JSON.stringify({type:"taskResult",taskResult:{
leaseId:task.leaseId,taskId:task.taskId,output:output,gpuTimeMs:gpuMs
}}));
}else{
// Shard execution (hidden state pass-through or Mamba2 block)
var shardParams=JSON.stringify({groupIdx:0});
var resultJson=await engine.executeShard(task.taskId,task.leaseId,task.params||"",shardParams);
ws.send(resultJson);
}
tasksDone++;
totalGpuMs+=Math.round(performance.now()-t0);
updateGpuBar();
setGpuStatus("idle ("+gpuTier+")","connected");
}catch(e){
console.error("task exec failed:",e);
ws.send(JSON.stringify({type:"taskFailed",taskFailed:{
leaseId:task.leaseId,taskId:task.taskId,reason:"executionError",error:e.message||String(e)
}}));
setGpuStatus("idle ("+gpuTier+")","connected");
}
}
</script>
</body>
</html>`;
