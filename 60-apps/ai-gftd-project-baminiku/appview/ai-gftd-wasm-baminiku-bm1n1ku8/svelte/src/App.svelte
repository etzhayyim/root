<script lang="ts">
  import { onMount } from 'svelte';
  import { createVrmEngine, type VrmEngine } from '@etzhayyim/kami-engine-sdk/builders';

  type Role = 'user' | 'assistant';
  type Provider = 'projector' | 'openai';
  type Msg = { role: Role; text: string };
  type XrpcOptions = { bearerToken?: string; timeout?: number };

  const DEFAULT_VRM_URL =
    'https://raw.githubusercontent.com/pixiv/three-vrm/dev/packages/three-vrm/examples/models/VRM1_Constraint_Twist_Sample.vrm';

  let engine: VrmEngine | null = null;
  let loadingVrm = true;
  let vrmError = '';

  let provider: Provider = 'projector';
  let input = '';
  let sending = false;
  let messages: Msg[] = [
    { role: 'assistant', text: 'Baminiku へようこそ。話しかけてください。' },
  ];

  let vrmUrl = localStorage.getItem('baminiku:vrm-url') ?? DEFAULT_VRM_URL;
  let agentDid = localStorage.getItem('baminiku:agent-did') ?? 'did:web:baminiku.etzhayyim.com';
  let bearer = localStorage.getItem('baminiku:access-jwt') ?? '';

  let openaiBase = localStorage.getItem('baminiku:openai-base') ?? 'https://api.openai.com/v1';
  let openaiModel = localStorage.getItem('baminiku:openai-model') ?? 'gpt-4o-mini';
  let openaiKey = localStorage.getItem('baminiku:openai-key') ?? '';

  let convoId = '';

  async function atProcedure<T = unknown>(
    nsid: string,
    body?: unknown,
    opts: XrpcOptions = {},
  ): Promise<T> {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), opts.timeout ?? 30_000);
    try {
      const res = await fetch(`https://atproto.etzhayyim.com/xrpc/${nsid}`, {
        method: 'POST',
        headers: {
          'content-type': 'application/json',
          ...(opts.bearerToken ? { authorization: `Bearer ${opts.bearerToken}` } : {}),
        },
        body: JSON.stringify(body ?? {}),
        signal: controller.signal,
      });
      const data = await res.json().catch((_err) => ({}));
      if (!res.ok) {
        throw new Error((data as { message?: string; error?: string }).message ?? (data as { error?: string }).error ?? `${nsid} failed (${res.status})`);
      }
      return data as T;
    } finally {
      window.clearTimeout(timeout);
    }
  }

  function saveConfig() {
    localStorage.setItem('baminiku:vrm-url', vrmUrl);
    localStorage.setItem('baminiku:agent-did', agentDid);
    localStorage.setItem('baminiku:access-jwt', bearer);
    localStorage.setItem('baminiku:openai-base', openaiBase);
    localStorage.setItem('baminiku:openai-model', openaiModel);
    localStorage.setItem('baminiku:openai-key', openaiKey);
  }

  async function bootVrm() {
    loadingVrm = true;
    vrmError = '';
    try {
      engine?.dispose();
      engine = createVrmEngine({
        canvasId: 'vrm-canvas',
        kamiCanvasId: 'vrm-canvas',
        vrmUrl,
        engines: ['kami'],
        wasmUrl: '/kami-web',
      });
      await engine.init();
      if (engine.state.error) throw new Error(engine.state.error);
    } catch (err) {
      vrmError = err instanceof Error ? err.message : String(err);
    } finally {
      loadingVrm = false;
    }
  }

  async function ensureProjectConvo() {
    if (convoId) return convoId;
    const res = await atProcedure<Record<string, unknown>>(
      'com.etzhayyim.projector.newProjectConvo',
      {
        name: `baminiku-${new Date().toISOString()}`,
        members: [agentDid],
      },
      { bearerToken: bearer || undefined },
    );
    const id = String((res as { convoId?: string }).convoId ?? '');
    if (!id) throw new Error('convoId が返りませんでした');
    convoId = id;
    return id;
  }

  async function sendProjector(text: string) {
    const id = await ensureProjectConvo();
    const res = await atProcedure<Record<string, unknown>>(
      'com.etzhayyim.projector.sendProjectMessage',
      { convoId: id, text },
      { bearerToken: bearer || undefined },
    );
    const reply = String((res as { reply?: string }).reply ?? '').trim();
    return reply || '応答を受信しました。';
  }

  async function sendOpenAI(text: string) {
    if (!openaiKey.trim()) throw new Error('OpenAI API key を設定してください');
    const upstream = await fetch(`${openaiBase.replace(/\/$/, '')}/chat/completions`, {
      method: 'POST',
      headers: {
        'content-type': 'application/json',
        authorization: `Bearer ${openaiKey}`,
      },
      body: JSON.stringify({
        model: openaiModel,
        messages: [
          {
            role: 'system',
            content:
              'You are Baminiku, a friendly VTuber-like AI agent. Keep answers concise, natural, and conversational in user language.',
          },
          ...messages.map((m) => ({ role: m.role, content: m.text })),
          { role: 'user', content: text },
        ],
        temperature: 0.8,
      }),
    });
    if (!upstream.ok) {
      const body = await upstream.text();
      throw new Error(`OpenAI ${upstream.status}: ${body.slice(0, 200)}`);
    }
    const data = await upstream.json();
    return String(data?.choices?.[0]?.message?.content ?? '').trim() || '...';
  }

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    input = '';
    sending = true;
    messages = [...messages, { role: 'user', text }];

    try {
      saveConfig();
      const reply = provider === 'projector' ? await sendProjector(text) : await sendOpenAI(text);
      messages = [...messages, { role: 'assistant', text: reply }];
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      messages = [...messages, { role: 'assistant', text: `エラー: ${msg}` }];
    } finally {
      sending = false;
    }
  }

  onMount(() => {
    bootVrm();
    return () => engine?.dispose();
  });
