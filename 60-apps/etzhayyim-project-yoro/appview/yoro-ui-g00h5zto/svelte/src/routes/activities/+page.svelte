<!--
  /activities — OCEL v2 Activity Log.
  Replaces /notifications with object-centric event timeline.
  Aggregates: Bluesky social notifications + OCEL events + Shinka evolution.
-->
<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { Avatar, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
	import { fade } from 'svelte/transition';
	import * as yoroApi from '$lib/atproto-agent';

	/** OCEL v2 ActivityEvent from PDS. */
	interface ActivityEvent {
		eventId: string;
		specVersion: 'ocel.v2';
		activity: string;
		objectType: string;
		objectId: string;
		actorDid: string;
		actorHandle: string;
		actorDisplayName: string;
		actorAvatar: string;
		timestamp: string;
		phase: string;
		subjectUri?: string;
		relatedObjects?: Array<{ objectType: string; objectId: string; qualifier: string }>;
	}

	type TabId = 'all' | 'social' | 'deploy' | 'evolution' | 'inference' | 'records';

	const TABS: Array<{ id: TabId; label: string; objectTypes: string[]; activities: string[] }> = [
		{ id: 'all', label: 'すべて', objectTypes: [], activities: [] },
		{ id: 'social', label: 'Social', objectTypes: ['notification'], activities: ['social:*'] },
		{ id: 'deploy', label: 'Deploy', objectTypes: ['deploy', 'worker'], activities: ['deploy:*'] },
		{ id: 'evolution', label: 'Evolution', objectTypes: ['app'], activities: ['evolution:*'] },
		{ id: 'inference', label: 'Inference', objectTypes: [], activities: [] },
		{ id: 'records', label: 'Records', objectTypes: ['record'], activities: ['record:*'] },
	];

	let activeTab = $state<TabId>(($page.url.searchParams.get('tab') as TabId) || 'all');
	let activities = $state<ActivityEvent[]>([]);
	let loading = $state(true);
	let cursor = $state<string | undefined>(undefined);

	/** Inference activity entry from PDS evolution records. */
	interface InferenceActivity {
		id: string;
		actorDid: string;
		actorName: string;
		collection: string;
		model: string;
		tokensUsed: number;
		summary: string;
		mood: string | undefined;
		grade: string | undefined;
		score: number;
		timestamp: string;
	}

	let inferenceActivities = $state<InferenceActivity[]>([]);
	let inferenceLoading = $state(false);

	/** Load inference activities from PDS evolution records. */
	async function loadInferenceActivities(): Promise<void> {
		inferenceLoading = true;
		try {
			const collections = [
				'com.etzhayyim.apps.yoro.shinkaInference',
				'com.etzhayyim.apps.yoro.shinkaKnowledge',
				'com.etzhayyim.apps.yoro.shinkaEvolution',
				'com.etzhayyim.apps.yoro.kojiDiscovery',
				'com.etzhayyim.apps.yoro.kyumeiValidation',
				'com.etzhayyim.apps.yoro.hinshitsuAssessment',
			];
			const entries: InferenceActivity[] = [];
			for (const collection of collections) {
				try {
					const res = await yoroApi.atProcedure<{ records?: Array<{ uri?: string; value?: Record<string, unknown> }> }>(
						'com.atproto.repo.listRecords',
						{ collection, limit: 15 },
					);
					const data = typeof res === 'string' ? JSON.parse(res) : res;
					for (const rec of data?.records ?? []) {
						const val = rec.value ?? {};
						const type = collection.split('.').pop() ?? '';
						entries.push({
							id: String(rec.uri || `${type}-${Date.now()}-${Math.random()}`),
							actorDid: String(val.actorDid ?? ''),
							actorName: String(val.actorName ?? val.actorDid ?? 'Actor'),
							collection: type,
							model: String(val.model ?? 'browser-llm'),
							tokensUsed: Number(val.tokensUsed ?? 0),
							summary: type === 'shinkaInference' ? `Joucho: ${String(val.mood ?? 'neutral')} — ${String(val.suggestion ?? '')}`
								: type === 'shinkaKnowledge' ? `${(val.subDids as unknown[] | undefined)?.length ?? 0} sub-DIDs, ${(val.knowledgeEdges as unknown[] | undefined)?.length ?? 0} edges`
								: type === 'kojiDiscovery' ? `Grade ${String(val.readinessGrade ?? '?')} — ${(val.capabilities as unknown[] | undefined)?.length ?? 0} capabilities`
								: type === 'kyumeiValidation' ? `Score ${String(val.validationScore ?? 0)}% — ${(val.inconsistencies as unknown[] | undefined)?.length ?? 0} issues`
								: type === 'hinshitsuAssessment' ? `Quality ${String(val.grade ?? '?')} (${String(val.qualityScore ?? 0)}%)`
								: `Evolution: ${String(val.mood ?? type)}`,
							mood: val.mood != null ? String(val.mood) : undefined,
							grade: val.grade != null ? String(val.grade) : val.readinessGrade != null ? String(val.readinessGrade) : undefined,
							score: Number(val.validationScore ?? val.qualityScore ?? 0),
							timestamp: String(val.createdAt ?? new Date().toISOString()),
						});
					}
				} catch {
					// skip failed collection
				}
			}
			entries.sort((a, b) => b.timestamp.localeCompare(a.timestamp));
			inferenceActivities = entries.slice(0, 50);
		} catch (e) {
			console.warn('loadInferenceActivities failed:', e);
		} finally {
			inferenceLoading = false;
		}
	}

	/** Activity namespace → icon + color. */
	const ACTIVITY_ICON: Record<string, { icon: string; color: string }> = {
		'social:like': { icon: '❤️', color: '#F91880' },
		'social:repost': { icon: '🔁', color: '#00BA7C' },
		'social:follow': { icon: '👤', color: '#1185FE' },
		'social:mention': { icon: '💬', color: '#1185FE' },
		'social:reply': { icon: '💬', color: '#1185FE' },
		'social:quote': { icon: '💬', color: '#F59E0B' },
		'deploy:build': { icon: '🔨', color: '#58CC02' },
		'deploy:upload': { icon: '📦', color: '#58CC02' },
		'deploy:smoke_test': { icon: '✅', color: '#58CC02' },
		'evolution:heartbeat': { icon: '💓', color: '#F59E0B' },
		'evolution:knowledge': { icon: '🧠', color: '#A855F7' },
		'evolution:post': { icon: '📝', color: '#1185FE' },
		'record:create': { icon: '➕', color: '#58CC02' },
		'record:update': { icon: '✏️', color: '#F59E0B' },
		'record:delete': { icon: '🗑️', color: '#EF4444' },
	};

	/** Activity → human-readable verb (Japanese). */
	const ACTIVITY_VERB: Record<string, string> = {
		'social:like': 'があなたの投稿にいいね',
		'social:repost': 'があなたの投稿をリポスト',
		'social:follow': 'があなたをフォロー',
		'social:mention': 'があなたをメンション',
		'social:reply': 'があなたの投稿に返信',
		'social:quote': 'があなたの投稿を引用',
		'deploy:build': 'がビルドを実行',
		'deploy:upload': 'がデプロイ',
		'deploy:smoke_test': 'がスモークテスト完了',
		'evolution:heartbeat': 'がハートビートを送信',
		'evolution:knowledge': 'がナレッジを生成',
		'evolution:post': 'がソーシャル投稿',
		'record:create': 'がレコードを作成',
		'record:update': 'がレコードを更新',
		'record:delete': 'がレコードを削除',
	};

	function getIcon(activity: string) {
		return ACTIVITY_ICON[activity] || { icon: '📋', color: '#6B7280' };
	}

	function getVerb(activity: string): string {
		return ACTIVITY_VERB[activity] || activity;
	}

	/** Phase indicator color. */
	function phaseColor(phase: string): string {
		if (phase === 'error') return '#EF4444';
		if (phase === 'start') return '#1185FE';
		return '#58CC02';
	}

	function timeAgo(ts: string): string {
		const date = new Date(ts);
		if (Number.isNaN(date.getTime())) {
			const numTs = Number(ts);
			if (!numTs) return '';
			const diff = Date.now() - numTs;
			const mins = Math.max(0, Math.floor(diff / 60000));
			if (mins < 60) return `${mins}分`;
			const hrs = Math.floor(mins / 60);
			if (hrs < 24) return `${hrs}時間`;
			return `${Math.floor(hrs / 24)}日`;
		}
		const diff = Date.now() - date.getTime();
		const mins = Math.max(0, Math.floor(diff / 60000));
		if (mins < 60) return `${mins}分`;
		const hrs = Math.floor(mins / 60);
		if (hrs < 24) return `${hrs}時間`;
		return `${Math.floor(hrs / 24)}日`;
	}

	async function loadActivities(append = false) {
		if (!append) loading = true;
		try {
			const tab = TABS.find(t => t.id === activeTab) || TABS[0];
			const res = await yoroApi.atProcedure<{ activities: ActivityEvent[]; cursor?: string }>(
				'com.etzhayyim.apps.yoro.activity.listActivities',
				{
					limit: 50,
					cursor: append ? cursor : undefined,
					objectTypes: tab.objectTypes.length > 0 ? tab.objectTypes : undefined,
					activities: tab.activities.length > 0 ? tab.activities : undefined,
				},
			);
			const data = typeof res === 'string' ? JSON.parse(res) : res;
			if (append) {
				activities = [...activities, ...(data?.activities || [])];
			} else {
				activities = data?.activities || [];
			}
			cursor = data?.cursor;
			// Mark as seen
			void yoroApi.atProcedure('com.etzhayyim.apps.yoro.activity.markSeen', {}).catch((e: unknown) => console.warn('markSeen failed', e));
		} catch (e) {
			console.warn('loadActivities failed:', e);
			if (!append) activities = [];
		} finally {
			loading = false;
		}
	}

	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}

	function openProfile(did: string) {
		void goto(`/profile/${encodeURIComponent(did)}`);
	}

	function openPost(uri: string) {
		const parts = uri.split('/');
		if (parts[2]) void goto(`/profile/${encodeURIComponent(parts[2])}`);
	}

	onMount(() => {
		void loadActivities();
	});

	$effect(() => {
		if (activeTab === 'inference') {
			void loadInferenceActivities();
		} else {
			void loadActivities();
		}
	});
