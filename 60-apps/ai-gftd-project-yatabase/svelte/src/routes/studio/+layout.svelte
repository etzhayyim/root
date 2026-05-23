<script lang="ts">
	import { onMount } from 'svelte';
	import StudioNav from '$lib/components/StudioNav.svelte';
	import SignInPanel from '$lib/components/SignInPanel.svelte';
	import { apiKey, identity, refreshSession } from '$lib/stores';

	let { children } = $props();

	onMount(() => {
		void refreshSession();
	});

	$effect(() => {
		// re-validate when the user pastes a new key into SignInPanel.
		void $apiKey;
		void refreshSession();
	});
</script>

<div class="flex min-h-screen bg-gftd-bg text-gftd-text">
	{#if $identity}
		<StudioNav />
	{/if}

	<main class="min-w-0 flex-1">
		{#if $identity}
			{@render children()}
		{:else}
			<div class="flex min-h-screen items-center justify-center p-6">
				<SignInPanel />
			</div>
		{/if}
	</main>
</div>
