<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';

	// Query: /bpmn-viewer?path=60-apps/etzhayyim-project-states/data/gov/jpn/bpmn/moj.bpmn
	//   or:  /bpmn-viewer?iso=jpn&file=moj
	let path = $state('');
	let iso = $state('');
	let file = $state('');
	let kind = $state<'bpmn' | 'dmn'>('bpmn');
	let xml = $state('');
	let error = $state('');
	let loading = $state(true);
	let containerEl: HTMLDivElement | undefined = $state();
	let viewer: any = $state(null);

	$effect(() => {
		const params = $page.url.searchParams;
		path = params.get('path') || '';
		iso = params.get('iso') || '';
		file = params.get('file') || '';
		const k = params.get('kind');
		kind = k === 'dmn' ? 'dmn' : 'bpmn';
	});

	async function loadBpmn() {
		loading = true;
		error = '';
		xml = '';
		try {
			// Resolve URL. The BPMN files live under the etzhayyim-apps repo. For
			// production we expose them via a simple /bpmn-files/{iso}/{file}.bpmn
			// static path that the Worker proxies to the repo asset. Until that
			// proxy exists, fall back to a clear error message.
			let url = '';
			if (path) {
				url = `/bpmn-files/${path.replace(/^.*\/data\/gov\//, '')}`;
			} else if (iso && file) {
				url = `/bpmn-files/${iso}/bpmn/${file.endsWith('.bpmn') ? file : file + '.bpmn'}`;
			} else {
				error = 'missing path or iso+file query param';
				return;
			}
			const resp = await fetch(url);
			if (!resp.ok) {
				error = `BPMN fetch failed: ${resp.status} ${url}`;
				return;
			}
			xml = await resp.text();
			if (viewer) viewer.destroy();
			if (kind === 'dmn') {
				// Lazy-load dmn-js Viewer
				const { default: DmnViewer } = await import(/* @vite-ignore */ 'dmn-js/lib/Viewer');
				viewer = new (DmnViewer as any)({ container: containerEl });
				await viewer.importXML(xml);
			} else {
				// Lazy-load bpmn-js Viewer
				const { default: BpmnViewer } = await import(/* @vite-ignore */ 'bpmn-js/lib/Viewer');
				viewer = new (BpmnViewer as any)({ container: containerEl });
				await viewer.importXML(xml);
				viewer.get('canvas').zoom('fit-viewport');
			}
		} catch (e: any) {
			error = `viewer error: ${e?.message ?? String(e)}`;
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if ((path || (iso && file)) && containerEl) void loadBpmn();
	});

	onMount(() => {
		return () => {
			if (viewer) {
				try { viewer.destroy(); } catch {}
				viewer = null;
			}
		};
	});
</script>

<svelte:head>
	<title>BPMN Viewer — {iso || path || 'gov procedure'} — YORO</title>
</svelte:head>

<div class="min-h-screen bg-gv2-bg-primary text-gv2-text-primary">
	<header class="border-b border-gv2-border/30 px-4 py-3">
		<h1 class="text-[16px] font-semibold">BPMN Viewer</h1>
		<p class="text-[12px] text-gv2-text-muted mt-0.5 font-mono truncate">
			{path || `${iso}/${file}`}
		</p>
	</header>

	<div class="relative w-full" style="height: calc(100vh - 64px)">
		{#if loading}
			<div class="absolute inset-0 flex items-center justify-center text-gv2-text-muted text-[13px]">
				Loading BPMN…
			</div>
		{/if}
		{#if error}
			<div class="p-4 text-red-500 text-[13px]">
				<p class="font-semibold">Error</p>
				<p class="mt-1 font-mono">{error}</p>
				<p class="mt-3 text-gv2-text-muted">
					BPMN files are sourced from
					<span class="font-mono">60-apps/etzhayyim-project-states/data/gov/{'{iso}'}/bpmn/</span>.
					A static asset proxy is required to serve them to the browser.
				</p>
			</div>
		{/if}
		<div bind:this={containerEl} class="absolute inset-0"></div>
	</div>
</div>

<style>
	:global(.bjs-container) { background: transparent; }
</style>
