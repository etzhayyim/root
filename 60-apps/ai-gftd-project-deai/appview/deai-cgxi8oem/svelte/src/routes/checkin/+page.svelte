<script lang="ts">
  import { onMount } from "svelte";
  import { deaiApi } from "$lib/api";
  import { HUME_EMOTION_KEYS, SPIRIT_TYPE_META, type HumeEmotionScores, type SpiritType } from "$lib/spirit-types";

  let phase: "ready" | "capturing" | "complete" | "cooldown" = "ready";
  let spiritType: SpiritType | null = null;
  let spiritDelta = 0;
  let nextCheckinAfter = "";
  let loading = false;

  // Text input state
  let textInput = "";
  let showTextInput = false;

  const quickMoods = [
    { emoji: "😊", label: "嬉しい" },
    { emoji: "😔", label: "落ち込み" },
    { emoji: "😤", label: "熱意" },
    { emoji: "😌", label: "穏やか" },
    { emoji: "🤩", label: "興奮" },
  ];

  onMount(() => {
    spiritType = (localStorage.getItem("deai-spirit-type") as SpiritType) ?? null;
    const stored = localStorage.getItem("deai-next-checkin");
    if (stored && new Date(stored) > new Date()) {
      phase = "cooldown";
      nextCheckinAfter = stored;
    }
  });

  function mockHumeScores(): HumeEmotionScores {
    const rand = () => Math.round(Math.random() * 700 + 150);
    return { joy: rand(), sadness: rand(), anger: rand(), fear: rand(), disgust: rand(), calm: rand(), focus: rand(), surprise: rand(), confusion: rand(), awe: rand() };
  }

  async function doCheckin(modality: "face" | "voice" | "text") {
    const actorDid = localStorage.getItem("deai-cohort-did") ?? "did:web:decom.etzhayyim.ai:demo";
    showTextInput = false;
    phase = "capturing";
    loading = true;
    try {
      const humeScores = mockHumeScores();
      const res = await deaiApi.createCheckin({ humeScores, modality }, actorDid);
      spiritType = res.updatedSpiritType as SpiritType;
      spiritDelta = res.spiritDelta;
      nextCheckinAfter = res.nextCheckinAfter;
      localStorage.setItem("deai-next-checkin", nextCheckinAfter);
      localStorage.setItem("deai-spirit-type", spiritType);
      const prev = parseInt(localStorage.getItem("deai-checkin-count") ?? "0");
      localStorage.setItem("deai-checkin-count", String(prev + 1));
      phase = "complete";
    } catch {
      // Demo fallback
      spiritType = spiritType ?? "Hero";
      spiritDelta = Math.round(Math.random() * 200 - 60);
      nextCheckinAfter = new Date(Date.now() + 6 * 3600000).toISOString();
      localStorage.setItem("deai-next-checkin", nextCheckinAfter);
      phase = "complete";
    } finally { loading = false; }
  }

  function selectQuickMood(emoji: string, label: string) {
    textInput = `${emoji} ${label}の気持ち`;
    doCheckin("text");
  }

  function formatUntil(iso: string): string {
    const diff = new Date(iso).getTime() - Date.now();
    const h = Math.floor(diff / 3600000);
    const m = Math.floor((diff % 3600000) / 60000);
    return `${h}時間${m}分後`;
  }
</script>

<svelte:head><title>今日のチェックイン — deai</title></svelte:head>

