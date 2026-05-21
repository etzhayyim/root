<script lang="ts">
  import { page } from "$app/stores";
  import { getApiKey, setApiKey } from "$lib/api";
  import { onMount } from "svelte";

  let apiKey = "";
  let showKeyInput = false;

  onMount(() => { apiKey = getApiKey(); });

  function saveKey() {
    setApiKey(apiKey.trim());
    showKeyInput = false;
  }

  const nav = [
    { href: "/",        label: "Incidents" },
    { href: "/scan",    label: "Scan" },
    { href: "/landing", label: "About" },
  ];
</script>

<div class="shell">
  <header>
    <a href="/" class="brand">
      <span class="logo">守</span>
      <span class="name">mamoru</span>
      <span class="tag">secret guardian</span>
    </a>
    <nav>
      {#each nav as item}
        <a href={item.href} class:active={$page.url.pathname === item.href}>{item.label}</a>
      {/each}
    </nav>
    <button class="key-btn" on:click={() => (showKeyInput = !showKeyInput)} title="API Key">
      {getApiKey() ? "🔑" : "⚠ key"}
    </button>
  </header>

  {#if showKeyInput}
    <div class="key-bar">
      <input
        type="password"
        placeholder="sk_live_..."
        bind:value={apiKey}
        on:keydown={(e) => e.key === "Enter" && saveKey()}
      />
      <button on:click={saveKey}>Save</button>
    </div>
  {/if}

  <main>
    <slot />
  </main>
</div>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(:root) {
    --bg:        #0d1117;
    --surface:   #161b22;
    --border:    #30363d;
    --text:      #e6edf3;
    --muted:     #8b949e;
    --red:       #f85149;
    --orange:    #d29922;
    --yellow:    #e3b341;
    --green:     #3fb950;
    --blue:      #388bfd;
    --purple:    #bc8cff;
    --accent:    #f85149;
  }
  :global(body) {
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, "Segoe UI", "Helvetica Neue", sans-serif;
    font-size: 14px;
    line-height: 1.5;
  }
  :global(a) { color: inherit; text-decoration: none; }
  :global(button) { cursor: pointer; }

  .shell { display: flex; flex-direction: column; min-height: 100dvh; }

  header {
    display: flex;
    align-items: center;
    gap: 24px;
    padding: 0 24px;
    height: 56px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
    position: sticky; top: 0; z-index: 100;
  }

  .brand {
    display: flex; align-items: center; gap: 8px;
    font-weight: 600;
  }
  .logo {
    font-size: 22px; color: var(--red);
    line-height: 1;
  }
  .name { font-size: 16px; font-weight: 700; letter-spacing: -0.3px; }
  .tag { font-size: 11px; color: var(--muted); font-weight: 400; }

  nav { display: flex; gap: 4px; flex: 1; }
  nav a {
    padding: 6px 12px;
    border-radius: 6px;
    color: var(--muted);
    font-size: 13px;
    transition: color 0.15s, background 0.15s;
  }
  nav a:hover { color: var(--text); background: rgba(255,255,255,0.06); }
  nav a.active { color: var(--text); background: rgba(255,255,255,0.08); font-weight: 500; }

  .key-btn {
    margin-left: auto;
    background: transparent;
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 4px 10px;
    color: var(--muted);
    font-size: 12px;
    transition: border-color 0.15s, color 0.15s;
  }
  .key-btn:hover { border-color: var(--blue); color: var(--text); }

  .key-bar {
    display: flex;
    gap: 8px;
    padding: 8px 24px;
    background: var(--surface);
    border-bottom: 1px solid var(--border);
  }
  .key-bar input {
    flex: 1; max-width: 400px;
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 6px 10px;
    color: var(--text);
    font-size: 13px;
    font-family: monospace;
  }
  .key-bar input:focus { outline: none; border-color: var(--blue); }
  .key-bar button {
    background: var(--blue);
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 6px 14px;
    font-size: 13px;
    font-weight: 500;
  }

  main { flex: 1; padding: 24px; max-width: 1200px; width: 100%; margin: 0 auto; }
</style>
