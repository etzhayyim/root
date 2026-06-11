<script lang="ts">
	import { Avatar, Badge, Card } from '@etzhayyim/design-system';
	import { memberLabel, blobUrl, decodeMessageBody, sendProjectMessage } from '$lib/atproto-agent';
	import { parseCardType, type ConvoEnvelope, type ConvoParticipantType, type CardType } from '$lib/atproto-agent';
	import CardList from './cards/CardList.svelte';
	import CardForm from './cards/CardForm.svelte';
	import CardTable from './cards/CardTable.svelte';
	import CardCarousel from './cards/CardCarousel.svelte';
	import CardChart from './cards/CardChart.svelte';
	import CardReceipt from './cards/CardReceipt.svelte';
	import CardCode from './cards/CardCode.svelte';
	import CardPoll from './cards/CardPoll.svelte';
	import CardCalendar from './cards/CardCalendar.svelte';
	import CardKanban from './cards/CardKanban.svelte';
	import CardConfirmation from './cards/CardConfirmation.svelte';
	import CardMetricDashboard from './cards/CardMetricDashboard.svelte';
	import CardImageGallery from './cards/CardImageGallery.svelte';
	import CardMapPin from './cards/CardMapPin.svelte';
	import CardEmbed from './cards/CardEmbed.svelte';
	import CardGame from './cards/CardGame.svelte';
	import CardPerson from './cards/CardPerson.svelte';
	import CardOrganization from './cards/CardOrganization.svelte';
	import CardService from './cards/CardService.svelte';
	import CardSystem from './cards/CardSystem.svelte';

	interface Props {
		envelopes: ConvoEnvelope[];
		selfDid?: string;
		typing?: string[];
		encrypted?: boolean;
		/** Map of DID → participant type for badge display. */
		participantTypes?: Map<string, ConvoParticipantType>;
		onReaction?: (rkey: string, emoji: string) => void;
		onReply?: (rkey: string) => void;
		onRedact?: (rkey: string) => void;
		onThread?: (rkey: string) => void;
		onLoadMore?: () => void;
		onDecryptBody?: (rkey: string, payload: string, senderDid: string) => Promise<string | null>;
	}

	let {
		envelopes,
		selfDid = '',
		typing = [],
		encrypted = false,
		participantTypes = new Map(),
		onReaction,
		onReply,
		onRedact,
		onThread,
		onLoadMore,
		onDecryptBody,
	}: Props = $props();

	let decryptedBodies = $state(new Map<string, string>());

	$effect(() => {
		if (!onDecryptBody) return;
		for (const env of envelopes) {
			if (env.encryption === 'plaintext' || decryptedBodies.has(env.rkey)) continue;
			const { rkey, payload, senderDid } = env;
			void onDecryptBody(rkey, payload, senderDid).then((plaintext) => {
				if (plaintext !== null) {
					decryptedBodies = new Map(decryptedBodies).set(rkey, plaintext);
				}
			}).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/w/FeedTimeline.svelte: suppressed async error", error); });
		}
	});

	const envelopeById = $derived.by(() => {
		const map = new Map<string, ConvoEnvelope>();
		for (const e of envelopes) map.set(e.rkey, e);
		return map;
	});

	const SYSTEM_KINDS = new Set(['member.join', 'member.leave', 'convo.update', 'convo.archive']);

	const renderableEnvelopes = $derived(
		envelopes.filter((e) => !SYSTEM_KINDS.has(e.kind)),
	);

	function getCardPayload(env: ConvoEnvelope): { type: CardType; data: any } | null {
		const cardType = parseCardType(env.contentType);
		if (!cardType) return null;
		try {
			const body = decodeMessageBody(env);
			return { type: cardType, data: JSON.parse(body) };
		} catch {
			return null;
		}
	}

	function handleCardAction(convoId: string, action: string, data?: Record<string, unknown>) {
		void sendProjectMessage(convoId, JSON.stringify({ action, ...data }), {
			contentType: 'application/vnd.etzhayyim.card.action',
		});
	}

	interface GroupInfo { isFirst: boolean; }
	const groupInfo = $derived.by(() => {
		const info = new Map<string, GroupInfo>();
		for (let i = 0; i < renderableEnvelopes.length; i++) {
			const e = renderableEnvelopes[i];
			const prev = i > 0 ? renderableEnvelopes[i - 1] : null;
			const isFirst =
				!prev || prev.senderDid !== e.senderDid ||
				Math.abs(new Date(e.createdAt).getTime() - new Date(prev.createdAt).getTime()) > 5 * 60 * 1000;
			info.set(e.rkey, { isFirst });
		}
		return info;
	});

	function dateLabel(ts: string): string {
		const d = new Date(ts);
		const now = new Date();
		const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
		const target = new Date(d.getFullYear(), d.getMonth(), d.getDate());
		const diff = today.getTime() - target.getTime();
		if (diff === 0) return 'Today';
		if (diff === 86400000) return 'Yesterday';
		return d.toLocaleDateString('ja-JP', { month: 'numeric', day: 'numeric' });
	}

	function timeLabel(ts: string): string {
		return new Date(ts).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
	}

	function needsDateSeparator(index: number): boolean {
		if (index === 0) return true;
		const prev = renderableEnvelopes[index - 1];
		const curr = renderableEnvelopes[index];
		return new Date(prev.createdAt).toDateString() !== new Date(curr.createdAt).toDateString();
	}

	function displayName(did: string): string {
		if (did === selfDid) return 'You';
		return memberLabel(did);
	}

	function getBody(env: ConvoEnvelope): string {
		if (decryptedBodies.has(env.rkey)) return decryptedBodies.get(env.rkey)!;
		return decodeMessageBody(env);
	}

	/** Parse MCP tool result from envelope payload. */
	function getToolResult(env: ConvoEnvelope): { toolName: string; toolResult: string } | null {
		if (env.contentType !== 'application/vnd.etzhayyim.mcp.tool-result') return null;
		try {
			const body = decodeMessageBody(env);
			const parsed = JSON.parse(body);
			if (parsed.toolName) return { toolName: parsed.toolName, toolResult: parsed.toolResult ?? '' };
		} catch { /* payload may not be JSON */ }
		// Fallback: text field contains "🔧 {name} executed", toolName/toolResult in record props
		const text = getBody(env);
		const match = text.match(/^🔧\s*(.+?)\s+executed$/);
		if (match) return { toolName: match[1], toolResult: '' };
		return null;
	}

	/** Check if sender is Murakumo LLM (agent auto-reply). */
	function isMurakumoReply(env: ConvoEnvelope): boolean {
		return env.senderDid !== selfDid && env.senderDid.startsWith('did:web:');
	}

	function renderTextBody(body: string): string {
		let s = body
			.replace(/&/g, '&amp;')
			.replace(/</g, '&lt;')
			.replace(/>/g, '&gt;')
			.replace(/"/g, '&quot;')
			.replace(/'/g, '&#39;');
		s = s.replace(/\*\*(.+?)\*\*/g, '<strong class="font-semibold">$1</strong>');
		s = s.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener noreferrer" class="underline opacity-80">$1</a>');
		return s;
	}

	let contextMenuRkey = $state<string | null>(null);
	let contextMenuPos = $state({ x: 0, y: 0 });
	let reactionPickerRkey = $state<string | null>(null);

	const quickReactions = ['👍', '❤️', '🔥', '😂', '🚽', '💅', '😤', '✨'];

	function handleContextMenu(e: MouseEvent | TouchEvent, rkey: string) {
		e.preventDefault();
		const pos = 'touches' in e ? { x: e.touches[0].clientX, y: e.touches[0].clientY } : { x: e.clientX, y: e.clientY };
		contextMenuPos = pos;
		contextMenuRkey = rkey;
		reactionPickerRkey = null;
	}

	function closeContextMenu() { contextMenuRkey = null; reactionPickerRkey = null; }
	function handleReplyAction(rkey: string) { closeContextMenu(); onReply?.(rkey); }
	function handleReactAction(rkey: string) { contextMenuRkey = null; reactionPickerRkey = rkey; }
	function handleRedactAction(rkey: string) { closeContextMenu(); onRedact?.(rkey); }
	function handleThreadAction(rkey: string) { closeContextMenu(); onThread?.(rkey); }
	function handleReactionPick(rkey: string, emoji: string) { reactionPickerRkey = null; onReaction?.(rkey, emoji); }

	let scrollContainer = $state<HTMLDivElement | null>(null);

	const typingText = $derived.by(() => {
		if (!typing.length) return '';
		const names = typing.map((did) => displayName(did));
		if (names.length === 1) return `${names[0]} is typing...`;
		if (names.length === 2) return `${names[0]} and ${names[1]} are typing...`;
		return `${names[0]} and ${names.length - 1} others are typing...`;
	});
</script>

<!-- svelte-ignore a11y_click_events_have_key_events -->
<!-- svelte-ignore a11y_no_static_element_interactions -->
<div class="relative flex h-full flex-col" onclick={closeContextMenu}>

	{#if encrypted}
		<div class="flex items-center justify-center gap-2 border-b border-[#58CC02]/20 bg-[#58CC02]/5 px-4 py-1.5">
			<span class="text-[13px]">🔒</span>
			<span class="text-[12px] font-semibold text-[#58CC02]">End-to-end encrypted</span>
		</div>
	{/if}

	<div bind:this={scrollContainer} class="flex-1 overflow-y-auto scrollbar-none pb-2">
		{#if onLoadMore}
			<div class="flex justify-center py-3">
				<button
					type="button"
					class="rounded-full border border-gv2-border bg-gv2-bg-card px-4 py-2 text-[13px] font-semibold text-gv2-text-muted shadow-[0_3px_0_rgba(0,0,0,0.15)] touch-manipulation active:shadow-none active:translate-y-[3px] transition-all"
					onclick={onLoadMore}
				>Load more</button>
			</div>
		{/if}

		{#each renderableEnvelopes as env, idx (env.rkey)}
			{@const group = groupInfo.get(env.rkey)}
			{@const replyToEnvelope = env.replyTo ? envelopeById.get(env.replyTo) : null}
			{@const isSelf = env.senderDid === selfDid}
			{@const body = getBody(env)}
			{@const isSignalEncrypted = env.encryption !== 'plaintext' && !decryptedBodies.has(env.rkey)}

			{#if needsDateSeparator(idx)}
				<div class="flex items-center gap-3 px-4 py-3">
					<div class="h-px flex-1 bg-gv2-border/30"></div>
					<span class="rounded-full bg-gv2-bg-card px-3 py-0.5 text-[11px] font-bold text-gv2-text-muted shadow-sm">{dateLabel(env.createdAt)}</span>
					<div class="h-px flex-1 bg-gv2-border/30"></div>
				</div>
			{/if}

			{#if group?.isFirst}
				<div
					class="flex {isSelf ? 'flex-row-reverse' : 'flex-row items-end gap-2'} px-3 pb-0.5 pt-3"
					oncontextmenu={(e) => handleContextMenu(e, env.rkey)}
				>
					{#if !isSelf}
						<Avatar
							fallback={displayName(env.senderDid).slice(0, 2).toUpperCase()}
							size="sm"
							class="mb-0.5 flex-shrink-0 !bg-emerald-600 !text-white !text-[11px]"
						/>
					{/if}
					<div class="max-w-[72%]">
						{#if !isSelf}
							<div class="mb-1 flex items-center gap-1.5 pl-0.5">
								<span class="text-[13px] font-bold text-[var(--gv2-accent,#06c755)]">{displayName(env.senderDid)}</span>
								{#if participantTypes.get(env.senderDid) === 'agent'}
									<Badge value="Agent" variant="accent" class="!text-[9px] !h-4 !min-w-0 !px-1.5" />
								{:else if participantTypes.get(env.senderDid) === 'service'}
									<Badge value="Service" variant="warning" class="!text-[9px] !h-4 !min-w-0 !px-1.5" />
								{/if}
								{#if isMurakumoReply(env)}
									<span class="inline-flex items-center gap-0.5 rounded-full bg-purple-500/15 px-1.5 py-0.5 text-[9px] font-bold text-purple-400">
										<svg class="h-2.5 w-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 2a4 4 0 0 1 4 4v2h1a3 3 0 0 1 3 3v7a3 3 0 0 1-3 3H7a3 3 0 0 1-3-3v-7a3 3 0 0 1 3-3h1V6a4 4 0 0 1 4-4z"/><circle cx="9" cy="14" r="1" fill="currentColor"/><circle cx="15" cy="14" r="1" fill="currentColor"/></svg>
										Murakumo
									</span>
								{/if}
								<span class="text-[11px] text-gv2-text-muted">{timeLabel(env.createdAt)}</span>
							</div>
						{:else}
							<div class="mb-1 flex items-baseline justify-end gap-1.5 pr-0.5">
								<span class="text-[11px] text-gv2-text-muted">{timeLabel(env.createdAt)}</span>
							</div>
						{/if}

						{#if replyToEnvelope}
							<div class="mb-1.5 border-l-2 border-[#58CC02]/50 pl-2">
								<span class="text-[11px] font-semibold text-[#58CC02]/70">↩ {displayName(replyToEnvelope.senderDid)}</span>
								<p class="truncate text-[12px] text-gv2-text-muted">{decodeMessageBody(replyToEnvelope).slice(0, 60)}</p>
							</div>
						{/if}

						{#if getToolResult(env)}
						{@const toolRes = getToolResult(env)!}
							<!-- MCP Tool Result card -->
							<div class="w-full max-w-[300px] rounded-2xl border border-purple-500/20 bg-purple-500/[0.06] px-3.5 py-2.5 shadow-sm">
								<div class="flex items-center gap-2 mb-1.5">
									<div class="flex h-6 w-6 items-center justify-center rounded-lg bg-purple-500/20">
										<svg class="h-3.5 w-3.5 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></svg>
									</div>
									<span class="text-[12px] font-bold text-purple-400">{toolRes.toolName}</span>
									<span class="ml-auto rounded-full bg-purple-500/15 px-1.5 py-0.5 text-[9px] font-bold text-purple-300 uppercase tracking-wider">MCP</span>
								</div>
								{#if toolRes.toolResult}
									{@const isJson = toolRes.toolResult.startsWith('{') || toolRes.toolResult.startsWith('[')}
									<div class="rounded-lg bg-black/20 px-2.5 py-2 {isJson ? 'font-mono text-[11px]' : 'text-[13px]'} leading-relaxed text-gv2-text-primary/80 max-h-[200px] overflow-y-auto scrollbar-none">
										<pre class="whitespace-pre-wrap break-words">{isJson ? JSON.stringify(JSON.parse(toolRes.toolResult), null, 2).slice(0, 1500) : toolRes.toolResult.slice(0, 1500)}</pre>
									</div>
								{:else}
									<p class="text-[12px] text-purple-400/60">Tool executed successfully</p>
								{/if}
							</div>
						{:else if getCardPayload(env)}
						{@const card = getCardPayload(env)!}
							<!-- Protocol Canvas: card rendering -->
							<div class="w-full max-w-[280px]">
								{#if card.type === 'list'}
									<CardList payload={card.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card.type === 'form'}
									<CardForm payload={card.data} onAction={(a, d) => handleCardAction((env.convoId), a, d)} />
								{:else if card.type === 'table'}
									<CardTable payload={card.data} />
								{:else if card.type === 'carousel'}
									<CardCarousel payload={card.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card.type === 'chart'}
									<CardChart payload={card.data} />
								{:else if card.type === 'receipt'}
									<CardReceipt payload={card.data} />
								{:else if card.type === 'code'}
									<CardCode payload={card.data} />
								{:else if card.type === 'poll'}
									<CardPoll payload={card.data} onAction={(a, d) => handleCardAction((env.convoId), a, d)} />
								{:else if card.type === 'calendar'}
									<CardCalendar payload={card.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card.type === 'kanban'}
									<CardKanban payload={card.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card.type === 'confirmation'}
									<CardConfirmation payload={card.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card.type === 'metric-dashboard'}
									<CardMetricDashboard payload={card.data} />
								{:else if card.type === 'image-gallery'}
									<CardImageGallery payload={card.data} />
								{:else if card.type === 'map-pin'}
									<CardMapPin payload={card.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card.type === 'embed'}
									<CardEmbed payload={card.data} />
								{:else if card.type === 'game'}
									<CardGame payload={card.data} />
								{:else if card.type === 'person'}
									<CardPerson payload={card.data} />
								{:else if card.type === 'organization'}
									<CardOrganization payload={card.data} />
								{:else if card.type === 'service'}
									<CardService payload={card.data} />
								{:else if card.type === 'system'}
									<CardSystem payload={card.data} />
								{:else}
									<div class="rounded-[18px] bg-gv2-bg-card px-3.5 py-2.5 shadow-sm">
										<p class="text-[13px] text-gv2-text-muted">Unsupported card: {card.type}</p>
									</div>
								{/if}
							</div>
						{:else}
							<div class="{isSelf ? 'rounded-[18px] rounded-tr-[5px] bg-[#58CC02]' : 'rounded-[18px] rounded-tl-[5px] bg-gv2-bg-card'} px-3.5 py-2.5 shadow-sm">
								{#if isSignalEncrypted}
									<p class="text-[15px] leading-snug {isSelf ? 'text-white/70' : 'text-gv2-text-muted'}">🔒 Encrypted</p>
								{:else}
									<p class="whitespace-pre-wrap break-words text-[15px] leading-snug {isSelf ? 'text-white' : 'text-gv2-text-primary'}">
										{@html renderTextBody(body)}
									</p>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{:else}
				<div
					class="flex {isSelf ? 'flex-row-reverse' : ''} px-3 py-0.5"
					oncontextmenu={(e) => handleContextMenu(e, env.rkey)}
				>
					{#if !isSelf}<div class="w-8 flex-shrink-0"></div>{/if}
					<div class="max-w-[72%]">
						{#if replyToEnvelope}
							<div class="mb-1 border-l-2 border-[#58CC02]/50 pl-2">
								<span class="text-[11px] font-semibold text-[#58CC02]/70">↩ {displayName(replyToEnvelope.senderDid)}</span>
								<p class="truncate text-[12px] text-gv2-text-muted">{decodeMessageBody(replyToEnvelope).slice(0, 60)}</p>
							</div>
						{/if}
						{#if getToolResult(env)}
						{@const toolRes2 = getToolResult(env)!}
							<div class="w-full max-w-[300px] rounded-2xl border border-purple-500/20 bg-purple-500/[0.06] px-3.5 py-2.5 shadow-sm">
								<div class="flex items-center gap-2 mb-1.5">
									<div class="flex h-6 w-6 items-center justify-center rounded-lg bg-purple-500/20">
										<svg class="h-3.5 w-3.5 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" /></svg>
									</div>
									<span class="text-[12px] font-bold text-purple-400">{toolRes2.toolName}</span>
									<span class="ml-auto rounded-full bg-purple-500/15 px-1.5 py-0.5 text-[9px] font-bold text-purple-300 uppercase tracking-wider">MCP</span>
								</div>
								{#if toolRes2.toolResult}
									{@const isJson2 = toolRes2.toolResult.startsWith('{') || toolRes2.toolResult.startsWith('[')}
									<div class="rounded-lg bg-black/20 px-2.5 py-2 {isJson2 ? 'font-mono text-[11px]' : 'text-[13px]'} leading-relaxed text-gv2-text-primary/80 max-h-[200px] overflow-y-auto scrollbar-none">
										<pre class="whitespace-pre-wrap break-words">{isJson2 ? JSON.stringify(JSON.parse(toolRes2.toolResult), null, 2).slice(0, 1500) : toolRes2.toolResult.slice(0, 1500)}</pre>
									</div>
								{:else}
									<p class="text-[12px] text-purple-400/60">Tool executed successfully</p>
								{/if}
							</div>
						{:else if getCardPayload(env)}
						{@const card2 = getCardPayload(env)!}
							<div class="w-full max-w-[280px]">
								{#if card2.type === 'list'}
									<CardList payload={card2.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else if card2.type === 'confirmation'}
									<CardConfirmation payload={card2.data} onAction={(a) => handleCardAction((env.convoId), a)} />
								{:else}
									<div class="rounded-[18px] bg-gv2-bg-card px-3.5 py-2.5 shadow-sm">
										<p class="text-[13px] text-gv2-text-muted">{card2.type} card</p>
									</div>
								{/if}
							</div>
						{:else}
							<div class="{isSelf ? 'rounded-[18px] rounded-tr-[5px] bg-[#58CC02]' : 'rounded-[18px] rounded-tl-[5px] bg-gv2-bg-card'} px-3.5 py-2.5 shadow-sm">
								{#if isSignalEncrypted}
									<p class="text-[15px] leading-snug {isSelf ? 'text-white/70' : 'text-gv2-text-muted'}">🔒 Encrypted</p>
								{:else}
									<p class="whitespace-pre-wrap break-words text-[15px] leading-snug {isSelf ? 'text-white' : 'text-gv2-text-primary'}">
										{@html renderTextBody(body)}
									</p>
								{/if}
							</div>
						{/if}
					</div>
				</div>
			{/if}
		{/each}

		{#if typing.length > 0}
			<div class="flex items-center gap-2.5 px-4 py-2">
				<div class="flex gap-1">
					<span class="inline-block h-2.5 w-2.5 animate-bounce rounded-full bg-[#58CC02] [animation-delay:0ms]"></span>
					<span class="inline-block h-2.5 w-2.5 animate-bounce rounded-full bg-[#58CC02] [animation-delay:150ms]"></span>
					<span class="inline-block h-2.5 w-2.5 animate-bounce rounded-full bg-[#58CC02] [animation-delay:300ms]"></span>
				</div>
				<span class="text-[13px] font-medium text-[#58CC02]">{typingText}</span>
			</div>
		{/if}
	</div>

	{#if contextMenuRkey}
		<div
			class="fixed z-50 min-w-[180px] overflow-hidden rounded-2xl border border-gv2-border/40 bg-gv2-bg-primary shadow-2xl backdrop-blur-xl"
			style="left: {Math.min(contextMenuPos.x, (typeof window !== 'undefined' ? window.innerWidth : 400) - 200)}px; top: {contextMenuPos.y}px;"
		>
			{#each [
				{ label: '↩ Reply', onclick: () => handleReplyAction(contextMenuRkey!) },
				{ label: '😂 React', onclick: () => handleReactAction(contextMenuRkey!) },
				{ label: '🧵 Thread', onclick: () => handleThreadAction(contextMenuRkey!) },
			] as item}
				<button
					type="button"
					class="flex w-full items-center gap-3 px-4 py-3 text-left text-[14px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
					onclick={item.onclick}
				>{item.label}</button>
			{/each}
			{#if envelopes.find((e) => e.rkey === contextMenuRkey)?.senderDid === selfDid}
				<div class="mx-3 h-px bg-gv2-border/30"></div>
				<button type="button" class="flex w-full items-center gap-3 px-4 py-3 text-left text-[14px] font-semibold text-red-400 touch-manipulation active:bg-gv2-bg-hover" onclick={() => handleRedactAction(contextMenuRkey!)}>🗑️ Delete</button>
			{/if}
		</div>
	{/if}

	{#if reactionPickerRkey}
		<div
			class="fixed z-50 flex gap-0.5 rounded-full border border-gv2-border/40 bg-gv2-bg-primary px-2 py-1.5 shadow-2xl backdrop-blur-xl"
			style="left: {Math.min(contextMenuPos.x, (typeof window !== 'undefined' ? window.innerWidth : 400) - 360)}px; top: {contextMenuPos.y - 56}px;"
		>
			{#each quickReactions as emoji}
				<button
					type="button"
					class="flex h-[44px] w-[44px] items-center justify-center rounded-full text-[20px] touch-manipulation active:bg-gv2-bg-hover active:scale-125 transition-transform"
					onclick={(e) => { e.stopPropagation(); handleReactionPick(reactionPickerRkey!, emoji); }}
				>{emoji}</button>
			{/each}
		</div>
	{/if}
</div>
