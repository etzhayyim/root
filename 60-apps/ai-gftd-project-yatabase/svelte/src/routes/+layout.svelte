<script lang="ts">
	import '../app.css';
	import { onMount } from 'svelte';
	import { theme } from '$lib/stores';

	let { children } = $props();

	onMount(() => {
		document.documentElement.setAttribute('data-theme', $theme);
	});
</script>

{@render children()}
