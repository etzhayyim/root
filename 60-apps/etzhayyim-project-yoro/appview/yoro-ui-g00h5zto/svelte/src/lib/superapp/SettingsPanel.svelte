<script lang="ts">
	import { onMount } from 'svelte';

	interface Props {
		appName?: string;
		accentColor?: string;
		whatsappNumber?: string;
		privacyHref?: string;
		termsHref?: string;
		supportHref?: string;
		languageCodes?: string[];
		onLanguageChange?: (code: string) => void;
	}

	let props: Props = $props();
	let loaded = $state(false);
	let SettingsPanelImpl = $state<null | typeof import('./SettingsPanelImpl.svelte').default>(null);

	onMount(async () => {
		SettingsPanelImpl = (await import('./SettingsPanelImpl.svelte')).default;
		loaded = true;
	});
</script>

{#if SettingsPanelImpl}
	<SettingsPanelImpl {...props} />
{:else}
	<div class="mx-auto flex w-full max-w-[600px] flex-col gap-4 p-4">
		<div class="h-6 w-32 animate-pulse rounded bg-etzhayyim-hover"></div>
		<div class="h-40 animate-pulse rounded-2xl border border-etzhayyim-border bg-etzhayyim-card"></div>
		<div class="h-40 animate-pulse rounded-2xl border border-etzhayyim-border bg-etzhayyim-card"></div>
		{#if loaded}
			<div class="text-[12px] text-etzhayyim-muted">Loading settings…</div>
		{/if}
	</div>
{/if}
