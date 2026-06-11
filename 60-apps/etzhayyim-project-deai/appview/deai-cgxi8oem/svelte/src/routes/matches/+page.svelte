<script lang="ts">
  import { onMount, tick } from "svelte";
  import gsap from "gsap";
  import { deaiApi } from "$lib/api";
  import { SPIRIT_TYPE_META, type MatchRecord, type SpiritType } from "$lib/spirit-types";
  import { computeMatch, demoVec, type EmotionVec5 } from "$lib/spirit-match";
  import SpiritRadar3D from "$lib/SpiritRadar3D.svelte";

  interface RichMatch extends MatchRecord {
    emotionVec: EmotionVec5;
    breakdown: ReturnType<typeof computeMatch>;
  }

  let matches: RichMatch[] = [];
  let loading = true;
  let selfDid = "";
  let selfType: SpiritType | null = null;
  let selfVec: EmotionVec5 = [0.5, 0.5, 0.5, 0.5, 0.5];
  let filterTab: "all" | "resonant" | "new" = "all";

  // GSAP refs
  let featuredCardEl: HTMLDivElement;
  let scoreNumEl: HTMLSpanElement;
  let uSpiritEl: HTMLSpanElement;
  let uResonanceEl: HTMLSpanElement;
  let matchListEl: HTMLDivElement;
  let headerEl: HTMLElement;

  const SPIRIT_COLORS: Record<string, string> = {
    Hero: "#ef4444", Sage: "#60a5fa", Lover: "#f472b6", Caregiver: "#34d399",
  };

  const DEMO_PARTNERS: Array<{ type: SpiritType; seed: number; did: string; hasConversation: boolean }> = [
    { type: "Caregiver", seed: 1,  did: "did:web:decom.etzhayyim.ai:demo1", hasConversation: false },
    { type: "Lover",     seed: 2,  did: "did:web:decom.etzhayyim.ai:demo2", hasConversation: true  },
    { type: "Hero",      seed: 3,  did: "did:web:decom.etzhayyim.ai:demo3", hasConversation: false },
    { type: "Sage",      seed: 4,  did: "did:web:decom.etzhayyim.ai:demo4", hasConversation: false },
    { type: "Caregiver", seed: 11, did: "did:web:decom.etzhayyim.ai:demo5", hasConversation: false },
  ];

  function compatibilityReason(typeA: SpiritType, typeB: SpiritType, score: number): string {
    const pairs: Record<string, string> = {
      "Hero-Caregiver":      "保護と養育のテンセグリティ補完",
      "Caregiver-Hero":      "養育と保護のテンセグリティ補完",
      "Sage-Lover":          "思考と感性の補完的共鳴",
      "Lover-Sage":          "感性と思考の補完的共鳴",
      "Hero-Sage":           "行動と洞察の協調",
      "Sage-Hero":           "洞察と行動の協調",
      "Hero-Lover":          "使命と感性の融合",
      "Lover-Hero":          "感性と使命の融合",
      "Sage-Caregiver":      "知恵と共感の統合",
      "Caregiver-Sage":      "共感と知恵の統合",
      "Lover-Caregiver":     "感性と養育の調和",
      "Caregiver-Lover":     "養育と感性の調和",
    };
    const key = `${typeA}-${typeB}`;
    const base = pairs[key] ?? `${typeA}×${typeB}: Spirit 共鳴`;
    if (score >= 900) return `🔥 ${base} (完全共鳴)`;
    if (score >= 750) return `💫 ${base}`;
    return base;
  }

  function buildRichMatch(
    type: SpiritType, seed: number, did: string, hasConversation: boolean, selfT: SpiritType
  ): RichMatch {
    const emotionVec = demoVec(type, seed);
    const breakdown = computeMatch(selfT, selfVec, type, emotionVec);
    return {
      cohortDid: did,
      spiritType: type,
      resonanceScore: breakdown.score1000,
      spiritCompatibility: Math.round(breakdown.uSpirit * 1000),
      separationDelta: Math.round(breakdown.uResonance * 500),
      compatibilityReason: compatibilityReason(selfT, type, breakdown.score1000),
      matchedAt: new Date().toISOString(),
      hasConversation,
      emotionVec,
      breakdown,
    };
  }

  onMount(async () => {
    selfDid = localStorage.getItem("deai-cohort-did") ?? "";
    selfType = (localStorage.getItem("deai-spirit-type") as SpiritType) ?? null;
    if (selfType) selfVec = demoVec(selfType, 0);

    if (!selfDid) { loading = false; return; }

    try {
      const res = await deaiApi.listMatches(selfDid);
      const raw = res.matches as MatchRecord[];
      matches = raw.map((m, i) => buildRichMatch(
        m.spiritType as SpiritType, i + 1, m.cohortDid, m.hasConversation, selfType ?? "Hero"
      ));
    } catch {
      matches = DEMO_PARTNERS.map(({ type, seed, did, hasConversation }) =>
        buildRichMatch(type, seed, did, hasConversation, selfType ?? "Hero")
      );
    } finally {
      matches.sort((a, b) => b.resonanceScore - a.resonanceScore);
      loading = false;
      await tick();
      runEntranceAnimation();
    }
  });

  function runEntranceAnimation() {
    const tl = gsap.timeline({ defaults: { ease: "power3.out" } });

    // Header slides down
    if (headerEl) {
      tl.fromTo(headerEl,
        { opacity: 0, y: -24 },
        { opacity: 1, y: 0, duration: 0.5 }
      );
    }

    // Featured card: rise + fade + subtle scale
    if (featuredCardEl) {
      tl.fromTo(featuredCardEl,
        { opacity: 0, y: 48, scale: 0.94 },
        { opacity: 1, y: 0, scale: 1, duration: 0.7 },
        "-=0.2"
      );
    }

    // Score number counts up from 0
    if (scoreNumEl && featured) {
      const target = { val: 0 };
      tl.to(target, {
        val: featured.resonanceScore,
        duration: 1.1,
        ease: "power2.out",
        onUpdate() { if (scoreNumEl) scoreNumEl.textContent = Math.round(target.val).toString(); },
      }, "-=0.4");
    }

    // Sub-scores count up
    if (uSpiritEl && featured) {
      const s = { v: 0 };
      tl.to(s, {
        v: Math.round(featured.breakdown.uSpirit * 100),
        duration: 0.9, ease: "power2.out",
        onUpdate() { if (uSpiritEl) uSpiritEl.textContent = Math.round(s.v) + "%"; },
      }, "<");
    }
    if (uResonanceEl && featured) {
      const r = { v: 0 };
      tl.to(r, {
        v: Math.round(featured.breakdown.uResonance * 100),
        duration: 0.9, ease: "power2.out",
        onUpdate() { if (uResonanceEl) uResonanceEl.textContent = Math.round(r.v) + "%"; },
      }, "<0.1");
    }

    // Match list cards stagger in
    if (matchListEl) {
      const cards = matchListEl.querySelectorAll(".match-card");
      tl.fromTo(cards,
        { opacity: 0, x: -32 },
        { opacity: 1, x: 0, duration: 0.45, stagger: 0.08 },
        "-=0.5"
      );
    }
  }

  // 3D card tilt on mouse/touch move
  function onCardMove(e: MouseEvent | TouchEvent, el: HTMLElement) {
    const rect = el.getBoundingClientRect();
    const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
    const clientY = "touches" in e ? e.touches[0].clientY : e.clientY;
    const cx = (clientX - rect.left) / rect.width - 0.5;   // -0.5 to 0.5
    const cy = (clientY - rect.top)  / rect.height - 0.5;
    gsap.to(el, {
      rotateY: cx * 10, rotateX: -cy * 8,
      scale: 1.018,
      duration: 0.3, ease: "power2.out",
      transformPerspective: 900,
    });
  }

  function onCardLeave(el: HTMLElement) {
    gsap.to(el, {
      rotateY: 0, rotateX: 0, scale: 1,
      duration: 0.6, ease: "elastic.out(1, 0.5)",
      transformPerspective: 900,
    });
  }

  $: filtered = filterTab === "resonant"
    ? matches.filter(m => m.resonanceScore >= 750)
    : filterTab === "new"
    ? matches.filter(m => !m.hasConversation)
    : matches;

  $: featured = filtered[0] ?? null;
  $: rest = filtered.slice(1);

  function spiritColor(type: string): string {
    return SPIRIT_COLORS[type] ?? "#c084fc";
  }

  function resonanceLabel(score: number): string {
    if (score >= 900) return "🔥 完全共鳴";
    if (score >= 750) return "💫 高共鳴";
    if (score >= 600) return "✨ 共鳴";
    return "🌱 芽生え";
  }

