<script lang="ts">
  import type { Message } from "./api";
  import { m } from "../paraglide/messages.js";

  let { messages, streamingDelta, streamStatus, toolEvents }: {
    messages: Message[];
    streamingDelta: string;
    streamStatus: string;
    toolEvents: { tool: string; ok: boolean; summary: string }[];
  } = $props();
</script>

<div class="thread">
  {#each messages as msg (msg.msgId)}
    <div class="row" class:user={msg.role === "user"} class:assistant={msg.role === "assistant"} class:system={msg.role === "system" || msg.role === "tool"}>
      <div class="bubble">
        {#if msg.role === "user"}
          <div class="badge user-badge">{m.role_user()}</div>
        {:else if msg.role === "assistant"}
          <div class="badge gftd-badge">{m.role_assistant()}</div>
        {:else}
          <div class="badge sys-badge">{msg.role}</div>
        {/if}
        <div class="content">{msg.content}</div>
        {#if msg.totalTokens}
          <div class="meta">{msg.totalTokens} {m.label_tokens()}{msg.modelUsed ? ` · ${msg.modelUsed}` : ""}</div>
        {/if}
      </div>
    </div>
  {/each}
  {#if streamingDelta || streamStatus}
    <div class="row assistant">
      <div class="bubble">
        <div class="badge gftd-badge">{m.role_assistant()}</div>
        {#if streamingDelta}
          <div class="content">{streamingDelta}<span class="cursor">▍</span></div>
        {:else}
          <div class="thinking">
            <span class="dot"></span>
            <span>{streamStatus}</span>
          </div>
        {/if}
        {#if toolEvents.length > 0}
          <div class="tools">
            {#each toolEvents as ev (ev.tool + ev.summary)}
              <div class="tool" class:fail={!ev.ok}>
                <code>{ev.tool}</code>
                <span class:ok={ev.ok} class:err={!ev.ok}>{ev.ok ? "✓" : "✗"}</span>
              </div>
            {/each}
          </div>
        {/if}
      </div>
    </div>
  {/if}
</div>

<style>
  .thread {
    max-width: 760px;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .row { display: flex; }
  .row.user { justify-content: flex-end; }
  .row.assistant, .row.system { justify-content: flex-start; }
  .bubble {
    max-width: 85%;
    background: #1d2230;
    border: 1px solid #2f3445;
    border-radius: 12px;
    padding: 12px 14px;
    font-size: 14px;
    line-height: 1.6;
    white-space: pre-wrap;
    word-wrap: break-word;
  }
  .row.user .bubble {
    background: #283045;
    border-color: #354060;
  }
  .row.system .bubble {
    background: #1a1d28;
    color: #a8acb8;
    font-family: ui-monospace, "SF Mono", Menlo, monospace;
    font-size: 12.5px;
  }
  .badge {
    font-size: 11px;
    color: #8a8e9a;
    margin-bottom: 4px;
  }
  .gftd-badge { color: #7aa2f7; }
  .user-badge { color: #b9bcc4; }
  .sys-badge { color: #f7768e; }
  .content { color: #e6e7e9; }
  .thinking {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    color: #b9bcc4;
  }
  .dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: #7aa2f7;
    animation: pulse 1.2s ease-in-out infinite;
  }
  .meta { font-size: 11px; color: #6b6f7c; margin-top: 6px; }
  .cursor {
    display: inline-block;
    margin-left: 2px;
    color: #7aa2f7;
    animation: blink 1s steps(2) infinite;
  }
  @keyframes blink { 50% { opacity: 0; } }
  @keyframes pulse {
    0%, 100% { opacity: 0.35; transform: scale(0.8); }
    50% { opacity: 1; transform: scale(1); }
  }
  .tools {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }
  .tool {
    background: #161922;
    border: 1px solid #2f3445;
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    display: inline-flex;
    gap: 6px;
    align-items: center;
  }
  .tool.fail { border-color: #4a2a30; }
  .tool .ok { color: #9ece6a; }
  .tool .err { color: #f7768e; }
</style>
