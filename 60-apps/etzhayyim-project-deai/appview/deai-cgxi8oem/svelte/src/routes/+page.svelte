<script lang="ts">
  import { onMount } from "svelte";
  import gsap from "gsap";
  import { SPIRIT_TYPE_META, type SpiritType } from "$lib/spirit-types";
  import SpiritOrb from "$lib/SpiritOrb.svelte";
  import { SPIRIT_PROTOTYPES } from "$lib/spirit-match";

  let participantId = "";
  let hasProfile = false;

  // Cycle through Spirit Types for the 3D orb
  const TYPES: SpiritType[] = ["Hero", "Sage", "Lover", "Caregiver"];
  let orbTypeIdx = 0;
  $: orbType = TYPES[orbTypeIdx];
  $: orbVec = SPIRIT_PROTOTYPES[orbType];

  // GSAP refs
  let heroEl: HTMLElement;
  let pillEl: HTMLElement;
  let headlineEl: HTMLElement;
  let taglineEl: HTMLElement;
  let ctaEl: HTMLElement;
  let stepsEls: HTMLElement[] = [];
  let typeCards: HTMLElement[] = [];
  let paperCardEl: HTMLElement;

  const SPIRIT_TYPES = Object.entries(SPIRIT_TYPE_META) as [SpiritType, typeof SPIRIT_TYPE_META[SpiritType]][];

  // Constellation star positions (fixed seed)
  const STARS = Array.from({ length: 38 }, (_, i) => ({
    x: ((Math.sin(i * 2.4) + 1) / 2) * 100,
    y: ((Math.cos(i * 3.7) + 1) / 2) * 100,
    r: 0.8 + (i % 4) * 0.35,
    delay: (i * 0.13) % 3,
    dur: 2.4 + (i % 5) * 0.6,
  }));

  onMount(() => {
    participantId = localStorage.getItem("deai-participant-id") ?? "";
    hasProfile = !!localStorage.getItem("deai-spirit-type");

    // Cycle orb type every 3s
    setInterval(() => { orbTypeIdx = (orbTypeIdx + 1) % TYPES.length; }, 3000);

    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    tl.fromTo(pillEl,
      { opacity: 0, y: -16, scale: 0.9 },
      { opacity: 1, y: 0, scale: 1, duration: 0.5 }
    )
    .fromTo(headlineEl,
      { opacity: 0, y: 32 },
      { opacity: 1, y: 0, duration: 0.7 },
      "-=0.25"
    )
    .fromTo(taglineEl,
      { opacity: 0, y: 18 },
      { opacity: 1, y: 0, duration: 0.55 },
      "-=0.4"
    )
    .fromTo(ctaEl,
      { opacity: 0, y: 20, scale: 0.96 },
      { opacity: 1, y: 0, scale: 1, duration: 0.5 },
      "-=0.3"
    );

    if (paperCardEl) {
      tl.fromTo(paperCardEl,
        { opacity: 0, y: 30 },
        { opacity: 1, y: 0, duration: 0.6 },
        "-=0.2"
      );
    }

    if (typeCards.length) {
      tl.fromTo(typeCards,
        { opacity: 0, y: 24, scale: 0.93 },
        { opacity: 1, y: 0, scale: 1, duration: 0.45, stagger: 0.08 },
        "-=0.3"
      );
    }

    if (stepsEls.length) {
      tl.fromTo(stepsEls,
        { opacity: 0, x: -24 },
        { opacity: 1, x: 0, duration: 0.4, stagger: 0.07 },
        "-=0.3"
      );
    }
  });

  function tiltCard(e: MouseEvent | TouchEvent, el: HTMLElement) {
    const rect = el.getBoundingClientRect();
    const cx = "touches" in e ? e.touches[0].clientX : e.clientX;
    const cy = "touches" in e ? e.touches[0].clientY : e.clientY;
    const dx = (cx - rect.left) / rect.width - 0.5;
    const dy = (cy - rect.top) / rect.height - 0.5;
    gsap.to(el, {
      rotateY: dx * 14, rotateX: -dy * 10, scale: 1.025,
      duration: 0.28, ease: "power2.out", transformPerspective: 800,
    });
  }

  function resetCard(el: HTMLElement) {
    gsap.to(el, {
      rotateY: 0, rotateX: 0, scale: 1,
      duration: 0.7, ease: "elastic.out(1, 0.45)", transformPerspective: 800,
    });
  }

  // Shimmer animation on CTA hover
  function ctaHover(el: HTMLElement, enter: boolean) {
    gsap.to(el, {
      scale: enter ? 1.025 : 1,
      boxShadow: enter
        ? "0 12px 48px rgba(192,132,252,0.55)"
        : "0 8px 32px rgba(192,132,252,0.3)",
      duration: 0.25, ease: "power2.out",
    });
  }
