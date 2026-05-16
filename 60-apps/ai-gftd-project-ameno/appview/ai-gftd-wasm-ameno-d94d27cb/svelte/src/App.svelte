<script lang="ts">
  import {
    MODELS,
    checkWebGPU,
    getGPUInfo,
    loadModel,
    generate,
    setLoraAdapters,
    getActiveAdapterIds,
    type ChatMessage,
    type InferenceDevice,
    type InferenceState,
    type GenerationStats,
  } from "./lib/inference";
  import { openBriefStream, type Brief } from "./lib/brief-stream";
  import { saveResult } from "./lib/save-result";
  import { encryptText, decryptText, isEncrypted } from "./lib/private-vault";
  import { listHistory, type HistoryItem } from "./lib/list-history";
  import { listActorAdapters, type AdapterRow } from "./lib/list-actor-adapters";
  import { listMyCredits, type MyCreditsResponse } from "./lib/list-my-credits";

  /** When true, outputs are AES-GCM encrypted client-side before saveResult. */
  let privateMode = $state(false);

  /** Engine model ids selectable by the user. SSoT: @gftd/ameno MODELS. */
  const MODEL_OPTIONS = Object.keys(MODELS);
  /** Models that prefer WASM ternary kernels over WebGPU. */
  const WASM_PREFERRED = new Set(["baien-bitnet-2b"]);
  let selectedModelId = $state(MODEL_OPTIONS[0] ?? "gemma-4-e2b-it");
  /** Device override for the next loadModel() call. null = engine default. */
  let selectedDevice = $state<InferenceDevice | null>(null);
  import type { AdapterCandidate } from "./lib/rag-lora";

  let state: InferenceState = $state({
    status: "idle",
    progress: 0,
    error: null,
    loadedModel: null,
    webgpuAvailable: false,
    activeAdapters: [],
    actorDid: null,
  });

  let messages: ChatMessage[] = $state([]);
  let inputText = $state("");
  let streamingText = $state("");
  let lastStats: GenerationStats | null = $state(null);
  let gpuInfo = $state("");
  let chatContainer: HTMLElement | undefined = $state();

  /** Actor DID input for per-actor LoRA scoping. */
  let actorDidInput = $state("");
  /** Available adapters for current actor. */
  let availableAdapters: AdapterCandidate[] = $state([]);
  /** Whether LoRA panel is expanded. */
  let loraPanelOpen = $state(false);

  /** Check WebGPU on mount; if absent and Baien is available, default to it on WASM. */
  $effect(() => {
    checkWebGPU().then((ok) => {
      state.webgpuAvailable = ok;
      if (!ok && MODELS["baien-bitnet-2b"]) {
        selectedModelId = "baien-bitnet-2b";
        selectedDevice = "wasm";
      }
    });
    getGPUInfo().then((info) => {
      gpuInfo = info;
    });
  });

  /** Auto-scroll chat to bottom. */
  function scrollToBottom() {
    if (chatContainer) {
      chatContainer.scrollTop = chatContainer.scrollHeight;
    }
  }

  /** Load the selected model (Gemma 4 E2B/E4B on WebGPU; Baien on WASM ternary). */
  async function handleLoadModel() {
    state.status = "loading";
    state.error = null;
    state.progress = 0;

    const device =
      selectedDevice ??
      (WASM_PREFERRED.has(selectedModelId) ? "wasm" : "webgpu");

    try {
      await loadModel((p) => {
        state.progress = p;
      }, selectedModelId, device);
      state.status = "ready";
      state.loadedModel = selectedModelId;
    } catch (e) {
      state.status = "error";
      state.error = e instanceof Error ? e.message : String(e);
      console.error("Model load failed:", e);
    }
  }

  /** Per-actor LoRA candidates fetched from vertex_lora_adapter (Phase 5g). */
  let actorAdapterRows = $state<AdapterRow[]>([]);
  let adaptersLoading = $state(false);
  let adaptersError = $state<string | null>(null);
  /** Selected adapter ids to record in saveResult.loraAdapters. */
  let selectedAdapterIds = $state<string[]>([]);

  /** Set actor DID for per-actor LoRA + fetch available adapters. */
  async function handleSetActor() {
    const did = actorDidInput.trim();
    if (!did) return;
    state.actorDid = did;
    state.activeAdapters = [];
    availableAdapters = [];
    selectedAdapterIds = [];
    setLoraAdapters([]);
    adaptersLoading = true;
    adaptersError = null;
    try {
      const res = await listActorAdapters({ actorDid: did, limit: 50 });
      actorAdapterRows = res.items;
    } catch (e) {
      adaptersError = e instanceof Error ? e.message : String(e);
    } finally {
      adaptersLoading = false;
    }
  }

  /** Clear actor and adapters. */
  function handleClearActor() {
    state.actorDid = null;
    state.activeAdapters = [];
    actorDidInput = "";
    availableAdapters = [];
    actorAdapterRows = [];
    selectedAdapterIds = [];
    adaptersError = null;
    setLoraAdapters([]);
  }

  /**
   * Toggle a LoRA adapter selection.
   *
   * NOTE: this commits the selection to state.activeAdapters and
   * saveResult.loraAdapters, but does NOT actually merge weights into the
   * loaded transformers.js pipeline — that requires getting at the model's
   * raw Float32Array weights, which is a separate (large) integration.
   * Per-actor inference quality is unchanged in this commit; the wiring
   * is in place for that follow-up.
   */
  function toggleAdapter(adapterId: string) {
    if (selectedAdapterIds.includes(adapterId)) {
      selectedAdapterIds = selectedAdapterIds.filter((x) => x !== adapterId);
    } else {
      selectedAdapterIds = [...selectedAdapterIds, adapterId];
    }
    state.activeAdapters = [...selectedAdapterIds];
  }

  /** Send a message and generate a response. */
  async function handleSend() {
    const text = inputText.trim();
    if (!text || state.status !== "ready") return;

    inputText = "";
    messages = [...messages, { role: "user", content: text }];
    streamingText = "";
    state.status = "generating";
    lastStats = null;

    setTimeout(scrollToBottom, 0);

    try {
      const chatMessages: ChatMessage[] = [
        {
          role: "system",
          content: state.actorDid
            ? `You are Murakumo, a personalized AI assistant for actor ${state.actorDid}. Running locally in the browser via WebGPU with per-actor LoRA adaptation. Be concise and helpful.`
            : "You are Murakumo, a helpful AI assistant running locally in the user's browser via WebGPU. Be concise and helpful.",
        },
        ...messages,
      ];

      const stats = await generate(chatMessages, (token) => {
        streamingText += token;
        setTimeout(scrollToBottom, 0);
      });

      messages = [
        ...messages,
        { role: "assistant", content: streamingText },
      ];
      streamingText = "";
      lastStats = stats;
      state.status = "ready";
      state.activeAdapters = getActiveAdapterIds();
    } catch (e) {
      state.status = "error";
      state.error = e instanceof Error ? e.message : String(e);
      console.error("Generation failed:", e);
    }
  }

  /** Handle Enter key in input. */
  function handleKeyDown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  // ── Auto-respond mode ──
  // Subscribes to ai.gftd.apps.ameno.subscribeBriefs (NATS firehose), runs
  // local inference per brief, and posts the result via saveResult. This
  // closes the murakumo Tier 2 crowd-source loop end-to-end (Phase 4a + 5a).

  let autoRespondActive = $state(false);
  let autoRespondCount = $state(0);
  let autoRespondError = $state<string | null>(null);
  let autoRespondHistory = $state<Array<{ prompt: string; output: string; uri: string }>>([]);
  let autoRespondCloser: (() => void) | null = null;
  /** Drop briefs while a generation is in flight to avoid queue blow-up. */
  let autoRespondInFlight = false;

  async function processBrief(brief: Brief) {
    if (autoRespondInFlight || state.status !== "ready") return;
    autoRespondInFlight = true;
    let output = "";
    try {
      const chat: ChatMessage[] = [
        {
          role: "system",
          content:
            "You are Ameno, a browser-local LLM serving the gftd platform. Reply briefly to the post below. Output ONE concise sentence in the same language as the input.",
        },
        { role: "user", content: brief.text },
      ];
      const stats = await generate(chat, (token) => {
        output += token;
      });
      const persistedOutput = privateMode ? await encryptText(output) : output;
      const res = await saveResult({
        modelId: state.loadedModel ?? "",
        prompt: brief.text,
        output: persistedOutput,
        actorDid: state.actorDid ?? "",
        loraAdapters: selectedAdapterIds.length > 0 ? selectedAdapterIds : undefined,
        elapsedMs: stats.durationMs,
        tokensPerSec: Math.round(stats.tokensPerSecond * 1000),
        outputTokens: stats.totalTokens,
        ragContextUsed: stats.ragActive,
      });
      autoRespondCount++;
      autoRespondHistory = [
        { prompt: brief.text, output, uri: res.uri ?? brief.uri },
        ...autoRespondHistory,
      ].slice(0, 5);
    } catch (e) {
      autoRespondError = e instanceof Error ? e.message : String(e);
    } finally {
      autoRespondInFlight = false;
    }
  }

  function startAutoRespond() {
    if (autoRespondActive || state.status !== "ready") return;
    autoRespondError = null;
    autoRespondActive = true;
    autoRespondCloser = openBriefStream({
      collection: "app.bsky.feed.post",
      maxEvents: 1000,
      idleTimeoutSec: 300,
      onBrief: (brief) => { void processBrief(brief); },
      onDone: () => { stopAutoRespond(); },
      onError: (e) => { autoRespondError = e.message; },
    });
  }

  function stopAutoRespond() {
    autoRespondActive = false;
    autoRespondCloser?.();
    autoRespondCloser = null;
  }

  // ── History panel ──
  // Pulls vertex_ameno_inferenceresult via listHistory and decrypts any
  // signal:v1: outputs (Phase 5b) on display so the round-trip is visible.

  interface HistoryView extends HistoryItem {
    /** Decrypted output (or original if it was plaintext). */
    displayOutput: string;
    /** True if the source row carried a signal:v1: envelope. */
    wasEncrypted: boolean;
    /** Decrypt error, if the envelope failed (e.g. lost localStorage key). */
    decryptError: string | null;
  }

  let historyItems = $state<HistoryView[]>([]);
  let historyLoading = $state(false);
  let historyError = $state<string | null>(null);
  let historyTotal = $state(0);
  let creditBalance = $state<MyCreditsResponse | null>(null);

  async function refreshHistory() {
    historyLoading = true;
    historyError = null;
    try {
      const did = state.actorDid ?? "";
      const [res, credits] = await Promise.all([
        listHistory({ actorDid: did, limit: 20 }),
        did ? listMyCredits(did) : Promise.resolve(null),
      ]);
      creditBalance = credits;
      const decrypted = await Promise.all(
        res.items.map(async (item) => {
          const wasEncrypted = isEncrypted(item.output);
          let displayOutput = item.output;
          let decryptError: string | null = null;
          if (wasEncrypted) {
            try {
              displayOutput = await decryptText(item.output);
            } catch (e) {
              decryptError = e instanceof Error ? e.message : String(e);
            }
          }
          return { ...item, displayOutput, wasEncrypted, decryptError };
        }),
      );
      historyItems = decrypted;
      historyTotal = res.total;
    } catch (e) {
      historyError = e instanceof Error ? e.message : String(e);
    } finally {
      historyLoading = false;
    }
  }
