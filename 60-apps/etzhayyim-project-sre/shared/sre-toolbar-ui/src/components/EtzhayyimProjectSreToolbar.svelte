<script lang="ts">
  type ComponentStatus = 'healthy' | 'degraded' | 'error';

  type ToolbarComponent = {
    id: string;
    name: string;
    status: ComponentStatus;
  };

  type FeedbackPayload = {
    content: string;
    'page_url': string;
    'component_id': string;
  };

  let {
    pageUrl,
    title = 'SRE Toolbar',
    componentId = 'etzhayyim-project-sre-toolbar',
    components = [
      { id: 'pubsub', name: 'NATS JetStream', status: 'healthy' },
      { id: 'statestore', name: 'PostgreSQL', status: 'healthy' },
      { id: 'cache', name: 'Redis Cache', status: 'healthy' },
      { id: 'legacy-runtime', name: 'App runtime', status: 'healthy' }
    ] as ToolbarComponent[],
    onSubmitFeedback
  } = $props<{
    pageUrl: string;
    title?: string;
    componentId?: string;
    components?: ToolbarComponent[];
    onSubmitFeedback?: (payload: FeedbackPayload) => Promise<boolean>;
  }>();

  let isMinimized = $state(true);
  let activeTab = $state<'status' | 'feedback' | 'perf'>('status');

  let feedbackContent = $state('');
  let feedbackStatus = $state<'idle' | 'sending' | 'sent'>('idle');

  let vitals = $state({
    lcp: 0,
    cls: 0,
    ttfb: 0,
    fid: 0
  });

  $effect(() => {
    try {
      new PerformanceObserver((list) => {
        const entries = list.getEntries();
        if (entries.length > 0) {
          vitals.lcp = Math.round(entries[entries.length - 1].startTime);
        }
      }).observe({ type: 'largest-contentful-paint', buffered: true });

      const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
      if (nav) vitals.ttfb = Math.round(nav.responseStart - nav.requestStart);
    } catch {
      // PerformanceObserver is unavailable in some contexts.
    }
  });

  async function submitFeedback() {
    if (!feedbackContent.trim() || !onSubmitFeedback) return;
    feedbackStatus = 'sending';

    try {
      const ok = await onSubmitFeedback({
        content: feedbackContent,
        'page_url': pageUrl,
        'component_id': componentId
      });

      if (!ok) {
        feedbackStatus = 'idle';
        return;
      }

      feedbackStatus = 'sent';
      feedbackContent = '';
      setTimeout(() => {
        feedbackStatus = 'idle';
      }, 2000);
    } catch {
      feedbackStatus = 'idle';
    }
  }

  function statusColor(status: ComponentStatus) {
    if (status === 'healthy') return '#22c55e';
    if (status === 'degraded') return '#f59e0b';
    return '#ef4444';
  }
</script>

{#if isMinimized}
  <button class="trigger" onclick={() => (isMinimized = false)}>SRE</button>
{:else}
  <div class="panel">
    <div class="header">
      <span class="title">{title}</span>
      <button class="close" onclick={() => (isMinimized = true)}>_</button>
    </div>

    <nav class="tabs">
      <button class:active={activeTab === 'status'} onclick={() => (activeTab = 'status')}>Status</button>
      <button class:active={activeTab === 'feedback'} onclick={() => (activeTab = 'feedback')}>Feedback</button>
      <button class:active={activeTab === 'perf'} onclick={() => (activeTab = 'perf')}>Perf</button>
    </nav>

    <div class="content">
      {#if activeTab === 'status'}
        <ul class="component-list">
          {#each components as component}
            <li>
              <span class="dot" style={`background:${statusColor(component.status)}`}></span>
              <span class="comp-name">{component.name}</span>
              <span class="comp-status">{component.status}</span>
            </li>
          {/each}
        </ul>
      {:else if activeTab === 'feedback'}
        <textarea bind:value={feedbackContent} placeholder="Report an issue or suggestion..." rows="3"></textarea>
        <button class="submit-btn" onclick={submitFeedback} disabled={feedbackStatus === 'sending' || !onSubmitFeedback}>
          {feedbackStatus === 'sending' ? 'Sending...' : feedbackStatus === 'sent' ? 'Sent' : 'Submit'}
        </button>
      {:else}
        <div class="vitals">
          <div class="vital">
            <span class="vital-label">LCP</span>
            <span class="vital-value">{vitals.lcp}ms</span>
          </div>
          <div class="vital">
            <span class="vital-label">TTFB</span>
            <span class="vital-value">{vitals.ttfb}ms</span>
          </div>
          <div class="vital">
            <span class="vital-label">CLS</span>
            <span class="vital-value">{vitals.cls.toFixed(3)}</span>
          </div>
          <div class="vital">
            <span class="vital-label">FID</span>
            <span class="vital-value">{vitals.fid}ms</span>
          </div>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .trigger {
    background: #18181b;
    color: #3b82f6;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 700;
    cursor: pointer;
    letter-spacing: 0.05em;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4);
  }
  .trigger:hover {
    background: #27272a;
  }

  .panel {
    width: 300px;
    background: rgba(15, 17, 23, 0.95);
    backdrop-filter: blur(12px);
    border: 1px solid #27272a;
    border-radius: 12px;
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.5);
    overflow: hidden;
    color: #e4e4e7;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    font-size: 13px;
  }

  .header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 14px;
    border-bottom: 1px solid #27272a;
  }

  .title {
    font-weight: 600;
    font-size: 14px;
    color: #f4f4f5;
  }

  .close {
    background: none;
    border: none;
    color: #71717a;
    cursor: pointer;
    font-size: 16px;
    padding: 0 4px;
  }

  .close:hover {
    color: #e4e4e7;
  }

  .tabs {
    display: flex;
    border-bottom: 1px solid #27272a;
  }

  .tabs button {
    flex: 1;
    background: none;
    border: none;
    color: #71717a;
    font-size: 12px;
    padding: 8px 0;
    cursor: pointer;
    border-bottom: 2px solid transparent;
  }

  .tabs button.active {
    color: #3b82f6;
    border-bottom-color: #3b82f6;
  }

  .content {
    padding: 12px 14px;
    max-height: 240px;
    overflow-y: auto;
  }

  .component-list {
    list-style: none;
    margin: 0;
    padding: 0;
  }

  .component-list li {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 0;
    border-bottom: 1px solid #1e1e22;
  }

  .component-list li:last-child {
    border-bottom: none;
  }

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .comp-name {
    flex: 1;
  }

  .comp-status {
    font-size: 11px;
    color: #71717a;
    text-transform: uppercase;
  }

  textarea {
    width: 100%;
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 6px;
    color: #e4e4e7;
    padding: 8px;
    font-size: 12px;
    resize: none;
  }

  textarea::placeholder {
    color: #52525b;
  }

  .submit-btn {
    width: 100%;
    margin-top: 8px;
    background: #3b82f6;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 8px;
    font-size: 12px;
    cursor: pointer;
  }

  .submit-btn:hover {
    background: #2563eb;
  }

  .submit-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .vitals {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .vital {
    background: #18181b;
    border-radius: 6px;
    padding: 10px;
    text-align: center;
  }

  .vital-label {
    display: block;
    font-size: 11px;
    color: #71717a;
    margin-bottom: 4px;
    font-weight: 600;
  }

  .vital-value {
    font-size: 16px;
    font-weight: 700;
    color: #f4f4f5;
  }
</style>
