<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  
  let summaryData: any[] = [];
  let traceData: any[] = [];
  let loading = true;
  let error = '';
  let interval: any;

  async function fetchLPMData() {
    try {
      const [resSummary, resTraces] = await Promise.all([
        fetch('http://localhost:8100/api/lpm'),
        fetch('http://localhost:8100/api/lpm/traces')
      ]);
      if (resSummary.ok && resTraces.ok) {
        summaryData = await resSummary.json();
        traceData = await resTraces.json();
      } else {
        error = 'Failed to fetch data';
      }
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    fetchLPMData();
    interval = setInterval(fetchLPMData, 10000); // refresh every 10s
  });

  onDestroy(() => {
    if (interval) clearInterval(interval);
  });
</script>

<div class="min-h-screen bg-[var(--gv2-bg-primary,#121212)] text-[var(--gv2-text-primary,#ffffff)] p-6">
  <div class="max-w-6xl mx-auto">
    <div class="mb-8 border-b border-[var(--gv2-border,#333)] pb-4">
      <h1 class="text-3xl font-bold flex items-center gap-3">
        <svg class="h-8 w-8 text-[#d4a574]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 12a9 9 0 0 1-9 9m9-9a9 9 0 0 0-9-9m9 9H3m9 9a9 9 0 0 1-9-9m9 9c1.66 0 3-4.03 3-9s-1.34-9-3-9m0 18c-1.66 0-3-4.03-3-9s1.34-9 3-9m-9 9a9 9 0 0 1 9-9" /></svg>
        LangProcessMiner Dashboard
      </h1>
      <p class="text-[var(--gv2-text-muted,#888)] mt-2">
        Real-time LangGraph agent performance & trace monitoring via RisingWave Graph DB.
      </p>
    </div>

    {#if loading && summaryData.length === 0}
      <div class="flex items-center justify-center p-12">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#d4a574]"></div>
      </div>
    {:else if error}
      <div class="p-4 bg-red-900/30 border border-red-500 rounded-xl text-red-200">
        Error: {error}
      </div>
    {:else}
      <!-- SUMMARY CARDS -->
      <h2 class="text-xl font-bold mb-4">Agent Performance Summary</h2>
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
        {#each summaryData as agent}
          <div class="bg-[var(--gv2-bg-secondary,#1f1f1f)] border border-[var(--gv2-border,#333)] rounded-2xl p-5 shadow-lg relative overflow-hidden group">
            <div class="absolute top-0 right-0 p-4 opacity-10">
              <svg class="w-16 h-16" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L2 7l10 5 10-5-10-5zm0 7.5l-10-5v10l10 5 10-5v-10l-10 5z"/></svg>
            </div>
            <h3 class="text-lg font-bold text-[#d4a574] mb-3 relative z-10">{agent.agent_role.toUpperCase()}</h3>
            <div class="grid grid-cols-2 gap-4 relative z-10">
              <div>
                <div class="text-[12px] text-[var(--gv2-text-muted,#888)] uppercase tracking-wider">Total Runs</div>
                <div class="text-2xl font-bold">{agent.total_runs}</div>
              </div>
              <div>
                <div class="text-[12px] text-[var(--gv2-text-muted,#888)] uppercase tracking-wider">Error Rate</div>
                <div class="text-2xl font-bold {agent.error_count > 0 ? 'text-red-400' : 'text-green-400'}">
                  {((agent.error_count / agent.total_runs) * 100).toFixed(1)}%
                </div>
              </div>
              <div>
                <div class="text-[12px] text-[var(--gv2-text-muted,#888)] uppercase tracking-wider">Avg Latency</div>
                <div class="text-2xl font-bold">{agent.avg_duration_sec}s</div>
              </div>
              <div>
                <div class="text-[12px] text-[var(--gv2-text-muted,#888)] uppercase tracking-wider">Total Tokens</div>
                <div class="text-2xl font-bold">{agent.total_tokens_used.toLocaleString()}</div>
              </div>
            </div>
          </div>
        {/each}
      </div>

      <!-- RECENT TRACES -->
      <h2 class="text-xl font-bold mb-4">Recent Agent Traces</h2>
      <div class="bg-[var(--gv2-bg-secondary,#1f1f1f)] border border-[var(--gv2-border,#333)] rounded-2xl overflow-hidden shadow-lg">
        <div class="overflow-x-auto">
          <table class="w-full text-left text-sm whitespace-nowrap">
            <thead class="bg-[#181818] text-[var(--gv2-text-muted,#888)]">
              <tr>
                <th class="px-6 py-4 font-semibold">Time (UTC)</th>
                <th class="px-6 py-4 font-semibold">Agent Role</th>
                <th class="px-6 py-4 font-semibold">Action / Run Name</th>
                <th class="px-6 py-4 font-semibold">Status</th>
                <th class="px-6 py-4 font-semibold">Tokens</th>
                <th class="px-6 py-4 font-semibold w-1/3">Output Rationale</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-[var(--gv2-border,#333)]">
              {#each traceData as trace}
                <tr class="hover:bg-[var(--gv2-bg-hover,#262626)] transition-colors">
                  <td class="px-6 py-4 text-xs font-mono text-[var(--gv2-text-muted,#888)]">
                    {new Date(trace.start_time).toLocaleString()}
                  </td>
                  <td class="px-6 py-4">
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium bg-[#333] text-[#d4a574]">
                      {trace.agent_role.toUpperCase()}
                    </span>
                  </td>
                  <td class="px-6 py-4 font-medium">
                    {trace.run_name}
                  </td>
                  <td class="px-6 py-4">
                    <span class="inline-flex items-center px-2 py-1 rounded text-xs font-medium {trace.status === 'success' ? 'bg-green-900/30 text-green-400' : 'bg-blue-900/30 text-blue-400'}">
                      {trace.status}
                    </span>
                  </td>
                  <td class="px-6 py-4 font-mono">
                    {trace.total_tokens.toLocaleString()}
                  </td>
                  <td class="px-6 py-4">
                    <div class="truncate max-w-md text-xs text-[var(--gv2-text-muted,#888)]" title={trace.output ? JSON.parse(trace.output).rationale : ''}>
                      {#if trace.output}
                        {JSON.parse(trace.output).rationale || 'No rationale extracted'}
                      {:else}
                        Running...
                      {/if}
                    </div>
                  </td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      </div>
    {/if}
  </div>
</div>
