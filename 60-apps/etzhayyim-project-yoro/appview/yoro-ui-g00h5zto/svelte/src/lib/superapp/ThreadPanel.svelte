<script lang="ts">
	/**
	 * ThreadPanel — AT Protocol convo messaging panel.
	 * Uses AT Protocol components from appshellv2/w.
	 */
	import ConvoList from '../w/ConvoList.svelte';
	import FeedTimeline from '../w/FeedTimeline.svelte';
	import DMComposer from '../w/DMComposer.svelte';
	import { getConvoMessages, sendProjectMessage, getCurrentDID } from '$lib/atproto-agent';
	import type { ConvoEnvelope, ConvoGroup } from '$lib/atproto-agent';

	interface Props {
		appNanoid?: string;
		appName?: string;
		servicePath?: string;
		defaultConvos?: Array<{ id: string; name: string }>;
	}

	let {
		appNanoid = '',
		appName = '',
		servicePath = '',
		defaultConvos = [],
	}: Props = $props();

	let activeConvoId = $state('');
	let envelopes = $state<ConvoEnvelope[]>([]);
	let loading = $state(false);
	let selfDid = $state('');

	let groups = $derived<ConvoGroup[]>(
		defaultConvos.length > 0
			? [
					{
						section: 'convos' as const,
						label: appName || 'Conversations',
						convos: defaultConvos.map((ch) => ({
							convoId: ch.id,
							name: ch.name,
							description: '',
							isDirect: false,
							isSpace: false,
							isFavorite: false,
							isMuted: false,
							isEncrypted: false,
							unreadCount: 0,
							highlightCount: 0,
							lastRecordTimestamp: '',
							lastRecordPreview: '',
						})),
					},
				]
			: [],
	);

	$effect(() => {
		if (!activeConvoId && defaultConvos.length > 0) {
			activeConvoId = defaultConvos[0].id;
		}
	});

	$effect(() => {
		void getCurrentDID().then((did) => { selfDid = did ?? ''; });
	});

	$effect(() => {
		if (activeConvoId) {
			void loadMessages(activeConvoId);
		}
	});

	async function loadMessages(convoId: string) {
		loading = true;
		try {
			envelopes = await getConvoMessages(convoId, { limit: 50 }) ?? [];
		} catch {
			envelopes = [];
		} finally {
			loading = false;
		}
	}

	async function handleSend(body: string, replyToRkey?: string) {
		if (!activeConvoId) return;
		await sendProjectMessage(activeConvoId, body, replyToRkey ? { replyTo: replyToRkey } : undefined);
		await loadMessages(activeConvoId);
	}
</script>

<div class="flex h-full w-full overflow-hidden">
	{#if groups.length > 1 || (groups[0]?.convos?.length ?? 0) > 1}
		<div class="w-[200px] shrink-0 border-r border-gv2-border/40 overflow-y-auto scrollbar-none">
			<ConvoList
				{groups}
				activeConvoId={activeConvoId}
				onSelectConvo={(id) => { activeConvoId = id; }}
			/>
		</div>
	{/if}

	<div class="flex flex-1 flex-col min-w-0">
		{#if loading}
			<div class="flex flex-1 items-center justify-center">
				<div class="flex gap-1">
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[#58CC02] [animation-delay:0ms]"></span>
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[#58CC02] [animation-delay:150ms]"></span>
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[#58CC02] [animation-delay:300ms]"></span>
				</div>
			</div>
		{:else if !activeConvoId}
			<div class="flex flex-1 flex-col items-center justify-center gap-4 px-8">
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--gv2-bg-hover,#252525)]">
					<svg class="h-8 w-8 text-[var(--gv2-text-muted,#666)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">
						<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
					</svg>
				</div>
				<div class="text-center">
					<p class="text-[17px] font-semibold text-[var(--gv2-text-primary,#fff)]">Start a conversation</p>
					<p class="mt-1 text-[14px] text-[var(--gv2-text-muted,#666)]">Select a conversation or create a new one to begin messaging.</p>
				</div>
			</div>
		{:else}
			<div class="flex-1 min-h-0 overflow-hidden">
				<FeedTimeline {envelopes} {selfDid} />
			</div>
			<DMComposer convoId={activeConvoId} onSend={handleSend} />
		{/if}
	</div>
</div>
