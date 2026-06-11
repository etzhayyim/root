// Orbital seeding + 5-iteration spring relaxation.
// No D3, no Cytoscape — pure JS. The semantic placement IS the visual signature.

import type { NodePos, Snapshot, Entity } from "./types";

const TAU = Math.PI * 2;

const AXIS_ORDER = [
  "autopoiesis", "metabolism", "homeostasis", "active_inference",
  "reproduction", "symbiosis", "diversity", "wellbecoming",
  "antifragility", "sanctification",
];

const R_AXES   = 220;   // inner ring
const R_FRUITS = 140;   // between center and axes
const R_SEEDS  =  85;   // deeper toward roots — returning home
const R_ADRS   =  60;   // tight ring around center
const R_CELLS  = 320;   // outside axes
const R_APPS   = 420;   // outermost belt

function seedR(kind: string): number {
  return ({ axis: 22, cell: 11, app: 8, adr: 14, fruit: 16, seed: 10, organism: 26, ecosystem: 38 })[kind] || 10;
}

export function buildLayout(snap: Snapshot, w: number, h: number): NodePos[] {
  const cx = w / 2, cy = h / 2;
  const positions: NodePos[] = [];
  const byId = new Map<string, NodePos>();
  const rng = mulberry32(0xe72ade1a);
  let i = 0;

  function place(id: string, kind: string, x: number, y: number) {
    const p: NodePos = {
      id, kind: kind as any, x, y, vx: 0, vy: 0,
      r: seedR(kind),
      phase: rng() * TAU,
    };
    positions.push(p); byId.set(id, p); i++;
  }

  // ecosystem center
  if (snap.entities["ecosystem/etzhayyim"])
    place("ecosystem/etzhayyim", "ecosystem", cx, cy);
  // organism just above center
  if (snap.entities["organism/cns"])
    place("organism/cns", "organism", cx, cy - 60);

  // 10 axes around ring
  AXIS_ORDER.forEach((axis, idx) => {
    const a = (idx / AXIS_ORDER.length) * TAU - Math.PI / 2;
    const id = `axis/${axis}`;
    if (snap.entities[id]) place(id, "axis", cx + Math.cos(a) * R_AXES, cy + Math.sin(a) * R_AXES);
  });

  // ADRs — tight inner ring around center
  const adrIds = Object.keys(snap.entities).filter(k => k.startsWith("adr/"));
  adrIds.forEach((id, idx) => {
    const a = (idx / Math.max(1, adrIds.length)) * TAU;
    place(id, "adr", cx + Math.cos(a) * R_ADRS, cy + Math.sin(a) * R_ADRS);
  });

  // Fruits — between center and axes, angle matched to their primary axis
  const fruitAxis: Record<string, string> = {
    "fruit/lands":            "wellbecoming",
    "fruit/members":          "wellbecoming",
    "fruit/fork-bootstrap":   "reproduction",
    "fruit/chaos-rehearsals": "antifragility",
  };
  snap.fruits.forEach((fid, idx) => {
    const ax = fruitAxis[fid] || AXIS_ORDER[idx % AXIS_ORDER.length];
    const axIdx = AXIS_ORDER.indexOf(ax);
    const a = (axIdx / AXIS_ORDER.length) * TAU - Math.PI / 2 + 0.05 * (idx % 2 ? 1 : -1);
    place(fid, "fruit", cx + Math.cos(a) * R_FRUITS, cy + Math.sin(a) * R_FRUITS);
  });

  // Seeds — closer to center than fruits (returning home), placed inside their fruit's arc
  snap.seeds.forEach((s, idx) => {
    const parent = byId.get(s.from);
    if (parent) {
      const dx = parent.x - cx, dy = parent.y - cy;
      const d = Math.max(1, Math.hypot(dx, dy));
      const ux = dx / d, uy = dy / d;
      // place at radius slightly less than fruit, offset perpendicular
      const px = -uy, py = ux;
      const off = 12 * (idx % 2 ? -1 : 1);
      place(s.id, "seed", cx + ux * R_SEEDS + px * off, cy + uy * R_SEEDS + py * off);
    } else {
      const a = rng() * TAU;
      place(s.id, "seed", cx + Math.cos(a) * R_SEEDS, cy + Math.sin(a) * R_SEEDS);
    }
  });

  // Cells — cluster behind their primary axis (read from entity's neighbors)
  const cellIds = Object.keys(snap.entities).filter(k => k.startsWith("cell/"));
  cellIds.forEach((id, idx) => {
    const ent = snap.entities[id];
    // first neighbor that's an axis
    const ax = (ent.neighbors || []).find(n => n.startsWith("axis/"));
    let baseA = (idx / Math.max(1, cellIds.length)) * TAU;
    if (ax) {
      const aKey = ax.replace("axis/", "");
      const axIdx = AXIS_ORDER.indexOf(aKey);
      if (axIdx >= 0) baseA = (axIdx / AXIS_ORDER.length) * TAU - Math.PI / 2;
    }
    const spread = (rng() - 0.5) * 0.45;
    const a = baseA + spread;
    const radius = R_CELLS + (rng() - 0.5) * 40;
    place(id, "cell", cx + Math.cos(a) * radius, cy + Math.sin(a) * radius);
  });

  // Apps — perimeter belt, sorted alphabetically for stability
  const appIds = Object.keys(snap.entities).filter(k => k.startsWith("app/"));
  appIds.forEach((id, idx) => {
    const a = (idx / Math.max(1, appIds.length)) * TAU;
    const r = R_APPS + (rng() - 0.5) * 30;
    place(id, "app", cx + Math.cos(a) * r, cy + Math.sin(a) * r);
  });

  // 5-iteration light relaxation
  const edges: [string, string][] = [];
  for (const ent of Object.values(snap.entities) as Entity[]) {
    for (const n of ent.neighbors || []) {
      if (snap.entities[n]) edges.push([ent.id, n]);
    }
  }

  const seed = positions.map(p => ({ ...p }));
  for (let it = 0; it < 5; it++) {
    // Coulomb repulsion (nearby only)
    for (let i = 0; i < positions.length; i++) {
      for (let j = i + 1; j < positions.length; j++) {
        const a = positions[i], b = positions[j];
        const dx = b.x - a.x, dy = b.y - a.y;
        const d2 = dx * dx + dy * dy;
        if (d2 > 60 * 60 || d2 < 1) continue;
        const d = Math.sqrt(d2);
        const f = 900 / d2;
        const fx = (dx / d) * f, fy = (dy / d) * f;
        a.vx -= fx; a.vy -= fy;
        b.vx += fx; b.vy += fy;
      }
    }
    // edge attraction
    for (const [u, v] of edges) {
      const a = byId.get(u), b = byId.get(v);
      if (!a || !b) continue;
      const dx = b.x - a.x, dy = b.y - a.y;
      const d = Math.max(1, Math.hypot(dx, dy));
      const target = 130;
      const f = 0.025 * (d - target);
      const fx = (dx / d) * f, fy = (dy / d) * f;
      a.vx += fx; a.vy += fy;
      b.vx -= fx; b.vy -= fy;
    }
    // pull back toward orbital seed (preserves semantic placement)
    for (let i = 0; i < positions.length; i++) {
      const p = positions[i], s = seed[i];
      p.vx += (s.x - p.x) * 0.06;
      p.vy += (s.y - p.y) * 0.06;
    }
    // integrate + damp
    for (const p of positions) {
      p.x += p.vx; p.y += p.vy;
      p.vx *= 0.5; p.vy *= 0.5;
    }
  }
  return positions;
}