</script>

<svelte:head><title>マッチ — deai</title></svelte:head>

<div class="matches-page">
  <!-- Ambient background orbs -->
  <div class="orb orb-1" aria-hidden="true"></div>
  <div class="orb orb-2" aria-hidden="true"></div>

  <header class="page-header" bind:this={headerEl}>
    <div class="header-top">
      <h1>Spirit マッチ</h1>
      {#if selfType}
        {@const meta = SPIRIT_TYPE_META[selfType]}
        <div class="self-badge" style="--c: {spiritColor(selfType)}">
          <span>{meta.emoji}</span>
          <span>{meta.ja}</span>
        </div>
      {:else}
        <a href="/assessment" class="no-profile-link">診断する →</a>
      {/if}
    </div>

    <div class="filter-tabs">
      <button class="filter-btn" class:active={filterTab === "all"} on:click={() => filterTab = "all"}>すべて</button>
      <button class="filter-btn" class:active={filterTab === "resonant"} on:click={() => filterTab = "resonant"}>高共鳴</button>
      <button class="filter-btn" class:active={filterTab === "new"} on:click={() => filterTab = "new"}>未連絡</button>
    </div>
  </header>

  {#if loading}
    <div class="loading-state">
      <div class="pulse-ring"></div>
      <p>Spirit テンセグリティ計算中...</p>
    </div>
  {:else if filtered.length === 0}
    <div class="empty-state">
      <p class="empty-icon">🌌</p>
      <p>マッチが見つかりません</p>
      <a href="/assessment" class="cta-link">Spirit 診断を完了してください</a>
    </div>
  {:else}
    <!-- Featured card -->
    {#if featured}
      {@const meta = SPIRIT_TYPE_META[featured.spiritType as SpiritType]}
      {@const accent = spiritColor(featured.spiritType)}
      {@const bd = featured.breakdown}
      <div class="featured-card" style="--accent: {accent}"
        bind:this={featuredCardEl}
        on:mousemove={(e) => onCardMove(e, featuredCardEl)}
        on:mouseleave={() => onCardLeave(featuredCardEl)}
        on:touchmove|passive={(e) => onCardMove(e, featuredCardEl)}
        on:touchend={() => onCardLeave(featuredCardEl)}
      >
        <div class="featured-glow" style="background: radial-gradient(ellipse 120% 80% at 90% 10%, {accent}28 0%, transparent 65%)"></div>
        <div class="hot-badge">⚡ 最高共鳴</div>

        <div class="featured-top">
          <!-- Spirit avatar -->
          <div class="spirit-avatar-lg" style="background: {accent}1a; border-color: {accent}55; box-shadow: 0 0 32px {accent}22">
            <span class="spirit-emoji-lg">{meta?.emoji ?? "✨"}</span>
          </div>
          <div class="featured-info">
            <span class="featured-type" style="color: {accent}">{meta?.ja ?? featured.spiritType}</span>
            <span class="featured-did">{featured.cohortDid.slice(-12)}</span>
            <span class="resonance-chip">{resonanceLabel(featured.resonanceScore)}</span>
          </div>

          <!-- 3D Dual-radar -->
          <div class="radar-wrap">
            <SpiritRadar3D
              selfVec={selfType ? selfVec : featured.emotionVec}
              partnerVec={featured.emotionVec}
              accentColor={accent}
              size={120}
            />
          </div>
        </div>

        <!-- Score breakdown -->
        <div class="score-row">
          <div class="score-chip">
            <span class="score-label">Spirit</span>
            <span class="score-val" bind:this={uSpiritEl}>{Math.round(bd.uSpirit * 100)}%</span>
          </div>
          <div class="score-divider">×</div>
          <div class="score-chip">
            <span class="score-label">共鳴</span>
            <span class="score-val" bind:this={uResonanceEl}>{Math.round(bd.uResonance * 100)}%</span>
          </div>
          {#if bd.complementBonus > 1}
            <div class="score-divider">×</div>
            <div class="score-chip complement">
              <span class="score-label">補完</span>
              <span class="score-val">×{bd.complementBonus}</span>
            </div>
          {/if}
          <div class="score-total">
            <span class="score-total-num" style="color: {accent}" bind:this={scoreNumEl}>{featured.resonanceScore}</span>
            <span class="score-total-denom">/1000</span>
          </div>
        </div>

        <p class="featured-reason">{featured.compatibilityReason}</p>

        <a
          href="/message?with={encodeURIComponent(featured.cohortDid)}&spirit={encodeURIComponent(featured.spiritType)}"
          class="featured-cta"
          style="background: linear-gradient(135deg, {accent}, #818cf8)"
        >
          話しかける ✨
        </a>
      </div>
    {/if}

    <!-- Compact list -->
    {#if rest.length > 0}
      <div class="section-label">他のマッチ</div>
      <div class="match-list" bind:this={matchListEl}>
        {#each rest as m}
          {@const meta = SPIRIT_TYPE_META[m.spiritType as SpiritType]}
          {@const accent = spiritColor(m.spiritType)}
          <a
            href="/message?with={encodeURIComponent(m.cohortDid)}&spirit={encodeURIComponent(m.spiritType)}"
            class="match-card"
            style="--accent: {accent}"
          >
            <div class="spirit-circle-sm" style="background: {accent}18; border-color: {accent}44; box-shadow: 0 0 14px {accent}18">
              <span class="spirit-emoji-sm">{meta?.emoji ?? "✨"}</span>
            </div>
            <div class="match-center">
              <div class="match-top-row">
                <span class="match-type" style="color: {accent}">{meta?.ja ?? m.spiritType}</span>
                <span class="match-badge">{resonanceLabel(m.resonanceScore)}</span>
              </div>
              <p class="match-reason">{m.compatibilityReason.replace(/^[🔥💫✨🌱]\s*/, "")}</p>
              <div class="resonance-bar-wrap">
                <div class="resonance-bar-track">
                  <div class="resonance-bar-fill" style="width: {m.resonanceScore / 10}%; background: linear-gradient(90deg, {accent}, #818cf8)"></div>
                </div>
                <span class="resonance-val">{m.resonanceScore}</span>
              </div>
            </div>
            <div class="match-arrow">›</div>
          </a>
        {/each}
      </div>
    {/if}
  {/if}
</div>

<style>
  .matches-page {
    position: relative;
    padding: 28px 18px 16px;
    max-width: 480px;
    margin: 0 auto;
    overflow: hidden;
  }

  /* Ambient orbs */
  .orb {
    position: fixed; border-radius: 50%;
    pointer-events: none; z-index: 0;
    filter: blur(80px); opacity: 0.18;
  }
  .orb-1 {
    width: 300px; height: 300px;
    background: radial-gradient(circle, #c084fc 0%, transparent 70%);
    top: -80px; right: -60px;
    animation: orbFloat1 8s ease-in-out infinite;
  }
  .orb-2 {
    width: 240px; height: 240px;
    background: radial-gradient(circle, #818cf8 0%, transparent 70%);
    bottom: 20%; left: -80px;
    animation: orbFloat2 11s ease-in-out infinite;
  }
  @keyframes orbFloat1 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(-20px,30px) scale(1.08); } }
  @keyframes orbFloat2 { 0%,100% { transform: translate(0,0) scale(1); } 60% { transform: translate(24px,-18px) scale(1.05); } }

  /* Header */
  .page-header { position: relative; z-index: 1; margin-bottom: 24px; display: flex; flex-direction: column; gap: 16px; }
  .header-top { display: flex; align-items: center; justify-content: space-between; }
  h1 {
    font-size: 28px; font-weight: 900; letter-spacing: -0.04em;
    background: linear-gradient(135deg, #f0f0f8 30%, rgba(192,132,252,0.8));
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .self-badge {
    display: inline-flex; align-items: center; gap: 5px;
    background: color-mix(in srgb, var(--c) 12%, transparent);
    border: 1px solid color-mix(in srgb, var(--c) 28%, transparent);
    border-radius: 20px; padding: 5px 12px; font-size: 12px;
    color: var(--c, #c084fc); font-weight: 600;
  }
  .no-profile-link { font-size: 13px; color: rgba(192,132,252,0.6); }

  .filter-tabs { display: flex; gap: 8px; }
  .filter-btn {
    flex: 1; padding: 9px 0; border-radius: 12px;
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.04);
    color: rgba(240,240,248,0.45); font-size: 13px; font-weight: 600;
    cursor: pointer; transition: all 0.18s ease;
    backdrop-filter: blur(12px);
  }
  .filter-btn.active {
    background: rgba(192,132,252,0.12);
    border-color: rgba(192,132,252,0.3);
    color: #c084fc;
  }

  /* Loading / Empty */
  .loading-state { text-align: center; padding: 60px 0; position: relative; z-index: 1; }
  .pulse-ring {
    width: 56px; height: 56px; border-radius: 50%;
    border: 2px solid rgba(192,132,252,0.35); margin: 0 auto 16px;
    animation: pulse 1.5s ease-in-out infinite;
    box-shadow: 0 0 0 0 rgba(192,132,252,0.15);
  }
  @keyframes pulse { 0%,100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(192,132,252,0.3); } 50% { transform: scale(1.1); box-shadow: 0 0 0 12px rgba(192,132,252,0); } }
  .loading-state p { color: rgba(240,240,248,0.4); font-size: 13px; }
  .empty-state { text-align: center; padding: 60px 20px; display: flex; flex-direction: column; align-items: center; gap: 12px; position: relative; z-index: 1; }
  .empty-icon { font-size: 48px; }
  .cta-link { color: #c084fc; font-size: 14px; }

  /* Featured card */
  .featured-card {
    position: relative; z-index: 1; overflow: hidden;
    background: rgba(255,255,255,0.038);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 24px; padding: 22px 20px 20px;
    margin-bottom: 28px;
    backdrop-filter: blur(20px) saturate(1.4);
    -webkit-backdrop-filter: blur(20px) saturate(1.4);
    box-shadow: 0 8px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.07);
    transform-style: preserve-3d;
    will-change: transform;
    cursor: default;
  }
  .featured-glow { position: absolute; inset: 0; pointer-events: none; }
  .hot-badge {
    position: absolute; top: 16px; right: 16px;
    background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.25);
    color: #f87171; font-size: 10px; font-weight: 800; letter-spacing: 0.04em;
    border-radius: 20px; padding: 3px 10px;
  }

  .featured-top {
    display: flex; align-items: center; gap: 14px;
    margin-bottom: 18px;
  }
  .spirit-avatar-lg {
    width: 68px; height: 68px; flex-shrink: 0; border-radius: 50%;
    border: 1.5px solid; display: flex; align-items: center; justify-content: center;
  }
  .spirit-emoji-lg { font-size: 34px; }
  .featured-info {
    flex: 1; display: flex; flex-direction: column; gap: 4px;
  }
  .featured-type { font-size: 20px; font-weight: 900; letter-spacing: -0.02em; }
  .featured-did { font-size: 10px; color: rgba(240,240,248,0.3); font-family: monospace; }
  .resonance-chip {
    display: inline-block; font-size: 11px; color: rgba(240,240,248,0.6);
    background: rgba(255,255,255,0.06); border-radius: 8px; padding: 2px 8px;
    align-self: flex-start;
  }

  /* Radar */
  .radar-wrap { flex-shrink: 0; }
  .radar-svg { overflow: visible; }

  /* Score breakdown */
  .score-row {
    display: flex; align-items: center; gap: 8px;
    padding: 12px 14px;
    background: rgba(255,255,255,0.04);
    border-radius: 14px; margin-bottom: 14px;
    border: 1px solid rgba(255,255,255,0.06);
  }
  .score-chip {
    display: flex; flex-direction: column; align-items: center; gap: 2px;
    flex: 1;
  }
  .score-chip.complement .score-val { color: #4ade80; }
  .score-label { font-size: 9px; color: rgba(240,240,248,0.35); letter-spacing: 0.04em; text-transform: uppercase; }
  .score-val { font-size: 13px; font-weight: 800; color: rgba(240,240,248,0.85); }
  .score-divider { color: rgba(240,240,248,0.2); font-size: 14px; flex-shrink: 0; }
  .score-total {
    display: flex; align-items: baseline; gap: 2px;
    margin-left: auto; flex-shrink: 0;
  }
  .score-total-num { font-size: 24px; font-weight: 900; line-height: 1; letter-spacing: -0.04em; }
  .score-total-denom { font-size: 11px; color: rgba(240,240,248,0.3); }

  .featured-reason {
    font-size: 13px; color: rgba(240,240,248,0.55); line-height: 1.6;
    margin-bottom: 16px;
  }
  .featured-cta {
    display: block; width: 100%; padding: 15px; text-align: center;
    color: #fff; font-size: 15px; font-weight: 800; letter-spacing: 0.01em;
    border-radius: 16px;
    box-shadow: 0 6px 24px rgba(192,132,252,0.35);
    transition: opacity 0.15s, transform 0.15s;
  }
  .featured-cta:hover { opacity: 0.88; transform: translateY(-2px); }
  .featured-cta:active { transform: translateY(0); }

  /* Section label */
  .section-label {
    position: relative; z-index: 1;
    font-size: 10px; font-weight: 800; letter-spacing: 0.1em;
    color: rgba(240,240,248,0.28); text-transform: uppercase;
    margin-bottom: 10px;
  }

  /* Compact match list */
  .match-list { position: relative; z-index: 1; display: flex; flex-direction: column; gap: 8px; }
  .match-card {
    display: flex; align-items: center; gap: 14px;
    background: rgba(255,255,255,0.035); border: 1px solid rgba(255,255,255,0.07);
    border-radius: 18px; padding: 14px 16px;
    backdrop-filter: blur(12px);
    transition: background 0.15s ease, border-color 0.15s ease, transform 0.12s ease;
    text-decoration: none; color: inherit;
  }
  .match-card:hover {
    background: rgba(255,255,255,0.065);
    border-color: rgba(255,255,255,0.13);
    transform: translateX(3px);
  }
  .spirit-circle-sm {
    width: 46px; height: 46px; flex-shrink: 0; border-radius: 50%;
    border: 1.5px solid; display: flex; align-items: center; justify-content: center;
  }
  .spirit-emoji-sm { font-size: 22px; }
  .match-center { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 4px; }
  .match-top-row { display: flex; align-items: center; justify-content: space-between; gap: 8px; }
  .match-type { font-size: 14px; font-weight: 800; }
  .match-badge { font-size: 11px; white-space: nowrap; color: rgba(240,240,248,0.45); }
  .match-reason { font-size: 11px; color: rgba(240,240,248,0.4); line-height: 1.45; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .resonance-bar-wrap { display: flex; align-items: center; gap: 8px; margin-top: 2px; }
  .resonance-bar-track { flex: 1; height: 2px; background: rgba(255,255,255,0.07); border-radius: 2px; overflow: hidden; }
  .resonance-bar-fill { height: 100%; border-radius: 2px; transition: width 0.7s cubic-bezier(0.16,1,0.3,1); }
  .resonance-val { font-size: 11px; color: rgba(240,240,248,0.35); flex-shrink: 0; min-width: 28px; text-align: right; }
  .match-arrow { color: rgba(240,240,248,0.22); font-size: 20px; flex-shrink: 0; font-weight: 300; }
</style>
