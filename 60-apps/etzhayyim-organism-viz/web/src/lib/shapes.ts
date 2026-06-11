// SVG path generators — per kind, hand-tuned. Imperfection is the aesthetic.

export function kotodamaPath(cx: number, cy: number, r: number): string {
  // 勾玉 — comma-shaped jewel. Hand-tuned cubic Bézier so each seed
  // reads as "alive" rather than generic comma. Slight asymmetry baked in.
  const k = r * 0.55;
  const x0 = cx + r * 0.92, y0 = cy - r * 0.05;          // tip (right)
  const x1 = cx + r * 0.50, y1 = cy + r * 1.05;          // belly bottom
  const x2 = cx - r * 0.95, y2 = cy + r * 0.05;          // tail (left)
  const x3 = cx - r * 0.05, y3 = cy - r * 0.92;          // top belly
  // start at tip, sweep around
  return [
    `M ${x0} ${y0}`,
    `C ${cx + r * 1.05} ${cy + r * 0.50}, ${x1 + k * 0.2} ${y1 - k * 0.15}, ${x1} ${y1}`,
    `C ${x1 - k * 0.9} ${y1}, ${x2 + k * 0.3} ${y2 + k * 0.4}, ${x2} ${y2}`,
    `C ${x2 - k * 0.2} ${y2 - k * 0.8}, ${x3 - k * 0.6} ${y3 + k * 0.2}, ${x3} ${y3}`,
    `C ${cx + r * 0.45} ${cy - r * 0.95}, ${x0 - k * 0.1} ${y0 - k * 0.7}, ${x0} ${y0}`,
    `Z`,
  ].join(" ");
}

export function leafPath(cx: number, cy: number, r: number): string {
  // Asymmetric single-stroke leaf. Tail at bottom-left, tip at top-right.
  const tipX = cx + r * 0.85, tipY = cy - r * 0.95;
  const tailX = cx - r * 0.55, tailY = cy + r * 0.95;
  return [
    `M ${tailX} ${tailY}`,
    `Q ${cx - r * 1.05} ${cy - r * 0.20}, ${tipX} ${tipY}`,
    `Q ${cx + r * 0.20} ${cy + r * 0.60}, ${tailX} ${tailY}`,
    `Z`,
  ].join(" ");
}

export function fanPath(cx: number, cy: number, r: number): string {
  // 扇 — folding fan wedge. Hinge at bottom, opens upward, slight cant.
  const ang = Math.PI * 0.78;   // total opening
  const half = ang / 2;
  const pts: string[] = [`M ${cx} ${cy + r * 0.3}`];
  const segs = 7;
  // arc along the top edge
  for (let i = 0; i <= segs; i++) {
    const t = i / segs;
    const a = -Math.PI / 2 + (t - 0.5) * ang;
    const xx = cx + Math.cos(a) * r * 1.05;
    const yy = cy + Math.sin(a) * r * 1.05 + r * 0.3;
    pts.push(`L ${xx} ${yy}`);
  }
  pts.push("Z");
  return pts.join(" ");
}

export function sealSquarePath(cx: number, cy: number, r: number): string {
  // 印 — rotated rounded square (seal stamp).
  const rot = 0.04;   // slight cant
  const c = Math.cos(rot), s = Math.sin(rot);
  const k = r * 0.18;   // corner radius
  const w = r;
  function P(dx: number, dy: number) {
    return [cx + dx * c - dy * s, cy + dx * s + dy * c];
  }
  const [ax, ay] = P(-w + k, -w);
  const [bx, by] = P(w - k, -w);
  const [c2x, c2y] = P(w, -w + k);
  const [dx, dy] = P(w, w - k);
  const [ex, ey] = P(w - k, w);
  const [fx, fy] = P(-w + k, w);
  const [gx, gy] = P(-w, w - k);
  const [hx, hy] = P(-w, -w + k);
  return `M ${ax} ${ay} L ${bx} ${by} Q ${P(w, -w)[0]} ${P(w, -w)[1]}, ${c2x} ${c2y} L ${dx} ${dy} Q ${P(w, w)[0]} ${P(w, w)[1]}, ${ex} ${ey} L ${fx} ${fy} Q ${P(-w, w)[0]} ${P(-w, w)[1]}, ${gx} ${gy} L ${hx} ${hy} Q ${P(-w, -w)[0]} ${P(-w, -w)[1]}, ${ax} ${ay} Z`;
}

// Wobble points along a path between two endpoints (used for brush-stroke edges)
export function brushPath(x1: number, y1: number, x2: number, y2: number, seed: number): string {
  const dx = x2 - x1, dy = y2 - y1;
  const len = Math.hypot(dx, dy);
  if (len < 1) return `M ${x1} ${y1} L ${x2} ${y2}`;
  const nx = -dy / len, ny = dx / len;
  const segs = 4;
  const pts: [number, number][] = [];
  pts.push([x1, y1]);
  const rng = mulberry32(seed);
  for (let i = 1; i < segs; i++) {
    const t = i / segs;
    const mx = x1 + dx * t, my = y1 + dy * t;
    const wob = (rng() - 0.5) * 3.2;
    pts.push([mx + nx * wob, my + ny * wob]);
  }
  pts.push([x2, y2]);
  // smooth via Catmull-Rom-ish midpoints
  const out: string[] = [`M ${pts[0][0]} ${pts[0][1]}`];
  for (let i = 1; i < pts.length; i++) {
    const [px, py] = pts[i - 1];
    const [cx, cy] = pts[i];
    const mx = (px + cx) / 2, my = (py + cy) / 2;
    out.push(`Q ${px} ${py}, ${mx} ${my}`);
  }
  out.push(`L ${pts[pts.length - 1][0]} ${pts[pts.length - 1][1]}`);
  return out.join(" ");
}

function mulberry32(a: number) {
  let t = (a += 0x6D2B79F5);
  t = Math.imul(t ^ (t >>> 15), t | 1);
  t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
  const seed = ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  // return a generator with stable state
  let st = seed;
  return function () {
    st = (st * 16807 + 0.13141592) % 1;
    return Math.abs(st);
  };
}
