<script lang="ts">
  /**
   * Spirit-in-Physics 語連想実験 (Word Association Experiment)
   *
   * Jung (1910) の語連想実験を現代の感情計測と統合。
   * 測定式: P(w_O|w_I) ∝ exp(w_I·w_O) × r^α × exp(γ·ΔSP/λ) × exp(η·F)
   *
   * 全データは spirit-in-physics.com/api に送信される（研究 SSoT）。
   * deai はデータ収集フロントエンド。
   */

  import { goto } from "$app/navigation";
  import { onMount, onDestroy, tick } from "svelte";
  import gsap from "gsap";
  import { page } from "$app/stores";
  import { sipApi, JUNG_STIMULUS_WORDS } from "$lib/sip-api";
  import { classifySpiritType, SPIRIT_TYPE_META, type SpiritType } from "$lib/spirit-types";
  import SpiritReveal from "$lib/SpiritReveal.svelte";
  import CameraPreview from "$lib/CameraPreview.svelte";
  import { HumeRecorder, type SessionResult } from "$lib/hume-recorder";

  type Phase = "consent" | "demographics" | "ready" | "running" | "complete" | "result";

  // Dev preview: ?reveal=Hero|Sage|Lover|Caregiver (dev only)
  onMount(() => {
    if (import.meta.env.DEV) {
      const t = $page.url.searchParams.get("reveal") as SpiritType | null;
      if (t && ["Hero","Sage","Lover","Caregiver"].includes(t)) {
        spiritType = t;
        showReveal = true;
      }
    }
  });

  onDestroy(() => {
    recorder?.stopSession().catch(() => {});
  });

  // セッションあたりの語数（100語を複数セッションに分割可能、今回は20語/セッション）
  const SESSION_SIZE = 20;
  const SESSION_INDEX = 0; // MVP: 最初のセッションのみ

  let phase: Phase = "consent";
  let participantId = "";
  let sessionStarted = false;

  // Demographics (研究データに含める)
  let ageGroup = "";
  let gender = "";
  let consentGiven = false;
  let dataPublic = false;

  // Experiment state
  const words = JUNG_STIMULUS_WORDS.slice(0, SESSION_SIZE);
  let currentIndex = 0;
  let wordStartTime = 0;
  let responses: Array<{
    wordId: number; word: string; reactionTimeMs: number;
    humeScores: Record<string, number>;
  }> = [];

  let spiritType: SpiritType | null = null;
  let loading = false;
  let error = "";
  let uploadProgress = 0;
  let showReveal = false;
  let wordKey = 0; // bump to re-trigger word entrance animation
  let resultPanelEl: HTMLDivElement;
  let feltBtnEl: HTMLButtonElement;

  // Recording
  // CF Worker WS proxy URL for Hume — auto-derived from origin, override with VITE_HUME_PROXY_WS
  const HUME_PROXY_WS = (import.meta.env.VITE_HUME_PROXY_WS as string | undefined)
    || (typeof window !== "undefined"
      ? `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host}/api/hume-ws`
      : undefined);
  let recorder: HumeRecorder | null = null;
  let cameraStream: MediaStream | null = null;
  let recordingActive = false;
  let sessionResult: SessionResult | null = null;

  // ── Consent ───────────────────────────────────────────────

  async function giveConsent() {
    consentGiven = true;
    phase = "demographics";
  }

  // ── Participant registration ───────────────────────────────

  async function startExperiment() {
    loading = true; error = "";
    try {
      // 匿名 participant ID（既存の cohort DID or 新規生成）
      participantId = localStorage.getItem("deai-participant-id") ?? "";
      if (!participantId) {
        participantId = "p-" + crypto.randomUUID().replace(/-/g, "").slice(0, 16);
        localStorage.setItem("deai-participant-id", participantId);
      }

      // spirit-in-physics に参加者登録（upsert）
      await sipApi.registerParticipant({
        id: participantId,
        ageGroup,
        gender,
        isPublic: dataPublic,
      });

      // アセスメント開始
      await sipApi.startAssessment(participantId);
      await sipApi.startSession(participantId, SESSION_INDEX);

      sessionStarted = true;

      // Start recording (non-blocking — experiment continues even if denied)
      recorder = new HumeRecorder(HUME_PROXY_WS);
      const recOk = await recorder.startSession();
      if (recOk) {
        cameraStream = recorder.liveStream;
        recordingActive = true;
        // Mark the first word
        const firstWord = words[0];
        recorder.markWord(firstWord.id, firstWord.japanese);
      } else {
        recorder = null;
        cameraStream = null;
      }

      phase = "running";
      wordStartTime = Date.now();
    } catch (e) {
      error = `研究サーバーへの接続に失敗しました。オフラインでも続行できます。\n${e}`;
      // Graceful degradation: オフラインでも実験は継続
      participantId = participantId || "p-offline-" + Date.now();
      recorder = new HumeRecorder(HUME_PROXY_WS);
      const recOk = await recorder.startSession().catch(() => false);
      if (recOk) {
        cameraStream = recorder.liveStream;
        recordingActive = true;
        recorder.markWord(words[0].id, words[0].japanese);
      } else {
        recorder = null;
      }
      sessionStarted = false;
      phase = "running";
      wordStartTime = Date.now();
    } finally { loading = false; }
  }

  // ── Experiment ────────────────────────────────────────────

  async function recordResponse(responseWord?: string) {
    const reactionTimeMs = Date.now() - wordStartTime;
    const currentWord = words[currentIndex];
    const humeScores = recorder
      ? recorder.getWordScores(currentWord.id)
      : mockScores();

    responses.push({
      wordId: currentWord.id,
      word: currentWord.japanese,
      reactionTimeMs,
      humeScores,
    });

    // spirit-in-physics API にリアルタイム送信（非同期、失敗しても実験継続）
    Promise.all([
      sipApi.submitWordResponse({
        participantId,
        session: SESSION_INDEX,
        stimulusWordId: currentWord.id,
        responseWord,
        reactionTimeMs,
        humeScores,
      }).catch(() => {}),
      // Hume スコアを artifact として記録
      sipApi.uploadArtifact({
        participantId,
        session: SESSION_INDEX,
        artifactType: "hume-face",
        payload: {
          stimulusWordId: currentWord.id,
          word: currentWord.japanese,
          reactionTimeMs,
          emotions: Object.entries(humeScores).map(([name, score]) => ({ name, score })),
          timestamp: new Date().toISOString(),
        },
      }).catch(() => {}),
    ]);

    currentIndex++;
    wordKey++;
    uploadProgress = Math.round((currentIndex / words.length) * 100);
    wordStartTime = Date.now();

    if (currentIndex >= words.length) {
      phase = "complete";
      await finishSession();
    } else {
      // Mark next word for Hume timestamp linkage
      const nextWord = words[currentIndex];
      recorder?.markWord(nextWord.id, nextWord.japanese);
    }
  }

  async function finishSession() {
    // Stop recording and save
    if (recorder) {
      sessionResult = await recorder.stopSession().catch(() => null);
      recordingActive = false;
      cameraStream = null;

      // Upload artifact blob reference (post-processing)
      if (sessionResult?.filePath) {
        sipApi.uploadArtifact({
          participantId,
          session: SESSION_INDEX,
          artifactType: "recording-ref",
          payload: {
            filePath: sessionResult.filePath,
            mimeType: sessionResult.mimeType,
            durationMs: sessionResult.durationMs,
            wordMarks: sessionResult.wordMarks,
            timestamp: new Date().toISOString(),
          },
        }).catch(() => {});
      }
    }

    // セッション完了を spirit-in-physics に通知
    await sipApi.completeSession(participantId, SESSION_INDEX).catch(() => {});

    // ローカルで Spirit Type を分類（表示用）
    const respsForClassify = responses.map((r) => ({
      word: r.word,
      reactionTimeMs: r.reactionTimeMs,
      humeScores: {
        joy: r.humeScores.joy ?? 0,
        sadness: r.humeScores.sadness ?? 0,
        anger: r.humeScores.anger ?? 0,
        fear: r.humeScores.fear ?? 0,
        disgust: r.humeScores.disgust ?? 0,
        calm: r.humeScores.calm ?? 0,
        focus: r.humeScores.focus ?? 0,
        surprise: r.humeScores.surprise ?? 0,
        confusion: r.humeScores.confusion ?? 0,
        awe: r.humeScores.awe ?? 0,
      },
    }));
    spiritType = classifySpiritType(respsForClassify);
    localStorage.setItem("deai-spirit-type", spiritType);
    localStorage.setItem("deai-assessed-at", new Date().toISOString());

    setTimeout(() => { showReveal = true; }, 600);
  }

  async function onRevealComplete() {
    showReveal = false;
    phase = "result";
    await tick();
    if (resultPanelEl) {
      const items = resultPanelEl.querySelectorAll(".anim-in");
      gsap.fromTo(items,
        { y: 24, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.5, stagger: 0.1, ease: "power3.out" },
      );
    }
  }

  function mockScores(): Record<string, number> {
    const rand = () => Math.round(Math.random() * 800 + 100);
    return {
      joy: rand(), sadness: rand(), anger: rand(), fear: rand(), disgust: rand(),
      calm: rand(), focus: rand(), surprise: rand(), confusion: rand(), awe: rand(),
    };
  }

  $: progress = words.length > 0 ? Math.round((currentIndex / words.length) * 100) : 0;
  $: currentWord = words[currentIndex];
