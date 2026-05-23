<script lang="ts">
  import type { Snapshot } from "./types";
  import { chatWith } from "./api";
  export let snap: Snapshot;
  export let selected: string | null;
  export let activity: any[] = [];
  export let onSelect: (id: string) => void;

  type Msg = { who: "you" | "them"; text: string };
  let chatLog: Msg[] = [];
  let inputVal = "";
  let lastInviteForId: string | null = null;

  $: ent = selected ? snap.entities[selected] : null;
  $: pruning = snap.pruning || [];

  $: if (ent && ent.id !== lastInviteForId) {
    chatLog = [{ who: "them", text: ent.chat_invite || "(silent)" }];
    lastInviteForId = ent.id;
  }

  async function send() {
    if (!selected || !inputVal.trim()) return;
    const msg = inputVal.trim();
    chatLog = [...chatLog, { who: "you", text: msg }];
    inputVal = "";
    try {
      const r = await chatWith(selected, msg);
      if (r.ok) chatLog = [...chatLog, { who: "them", text: r.voice }];
      else      chatLog = [...chatLog, { who: "them", text: "[error] " + (r.error || "?") }];
    } catch (e: any) {
      chatLog = [...chatLog, { who: "them", text: "[network] " + e.message }];
    }
  }
  function kindIcon(kind: string): string {
    return ({ axis: "枝", cell: "葉", organism: "中", ecosystem: "縁",
              fruit: "実", seed: "勾", app: "扇", adr: "輪" } as any)[kind] || "•";
  }
</script>

