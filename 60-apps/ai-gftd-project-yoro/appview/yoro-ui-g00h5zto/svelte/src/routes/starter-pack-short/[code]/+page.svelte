<!--
  /starter-pack-short/{code} — Short URL redirect for starter packs.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	const code = $derived(decodeURIComponent(($page.params as Record<string, string>).code ?? ''));

	onMount(() => {
		// Short codes resolve to full starter pack URLs.
		// For now, redirect to home. In production, resolve the short code server-side.
		void goto('/', { replaceState: true });
	});
</script>

<svelte:head><title>Starter Pack — YORO</title></svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">Loading starter pack...</p>
</div>
