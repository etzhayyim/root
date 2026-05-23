// etzhayyim-organism-viz — interactive bonsai client.
// Vanilla JS, no framework. Substrate-boundary safe: only talks to same-origin /api/*.

const $ = (sel) => document.querySelector(sel);
const NS = "http://www.w3.org/2000/svg";

let state = null;
let selectedEntity = null;

// ── SVG render ────────────────────────────────────────────────────────────

function clear(el) { while (el.firstChild) el.removeChild(el.firstChild); }

function svgEl(tag, attrs = {}) {
  const e = document.createElementNS(NS, tag);
  for (const [k, v] of Object.entries(attrs)) e.setAttribute(k, v);
  return e;
}

const AXES = [
  ["autopoiesis",      "Autopoiesis 自己創出"],
  ["metabolism",       "Metabolism 代謝"],
  ["homeostasis",      "Homeostasis 恒常性"],
  ["active_inference", "Active Inference 能動推論"],
  ["reproduction",     "Reproduction 生殖"],
  ["symbiosis",        "Symbiosis 共生"],
  ["diversity",        "Diversity 多様性"],
  ["wellbecoming",     "Wellbecoming 動的軌跡"],
  ["antifragility",    "Anti-fragility 反脆弱"],
  ["sanctification",   "Sanctification 聖化"],
];

