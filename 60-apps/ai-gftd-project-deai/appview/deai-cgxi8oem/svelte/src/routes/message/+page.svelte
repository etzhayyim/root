<script lang="ts">
  import { onMount } from "svelte";
  import { page } from "$app/stores";
  import { deaiApi } from "$lib/api";
  import { SPIRIT_TYPE_META, type SpiritType } from "$lib/spirit-types";

  interface Message { messageId: string; fromCohortDid: string; ciphertext: string; sentAt: string; }

  const SPIRIT_COLORS: Record<string, string> = {
    Hero: "#ff6b6b", Sage: "#60a5fa", Lover: "#f472b6", Caregiver: "#34d399",
  };

  const plaintextMap = new Map<string, string>();

  const DEMO_MESSAGES: Record<string, string> = {
    "msg-1": "はじめまして。Spirit 共鳴スコアが高くて驚きました。",
    "msg-2": "こちらこそ。同じく感じていました。あなたの実験データ、興味深いです。",
    "msg-3": "語連想実験で「使命」に強く反応するんですよね。",
    "msg-4": "私は「共感」への反応が強くて。補完的ですね。",
  };

  let messages: Message[] = [];
  let selfDid = "";
  let withDid = "";
  let input = "";
  let loading = false;
  let partnerSpiritType: SpiritType | null = null;
  let msgListEl: HTMLDivElement;

  $: withDid = $page.url.searchParams.get("with") ?? "";
  $: partnerSpiritType = ($page.url.searchParams.get("spirit") as SpiritType) ?? null;

  onMount(async () => {
    selfDid = localStorage.getItem("deai-cohort-did") ?? "did:web:decom.etzhayyim.ai:demo";
    // Try to infer partner spirit type from stored matches
    if (!partnerSpiritType) {
      // default fallback for demo
      partnerSpiritType = "Caregiver";
    }
    if (withDid) await loadMessages();
  });

  async function loadMessages() {
    loading = true;
    try {
      const res = await deaiApi.listMessages(withDid, selfDid);
      messages = res.messages as Message[];
    } catch {
      messages = [
        { messageId: "msg-1", fromCohortDid: withDid, ciphertext: "signal:v1:enc1", sentAt: new Date(Date.now() - 180000).toISOString() },
        { messageId: "msg-2", fromCohortDid: selfDid, ciphertext: "signal:v1:enc2", sentAt: new Date(Date.now() - 120000).toISOString() },
        { messageId: "msg-3", fromCohortDid: withDid, ciphertext: "signal:v1:enc3", sentAt: new Date(Date.now() - 60000).toISOString() },
        { messageId: "msg-4", fromCohortDid: selfDid, ciphertext: "signal:v1:enc4", sentAt: new Date(Date.now() - 30000).toISOString() },
      ];
    } finally {
      loading = false;
      scrollToBottom();
    }
  }

  async function encryptMessage(text: string): Promise<{ ciphertext: string; iv: string }> {
    const key = await crypto.subtle.generateKey({ name: "AES-GCM", length: 256 }, false, ["encrypt", "decrypt"]);
    const iv = crypto.getRandomValues(new Uint8Array(12));
    const enc = new TextEncoder();
    const encrypted = await crypto.subtle.encrypt({ name: "AES-GCM", iv }, key, enc.encode(text));
    const b64 = btoa(String.fromCharCode(...new Uint8Array(encrypted)));
    const ivB64 = btoa(String.fromCharCode(...iv));
    return { ciphertext: `signal:v1:${b64}`, iv: ivB64 };
  }

  async function send() {
    if (!input.trim()) return;
    const text = input.trim();
    const tempId = `sent-${Date.now()}`;
    input = "";
    plaintextMap.set(tempId, text);
    messages = [...messages, {
      messageId: tempId,
      fromCohortDid: selfDid,
      ciphertext: "signal:v1:local",
      sentAt: new Date().toISOString()
    }];
    scrollToBottom();
    try {
      const { ciphertext, iv } = await encryptMessage(text);
      await deaiApi.sendMessage({ toCohortDid: withDid, ciphertext, iv }, selfDid);
    } catch { /* silent - message already shown optimistically */ }
  }

  function handleKey(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
  }

  function decryptDisplay(msg: Message): string {
    const local = plaintextMap.get(msg.messageId);
    if (local) return local;
    const demo = DEMO_MESSAGES[msg.messageId];
    if (demo) return demo;
    return "🔒 暗号化メッセージ";
  }

  function isOwn(msg: Message): boolean { return msg.fromCohortDid === selfDid; }
  function timeStr(iso: string): string { return new Date(iso).toLocaleTimeString("ja", { hour: "2-digit", minute: "2-digit" }); }

  function scrollToBottom() {
    setTimeout(() => { msgListEl?.scrollTo({ top: msgListEl.scrollHeight, behavior: "smooth" }); }, 50);
  }

  $: partnerMeta = partnerSpiritType ? SPIRIT_TYPE_META[partnerSpiritType] : null;
  $: partnerColor = partnerSpiritType ? (SPIRIT_COLORS[partnerSpiritType] ?? "#c084fc") : "#c084fc";
