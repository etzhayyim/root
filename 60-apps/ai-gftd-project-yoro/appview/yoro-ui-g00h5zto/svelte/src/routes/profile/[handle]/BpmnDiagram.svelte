<!--
  BpmnDiagram.svelte — read-only BPMN 2.0 viewer (bpmn-js NavigatedViewer).

  Renders a BPMN XML string (must include BPMNDI layout) as a pan/zoom diagram.
  Client-only: bpmn-js touches the DOM, so the viewer is dynamically imported
  inside an effect (never on the server). Reused by AgentProfile's "Process" tab
  for any actor that publishes a BPMN manifest.
-->
<script lang="ts">
	import { onDestroy } from 'svelte';
	import 'bpmn-js/dist/assets/diagram-js.css';
	import 'bpmn-js/dist/assets/bpmn-js.css';

	let { xml = '' }: { xml?: string } = $props();

	let container = $state<HTMLDivElement | null>(null);
	let error = $state('');
	let loading = $state(false);
	// eslint-disable-next-line @typescript-eslint/no-explicit-any
	let viewer: any = null;

	async function render(x: string, el: HTMLDivElement) {
		loading = true;
		error = '';
		try {
			const mod = await import('bpmn-js/lib/NavigatedViewer');
			const Viewer = mod.default;
			if (viewer) {
				try { viewer.destroy(); } catch { /* noop */ }
				viewer = null;
			}
			viewer = new Viewer({ container: el });
			await viewer.importXML(x);
			viewer.get('canvas').zoom('fit-viewport');
		} catch (e) {
			error = e instanceof Error ? e.message : String(e);
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (xml && container) {
			void render(xml, container);
		}
	});

	onDestroy(() => {
		if (viewer) {
			try { viewer.destroy(); } catch { /* noop */ }
		}
	});
</script>

<div class="bpmn-diagram">
	{#if error}
		<p class="bpmn-error">BPMN render error: {error}</p>
	{/if}
	{#if loading}
		<p class="bpmn-loading">レンダリング中…</p>
	{/if}
	<div class="bpmn-canvas" bind:this={container}></div>
</div>

<style>
	.bpmn-diagram {
		width: 100%;
	}
	.bpmn-canvas {
		width: 100%;
		height: 440px;
		background: #ffffff;
		border: 1px solid #e5e7eb;
		border-radius: 8px;
		overflow: hidden;
	}
	.bpmn-error {
		color: #b91c1c;
		font-size: 0.85rem;
		padding: 0.5rem 0;
	}
	.bpmn-loading {
		color: #6b7280;
		font-size: 0.85rem;
		padding: 0.5rem 0;
	}
	/* hide the bpmn-js attribution watermark */
	:global(.bpmn-canvas .bjs-powered-by) {
		display: none;
	}
</style>