</script>

<svelte:head>
  <title>deai — Spirit in Physics</title>
  <meta name="description" content="Jung語連想実験×Hume AI感情計測で Spirit を測定し、共鳴するたましいと出会う" />
</svelte:head>

<div class="home">

  <!-- ── Hero ──────────────────────────────── -->
  <header class="hero" bind:this={heroEl}>

    <!-- Constellation background -->
    <div class="constellation" aria-hidden="true">
      <svg width="100%" height="100%" viewBox="0 0 100 100" preserveAspectRatio="xMidYMid slice">
        {#each STARS as s, i}
          <circle cx={s.x} cy={s.y} r={s.r} fill="rgba(192,132,252,0.55)"
            style="animation: starPulse {s.dur}s {s.delay}s ease-in-out infinite"/>
        {/each}
        <!-- constellation lines between nearby stars -->
        {#each STARS.slice(0, 18) as s, i}
          {#if i < 17}
            {@const t = STARS[i + 1]}
            <line x1={s.x} y1={s.y} x2={t.x} y2={t.y}
              stroke="rgba(192,132,252,0.1)" stroke-width="0.3"/>
          {/if}
        {/each}
      </svg>
    </div>

    <!-- Ambient orbs -->
    <div class="orb orb-a" aria-hidden="true"></div>
    <div class="orb orb-b" aria-hidden="true"></div>
    <div class="orb orb-c" aria-hidden="true"></div>

    <!-- 3D Spirit Orb -->
    <div class="orb-stage" aria-hidden="true">
      <SpiritOrb type={orbType} emotionVec={orbVec} size={220} interactive={false} />
      <div class="orb-type-label" style="color: {SPIRIT_TYPE_META[orbType].color}">
        {SPIRIT_TYPE_META[orbType].emoji} {orbType}
      </div>
    </div>

    <div class="hero-inner">
      <div class="pill" bind:this={pillEl}>
        <span class="pill-dot"></span>
        研究データ収集プロジェクト
      </div>

      <h1 bind:this={headlineEl}>
        <span class="h1-sub">Spirit in Physics</span>
        <span class="h1-main">出会いの<br/>物理学</span>
      </h1>

      <p class="tagline" bind:this={taglineEl}>
        Jung の語連想実験 × Hume AI × 熱力学で<br/>
        あなたの <em>Spirit</em> を測定し、共鳴する魂と繋ぐ
      </p>

      <div class="hero-cta" bind:this={ctaEl}>
        {#if hasProfile}
          <a href="/assessment" class="cta-primary"
            on:mouseenter={(e) => ctaHover(e.currentTarget, true)}
            on:mouseleave={(e) => ctaHover(e.currentTarget, false)}
          >
            <span class="cta-shimmer"></span>
            続けて実験する
          </a>
          <a href="/matches" class="cta-ghost">マッチを見る →</a>
        {:else}
          <a href="/assessment" class="cta-primary"
            on:mouseenter={(e) => ctaHover(e.currentTarget, true)}
            on:mouseleave={(e) => ctaHover(e.currentTarget, false)}
          >
            <span class="cta-shimmer"></span>
            Spirit を測定する（無料・匿名）
          </a>
        {/if}
        <p class="hero-note">生体データは端末上でのみ処理 · Cohort DID で匿名化</p>
      </div>
    </div>
  </header>

  <!-- ── Spirit Types ───────────────────────── -->
  <section class="section types-section">
    <p class="section-label">4 Spirit Types</p>
    <h2 class="section-title">Jung アーキタイプ × 熱力学情報空間</h2>
    <div class="type-grid">
      {#each SPIRIT_TYPES as [type, meta], i}
        <div class="type-card" style="--c: {meta.color}"
          bind:this={typeCards[i]}
          on:mousemove={(e) => tiltCard(e, typeCards[i])}
          on:mouseleave={() => resetCard(typeCards[i])}
          on:touchmove|passive={(e) => tiltCard(e, typeCards[i])}
          on:touchend={() => resetCard(typeCards[i])}
        >
          <div class="type-glow" aria-hidden="true"></div>
          <span class="type-emoji">{meta.emoji}</span>
          <span class="type-name">{meta.ja}</span>
          <span class="type-en">{type}</span>
          <span class="type-desc">{meta.desc}</span>
          <div class="type-badge" style="background: {meta.color}18; border-color: {meta.color}44; color: {meta.color}">
            {type === "Hero" ? "Hero↔Caregiver" : type === "Caregiver" ? "Caregiver↔Hero" : type === "Sage" ? "Sage↔Lover" : "Lover↔Sage"}
          </div>
        </div>
      {/each}
    </div>
  </section>

  <!-- ── Research Paper ────────────────────── -->
  <section class="section paper-section">
    <p class="section-label">Research Basis</p>
    <div class="paper-card" bind:this={paperCardEl}>
      <div class="paper-top">
        <div class="paper-badge">arXiv · CNS 2026</div>
        <div class="paper-dot-grid" aria-hidden="true"></div>
      </div>
      <p class="paper-title">Spirit in Physics:<br/><em>Spirit as a Thermodynamic Information Quantity</em></p>
      <p class="paper-authors">Jun Kawasaki · Kazuki Tainaka · Tomonori Takeuchi</p>
      <p class="paper-inst">新潟大学 / オーフス大学</p>
      <div class="formula-wrap">
        <div class="formula-label">Matching Kernel</div>
        <div class="formula">
          <span class="f-main">P(w<sub>O</sub>|w<sub>I</sub>)</span>
          <span class="f-op">∝</span>
          <span class="f-term f-v1">exp(w<sub>I</sub>·w<sub>O</sub>)</span>
          <span class="f-op">×</span>
          <span class="f-term f-v2">r<sup>α</sup></span>
          <span class="f-op">×</span>
          <span class="f-term f-v3">exp(γ·ΔSP/λ)</span>
          <span class="f-op">×</span>
          <span class="f-term f-v4">exp(η·F)</span>
        </div>
        <div class="formula-legend">
          <span><b>r</b> 反応時間逆数</span>
          <span><b>ΔSP</b> 皮膚電位変化</span>
          <span><b>F</b> Hume 感情ベクトル</span>
        </div>
      </div>
    </div>
  </section>

  <!-- ── How it works ──────────────────────── -->
  <section class="section steps-section">
    <p class="section-label">How it works</p>
    <h2 class="section-title">研究の流れ</h2>
    <div class="steps">
      {#each [
        { n: "01", title: "同意 + 参加登録", body: "匿名 Cohort DID で参加。生体データは端末上でのみ処理。" },
        { n: "02", title: "Jung 語連想実験（20語/回）", body: "100語の刺激語に反応。Hume AI が感情を読み取り Spirit Type を判定。" },
        { n: "03", title: "研究 DB に蓄積", body: "反応時間 + Hume スコアが spirit-in-physics.com に送信。研究者が分析。" },
        { n: "04", title: "テンセグリティ共鳴マッチング", body: "RBF カーネルで感情ベクトル距離を計算。Spirit が共鳴する相手と繋がる。" },
      ] as step, i}
        <div class="step" bind:this={stepsEls[i]}>
          <div class="step-num">{step.n}</div>
          <div class="step-body">
            <strong>{step.title}</strong>
            <p>{step.body}</p>
          </div>
        </div>
      {/each}
    </div>
  </section>

  <!-- ── Data transparency ─────────────────── -->
  <section class="section transparency-section">
    <div class="transparency-grid">
      {#each [
        { icon: "🔒", t: "E2E暗号化 + 端末処理", d: "顔・音声は端末で Hume 処理後即破棄。スコアのみ送信。" },
        { icon: "🔗", t: "オープンアクセス", d: "同意データは researcher.spirit-in-physics.com で公開予定。" },
        { icon: "🗑️", t: "いつでも削除可能", d: "メールで Cohort ID を送るだけで全データを完全削除。" },
      ] as item}
        <div class="ti">
          <span class="ti-icon">{item.icon}</span>
          <div>
            <strong>{item.t}</strong>
            <p>{item.d}</p>
          </div>
        </div>
      {/each}
    </div>
  </section>

</div>

<style>
  /* ─── Layout ─────────────────────────── */
  .home { padding-bottom: 48px; }
  .section { padding: 0 20px 40px; max-width: 480px; margin: 0 auto; }
  .section-label {
    font-size: 10px; font-weight: 800; letter-spacing: 0.12em;
    color: rgba(192,132,252,0.6); text-transform: uppercase; margin-bottom: 6px;
  }
  .section-title {
    font-size: 20px; font-weight: 900; letter-spacing: -0.025em;
    color: #f0f0f8; margin-bottom: 20px; line-height: 1.25;
  }

  /* ─── Hero ───────────────────────────── */
  .hero {
    position: relative; overflow: hidden;
    padding: 56px 20px 48px; text-align: center;
    min-height: 380px; display: flex; align-items: center; justify-content: center;
  }

  /* Constellation */
  .constellation {
    position: absolute; inset: 0; pointer-events: none;
  }
  @keyframes starPulse {
    0%, 100% { opacity: 0.25; transform: scale(1); }
    50%       { opacity: 1;    transform: scale(1.5); }
  }

  /* Ambient orbs */
  .orb {
    position: absolute; border-radius: 50%;
    filter: blur(72px); pointer-events: none;
  }
  .orb-a {
    width: 360px; height: 360px;
    background: radial-gradient(circle, rgba(192,132,252,0.22) 0%, transparent 70%);
    top: -100px; left: 50%; transform: translateX(-50%);
    animation: orbDrift 9s ease-in-out infinite;
  }
  .orb-b {
    width: 220px; height: 220px;
    background: radial-gradient(circle, rgba(129,140,248,0.18) 0%, transparent 70%);
    bottom: -40px; right: -40px;
    animation: orbDrift 12s ease-in-out infinite reverse;
  }
  .orb-c {
    width: 180px; height: 180px;
    background: radial-gradient(circle, rgba(244,114,182,0.14) 0%, transparent 70%);
    bottom: 0; left: -30px;
    animation: orbDrift 7.5s ease-in-out infinite 2s;
  }
  @keyframes orbDrift {
    0%,100% { transform: translateX(-50%) scale(1); }
    33%      { transform: translateX(calc(-50% + 18px)) scale(1.06); }
    66%      { transform: translateX(calc(-50% - 22px)) scale(0.95); }
  }
  .orb-b, .orb-c { transform: none; }
  @keyframes orbDriftAbs {
    0%,100% { transform: translate(0,0) scale(1); }
    50%      { transform: translate(-12px, 16px) scale(1.08); }
  }
  .orb-b { animation-name: orbDriftAbs; }
  .orb-c { animation-name: orbDriftAbs; animation-delay: 3.5s; }

  /* 3D Orb */
  .orb-stage {
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -52%);
    z-index: 0;
    display: flex; flex-direction: column; align-items: center; gap: 6px;
    pointer-events: none;
    opacity: 0.65;
  }
  .orb-type-label {
    font-size: 10px; font-weight: 800; letter-spacing: 0.14em;
    text-transform: uppercase; opacity: 0.9;
    transition: color 0.8s ease;
  }

  .hero-inner {
    position: relative; z-index: 1;
    display: flex; flex-direction: column; align-items: center; gap: 18px;
    max-width: 420px; margin: 0 auto;
  }

  /* Pill badge */
  .pill {
    display: inline-flex; align-items: center; gap: 7px;
    padding: 6px 16px;
    background: rgba(129,140,248,0.1);
    border: 1px solid rgba(129,140,248,0.25);
    border-radius: 20px; font-size: 11px; font-weight: 700;
    color: #a5b4fc; letter-spacing: 0.05em;
  }
  .pill-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #4ade80;
    box-shadow: 0 0 6px #4ade80;
    animation: dotBlink 2s ease-in-out infinite;
  }
  @keyframes dotBlink { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }

  /* Headline */
  h1 {
    display: flex; flex-direction: column; align-items: center; gap: 4px;
    margin: 0;
  }
  .h1-sub {
    font-size: 13px; font-weight: 700; letter-spacing: 0.16em;
    color: rgba(192,132,252,0.7); text-transform: uppercase;
  }
  .h1-main {
    font-size: 42px; font-weight: 900; line-height: 1.08; letter-spacing: -0.04em;
    background: linear-gradient(135deg, #f0f0f8 20%, rgba(192,132,252,0.85) 60%, rgba(129,140,248,0.9));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .tagline {
    font-size: 14px; color: rgba(240,240,248,0.5); line-height: 1.75; margin: 0;
  }
  .tagline em { font-style: normal; color: #c084fc; }

  /* CTA */
  .hero-cta { display: flex; flex-direction: column; align-items: center; gap: 12px; width: 100%; }
  .cta-primary {
    position: relative; overflow: hidden;
    display: block; width: 100%; padding: 18px 24px;
    background: linear-gradient(135deg, #c084fc 0%, #818cf8 100%);
    color: #fff; font-size: 16px; font-weight: 800; letter-spacing: 0.01em;
    border-radius: 18px; text-align: center; text-decoration: none;
    box-shadow: 0 8px 32px rgba(192,132,252,0.3);
    will-change: transform;
  }
  .cta-shimmer {
    position: absolute; inset: 0;
    background: linear-gradient(105deg, transparent 30%, rgba(255,255,255,0.22) 50%, transparent 70%);
    transform: translateX(-100%);
    animation: shimmerSlide 3.2s ease-in-out infinite 1s;
  }
  @keyframes shimmerSlide {
    0%   { transform: translateX(-100%); }
    40%  { transform: translateX(100%); }
    100% { transform: translateX(100%); }
  }
  .cta-ghost {
    font-size: 14px; color: rgba(192,132,252,0.65);
    text-decoration: none; transition: color 0.2s;
  }
  .cta-ghost:hover { color: #c084fc; }
  .hero-note {
    font-size: 10px; color: rgba(240,240,248,0.28); letter-spacing: 0.03em;
    margin: 0;
  }

  /* ─── Spirit Types ─────────────────── */
  .types-section { padding-top: 8px; }
  .type-grid {
    display: grid; grid-template-columns: 1fr 1fr; gap: 12px;
  }
  .type-card {
    position: relative; overflow: hidden;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px; padding: 18px 16px;
    display: flex; flex-direction: column; gap: 5px;
    transform-style: preserve-3d; will-change: transform;
    cursor: default;
    transition: border-color 0.2s;
  }
  .type-card:hover { border-color: color-mix(in srgb, var(--c) 40%, transparent); }
  .type-glow {
    position: absolute; inset: 0; pointer-events: none;
    background: radial-gradient(ellipse 80% 60% at 50% 0%, color-mix(in srgb, var(--c) 18%, transparent) 0%, transparent 70%);
  }
  .type-emoji { font-size: 28px; position: relative; z-index: 1; }
  .type-name  { font-size: 16px; font-weight: 900; letter-spacing: -0.02em; position: relative; z-index: 1; }
  .type-en    { font-size: 10px; font-weight: 700; color: var(--c); letter-spacing: 0.08em; text-transform: uppercase; position: relative; z-index: 1; }
  .type-desc  { font-size: 11px; color: rgba(240,240,248,0.42); line-height: 1.45; position: relative; z-index: 1; margin-top: 2px; }
  .type-badge {
    display: inline-block; margin-top: 6px;
    font-size: 9px; font-weight: 700; letter-spacing: 0.04em;
    padding: 3px 8px; border-radius: 8px; border: 1px solid;
    position: relative; z-index: 1; align-self: flex-start;
  }

  /* ─── Paper Card ──────────────────── */
  .paper-section { padding-top: 0; }
  .paper-card {
    position: relative; overflow: hidden;
    background: rgba(99,102,241,0.06);
    border: 1px solid rgba(99,102,241,0.18);
    border-radius: 22px; padding: 22px 20px;
    backdrop-filter: blur(16px);
  }
  .paper-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 14px; }
  .paper-badge {
    font-size: 10px; font-weight: 800; letter-spacing: 0.1em;
    color: #818cf8; text-transform: uppercase;
    background: rgba(129,140,248,0.1); border: 1px solid rgba(129,140,248,0.22);
    border-radius: 8px; padding: 4px 10px;
  }
  .paper-dot-grid {
    width: 48px; height: 24px;
    background-image: radial-gradient(circle, rgba(129,140,248,0.35) 1px, transparent 1px);
    background-size: 8px 8px;
  }
  .paper-title {
    font-size: 15px; font-weight: 800; line-height: 1.4; margin-bottom: 6px;
    color: #f0f0f8;
  }
  .paper-title em { font-style: italic; color: #a5b4fc; }
  .paper-authors { font-size: 12px; color: rgba(240,240,248,0.55); margin-bottom: 2px; }
  .paper-inst    { font-size: 11px; color: rgba(240,240,248,0.35); margin-bottom: 16px; }

  .formula-wrap {
    background: rgba(0,0,0,0.28); border-radius: 14px; padding: 14px 16px;
    border: 1px solid rgba(255,255,255,0.06);
  }
  .formula-label {
    font-size: 9px; font-weight: 700; letter-spacing: 0.1em;
    color: rgba(192,132,252,0.5); text-transform: uppercase; margin-bottom: 10px;
  }
  .formula {
    display: flex; align-items: baseline; flex-wrap: wrap; gap: 4px 6px;
    margin-bottom: 12px;
  }
  .f-main { font-size: 13px; color: rgba(240,240,248,0.7); font-weight: 600; }
  .f-op   { font-size: 13px; color: rgba(240,240,248,0.3); }
  .f-term {
    font-size: 12px; font-weight: 700; font-family: "SF Mono", "Fira Code", monospace;
    padding: 2px 7px; border-radius: 6px;
  }
  .f-v1 { color: #c084fc; background: rgba(192,132,252,0.12); }
  .f-v2 { color: #60a5fa; background: rgba(96,165,250,0.12); }
  .f-v3 { color: #34d399; background: rgba(52,211,153,0.12); }
  .f-v4 { color: #f472b6; background: rgba(244,114,182,0.12); }
  .formula-legend {
    display: flex; gap: 14px; flex-wrap: wrap;
  }
  .formula-legend span { font-size: 10px; color: rgba(240,240,248,0.35); }
  .formula-legend b { color: rgba(240,240,248,0.6); }

  /* ─── Steps ───────────────────────── */
  .steps { display: flex; flex-direction: column; gap: 0; }
  .step {
    display: flex; gap: 16px; padding: 16px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }
  .step:last-child { border-bottom: none; }
  .step-num {
    width: 36px; height: 36px; border-radius: 12px; flex-shrink: 0;
    background: rgba(192,132,252,0.1); border: 1px solid rgba(192,132,252,0.2);
    color: #c084fc; font-size: 11px; font-weight: 900; letter-spacing: 0.05em;
    display: flex; align-items: center; justify-content: center;
  }
  .step-body strong { display: block; font-size: 14px; font-weight: 700; margin-bottom: 4px; color: #f0f0f8; }
  .step-body p { font-size: 12px; color: rgba(240,240,248,0.45); line-height: 1.6; margin: 0; }

  /* ─── Transparency ────────────────── */
  .transparency-section { padding-top: 0; }
  .transparency-grid { display: flex; flex-direction: column; gap: 0; }
  .ti {
    display: flex; gap: 14px; padding: 14px 0;
    border-bottom: 1px solid rgba(255,255,255,0.05);
  }
  .ti:last-child { border-bottom: none; }
  .ti-icon { font-size: 22px; flex-shrink: 0; margin-top: 1px; }
  .ti strong { display: block; font-size: 13px; font-weight: 700; margin-bottom: 3px; }
  .ti p { font-size: 12px; color: rgba(240,240,248,0.45); line-height: 1.55; margin: 0; }
</style>
