<script lang="ts">
  import { onMount } from "svelte";
  import Sidebar from "./lib/Sidebar.svelte";
  import ChatPanel from "./lib/ChatPanel.svelte";
  import SodaiWizard from "./lib/SodaiWizard.svelte";
  import Header from "./lib/Header.svelte";
  import { listConversations, type Conversation } from "./lib/api";
  import { whoami, type ViewerState } from "./lib/auth";
  import { initLocalIdentity } from "./lib/signal-store";

  type Mode = "chat" | "sodai";
  let mode = $state<Mode>("chat");

  let conversations = $state<Conversation[]>([]);
  let activeConvId = $state<string>("");
  let viewerState = $state<ViewerState>({ status: "loading" });

  async function refreshConversations() {
    try {
      conversations = await listConversations();
    } catch (e) {
      console.error("[chat-shell] listConversations failed", e);
      conversations = [];
    }
  }

  function onSelectConv(convId: string) {
    activeConvId = convId;
  }

  function onNewConv() {
    activeConvId = "";
  }

  function onConversationUpdated() {
    refreshConversations();
  }

  onMount(async () => {
    // Resolve the viewer first so the chat-agent can attribute the
    // anonymous-vs-signed-in conversation list correctly. whoami()
    // never throws — it returns ViewerState directly.
    viewerState = await whoami();
    if (viewerState.status === "signed-in") {
      // Ensure a local Signal identity exists for ephemeral encryption.
      // generateIdentity() is idempotent (hasIdentity check inside).
      void initLocalIdentity(viewerState.viewer.did);
    }
    refreshConversations();
  });
</script>

<Header viewer={viewerState} />
<nav class="modetabs">
  <button class:active={mode === "chat"} onclick={() => (mode = "chat")}>チャット</button>
  <button class:active={mode === "sodai"} onclick={() => (mode = "sodai")}>粗大ごみ申請</button>
</nav>
{#if mode === "chat"}
  <div class="shell">
    <aside class="sidebar">
      <Sidebar
        {conversations}
        {activeConvId}
        onSelect={onSelectConv}
        onNew={onNewConv}
        onRefresh={refreshConversations}
      />
    </aside>
    <main class="main">
      <ChatPanel
        bind:convId={activeConvId}
        did={viewerState.status === "signed-in" ? viewerState.viewer.did : ""}
        onTurnComplete={onConversationUpdated}
      />
    </main>
  </div>
{:else}
  <main class="main sodai-main">
    <SodaiWizard />
  </main>
{/if}

<style>
  :global(html, body) {
    margin: 0;
    padding: 0;
    height: 100%;
    background: #0f1115;
    color: #e6e7e9;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans",
                 "Noto Sans JP", sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  :global(*) { box-sizing: border-box; }
  :global(#app) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  .modetabs {
    display: flex;
    gap: 4px;
    padding: 6px 12px;
    background: #12141a;
    border-bottom: 1px solid #232735;
    flex: 0 0 auto;
  }
  .modetabs button {
    background: none;
    border: 1px solid transparent;
    border-radius: 6px;
    color: #8a8e99;
    padding: 5px 14px;
    font-size: 13px;
    cursor: pointer;
    font-family: inherit;
  }
  .modetabs button:hover { color: #e6e7e9; }
  .modetabs button.active {
    background: #1d2230;
    border-color: #2f3445;
    color: #e6e7e9;
  }
  .shell {
    display: grid;
    grid-template-columns: 280px 1fr;
    flex: 1 1 auto;
    min-height: 0;
  }
  .sodai-main { flex: 1 1 auto; min-height: 0; }
  .sidebar {
    background: #161922;
    border-right: 1px solid #232735;
    overflow-y: auto;
  }
  .main {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }
  @media (max-width: 720px) {
    .shell { grid-template-columns: 1fr; }
    .sidebar { display: none; }
  }
</style>