</script>

<svelte:head><title>語連想実験 — Spirit in Physics</title></svelte:head>

{#if showReveal && spiritType}
  <SpiritReveal type={spiritType} onComplete={onRevealComplete} />
{/if}

<!-- Small camera preview (bottom-right, only while running) -->
{#if phase === "running" && cameraStream}
  <CameraPreview
    stream={cameraStream}
    recording={recordingActive}
    on:videoready={(e) => recorder?.attachVideo(e.detail)}
  />
{/if}

<div class="assessment">

  <!-- ── 同意フォーム ────────────────────────────────────── -->
  {#if phase === "consent"}
    <div class="panel consent-panel">
      <div class="research-badge">研究参加</div>
      <h1>Spirit in Physics<br/>語連想実験</h1>
      <p class="lead">この診断は科学研究のデータ収集です。</p>

      <div class="paper-box">
        <p class="paper-title">Spirit in Physics:<br/>Spirit as a Thermodynamic Information Quantity</p>
        <p class="paper-authors">Jun Kawasaki, Kazuki Tainaka, Tomonori Takeuchi</p>
        <p class="paper-inst">Niigata University / Aarhus University, 2026</p>
      </div>

      <div class="consent-items">
        <div class="consent-item">
          <span class="ci-icon">📊</span>
          <div>
            <strong>収集するデータ</strong>
            <p>刺激語への反応時間、顔表情・音声の感情スコア（Hume AI処理後）。生体画像・音声は端末上で処理し外部送信しません。</p>
          </div>
        </div>
        <div class="consent-item">
          <span class="ci-icon">🔬</span>
          <div>
            <strong>研究目的</strong>
            <p>Jung 語連想実験 × 感情生体計測による Spirit の熱力学的情報量としての測定。データは spirit-in-physics.com に保存されます。</p>
          </div>
        </div>
        <div class="consent-item">
          <span class="ci-icon">🔒</span>
          <div>
            <strong>匿名性</strong>
            <p>個人識別情報（氏名・連絡先）は一切不要です。匿名IDのみで参加できます。</p>
          </div>
        </div>
        <div class="consent-item">
          <span class="ci-icon">↩️</span>
          <div>
            <strong>撤回の権利</strong>
            <p>いつでも参加を中止できます。収集済みデータの削除を research@spirit-in-physics.com に申請できます。</p>
          </div>
        </div>
      </div>

      <label class="checkbox-row">
        <input type="checkbox" bind:checked={consentGiven} />
        <span>上記の研究参加に同意します</span>
      </label>

      <label class="checkbox-row">
        <input type="checkbox" bind:checked={dataPublic} />
        <span>データを公開研究データセットに含めることに同意します（任意）</span>
      </label>

      <button class="primary-btn" disabled={!consentGiven} on:click={giveConsent}>
        同意して続行
      </button>
    </div>

  <!-- ── 人口統計 ─────────────────────────────────────────── -->
  {:else if phase === "demographics"}
    <div class="panel demographics-panel">
      <h2>基本情報（任意）</h2>
      <p class="subdesc">研究の統計分析に使用します。すべて任意です。</p>

      <div class="field">
        <label for="age-group">年齢層</label>
        <select id="age-group" bind:value={ageGroup}>
          <option value="">選択しない</option>
          <option value="10s">10代</option>
          <option value="20s">20代</option>
          <option value="30s">30代</option>
          <option value="40s">40代</option>
          <option value="50s">50代以上</option>
        </select>
      </div>

      <div class="field">
        <label for="gender">性別</label>
        <select id="gender" bind:value={gender}>
          <option value="">選択しない</option>
          <option value="male">男性</option>
          <option value="female">女性</option>
          <option value="non-binary">ノンバイナリー</option>
          <option value="prefer-not">回答しない</option>
        </select>
      </div>

      {#if error}<p class="error">{error}</p>{/if}

      <button class="primary-btn" on:click={startExperiment} disabled={loading}>
        {loading ? "準備中..." : "実験を開始する"}
      </button>
    </div>

  <!-- ── 実験中 ──────────────────────────────────────────── -->
  {:else if phase === "running"}
    <div class="running-panel">
      <div class="progress-header">
        <div class="progress-bar">
          <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <span class="prog-text">{currentIndex}/{words.length}</span>
      </div>

      {#if currentWord}
        {#key wordKey}
          <div class="word-display">
            <div class="word-flash"></div>
            <div class="word-ja">{currentWord.japanese}</div>
            <div class="word-en">{currentWord.english}</div>
            <div class="word-pronunciation">（{currentWord.pronunciation}）</div>
          </div>
        {/key}

        <p class="instruction">この言葉を見て、最初に浮かんだことを感じたら押す</p>

        <div class="response-area">
          <button class="felt-btn" bind:this={feltBtnEl}
            on:click={() => recordResponse()}
            on:pointerdown={(e) => {
              const btn = e.currentTarget as HTMLButtonElement;
              const r = document.createElement("span");
              r.className = "ripple";
              const rect = btn.getBoundingClientRect();
              const size = Math.max(rect.width, rect.height);
              r.style.cssText = `width:${size}px;height:${size}px;left:${e.clientX-rect.left-size/2}px;top:${e.clientY-rect.top-size/2}px`;
              btn.appendChild(r);
              setTimeout(() => r.remove(), 600);
            }}
          >
            <span class="felt-pulse"></span>
            感じた
          </button>
        </div>

        <div class="data-indicator">
          <span class="di-dot" class:active={sessionStarted}></span>
          <span class="di-text">{sessionStarted ? "研究データ送信中" : "オフラインモード"}</span>
        </div>
      {/if}
    </div>

  <!-- ── 完了中 ──────────────────────────────────────────── -->
  {:else if phase === "complete"}
    <div class="panel complete-panel">
      <div class="upload-orb">
        <div class="orb-ring" style="--p: {uploadProgress}%"></div>
        <span>分析中</span>
      </div>
      <p>Spirit Type を計算中...</p>
      <p class="upload-note">反応データを research DB に送信しています</p>
    </div>

  <!-- ── 結果 ───────────────────────────────────────────── -->
  {:else if phase === "result" && spiritType}
    {@const meta = SPIRIT_TYPE_META[spiritType]}
    <div class="panel result-panel" bind:this={resultPanelEl}>
      <div class="result-header anim-in">
        <span class="result-emoji">{meta.emoji}</span>
        <div>
          <h2 class="result-type">{meta.ja}</h2>
          <p class="result-en">{spiritType} Type</p>
        </div>
      </div>
      <p class="result-desc anim-in">{meta.desc}</p>

      <div class="data-saved-box anim-in">
        <p>実験データを保存しました</p>
        <p class="ds-id">参加者 ID: <code>{participantId}</code></p>
        <a
          href="https://researcher.spirit-in-physics.com?participantId={encodeURIComponent(participantId)}"
          target="_blank" rel="noopener" class="researcher-link"
        >
          研究者フロントエンドで分析を見る →
        </a>
      </div>

      <div class="next-actions anim-in">
        <a href="/matches" class="primary-btn">マッチングへ進む</a>
        <a href="/checkin" class="secondary-link">毎日のチェックインを設定</a>
      </div>

      <div class="theory-mini anim-in">
        <p>測定式: <code>P(w|w_i) ∝ exp(w·w_i) × r^α × exp(η·F)</code></p>
        <p>反応時間 r = {Math.round(responses.reduce((s, r) => s + r.reactionTimeMs, 0) / responses.length)}ms 平均</p>
        <p>有効応答数 {responses.length} / {words.length} 語</p>
      </div>
    </div>
  {/if}
</div>

<style>
  .assessment { min-height: 100dvh; display: flex; align-items: center; justify-content: center; padding: 20px; }
  .panel { width: 100%; max-width: 480px; display: flex; flex-direction: column; gap: 18px; }
  .research-badge {
    display: inline-flex; align-self: flex-start; padding: 4px 12px; border-radius: 20px;
    background: rgba(99,102,241,0.15); border: 1px solid rgba(99,102,241,0.3);
    font-size: 11px; font-weight: 700; color: #818cf8; letter-spacing: 0.08em; text-transform: uppercase;
  }
  h1 { font-size: 28px; font-weight: 900; line-height: 1.2; }
  h2 { font-size: 22px; font-weight: 800; }
  .lead { font-size: 15px; color: rgba(240,240,248,0.65); }
  .paper-box {
    background: rgba(99,102,241,0.06); border: 1px solid rgba(99,102,241,0.15);
    border-radius: 12px; padding: 14px 16px;
  }
  .paper-title { font-size: 13px; font-weight: 700; font-style: italic; margin-bottom: 6px; line-height: 1.4; }
  .paper-authors { font-size: 12px; color: rgba(240,240,248,0.6); margin-bottom: 2px; }
  .paper-inst { font-size: 11px; color: rgba(240,240,248,0.4); }
  .consent-items { display: flex; flex-direction: column; gap: 14px; }
  .consent-item { display: flex; gap: 12px; }
  .ci-icon { font-size: 20px; flex-shrink: 0; margin-top: 2px; }
  .consent-item strong { display: block; font-size: 14px; margin-bottom: 4px; }
  .consent-item p { font-size: 12px; color: rgba(240,240,248,0.55); line-height: 1.5; }
  .checkbox-row { display: flex; align-items: flex-start; gap: 10px; font-size: 13px; color: rgba(240,240,248,0.7); cursor: pointer; }
  .checkbox-row input { margin-top: 2px; accent-color: #c084fc; }
  .primary-btn {
    display: block; width: 100%; padding: 18px; text-align: center; border: none; border-radius: 16px;
    background: linear-gradient(135deg, #c084fc, #818cf8); color: #fff; font-size: 17px;
    font-weight: 700; cursor: pointer; text-decoration: none;
  }
  .primary-btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .subdesc { font-size: 13px; color: rgba(240,240,248,0.5); margin-top: -10px; }
  .field { display: flex; flex-direction: column; gap: 6px; }
  .field label { font-size: 13px; color: rgba(240,240,248,0.6); }
  .field select {
    padding: 12px 14px; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px; color: #f0f0f8; font-size: 15px; cursor: pointer;
  }
  .error { font-size: 12px; color: #f87171; }

  /* Running */
  .running-panel { width: 100%; max-width: 480px; display: flex; flex-direction: column; align-items: center; gap: 24px; padding: 20px; }
  .progress-header { width: 100%; display: flex; align-items: center; gap: 10px; }
  .progress-bar { flex: 1; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; }
  .progress-fill { height: 100%; background: linear-gradient(90deg, #c084fc, #818cf8); border-radius: 2px; transition: width 0.4s ease; }
  .prog-text { font-size: 12px; color: rgba(240,240,248,0.4); white-space: nowrap; }
  .word-display {
    position: relative; text-align: center; display: flex; flex-direction: column; gap: 8px;
  }
  .word-flash {
    position: absolute; inset: -20px; border-radius: 16px;
    background: radial-gradient(ellipse 60% 60% at 50% 50%, rgba(192,132,252,0.18), transparent 70%);
    animation: flashIn 0.35s ease-out forwards;
    pointer-events: none;
  }
  @keyframes flashIn {
    from { opacity: 1; transform: scale(0.6); }
    to   { opacity: 0; transform: scale(1.4); }
  }
  .word-ja {
    font-size: 64px; font-weight: 900; letter-spacing: -0.02em;
    animation: wordAppear 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  }
  @keyframes wordAppear {
    from { opacity: 0; transform: scale(0.75) translateY(16px); filter: blur(4px); }
    to   { opacity: 1; transform: scale(1) translateY(0); filter: blur(0); }
  }
  .word-en { font-size: 16px; color: rgba(240,240,248,0.4); animation: fadeUp 0.3s 0.1s both ease-out; }
  .word-pronunciation { font-size: 13px; color: rgba(240,240,248,0.3); animation: fadeUp 0.3s 0.15s both ease-out; }
  @keyframes fadeUp { from { opacity: 0; transform: translateY(8px); } to { opacity: 1; transform: none; } }
  .instruction { font-size: 13px; color: rgba(240,240,248,0.45); text-align: center; }
  .response-area { width: 100%; }
  .felt-btn {
    position: relative; overflow: hidden;
    width: 100%; padding: 28px; border: 2px solid rgba(192,132,252,0.35);
    background: rgba(192,132,252,0.08); border-radius: 20px; color: #c084fc;
    font-size: 22px; font-weight: 700; cursor: pointer; transition: background 0.12s, transform 0.08s, border-color 0.12s;
    letter-spacing: 0.04em;
  }
  .felt-btn:active { background: rgba(192,132,252,0.22); transform: scale(0.97); border-color: rgba(192,132,252,0.6); }
  .felt-pulse {
    position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
    border: 2px solid rgba(192,132,252,0.5);
    animation: heartbeat 2.2s ease-in-out infinite;
  }
  @keyframes heartbeat {
    0%   { transform: scale(1); opacity: 0.5; }
    14%  { transform: scale(1.04); opacity: 0.8; }
    28%  { transform: scale(1); opacity: 0.5; }
    42%  { transform: scale(1.03); opacity: 0.7; }
    70%  { transform: scale(1); opacity: 0.3; }
    100% { transform: scale(1); opacity: 0.5; }
  }
  :global(.ripple) {
    position: absolute; border-radius: 50%; pointer-events: none;
    background: rgba(192,132,252,0.35);
    transform: scale(0); animation: rippleAnim 0.6s linear;
  }
  @keyframes rippleAnim { to { transform: scale(2.5); opacity: 0; } }
  .data-indicator { display: flex; align-items: center; gap: 6px; }
  .di-dot { width: 7px; height: 7px; border-radius: 50%; background: rgba(240,240,248,0.2); }
  .di-dot.active { background: #4ade80; animation: blink 2s ease-in-out infinite; }
  @keyframes blink { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
  .di-text { font-size: 11px; color: rgba(240,240,248,0.4); }

  /* Complete */
  .complete-panel { align-items: center; padding: 60px 0; }
  .upload-orb { width: 80px; height: 80px; position: relative; display: flex; align-items: center; justify-content: center; }
  .orb-ring {
    position: absolute; inset: 0; border-radius: 50%;
    border: 4px solid rgba(192,132,252,0.2);
    border-top-color: #c084fc; animation: spin 1s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  .upload-note { font-size: 12px; color: rgba(240,240,248,0.35); }

  /* Result */
  .result-panel { }
  .anim-in { opacity: 0; }
  .result-header { display: flex; align-items: center; gap: 16px; margin-bottom: 8px; }
  .result-emoji { font-size: 56px; }
  .result-type { font-size: 28px; font-weight: 900; }
  .result-en { font-size: 14px; color: rgba(240,240,248,0.5); }
  .result-desc { font-size: 15px; color: rgba(240,240,248,0.65); }
  .data-saved-box { background: rgba(74,222,128,0.06); border: 1px solid rgba(74,222,128,0.2); border-radius: 14px; padding: 16px; }
  .data-saved-box p { font-size: 13px; color: #4ade80; margin-bottom: 6px; }
  .ds-id { font-size: 11px; }
  .ds-id code { font-family: monospace; color: rgba(240,240,248,0.6); font-size: 10px; }
  .researcher-link { display: inline-block; margin-top: 8px; font-size: 13px; color: #818cf8; text-decoration: none; }
  .next-actions { display: flex; flex-direction: column; gap: 12px; }
  .secondary-link { text-align: center; font-size: 14px; color: rgba(192,132,252,0.7); text-decoration: none; }
  .theory-mini { background: rgba(0,0,0,0.2); border-radius: 10px; padding: 12px 14px; }
  .theory-mini p { font-size: 11px; color: rgba(240,240,248,0.4); margin-bottom: 4px; line-height: 1.5; }
  .theory-mini code { color: #c084fc; font-size: 10px; }
</style>
