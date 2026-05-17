<script lang="ts">
	import { ServicesPanel } from '$lib/superapp';
	import { activeServiceApp, closeActor } from '$lib/superapp';
	import ActorFrame from '$lib/actor/ActorFrame.svelte';
</script>

<svelte:head>
	<title>Apps — YORO</title>
</svelte:head>

{#if $activeServiceApp}
	<div class="w-full overflow-hidden h-full">
		{#key $activeServiceApp}
			<ActorFrame nanoid={$activeServiceApp} onClose={closeActor} />
		{/key}
	</div>
{:else}
	<ServicesPanel />
{/if}
