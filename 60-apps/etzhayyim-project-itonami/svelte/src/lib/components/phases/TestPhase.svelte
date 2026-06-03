<script lang="ts">
    import { simulation } from '$lib/stores/simulation';
    import { onMount, onDestroy } from 'svelte';
    import * as THREE from 'three';

    let metrics = $derived($simulation.engine_test_metrics);
    let robots = $derived($simulation.assembly_robot_ids);
    let container = $state<HTMLDivElement>();

    $effect(() => {
        if (!container || !metrics) return;
        
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(6, 4, 6);
        camera.lookAt(0, 0, 0);

        const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
        renderer.setSize(container.clientWidth, container.clientHeight);
        renderer.setPixelRatio(window.devicePixelRatio);
        container.appendChild(renderer.domElement);

        const light = new THREE.DirectionalLight(0xffffff, 1.5);
        light.position.set(10, 10, 10);
        scene.add(light);
        scene.add(new THREE.AmbientLight(0xffffff, 0.5));

        const group = new THREE.Group();
        
        const coreGeo = new THREE.CylinderGeometry(1, 1, 4, 32);
        // Emissive material for heat glow
        const coreMat = new THREE.MeshStandardMaterial({ 
            color: 0x334155, 
            metalness: 0.8, 
            roughness: 0.2,
            emissive: 0xff3300,
            emissiveIntensity: 0
        });
        const core = new THREE.Mesh(coreGeo, coreMat);
        group.add(core);
        
        const cowlGeo = new THREE.CylinderGeometry(1.5, 1.5, 1, 32);
        const cowlMat = new THREE.MeshStandardMaterial({ color: 0x1e293b, metalness: 0.5, roughness: 0.5, transparent: true, opacity: 0.8 });
        const cowl = new THREE.Mesh(cowlGeo, cowlMat);
        cowl.position.set(0, 1.5, 0);
        group.add(cowl);
        
        const spinnerGeo = new THREE.ConeGeometry(0, 0.4, 0.5, 32);
        const spinnerMat = new THREE.MeshStandardMaterial({ color: 0x94a3b8, metalness: 0.9, roughness: 0.1 });
        const spinner = new THREE.Mesh(spinnerGeo, spinnerMat);
        spinner.position.set(0, 2, 0);
        group.add(spinner);

        // Test stand structure
        const standGeo = new THREE.BoxGeometry(3, 1, 3);
        const standMat = new THREE.MeshStandardMaterial({ color: 0x111827 });
        const stand = new THREE.Mesh(standGeo, standMat);
        stand.position.set(0, -2.5, 0);
        scene.add(stand);

        scene.add(group);
        
        const grid = new THREE.GridHelper(10, 10, 0x334155, 0x1e293b);
        grid.position.set(0, -2, 0);
        scene.add(grid);

        let animationFrameId: number;
        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            
            // Fast rotation to simulate running
            group.rotation.y += 0.2;
            
            // Physics Simulation: Heat Glow
            if (metrics) {
                // Map 20-1600 C to 0-2 emissive intensity
                const heatIntensity = Math.max(0, (metrics.max_temp_celsius - 500) / 500);
                coreMat.emissiveIntensity = Math.min(2.0, heatIntensity);
                
                // Physics Simulation: Vibration Shake
                if (metrics.vibration_hz > 5) {
                    const shakeAmt = (metrics.vibration_hz / 50);
                    group.position.x = (Math.random() - 0.5) * shakeAmt;
                    group.position.z = (Math.random() - 0.5) * shakeAmt;
                } else {
                    group.position.set(0,0,0);
                }
            }

            renderer.render(scene, camera);
        };
        animate();

        const handleResize = () => {
            if (!container) return;
            camera.aspect = container.clientWidth / container.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(container.clientWidth, container.clientHeight);
        };
        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            cancelAnimationFrame(animationFrameId);
            coreMat.dispose();
            cowlMat.dispose();
            spinnerMat.dispose();
            coreGeo.dispose();
            cowlGeo.dispose();
            spinnerGeo.dispose();
            renderer.dispose();
            if (container && renderer.domElement.parentNode === container) {
                container.removeChild(renderer.domElement);
            }
        };
    });
</script>

