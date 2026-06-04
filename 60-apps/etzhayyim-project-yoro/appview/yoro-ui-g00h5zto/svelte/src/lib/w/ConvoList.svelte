<script lang="ts">
	import { Avatar, Badge, Chip, cn } from '@etzhayyim/design-system';
	import type { ConvoGroup, ConvoSection, PresenceState, ConversationKind } from '$lib/atproto-agent';

	type ConversationFilter = 'all' | ConversationKind;

	interface Props {
		groups: ConvoGroup[];
		activeConvoId?: string;
		presenceMap?: Map<string, PresenceState>;
		firehoseState?: 'connecting' | 'open' | 'streaming' | 'closed' | 'reconnecting' | 'polling';
		conversationFilter?: ConversationFilter;
		onSelectConvo?: (convoId: string) => void;
		onToggleSection?: (section: ConvoSection) => void;
		onCreateConvo?: () => void;
		onCreateDM?: () => void;
		onConversationFilterChange?: (filter: ConversationFilter) => void;
	}

	let {
		groups,
		activeConvoId = '',
		presenceMap = new Map(),
		firehoseState = 'closed',
		conversationFilter = 'all',
		onSelectConvo,
		onToggleSection,
		onCreateConvo,
		onCreateDM,
		onConversationFilterChange,
	}: Props = $props();

	const filterTabs: Array<{ id: ConversationFilter; label: string }> = [
		{ id: 'all', label: 'All' },
		{ id: 'user2user', label: 'People' },
		{ id: 'user2agent', label: 'Agents' },
		{ id: 'agent2agent', label: 'Orchestration' },
	];

	function presenceDot(did: string | undefined): string {
		if (!did) return '';
		const p = presenceMap.get(did);
		if (!p) return '';
		if (p.status === 'online') return 'bg-[#58CC02]';
		if (p.status === 'away') return 'bg-yellow-400';
		return '';
	}

	const sectionIcons: Record<string, string> = {
		favorites: '⭐',
		directs: '💬',
		spaces: '🏠',
		convos: '💬',
		lowPriority: '⚙️',
	};

	function formatTime(timestamp: string): string {
		if (!timestamp) return '';
		const date = new Date(timestamp);
		const now = new Date();
		const diffMs = now.getTime() - date.getTime();
		const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
		if (diffDays === 0) return date.toLocaleTimeString(undefined, { hour: '2-digit', minute: '2-digit' });
		if (diffDays === 1) return 'Yesterday';
		if (diffDays < 7) return `${diffDays}d`;
		return date.toLocaleDateString(undefined, { month: 'numeric', day: 'numeric' });
	}
</script>