</script>

<svelte:head>
	<title>Activities — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
			onclick={goBack}
			aria-label="戻る"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
			</svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Activities</span>
		<!-- OCEL v2 badge -->
		<span class="ml-auto rounded-full bg-[#A855F7]/15 px-2 py-0.5 text-[10px] font-semibold text-[#A855F7]">OCEL v2</span>
	</div>

	<!-- Filter tabs -->
	<div class="flex border-b border-gv2-border/30 bg-gv2-bg-primary/90 material-blur sticky top-[48px] z-10 overflow-x-auto scrollbar-none">
		{#each TABS as tab}
			<button
				type="button"
				class="relative shrink-0 px-4 py-3 text-center text-[13px] font-semibold touch-manipulation transition-colors {activeTab === tab.id
					? 'text-gv2-text-primary'
					: 'text-gv2-text-muted active:text-gv2-text-secondary'}"
				onclick={() => { activeTab = tab.id; }}
			>
				{tab.label}
				{#if activeTab === tab.id}
					<div class="absolute bottom-0 left-1/2 h-[3px] w-12 -translate-x-1/2 rounded-full bg-[#1185FE]"></div>
				{/if}
			</button>
		{/each}
	</div>

	<!-- Inference tab -->
	{#if activeTab === 'inference'}
		{#if inferenceLoading}
			<div class="flex flex-col" in:fade={staggerFade(0, { duration: 300 })}>
				{#each { length: 6 } as _}
					<div class="flex gap-2.5 border-b border-gv2-border/20 px-4 py-3">
						<Skeleton variant="circular" class="h-9 w-9 flex-shrink-0" />
						<div class="flex-1 space-y-2 pt-0.5">
							<Skeleton variant="text" class="h-3 w-3/5" />
							<Skeleton variant="text" class="h-4 w-4/5" />
						</div>
					</div>
				{/each}
			</div>
		{:else if inferenceActivities.length === 0}
			<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8" in:fade={{ duration: 300 }}>
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#9333EA]/10">
					<svg class="h-8 w-8 text-[#9333EA]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M12 2a4 4 0 0 0-4 4c0 2 1.5 3 3 4l1 1 1-1c1.5-1 3-2 3-4a4 4 0 0 0-4-4Z" />
						<path d="M12 11v4" /><circle cx="12" cy="18" r="2" />
					</svg>
				</div>
				<p class="text-[17px] font-bold text-gv2-text-primary">推論アクティビティはまだありません</p>
				<p class="text-[14px] text-gv2-text-muted text-center">Credits ページで Evolution Tasks を開始すると、推論ログがここに表示されます</p>
			</div>
		{:else}
			<div class="divide-y divide-gv2-border/20 overflow-y-auto scrollbar-none">
				{#each inferenceActivities as inf (inf.id)}
					{@const typeColor = inf.collection === 'kojiDiscovery' ? '#1185FE'
						: inf.collection === 'kyumeiValidation' ? '#9333EA'
						: inf.collection === 'shinkaEvolution' || inf.collection === 'shinkaInference' ? '#58CC02'
						: inf.collection === 'hinshitsuAssessment' ? '#F59E0B'
						: '#EC4899'}
					{@const typeIcon = inf.collection === 'kojiDiscovery' ? '🔍'
						: inf.collection === 'kyumeiValidation' ? '🔬'
						: inf.collection === 'shinkaEvolution' || inf.collection === 'shinkaInference' ? '🌱'
						: inf.collection === 'hinshitsuAssessment' ? '💎'
						: '🧠'}
					<div class="flex w-full gap-3 px-4 py-3">
						<div class="flex flex-col items-center gap-1 pt-0.5">
							<span class="text-[18px]">{typeIcon}</span>
							<img
								src="https://api.dicebear.com/9.x/identicon/svg?seed={encodeURIComponent(inf.actorName)}"
								alt={inf.actorName}
								class="h-8 w-8 rounded-full bg-gv2-bg-secondary"
							/>
						</div>
						<div class="min-w-0 flex-1">
							<div class="flex items-baseline gap-1.5 text-[14px] leading-tight">
								<span class="font-bold text-gv2-text-primary truncate">{inf.actorName}</span>
								<span class="rounded-full px-1.5 py-0.5 text-[10px] font-medium" style="background: {typeColor}15; color: {typeColor}">{inf.collection}</span>
							</div>
							<p class="mt-0.5 text-[13px] text-gv2-text-secondary leading-snug">{inf.summary}</p>
							<div class="mt-1 flex items-center gap-2 text-[11px] flex-wrap">
								<span class="text-gv2-text-muted">{timeAgo(inf.timestamp)}</span>
								{#if inf.model}
									<span class="rounded bg-gv2-bg-card px-1 py-0.5 text-[10px] font-medium text-gv2-text-secondary">{inf.model}</span>
								{/if}
								{#if inf.tokensUsed > 0}
									<span class="text-gv2-text-muted tabular-nums">{inf.tokensUsed} tok</span>
								{/if}
								{#if inf.grade}
									<span class="rounded px-1 py-0.5 text-[10px] font-semibold" style="background: {typeColor}15; color: {typeColor}">{inf.grade}</span>
								{/if}
								{#if inf.mood}
									<span class="rounded px-1 py-0.5 text-[10px] font-medium bg-emerald-500/10 text-emerald-400">{inf.mood}</span>
								{/if}
							</div>
						</div>
					</div>
				{/each}
			</div>
		{/if}
	<!-- Standard activity list -->
	{:else if loading}
		<div class="flex flex-col" in:fade={staggerFade(0, { duration: 300 })}>
			{#each { length: 8 } as _}
				<div class="flex gap-2.5 border-b border-gv2-border/20 px-4 py-3">
					<Skeleton variant="circular" class="h-9 w-9 flex-shrink-0" />
					<div class="flex-1 space-y-2 pt-0.5">
						<Skeleton variant="text" class="h-3 w-3/5" />
						<Skeleton variant="text" class="h-4 w-4/5" />
					</div>
				</div>
			{/each}
		</div>
	{:else if activities.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 p-8" in:fade={{ duration: 300 }}>
			<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[#A855F7]/10">
				<svg class="h-8 w-8 text-[#A855F7]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
				</svg>
			</div>
			<p class="text-[17px] font-bold text-gv2-text-primary">アクティビティはまだありません</p>
			<p class="text-[14px] text-gv2-text-muted text-center">いいね、デプロイ、進化イベントなどがここに表示されます</p>
		</div>
	{:else}
		<div class="divide-y divide-gv2-border/20 overflow-y-auto scrollbar-none">
			{#each activities as event (event.eventId)}
				{@const ic = getIcon(event.activity)}
				<button
					type="button"
					class="flex w-full gap-3 px-4 py-3 text-left touch-manipulation transition-colors active:bg-gv2-bg-hover/40"
					onclick={() => {
						if (event.objectType === 'notification' && event.activity === 'social:follow') openProfile(event.actorDid);
						else if (event.subjectUri) openPost(event.subjectUri);
						else if (event.actorDid) openProfile(event.actorDid);
					}}
				>
					<!-- Activity icon + phase dot -->
					<div class="flex flex-col items-center gap-1 pt-0.5">
						<span class="text-[18px]">{ic.icon}</span>
						{#if event.actorAvatar || event.actorDisplayName}
							<Avatar
								src={event.actorAvatar || undefined}
								fallback={(event.actorDisplayName || event.actorHandle || '?').slice(0, 2).toUpperCase()}
								size="sm"
								class="!h-8 !w-8"
							/>
						{/if}
						{#if event.phase && event.phase !== 'success'}
							<div class="h-1.5 w-1.5 rounded-full" style="background: {phaseColor(event.phase)}"></div>
						{/if}
					</div>
					<!-- Content -->
					<div class="min-w-0 flex-1">
						<div class="flex items-baseline gap-1 text-[14px] leading-tight">
							<span class="font-bold text-gv2-text-primary truncate">{event.actorDisplayName || event.actorHandle || event.actorDid.slice(0, 20)}</span>
							<span class="text-gv2-text-muted">{getVerb(event.activity)}</span>
						</div>
						<div class="mt-0.5 flex items-center gap-2">
							<span class="text-[13px] text-gv2-text-muted">{timeAgo(event.timestamp)}</span>
							<!-- Object type chip -->
							<span class="rounded-full px-1.5 py-0.5 text-[10px] font-medium" style="background: {ic.color}15; color: {ic.color}">{event.objectType}</span>
						</div>
						{#if event.subjectUri}
							<div class="mt-1 rounded-lg bg-gv2-bg-card/50 px-3 py-1.5 text-[13px] text-gv2-text-muted truncate">
								{event.subjectUri}
							</div>
						{/if}
					</div>
				</button>
			{/each}

			<!-- Load more -->
			{#if cursor}
				<button
					type="button"
					class="w-full py-4 text-center text-[14px] font-semibold text-[#1185FE] touch-manipulation active:opacity-70"
					onclick={() => void loadActivities(true)}
				>
					さらに読み込む
				</button>
			{/if}
		</div>
	{/if}
</div>
