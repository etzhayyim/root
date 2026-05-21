<script lang="ts">
    import { simulation } from '$lib/stores/simulation';
    import DesignPhase from '$lib/components/phases/DesignPhase.svelte';
    import ProcurePhase from '$lib/components/phases/ProcurePhase.svelte';
    import TestPhase from '$lib/components/phases/TestPhase.svelte';
    import OperatePhase from '$lib/components/phases/OperatePhase.svelte';

    // We will switch the component rendered based on the active phase.
</script>

{#if $simulation.phase === 'init'}
    <div class="h-full flex flex-col items-center justify-center">
        <div class="text-center max-w-md">
            <div class="mb-6 p-4 inline-block rounded-full bg-[var(--gv2-accent)]/10">
                <svg class="h-12 w-12 text-[var(--gv2-accent)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
            </div>
            <h2 class="text-2xl font-bold mb-2">Ready to Start Lifecycle</h2>
            <p class="text-[var(--gv2-text-secondary)] mb-8">
                Initialize the LangGraph Pregel runner to begin the end-to-end design, procurement, testing, and flight operation process for the new engine.
            </p>
            <button 
                onclick={simulation.start}
                disabled={$simulation.isProcessing}
                class="px-8 py-3 rounded-lg bg-[var(--gv2-accent)] text-white font-medium hover:bg-blue-600 disabled:opacity-50 transition-colors"
            >
                Start Simulation Node
            </button>
        </div>
    </div>
{:else if $simulation.phase === 'design'}
    <DesignPhase />
{:else if $simulation.phase === 'procure'}
    <ProcurePhase />
{:else if $simulation.phase === 'manufacture_test'}
    <TestPhase />
{:else if $simulation.phase === 'operate'}
    <OperatePhase />
{/if}