</script>

<main class="layout">
  <section class="viewer">
    <div class="viewer-head">
      <h1>Baminiku Live Agent</h1>
      <p>Kami Engine SDK + VRM</p>
    </div>
    <canvas id="vrm-canvas"></canvas>
    {#if loadingVrm}
      <div class="overlay">VRM 読み込み中...</div>
    {/if}
    {#if vrmError}
      <div class="overlay error">VRMエラー: {vrmError}</div>
    {/if}
  </section>

  <section class="chat">
    <div class="panel settings">
      <div class="row">
        <label for="provider">Provider</label>
        <select id="provider" bind:value={provider}>
          <option value="projector">Projector (atproto)</option>
          <option value="openai">OpenAI Compatible</option>
        </select>
      </div>
      <div class="row">
        <label for="vrm-url">VRM URL</label>
        <input id="vrm-url" bind:value={vrmUrl} placeholder="https://...vrm" />
      </div>
      <button class="btn" on:click={bootVrm}>VRM Reload</button>

      {#if provider === 'projector'}
        <div class="row"><label for="agent-did">Agent DID</label><input id="agent-did" bind:value={agentDid} /></div>
        <div class="row"><label for="access-jwt">Access JWT</label><input id="access-jwt" bind:value={bearer} type="password" placeholder="Bearer token" /></div>
      {:else}
        <div class="row"><label for="openai-base">Base URL</label><input id="openai-base" bind:value={openaiBase} /></div>
        <div class="row"><label for="openai-model">Model</label><input id="openai-model" bind:value={openaiModel} /></div>
        <div class="row"><label for="openai-key">API Key</label><input id="openai-key" bind:value={openaiKey} type="password" /></div>
      {/if}
      <button class="btn ghost" on:click={saveConfig}>設定保存</button>
    </div>

    <div class="panel timeline">
      {#each messages as m}
        <div class={`msg ${m.role}`}>
          <span>{m.text}</span>
        </div>
      {/each}
      {#if sending}
        <div class="msg assistant"><span>...</span></div>
      {/if}
    </div>

    <div class="composer">
      <input
        bind:value={input}
        on:keydown={(e) => e.key === 'Enter' && send()}
        placeholder="メッセージを入力"
      />
      <button class="btn" on:click={send} disabled={sending}>送信</button>
    </div>
  </section>
</main>

<style>
  .layout {
    min-height: 100vh;
    display: grid;
    grid-template-columns: minmax(320px, 1fr) minmax(320px, 420px);
    gap: 16px;
    padding: 16px;
  }
  .viewer {
    position: relative;
    border-radius: 20px;
    background: linear-gradient(160deg, rgba(35, 48, 86, 0.75), rgba(10, 15, 29, 0.92));
    border: 1px solid rgba(255, 255, 255, 0.14);
    overflow: hidden;
    min-height: 520px;
  }
  .viewer-head { position: absolute; left: 12px; top: 12px; z-index: 2; }
  .viewer-head h1 { margin: 0; font-size: 20px; letter-spacing: 0.04em; }
  .viewer-head p { margin: 2px 0 0; font-size: 12px; color: #a8bbff; }
  canvas { width: 100%; height: 100%; min-height: 520px; display: block; }
  .overlay {
    position: absolute;
    inset: auto 12px 12px 12px;
    background: rgba(5, 8, 16, 0.75);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 10px;
    padding: 8px 10px;
    font-size: 12px;
  }
  .overlay.error { color: #ffb4b4; }

  .chat { display: grid; gap: 10px; grid-template-rows: auto 1fr auto; min-height: 520px; }
  .panel {
    border-radius: 16px;
    border: 1px solid rgba(255, 255, 255, 0.12);
    background: rgba(8, 10, 18, 0.75);
    padding: 10px;
  }
  .settings { display: grid; gap: 8px; }
  .row { display: grid; gap: 4px; }
  label { font-size: 11px; color: #9ca8cf; }
  input, select {
    background: #12172a;
    color: #f1f4ff;
    border: 1px solid #2b355a;
    border-radius: 8px;
    padding: 8px;
    font-size: 13px;
  }
  .timeline {
    overflow: auto;
    display: grid;
    gap: 8px;
    align-content: start;
    max-height: 420px;
  }
  .msg {
    border-radius: 10px;
    padding: 8px 10px;
    font-size: 13px;
    line-height: 1.45;
    white-space: pre-wrap;
  }
  .msg.user { background: #1f2f63; margin-left: 24px; }
  .msg.assistant { background: #20252d; margin-right: 24px; }
  .composer { display: grid; grid-template-columns: 1fr auto; gap: 8px; }
  .btn {
    border: 0;
    border-radius: 10px;
    padding: 8px 12px;
    background: linear-gradient(135deg, #18a0fb, #5f68ff);
    color: white;
    font-weight: 700;
    cursor: pointer;
  }
  .btn.ghost { background: #273153; }
  .btn:disabled { opacity: 0.5; cursor: default; }

  @media (max-width: 960px) {
    .layout {
      grid-template-columns: 1fr;
      grid-template-rows: auto auto;
    }
    .viewer, canvas, .chat { min-height: 420px; }
  }
</style>
