<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => { void goto('/profile/did:web:support.etzhayyim.com', { replaceState: true }); });
</script>

<svelte:head>
	<title>Support | YORO</title>
	<meta name="description" content="etzhayyim Support Agent — LLM-powered support for YORO and etzhayyim services." />
	<meta name="at:did" content="did:web:support.etzhayyim.com" />
</svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">Redirecting to Support Agent...</p>
</div>