</script>

<div class="app">
  <!-- Header -->
  <header class="header">
    <div class="header-inner">
      <h1 class="logo">Murakumo Browser</h1>
      <span class="badge">WebGPU</span>
      {#if state.activeAdapters.length > 0}
        <span class="badge lora-badge">LoRA</span>
      {/if}
      {#if state.actorDid}
        <span class="actor-badge" title={state.actorDid}>
          {state.actorDid.slice(0, 20)}...
        </span>
      {/if}
    </div>
  </header>

  <!-- Main content -->
  <main class="main">
    {#if state.status === "idle"}
      <!-- Landing: load model -->
      <div class="landing">
        <div class="landing-card">
          <h2>Gemma 4 E2B</h2>
          <p class="model-desc">
            2.3B effective parameters, multimodal (text + image + audio).
            Runs entirely in your browser via WebGPU.
          </p>

          {#if !state.webgpuAvailable}
            <div class="warning">
              WebGPU is not available in this browser. Use Chrome 113+ or Edge 113+.
            </div>
          {:else}
            <p class="gpu-info">{gpuInfo}</p>

            <!-- Actor LoRA panel -->
            <div class="lora-panel">
              <button
                class="btn-toggle"
                onclick={() => loraPanelOpen = !loraPanelOpen}
              >
                {loraPanelOpen ? "Hide" : "Show"} Actor LoRA
              </button>

              {#if loraPanelOpen}
                <div class="lora-config">
                  <input
                    class="input-actor"
                    type="text"
                    placeholder="Actor DID (e.g. did:web:...)"
                    bind:value={actorDidInput}
                  />
                  <div class="lora-actions">
                    <button class="btn-small" onclick={handleSetActor}>
                      Set Actor
                    </button>
                    {#if state.actorDid}
                      <button class="btn-small btn-clear" onclick={handleClearActor}>
                        Clear
                      </button>
                    {/if}
                  </div>
                  {#if state.actorDid}
                    <p class="lora-status">
                      Actor: {state.actorDid.slice(0, 30)}...
                      {#if selectedAdapterIds.length > 0}
                        <br />Selected: {selectedAdapterIds.join(", ")}
                      {:else}
                        <br />No adapter selected (base model)
                      {/if}
                    </p>
                    {#if adaptersLoading}
                      <p class="lora-status">Loading adapters...</p>
                    {:else if adaptersError}
                      <p class="lora-status auto-respond-error">⚠ {adaptersError}</p>
                    {:else if actorAdapterRows.length === 0}
                      <p class="lora-status">No adapters registered for this actor.</p>
                    {:else}
                      <div class="lora-adapter-list">
                        {#each actorAdapterRows as row}
                          <label class="lora-adapter-item">
                            <input
                              type="checkbox"
                              checked={selectedAdapterIds.includes(row.adapterId)}
                              onchange={() => toggleAdapter(row.adapterId)}
                            />
                            <span class="lora-adapter-id">{row.adapterId}</span>
                            <span class="lora-adapter-meta">
                              {row.domain || 'general'} · r{row.adapterRank} · {row.baseModel}
                            </span>
                          </label>
                        {/each}
                      </div>
                    {/if}
                  {/if}
                </div>
              {/if}
            </div>

            <div class="model-picker">
              <label for="model-select">Model:</label>
              <select id="model-select" bind:value={selectedModelId}>
                {#each MODEL_OPTIONS as opt}
                  <option value={opt}>{opt}</option>
                {/each}
              </select>
              <span class="device-pill">
                {selectedDevice ?? (WASM_PREFERRED.has(selectedModelId) ? "wasm" : "webgpu")}
              </span>
            </div>
            <button class="btn-primary" onclick={handleLoadModel}>
              Load Model
            </button>
          {/if}
        </div>
      </div>

    {:else if state.status === "loading"}
      <!-- Loading progress -->
      <div class="landing">
        <div class="landing-card">
          <h2>Loading {selectedModelId}...</h2>
          <div class="progress-bar">
            <div class="progress-fill" style="width: {state.progress}%"></div>
          </div>
          <p class="progress-text">{state.progress}% — Downloading ONNX weights</p>
        </div>
      </div>

    {:else if state.status === "merging-lora"}
      <!-- LoRA merge progress -->
      <div class="landing">
        <div class="landing-card">
          <h2>Merging LoRA Adapter...</h2>
          <div class="progress-bar">
            <div class="progress-fill lora-fill" style="width: {state.progress}%"></div>
          </div>
          <p class="progress-text">{state.progress}% — Applying actor adaptation</p>
        </div>
      </div>

    {:else if state.status === "error"}
      <!-- Error state -->
      <div class="landing">
        <div class="landing-card error-card">
          <h2>Error</h2>
          <p class="error-text">{state.error}</p>
          <button class="btn-primary" onclick={handleLoadModel}>
            Retry
          </button>
        </div>
      </div>

    {:else}
      <!-- Chat interface -->
      <div class="chat-container" bind:this={chatContainer}>
        {#if messages.length === 0}
          <div class="empty-state">
            <p>Model loaded. Start chatting.</p>
            <p class="hint">
              Inference runs locally on your GPU — no data leaves your device.
              {#if state.actorDid}
                <br />Actor: {state.actorDid.slice(0, 40)}
                {#if state.activeAdapters.length > 0}
                  (LoRA active)
                {/if}
              {/if}
            </p>
          </div>
        {/if}

        {#each messages as msg}
          <div class="message {msg.role}">
            <div class="message-label">{msg.role === "user" ? "You" : "Murakumo"}</div>
            <div class="message-content">{typeof msg.content === 'string' ? msg.content : JSON.stringify(msg.content)}</div>
          </div>
        {/each}

        {#if streamingText}
          <div class="message assistant">
            <div class="message-label">Murakumo</div>
            <div class="message-content">{streamingText}<span class="cursor">|</span></div>
          </div>
        {/if}
      </div>

      <!-- Stats bar -->
      {#if lastStats}
        <div class="stats-bar">
          {lastStats.tokensPerSecond.toFixed(1)} tok/s | {lastStats.totalTokens} tokens | {(lastStats.durationMs / 1000).toFixed(1)}s
          {#if lastStats.loraActive} | LoRA{/if}
          {#if lastStats.ragActive} | RAG{/if}
        </div>
      {/if}

      <!-- Auto-respond panel (Phase 5a: NATS firehose → local inference → saveResult) -->
      <div class="auto-respond">
        <div class="auto-respond-header">
          <label>
            <input
              type="checkbox"
              checked={autoRespondActive}
              onchange={(e) => (e.currentTarget as HTMLInputElement).checked ? startAutoRespond() : stopAutoRespond()}
            />
            Auto-respond to PDS firehose
          </label>
          <label class="private-toggle" title="Encrypt outputs (signal:v1:) before saveResult. Server stores ciphertext only.">
            <input type="checkbox" bind:checked={privateMode} />
            🔒 Private mode
          </label>
          {#if autoRespondActive}
            <span class="auto-respond-status">live · {autoRespondCount} responded</span>
          {/if}
          {#if autoRespondError}
            <span class="auto-respond-error" title={autoRespondError}>⚠ {autoRespondError.slice(0, 60)}</span>
          {/if}
        </div>
        {#if autoRespondHistory.length > 0}
          <div class="auto-respond-list">
            {#each autoRespondHistory as item}
              <div class="auto-respond-item">
                <div class="auto-respond-prompt">→ {item.prompt.slice(0, 100)}</div>
                <div class="auto-respond-output">⤷ {item.output.slice(0, 200)}</div>
              </div>
            {/each}
          </div>
        {/if}
      </div>

<!-- History panel (Phase 5f: listHistory + decrypt for signal:v1: rows; Phase 5j: balance) -->
      <div class="history">
        <div class="history-header">
          <button class="btn-small" onclick={refreshHistory} disabled={historyLoading}>
            {historyLoading ? "Loading..." : "Refresh history"}
          </button>
          {#if historyTotal > 0}
            <span class="history-status">{historyItems.length} / {historyTotal}</span>
          {/if}
          {#if creditBalance && creditBalance.eventCount > 0}
            <span
              class="history-status"
              title="Tier 2 credits earned from saveResult-credited inferences (Phase 5c)"
            >
              💎 {creditBalance.balance} credits · {creditBalance.eventCount} events
            </span>
          {/if}
          {#if historyError}
            <span class="auto-respond-error" title={historyError}>⚠ {historyError.slice(0, 60)}</span>
          {/if}
        </div>
        {#if historyItems.length > 0}
          <div class="history-list">
            {#each historyItems as item}
              <div class="history-item">
                <div class="history-meta">
                  <span class="history-model">{item.modelId}</span>
                  {#if item.wasEncrypted}
                    <span class="history-badge" title="Decrypted from signal:v1: envelope">🔒</span>
                  {/if}
                  <span class="history-time">{item.createdAt.slice(0, 19).replace("T", " ")}</span>
                  {#if item.elapsedMs > 0}
                    <span class="history-perf">{(item.elapsedMs / 1000).toFixed(1)}s</span>
                  {/if}
                </div>
                <div class="history-prompt">→ {item.prompt.slice(0, 200)}</div>
                {#if item.decryptError}
                  <div class="history-output history-decrypt-failed">
                    ⤷ <em>decrypt failed: {item.decryptError}</em>
                  </div>
                {:else}
                  <div class="history-output">⤷ {item.displayOutput.slice(0, 400)}</div>
                {/if}
              </div>
            {/each}
          </div>
        {/if}
      </div>

      <!-- Input area -->
      <div class="input-area">
        <div class="input-inner">
          <textarea
            class="input-field"
            placeholder="Message Murakumo..."
            bind:value={inputText}
            onkeydown={handleKeyDown}
            disabled={state.status === "generating"}
            rows={1}
          ></textarea>
          <button
            class="btn-send"
            onclick={handleSend}
            disabled={state.status === "generating" || !inputText.trim()}
          >
            {state.status === "generating" ? "..." : "Send"}
          </button>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  .app {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    max-width: 600px;
    margin: 0 auto;
  }

  .header {
    position: sticky;
    top: 0;
    z-index: 10;
    background: #0a0a0a;
    border-bottom: 1px solid #1a1a1a;
    height: 48px;
    display: flex;
    align-items: center;
  }

  .header-inner {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 16px;
    width: 100%;
  }

  .logo {
    font-size: 15px;
    font-weight: 600;
    color: #e5e5e5;
  }

  .badge {
    font-size: 10px;
    font-weight: 600;
    color: #22c55e;
    background: #14532d;
    padding: 2px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .lora-badge {
    color: #a78bfa;
    background: #2e1065;
  }

  .actor-badge {
    font-size: 10px;
    color: #737373;
    margin-left: auto;
    max-width: 150px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .main {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .landing {
    flex: 1;
    display: grid;
    place-content: center;
    padding: 24px 16px;
  }

  .landing-card {
    text-align: center;
    max-width: 360px;
  }

  .landing-card h2 {
    font-size: 20px;
    font-weight: 700;
    margin-bottom: 12px;
  }

  .model-desc {
    font-size: 13px;
    color: #a3a3a3;
    line-height: 1.5;
    margin-bottom: 20px;
  }

  .gpu-info {
    font-size: 12px;
    color: #737373;
    margin-bottom: 16px;
  }

  .warning {
    font-size: 13px;
    color: #f59e0b;
    background: #451a03;
    padding: 12px;
    border-radius: 8px;
  }

  .lora-panel {
    margin-bottom: 16px;
  }

  .btn-toggle {
    background: none;
    border: 1px solid #262626;
    color: #a3a3a3;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    cursor: pointer;
    margin-bottom: 8px;
  }

  .btn-toggle:hover {
    border-color: #404040;
    color: #e5e5e5;
  }

  .lora-config {
    text-align: left;
    background: #111111;
    border: 1px solid #1a1a1a;
    border-radius: 8px;
    padding: 12px;
    margin-top: 4px;
  }

  .input-actor {
    width: 100%;
    background: #171717;
    border: 1px solid #262626;
    border-radius: 6px;
    color: #e5e5e5;
    font-size: 13px;
    padding: 8px 10px;
    margin-bottom: 8px;
    font-family: inherit;
    box-sizing: border-box;
  }

  .input-actor::placeholder {
    color: #525252;
  }

  .input-actor:focus {
    outline: none;
    border-color: #a78bfa;
  }

  .lora-actions {
    display: flex;
    gap: 8px;
    margin-bottom: 8px;
  }

  .btn-small {
    background: #a78bfa;
    color: white;
    border: none;
    padding: 6px 12px;
    border-radius: 6px;
    font-size: 12px;
    font-weight: 600;
    cursor: pointer;
    min-height: 32px;
  }

  .btn-small:active {
    background: #8b5cf6;
  }

  .btn-clear {
    background: #404040;
  }

  .btn-clear:active {
    background: #525252;
  }

  .lora-status {
    font-size: 11px;
    color: #737373;
    line-height: 1.5;
  }

  .btn-primary {
    background: #3b82f6;
    color: white;
    border: none;
    padding: 12px 32px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    min-height: 44px;
    min-width: 44px;
  }

  .btn-primary:active {
    background: #2563eb;
  }

  .progress-bar {
    height: 6px;
    background: #1a1a1a;
    border-radius: 3px;
    overflow: hidden;
    margin: 16px 0 8px;
  }

  .progress-fill {
    height: 100%;
    background: #3b82f6;
    border-radius: 3px;
    transition: width 0.3s ease;
  }

  .lora-fill {
    background: #a78bfa;
  }

  .progress-text {
    font-size: 13px;
    color: #737373;
  }

  .error-card .error-text {
    font-size: 13px;
    color: #ef4444;
    margin-bottom: 16px;
    word-break: break-word;
  }

  .chat-container {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    padding-bottom: 80px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .empty-state {
    text-align: center;
    padding: 48px 16px;
    color: #737373;
    font-size: 13px;
  }

  .empty-state .hint {
    margin-top: 8px;
    font-size: 12px;
    color: #525252;
  }

  .message {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .message-label {
    font-size: 11px;
    font-weight: 600;
    color: #737373;
    text-transform: uppercase;
    letter-spacing: 0.05em;
  }

  .message-content {
    font-size: 15px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message.user .message-content {
    color: #e5e5e5;
  }

  .message.assistant .message-content {
    color: #d4d4d4;
  }

  .cursor {
    animation: blink 1s step-end infinite;
    color: #3b82f6;
  }

  @keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0; }
  }

  .stats-bar {
    font-size: 11px;
    color: #525252;
    text-align: center;
    padding: 4px;
    background: #0a0a0a;
    border-top: 1px solid #1a1a1a;
  }

  .input-area {
    position: sticky;
    bottom: 0;
    background: #0a0a0a;
    border-top: 1px solid #1a1a1a;
    padding: 12px 16px;
    padding-bottom: max(12px, env(safe-area-inset-bottom));
  }

  .input-inner {
    display: flex;
    gap: 8px;
    align-items: flex-end;
  }

  .input-field {
    flex: 1;
    background: #171717;
    border: 1px solid #262626;
    border-radius: 8px;
    color: #e5e5e5;
    font-size: 15px;
    padding: 10px 12px;
    resize: none;
    min-height: 44px;
    max-height: 120px;
    font-family: inherit;
  }

  .input-field::placeholder {
    color: #525252;
  }

  .input-field:focus {
    outline: none;
    border-color: #3b82f6;
  }

  .btn-send {
    background: #3b82f6;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    font-size: 15px;
    font-weight: 600;
    cursor: pointer;
    min-height: 44px;
    min-width: 44px;
  }

  .btn-send:disabled {
    background: #1e3a5f;
    color: #525252;
    cursor: not-allowed;
  }

  .btn-send:active:not(:disabled) {
    background: #2563eb;
  }
</style>
