<script lang="ts">
  import { onMount } from "svelte";
  import { SPIRIT_TYPE_META, COMPATIBILITY, type SpiritType } from "$lib/spirit-types";

  let spiritType: SpiritType | null = null;
  let cohortDid = "";
  let checkinCount = 0;
  let assessedAt = "";

  // Emotion radar data
  let emotionScores = { joy: 720, calm: 680, focus: 590, awe: 450, surprise: 380 };
  const emotionLabels = ["喜び", "平静", "集中", "畏敬", "驚き"];
  const emotionKeys = ["joy", "calm", "focus", "awe", "surprise"] as const;

  function radarPath(vals: number[], cx: number, cy: number, r: number): string {
    const n = vals.length;
    return vals.map((v, i) => {
      const angle = (2 * Math.PI * i / n) - Math.PI / 2;
      const len = (v / 1000) * r;
      return `${i === 0 ? "M" : "L"} ${(cx + len * Math.cos(angle)).toFixed(1)},${(cy + len * Math.sin(angle)).toFixed(1)}`;
    }).join(" ") + " Z";
  }

  function radarGrid(cx: number, cy: number, r: number, n: number, frac: number): string {
    return Array.from({length: n}, (_, i) => {
      const angle = (2 * Math.PI * i / n) - Math.PI / 2;
      const len = r * frac;
      return `${i === 0 ? "M" : "L"} ${(cx + len * Math.cos(angle)).toFixed(1)},${(cy + len * Math.sin(angle)).toFixed(1)}`;
    }).join(" ") + " Z";
  }

  function axisPoint(i: number, n: number, cx: number, cy: number, r: number): {x: number; y: number} {
    const angle = (2 * Math.PI * i / n) - Math.PI / 2;
    return { x: cx + r * Math.cos(angle), y: cy + r * Math.sin(angle) };
  }

  function labelPoint(i: number, n: number, cx: number, cy: number, r: number): {x: number; y: number} {
    const angle = (2 * Math.PI * i / n) - Math.PI / 2;
    const len = r + 16;
    return { x: cx + len * Math.cos(angle), y: cy + len * Math.sin(angle) };
  }

  onMount(() => {
    spiritType = (localStorage.getItem("deai-spirit-type") as SpiritType) ?? null;
    cohortDid = localStorage.getItem("deai-cohort-did") ?? "";
    const countStr = localStorage.getItem("deai-checkin-count");
    checkinCount = countStr ? parseInt(countStr) : 0;
    assessedAt = localStorage.getItem("deai-assessed-at") ?? "";
  });

  $: compatibleTypes = spiritType
    ? (Object.entries(COMPATIBILITY[spiritType]) as [SpiritType, number][])
        .sort((a, b) => b[1] - a[1])
    : [];

  $: radarVals = emotionKeys.map(k => emotionScores[k]);
  const SVG_CX = 100;
  const SVG_CY = 100;
  const SVG_R = 70;
  const N = 5;
</script>

<svelte:head><title>プロフィール — deai</title></svelte:head>