<div class="checkin-page">
  <div class="page-head">
    <h1 class="title">今日の Spirit</h1>
    <p class="subtitle">感情状態を記録して、共鳴精度を高める</p>
  </div>

  {#if phase === "cooldown"}
    <div class="cooldown-panel">
      <div class="cooldown-orb">⏳</div>
      <p class="cool-label">次のチェックインまで</p>
      <p class="cool-time">{formatUntil(nextCheckinAfter)}</p>
      <p class="cool-desc">Spirit は時間をかけて安定します</p>
      <div class="cool-divider"></div>
      <a href="/matches" class="see-matches-btn">マッチを確認する →</a>
    </div>

  {:else if phase === "ready"}
    {#if spiritType}
      {@const meta = SPIRIT_TYPE_META[spiritType]}
      <div class="current-type" style="border-color: {meta.color}33; background: {meta.color}0d">
        <span class="type-emoji">{meta.emoji}</span>
        <div>
          <span class="type-label" style="color: {meta.color}">{meta.ja}</span>
          <span class="type-sub">現在の Spirit Type</span>
        </div>
      </div>
    {/if}

    <div class="modality-grid">
      <button class="modality-btn" on:click={() => doCheckin("face")} disabled={loading}>
        <span class="mod-icon">📷</span>
        <div class="mod-text">
          <span class="mod-name">顔で計測</span>
          <span class="mod-desc">カメラで感情を読み取る</span>
        </div>
        <span class="mod-arrow">›</span>
      </button>

      <button class="modality-btn" on:click={() => doCheckin("voice")} disabled={loading}>
        <span class="mod-icon">🎙️</span>
        <div class="mod-text">
          <span class="mod-name">声で計測</span>
          <span class="mod-desc">3秒間話しかける</span>
        </div>
        <span class="mod-arrow">›</span>
      </button>

      <button class="modality-btn" on:click={() => showTextInput = !showTextInput} disabled={loading} class:expanded={showTextInput}>
        <span class="mod-icon">✍️</span>
        <div class="mod-text">
          <span class="mod-name">気分を入力</span>
          <span class="mod-desc">今の感覚を言葉で</span>
        </div>
        <span class="mod-arrow" class:rotated={showTextInput}>›</span>
      </button>
    </div>

    {#if showTextInput}
      <div class="text-input-area">
        <p class="quick-label">クイック気分</p>
        <div class="quick-moods">
          {#each quickMoods as m}
            <button class="quick-btn" on:click={() => selectQuickMood(m.emoji, m.label)}>
              <span class="quick-emoji">{m.emoji}</span>
              <span class="quick-name">{m.label}</span>
            </button>
          {/each}
        </div>
        <textarea
          bind:value={textInput}
          placeholder="今感じていることを自由に..."
          class="text-area"
          rows="3"
        ></textarea>
        <button class="submit-btn" on:click={() => doCheckin("text")} disabled={!textInput.trim()}>
          記録する ✨
        </button>
      </div>
    {/if}

    <div class="privacy-note">
      <span class="privacy-icon">🔒</span>
      <p>カメラ・音声データは端末の Hume AI で処理後、スコアのみ送信。画像・音声は外部に送信されません。</p>
    </div>

  {:else if phase === "capturing"}
    <div class="capturing-panel">
      <div class="spirit-orb">
        <div class="orb-ring r1"></div>
        <div class="orb-ring r2"></div>
        <div class="orb-ring r3"></div>
        <span class="orb-emoji">🔮</span>
      </div>
      <p class="capturing-text">Spirit エネルギーを読み取っています...</p>
      <p class="capturing-sub">感情の熱力学的情報量を計算中</p>
    </div>

  {:else if phase === "complete" && spiritType}
    {@const meta = SPIRIT_TYPE_META[spiritType]}
    <div class="complete-panel">
      <div class="complete-emoji-wrap">
        <span class="complete-emoji">{meta.emoji}</span>
        <div class="complete-glow" style="background: radial-gradient(circle, {meta.color}33, transparent 70%)"></div>
      </div>
      <h2>{meta.ja}</h2>
      <p class="complete-type-en">{spiritType} — Spirit Type</p>
      <div class="delta-display" class:positive={spiritDelta >= 0} class:negative={spiritDelta < 0}>
        <span class="delta-val">{spiritDelta >= 0 ? "+" : ""}{spiritDelta}</span>
        <span class="delta-label">U_spirit 変化</span>
      </div>
      <p class="complete-msg">
        {spiritDelta > 100 ? "今日の Spirit エネルギーは高まっています ✨" :
         spiritDelta < -100 ? "今日は内省の時間が必要かもしれません 🌙" :
         "Spirit は安定しています 🌱"}
      </p>
      <a href="/matches" class="see-matches-btn">今日のマッチを見る →</a>
    </div>
  {/if}
</div>

<style>
  .checkin-page { padding: 28px 18px 24px; max-width: 400px; margin: 0 auto; display: flex; flex-direction: column; gap: 22px; }

  .page-head { display: flex; flex-direction: column; gap: 6px; }
  .title { font-size: 26px; font-weight: 800; letter-spacing: -0.03em; }
  .subtitle { font-size: 13px; color: rgba(240,240,248,0.5); }

  /* Current type */
  .current-type {
    display: flex; align-items: center; gap: 12px;
    padding: 14px 18px; border-radius: 16px; border: 1px solid;
    backdrop-filter: blur(12px);
  }
  .type-emoji { font-size: 32px; }
  .type-label { display: block; font-size: 16px; font-weight: 700; }
  .type-sub { font-size: 11px; color: rgba(240,240,248,0.4); display: block; margin-top: 2px; }

  /* Modality buttons */
  .modality-grid { display: flex; flex-direction: column; gap: 10px; }
  .modality-btn {
    display: flex; align-items: center; gap: 14px;
    padding: 18px; border: 1px solid rgba(255,255,255,0.09);
    border-radius: 18px; background: rgba(255,255,255,0.04);
    text-align: left; cursor: pointer;
    transition: background 0.15s, border-color 0.15s, transform 0.12s;
    backdrop-filter: blur(12px);
  }
  .modality-btn:hover { background: rgba(192,132,252,0.08); border-color: rgba(192,132,252,0.28); transform: translateY(-1px); }
  .modality-btn:active { transform: translateY(0); }
  .modality-btn:disabled { opacity: 0.45; cursor: wait; transform: none; }
  .modality-btn.expanded { border-color: rgba(192,132,252,0.35); background: rgba(192,132,252,0.07); }
  .mod-icon { font-size: 36px; flex-shrink: 0; }
  .mod-text { flex: 1; }
  .mod-name { display: block; font-size: 15px; font-weight: 700; color: #f0f0f8; margin-bottom: 3px; }
  .mod-desc { font-size: 12px; color: rgba(240,240,248,0.45); }
  .mod-arrow {
    font-size: 22px; color: rgba(240,240,248,0.25);
    transition: transform 0.2s ease, color 0.2s;
  }
  .mod-arrow.rotated { transform: rotate(90deg); color: #c084fc; }

  /* Text input area */
  .text-input-area {
    background: rgba(255,255,255,0.03); border: 1px solid rgba(192,132,252,0.2);
    border-radius: 16px; padding: 18px; display: flex; flex-direction: column; gap: 14px;
    animation: slideDown 0.2s ease;
  }
  @keyframes slideDown { from { opacity: 0; transform: translateY(-8px); } to { opacity: 1; transform: translateY(0); } }
  .quick-label { font-size: 11px; color: rgba(240,240,248,0.4); letter-spacing: 0.05em; text-transform: uppercase; }
  .quick-moods { display: flex; gap: 8px; }
  .quick-btn {
    flex: 1; display: flex; flex-direction: column; align-items: center; gap: 4px;
    padding: 10px 6px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.09);
    background: rgba(255,255,255,0.04); cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
  }
  .quick-btn:hover { background: rgba(192,132,252,0.1); border-color: rgba(192,132,252,0.3); }
  .quick-emoji { font-size: 22px; }
  .quick-name { font-size: 10px; color: rgba(240,240,248,0.5); white-space: nowrap; }
  .text-area {
    width: 100%; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 12px; padding: 12px 14px; color: #f0f0f8; font-size: 14px;
    font-family: inherit; resize: none; line-height: 1.55;
    transition: border-color 0.15s;
  }
  .text-area:focus { outline: none; border-color: rgba(192,132,252,0.4); }
  .text-area::placeholder { color: rgba(240,240,248,0.3); }
  .submit-btn {
    width: 100%; padding: 14px; border: none; border-radius: 12px;
    background: linear-gradient(135deg, #c084fc, #818cf8);
    color: #fff; font-size: 15px; font-weight: 700; cursor: pointer;
    transition: opacity 0.15s, transform 0.12s;
    box-shadow: 0 4px 16px rgba(192,132,252,0.3);
  }
  .submit-btn:hover { opacity: 0.9; transform: translateY(-1px); }
  .submit-btn:disabled { opacity: 0.4; cursor: default; transform: none; }

  /* Privacy */
  .privacy-note {
    display: flex; gap: 10px; align-items: flex-start;
    padding: 12px 14px; background: rgba(251,191,36,0.04); border: 1px solid rgba(251,191,36,0.12); border-radius: 12px;
  }
  .privacy-icon { font-size: 16px; flex-shrink: 0; margin-top: 1px; }
  .privacy-note p { font-size: 11px; color: rgba(251,191,36,0.65); line-height: 1.5; }

  /* Cooldown */
  .cooldown-panel { text-align: center; padding: 24px 0; display: flex; flex-direction: column; align-items: center; gap: 12px; }
  .cooldown-orb { font-size: 56px; filter: drop-shadow(0 0 16px rgba(192,132,252,0.4)); }
  .cool-label { font-size: 13px; color: rgba(240,240,248,0.5); }
  .cool-time { font-size: 32px; font-weight: 900; color: #c084fc; letter-spacing: -0.03em; }
  .cool-desc { font-size: 12px; color: rgba(240,240,248,0.35); }
  .cool-divider { width: 60px; height: 1px; background: rgba(255,255,255,0.08); }

  /* Capturing */
  .capturing-panel { text-align: center; padding: 32px 0; display: flex; flex-direction: column; align-items: center; gap: 16px; }
  .spirit-orb { position: relative; width: 120px; height: 120px; display: flex; align-items: center; justify-content: center; }
  .orb-ring {
    position: absolute; border-radius: 50%; border: 2px solid rgba(192,132,252,0.3);
    animation: orbPulse 2s ease-in-out infinite;
  }
  .r1 { width: 60px; height: 60px; animation-delay: 0s; }
  .r2 { width: 90px; height: 90px; animation-delay: 0.4s; border-color: rgba(192,132,252,0.18); }
  .r3 { width: 118px; height: 118px; animation-delay: 0.8s; border-color: rgba(192,132,252,0.09); }
  @keyframes orbPulse { 0%,100% { transform: scale(1); opacity: 0.9; } 50% { transform: scale(1.08); opacity: 0.3; } }
  .orb-emoji { font-size: 36px; position: relative; z-index: 1; }
  .capturing-text { font-size: 15px; font-weight: 600; color: rgba(240,240,248,0.8); }
  .capturing-sub { font-size: 12px; color: rgba(240,240,248,0.35); }

  /* Complete */
  .complete-panel { text-align: center; display: flex; flex-direction: column; align-items: center; gap: 14px; }
  .complete-emoji-wrap { position: relative; width: 100px; height: 100px; display: flex; align-items: center; justify-content: center; }
  .complete-emoji { font-size: 72px; position: relative; z-index: 1; filter: drop-shadow(0 0 12px rgba(192,132,252,0.4)); }
  .complete-glow { position: absolute; inset: -10px; border-radius: 50%; }
  h2 { font-size: 30px; font-weight: 900; letter-spacing: -0.03em; }
  .complete-type-en { font-size: 12px; color: rgba(240,240,248,0.35); letter-spacing: 0.06em; }
  .delta-display { display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 14px 28px; border-radius: 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); }
  .delta-val { font-size: 36px; font-weight: 900; color: rgba(240,240,248,0.4); }
  .delta-display.positive .delta-val { color: #4ade80; }
  .delta-display.negative .delta-val { color: #f87171; }
  .delta-label { font-size: 11px; color: rgba(240,240,248,0.35); }
  .complete-msg { font-size: 14px; color: rgba(240,240,248,0.6); line-height: 1.5; }
  .see-matches-btn {
    display: inline-block; padding: 15px 32px;
    background: linear-gradient(135deg, #c084fc, #818cf8); color: #fff;
    font-size: 15px; font-weight: 700; border-radius: 14px;
    box-shadow: 0 4px 20px rgba(192,132,252,0.35);
    transition: opacity 0.15s, transform 0.12s;
  }
  .see-matches-btn:hover { opacity: 0.9; transform: translateY(-1px); }
</style>
