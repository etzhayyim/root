<script lang="ts">
	import { Button } from '@etzhayyim/design-system';
	import { getProfile, setProfile, getCurrentDID } from '$lib/atproto-agent';
	import type { Did } from '$lib/atproto-agent';

	interface Props {
		onClose?: () => void;
	}

	let { onClose }: Props = $props();

	let did = $state('');
	let displayName = $state('');
	let avatarUrl = $state('');
	let loading = $state(true);
	let saving = $state(false);
	let saved = $state(false);

	$effect(() => {
		void load();
	});

	async function load() {
		loading = true;
		try {
			did = await getCurrentDID();
			const profile = await getProfile(did);
			displayName = profile.displayName ?? '';
			avatarUrl = profile.avatarUrl ?? '';
		} catch { /* ignore */ }
		finally { loading = false; }
	}

	async function handleSave() {
		saving = true;
		saved = false;
		try {
			await setProfile({ displayName, avatarUrl: avatarUrl || undefined });
			saved = true;
			setTimeout(() => { saved = false; }, 2000);
		} catch { /* ignore */ }
		finally { saving = false; }
	}
</script>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 px-4">
		{#if onClose}
			<button
				type="button"
				class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
				onclick={onClose}
				aria-label="Close"
			>
				<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M15 19l-7-7 7-7" /></svg>
			</button>
		{/if}
		<span class="text-[15px] font-bold text-gv2-text-primary">Edit profile</span>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none p-4 space-y-4">
		{#if loading}
			<div class="flex items-center justify-center py-12">
				<div class="flex gap-1">
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[var(--gv2-accent,#06c755)] [animation-delay:0ms]"></span>
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[var(--gv2-accent,#06c755)] [animation-delay:150ms]"></span>
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[var(--gv2-accent,#06c755)] [animation-delay:300ms]"></span>
				</div>
			</div>
		{:else}
			<!-- Avatar preview -->
			<div class="flex flex-col items-center gap-3">
				<div class="flex h-20 w-20 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)]/20 text-[28px] font-bold text-[var(--gv2-accent,#06c755)] overflow-hidden">
					{#if avatarUrl}
						<img src={avatarUrl} alt="Avatar" class="h-full w-full object-cover" />
					{:else}
						{(displayName || 'U').slice(0, 2).toUpperCase()}
					{/if}
				</div>
				{#if did}
					<p class="text-[12px] font-mono text-gv2-text-muted">{did}</p>
				{/if}
			</div>

			<!-- Display name -->
			<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-2">
				<label class="text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted" for="profile-name">Display name</label>
				<input
					id="profile-name"
					class="w-full min-h-[44px] rounded-xl bg-gv2-bg-input px-3 py-2 text-[15px] text-gv2-text-primary outline-none border border-gv2-border focus:border-[var(--gv2-accent,#06c755)]"
					bind:value={displayName}
					placeholder="Your name"
				/>
			</div>

			<!-- Avatar URL -->
			<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-2">
				<label class="text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted" for="profile-avatar">Avatar URL</label>
				<input
					id="profile-avatar"
					class="w-full min-h-[44px] rounded-xl bg-gv2-bg-input px-3 py-2 text-[15px] text-gv2-text-primary outline-none border border-gv2-border focus:border-[var(--gv2-accent,#06c755)]"
					bind:value={avatarUrl}
					placeholder="https://..."
				/>
			</div>

			<!-- Save -->
			<div class="flex gap-2">
				<Button variant="solid-fill" size="md" class="flex-1" disabled={saving} onclick={handleSave}>
					{#if saved}
						Saved
					{:else if saving}
						Saving...
					{:else}
						Save profile
					{/if}
				</Button>
			</div>
		{/if}
	</div>
</div>