<div class="profile-page">
  <h1>Spirit プロフィール</h1>

  {#if !spiritType}
    <div class="no-profile">
      <span class="no-profile-icon">🪬</span>
      <p>Spirit 診断がまだ完了していません。</p>
      <a href="/assessment" class="cta-btn">診断を始める</a>
    </div>
  {:else}
    {@const meta = SPIRIT_TYPE_META[spiritType]}
    {@const accent = meta.color}

    <!-- Spirit Card -->
    <div class="spirit-card" style="--accent: {accent}">
      <div class="card-bg-glow" style="background: radial-gradient(circle at 85% 15%, {accent}28, transparent 60%)"></div>
      <div class="glow-dot" style="background: {accent}; box-shadow: 0 0 30px {accent}88"></div>
      <span class="card-emoji">{meta.emoji}</span>
      <div class="card-text">
        <h2>{meta.ja}</h2>
        <span class="en-type">{spiritType}</span>
        <p class="card-desc">{meta.desc}</p>
      </div>
      <div class="accent-strip" style="background: {accent}"></div>
    </div>

    <!-- Stats -->
    <div class="stats-row">
      <div class="stat">
        <span class="stat-val">{checkinCount}</span>
        <span class="stat-label">Check-in 回数</span>
      </div>
      <div class="stat">
        <span class="stat-val">{assessedAt ? new Date(assessedAt).toLocaleDateString("ja") : "—"}</span>
        <span class="stat-label">診断日</span>
      </div>
    </div>

    <!-- Emotion Radar -->
    <section class="radar-section">
      <h3 class="section-title">感情場</h3>
      <div class="radar-wrap">
        <svg viewBox="0 0 200 200" width="200" height="200" class="radar-svg">
          <!-- Grid rings -->
          {#each [0.33, 0.66, 1.0] as frac}
            <path d={radarGrid(SVG_CX, SVG_CY, SVG_R, N, frac)}
                  fill="none" stroke="rgba(255,255,255,0.1)" stroke-width="1"/>
          {/each}
          <!-- Axis lines -->
          {#each Array.from({length: N}, (_, i) => i) as i}
            {@const pt = axisPoint(i, N, SVG_CX, SVG_CY, SVG_R)}
            <line x1={SVG_CX} y1={SVG_CY} x2={pt.x} y2={pt.y}
                  stroke="rgba(255,255,255,0.08)" stroke-width="1"/>
          {/each}
          <!-- Score polygon -->
          <path d={radarPath(radarVals, SVG_CX, SVG_CY, SVG_R)}
                fill="rgba(192,132,252,0.22)" stroke="#c084fc" stroke-width="2"
                style="filter: drop-shadow(0 0 8px rgba(192,132,252,0.5))"/>
          <!-- Labels -->
          {#each Array.from({length: N}, (_, i) => i) as i}
            {@const lp = labelPoint(i, N, SVG_CX, SVG_CY, SVG_R)}
            <text x={lp.x} y={lp.y} text-anchor="middle" dominant-baseline="middle"
                  fill="rgba(240,240,248,0.65)" font-size="9.5" font-family="-apple-system,sans-serif">
              {emotionLabels[i]}
            </text>
          {/each}
        </svg>
        <div class="radar-legend">
          {#each emotionKeys as k, i}
            <div class="legend-item">
              <span class="legend-dot"></span>
              <span class="legend-name">{emotionLabels[i]}</span>
              <span class="legend-val">{emotionScores[k]}</span>
            </div>
          {/each}
        </div>
      </div>
    </section>

    <!-- Cohort DID -->
    {#if cohortDid}
      <div class="did-panel">
        <p class="did-label">Cohort DID（匿名 ID）</p>
        <p class="did-value">{cohortDid}</p>
        <p class="did-note">✓ 実名・メールはサーバーに保存されません</p>
      </div>
    {/if}

    <!-- Compatibility -->
    <section class="compat-section">
      <h3 class="section-title">Spirit 相性</h3>
      <div class="compat-list">
        {#each compatibleTypes as [type, score]}
          {@const m = SPIRIT_TYPE_META[type]}
          <div class="compat-item">
            <span class="compat-emoji">{m.emoji}</span>
            <div class="compat-info">
              <span class="compat-name">{m.ja}</span>
              <div class="compat-bar">
                <div class="compat-fill" style="width: {score/10}%; background: {m.color}"></div>
              </div>
            </div>
            <span class="compat-score">{score}</span>
          </div>
        {/each}
      </div>
    </section>

    <!-- Theory -->
    <section class="theory-section">
      <h3 class="section-title">Spirit in Physics</h3>
      <div class="theory-content">
        <p>あなたの Spirit Type は以下の測定式で判定されました:</p>
        <code>P(w|w_i) ∝ exp(w·w_i) × r^α × exp(η·F)</code>
        <ul>
          <li><code>r</code> = 語への反応時間逆数</li>
          <li><code>F</code> = Hume AI 感情スコア（10次元）</li>
          <li>Spirit = 熱力学的情報量として測定</li>
        </ul>
        <p class="paper-ref">Kawasaki et al. (2026) — Niigata Univ. / Aarhus Univ.</p>
      </div>
    </section>

    <button class="reset-btn" on:click={() => { localStorage.clear(); spiritType = null; }}>
      プロフィールをリセット
    </button>
  {/if}
</div>

<style>
  .profile-page { padding: 28px 18px 12px; max-width: 480px; margin: 0 auto; display: flex; flex-direction: column; gap: 22px; }
  h1 { font-size: 26px; font-weight: 800; letter-spacing: -0.03em; }

  .no-profile { text-align: center; padding: 60px 0; display: flex; flex-direction: column; gap: 16px; align-items: center; }
  .no-profile-icon { font-size: 56px; }
  .no-profile p { color: rgba(240,240,248,0.55); font-size: 14px; }
  .cta-btn { padding: 15px 32px; background: linear-gradient(135deg, #c084fc, #818cf8); color: #fff; border-radius: 14px; font-size: 15px; font-weight: 700; box-shadow: 0 4px 20px rgba(192,132,252,0.35); }

  /* Spirit Card */
  .spirit-card {
    position: relative; overflow: hidden;
    display: flex; align-items: center; gap: 16px;
    padding: 24px; border-radius: 22px;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.09);
    backdrop-filter: blur(12px);
  }
  .accent-strip {
    position: absolute; top: 0; left: 0; width: 4px; bottom: 0; border-radius: 4px 0 0 4px;
  }
  .card-bg-glow { position: absolute; inset: 0; pointer-events: none; }
  .glow-dot {
    position: absolute; top: 14px; right: 14px;
    width: 40px; height: 40px; border-radius: 50%;
    opacity: 0.5; filter: blur(8px);
    pointer-events: none;
  }
  .card-emoji { font-size: 54px; flex-shrink: 0; position: relative; z-index: 1; }
  .card-text { flex: 1; position: relative; z-index: 1; }
  h2 { font-size: 22px; font-weight: 900; margin-bottom: 2px; color: var(--accent); }
  .en-type { font-size: 12px; color: rgba(240,240,248,0.4); display: block; margin-bottom: 6px; letter-spacing: 0.04em; }
  .card-desc { font-size: 13px; color: rgba(240,240,248,0.6); line-height: 1.55; }

  /* Stats */
  .stats-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  .stat { background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 16px; padding: 18px; text-align: center; }
  .stat-val { display: block; font-size: 24px; font-weight: 800; color: #c084fc; }
  .stat-label { font-size: 11px; color: rgba(240,240,248,0.4); margin-top: 4px; display: block; }

  /* Radar */
  .radar-section {}
  .section-title { font-size: 11px; font-weight: 700; color: rgba(240,240,248,0.4); text-transform: uppercase; letter-spacing: 0.07em; margin-bottom: 16px; }
  .radar-wrap { display: flex; align-items: center; gap: 20px; background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 18px; padding: 20px; }
  .radar-svg { flex-shrink: 0; }
  .radar-legend { flex: 1; display: flex; flex-direction: column; gap: 8px; }
  .legend-item { display: flex; align-items: center; gap: 8px; }
  .legend-dot { width: 7px; height: 7px; border-radius: 50%; background: #c084fc; flex-shrink: 0; }
  .legend-name { flex: 1; font-size: 12px; color: rgba(240,240,248,0.6); }
  .legend-val { font-size: 12px; color: #c084fc; font-weight: 700; }

  /* DID */
  .did-panel { background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.07); border-radius: 14px; padding: 14px 16px; }
  .did-label { font-size: 10px; color: rgba(240,240,248,0.35); margin-bottom: 6px; letter-spacing: 0.04em; text-transform: uppercase; }
  .did-value { font-size: 11px; font-family: monospace; color: rgba(240,240,248,0.65); word-break: break-all; line-height: 1.5; }
  .did-note { font-size: 10px; color: #4ade80; margin-top: 8px; }

  /* Compat */
  .compat-section {}
  .compat-list { display: flex; flex-direction: column; gap: 10px; }
  .compat-item { display: grid; grid-template-columns: 2rem 1fr 3rem; gap: 10px; align-items: center; }
  .compat-emoji { font-size: 22px; }
  .compat-name { font-size: 13px; display: block; margin-bottom: 5px; font-weight: 600; }
  .compat-bar { height: 4px; background: rgba(255,255,255,0.08); border-radius: 2px; overflow: hidden; }
  .compat-fill { height: 100%; border-radius: 2px; transition: width 0.7s ease; }
  .compat-score { font-size: 12px; color: rgba(240,240,248,0.45); text-align: right; }

  /* Theory */
  .theory-content { background: rgba(192,132,252,0.05); border: 1px solid rgba(192,132,252,0.13); border-radius: 14px; padding: 18px; }
  .theory-content p { font-size: 13px; color: rgba(240,240,248,0.6); margin-bottom: 10px; line-height: 1.6; }
  .theory-content code { display: block; font-size: 11.5px; color: #c084fc; background: rgba(0,0,0,0.25); padding: 8px 12px; border-radius: 8px; margin: 10px 0; overflow-x: auto; }
  .theory-content ul { padding-left: 16px; display: flex; flex-direction: column; gap: 4px; }
  .theory-content li { font-size: 12px; color: rgba(240,240,248,0.5); }
  .theory-content li code { display: inline; padding: 1px 5px; font-size: 11px; }
  .paper-ref { font-size: 11px; color: rgba(240,240,248,0.3); font-style: italic; }

  /* Reset */
  .reset-btn { width: 100%; padding: 14px; background: none; border: 1px solid rgba(248,113,113,0.25); color: rgba(248,113,113,0.6); border-radius: 12px; font-size: 14px; cursor: pointer; transition: border-color 0.15s, color 0.15s; }
  .reset-btn:hover { border-color: rgba(248,113,113,0.45); color: rgba(248,113,113,0.85); }
</style>
