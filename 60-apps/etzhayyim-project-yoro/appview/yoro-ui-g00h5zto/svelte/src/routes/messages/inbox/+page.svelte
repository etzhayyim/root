<!--
  /messages/inbox — Messages inbox view (redirects to /messages).
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => { void goto('/projects', { replaceState: true }); });
</script>

<svelte:head>
	<title>Inbox — YORO</title>
</svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">Loading inbox...</p>
</div>
