<script lang="ts">
  import type { Conversation } from "./api";
  import { deleteConversation } from "./api";
  import { m } from "../paraglide/messages.js";
  import LanguageSwitcher from "./LanguageSwitcher.svelte";

  let {
    conversations,
    activeConvId,
    onSelect,
    onNew,
    onRefresh,
  }: {
    conversations: Conversation[];
    activeConvId: string;
    onSelect: (convId: string) => void;
    onNew: () => void;
    onRefresh: () => void;
  } = $props();

  async function handleDelete(convId: string, e: Event) {
    e.stopPropagation();
    if (!confirm(m.confirm_delete())) return;
    await deleteConversation(convId, false);
    onRefresh();
    if (activeConvId === convId) onNew();
  }
</script>

<div class="sidebar-inner">
  <button class="new" onclick={onNew} aria-label={m.new_chat()}>{m.new_chat()}</button>
  <ul class="convs">
    {#each conversations as c (c.convId)}
      <li
        class:active={c.convId === activeConvId}
        onclick={() => onSelect(c.convId)}
        onkeydown={(e) => { if (e.key === "Enter") onSelect(c.convId); }}
        role="button"
        tabindex="0"
      >
        <div class="title">{c.title || m.untitled()}</div>
        <div class="meta">{m.msg_count_label({ count: String(c.messageCount) })} · {c.lastMessageAt?.slice(0, 10) ?? ""}</div>
        <button class="del" onclick={(e) => handleDelete(c.convId, e)} aria-label="delete">×</button>
      </li>
    {/each}
    {#if conversations.length === 0}
      <li class="empty">{m.no_conversations()}</li>
    {/if}
  </ul>
  <div class="brand">
    <div>gftd.ai</div>
    <div class="sub">{m.brand_subtitle()}</div>
  </div>
  <LanguageSwitcher />
</div>

<style>
  .sidebar-inner {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 12px 8px;
  }
  .new {
    background: #232735;
    color: #e6e7e9;
    border: 1px solid #2f3445;
    border-radius: 8px;
    padding: 10px;
    cursor: pointer;
    text-align: left;
    margin-bottom: 8px;
    font-size: 14px;
  }
  .new:hover { background: #2a2f40; }
  .convs {
    list-style: none;
    padding: 0;
    margin: 0;
    flex: 1;
    overflow-y: auto;
  }
  .convs li {
    position: relative;
    padding: 8px 28px 8px 10px;
    border-radius: 6px;
    cursor: pointer;
    margin-bottom: 2px;
  }
  .convs li:hover { background: #1d2230; }
  .convs li.active { background: #2a2f40; }
  .convs li.empty {
    color: #6b6f7c;
    font-size: 13px;
    text-align: center;
    padding: 16px 0;
    cursor: default;
  }
  .convs li.empty:hover { background: transparent; }
  .title {
    font-size: 13px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .meta {
    font-size: 11px;
    color: #6b6f7c;
    margin-top: 2px;
  }
  .del {
    position: absolute;
    right: 6px;
    top: 50%;
    transform: translateY(-50%);
    background: transparent;
    border: none;
    color: #6b6f7c;
    cursor: pointer;
    font-size: 16px;
    padding: 2px 6px;
    line-height: 1;
  }
  .del:hover { color: #ff6b6b; }
  .brand {
    padding: 12px 6px 4px;
    font-size: 11px;
    color: #6b6f7c;
    border-top: 1px solid #232735;
  }
  .sub { margin-top: 2px; font-size: 10px; }
</style>