function renderBonsai(s) {
  const svg = $("#bonsai");
  clear(svg);
  const cx = 500, baseY = 700, trunkTopY = 420;

  // roots
  const root = svgEl("rect", {
    x: cx - 160, y: baseY, width: 320, height: 56, rx: 8,
    fill: "var(--root)", stroke: "#3a2a14", "stroke-width": 2,
    class: "root-node", "data-entity": "fruit/lands",
  });
  svg.appendChild(root);
  svg.appendChild(svgEl("text", {
    x: cx, y: baseY + 22, "text-anchor": "middle", fill: "#fff8e8",
    class: "root-node", "data-entity": "fruit/lands",
  })).textContent = "inalienable roots — LANDS · MEMBERS";
  svg.appendChild(svgEl("text", {
    x: cx, y: baseY + 42, "text-anchor": "middle", fill: "#fff8e8",
    "font-size": 11, class: "root-node", "data-entity": "fruit/members",
  })).textContent = `子世代 → 孫世代 (MGI = ${s.alive.G_generational.toFixed(2)})`;

  // trunk
  const trunk = svgEl("polygon", {
    points: `${cx-36},${baseY} ${cx+36},${baseY} ${cx+22},${trunkTopY} ${cx-22},${trunkTopY}`,
    fill: "var(--trunk)", stroke: "#5e4520", "stroke-width": 2,
    class: "trunk-node", "data-entity": "organism/cns",
  });
  svg.appendChild(trunk);
  svg.appendChild(svgEl("text", {
    x: cx, y: baseY - 8, "text-anchor": "middle", fill: "#fff8e8",
    "font-size": 10, class: "trunk-node", "data-entity": "organism/cns",
  })).textContent = "trunk = ADR-2605192100 (constitution)";

  // branches — 10 axes
  const n = AXES.length;
  const Rx = 380, Ry = 280;
  for (let i = 0; i < n; i++) {
    const [key, label] = AXES[i];
    const t = i / (n - 1);
    const angDeg = -150 + 120 * t;
    const ang = (angDeg * Math.PI) / 180;
    const tipX = cx + Math.cos(ang) * Rx;
    const tipY = trunkTopY + Math.sin(ang) * Ry;
    const score = s.axis_scores[key] || 0;
    const color = score >= 8 ? "var(--leaf)" : score >= 5 ? "var(--leaf-mid)" : "var(--leaf-bad)";

    const branch = svgEl("line", {
      x1: cx, y1: trunkTopY + 10, x2: tipX.toFixed(0), y2: tipY.toFixed(0),
      stroke: color, "stroke-width": (2 + score / 3).toFixed(1), "stroke-linecap": "round",
      class: "branch-line", "data-entity": `axis/${key}`,
    });
    svg.appendChild(branch);

    // leaves (count = score)
    for (let j = 0; j < score; j++) {
      const jt = (j + 1) / (score + 1);
      const lx = cx + Math.cos(ang) * Rx * (0.55 + 0.45 * jt) + Math.sin(ang) * 8;
      const ly = trunkTopY + Math.sin(ang) * Ry * (0.55 + 0.45 * jt) - Math.cos(ang) * 8;
      const leaf = svgEl("circle", {
        cx: lx.toFixed(0), cy: ly.toFixed(0), r: 4, fill: color, opacity: 0.9,
        class: "leaf-node", "data-entity": `axis/${key}`,
      });
      svg.appendChild(leaf);
    }

    // flowers — bloom on branches with positive Δ (state.flowers contains axis ids)
    if ((s.flowers || []).includes(`axis/${key}`)) {
      const fx = cx + Math.cos(ang) * Rx * 0.85 + Math.sin(ang) * 14;
      const fy = trunkTopY + Math.sin(ang) * Ry * 0.85 - Math.cos(ang) * 14;
      const flower = svgEl("circle", {
        cx: fx.toFixed(0), cy: fy.toFixed(0), r: 7, fill: "var(--flower)",
        stroke: "#fff", "stroke-width": 2, class: "flower-node",
        "data-entity": `axis/${key}`,
      });
      svg.appendChild(flower);
    }

    // tip label
    const anchor = tipX < cx ? "end" : "start";
    const ofx = tipX < cx ? -8 : 8;
    const tl = svgEl("text", {
      x: (tipX + ofx).toFixed(0), y: tipY.toFixed(0),
      "text-anchor": anchor, fill: "#333", "font-size": 11,
      class: "axis-label", "data-entity": `axis/${key}`,
    });
    tl.appendChild(document.createTextNode(label + " "));
    const sp = svgEl("tspan", { fill: "#888" });
    sp.textContent = `${score}/10`;
    tl.appendChild(sp);
    svg.appendChild(tl);
  }

  // apps — small cluster as moss at the base of the trunk
  const appIds = Object.keys(s.entities).filter(k => k.startsWith("app/")).slice(0, 30);
  appIds.forEach((aid, i) => {
    const col = i % 10, row = Math.floor(i / 10);
    const ax = cx - 130 + col * 26;
    const ay = baseY - 26 + row * 8;
    const ent = s.entities[aid];
    const idle = ent.state.idle_days || 0;
    const fill = idle > 180 ? "#a05050" : (idle > 90 ? "#c9a25b" : "#5a8a4a");
    const m = svgEl("circle", {
      cx: ax, cy: ay, r: 4, fill, opacity: 0.85,
      class: "app-node", "data-entity": aid,
    });
    svg.appendChild(m);
  });

  // recent ADRs — small dark rings around the trunk's bottom (growth rings)
  const adrIds = Object.keys(s.entities).filter(k => k.startsWith("adr/")).slice(0, 12);
  adrIds.forEach((did, i) => {
    const yy = baseY - 18 - i * 6;
    const r = svgEl("ellipse", {
      cx: cx, cy: yy, rx: 30 - i * 0.8, ry: 3, fill: "none",
      stroke: "#5e4520", "stroke-width": 0.8, opacity: 0.55,
      class: "adr-node", "data-entity": did,
    });
    svg.appendChild(r);
  });

  // fruits — at branch tips or in canopy. Place around top arc.
  const fruits = s.fruits || [];
  fruits.forEach((fid, i) => {
    const t = i / Math.max(1, fruits.length - 1 || 1);
    const angDeg = -130 + 80 * t;
    const ang = (angDeg * Math.PI) / 180;
    const fx = cx + Math.cos(ang) * (Rx - 30);
    const fy = trunkTopY + Math.sin(ang) * (Ry - 20) - 40;
    const fruit = svgEl("circle", {
      cx: fx.toFixed(0), cy: fy.toFixed(0), r: 9, fill: "var(--fruit)",
      stroke: "#5e2810", "stroke-width": 1.5, class: "fruit-node",
      "data-entity": fid,
    });
    svg.appendChild(fruit);
    const lbl = svgEl("text", {
      x: fx.toFixed(0), y: (fy - 12).toFixed(0), "text-anchor": "middle",
      "font-size": 10, fill: "#5e2810",
      class: "fruit-node", "data-entity": fid,
    });
    lbl.textContent = fid.replace("fruit/", "");
    svg.appendChild(lbl);
  });

  // seeds — emanate from fruits down toward root area
  const seeds = s.seeds || [];
  seeds.forEach((seed, i) => {
    const fromFruit = (s.fruits || []).indexOf(seed.from);
    if (fromFruit < 0) return;
    const t = fromFruit / Math.max(1, (s.fruits || []).length - 1 || 1);
    const angDeg = -130 + 80 * t;
    const ang = (angDeg * Math.PI) / 180;
    const fx = cx + Math.cos(ang) * (Rx - 30);
    const fy = trunkTopY + Math.sin(ang) * (Ry - 20) - 40;
    // seed lands somewhere along root area
    const sx = cx - 140 + (i / Math.max(1, seeds.length - 1 || 1)) * 280;
    const sy = baseY - 6;
    // dotted line from fruit to seed landing
    const line = svgEl("path", {
      d: `M ${fx.toFixed(0)} ${fy.toFixed(0)} Q ${(fx+sx)/2} ${(fy+sy)/2 + 80} ${sx.toFixed(0)} ${sy.toFixed(0)}`,
      stroke: "var(--seed)", "stroke-width": 1, fill: "none",
      "stroke-dasharray": "3 4", opacity: 0.4,
    });
    svg.appendChild(line);
    const seedEl = svgEl("polygon", {
      points: `${sx-4},${sy} ${sx+4},${sy} ${sx},${sy-6}`,
      fill: "var(--seed)", class: "seed-node", "data-entity": seed.id,
    });
    svg.appendChild(seedEl);
  });

  // event wiring
  svg.querySelectorAll("[data-entity]").forEach(el => {
    el.addEventListener("click", (ev) => {
      ev.stopPropagation();
      const id = el.getAttribute("data-entity");
      selectEntity(id);
    });
  });
}

