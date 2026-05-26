<script lang="ts">
  import { page } from "$app/stores";
  const navItems = [
    { href: "/",           icon: "✨", label: "Home" },
    { href: "/assessment", icon: "🔮", label: "診断" },
    { href: "/matches",    icon: "💫", label: "マッチ" },
    { href: "/checkin",    icon: "🌱", label: "今日" },
    { href: "/profile",    icon: "🪬", label: "自分" },
  ];
</script>

<div class="app">
  <main class="main-content">
    <slot />
  </main>
  <nav class="bottom-nav">
    {#each navItems as item}
      {@const active = $page.url.pathname === item.href}
      <a href={item.href} class="nav-item" class:active>
        <span class="nav-icon" class:active-icon={active}>{item.icon}</span>
        <span class="nav-label">{item.label}</span>
        {#if active}<span class="active-dot"></span>{/if}
      </a>
    {/each}
  </nav>
</div>

<style>
  :global(*) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(:root) {
    --bg: #08080f;
    --card: rgba(255,255,255,0.05);
    --border: rgba(255,255,255,0.09);
    --violet: #c084fc;
    --indigo: #818cf8;
  }
  :global(body) {
    font-family: -apple-system, BlinkMacSystemFont, "Hiragino Sans", "Yu Gothic UI", "Segoe UI", sans-serif;
    background: var(--bg);
    color: #f0f0f8;
    min-height: 100dvh;
    overscroll-behavior: none;
    scroll-behavior: smooth;
  }
  :global(a) { color: inherit; text-decoration: none; }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0); }
  }

  .app { display: flex; flex-direction: column; min-height: 100dvh; }
  .main-content {
    flex: 1; overflow-y: auto; padding-bottom: 84px;
    animation: fadeIn 0.2s ease;
  }
  .bottom-nav {
    position: fixed; bottom: 0; left: 0; right: 0;
    display: flex;
    background: rgba(8,8,15,0.92);
    backdrop-filter: blur(20px) saturate(1.5);
    -webkit-backdrop-filter: blur(20px) saturate(1.5);
    border-top: 1px solid rgba(255,255,255,0.07);
    padding-bottom: env(safe-area-inset-bottom, 0);
    z-index: 100;
  }
  .nav-item {
    flex: 1; display: flex; flex-direction: column; align-items: center;
    padding: 10px 4px 8px; text-decoration: none;
    color: rgba(240,240,248,0.38);
    transition: color 0.2s ease;
    position: relative;
  }
  .nav-item.active { color: #c084fc; }
  .nav-icon {
    font-size: 22px; line-height: 1;
    transition: transform 0.2s cubic-bezier(0.34,1.56,0.64,1);
    display: block;
  }
  .active-icon { transform: scale(1.18); }
  .nav-label { font-size: 10px; margin-top: 4px; letter-spacing: 0.03em; font-weight: 500; }
  .active-dot {
    position: absolute; bottom: 3px; left: 50%; transform: translateX(-50%);
    width: 4px; height: 4px; border-radius: 50%;
    background: #c084fc;
    box-shadow: 0 0 6px rgba(192,132,252,0.8);
  }
</style>
