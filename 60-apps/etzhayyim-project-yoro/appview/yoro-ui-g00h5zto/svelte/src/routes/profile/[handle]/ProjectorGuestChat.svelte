<script lang="ts">
	import { createProjectConvo, getSession, sendProjectMessage } from '$lib/atproto-agent';
	import type { ConvoId } from '$lib/atproto-agent';
	import { useLocalLLM, type ChatMessage } from '$lib/provider/local-llm.svelte';

	interface Props {
		did: string;
		agentName: string;
	}

	let { did, agentName }: Props = $props();

	let convoId = $state<ConvoId | null>(null);
	let input = $state('');
	let sending = $state(false);
	let messages = $state<Array<{ id: string; from: string; text: string; isAgent: boolean; ts: number }>>([]);
	let guestHistory = $state<ChatMessage[]>([]);

	const localLLM = useLocalLLM();
	const isAuthenticated = $derived(!!getSession());

	async function ensureConvo(): Promise<ConvoId | null> {
		if (convoId) return convoId;
		const result = await createProjectConvo(did);
		const next = result?.convo?.convoId;
		if (next) convoId = next;
		return next ?? null;
	}

	async function sendGuestChat(text: string) {
		const replyId = `guest-${Date.now()}`;
		messages = [...messages, {
			id: replyId,
			from: agentName,
			text: localLLM.isReady ? '' : 'Gemma E2B を読み込んでいます...',
			isAgent: true,
			ts: Date.now(),
		}];

		if (!localLLM.isReady) await localLLM.init('gemma4-e2b');
		if (!localLLM.isAvailable) {
			const errorText = localLLM.error || 'このブラウザでは WebGPU 推論を開始できませんでした。';
			messages = messages.map((msg) => msg.id === replyId ? { ...msg, text: errorText } : msg);
			return;
		}

		const requestMessages: ChatMessage[] = [
			{
				role: 'system',
				content: [
					`You are ${agentName}, an actor on YORO.`,
					`Your DID is ${did}.`,
					'You are speaking with an unauthenticated visitor through browser-local Gemma E2B IT inference.',
					'Reply in the user language. Keep responses concise and conversational.',
				].join('\n'),
			},
			...guestHistory.slice(-12),
			{ role: 'user', content: text },
		];

		let replyText = '';
		const stream = localLLM.chatCompletionStream(requestMessages, { maxTokens: 512, temperature: 0.7 });
		for await (const chunk of stream) {
			replyText += chunk;
			messages = messages.map((msg) => msg.id === replyId ? { ...msg, text: replyText } : msg);
		}

		if (!replyText.trim()) {
			replyText = await localLLM.chatCompletion(requestMessages, { maxTokens: 512, temperature: 0.7 });
			messages = messages.map((msg) => msg.id === replyId ? { ...msg, text: replyText } : msg);
		}

		guestHistory = [...guestHistory, { role: 'user', content: text }, { role: 'assistant', content: replyText }].slice(-16);
	}

	async function sendChat() {
		const text = input.trim();
		if (!text || sending) return;
		input = '';
		sending = true;
		messages = [...messages, { id: `user-${Date.now()}`, from: 'You', text, isAgent: false, ts: Date.now() }];

		try {
			if (getSession()) {
				const id = await ensureConvo();
				if (id) await sendProjectMessage(id, text);
			} else {
				await sendGuestChat(text);
			}
		} catch (error) {
			messages = [...messages, {
				id: `error-${Date.now()}`,
				from: agentName,
				text: error instanceof Error ? error.message : String(error),
				isAgent: true,
				ts: Date.now(),
			}];
		} finally {
			sending = false;
			if (messages.length > 40) messages = messages.slice(-40);
		}
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			void sendChat();
		}
	}
</script>

<section class="mx-2 mt-3 rounded-xl border border-gv2-border/40 bg-gv2-bg-secondary/70 px-3 py-3">
	<div class="mb-2 flex items-center justify-between gap-3">
		<div class="min-w-0">
			<div class="truncate text-[13px] font-bold text-gv2-text-primary">{agentName}</div>
			<div class="truncate text-[11px] text-gv2-text-muted">{isAuthenticated ? 'Projector' : 'Gemma E2B / Web推論'}</div>
		</div>
		<span class="rounded-full bg-[#1185FE]/10 px-2 py-0.5 text-[11px] font-semibold text-[#1185FE]">message</span>
	</div>

	{#if messages.length > 0}
		<div class="mb-2 max-h-56 space-y-2 overflow-y-auto pr-1">
			{#each messages as msg (msg.id)}
				<div class="flex {msg.isAgent ? 'justify-start' : 'justify-end'}">
					<div class="max-w-[82%] rounded-2xl px-3 py-2 text-[13px] leading-relaxed {msg.isAgent ? 'bg-gv2-bg-hover text-gv2-text-primary' : 'bg-[#1185FE] text-white'}">
						{msg.text}
					</div>
				</div>
			{/each}
		</div>
	{/if}

	<div class="flex items-center gap-2 rounded-xl bg-gv2-bg-hover/60 px-3 py-2">
		<input
			type="text"
			bind:value={input}
			onkeydown={handleKeydown}
			placeholder={isAuthenticated ? `${agentName} に話しかける...` : `${agentName} と話す (Gemma E2B / Web推論)`}
			class="min-w-0 flex-1 bg-transparent text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted outline-none"
			disabled={sending}
		/>
		<button
			type="button"
			class="flex h-8 w-8 flex-shrink-0 items-center justify-center rounded-full bg-[#1185FE] text-white touch-manipulation active:opacity-80 disabled:opacity-40"
			onclick={sendChat}
			disabled={!input.trim() || sending}
			aria-label="送信"
		>
			<svg class="h-4 w-4" viewBox="0 0 24 24" fill="currentColor"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
		</button>
	</div>

	{#if !isAuthenticated && localLLM.isLoading}
		<div class="mt-1 px-1 text-[11px] text-gv2-text-muted">
			Gemma E2B loading {localLLM.loadProgress}% {localLLM.loadLabel}
		</div>
	{/if}
</section>