<aside class="sidebar">
  <!-- entity card -->
  <section class="entity">
    {#if ent}
      <div class="title-row">
        <span class="glyph">{kindIcon(ent.kind)}</span>
        <h2>{ent.title}</h2>
        {#if ent.pruning_severity > 0}
          <span class="prune-tag sev-{ent.pruning_severity}">剪 ×{ent.pruning_severity}</span>
        {/if}
      </div>
      <div class="meta">
        <code>{ent.id}</code> · {ent.kind} ·
        neighbors: {(ent.neighbors || []).length}
      </div>
      {#if ent.neighbors && ent.neighbors.length}
        <div class="neighbors">
          {#each ent.neighbors as n}
            <a href="#" on:click|preventDefault={() => onSelect(n)}>{n}</a>
          {/each}
        </div>
      {/if}
      <details>
        <summary>state</summary>
        <pre>{JSON.stringify(ent.state || {}, null, 2)}</pre>
      </details>
    {:else}
      <div class="title-row"><span class="glyph">縁</span><h2>対話相手を選ぶ</h2></div>
      <div class="muted">クリックして 葉・花・果実・種・枝・年輪 のいずれかと話す</div>
    {/if}
  </section>

  <!-- chat -->
  <section class="chat">
    <div class="log" role="log">
      {#each chatLog as m}
        <div class="msg msg-{m.who}">
          {#if m.who === "them"}<span class="seal">朱</span>{/if}
          <span class="txt">{m.text}</span>
        </div>
      {/each}
      {#if chatLog.length === 0 && !ent}
        <div class="muted">問いの例: <em>だれ?</em> · <em>目的は?</em> · <em>状態は?</em> · <em>つながりは?</em> · <em>次は?</em></div>
      {/if}
    </div>
    <form on:submit|preventDefault={send}>
      <input bind:value={inputVal}
             placeholder="話しかける… (だれ? 目的? 状態? 次? つながり? 剪定?)"
             autocomplete="off" />
      <button type="submit">送</button>
    </form>
  </section>

  <!-- pruning + activity -->
  <section class="meta-cols">
    <div class="col">
      <h3>剪定候補 <small>(operator)</small></h3>
      {#if pruning.length === 0}
        <div class="muted">候補なし — 盆栽 健全</div>
      {:else}
        <ul class="prune-list">
          {#each pruning.slice(0, 12) as c}
            <li class="sev-{c.severity}" on:click={() => onSelect(c.id)}>
              <span class="sev-bar"></span>
              <code>{c.id}</code>
              <span class="idle">{c.idle_days}日</span>
            </li>
          {/each}
        </ul>
      {/if}
    </div>
    <div class="col">
      <h3>activity <small>(SSE)</small></h3>
      <ul class="activity-list">
        {#each activity.slice(0, 18) as ev}
          <li class:is-chat={ev.type === 'chat'}>
            <time>{new Date(((ev.ts || Date.now()/1000) * 1000)).toLocaleTimeString("ja-JP", { hour12: false })}</time>
            <span class="atype">{ev.type}</span>
            {#if ev.type === 'chat'}
              <span class="asum">
                <a href="#" on:click|preventDefault={() => onSelect(ev.entity)}>{ev.entity}</a>
                {#if ev.message}<span class="chat-q">「{ev.message}」</span>{/if}
                {#if ev.voice}<span class="chat-a">→ {ev.voice.slice(0, 80)}{ev.voice.length > 80 ? '…' : ''}</span>{/if}
              </span>
            {:else}
              <span class="asum">{ev.summary || ev.subject || ev.id || ""}</span>
            {/if}
          </li>
        {/each}
      </ul>
    </div>
  </section>
</aside>

<style>
  .sidebar {
    background: var(--washi);
    border-left: 1px solid var(--sumi);
    padding: 18px 22px;
    display: grid;
    grid-template-rows: auto 1fr auto;
    gap: 14px; min-height: 0;
    font-family: var(--font-mincho);
  }
  .entity .title-row { display: flex; align-items: baseline; gap: 10px; }
  .entity h2 { margin: 0; font-size: 18px; font-weight: 700; letter-spacing: 0.01em; }
  .entity .glyph {
    display: inline-block; min-width: 28px; height: 28px;
    background: var(--shinshu); color: var(--washi);
    text-align: center; line-height: 28px; font-size: 14px; font-weight: 700;
    transform: rotate(-2deg);
  }
  .entity .meta { font-size: 11px; color: var(--sumi-soft); margin: 6px 0 4px; font-variant-numeric: tabular-nums; }
  .entity code { background: var(--washi-warm); padding: 1px 5px; border-radius: 2px; font-family: var(--font-num); }
  .neighbors { display: flex; flex-wrap: wrap; gap: 6px; margin: 4px 0 8px; font-size: 11px; }
  .neighbors a { color: var(--ai); text-decoration: none; border-bottom: 1px dotted var(--ai-pale); }
  .neighbors a:hover { color: var(--shinshu); border-color: var(--shinshu); }
  details summary { font-size: 11px; color: var(--sumi-soft); cursor: pointer; }
  details pre {
    background: var(--washi-warm); border: 1px solid var(--washi-deep);
    padding: 6px 8px; max-height: 120px; overflow: auto;
    font-family: var(--font-num); font-size: 10px; white-space: pre-wrap;
  }

  .chat { display: grid; grid-template-rows: 1fr auto; gap: 8px; min-height: 0; }
  .chat .log {
    background: var(--washi-warm);
    border: 1px solid var(--washi-deep);
    padding: 10px 12px;
    overflow-y: auto; min-height: 140px;
    font-size: 13px; line-height: 1.65;
  }
  .msg { margin: 0 0 6px; }
  .msg .seal {
    display: inline-block; background: var(--shinshu); color: var(--washi);
    padding: 0 4px; margin-right: 6px; font-size: 10px;
    transform: rotate(-3deg); vertical-align: middle;
  }
  .msg-you { color: var(--sumi-soft); }
  .msg-them .txt { color: var(--sumi); }
  .chat form { display: flex; gap: 6px; }
  .chat input {
    flex: 1; background: var(--washi); color: var(--sumi);
    border: 1px solid var(--sumi-pale); padding: 7px 10px;
    font-family: var(--font-mincho); font-size: 13px;
  }
  .chat button {
    padding: 7px 12px; background: var(--shinshu); color: var(--washi);
    border: none; font-family: var(--font-mincho); font-size: 13px; cursor: pointer;
  }
  .chat button:hover { filter: brightness(1.08); }

  .meta-cols { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; min-height: 0; }
  .col { min-height: 0; overflow: hidden; display: flex; flex-direction: column; }
  .col h3 { margin: 0 0 6px; font-size: 12px; color: var(--sumi-soft); letter-spacing: 0.05em; }
  .col h3 small { color: var(--sumi-pale); font-weight: 400; }
  .prune-list, .activity-list { list-style: none; margin: 0; padding: 0; overflow-y: auto; flex: 1; }
  .prune-list li {
    display: flex; align-items: center; gap: 6px;
    padding: 3px 4px 3px 0; cursor: pointer; font-size: 11px;
  }
  .prune-list li:hover { background: var(--washi-warm); }
  .prune-list .sev-bar { display: inline-block; width: 3px; height: 14px; background: var(--suou); }
  .prune-list li.sev-2 .sev-bar { width: 4px; }
  .prune-list li.sev-3 .sev-bar { width: 6px; background: #a01010; }
  .prune-list code { font-family: var(--font-num); color: var(--sumi); }
  .prune-list .idle { color: var(--sumi-pale); margin-left: auto; font-variant-numeric: tabular-nums; }
  .activity-list li {
    display: grid; grid-template-columns: 56px 60px 1fr; gap: 6px;
    padding: 2px 0; font-size: 11px; border-bottom: 1px dotted var(--washi-deep);
  }
  .activity-list time { font-family: var(--font-num); color: var(--sumi-pale); font-variant-numeric: tabular-nums; }
  .activity-list .atype { color: var(--ai); font-size: 10px; }
  .activity-list .asum { color: var(--sumi-soft); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .activity-list li.is-chat { background: var(--washi-warm); border-left: 2px solid var(--shinshu); padding-left: 4px; }
  .activity-list li.is-chat .atype { color: var(--shinshu); font-weight: 600; }
  .activity-list .chat-q { color: var(--ai); font-style: italic; }
  .activity-list .chat-a { color: var(--sumi); }
  .activity-list .asum a { color: var(--shinshu); text-decoration: none; border-bottom: 1px dotted var(--shinshu); margin-right: 4px; }
  .muted { color: var(--sumi-pale); font-size: 12px; }
  .prune-tag {
    margin-left: auto; background: var(--suou); color: var(--washi);
    padding: 1px 6px; font-size: 10px; transform: rotate(-2deg);
  }
</style>
