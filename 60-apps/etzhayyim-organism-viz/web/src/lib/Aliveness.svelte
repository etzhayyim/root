<script lang="ts">
  import type { Snapshot } from "./types";
  export let snap: Snapshot;
  $: a = snap?.alive;
  $: bands = snap?.in_band || {};
  const DIMS = [
    { k: "M", label: "M 動 motion",       lo: "> 0.5",      get: () => a.M_motion       },
    { k: "D", label: "D 多 diversity",    lo: "> 1.5 nats", get: () => a.D_diversity    },
    { k: "C", label: "C 縁 coupling",     lo: "0.2..0.7",   get: () => a.C_coupling     },
    { k: "P", label: "P 剪 pruning",      lo: "0.5..1.0",   get: () => a.P_pruning      },
    { k: "G", label: "G 継 generational", lo: "> 1.0",      get: () => a.G_generational },
  ];

  const AXES = [
    ["autopoiesis",      "自"],
    ["metabolism",       "代"],
    ["homeostasis",      "和"],
    ["active_inference", "縁"],
    ["reproduction",     "生"],
    ["symbiosis",        "共"],
    ["diversity",        "八"],
    ["wellbecoming",     "孫"],
    ["antifragility",    "脆"],
    ["sanctification",   "聖"],
  ];

  function sparkline(values: number[], w = 56, h = 16): string {
    if (!values || values.length === 0) return "";
    const max = 10, min = 0;
    const xs = values.map((_v, i) => (values.length === 1 ? w / 2 : (i / (values.length - 1)) * w));
    const ys = values.map(v => h - ((v - min) / (max - min)) * h);
    return xs.map((x, i) => (i === 0 ? "M" : "L") + ` ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(" ");
  }
  function endValue(values: number[]): number { return values && values.length ? values[values.length - 1] : 0; }
  function sparkColor(end: number): string {
    return end >= 8 ? "var(--moegi)" : end >= 5 ? "var(--kincha)" : "var(--suou)";
  }

  // total trajectory geometry (computed reactively so we can use it in SVG markup)
  const TOTAL_W = 600;
  const TOTAL_H = 38;
  const TOTAL_MAX = 100;
  const TOTAL_MIN = 60;
  function totalGeom(totals: number[]) {
    const len = totals?.length || 0;
    if (len === 0) return { xs: [] as number[], ys: [] as number[], line: "", area: "" };
    const xs = totals.map((_, i) => len === 1 ? TOTAL_W / 2 : (i / (len - 1)) * TOTAL_W);
    const ys = totals.map(v => TOTAL_H - 4 - ((Math.max(TOTAL_MIN, Math.min(TOTAL_MAX, v)) - TOTAL_MIN) / (TOTAL_MAX - TOTAL_MIN)) * (TOTAL_H - 8));
    const line = xs.map((x, i) => `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(" ");
    const area = `M 0 ${TOTAL_H - 4} ` + xs.map((x, i) => `L ${x.toFixed(1)} ${ys[i].toFixed(1)}`).join(" ") + ` L ${TOTAL_W} ${TOTAL_H - 4} Z`;
    return { xs, ys, line, area };
  }
  $: totalG = totalGeom(snap?.trajectory_totals || []);
</script>

<header class="kakejiku">
  <div class="brand">
    <span class="brand-jp">etzhayyim</span>
    <span class="sep">·</span>
    <span class="brand-en">縁起トポロジー</span>
  </div>
  {#if a}
    <div class="dials">
      {#each DIMS as d}
        <div class="dial" class:on={bands[d.k]}>
          <span class="dot">{bands[d.k] ? "●" : "○"}</span>
          <span class="lbl">{d.label}</span>
          <span class="val">{d.get().toFixed(2)}</span>
          <span class="band">{d.lo}</span>
        </div>
      {/each}
    </div>
  {/if}

  {#if snap.trajectory && snap.trajectory_cycles && snap.trajectory_cycles.length > 1}
    <div class="trajectory">
      <div class="trajectory-head">
        軌跡
        <span class="cycle-range">cycle {snap.trajectory_cycles[0]}…{snap.trajectory_cycles[snap.trajectory_cycles.length - 1]}</span>
        <span class="total-now">total {snap.trajectory_totals[snap.trajectory_totals.length - 1]} / 100</span>
      </div>

      <!-- big-picture: total trajectory across all axes (max 100) -->
      <svg class="total-spark" viewBox="0 0 600 38" preserveAspectRatio="none">
        <line x1="0" y1="34" x2="600" y2="34" stroke="var(--washi-deep)" stroke-width="0.6" stroke-dasharray="2 3"/>
        <path d={totalG.area} fill="var(--shinshu)" opacity="0.10"/>
        <path d={totalG.line} fill="none" stroke="var(--shinshu)" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
        {#if totalG.xs.length > 0}
          <circle cx={totalG.xs[totalG.xs.length - 1]} cy={totalG.ys[totalG.ys.length - 1]} r="2.2" fill="var(--shinshu)"/>
          <text x="4" y="30" font-size="9" fill="var(--sumi-pale)">{snap.trajectory_totals[0]}</text>
          <text x="584" y="30" font-size="9" fill="var(--shinshu)" text-anchor="end">{snap.trajectory_totals[snap.trajectory_totals.length - 1]}</text>
        {/if}
      </svg>

      <div class="sparks">
        {#each AXES as [k, glyph]}
          {@const values = snap.trajectory[k] || []}
          {@const end = endValue(values)}
          <div class="spark" title={`${k}: ${values.join(" → ")}`}>
            <span class="g">{glyph}</span>
            <svg viewBox="0 0 56 16" preserveAspectRatio="none">
              <path d={sparkline(values)} fill="none" stroke={sparkColor(end)} stroke-width="1.4"/>
              {#if values.length}
                <circle cx={values.length === 1 ? 28 : (((values.length - 1) / (values.length - 1)) * 56)}
                        cy={16 - (end / 10) * 16}
                        r="1.6" fill={sparkColor(end)}/>
              {/if}
            </svg>
            <span class="v">{end}</span>
          </div>
        {/each}
      </div>
    </div>
  {/if}
</header>

<style>
  .kakejiku {
    grid-row: 1;
    background: var(--washi-warm);
    border-bottom: 1px solid var(--sumi);
    padding: 14px 28px 12px;
    display: flex; align-items: baseline; gap: 24px;
    flex-wrap: wrap;
  }
  .brand { font-size: 19px; font-weight: 700; letter-spacing: 0.01em; }
  .brand-jp { color: var(--shinshu); }
  .brand-en { color: var(--sumi-soft); font-weight: 500; }
  .sep { color: var(--sumi-pale); margin: 0 6px; }
  .dials { display: flex; gap: 14px; flex-wrap: wrap; flex: 1; }
  .dial {
    display: flex; align-items: baseline; gap: 6px;
    padding: 2px 8px;
    border-left: 1px solid var(--sumi-pale);
    font-family: var(--font-num);
  }
  .dial .dot { font-size: 14px; color: var(--sumi-pale); }
  .dial.on .dot { color: var(--shinshu); }
  .dial .lbl { font-size: 11px; color: var(--sumi-soft); letter-spacing: 0.04em; }
  .dial .val { font-size: 15px; font-weight: 700; color: var(--sumi); font-variant-numeric: tabular-nums; }
  .dial .band { font-size: 10px; color: var(--sumi-pale); }

  .trajectory { flex-basis: 100%; padding-top: 8px; border-top: 1px dotted var(--sumi-pale); }
  .total-spark { width: 100%; height: 38px; display: block; margin: 4px 0 8px; }
  .trajectory-head {
    display: flex; align-items: baseline; gap: 10px;
    font-size: 11px; color: var(--sumi-soft); margin-bottom: 4px;
  }
  .trajectory-head .cycle-range, .trajectory-head .total-now {
    color: var(--sumi-pale); font-family: var(--font-num); font-variant-numeric: tabular-nums;
  }
  .trajectory-head .total-now { color: var(--shinshu); }
  .sparks { display: flex; flex-wrap: wrap; gap: 10px 14px; }
  .spark { display: flex; align-items: center; gap: 4px; }
  .spark .g { font-size: 12px; color: var(--sumi-soft); }
  .spark svg { width: 56px; height: 16px; display: block; }
  .spark .v {
    font-size: 11px; color: var(--sumi); font-family: var(--font-num);
    font-variant-numeric: tabular-nums; min-width: 14px; text-align: right;
  }
</style>
