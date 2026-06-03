<script lang="ts">
    import { simulation } from '$lib/stores/simulation';
    
    let bom = $derived($simulation.unspsc_bom);
    let suppliers = $derived($simulation.isic_suppliers);
</script>

<div class="h-full p-8 max-w-5xl mx-auto flex flex-col gap-8">
    <div class="flex items-center justify-between">
        <h2 class="text-2xl font-bold flex items-center gap-3">
            <span class="p-2 rounded bg-green-500/20 text-green-500">
                <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" /></svg>
            </span>
            UNSPSC & ISIC Procurement
        </h2>
        
        <button 
            onclick={simulation.runTest}
            disabled={$simulation.isProcessing || !bom}
            class="px-6 py-2.5 rounded-lg bg-[var(--gv2-accent)] text-white font-medium disabled:opacity-50 hover:bg-blue-600 transition-colors"
        >
            Execute Manufacturing & Testing
        </button>
    </div>

    {#if !bom}
        <div class="p-12 border-2 border-dashed border-[var(--gv2-border)] rounded-xl flex flex-col items-center justify-center text-center">
            <p class="text-[var(--gv2-text-secondary)] mb-4">Awaiting procurement node execution.</p>
            <button 
                onclick={simulation.runProcure}
                disabled={$simulation.isProcessing}
                class="px-6 py-2 rounded border border-[var(--gv2-accent)] text-[var(--gv2-accent)] hover:bg-[var(--gv2-accent)]/10 disabled:opacity-50"
            >
                Run Procurement Superstep
            </button>
        </div>
    {:else}
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <!-- BOM Table -->
            <div class="flex flex-col gap-4">
                <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--gv2-text-tertiary)]">Bill of Materials (UNSPSC)</h3>
                <div class="rounded-xl border border-[var(--gv2-border)] overflow-hidden bg-[var(--gv2-bg-secondary)]">
                    <table class="w-full text-sm text-left">
                        <thead class="bg-[var(--gv2-bg-tertiary)] text-[var(--gv2-text-secondary)] border-b border-[var(--gv2-border)]">
                            <tr>
                                <th class="px-4 py-3 font-medium">Code</th>
                                <th class="px-4 py-3 font-medium">Description</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-[var(--gv2-border)]">
                            {#each bom as item}
                                {@const [code, desc] = item.split(' (')}
                                <tr class="hover:bg-[var(--gv2-bg-tertiary)]/50 transition-colors">
                                    <td class="px-4 py-3 font-mono text-[var(--gv2-accent)]">{code.replace('UNSPSC ', '')}</td>
                                    <td class="px-4 py-3 text-[var(--gv2-text-primary)]">{desc.replace(')', '')}</td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Suppliers Table -->
            <div class="flex flex-col gap-4">
                <h3 class="text-sm font-semibold uppercase tracking-wider text-[var(--gv2-text-tertiary)]">Matched Suppliers (ISIC)</h3>
                <div class="rounded-xl border border-[var(--gv2-border)] overflow-hidden bg-[var(--gv2-bg-secondary)]">
                    <table class="w-full text-sm text-left">
                        <thead class="bg-[var(--gv2-bg-tertiary)] text-[var(--gv2-text-secondary)] border-b border-[var(--gv2-border)]">
                            <tr>
                                <th class="px-4 py-3 font-medium">Supplier Name</th>
                                <th class="px-4 py-3 font-medium">ISIC Classification</th>
                            </tr>
                        </thead>
                        <tbody class="divide-y divide-[var(--gv2-border)]">
                            {#each suppliers || [] as supplier}
                                {@const [code, desc] = supplier.isic.split(' (')}
                                <tr class="hover:bg-[var(--gv2-bg-tertiary)]/50 transition-colors">
                                    <td class="px-4 py-3 font-medium">{supplier.name}</td>
                                    <td class="px-4 py-3">
                                        <div class="flex items-center gap-2">
                                            <span class="px-1.5 py-0.5 rounded bg-[var(--gv2-bg-primary)] border border-[var(--gv2-border)] font-mono text-xs">{code}</span>
                                            <span class="text-[var(--gv2-text-secondary)] text-xs">{desc.replace(')', '')}</span>
                                        </div>
                                    </td>
                                </tr>
                            {/each}
                        </tbody>
                    </table>
                </div>
                
                <div class="mt-4 p-4 rounded-xl bg-green-500/10 border border-green-500/20 flex items-start gap-3">
                    <svg class="w-5 h-5 text-green-500 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" /></svg>
                    <div>
                        <h4 class="text-sm font-medium text-green-400">CAB Approval Passed</h4>
                        <p class="text-xs text-green-500/70 mt-1">All dual-use export controls and risk tags have been reviewed and approved automatically by the LangGraph agent.</p>
                    </div>
                </div>
            </div>
        </div>
    {/if}
</div>
