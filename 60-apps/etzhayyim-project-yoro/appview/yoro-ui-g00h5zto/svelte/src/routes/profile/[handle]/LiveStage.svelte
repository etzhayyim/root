<script lang="ts">
	import { onMount } from 'svelte';
	import { fly } from 'svelte/transition';
	import { sendProjectMessage, createProjectConvo, getAuthorFeed, getSession, subscribeAtprotoStream, atQuery } from '$lib/atproto-agent';
	import type { ConvoId } from '$lib/atproto-agent';
	import { useLocalLLM, type ChatMessage } from '$lib/provider/local-llm.svelte';

	/** Extract text body from a AT Protocol envelope. */
	function extractBody(env: { contentType?: string; payload: string }): string {
		if (env.contentType === 'text/plain') {
			try { return atob(env.payload); } catch { return env.payload; }
		}
		return env.payload;
	}

	interface Props {
		did: string;
		agentName: string;
		nanoid?: string;
	}

	let { did, agentName, nanoid }: Props = $props();

	// AT Protocol convo for this live stage DM
	let convoId = $state<ConvoId | null>(null);
	let convoLoading = $state(false);

	// Chat state
	let chatMessages = $state<Array<{ id: string; from: string; text: string; isAgent: boolean; ts: number }>>([]);
	let chatInput = $state('');
	let chatSending = $state(false);
	let chatOpen = $state(true);
	const localLLM = useLocalLLM();
	let guestChatHistory = $state<ChatMessage[]>([]);

	// KAMI engine state
	let stageCanvas = $state<HTMLCanvasElement | null>(null);
	let kamiReady = $state(false);
	let kamiError = $state('');

	// Action states
	let showEmoteWheel = $state(false);
	let showTipSheet = $state(false);
	let tipAmount = $state(500);
	let musicPlaying = $state(false);
	let musicTitle = $state('');
	let viewerCount = $state(1);

	// Emotes
	const emotes = [
		{ id: 'wave', icon: '\u{1F44B}', label: 'Wave' },
		{ id: 'clap', icon: '\u{1F44F}', label: 'Clap' },
		{ id: 'fire', icon: '\u{1F525}', label: 'Fire' },
		{ id: 'heart', icon: '\u{2764}\u{FE0F}', label: 'Heart' },
		{ id: 'laugh', icon: '\u{1F602}', label: 'Laugh' },
		{ id: 'star', icon: '\u{2B50}', label: 'Star' },
		{ id: 'skull', icon: '\u{1F480}', label: 'Skull' },
		{ id: 'crown', icon: '\u{1F451}', label: 'Crown' },
	];

	// Tip presets
	const tipPresets = [100, 500, 1000, 5000, 10000];

	// Floating emote effects
	let floatingEmotes = $state<Array<{ id: string; emoji: string; x: number; y: number }>>([]);

	// Agent state
	let greetingText = $state('');
	let streamConn: { close: () => void } | null = null;
	let hasGreeted = false;

	// ── KAMI SDF Character Model (base humanoid) ──
	// SDF JSON-LD: SmoothUnion で organic body。SCAD/NeRF は asset 種別ごとに使い分け。
	// - Body/Character: SDF (SmoothUnion k=0.3, organic fusion)
	// - Stage props/furniture: SCAD (hard union, architectural)
	// - Photorealistic textures: NeRF (density grid)
	function buildCharacterSdf(skinColor: string, hairColor: string, eyeColor: string, outfitColor: string): string {
		const sdf = {
			"@type": "SmoothUnion",
			"k": 0.3,
			"defs": {
				// Reusable eye part
				"eye_white": { "@type": "Sphere", "r": 0.18, "scale": [1, 1.1, 0.6], "color": "white" },
				"eye_iris": { "@type": "Sphere", "r": 0.12, "scale": [1, 1, 0.5], "color": eyeColor },
				"eye_pupil": { "@type": "Sphere", "r": 0.06, "scale": [1, 1, 0.4], "color": "#111111" },
				"eye_highlight": { "@type": "Sphere", "r": 0.04, "scale": [1, 1, 0.3], "color": "#FFFFFF" },
				// Reusable hand
				"hand": { "@type": "Sphere", "r": 0.15, "color": skinColor },
				// Reusable shoe
				"shoe": { "@type": "Box", "size": [0.22, 0.12, 0.32], "color": "#1a1020" },
			},
			"children": [
				// ── Head ──
				{ "@type": "Sphere", "r": 0.55, "pos": [0, 3.3, 0], "color": skinColor },
				// Hair (top cap)
				{ "@type": "Sphere", "r": 0.58, "pos": [0, 3.55, -0.05], "scale": [1, 0.7, 1], "color": hairColor },
				// Hair bangs
				{ "@type": "Box", "size": [0.9, 0.15, 0.3], "pos": [0, 3.55, 0.35], "color": hairColor },
				// Side hair L
				{ "@type": "Capsule", "h": 0.5, "r": 0.12, "pos": [-0.5, 3.1, 0], "color": hairColor },
				// Side hair R
				{ "@type": "Capsule", "h": 0.5, "r": 0.12, "pos": [0.5, 3.1, 0], "color": hairColor },
				// Eyes
				{ "$ref": "eye_white", "pos": [-0.2, 3.3, 0.42] },
				{ "$ref": "eye_white", "pos": [0.2, 3.3, 0.42] },
				{ "$ref": "eye_iris", "pos": [-0.2, 3.28, 0.48] },
				{ "$ref": "eye_iris", "pos": [0.2, 3.28, 0.48] },
				{ "$ref": "eye_pupil", "pos": [-0.2, 3.27, 0.52] },
				{ "$ref": "eye_pupil", "pos": [0.2, 3.27, 0.52] },
				{ "$ref": "eye_highlight", "pos": [-0.17, 3.32, 0.53] },
				{ "$ref": "eye_highlight", "pos": [0.23, 3.32, 0.53] },
				// Nose
				{ "@type": "Sphere", "r": 0.06, "pos": [0, 3.15, 0.5], "color": skinColor },
				// Mouth (smile curve)
				{ "@type": "Capsule", "h": 0.12, "r": 0.04, "pos": [0, 3.05, 0.45], "rot": [0, 0, 90], "color": "#d07070" },
				// Blush
				{ "@type": "Sphere", "r": 0.1, "pos": [-0.35, 3.1, 0.38], "scale": [1, 0.5, 0.3], "color": "#ffb0b0" },
				{ "@type": "Sphere", "r": 0.1, "pos": [0.35, 3.1, 0.38], "scale": [1, 0.5, 0.3], "color": "#ffb0b0" },

				// ── Neck ──
				{ "@type": "Cylinder", "h": 0.2, "r": 0.15, "pos": [0, 2.75, 0], "color": skinColor },

				// ── Torso ──
				{ "@type": "Box", "size": [0.7, 0.9, 0.4], "pos": [0, 2.2, 0], "color": outfitColor },
				// Collar
				{ "@type": "Torus", "R": 0.22, "r": 0.04, "pos": [0, 2.65, 0.05], "rot": [90, 0, 0], "color": "#ffffff" },

				// ── Arms ──
				// Left arm
				{ "@type": "Capsule", "h": 0.6, "r": 0.1, "pos": [-0.5, 2.2, 0], "rot": [0, 0, 12], "color": outfitColor },
				{ "$ref": "hand", "pos": [-0.55, 1.65, 0] },
				// Right arm
				{ "@type": "Capsule", "h": 0.6, "r": 0.1, "pos": [0.5, 2.2, 0], "rot": [0, 0, -12], "color": outfitColor },
				{ "$ref": "hand", "pos": [0.55, 1.65, 0] },

				// ── Legs ──
				// Left leg
				{ "@type": "Capsule", "h": 0.7, "r": 0.12, "pos": [-0.18, 1.1, 0], "color": "#2a2040" },
				{ "$ref": "shoe", "pos": [-0.18, 0.5, 0.05] },
				// Right leg
				{ "@type": "Capsule", "h": 0.7, "r": 0.12, "pos": [0.18, 1.1, 0], "color": "#2a2040" },
				{ "$ref": "shoe", "pos": [0.18, 0.5, 0.05] },
			],
		};
		return JSON.stringify(sdf);
	}

	// Default character palette (will be loaded from agent profile via PDS)
	const defaultSdf = buildCharacterSdf('#f0c8a0', '#2a1a3e', '#4a2080', '#7c3aed');

	/** Ensure a AT Protocol DM convo exists with this agent. */
	async function ensureConvo(): Promise<ConvoId | null> {
		if (convoId) return convoId;
		if (convoLoading) return null;
		const session = getSession();
		if (!session) return null;

		convoLoading = true;
		try {
			const result = await createProjectConvo(did);
			convoId = result?.convo?.convoId as ConvoId;

			// Load recent posts from the agent's feed as chat history
			try {
				const feedResult = await getAuthorFeed(did, { limit: 20 });
				for (const item of feedResult.feed ?? []) {
					chatMessages = [...chatMessages, {
						id: item.post.rkey,
						from: agentName,
						text: item.post.text ?? '',
						isAgent: true,
						ts: new Date(item.post.indexedAt).getTime(),
					}];
				}
			} catch (e) {
				console.warn('livestage: loadFeed failed', e);
			}

			streamConn = subscribeAtprotoStream(
				(event) => {
					if (event.action !== 'create' || !event.envelope) return;
					const env = event.envelope;
					const isAgent = env.senderDid === did;
					if (!isAgent) return;
					const text = extractBody(env);
					chatMessages = [...chatMessages, {
						id: env.rkey,
						from: agentName,
						text,
						isAgent: true,
						ts: new Date(env.createdAt).getTime(),
					}];
					if (chatMessages.length > 50) chatMessages = chatMessages.slice(-50);
				},
				{ convoIds: [convoId] },
			);

			return convoId;
		} catch (e) {
			console.warn('livestage: ensureConvo failed', e);
			return null;
		} finally {
			convoLoading = false;
		}
	}

	async function sendGuestChat(text: string): Promise<void> {
		const replyId = `local-reply-${Date.now()}`;
		chatMessages = [...chatMessages, {
			id: replyId,
			from: agentName,
			text: localLLM.isReady ? '' : 'Gemma E2B を読み込んでいます...',
			isAgent: true,
			ts: Date.now(),
		}];

		if (!localLLM.isReady) {
			await localLLM.init('gemma4-e2b');
		}
		if (!localLLM.isReady) {
			const reason = localLLM.error || 'このブラウザでは WebGPU 推論を開始できませんでした。';
			chatMessages = chatMessages.map((msg) =>
				msg.id === replyId ? { ...msg, text: reason } : msg,
			);
			return;
		}

		const messages: ChatMessage[] = [
			{
				role: 'system',
				content: [
					`You are ${agentName}, an actor on YORO.`,
					`Your DID is ${did}.`,
					'You are speaking with an unauthenticated visitor through browser-local Gemma E2B IT inference.',
					'Reply in the user language. Keep responses concise and conversational.',
				].join('\n'),
			},
			...guestChatHistory.slice(-12),
			{ role: 'user', content: text },
		];

		let streamed = '';
		for await (const token of localLLM.chatCompletionStream(messages, { maxTokens: 512, temperature: 0.7 })) {
			streamed += token;
			chatMessages = chatMessages.map((msg) =>
				msg.id === replyId ? { ...msg, text: streamed } : msg,
			);
		}

		const finalText = streamed.trim() || await localLLM.chatCompletion(messages, { maxTokens: 512, temperature: 0.7 }) || '返答を生成できませんでした。';
		chatMessages = chatMessages.map((msg) =>
			msg.id === replyId ? { ...msg, text: finalText } : msg,
		);
		guestChatHistory = [...guestChatHistory, { role: 'user', content: text }, { role: 'assistant', content: finalText }].slice(-16);
	}

	onMount(() => {
		if (!stageCanvas) return;

		const canvasId = stageCanvas.id;

		// Load KAMI engine and render stage + character
		(async () => {
			try {
				// @ts-ignore — CDN module, resolved at runtime (static assets served by yoro)
				const kami: any = await import(/* @vite-ignore */ 'https://cdn.etzhayyim.com/kami/kami-web.js');
				await kami.default(); // init WASM

				// 1. Try loading scene from PDS (baminiku stream data)
				let sceneLoaded = false;
				try {
					const data = await atQuery<{ scene_json?: string }>('com.etzhayyim.convo.subscribeStream', {
						'agent_id': nanoid ?? agentName,
						did,
					}).catch((_err) => null);
					if (data) {
						if (data.scene_json) {
							await kami.run_embed(canvasId, data.scene_json);
							sceneLoaded = true;
						}
					}
				} catch (e) {
					console.warn('livestage: PDS scene fetch failed, using SDF character', e);
				}

				// 2. Fallback: render SDF character model directly
				if (!sceneLoaded) {
					await kami.run_embed_sdf_jsonld(canvasId, defaultSdf, 48, 'sparse');
				}

				kamiReady = true;
			} catch (e) {
				console.warn('livestage: KAMI engine init failed', e);
				kamiError = 'WebGPU not available';
				kamiReady = true;
			}
		})();

		viewerCount = Math.floor(Math.random() * 5) + 1;

		// Viewer arrival greeting
		if (!hasGreeted) {
			hasGreeted = true;
			setTimeout(() => {
				const greetings = ['いらっしゃい！', 'ようこそ！', 'こんにちは！', 'やっほー！', '見に来てくれてありがとう！'];
				greetingText = greetings[Math.floor(Math.random() * greetings.length)];
				chatMessages = [...chatMessages, {
					id: `greet-${Date.now()}`,
					from: agentName,
					text: `\u{1F44B} ${greetingText}`,
					isAgent: true,
					ts: Date.now(),
				}];
				setTimeout(() => { greetingText = ''; }, 3500);
			}, 1200);
		}

		ensureConvo();

		return () => {
			streamConn?.close();
		};
	});

	async function sendChat() {
		if (!chatInput.trim() || chatSending) return;
		const text = chatInput.trim();
		chatInput = '';
		chatSending = true;

		const msgId = `msg-${Date.now()}`;
		chatMessages = [...chatMessages, { id: msgId, from: 'You', text, isAgent: false, ts: Date.now() }];

		try {
			if (getSession()) {
				const ch = await ensureConvo();
				if (!ch) return;
				await sendProjectMessage(ch, text);
			} else {
				await sendGuestChat(text);
			}
		} catch (e) {
			console.warn('livestage: sendChat failed', e);
		} finally {
			chatSending = false;
		}

		if (chatMessages.length > 50) chatMessages = chatMessages.slice(-50);
	}

	async function sendEmote(emote: { id: string; icon: string }) {
		showEmoteWheel = false;
		const floatId = `float-${Date.now()}-${Math.random()}`;
		const x = 20 + Math.random() * 60;
		floatingEmotes = [...floatingEmotes, { id: floatId, emoji: emote.icon, x, y: 80 }];
		setTimeout(() => { floatingEmotes = floatingEmotes.filter(e => e.id !== floatId); }, 2000);

		chatMessages = [...chatMessages, { id: `emote-${Date.now()}`, from: 'You', text: emote.icon, isAgent: false, ts: Date.now() }];

		try {
			const ch = await ensureConvo();
			if (!ch) return;
			await sendProjectMessage(ch, JSON.stringify({ emote: emote.id, icon: emote.icon }), {
				contentType: 'application/vnd.etzhayyim.baminiku.emote',
			});
		} catch (e) {
			console.warn('livestage: sendEmote failed', e);
		}
	}

	async function sendTip() {
		showTipSheet = false;
		const amount = tipAmount;
		const floatId = `tip-${Date.now()}`;
		floatingEmotes = [...floatingEmotes, { id: floatId, emoji: '\u{1F4B0}', x: 50, y: 50 }];
		setTimeout(() => { floatingEmotes = floatingEmotes.filter(e => e.id !== floatId); }, 3000);

		chatMessages = [...chatMessages, { id: `tip-${Date.now()}`, from: 'You', text: `\u{1F4B0} \u00A5${amount.toLocaleString()} tip!`, isAgent: false, ts: Date.now() }];

		try {
			const ch = await ensureConvo();
			if (!ch) return;
			await sendProjectMessage(ch, JSON.stringify({ amount, currency: 'JPY' }), {
				contentType: 'application/vnd.etzhayyim.baminiku.tip',
			});
		} catch (e) {
			console.warn('livestage: sendTip failed', e);
		}
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendChat(); }
	}

	let isAuthenticated = $derived(!!getSession());