// Compute edges keyed for rendering — annotate with relationship kind for color.
export function buildEdges(snap: Snapshot, positions: NodePos[]): {
  a: NodePos; b: NodePos; kind: "default" | "sacred" | "inheritance" | "ring";
}[] {
  const byId = new Map(positions.map(p => [p.id, p]));
  const edges: any[] = [];
  const seen = new Set<string>();
  for (const ent of Object.values(snap.entities) as Entity[]) {
    for (const n of ent.neighbors || []) {
      const k = ent.id < n ? `${ent.id}|${n}` : `${n}|${ent.id}`;
      if (seen.has(k)) continue;
      seen.add(k);
      const a = byId.get(ent.id), b = byId.get(n);
      if (!a || !b) continue;
      const involves = (kind: string) =>
        ent.kind === kind || (snap.entities[n] && snap.entities[n].kind === kind);
      let kKind: any = "default";
      if (involves("ecosystem") || involves("organism")) kKind = "sacred";
      else if (involves("adr")) kKind = "ring";
      else if (involves("fruit") && involves("seed")) kKind = "inheritance";
      else if (involves("seed")) kKind = "inheritance";
      edges.push({ a, b, kind: kKind });
    }
  }
  return edges;
}

// PRNG so layout is deterministic between renders.
function mulberry32(a: number) {
  return function () {
    let t = (a += 0x6D2B79F5);
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}