// ── side panel ────────────────────────────────────────────────────────────

function selectEntity(id) {
  selectedEntity = id;
  // clear previous highlights
  document.querySelectorAll(".selected, .neighbor").forEach(n => n.classList.remove("selected", "neighbor"));
  document.querySelectorAll(`[data-entity="${CSS.escape(id)}"]`).forEach(n => n.classList.add("selected"));
  const ent = state && state.entities && state.entities[id];
  if (!ent) {
    $("#entity-title").textContent = id;
    $("#entity-sub").textContent = "(unknown entity)";
    $("#entity-state").textContent = "";
    return;
  }
  // highlight neighbors (縁起 chain made visible)
  for (const nb of ent.neighbors || []) {
    document.querySelectorAll(`[data-entity="${CSS.escape(nb)}"]`).forEach(n => n.classList.add("neighbor"));
  }
  // render the entity card
  const pruneTag = (ent.pruning_severity || 0) > 0 ? ` 🪒×${ent.pruning_severity}` : "";
  $("#entity-title").textContent = `${kindIcon(ent.kind)} ${ent.title}${pruneTag}`;
  $("#entity-sub").innerHTML =
    `${ent.kind} · <code>${ent.id}</code> · ` +
    `neighbors: ${(ent.neighbors || []).map(n =>
      `<a href="#" data-jump="${escapeAttr(n)}">${n}</a>`).join(", ") || "—"}`;
  $("#entity-sub").querySelectorAll("[data-jump]").forEach(a => {
    a.addEventListener("click", (ev) => { ev.preventDefault(); selectEntity(a.getAttribute("data-jump")); });
  });
  $("#entity-state").textContent = JSON.stringify(ent.state || {}, null, 2);
  const log = $("#chat-log");
  appendMsg(log, "them", ent.chat_invite || "(silent)", ent.title);
  log.scrollTop = log.scrollHeight;
}

