<!--
  /messages/{convoId} → /convo/{convoId} redirect
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	const convoId = ($page.params as Record<string, string>).convoId ?? '';
	onMount(() => { void goto(`/projects/${convoId}`, { replaceState: true }); });
</script>

<svelte:head>
	<title>Redirecting — YORO</title>
</svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">Redirecting...</p>
</div>
