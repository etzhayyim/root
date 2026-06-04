<script lang="ts">
	// Route-First Architecture (CLAUDE.md): `/` renders the Vibes feed directly.
	// NOTE: do NOT render <App/> here — App.svelte mounts a client SPA router
	// whose `import.meta.glob("../routes/**/+page.svelte")` re-matches `/` back
	// to THIS file, so <App/> would render itself recursively → "Maximum call
	// stack size exceeded" → blank (black) screen on ssr:false CSR bootstrap.
	import { VibesPanel } from '$lib/superapp';
</script>

<svelte:head>
	<title>YORO</title>
</svelte:head>

<VibesPanel />
