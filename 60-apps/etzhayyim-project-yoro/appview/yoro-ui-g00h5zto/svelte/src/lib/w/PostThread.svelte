<script lang="ts">
	import { Avatar } from '@etzhayyim/design-system';
	import { getThread, sendProjectMessage, memberLabel, decodeMessageBody, isEncryptedVal } from '$lib/atproto-agent';
	import type { ConvoEnvelope } from '$lib/atproto-agent';
	import { useLocalLLM } from '$lib/provider/local-llm.svelte.js';

	interface Props {
		convoId: string;
		rootRkey: string;
		rootSenderDid: string;
		rootBody: string;
		selfDid?: string;
		onClose?: () => void;
	}

	let { convoId, rootRkey, rootSenderDid, rootBody, selfDid = '', onClose }: Props = $props();

	let replies = $state<ConvoEnvelope[]>([]);
	let loading = $state(true);
	let replyText = $state('');
	let sending = $state(false);

	$effect(() => {
		void loadThread();
	});

	async function loadThread() {
		loading = true;
		try {
			replies = await getThread(convoId, rootRkey);
		} finally {
			loading = false;
		}
	}

	const llm = useLocalLLM();

	async function handleSend() {
		const body = replyText.trim();
		if (!body || sending) return;
		sending = true;
		try {
			const e2e = llm.isReady && !!selfDid;
			await sendProjectMessage(convoId, body, { replyTo: rootRkey, threadId: rootRkey, encrypt: e2e });
			replyText = '';
			await loadThread();
		} finally {
			sending = false;
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void handleSend(); }
	}

	function displayName(did: string): string {
		if (did === selfDid) return 'You';
		return memberLabel(did);
	}

	function timeLabel(ts: string): string {
		return new Date(ts).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit' });
	}
</script>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 px-4">
		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
			onclick={onClose}
			aria-label="閉じる"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
				<path d="M18 6L6 18M6 6l12 12" />
			</svg>
		</button>
		<span class="text-[15px] font-bold text-gv2-text-primary">🧵 スレッド</span>
	</div>

	<div class="border-b border-gv2-border/40 px-4 py-3">
		<div class="flex items-center gap-2 mb-2">
			<Avatar fallback={displayName(rootSenderDid).slice(0, 2).toUpperCase()} size="sm" class="!bg-emerald-600 !text-white !text-[11px]" />
			<span class="text-[13px] font-bold text-[#58CC02]">{displayName(rootSenderDid)}</span>
		</div>
		<p class="text-[15px] text-gv2-text-primary whitespace-pre-wrap break-words">{rootBody}</p>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none px-4 py-2 space-y-3">
		{#if loading}
			<div class="flex justify-center py-4">
				<div class="flex gap-1">
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[#58CC02] [animation-delay:0ms]"></span>
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[#58CC02] [animation-delay:150ms]"></span>
					<span class="inline-block h-2 w-2 animate-bounce rounded-full bg-[#58CC02] [animation-delay:300ms]"></span>
				</div>
			</div>
		{:else if replies.length === 0}
			<p class="py-4 text-center text-[14px] text-gv2-text-muted">まだ返信なし 🫙</p>
		{:else}
			{#each replies as reply (reply.rkey)}
				{@const isSelf = reply.senderDid === selfDid}
				<div class="flex {isSelf ? 'flex-row-reverse' : 'flex-row'} items-end gap-2">
					{#if !isSelf}
						<Avatar fallback={displayName(reply.senderDid).slice(0, 2).toUpperCase()} size="sm" class="flex-shrink-0 !bg-emerald-600 !text-white !text-[11px]" />
					{/if}
					<div class="max-w-[80%]">
						{#if !isSelf}
							<div class="mb-0.5 flex items-baseline gap-1.5 pl-0.5">
								<span class="text-[12px] font-bold text-[#58CC02]">{displayName(reply.senderDid)}</span>
								<span class="text-[11px] text-gv2-text-muted">{timeLabel(reply.createdAt)}</span>
							</div>
						{:else}
							<div class="mb-0.5 flex items-baseline justify-end gap-1.5 pr-0.5">
								<span class="text-[11px] text-gv2-text-muted">{timeLabel(reply.createdAt)}</span>
							</div>
						{/if}
						<div class="{isSelf ? 'rounded-[18px] rounded-tr-[5px] bg-[#58CC02]' : 'rounded-[18px] rounded-tl-[5px] bg-gv2-bg-card'} px-3.5 py-2.5 shadow-sm">
							<p class="whitespace-pre-wrap break-words text-[15px] leading-snug {isSelf ? 'text-white' : 'text-gv2-text-primary'}">{decodeMessageBody(reply)}</p>
						</div>
					</div>
				</div>
			{/each}
		{/if}
	</div>

	<div class="border-t border-gv2-border/40 px-3 pb-[max(env(safe-area-inset-bottom),10px)] pt-2">
		<div class="flex items-end gap-2">
			<div class="relative min-w-0 flex-1">
				<textarea
					bind:value={replyText}
					class="block max-h-[120px] min-h-[44px] w-full resize-none rounded-[22px] bg-gv2-bg-card px-4 py-3 text-[15px] leading-tight text-gv2-text-primary placeholder-gv2-text-muted/50 shadow-sm focus:outline-none focus:ring-2 focus:ring-[#58CC02]/40"
					rows="1"
					placeholder="スレッドに返信... 🧵"
					onkeydown={handleKeydown}
					disabled={sending}
				></textarea>
			</div>
			{#if replyText.trim()}
				<button
					type="button"
					class="flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full bg-[#58CC02] text-white shadow-[0_4px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[4px] disabled:opacity-40 transition-all duration-75"
					onclick={() => void handleSend()}
					disabled={sending}
					aria-label="送信"
				>
					<svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
						<path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
					</svg>
				</button>
			{/if}
		</div>
	</div>
</div>
