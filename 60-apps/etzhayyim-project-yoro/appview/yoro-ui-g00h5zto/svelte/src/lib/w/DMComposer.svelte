<script lang="ts">
	/**
	 * DMComposer — Bluesky-style DM message composer.
	 * Ref: github.com/bluesky-social/social-app/src/screens/Messages/components/MessageInput.tsx
	 * Auto-resize textarea, grapheme-aware length limit, typing indicator, draft persistence.
	 */
	interface Props {
		convoId: string;
		disabled?: boolean;
		onSend?: (body: string) => void;
		onTyping?: () => void;
		onDraftChange?: (text: string) => void;
		initialDraft?: string;
	}

	let { convoId, disabled = false, onSend, onTyping, onDraftChange, initialDraft = '' }: Props = $props();

	const MAX_DM_GRAPHEME_LENGTH = 1000;

	let text = $state(initialDraft);
	let textareaRef: HTMLTextAreaElement | undefined = $state();
	let isFocused = $state(false);

	// Grapheme count (Bluesky uses unicode-segmenter, we approximate with spread)
	const graphemeCount = $derived([...text.trim()].length);
	const canSend = $derived(graphemeCount > 0 && graphemeCount <= MAX_DM_GRAPHEME_LENGTH && !disabled);
	const isOverLimit = $derived(graphemeCount > MAX_DM_GRAPHEME_LENGTH);
	const showCounter = $derived(graphemeCount > MAX_DM_GRAPHEME_LENGTH - 100);
	const counterProgress = $derived(Math.min(graphemeCount / MAX_DM_GRAPHEME_LENGTH, 1));

	// Reset draft when convoId changes
	$effect(() => {
		void convoId;
		text = initialDraft;
		if (textareaRef) textareaRef.style.height = 'auto';
	});

	function autoResize() {
		if (!textareaRef) return;
		textareaRef.style.height = 'auto';
		textareaRef.style.height = Math.min(textareaRef.scrollHeight, 120) + 'px';
	}

	function handleInput() {
		autoResize();
		onTyping?.();
		onDraftChange?.(text);
	}

	function handleKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter' && !e.shiftKey) {
			e.preventDefault();
			handleSend();
		}
	}

	function handleSend() {
		if (!canSend) return;
		const body = text.trim();
		onSend?.(body);
		text = '';
		if (textareaRef) {
			textareaRef.style.height = 'auto';
			textareaRef.focus();
		}
	}
</script>

<div class="border-t border-[var(--gv2-border,#2f2f2f)]/40 bg-[var(--gv2-bg-primary,#0a0a0a)] px-3 pb-[max(env(safe-area-inset-bottom),10px)] pt-2">
	<div class="flex items-end gap-2">
		<div class="relative min-w-0 flex-1">
			<textarea
				bind:this={textareaRef}
				bind:value={text}
				class="block max-h-[120px] min-h-[44px] w-full resize-none rounded-[22px] bg-[var(--gv2-bg-card,#1a1a1a)] px-4 py-3 text-[15px] leading-tight text-[var(--gv2-text-primary,#fff)] placeholder-[var(--gv2-text-muted,#777)]/50 shadow-sm focus:outline-none focus:ring-2 focus:ring-[var(--gv2-accent,#3b82f6)]/40 {isOverLimit ? 'ring-2 ring-red-500/60' : ''}"
				rows="1"
				placeholder="Message..."
				oninput={handleInput}
				onkeydown={handleKeydown}
				onfocus={() => { isFocused = true; }}
				onblur={() => { isFocused = false; }}
				{disabled}
			></textarea>

			<!-- Grapheme counter (Bluesky-style circular progress) -->
			{#if showCounter}
				<div class="absolute bottom-2.5 right-12 flex items-center justify-center">
					<svg class="h-5 w-5" viewBox="0 0 20 20">
						<circle cx="10" cy="10" r="8" fill="none" stroke="var(--gv2-border, #2f2f2f)" stroke-width="2" opacity="0.3" />
						<circle
							cx="10" cy="10" r="8" fill="none"
							stroke={isOverLimit ? '#ef4444' : counterProgress > 0.9 ? '#f59e0b' : '#1185FE'}
							stroke-width="2"
							stroke-dasharray={2 * Math.PI * 8}
							stroke-dashoffset={2 * Math.PI * 8 * (1 - counterProgress)}
							stroke-linecap="round"
							transform="rotate(-90 10 10)"
						/>
					</svg>
					{#if graphemeCount > MAX_DM_GRAPHEME_LENGTH - 20}
						<span class="absolute text-[9px] font-bold {isOverLimit ? 'text-red-400' : 'text-gv2-text-muted'}">
							{MAX_DM_GRAPHEME_LENGTH - graphemeCount}
						</span>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Send button -->
		<button
			type="button"
			class="flex h-10 w-10 shrink-0 items-center justify-center rounded-full transition-all duration-75 touch-manipulation {canSend ? 'bg-[#1185FE] text-white shadow-[0_3px_0_rgba(0,0,0,0.2)] active:shadow-none active:translate-y-[3px]' : 'bg-gv2-bg-card text-gv2-text-muted/30'}"
			onclick={handleSend}
			disabled={!canSend}
			aria-label="Send"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="currentColor">
				<path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
			</svg>
		</button>
	</div>
</div>
