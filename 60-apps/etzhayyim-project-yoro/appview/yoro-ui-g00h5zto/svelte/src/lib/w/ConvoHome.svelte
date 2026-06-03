<script lang="ts">
	import { convos } from './convo-store.svelte.js';
	import { sendProjectMessage, createConvo, createProjectConvo, getCurrentDID, decodePayload, decodeAndDecryptPayload, listConvoMembers } from '$lib/atproto-agent';
	import ConvoList from './ConvoList.svelte';
	import FeedTimeline from './FeedTimeline.svelte';
	import DMComposer from './DMComposer.svelte';
	import ConvoSettings from './ConvoSettings.svelte';
	import { useGraphRAG } from '$lib/provider/graph-rag.svelte.js';
	import type { ConvoSection, ConversationKind, ConvoParticipantType } from '$lib/atproto-agent';
	import { useStream } from '@langchain/svelte';
	import type { BaseMessage } from '@langchain/core/messages';

	const graphRAG = useGraphRAG();

	let selfDid = $state('');
	let sending = $state(false);
	let createMode = $state<'convo' | 'dm' | null>(null);
	let createName = $state('');
	let createBusy = $state(false);
	let showSettings = $state(false);
	let conversationFilter = $state<'all' | ConversationKind>('all');
	let participantTypes = $state<Map<string, ConvoParticipantType>>(new Map());

	const activeConvoId = $derived(convos.activeConvoId);

	// LangGraph convoId → thread ID mapping (one LG thread per AT Protocol convo).
	let lgThreadMap = $state<Record<string, string>>({});
	const lgThreadId = $derived(activeConvoId ? (lgThreadMap[activeConvoId] ?? null) : null);

	const stream = useStream({
		assistantId: 'agent',
		apiUrl: '/api/pregel',
		threadId: () => lgThreadId,
		onThreadId: (id) => {
			if (activeConvoId) lgThreadMap = { ...lgThreadMap, [activeConvoId]: id };
		},
	});

	// Streaming delta — the in-flight AI message while LangGraph is generating.
	const lastStreamMsg = $derived(stream.messages.at(-1));
	const lastIsAI = $derived(
		!!lastStreamMsg &&
			(lastStreamMsg as unknown as { _getType?: () => string })._getType?.() === 'ai'
	);
	const streamingDelta = $derived(
		stream.isLoading && lastIsAI
			? typeof lastStreamMsg!.content === 'string'
				? lastStreamMsg!.content
				: JSON.stringify(lastStreamMsg!.content)
			: ''
	);
	const convoList = $derived(convos.convoList);
	const activeConvoEnvelopes = $derived(convos.activeConvoEnvelopes);
	const typingUsers = $derived(convos.typingUsers);
	const activeConvo = $derived(convos.activeConvo);
	const convoName = $derived(activeConvo?.convo?.name ?? activeConvoId);
	const presenceMap = $derived(convos.presenceMap);
	const streamState = $derived(convos.streamState);

	const isDirect = $derived(
		(convos.snapshot?.directConvoIds ?? []).includes(activeConvoId) ?? false,
	);

	$effect(() => {
		convos.subscribe();
		getCurrentDID().then((did) => { selfDid = did ?? ''; }).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/w/ConvoHome.svelte: suppressed async error", error); });
	});

	// Load participant types when active convo changes
	$effect(() => {
		if (!activeConvoId) { participantTypes = new Map(); return; }
		void listConvoMembers(activeConvoId).then((members) => {
			const map = new Map<string, ConvoParticipantType>();
			for (const m of members) {
				if (m.participantType) map.set(m.did, m.participantType);
			}
			participantTypes = map;
		}).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/w/ConvoHome.svelte: suppressed async error", error); });
	});

	function handleSelectConvo(convoId: string) {
		convos.setActiveConvo(convoId);
	}

	function handleBack() {
		convos.setActiveConvo('');
		showSettings = false;
	}

	function handleToggleSection(section: ConvoSection) {
		convos.toggleSection(section);
	}

	async function handleSend(body: string) {
		if (!activeConvoId || sending || stream.isLoading) return;
		sending = true;
		try {
			// E2E encrypt when WebLLM is active (LLM runs client-side, server sees ciphertext only)
			const e2e = graphRAG.isLLMReady && !!selfDid;

			// Persist message to PDS (encrypted if E2E, plaintext if server-side LLM)
			await sendProjectMessage(activeConvoId, body, { encrypt: e2e });

			if (graphRAG.isLLMReady) {
				// GraphRAG: local LLM + XRPC-backed graph context (E2E — all processing client-side)
				const recentEnvelopes = (activeConvoEnvelopes ?? []).slice(-10);
				const history = await Promise.all(recentEnvelopes.map(async (env) => ({
					role: (env.senderDid === selfDid ? 'user' : 'assistant') as 'user' | 'assistant',
					content: await decodeAndDecryptPayload(env, activeConvoId),
				})));
				const filteredHistory = history.filter((m) => m.content && m.content !== '[encrypted]');
				const localReply = await graphRAG.query(filteredHistory, body);
				if (localReply) {
					await sendProjectMessage(activeConvoId, localReply, { encrypt: e2e });
				}
			} else {
				// LangGraph streaming path — response streams back as streamingDelta.
				void stream.submit(
					{ messages: [{ type: 'human', content: body }] },
					{ config: { configurable: { convId: activeConvoId } } },
				);
			}
		} finally {
			sending = false;
		}
	}

	async function handleCreate() {
		if (!createName.trim()) return;
		createBusy = true;
		try {
			if (createMode === 'convo') {
				const result = await createConvo(createName.trim());
				const id = result?.convoId;
				if (id) convos.setActiveConvo(id);
			} else if (createMode === 'dm') {
				const result = await createProjectConvo(createName.trim());
				const id = result?.convo?.convoId;
				if (id) convos.setActiveConvo(id);
			}
			createMode = null;
			createName = '';
		} finally {
			createBusy = false;
		}
	}