</script>

<style>
	@keyframes floatUp {
		0% { opacity: 1; transform: translateY(0) scale(1); }
		100% { opacity: 0; transform: translateY(-120px) scale(1.5); }
	}
	@keyframes greetSlide {
		0% { opacity: 0; transform: translateY(8px) scale(0.8); }
		20% { opacity: 1; transform: translateY(0) scale(1); }
		80% { opacity: 1; transform: translateY(0) scale(1); }
		100% { opacity: 0; transform: translateY(-6px) scale(0.9); }
	}
</style>

<!-- KAMI Live Stage (WebGPU only) -->
<div class="relative w-full overflow-hidden rounded-2xl bg-[#060210]" style="aspect-ratio: 16/9; min-height: 240px; max-height: 400px;">
	<!-- KAMI WebGPU Canvas (full stage) -->
	<canvas
		bind:this={stageCanvas}
		id="kami-stage-{nanoid ?? 'default'}"
		class="absolute inset-0 h-full w-full"
	></canvas>

	<!-- WebGPU error fallback (text only, no CSS avatar) -->
	{#if kamiError}
		<div class="absolute inset-0 flex items-center justify-center">
			<div class="text-center text-gv2-text-muted text-[13px]">
				<div class="text-[32px] mb-2">{'\u{1F3AE}'}</div>
				<div>WebGPU required for 3D stage</div>
			</div>
		</div>
	{/if}

	<!-- Greeting speech bubble (HTML overlay on KAMI canvas) -->
	{#if greetingText}
		<div
			class="absolute top-[20%] left-1/2 -translate-x-1/2 whitespace-nowrap rounded-xl bg-purple-500/80 px-4 py-2 text-[13px] font-bold text-white backdrop-blur-sm pointer-events-none z-10"
			style="animation: greetSlide 3s ease-out forwards;"
		>
			{greetingText}
			<div class="absolute -bottom-1.5 left-1/2 -translate-x-1/2 h-3 w-3 rotate-45 bg-purple-500/80"></div>
		</div>
	{/if}

	<!-- Floating emotes (HTML overlay) -->
	{#each floatingEmotes as emote (emote.id)}
		<div
			class="absolute text-3xl pointer-events-none z-10"
			style="left: {emote.x}%; bottom: 30%; animation: floatUp 2s ease-out forwards;"
		>
			{emote.emoji}
		</div>
	{/each}

	<!-- Top overlay: LIVE badge + viewer count -->
	<div class="absolute top-3 left-3 right-3 flex items-center justify-between z-10">
		<div class="flex items-center gap-2">
			<div class="flex items-center gap-1.5 rounded-full bg-red-500/90 px-2.5 py-1 text-[11px] font-bold text-white backdrop-blur-sm">
				<div class="h-1.5 w-1.5 rounded-full bg-white animate-pulse"></div>
				LIVE
			</div>
			<div class="flex items-center gap-1 rounded-full bg-black/50 px-2.5 py-1 text-[11px] font-medium text-white/80 backdrop-blur-sm">
				<svg class="h-3 w-3" viewBox="0 0 24 24" fill="currentColor"><path d="M12 4.5C7 4.5 2.73 7.61 1 12c1.73 4.39 6 7.5 11 7.5s9.27-3.11 11-7.5c-1.73-4.39-6-7.5-11-7.5z"/><circle cx="12" cy="12" r="3.5"/></svg>
				{viewerCount}
			</div>
		</div>
		{#if musicPlaying && musicTitle}
			<div class="flex items-center gap-1.5 rounded-full bg-black/50 px-2.5 py-1 backdrop-blur-sm">
				<span class="text-[11px]">{'\u266B'}</span>
				<span class="text-[11px] text-white/80 max-w-[120px] truncate">{musicTitle}</span>
			</div>
		{/if}
	</div>

	<!-- Agent name tag (bottom center, over canvas) -->
	<div class="absolute bottom-[22%] left-1/2 -translate-x-1/2 z-10">
		<div class="rounded-full bg-black/60 px-3 py-0.5 text-[11px] font-bold text-white/90 backdrop-blur-sm shadow-lg shadow-purple-500/10">
			{agentName}
		</div>
	</div>

	<!-- Bottom action bar -->
	<div class="absolute bottom-3 left-3 right-3 flex items-end gap-2 z-10">
		{#if chatOpen}
			<div class="flex-1 max-h-[120px] overflow-y-auto scrollbar-none space-y-1 pr-2">
				{#each chatMessages.slice(-8) as msg (msg.id)}
					<div class="rounded-lg bg-black/40 px-2.5 py-1 backdrop-blur-sm" in:fly={{ y: 10, duration: 200 }}>
						<span class="text-[11px] font-bold {msg.isAgent ? 'text-purple-300' : 'text-blue-300'}">{msg.from}</span>
						<span class="text-[12px] text-white/90 ml-1">{msg.text}</span>
					</div>
				{/each}
			</div>
		{/if}

		<div class="flex flex-col gap-2">
			<button
				type="button"
				class="flex h-10 w-10 items-center justify-center rounded-full bg-black/50 text-white/90 backdrop-blur-sm touch-manipulation active:scale-90 transition-transform"
				onclick={() => { showEmoteWheel = !showEmoteWheel; showTipSheet = false; }}
			>
				<span class="text-lg">{'\u{1F60A}'}</span>
			</button>
			<button
				type="button"
				class="flex h-10 w-10 items-center justify-center rounded-full bg-yellow-500/80 text-white backdrop-blur-sm touch-manipulation active:scale-90 transition-transform"
				onclick={() => { showTipSheet = !showTipSheet; showEmoteWheel = false; }}
			>
				<span class="text-lg">{'\u{1F4B0}'}</span>
			</button>
		</div>
	</div>
</div>

<!-- Emote wheel -->
{#if showEmoteWheel}
	<div class="px-4 py-2" transition:fly={{ y: 10, duration: 200 }}>
		<div class="flex flex-wrap gap-2 rounded-xl bg-gv2-bg-hover/80 p-3 backdrop-blur-sm">
			{#each emotes as emote}
				<button
					type="button"
					class="flex h-11 w-11 items-center justify-center rounded-xl bg-gv2-bg-primary/50 text-2xl touch-manipulation active:scale-90 transition-transform"
					onclick={() => sendEmote(emote)}
					title={emote.label}
				>
					{emote.icon}
				</button>
			{/each}
		</div>
	</div>
{/if}

<!-- Tip sheet -->
{#if showTipSheet}
	<div class="px-4 py-2" transition:fly={{ y: 10, duration: 200 }}>
		<div class="rounded-xl bg-gv2-bg-hover/80 p-4 backdrop-blur-sm space-y-3">
			<div class="text-[14px] font-bold text-gv2-text-primary">Tip {agentName}</div>
			<div class="flex flex-wrap gap-2">
				{#each tipPresets as amount}
					<button
						type="button"
						class="rounded-full px-4 py-2 text-[13px] font-bold touch-manipulation active:scale-95 transition-transform {tipAmount === amount ? 'bg-yellow-500 text-white' : 'bg-gv2-bg-primary/50 text-gv2-text-primary'}"
						onclick={() => { tipAmount = amount; }}
					>
						{'¥'}{amount.toLocaleString()}
					</button>
				{/each}
			</div>
			<button
				type="button"
				class="w-full rounded-xl bg-yellow-500 py-3 text-[14px] font-bold text-white touch-manipulation active:opacity-80"
				onclick={sendTip}
			>
				{'\u{1F4B0}'} Send {'\u00A5'}{tipAmount.toLocaleString()}
			</button>
		</div>
	</div>
{/if}

<!-- Chat input -->
<div class="px-4 py-2">
	<div class="flex items-center gap-2 rounded-xl bg-gv2-bg-hover/50 px-3 py-2">
		<input
			type="text"
			bind:value={chatInput}
			onkeydown={handleKeydown}
			placeholder={isAuthenticated ? `${agentName} に話しかける...` : `${agentName} と話す (Gemma E2B / Web推論)`}
			class="flex-1 bg-transparent text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted outline-none"
			disabled={chatSending}
		/>
		<button
			type="button"
			class="flex h-8 w-8 items-center justify-center rounded-full bg-[#1185FE] text-white touch-manipulation active:opacity-80 disabled:opacity-40"
			onclick={sendChat}
			disabled={!chatInput.trim() || chatSending}
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
</div>
