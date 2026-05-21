<script lang="ts">
    import { simulation } from '$lib/stores/simulation';
    import { onMount, onDestroy } from 'svelte';
    import maplibregl from 'maplibre-gl';
    import 'maplibre-gl/dist/maplibre-gl.css';

    let mapContainer: HTMLElement;
    let map: maplibregl.Map;
    let marker: maplibregl.Marker;

    let telemetry = $derived($simulation.telemetry || []);
    let currentState = $derived($simulation.flight_state);

    onMount(() => {
        map = new maplibregl.Map({
            container: mapContainer,
            style: 'https://basemaps.cartocdn.com/gl/dark-matter-gl-style/style.json', // Simple dark style
            center: [139.7811, 35.5494], // HND Airport
            zoom: 12,
            pitch: 45
        });

        const el = document.createElement('div');
        el.className = 'w-4 h-4 bg-[var(--gv2-accent)] rounded-full shadow-[0_0_10px_#3b82f6] border-2 border-white';
        marker = new maplibregl.Marker(el)
            .setLngLat([139.7811, 35.5494])
            .addTo(map);
    });

    onDestroy(() => {
        if (map) map.remove();
    });

    // Simulate flight movement based on telemetry array length
    $effect(() => {
        if (map && marker && telemetry.length > 0) {
            const step = telemetry.length;
            
            let lng = 139.7811;
            let lat = 35.5494;
            let zoom = 12;

            if (step === 2) {
                // Climb
                lng = 139.85;
                lat = 35.45;
                zoom = 10;
            } else if (step === 3) {
                // Cruise
                lng = 139.2;
                lat = 34.8;
                zoom = 8;
            }

            marker.setLngLat([lng, lat]);
            map.flyTo({ center: [lng, lat], zoom, speed: 0.5 });
        }
    });
</script>

<div class="h-full flex flex-col relative">
    <!-- Map Container -->
    <div bind:this={mapContainer} class="flex-1 w-full bg-black"></div>

    <!-- Telemetry Overlay -->
    <div class="absolute top-6 left-6 w-80 bg-[var(--gv2-bg-primary)]/90 backdrop-blur-md border border-[var(--gv2-border)] rounded-xl shadow-2xl p-5">
        <h3 class="text-sm font-bold flex items-center gap-2 mb-4">
            <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
            Live Telemetry (Digital Twin)
        </h3>

        {#if telemetry.length === 0}
            <div class="text-center py-6">
                <button 
                    onclick={simulation.runOperate}
                    disabled={$simulation.isProcessing}
                    class="px-6 py-2 rounded border border-[var(--gv2-accent)] text-[var(--gv2-accent)] hover:bg-[var(--gv2-accent)]/10 disabled:opacity-50 text-sm"
                >
                    Start Flight Sim
                </button>
            </div>
        {:else}
            {@const current = telemetry[telemetry.length - 1]}
            <div class="space-y-4">
                <div>
                    <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Status</p>
                    <p class="font-mono text-[var(--gv2-accent)] text-lg font-bold">{currentState}</p>
                </div>
                
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Altitude</p>
                        <p class="font-mono text-xl">{current.alt} <span class="text-xs text-[var(--gv2-text-secondary)]">ft</span></p>
                    </div>
                    <div>
                        <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Speed</p>
                        <p class="font-mono text-xl">{current.spd} <span class="text-xs text-[var(--gv2-text-secondary)]">kts</span></p>
                    </div>
                </div>

                <div class="mt-4 pt-4 border-t border-[var(--gv2-border)]">
                    <p class="text-xs text-[var(--gv2-text-tertiary)] mb-2">Flight History</p>
                    <div class="space-y-1">
                        {#each telemetry as t}
                            <div class="flex justify-between text-xs font-mono text-[var(--gv2-text-secondary)]">
                                <span>{t.thrust}</span>
                                <span>{t.alt}ft / {t.spd}kts</span>
                            </div>
                        {/each}
                    </div>
                </div>
            </div>
        {/if}
    </div>
</div>
