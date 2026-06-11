<script lang="ts">
	import { page } from '$app/stores';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	onMount(() => { void goto(`/projects/${$page.params.convoId}`, { replaceState: true }); });
</script>
<p>Redirecting...</p>
