<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => { void goto('/privacy', { replaceState: true }); });
</script>

<svelte:head><title>Privacy Policy — YORO</title></svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">Redirecting...</p>
</div>
