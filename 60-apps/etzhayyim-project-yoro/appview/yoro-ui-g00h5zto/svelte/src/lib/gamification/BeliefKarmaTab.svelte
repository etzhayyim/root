<script lang="ts">
	import { graphSql, sqlString } from '$lib/graph-sql';

	interface Props {
		/** Actor DID — when provided, fetches actor-specific belief karma from RisingWave.
		 *  Falls back to showing all 7 belief systems (global view) when actor has no edges. */
		did?: string;
	}

	const { did }: Props = $props();

	// ── types ────────────────────────────────────────────────────────────────

	type Tradition = 'abrahamic' | 'dharmic' | 'indigenous' | 'secular' | 'east-asian' | 'dialectical';
	type TimeStructure = 'linear_teleological' | 'cyclical_karmic' | 'eternal_present' | 'dialectical';
	type ConsentModel = 'divine_covenant' | 'karmic_accumulation' | 'social_contract' | 'collective_mandate' | 'spontaneous' | 'individual' | 'collective' | 'non-dual';

	interface BeliefRow {
		belief_vertex_id: string;
		belief_name: string;
		belief_display_name: string;
		tradition: Tradition;
		self_other_separation: number;
		individual_primacy: boolean;
		time_structure: TimeStructure;
		consent_model: ConsentModel;
		approx_followers: number;
		belief_description: string;
		binding_strength: number;
		constraint_type: string | null;
		evidence_type: string | null;
		epoch: string | null;
	}

	interface AggRow {
		actor_vid: string;
		belief_count: number;
		avg_individuation: number;
		total_binding: number;
		weighted_individuation: number;
	}


	// ── state ────────────────────────────────────────────────────────────────

	let beliefs = $state<BeliefRow[]>([]);
	let agg = $state<AggRow | null>(null);
	let loading = $state(false);
	let loaded = $state(false);
	let isActorSpecific = $state(false);

	// ── load ─────────────────────────────────────────────────────────────────

	async function load() {
		if (loaded || loading) return;
		loading = true;
		try {
			if (did) {
				// fetch actor-specific belief karma from mv_actor_belief_karma
				const rows = await graphSql<BeliefRow>(
					`SELECT
						belief_vertex_id, belief_name, belief_display_name,
						tradition, self_other_separation, individual_primacy,
						time_structure, consent_model, approx_followers,
						belief_description, binding_strength,
						constraint_type, evidence_type, epoch
					FROM mv_actor_belief_karma
					WHERE actor_vid = ${sqlString(did)}
					ORDER BY binding_strength DESC`
				);

				if (rows.length > 0) {
					beliefs = rows;
					isActorSpecific = true;

					// fetch aggregate
					const aggRows = await graphSql<AggRow>(
						`SELECT actor_vid, belief_count, avg_individuation, total_binding, weighted_individuation
						FROM mv_actor_karma_aggregate
						WHERE actor_vid = ${sqlString(did)}
						LIMIT 1`
					);
					agg = aggRows[0] ?? null;
				} else {
					// actor not seeded — show global belief systems
					beliefs = await loadGlobalBeliefs();
					isActorSpecific = false;
				}
			} else {
				// no DID — show global belief systems
				beliefs = await loadGlobalBeliefs();
				isActorSpecific = false;
			}
		} catch {
			beliefs = [];
			isActorSpecific = false;
		} finally {
			loading = false;
			loaded = true;
		}
	}

	async function loadGlobalBeliefs(): Promise<BeliefRow[]> {
		return graphSql<BeliefRow>(
			`SELECT
				vertex_id       AS belief_vertex_id,
				name            AS belief_name,
				display_name    AS belief_display_name,
				tradition,
				self_other_separation,
				individual_primacy,
				time_structure,
				consent_model,
				approx_followers,
				description     AS belief_description,
				0               AS binding_strength,
				NULL            AS constraint_type,
				NULL            AS evidence_type,
				NULL            AS epoch
			FROM vertex_belief_system
			WHERE status = 'active'
			ORDER BY approx_followers DESC`
		);
	}

	$effect(() => {
		void load();
	});

	// ── derived ──────────────────────────────────────────────────────────────

	const sorted = $derived(
		beliefs.slice().sort((a, b) =>
			isActorSpecific
				? b.binding_strength - a.binding_strength
				: b.approx_followers - a.approx_followers
		)
	);

	// ── display helpers ──────────────────────────────────────────────────────

	const traditionColors: Record<Tradition | string, { bg: string; border: string; text: string; bar: string }> = {
		abrahamic: { bg: 'bg-amber-500/10', border: 'border-amber-500/30', text: 'text-amber-400', bar: 'bg-amber-500' },
		dharmic: { bg: 'bg-orange-500/10', border: 'border-orange-500/30', text: 'text-orange-400', bar: 'bg-orange-500' },
		indigenous: { bg: 'bg-emerald-500/10', border: 'border-emerald-500/30', text: 'text-emerald-400', bar: 'bg-emerald-500' },
		secular: { bg: 'bg-blue-500/10', border: 'border-blue-500/30', text: 'text-blue-400', bar: 'bg-blue-500' },
		'east-asian': { bg: 'bg-red-500/10', border: 'border-red-500/30', text: 'text-red-400', bar: 'bg-red-500' },
		dialectical: { bg: 'bg-rose-900/20', border: 'border-rose-800/40', text: 'text-rose-400', bar: 'bg-rose-700' },
	};

	const defaultColors = { bg: 'bg-gv2-bg-hover/20', border: 'border-gv2-border/30', text: 'text-gv2-text-secondary', bar: 'bg-gv2-text-muted' };

	function getColors(tradition: string) {
		return traditionColors[tradition] ?? defaultColors;
	}

	const timeStructureLabel: Record<string, string> = {
		linear_teleological: '直線・終末',
		cyclical_karmic: '輪廻',
		eternal_present: '永遠の今',
		dialectical: '弁証法',
	};

	const consentModelLabel: Record<string, string> = {
		divine_covenant: '神との契約',
		karmic_accumulation: 'カルマ蓄積',
		social_contract: '社会契約',
		collective_mandate: '集団的命令',
		spontaneous: '自然・即興',
		individual: '個人合理',
		collective: '集団合意',
		'non-dual': '非二元',
	};

	const evidenceTypeLabel: Record<string, string> = {
		institutional: '制度的',
		cultural: '文化的',
		inferential: '推論的',
		historical: '歴史的',
	};

	const constraintTypeLabel: Record<string, string> = {
		epistemological: '認識論',
		soteriological: '救済論',
		cosmological: '宇宙論',
		political: '政治的',
		recognition_seeking: '承認欲求',
	};

	function formatFollowers(n: number): string {
		if (n >= 1_000_000_000) return `${(n / 1_000_000_000).toFixed(1)}B`;
		if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(0)}M`;
		if (n >= 1_000) return `${(n / 1_000).toFixed(0)}K`;
		return String(n);
	}

	const traditionNames: Record<string, string> = {
		abrahamic: 'アブラハム',
		dharmic: 'ダルミック',
		indigenous: '先住民的',
		secular: '世俗',
		'east-asian': '東アジア',
		dialectical: '弁証法',
	};
</script>

<div class="flex flex-col gap-5">
	<!-- Section header -->
	<div>
		<h2 class="text-[17px] font-bold text-gv2-text-primary mb-1">
			{isActorSpecific ? 'このアクターの信仰カルマ' : '信仰系統グラフ'}
		</h2>
		<p class="text-[13px] text-gv2-text-muted leading-snug">
			{#if isActorSpecific}
				認識論的前提を信仰系統グラフで可視化。<br>
				<span class="text-gv2-text-secondary">拘束強度</span>: 0 = 影響なし → 1.0 = 完全規定
			{:else}
				世界の信仰・哲学系統を認識論的座標で可視化。<br>
				<span class="text-gv2-text-secondary">自他分離度</span>: 0 = 非分離 (神道) → 1.0 = 離散個 (アブラハム)
			{/if}
		</p>
	</div>

	<!-- Loading state -->
	{#if loading}
		<div class="flex flex-col gap-3">
			{#each [1, 2, 3] as _}
				<div class="rounded-2xl border border-gv2-border/20 bg-gv2-bg-hover/20 p-4 animate-pulse">
					<div class="h-4 bg-gv2-bg-hover rounded w-48 mb-3"></div>
					<div class="h-2 bg-gv2-bg-hover rounded w-full mb-2"></div>
					<div class="h-2 bg-gv2-bg-hover rounded w-3/4"></div>
				</div>
			{/each}
		</div>
	{:else}
		<!-- Actor aggregate summary (when actor-specific) -->
		{#if isActorSpecific && agg}
			<div class="rounded-xl border border-gv2-border/30 bg-gv2-bg-hover/20 px-4 py-3">
				<div class="grid grid-cols-3 gap-3 text-center">
					<div>
						<div class="text-[18px] font-bold text-gv2-text-primary">{agg.belief_count}</div>
						<div class="text-[11px] text-gv2-text-muted">信仰系統</div>
					</div>
					<div>
						<div class="text-[18px] font-bold text-gv2-text-primary">{(agg.weighted_individuation * 100).toFixed(0)}%</div>
						<div class="text-[11px] text-gv2-text-muted">自他分離度 (重み付き)</div>
					</div>
					<div>
						<div class="text-[18px] font-bold text-gv2-text-primary">{agg.total_binding.toFixed(2)}</div>
						<div class="text-[11px] text-gv2-text-muted">総拘束強度</div>
					</div>
				</div>
			</div>
		{/if}

		<!-- Self-other separation axis legend -->
		<div class="rounded-xl border border-gv2-border/30 bg-gv2-bg-hover/30 px-4 py-3">
			<div class="flex items-center justify-between text-[11px] text-gv2-text-muted mb-2">
				<span>← 自他非分離 (0.0)</span>
				<span class="font-semibold text-gv2-text-secondary">
					{isActorSpecific ? '拘束強度軸' : '自他分離度'}
				</span>
				<span>離散的個 (1.0) →</span>
			</div>
			<div class="relative h-2 rounded-full bg-gv2-bg-primary overflow-hidden">
				<div class="absolute inset-0 rounded-full"
					style="background: linear-gradient(to right, #10b981, #f59e0b, #ef4444);"></div>
				{#each sorted as b}
					<div
						class="absolute top-1/2 -translate-y-1/2 h-3 w-1 rounded-full border border-gv2-bg-hover/80 {getColors(b.tradition).bar}"
						style="left: calc({b.self_other_separation * 100}% - 2px);"
						title="{b.belief_name}: {b.self_other_separation.toFixed(2)}"
					></div>
				{/each}
			</div>
			<div class="flex flex-wrap gap-2 mt-3">
				{#each ['indigenous', 'dharmic', 'secular', 'east-asian', 'dialectical', 'abrahamic'] as t}
					<div class="flex items-center gap-1.5">
						<div class="h-2 w-2 rounded-full {getColors(t).bar}"></div>
						<span class="text-[11px] text-gv2-text-muted">{traditionNames[t] ?? t}</span>
					</div>
				{/each}
			</div>
		</div>

		<!-- Belief system cards -->
		{#each sorted as b, i}
			{@const colors = getColors(b.tradition)}
			<div class="rounded-2xl border {colors.border} {colors.bg} p-4">
				<!-- Header row -->
				<div class="flex items-start justify-between gap-3 mb-3">
					<div>
						<div class="flex items-center gap-2 flex-wrap">
							<span class="text-[15px] font-bold text-gv2-text-primary">{b.belief_display_name || b.belief_name}</span>
							{#if i === 0 && isActorSpecific}
								<span class="rounded-full bg-blue-500/20 px-2 py-0.5 text-[10px] font-bold text-blue-400">主要</span>
							{/if}
							{#if i === 0 && !isActorSpecific}
								<span class="rounded-full bg-amber-500/20 px-2 py-0.5 text-[10px] font-bold text-amber-400">#1</span>
							{/if}
						</div>
						<div class="flex items-center gap-2 mt-0.5">
							<span class="text-[12px] {colors.text} font-semibold">
								{isActorSpecific
									? `拘束: ${(b.binding_strength * 100).toFixed(0)}%`
									: `信者数: ${formatFollowers(b.approx_followers)}`}
							</span>
							{#if b.approx_followers > 0 && isActorSpecific}
								<span class="text-[11px] text-gv2-text-muted">({formatFollowers(b.approx_followers)}人)</span>
							{/if}
						</div>
					</div>
					<div class="text-right flex-shrink-0">
						<span class="text-[11px] text-gv2-text-muted">分離度</span>
						<div class="text-[16px] font-bold {colors.text}">{b.self_other_separation.toFixed(2)}</div>
					</div>
				</div>

				<!-- Binding strength bar (actor-specific) or followers bar (global) -->
				{#if isActorSpecific}
					<div class="mb-3">
						<div class="flex items-center justify-between text-[11px] text-gv2-text-muted mb-1">
							<span>拘束強度</span>
							<span>{(b.binding_strength * 100).toFixed(0)}%</span>
						</div>
						<div class="h-1.5 rounded-full bg-gv2-bg-primary overflow-hidden">
							<div class="h-full rounded-full {colors.bar} transition-all" style="width: {b.binding_strength * 100}%"></div>
						</div>
					</div>
				{/if}

				<!-- Self-other separation bar -->
				<div class="mb-3">
					<div class="flex items-center justify-between text-[11px] text-gv2-text-muted mb-1">
						<span>自他分離度</span>
						<span>{(b.self_other_separation * 100).toFixed(0)}%</span>
					</div>
					<div class="h-1.5 rounded-full bg-gv2-bg-primary overflow-hidden">
						<div class="h-full rounded-full {colors.bar} transition-all" style="width: {b.self_other_separation * 100}%"></div>
					</div>
				</div>

				<!-- Individual primacy bar -->
				<div class="mb-3">
					<div class="flex items-center justify-between text-[11px] text-gv2-text-muted mb-1">
						<span>個人主体性</span>
						<span>{b.individual_primacy ? '高' : '低'}</span>
					</div>
					<div class="h-1.5 rounded-full bg-gv2-bg-primary overflow-hidden">
						<div class="h-full rounded-full {colors.bar} opacity-60 transition-all" style="width: {b.individual_primacy ? 80 : 25}%"></div>
					</div>
				</div>

				<!-- Badges -->
				<div class="flex flex-wrap gap-1.5 mb-3">
					<span class="rounded-full bg-gv2-bg-primary/50 px-2.5 py-0.5 text-[11px] text-gv2-text-secondary border border-gv2-border/20">
						{timeStructureLabel[b.time_structure] ?? b.time_structure}
					</span>
					<span class="rounded-full bg-gv2-bg-primary/50 px-2.5 py-0.5 text-[11px] text-gv2-text-secondary border border-gv2-border/20">
						{consentModelLabel[b.consent_model] ?? b.consent_model}
					</span>
					{#if b.constraint_type}
						<span class="rounded-full bg-gv2-bg-primary/50 px-2.5 py-0.5 text-[11px] text-gv2-text-secondary border border-gv2-border/20">
							{constraintTypeLabel[b.constraint_type] ?? b.constraint_type}
						</span>
					{/if}
					{#if b.evidence_type}
						<span class="rounded-full bg-gv2-bg-primary/50 px-2.5 py-0.5 text-[11px] text-gv2-text-muted/70 border border-gv2-border/15">
							{evidenceTypeLabel[b.evidence_type] ?? b.evidence_type}
						</span>
					{/if}
					{#if b.epoch}
						<span class="rounded-full bg-gv2-bg-primary/50 px-2.5 py-0.5 text-[11px] text-gv2-text-muted/70 border border-gv2-border/15">
							{b.epoch}
						</span>
					{/if}
				</div>

				<!-- Description -->
				<p class="text-[12px] text-gv2-text-muted leading-relaxed">{b.belief_description}</p>
			</div>
		{/each}

		<!-- Recognition dynamics note -->
		<div class="rounded-xl border border-gv2-border/20 bg-gv2-bg-hover/20 px-4 py-3">
			<p class="text-[12px] text-gv2-text-muted leading-relaxed">
				<span class="text-gv2-text-secondary font-semibold">承認欲求と認識論的前提:</span>
				自他分離度が高い系統 (アブラハム系・正教) ほど「他者から認められる個人」という概念が強く、
				承認欲求 (recognition deficit) が権力・外交動態に表れやすい。
				自他非分離の系統 (神道・仏教) では承認は内在的であり外部からの確認を必要としない。
			</p>
		</div>
	{/if}
</div>
