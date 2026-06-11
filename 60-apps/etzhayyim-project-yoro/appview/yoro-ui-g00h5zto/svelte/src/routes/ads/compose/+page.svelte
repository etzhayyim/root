<script lang="ts">
	/**
	 * /ads/compose — advertiser composer for sponsored posts.
	 *
	 * Creates a campaign (or picks an existing one) and publishes a sponsored
	 * `app.bsky.feed.post` with self-label `!ad` via the ads worker
	 * (`com.etzhayyim.apps.ads.postSponsored`). The post shows up in the yoro feed
	 * ranker pool after the campaign DID is added to SPONSORED_DIDS.
	 *
	 * ADR: 90-docs/adr/0039-yoro-ads-integration.md §Sponsored Feed
	 */
	import { onMount } from 'svelte';
	import { atQuery, atProcedure } from '$lib/atproto-agent';

	interface Campaign {
		campaignId: string;
		did: string;
		name: string;
		description?: string;
		active?: boolean;
	}

	let campaigns = $state<Campaign[]>([]);
	let loading = $state(true);
	let loadError = $state('');

	// New campaign form
	let newName = $state('');
	let newDescription = $state('');
	let newAdvertiser = $state('');
	let newBudgetJpy = $state<number | undefined>();
	let creatingCampaign = $state(false);

	// Sponsored post form
	let selectedCampaignId = $state('');
	let postText = $state('');
	let embedUri = $state('');
	let embedTitle = $state('');
	let embedDesc = $state('');
	let posting = $state(false);
	let lastPostUri = $state('');
	let postError = $state('');

	onMount(() => { void refreshCampaigns(); });

	async function refreshCampaigns() {
		loading = true;
		loadError = '';
		try {
			const res: any = await atQuery('com.etzhayyim.apps.ads.listCampaigns', { limit: 100 });
			campaigns = (res?.campaigns ?? []) as Campaign[];
			if (!selectedCampaignId && campaigns.length) selectedCampaignId = campaigns[0].campaignId;
		} catch (e: any) {
			loadError = e?.message ?? String(e);
		} finally {
			loading = false;
		}
	}

	async function createCampaign() {
		if (!newName.trim()) return;
		creatingCampaign = true;
		try {
			const res: any = await atProcedure('com.etzhayyim.apps.ads.createCampaign', {
				name: newName.trim(),
				description: newDescription.trim() || undefined,
				advertiser: newAdvertiser.trim() || undefined,
				budgetJpy: newBudgetJpy,
			});
			newName = ''; newDescription = ''; newAdvertiser = ''; newBudgetJpy = undefined;
			await refreshCampaigns();
			if (res?.campaignId) selectedCampaignId = res.campaignId;
		} catch (e: any) {
			loadError = e?.message ?? String(e);
		} finally {
			creatingCampaign = false;
		}
	}

	async function postSponsored() {
		if (!selectedCampaignId || !postText.trim()) return;
		posting = true;
		postError = '';
		try {
			const res: any = await atProcedure('com.etzhayyim.apps.ads.postSponsored', {
				campaignId: selectedCampaignId,
				text: postText.trim(),
				embedUri: embedUri.trim() || undefined,
				embedTitle: embedTitle.trim() || undefined,
				embedDesc: embedDesc.trim() || undefined,
			});
			lastPostUri = res?.uri ?? '';
			postText = ''; embedUri = ''; embedTitle = ''; embedDesc = '';
		} catch (e: any) {
			postError = e?.message ?? String(e);
		} finally {
			posting = false;
		}
	}
</script>

<svelte:head>
	<title>Ads Composer — YORO</title>
</svelte:head>

<div class="mx-auto max-w-[720px] px-4 py-6">
	<header class="mb-6">
		<h1 class="text-[22px] font-black text-gv2-text-primary">Sponsored Post Composer</h1>
		<p class="mt-1 text-[13px] text-gv2-text-muted">
			Publish an `app.bsky.feed.post` self-labeled <code class="rounded bg-gv2-bg-card px-1 py-0.5 text-[12px]">!ad</code> from a campaign DID.
			The yoro feed ranker picks it up once the DID is added to <code class="rounded bg-gv2-bg-card px-1 py-0.5 text-[12px]">SPONSORED_DIDS</code>.
		</p>
	</header>

	<!-- Create campaign -->
	<section class="mb-8 rounded-2xl border border-gv2-border/40 bg-gv2-bg-card/50 p-4">
		<h2 class="mb-3 text-[15px] font-bold text-gv2-text-primary">1. New campaign</h2>
		<div class="grid gap-2">
			<input class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Campaign name (required)" bind:value={newName} />
			<input class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Description (optional)" bind:value={newDescription} />
			<input class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Advertiser name or controller DID (optional)" bind:value={newAdvertiser} />
			<input type="number" class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Budget JPY (optional)" bind:value={newBudgetJpy} />
			<button
				type="button"
				class="mt-1 rounded-xl bg-[#1185FE] px-4 py-2 text-[14px] font-bold text-white disabled:opacity-50"
				disabled={!newName.trim() || creatingCampaign}
				onclick={() => void createCampaign()}
			>
				{creatingCampaign ? 'Creating…' : 'Create campaign'}
			</button>
		</div>
	</section>

	<!-- Existing campaigns -->
	<section class="mb-8 rounded-2xl border border-gv2-border/40 bg-gv2-bg-card/50 p-4">
		<h2 class="mb-3 text-[15px] font-bold text-gv2-text-primary">2. Pick a campaign</h2>
		{#if loading}
			<p class="text-[13px] text-gv2-text-muted">Loading…</p>
		{:else if loadError}
			<p class="text-[13px] text-red-400">Error: {loadError}</p>
		{:else if campaigns.length === 0}
			<p class="text-[13px] text-gv2-text-muted">No campaigns yet. Create one above.</p>
		{:else}
			<select
				class="w-full rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]"
				bind:value={selectedCampaignId}
			>
				{#each campaigns as c}
					<option value={c.campaignId}>
						{c.name} — {c.did}
					</option>
				{/each}
			</select>
		{/if}
	</section>

	<!-- Post sponsored -->
	<section class="mb-8 rounded-2xl border border-gv2-border/40 bg-gv2-bg-card/50 p-4">
		<h2 class="mb-3 text-[15px] font-bold text-gv2-text-primary">3. Publish sponsored post</h2>
		<div class="grid gap-2">
			<textarea class="min-h-[96px] rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Post text (max 3000)" bind:value={postText}></textarea>
			<input class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Link URL (optional)" bind:value={embedUri} />
			<input class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Link title (optional)" bind:value={embedTitle} />
			<input class="rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px]" placeholder="Link description (optional)" bind:value={embedDesc} />
			<button
				type="button"
				class="mt-1 rounded-xl bg-[#58CC02] px-4 py-2 text-[14px] font-bold text-white disabled:opacity-50"
				disabled={!selectedCampaignId || !postText.trim() || posting}
				onclick={() => void postSponsored()}
			>
				{posting ? 'Publishing…' : 'Publish (with !ad label)'}
			</button>
			{#if lastPostUri}
				<p class="mt-2 break-all text-[12px] text-gv2-text-muted">
					Posted: <code>{lastPostUri}</code>
				</p>
			{/if}
			{#if postError}
				<p class="mt-2 text-[12px] text-red-400">Error: {postError}</p>
			{/if}
		</div>
	</section>

	<footer class="text-[11px] text-gv2-text-muted">
		Every post from this composer carries a self <code>!ad</code> label. Labelers and
		other AppViews can filter via this value (AT Protocol standard).
	</footer>
</div>