function escapeAttr(s) { return String(s).replace(/"/g, "&quot;"); }

function kindIcon(kind) {
  return ({
    axis: "🌿", cell: "✿", organism: "🌳", ecosystem: "🌏",
    fruit: "🍎", seed: "🌰", app: "📦", adr: "📜",
  })[kind] || "•";
}

function appendMsg(log, who, text, label) {
  const div = document.createElement("div");
  div.className = `msg ${who}`;
  const w = document.createElement("span");
  w.className = "who"; w.textContent = label || (who === "you" ? "you" : "");
  const t = document.createElement("span");
  t.textContent = text;
  div.appendChild(w); div.appendChild(t);
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
}

$("#chat-form").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const msg = $("#chat-input").value.trim();
  if (!msg) return;
  if (!selectedEntity) {
    appendMsg($("#chat-log"), "them", "対話相手を SVG から選んでください。", "system");
    return;
  }
  appendMsg($("#chat-log"), "you", msg, "you");
  $("#chat-input").value = "";
  try {
    const r = await fetch("/api/chat", {
      method: "POST", headers: {"Content-Type": "application/json"},
      body: JSON.stringify({entity_id: selectedEntity, message: msg}),
    });
    const data = await r.json();
    if (data.ok) {
      appendMsg($("#chat-log"), "them", data.voice, state.entities[selectedEntity]?.title || selectedEntity);
    } else {
      appendMsg($("#chat-log"), "them", "[error] " + (data.error || "unknown"), "system");
    }
  } catch (e) {
    appendMsg($("#chat-log"), "them", "[network] " + e.message, "system");
  }
});

// ── activity / state plumbing ────────────────────────────────────────────

function updatePills(s) {
  $("#status-pill").textContent = "online";
  $("#status-pill").className = "pill ok";
  const a = s.alive;
  const inb = s.in_band || {};
  const inCount = Object.values(inb).filter(Boolean).length;
  $("#aliveness-pill").textContent =
    `A(t) = ⟨ M ${a.M_motion.toFixed(2)} · D ${a.D_diversity.toFixed(2)} · C ${a.C_coupling.toFixed(2)} · P ${a.P_pruning.toFixed(2)} · G ${a.G_generational.toFixed(2)} ⟩  (${inCount}/5 in band)`;
  $("#aliveness-pill").className = `pill ${inCount === 5 ? "ok" : (inCount >= 3 ? "" : "bad")}`;
  $("#cycles-pill").textContent = `entities = ${Object.keys(s.entities).length}`;
  $("#ts-pill").textContent = new Date(s.timestamp * 1000).toLocaleTimeString("ja-JP");
}

function pushActivity(ev) {
  const list = $("#activity-list");
  const li = document.createElement("li");
  const t = document.createElement("span");
  t.className = "t";
  t.textContent = new Date((ev.ts || Date.now()/1000) * 1000).toLocaleTimeString("ja-JP");
  const s = document.createElement("span");
  s.textContent = `[${ev.type}] ${ev.summary || ev.subject || ev.id || ""}`;
  li.appendChild(t); li.appendChild(s);
  list.insertBefore(li, list.firstChild);
  while (list.children.length > 60) list.removeChild(list.lastChild);
}

function renderPruning(s) {
  const list = $("#pruning-list");
  if (!list) return;
  list.innerHTML = "";
  const cands = s.pruning || [];
  if (!cands.length) {
    list.innerHTML = '<li class="muted">候補なし — 盆栽は overgrowth なく健全に伸びている</li>';
    return;
  }
  for (const c of cands.slice(0, 30)) {
    const li = document.createElement("li");
    li.className = `sev${c.severity}`;
    li.innerHTML = `🪒 <code>${c.id}</code> · idle ${c.idle_days}日 · ${c.reasons.join("; ")}`;
    li.addEventListener("click", () => selectEntity(c.id));
    list.appendChild(li);
  }
}

async function fetchState() {
  try {
    const r = await fetch("/api/state");
    state = await r.json();
    renderBonsai(state);
    updatePills(state);
    renderPruning(state);
    (state.activity || []).slice(0, 20).forEach(pushActivity);
  } catch (e) {
    $("#status-pill").textContent = "fetch error: " + e.message;
    $("#status-pill").className = "pill bad";
  }
}

function startSSE() {
  const es = new EventSource("/api/events");
  es.onopen = () => { $("#status-pill").textContent = "stream open"; $("#status-pill").className = "pill ok"; };
  es.onerror = () => { $("#status-pill").textContent = "stream reconnecting…"; $("#status-pill").className = "pill bad"; };
  es.onmessage = (m) => {
    try {
      const ev = JSON.parse(m.data);
      if (ev.type === "tick" || ev.type === "hello") {
        if (ev.state) {
          state = ev.state;
          renderBonsai(state);
          updatePills(state);
          renderPruning(state);
        }
      }
      if (ev.type !== "heartbeat") pushActivity(ev);
    } catch {}
  };
}

// boot
fetchState().then(startSSE);