<div class="flex h-full max-w-[600px] flex-col overflow-y-auto scrollbar-none bg-gv2-bg-primary">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center justify-between border-b border-gv2-border/40 px-4">
		<div class="flex items-center gap-2">
			<h2 class="text-[15px] font-bold tracking-wide text-gv2-text-primary">Conversations</h2>
			{#if firehoseState === 'open'}
				<div class="h-2 w-2 rounded-full bg-[#58CC02]" title="Connected"></div>
			{:else if firehoseState === 'reconnecting'}
				<div class="h-2 w-2 rounded-full bg-yellow-400 animate-pulse" title="Reconnecting..."></div>
			{:else if firehoseState === 'polling'}
				<div class="h-2 w-2 rounded-full bg-gv2-text-muted/40" title="Polling"></div>
			{/if}
		</div>
		<button
			class="flex h-10 w-10 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)] text-white shadow-sm touch-manipulation active:opacity-80 transition-opacity"
			onclick={onCreateConvo}
			aria-label="Create conversation"
		>
			<svg class="h-5 w-5" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="2.5">
				<path d="M10 3v14M3 10h14" />
			</svg>
		</button>
	</div>

	<!-- Conversation kind filter -->
	<div class="flex items-center gap-1.5 overflow-x-auto px-3 py-2 scrollbar-none border-b border-gv2-border/20">
		{#each filterTabs as tab (tab.id)}
			<Chip
				label={tab.label}
				active={conversationFilter === tab.id}
				class={cn(
					'shrink-0 !border !text-[12px] !px-3 !py-1',
					conversationFilter === tab.id
						? '!border-[var(--gv2-accent,#06c755)]/40 !bg-[var(--gv2-accent,#06c755)]/15 !text-[var(--gv2-accent,#06c755)]'
						: '!border-gv2-border/30 !bg-transparent !text-gv2-text-muted active:!bg-gv2-bg-hover'
				)}
				onclick={() => onConversationFilterChange?.(tab.id)}
			/>
		{/each}
	</div>

	<!-- Convo list -->
	<nav class="flex-1 px-2 py-2">
		{#each groups as group}
			{@const isCollapsed = group.collapsed ?? false}
			<div class="mb-2">
				<div class="flex items-center justify-between px-2 py-1">
					<button
						class="flex flex-1 items-center gap-2 rounded-lg px-1 py-1 touch-manipulation active:bg-gv2-bg-hover/50"
						onclick={() => onToggleSection?.(group.section)}
						aria-label="Toggle {group.label}"
					>
						<span class="text-[14px]">{sectionIcons[group.section] ?? '#'}</span>
						<span class="text-[11px] font-bold uppercase tracking-widest text-gv2-text-muted">
							{group.label}
						</span>
						<span class="text-[10px] text-gv2-text-muted/50 ml-auto">
							{isCollapsed ? '▸' : '▾'}
						</span>
					</button>
					{#if group.section === 'directs'}
						<button
							class="flex h-7 w-7 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)]/15 text-[var(--gv2-accent,#06c755)] touch-manipulation active:opacity-60"
							onclick={onCreateDM}
							aria-label="New DM"
						>
							<svg class="h-3.5 w-3.5" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2.5">
								<path d="M8 2v12M2 8h12" />
							</svg>
						</button>
					{/if}
				</div>

				{#if !isCollapsed}
					<div class="space-y-0.5 px-1">
						{#each group.convos as ch}
							{@const isActive = ch.convoId === activeConvoId}
							{@const hasUnread = ch.unreadCount > 0}
							{@const hasHighlight = ch.highlightCount > 0}
							<button
								class={cn(
									'flex w-full min-h-[56px] items-center gap-3 rounded-2xl px-3 py-2 text-left touch-manipulation transition-all',
									isActive
										? 'bg-[var(--gv2-accent,#06c755)]/10 shadow-sm'
										: 'active:bg-gv2-bg-hover/50',
									ch.isMuted && 'opacity-50'
								)}
								onclick={() => onSelectConvo?.(ch.convoId)}
								aria-label={ch.name}
								aria-current={isActive ? 'true' : undefined}
							>
								<div class="relative flex-shrink-0">
									{#if isActive}
										<div class="absolute -left-2 top-1/2 h-5 w-1 -translate-y-1/2 rounded-r-full bg-[var(--gv2-accent,#06c755)]"></div>
									{/if}
									{#if ch.isDirect}
										<Avatar
											src={ch.avatarUrl}
											fallback={ch.name}
											size="sm"
											class={cn(
												'!text-white !text-[12px]',
												isActive ? '!bg-[var(--gv2-accent,#06c755)]' : '!bg-gv2-text-muted/30 !text-gv2-text-secondary'
											)}
										/>
										{@const dot = presenceDot(ch.convoId.split('-dm-').find((d) => d !== activeConvoId))}
										{#if dot}
											<div class="absolute -bottom-0.5 -right-0.5 h-3 w-3 rounded-full border-2 border-gv2-bg-primary {dot}"></div>
										{/if}
									{:else}
										<div class={cn(
											'flex h-9 w-9 items-center justify-center rounded-xl text-[14px] font-semibold',
											isActive ? 'bg-[var(--gv2-accent,#06c755)]/20 text-[var(--gv2-accent,#06c755)]' : 'bg-gv2-bg-card text-gv2-text-muted'
										)}>
											{ch.isEncrypted ? '🔒' : '#'}
										</div>
									{/if}
								</div>

								<div class="min-w-0 flex-1">
									<div class="flex items-center gap-1">
										<span class={cn(
											'truncate text-[15px]',
											isActive || hasUnread
												? 'font-bold text-gv2-text-primary'
												: 'font-medium text-gv2-text-muted'
										)}>
											{ch.name}
										</span>
										{#if ch.isMuted}
											<span class="text-[12px] opacity-50">🔇</span>
										{/if}
									</div>
									{#if ch.lastRecordPreview}
										<p class="truncate text-[12px] leading-tight {hasUnread ? 'font-medium text-gv2-text-secondary' : 'text-gv2-text-muted/70'}">
											{ch.lastRecordPreview}
										</p>
									{/if}
								</div>

								<div class="flex flex-shrink-0 flex-col items-end gap-1">
									{#if ch.lastRecordTimestamp}
										<span class="text-[11px] {hasUnread ? 'font-semibold text-[var(--gv2-accent,#06c755)]' : 'text-gv2-text-muted/60'}">
											{formatTime(ch.lastRecordTimestamp)}
										</span>
									{/if}
									{#if hasHighlight}
										<Badge value={ch.highlightCount} variant="error" />
									{:else if hasUnread}
										<div class="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)] px-1.5 text-[11px] font-bold text-white">
											{ch.unreadCount}
										</div>
									{/if}
								</div>
							</button>
						{/each}
					</div>
				{/if}
			</div>
		{/each}

		{#if groups.length === 0}
			<div class="flex flex-col items-center justify-center gap-3 py-12 px-6">
				<div class="flex h-14 w-14 items-center justify-center rounded-full bg-gv2-bg-card">
					<svg class="h-7 w-7 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
				</div>
				<p class="text-center text-[14px] text-gv2-text-muted">No conversations found</p>
			</div>
		{/if}
	</nav>
</div>
