<script lang="ts">
  import { signIn, signOut, shortLabel, type ViewerState } from "./auth";
  import AppLauncher from "./AppLauncher.svelte";

  let { viewer }: { viewer: ViewerState } = $props();

  let busy = $state(false);

  async function onSignIn() {
    if (busy) return;
    busy = true;
    try { await signIn(); } finally { busy = false; }
  }
  async function onSignOut() {
    if (busy) return;
    busy = true;
    try { await signOut(); } finally { busy = false; }
  }
</script>

<header class="topbar">
  <div class="left">
    <AppLauncher />
    <div class="brand">gftd.ai</div>
  </div>
  <div class="auth">
    {#if viewer.status === "loading"}
      <span class="muted">…</span>
    {:else if viewer.status === "signed-in"}
      <span class="handle" title={viewer.viewer.did}>{shortLabel(viewer.viewer)}</span>
      <button type="button" onclick={onSignOut} disabled={busy}>Sign out</button>
    {:else if viewer.status === "error"}
      <span class="muted" title={viewer.message}>auth offline</span>
      <button type="button" onclick={onSignIn} disabled={busy}>Sign in</button>
    {:else}
      <button type="button" class="primary" onclick={onSignIn} disabled={busy}>
        Sign in
      </button>
    {/if}
  </div>
</header>

<style>
  .topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    height: 44px;
    background: #161922;
    border-bottom: 1px solid #232735;
    flex: 0 0 auto;
  }
  .left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  .brand {
    font-weight: 600;
    letter-spacing: 0.02em;
    color: #e6e7e9;
  }
  .auth {
    display: flex;
    gap: 8px;
    align-items: center;
  }
  .handle {
    font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
    font-size: 12px;
    color: #b6b9c2;
    max-width: 240px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .muted {
    color: #8a8e99;
    font-size: 12px;
  }
  button {
    background: #232735;
    color: #e6e7e9;
    border: 1px solid #2e3343;
    border-radius: 6px;
    padding: 4px 12px;
    font-size: 13px;
    cursor: pointer;
  }
  button:hover:not(:disabled) {
    background: #2a3044;
  }
  button.primary {
    background: #3b6cf6;
    border-color: #3b6cf6;
    color: #fff;
  }
  button.primary:hover:not(:disabled) {
    background: #4978ff;
  }
  button:disabled {
    opacity: 0.5;
    cursor: default;
  }
</style>