</script>

<div class="flex h-full w-full max-w-[600px] mx-auto flex-col" style="height: calc(100dvh - 48px - 80px);">
	{#if showSettings && activeConvoId}
		<ConvoSettings
			convoId={activeConvoId}
			convoName={convoName ?? ''}
			description={activeConvo?.convo?.description}
			isEncrypted={activeConvo?.convo?.encryptionEnabled}
			{isDirect}
			{selfDid}
			onClose={() => { showSettings = false; }}
			onEncryptionChange={() => void convos.refresh()}
			onArchived={() => { showSettings = false; convos.setActiveConvo(''); void convos.refresh(); }}
		/>
	{:else if activeConvoId}
		<div class="flex min-h-[48px] items-center gap-2 border-b border-[var(--gv2-border,#2f2f2f)] px-3">
			<button
				type="button"
				class="flex h-11 w-11 items-center justify-center rounded-full tap-target-44 touch-manipulation active:opacity-80"
				onclick={handleBack}
				aria-label="Back"
			>
				<svg class="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2">
					<path d="M13 4L7 10l6 6" />
				</svg>
			</button>
			<span class="flex-1 truncate text-[15px] font-semibold">{convoName}</span>
			{#if activeConvo?.convo?.encryptionEnabled}
				<span class="text-[14px]" title="E2E 暗号化">🔒</span>
			{/if}
			<button
				type="button"
				class="flex h-11 w-11 items-center justify-center rounded-full tap-target-44 touch-manipulation active:opacity-80"
				onclick={() => { showSettings = true; }}
				aria-label="設定"
			>
				<svg class="h-5 w-5 text-gv2-text-muted" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.5">
					<circle cx="10" cy="10" r="2" />
					<path d="M10 1.5v2M10 16.5v2M1.5 10h2M16.5 10h2M3.4 3.4l1.4 1.4M15.2 15.2l1.4 1.4M3.4 16.6l1.4-1.4M15.2 4.8l1.4-1.4" />
				</svg>
			</button>
		</div>
		<div class="flex-1 overflow-hidden">
			<FeedTimeline
				envelopes={activeConvoEnvelopes}
				{selfDid}
				typing={typingUsers}
				encrypted={activeConvo?.convo?.encryptionEnabled ?? false}
				{participantTypes}
			/>
		</div>
		{#if stream.isLoading || streamingDelta}
			<div class="px-4 pb-1">
				<div class="max-w-[80%] rounded-2xl rounded-tl-sm bg-[var(--gv2-bg-card,#1e1e1e)] px-4 py-3 text-[15px] text-[var(--gv2-text,#f1f2f5)]">
					{#if streamingDelta}
						<p class="whitespace-pre-wrap break-words">{streamingDelta}</p>
					{:else}
						<span class="text-[var(--gv2-text-muted,#b9bcc4)]">…</span>
					{/if}
				</div>
			</div>
		{/if}
		<DMComposer
			convoId={activeConvoId}
			disabled={sending || stream.isLoading}
			onSend={handleSend}
		/>
	{:else}
		<ConvoList
			groups={convoList}
			activeConvoId={activeConvoId}
			{presenceMap}
			firehoseState={streamState}
			{conversationFilter}
			onSelectConvo={handleSelectConvo}
			onToggleSection={handleToggleSection}
			onCreateConvo={() => { createMode = 'convo'; }}
			onCreateDM={() => { createMode = 'dm'; }}
			onConversationFilterChange={(f) => { conversationFilter = f; }}
		/>
	{/if}
</div>

{#if createMode}
	<div class="fixed inset-0 z-50 flex items-end justify-center bg-black/60" role="dialog" aria-modal="true">
		<div class="w-full max-w-[600px] rounded-t-2xl bg-[var(--gv2-bg-card,#1e1e1e)] p-4 pb-safe-bottom">
			<h2 class="mb-3 text-[17px] font-bold">
				{createMode === 'convo' ? '会話を作成' : '新しい DM'}
			</h2>
			<input
				class="mb-3 w-full rounded-xl bg-[var(--gv2-bg-input,#2a2a2a)] px-4 py-3 text-[15px] outline-none"
				placeholder={createMode === 'convo' ? '会話名' : 'DID (did:plc:...)'}
				bind:value={createName}
				onkeydown={(e) => { if (e.key === 'Enter') void handleCreate(); }}
			/>
			<div class="flex gap-2">
				<button
					type="button"
					class="flex-1 rounded-xl bg-[var(--gv2-bg-hover,#2f2f2f)] py-3 text-[15px] font-semibold touch-manipulation active:opacity-80"
					onclick={() => { createMode = null; createName = ''; }}
				>キャンセル</button>
				<button
					type="button"
					class="flex-1 rounded-xl bg-[#58CC02] py-3 text-[15px] font-bold text-white shadow-[0_3px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[3px] transition-all disabled:opacity-50"
					disabled={createBusy || !createName.trim()}
					onclick={() => void handleCreate()}
				>{createBusy ? '作成中…' : '作成'}</button>
			</div>
		</div>
	</div>
{/if}
