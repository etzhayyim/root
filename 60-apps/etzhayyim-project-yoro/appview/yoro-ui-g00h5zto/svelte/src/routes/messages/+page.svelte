<!--
  /messages → /convo redirect (chat.bsky.convo.* lexicon alignment)
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => { void goto('/projects', { replaceState: true }); });
</script>

<svelte:head>
	<title>Redirecting — YORO</title>
</svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">Redirecting to /convo...</p>
</div>
