<!--
  /notifications → /activities redirect.
  Notifications are now part of the OCEL v2 Activity Log.
  Social notifications: /activities?tab=social
  Project notifications: integrated into /projects badge panel.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';

	onMount(() => {
		void goto('/activities?tab=social', { replaceState: true });
	});
</script>

<svelte:head>
	<title>Activities — YORO</title>
</svelte:head>

<div class="flex h-full items-center justify-center">
	<p class="text-[14px] text-gv2-text-muted">リダイレクト中...</p>
</div>
