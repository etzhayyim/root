<script lang="ts">
    import '../app.css';
    import { simulation } from '$lib/stores/simulation';
    import { Plane, Cpu, ShoppingCart, TestTube, Globe, CheckCircle2, CircleDashed, TerminalSquare, Loader2 } from 'lucide-svelte';

    let { children } = $props();

    const steps = [
        { id: 'init', label: 'Initialization', icon: TerminalSquare },
        { id: 'design', label: 'Engine CAD & RTL', icon: Cpu },
        { id: 'procure', label: 'Procurement', icon: ShoppingCart },
        { id: 'manufacture_test', label: 'Assembly & Testing', icon: TestTube },
        { id: 'operate', label: 'Digital Twin Flight', icon: Globe }
    ];

    function getStepStatus(stepId: string, currentPhase: string, isProcessing: boolean) {
        const stepIndex = steps.findIndex(s => s.id === stepId);
        const currentIndex = steps.findIndex(s => s.id === currentPhase);
        
        if (stepIndex < currentIndex) return 'completed';
        if (stepIndex === currentIndex) return isProcessing ? 'processing' : 'active';
        return 'pending';
    }
</script>

<div class="flex h-screen w-full bg-[var(--gv2-bg-primary)] text-[var(--gv2-text-primary)]">
    <!-- Sidebar / Pregel Timeline -->
    <aside class="w-80 border-r border-[var(--gv2-border)] bg-[var(--gv2-bg-secondary)] flex flex-col">
        <div class="p-6 border-b border-[var(--gv2-border)] flex items-center gap-3">
            <div class="p-2 bg-[var(--gv2-accent)]/20 rounded-lg">
                <Plane class="h-6 w-6 text-[var(--gv2-accent)]" />
            </div>
            <div>
                <h1 class="font-bold text-lg leading-tight">Itonami (営み)</h1>
                <p class="text-xs text-[var(--gv2-text-tertiary)]">LangGraph Pregel Runtime</p>
            </div>
        </div>

        <div class="flex-1 overflow-y-auto p-6 space-y-6">
            <h2 class="text-xs font-semibold tracking-wider text-[var(--gv2-text-tertiary)] uppercase mb-4">Supersteps</h2>
            
            <div class="space-y-4">
                {#each steps as step, i}
                    {@const status = getStepStatus(step.id, $simulation.phase, $simulation.isProcessing)}
                    <div class="flex items-start gap-4">
                        <div class="relative flex flex-col items-center">
                            <div class="flex h-8 w-8 items-center justify-center rounded-full border-2 
                                {status === 'completed' ? 'border-green-500 bg-green-500/10' : 
                                 status === 'processing' || status === 'active' ? 'border-[var(--gv2-accent)] bg-[var(--gv2-accent)]/10' : 
                                 'border-[var(--gv2-border)] bg-[var(--gv2-bg-tertiary)]'}">
                                {#if status === 'completed'}
                                    <CheckCircle2 class="h-4 w-4 text-green-500" />
                                {:else if status === 'processing'}
                                    <Loader2 class="h-4 w-4 text-[var(--gv2-accent)] animate-spin" />
                                {:else}
                                    <step.icon class="h-4 w-4 {status === 'active' ? 'text-[var(--gv2-accent)]' : 'text-[var(--gv2-text-tertiary)]'}" />
                                {/if}
                            </div>
                            {#if i < steps.length - 1}
                                <div class="w-px h-8 my-1 {status === 'completed' ? 'bg-green-500/50' : 'bg-[var(--gv2-border)]'}"></div>
                            {/if}
                        </div>
                        <div class="pt-1.5 flex-1">
                            <p class="text-sm font-medium {status === 'pending' ? 'text-[var(--gv2-text-tertiary)]' : 'text-[var(--gv2-text-primary)]'}">
                                {step.label}
                            </p>
                            {#if status === 'processing' || status === 'active'}
                                <p class="text-xs text-[var(--gv2-accent)] mt-0.5 animate-pulse">
                                    {status === 'processing' ? 'Executing Node...' : 'Awaiting Action...'}
                                </p>
                            {/if}
                        </div>
                    </div>
                {/each}
            </div>
        </div>

        <div class="p-4 border-t border-[var(--gv2-border)] bg-black/40">
            <h3 class="text-xs font-semibold text-[var(--gv2-text-tertiary)] mb-2 flex items-center gap-2">
                <TerminalSquare class="h-3 w-3" /> Event Log
            </h3>
            <div class="h-48 overflow-y-auto rounded bg-black/60 p-2 font-mono text-[10px] leading-relaxed text-[var(--gv2-text-secondary)]">
                {#each $simulation.log as msg}
                    <div class="mb-1">{msg}</div>
                {/each}
                {#if $simulation.isProcessing}
                    <div class="text-[var(--gv2-accent)] animate-pulse">...</div>
                {/if}
            </div>
        </div>
    </aside>

    <!-- Main Content Area -->
    <main class="flex-1 flex flex-col min-w-0">
        <header class="h-16 border-b border-[var(--gv2-border)] px-6 flex items-center justify-between bg-[var(--gv2-bg-secondary)] shrink-0">
            <div class="flex items-center gap-6 text-sm">
                <div>
                    <span class="text-[var(--gv2-text-tertiary)] mr-2">Project:</span>
                    <span class="font-mono text-[var(--gv2-accent)]">{$simulation.project_id || 'PENDING'}</span>
                </div>
                <div>
                    <span class="text-[var(--gv2-text-tertiary)] mr-2">Model:</span>
                    <span class="font-medium">{$simulation.aircraft_model}</span>
                </div>
                {#if $simulation.icao24_address}
                    <div class="px-2.5 py-1 rounded-md bg-[var(--gv2-accent)]/20 text-[var(--gv2-accent)] font-mono text-xs border border-[var(--gv2-accent)]/30">
                        ICAO: {$simulation.icao24_address}
                    </div>
                {/if}
            </div>
            
            <button 
                onclick={() => simulation.reset()}
                class="text-xs text-[var(--gv2-text-tertiary)] hover:text-white px-3 py-1.5 rounded border border-[var(--gv2-border)] hover:bg-[var(--gv2-bg-tertiary)] transition-colors"
            >
                Reset Simulation
            </button>
        </header>
        
        <div class="flex-1 overflow-auto relative">
            {@render children()}
        </div>
    </main>
</div>
