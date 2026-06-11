<script>
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => { void goto('/projects', { replaceState: true }); });
</script>
<p>Redirecting...</p>
