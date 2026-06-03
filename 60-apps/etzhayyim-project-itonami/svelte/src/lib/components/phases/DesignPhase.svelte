<script lang="ts">
    import { simulation } from '$lib/stores/simulation';
    import { onMount, onDestroy } from 'svelte';
    import * as THREE from 'three';

    let design = $derived($simulation.engine_design);
    let container = $state<HTMLDivElement>();

    $effect(() => {
        if (!container || !design) return;
        
        const scene = new THREE.Scene();
        const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.1, 100);
        camera.position.set(5, 3, 5);
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
        const coreMat = new THREE.MeshStandardMaterial({ color: 0x334155, metalness: 0.8, roughness: 0.2 });
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

        scene.add(group);
        
        const grid = new THREE.GridHelper(10, 10, 0x334155, 0x1e293b);
        grid.position.set(0, -2, 0);
        scene.add(grid);

        let animationFrameId: number;
        const animate = () => {
            animationFrameId = requestAnimationFrame(animate);
            group.rotation.y += 0.01;
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
            renderer.dispose();
            if (container && renderer.domElement.parentNode === container) {
                container.removeChild(renderer.domElement);
            }
        };
    });
</script>

<div class="h-full flex flex-col">
    <!-- Top Bar with Specs -->
    <div class="p-6 bg-[var(--gv2-bg-primary)] border-b border-[var(--gv2-border)] flex gap-8 shrink-0">
        <div class="flex-1">
            <h2 class="text-xl font-bold mb-4 flex items-center gap-2">
                <span class="p-1.5 rounded bg-[var(--gv2-accent)]/20 text-[var(--gv2-accent)]">
                    <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                    </svg>
                </span>
                Engine Design Specifications
            </h2>
            {#if design}
                <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
                    <div class="p-4 rounded-xl bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)]">
                        <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Model</p>
                        <p class="font-mono text-[var(--gv2-accent)]">{design.model_name}</p>
                    </div>
                    <div class="p-4 rounded-xl bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)]">
                        <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Thrust</p>
                        <p class="text-xl font-bold">{design.thrust_kn} <span class="text-sm font-normal text-[var(--gv2-text-secondary)]">kN</span></p>
                    </div>
                    <div class="p-4 rounded-xl bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)]">
                        <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Weight</p>
                        <p class="text-xl font-bold">{design.weight_kg} <span class="text-sm font-normal text-[var(--gv2-text-secondary)]">kg</span></p>
                    </div>
                    <div class="p-4 rounded-xl bg-[var(--gv2-bg-secondary)] border border-[var(--gv2-border)]">
                        <p class="text-xs text-[var(--gv2-text-tertiary)] uppercase tracking-wider mb-1">Bypass Ratio</p>
                        <p class="text-xl font-bold">{design.bypass_ratio}:1</p>
                    </div>
                </div>
                
                <div class="mt-4 flex items-center justify-between">
                    <div class="flex gap-2">
                        {#each design.core_materials as mat}
                            <span class="px-2.5 py-1 rounded-md bg-[var(--gv2-bg-secondary)] text-xs border border-[var(--gv2-border)]">
                                {mat}
                            </span>
                        {/each}
                    </div>
                    
                    {#if design.rtl_validation_passed}
                        <div class="flex items-center gap-2 text-green-500 text-sm font-medium">
                            <svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg>
                            RTL Validation Passed
                        </div>
                    {/if}
                </div>
            {:else}
                <div class="h-24 flex items-center justify-center text-[var(--gv2-text-tertiary)] text-sm animate-pulse">
                    Waiting for CAD nodes to complete...
                </div>
            {/if}
        </div>
        
        <div class="w-64 flex flex-col justify-center gap-4 border-l border-[var(--gv2-border)] pl-8">
            <button 
                onclick={simulation.runProcure}
                disabled={$simulation.isProcessing || !design?.rtl_validation_passed}
                class="w-full py-3 rounded-lg bg-[var(--gv2-accent)] text-white font-medium disabled:opacity-50 hover:bg-blue-600 transition-colors"
            >
                Proceed to Procurement
            </button>
            <p class="text-xs text-[var(--gv2-text-tertiary)] text-center">Requires RTL Validation</p>
        </div>
    </div>

    <!-- 3D Canvas Area -->
    <div class="flex-1 relative bg-black">
        {#if design}
            <div bind:this={container} class="absolute inset-0 w-full h-full"></div>
            
            <div class="absolute bottom-4 left-4 text-xs text-[var(--gv2-text-tertiary)] font-mono">
                Three.js WebGL Viewer Active
            </div>
        {:else}
            <div class="absolute inset-0 flex items-center justify-center">
                <button 
                    onclick={simulation.runDesign}
                    disabled={$simulation.isProcessing}
                    class="px-6 py-2 rounded border border-[var(--gv2-accent)] text-[var(--gv2-accent)] hover:bg-[var(--gv2-accent)]/10 disabled:opacity-50"
                >
                    Run Design Superstep
                </button>
            </div>
        {/if}
    </div>
</div>