<div class="h-full flex flex-col">
    <div class="p-6 bg-[var(--gv2-bg-primary)] border-b border-[var(--gv2-border)] flex items-center justify-between shrink-0">
        <h2 class="text-xl font-bold flex items-center gap-3">
            <span class="p-1.5 rounded bg-orange-500/20 text-orange-500">
                <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" /></svg>
            </span>
            Physical Testing & Assembly
        </h2>
        
        <button 
            onclick={simulation.runOperate}
            disabled={$simulation.isProcessing || !metrics?.passed_certification}
            class="px-6 py-2 rounded-lg bg-[var(--gv2-accent)] text-white font-medium disabled:opacity-50 hover:bg-blue-600 transition-colors"
        >
            Commission Aircraft
        </button>
    </div>

    {#if !metrics}
        <div class="flex-1 flex items-center justify-center">
            <button 
                onclick={simulation.runTest}
                disabled={$simulation.isProcessing}
                class="px-6 py-2 rounded border border-[var(--gv2-accent)] text-[var(--gv2-accent)] hover:bg-[var(--gv2-accent)]/10 disabled:opacity-50"
            >
                Run Physical Test Simulation
            </button>
        </div>
    {:else}
        <div class="flex-1 flex relative">
            <!-- 3D Canvas (Left Side) -->
            <div class="flex-1 relative bg-black border-r border-[var(--gv2-border)]">
                <div bind:this={container} class="absolute inset-0 w-full h-full"></div>
                <div class="absolute bottom-4 left-4 text-xs text-[var(--gv2-text-tertiary)] font-mono">
                    Live Physics Sim: Core Heat & Vibration Active
                </div>
            </div>

            <!-- Metrics Sidebar (Right Side) -->
            <div class="w-96 bg-[var(--gv2-bg-secondary)] overflow-y-auto p-6 space-y-6">
                <div>
                    <h3 class="text-xs font-semibold uppercase tracking-wider text-[var(--gv2-text-tertiary)] mb-4">150-Hour Endurance Test</h3>
                    <div class="space-y-4">
                        <div class="p-4 rounded-xl bg-[var(--gv2-bg-primary)] border border-[var(--gv2-border)]">
                            <div class="flex justify-between items-start mb-2">
                                <p class="text-sm text-[var(--gv2-text-secondary)]">Max Core Temp</p>
                                <span class="text-xs text-[var(--gv2-text-tertiary)]">Limit: 1600°C</span>
                            </div>
                            <p class="text-2xl font-bold {metrics.max_temp_celsius > 1550 ? 'text-red-500' : 'text-orange-500'}">
                                {metrics.max_temp_celsius.toFixed(1)}<span class="text-sm font-normal text-[var(--gv2-text-tertiary)] ml-1">°C</span>
                            </p>
                            <div class="mt-2 w-full bg-[var(--gv2-bg-tertiary)] h-1 rounded-full overflow-hidden">
                                <div class="bg-orange-500 h-full" style="width: {(metrics.max_temp_celsius / 1600) * 100}%"></div>
                            </div>
                        </div>
                        
                        <div class="p-4 rounded-xl bg-[var(--gv2-bg-primary)] border border-[var(--gv2-border)]">
                            <div class="flex justify-between items-start mb-2">
                                <p class="text-sm text-[var(--gv2-text-secondary)]">Vibration</p>
                                <span class="text-xs text-[var(--gv2-text-tertiary)]">Limit: 25.0 Hz</span>
                            </div>
                            <p class="text-2xl font-bold {metrics.vibration_hz > 20 ? 'text-red-500' : 'text-yellow-500'}">
                                {metrics.vibration_hz.toFixed(2)}<span class="text-sm font-normal text-[var(--gv2-text-tertiary)] ml-1">Hz</span>
                            </p>
                            <div class="mt-2 w-full bg-[var(--gv2-bg-tertiary)] h-1 rounded-full overflow-hidden">
                                <div class="bg-yellow-500 h-full" style="width: {(metrics.vibration_hz / 25) * 100}%"></div>
                            </div>
                        </div>
                        
                        <div class="p-4 rounded-xl bg-[var(--gv2-bg-primary)] border border-[var(--gv2-border)]">
                            <p class="text-sm text-[var(--gv2-text-secondary)] mb-1">Fuel Efficiency</p>
                            <p class="text-xl font-bold text-green-500">
                                {metrics.fuel_flow_kg_s.toFixed(3)}<span class="text-sm font-normal text-[var(--gv2-text-tertiary)] ml-1">kg/s</span>
                            </p>
                        </div>
                        
                        <div class="p-4 rounded-xl bg-[var(--gv2-bg-primary)] border border-[var(--gv2-border)]">
                            <p class="text-sm text-[var(--gv2-text-secondary)] mb-1">NOx Emissions (Tier 4)</p>
                            <p class="text-xl font-bold text-green-500">
                                {metrics.emission_nox_ppm.toFixed(1)}<span class="text-sm font-normal text-[var(--gv2-text-tertiary)] ml-1">ppm</span>
                            </p>
                        </div>
                    </div>
                </div>

                {#if metrics.passed_certification}
                    <div class="pt-6 border-t border-[var(--gv2-border)]">
                        <div class="flex items-center gap-2 text-green-500 font-bold mb-4">
                            <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z" /></svg>
                            Flight Certified
                        </div>
                        
                        <p class="text-sm text-[var(--gv2-text-secondary)] mb-2">Active Robotic Assembly</p>
                        <ul class="space-y-2">
                            {#each robots || [] as robot}
                                <li class="flex items-center gap-2 text-xs font-mono">
                                    <div class="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
                                    {robot}
                                </li>
                            {/each}
                        </ul>
                    </div>
                {/if}
            </div>
        </div>
    {/if}
</div>