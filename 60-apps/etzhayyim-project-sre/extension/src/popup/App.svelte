<script lang="ts">
  let status = $state<'loading' | 'connected' | 'error'>('loading');
  let version = $state('1.0.0');

  const services = $state([
    { name: 'System Status', status: 'active' as const },
    { name: 'Feedback', status: 'active' as const },
    { name: 'Theme Sync', status: 'active' as const },
  ]);

  $effect(() => {
    status = 'connected';
  });
</script>

<div class="popup">
  <header>
    <h1>SRE Toolbar</h1>
    <span class="version">v{version}</span>
  </header>

  <div class="status-bar">
    <span class="dot" class:connected={status === 'connected'} class:error={status === 'error'}></span>
    <span>{status === 'connected' ? 'Connected' : status === 'error' ? 'Error' : 'Loading...'}</span>
  </div>

  <ul class="services">
    {#each services as svc}
      <li>
        <span class="svc-name">{svc.name}</span>
        <span class="svc-status" class:active={svc.status === 'active'}>{svc.status.toUpperCase()}</span>
      </li>
    {/each}
  </ul>

  <footer>
    <a href="https://sre.etzhayyim.com" target="_blank">sre.etzhayyim.com</a>
  </footer>
</div>

<style>
  .popup {
    width: 280px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: #0f1117;
    color: #e4e4e7;
    padding: 16px;
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  h1 {
    font-size: 16px;
    font-weight: 600;
    margin: 0;
    color: #f4f4f5;
  }
  .version {
    font-size: 11px;
    color: #71717a;
    background: #27272a;
    padding: 2px 6px;
    border-radius: 4px;
  }
  .status-bar {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    margin-bottom: 12px;
    padding: 8px;
    background: #18181b;
    border-radius: 6px;
  }
  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #71717a;
  }
  .dot.connected { background: #22c55e; }
  .dot.error { background: #ef4444; }
  .services {
    list-style: none;
    margin: 0;
    padding: 0;
  }
  .services li {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #27272a;
    font-size: 13px;
  }
  .services li:last-child { border-bottom: none; }
  .svc-status {
    font-size: 10px;
    font-weight: 600;
    padding: 2px 6px;
    border-radius: 4px;
    background: #27272a;
    color: #71717a;
  }
  .svc-status.active {
    background: rgba(34, 197, 94, 0.15);
    color: #22c55e;
  }
  footer {
    margin-top: 12px;
    text-align: center;
  }
  footer a {
    font-size: 12px;
    color: #3b82f6;
    text-decoration: none;
  }
  footer a:hover { text-decoration: underline; }
</style>
