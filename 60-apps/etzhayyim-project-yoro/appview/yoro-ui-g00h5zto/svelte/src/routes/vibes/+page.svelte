<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	// /vibes is an alias for / (home). SvelteKit route-based — redirect to canonical URL.
	onMount(() => {
		void goto('/', { replaceState: true });
	});
</script>