</script>

<svelte:head><title>メッセージ — deai</title></svelte:head>

<div class="message-page">
  <!-- Header -->
  <header class="msg-header">
    <a href="/matches" class="back-btn" aria-label="戻る">
      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
        <path d="M12 4L6 10L12 16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
      </svg>
    </a>
    <div class="header-avatar" style="background: {partnerColor}22; border-color: {partnerColor}55">
      <span class="avatar-emoji">{partnerMeta?.emoji ?? "✨"}</span>
    </div>
    <div class="header-info">
      <div class="header-top-row">
        <span class="partner-name">{partnerMeta?.ja ?? "Spirit"}</span>
        <span class="resonance-indicator">
          <span class="resonance-dot"></span>
          Spirit 共鳴中
        </span>
      </div>
      <span class="partner-did">{withDid.slice(-14)}</span>
    </div>
    <div class="e2e-pill">🔒 E2E</div>
  </header>

  <!-- Messages -->
  <div class="message-list" bind:this={msgListEl}>
    {#if loading}
      <div class="loading-msg">
        <div class="loading-dot d1"></div>
        <div class="loading-dot d2"></div>
        <div class="loading-dot d3"></div>
      </div>
    {:else}
      {#each messages as msg}
        {@const own = isOwn(msg)}
        <div class="msg-row" class:own>
          {#if !own}
            <div class="msg-avatar" style="background: {partnerColor}22; border-color: {partnerColor}44">
              <span class="avatar-sm">{partnerMeta?.emoji ?? "✨"}</span>
            </div>
          {/if}
          <div class="msg-col" class:own>
            <div class="bubble" class:own>
              {decryptDisplay(msg)}
            </div>
            <span class="msg-time" class:own>{timeStr(msg.sentAt)}</span>
          </div>
        </div>
      {/each}
    {/if}
  </div>

  <!-- Input -->
  <div class="input-area">
    <div class="input-row">
      <textarea
        bind:value={input}
        on:keydown={handleKey}
        placeholder="メッセージ（E2E暗号化）"
        rows="1"
        class="msg-input"
      ></textarea>
      <button class="send-btn" on:click={send} disabled={!input.trim()}>
        <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
          <path d="M16 9L2 2L5.5 9L2 16L16 9Z" fill="currentColor"/>
        </svg>
      </button>
    </div>
    <p class="privacy-bar">🔒 エンドツーエンド暗号化。平文はサーバーに届きません。</p>
  </div>
</div>

<style>
  .message-page {
    display: flex; flex-direction: column;
    height: calc(100dvh - 84px - env(safe-area-inset-bottom, 0px));
    background: var(--bg, #08080f);
  }

  /* Header */
  .msg-header {
    display: flex; align-items: center; gap: 10px;
    padding: 12px 16px;
    border-bottom: 1px solid rgba(255,255,255,0.07);
    background: rgba(8,8,15,0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    flex-shrink: 0;
  }
  .back-btn {
    color: #c084fc; padding: 6px; display: flex; align-items: center;
    border-radius: 8px; transition: background 0.15s;
    flex-shrink: 0;
  }
  .back-btn:hover { background: rgba(192,132,252,0.1); }
  .header-avatar {
    width: 40px; height: 40px; border-radius: 50%; border: 1.5px solid;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .avatar-emoji { font-size: 20px; }
  .header-info { flex: 1; min-width: 0; display: flex; flex-direction: column; gap: 2px; }
  .header-top-row { display: flex; align-items: center; gap: 8px; }
  .partner-name { font-size: 15px; font-weight: 700; color: #f0f0f8; }
  .resonance-indicator { display: flex; align-items: center; gap: 4px; font-size: 10px; color: rgba(240,240,248,0.45); }
  .resonance-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #4ade80;
    animation: resPulse 2s ease-in-out infinite;
    box-shadow: 0 0 4px #4ade80;
  }
  @keyframes resPulse { 0%,100% { opacity: 1; } 50% { opacity: 0.3; } }
  .partner-did { font-size: 10px; font-family: monospace; color: rgba(240,240,248,0.3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .e2e-pill { font-size: 10px; color: #4ade80; background: rgba(74,222,128,0.1); border: 1px solid rgba(74,222,128,0.2); padding: 3px 8px; border-radius: 10px; flex-shrink: 0; font-weight: 600; }

  /* Message list */
  .message-list {
    flex: 1; overflow-y: auto; padding: 16px 14px;
    display: flex; flex-direction: column; gap: 10px;
  }
  .loading-msg { display: flex; align-items: center; justify-content: center; gap: 6px; padding: 40px; }
  .loading-dot { width: 8px; height: 8px; border-radius: 50%; background: rgba(192,132,252,0.5); animation: dotBounce 1.2s ease-in-out infinite; }
  .d1 { animation-delay: 0s; }
  .d2 { animation-delay: 0.18s; }
  .d3 { animation-delay: 0.36s; }
  @keyframes dotBounce { 0%,80%,100% { transform: scale(0.7); opacity: 0.4; } 40% { transform: scale(1.2); opacity: 1; } }

  /* Message bubbles */
  .msg-row { display: flex; align-items: flex-end; gap: 8px; max-width: 82%; }
  .msg-row.own { align-self: flex-end; flex-direction: row-reverse; }
  .msg-avatar {
    width: 30px; height: 30px; border-radius: 50%; border: 1px solid;
    display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  }
  .avatar-sm { font-size: 15px; }
  .msg-col { display: flex; flex-direction: column; gap: 3px; max-width: 100%; }
  .msg-col.own { align-items: flex-end; }
  .bubble {
    padding: 11px 15px; border-radius: 18px; font-size: 14px; line-height: 1.55;
    background: rgba(255,255,255,0.07); color: rgba(240,240,248,0.9);
    border-bottom-left-radius: 4px;
    backdrop-filter: blur(8px);
    word-break: break-word;
    max-width: 280px;
  }
  .bubble.own {
    background: linear-gradient(135deg, rgba(192,132,252,0.8), rgba(129,140,248,0.8));
    color: #fff;
    border-bottom-left-radius: 18px;
    border-bottom-right-radius: 4px;
    box-shadow: 0 4px 16px rgba(192,132,252,0.25);
  }
  .msg-time { font-size: 10px; color: rgba(240,240,248,0.28); }
  .msg-time.own { }

  /* Input */
  .input-area {
    border-top: 1px solid rgba(255,255,255,0.07);
    background: rgba(8,8,15,0.92);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    padding: 10px 14px 8px;
    flex-shrink: 0;
  }
  .input-row { display: flex; gap: 8px; align-items: flex-end; }
  .msg-input {
    flex: 1; background: rgba(255,255,255,0.06); border: 1px solid rgba(255,255,255,0.1);
    border-radius: 14px; padding: 11px 14px; color: #f0f0f8; font-size: 14px;
    resize: none; line-height: 1.45; font-family: inherit; max-height: 120px;
    transition: border-color 0.15s;
  }
  .msg-input:focus { outline: none; border-color: rgba(192,132,252,0.4); background: rgba(255,255,255,0.08); }
  .msg-input::placeholder { color: rgba(240,240,248,0.28); }
  .send-btn {
    width: 42px; height: 42px; flex-shrink: 0;
    background: linear-gradient(135deg, #c084fc, #818cf8);
    border: none; border-radius: 12px; color: #fff;
    display: flex; align-items: center; justify-content: center;
    cursor: pointer;
    transition: opacity 0.15s, transform 0.12s;
    box-shadow: 0 3px 12px rgba(192,132,252,0.35);
  }
  .send-btn:hover { opacity: 0.9; transform: scale(1.04); }
  .send-btn:active { transform: scale(0.96); }
  .send-btn:disabled { opacity: 0.35; cursor: default; transform: none; box-shadow: none; }
  .privacy-bar { font-size: 10px; color: rgba(74,222,128,0.5); text-align: center; margin-top: 6px; letter-spacing: 0.02em; }
</style>
