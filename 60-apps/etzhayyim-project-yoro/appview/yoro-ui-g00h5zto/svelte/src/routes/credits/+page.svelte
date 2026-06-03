<!--
  /credits — Unified credits, wallet & inference page.
  Consolidates ProviderPanel (wallet + browser inference + expert provider) into a dedicated route.
  Header "Credits" button navigates here.
-->
<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Badge } from '@etzhayyim/design-system';
	import { isSignedIn } from '$lib/auth/stores.js';
	import { useProviderWorker } from '$lib/provider/worker-state.svelte.js';
	import { useProviderMarket } from '$lib/provider/market-state.svelte.js';
	import { useBrowserInference } from '$lib/provider/browser-inference-state.svelte.js';
	import { useLocalLLM } from '$lib/provider/local-llm.svelte.js';
	import { useShinkaInference } from '$lib/provider/shinka-inference.svelte.js';
	import { useEvolutionTasks, type EvolutionTaskType, type InferenceLogEntry } from '$lib/provider/evolution-tasks.svelte.js';
	import { useActivityFeed } from '$lib/provider/activity-feed.svelte.js';
	import { requestInferenceConsent } from '$lib/components/inference-consent-state.svelte.js';
	import { useEmbedding } from '$lib/provider/embedding.svelte.js';
	import { useLocalDiffusion } from '$lib/provider/local-diffusion.svelte.js';
	import {
		walletState,
		ethBalanceFormatted,
		tokenBalances,
		walletError,
		walletLoading,
		connectWallet,
		disconnectWallet,
		refreshBalances,
		shortenAddress,
		isWalletAvailable,
	} from '$lib/wallet/web3.js';

	const worker = useProviderWorker();
	const mkt = useProviderMarket();
	const inference = useBrowserInference();
	const localLLM = useLocalLLM();
	const shinkaInf = useShinkaInference();
	const evo = useEvolutionTasks();
	const activity = useActivityFeed();
	const embedding = useEmbedding();
	const diffusion = useLocalDiffusion();

	let diffusionPrompt = $state('');
	let diffusionNegPrompt = $state('low quality, blurry, deformed');
	let diffusionSteps = $state(20);
	let diffusionSeed = $state(Math.floor(Math.random() * 2147483647));
	let showDiffusionAdvanced = $state(false);

	onMount(() => {
		activity.startPolling();
		// Restore evolution stats from kagami graph (survives page reload)
		void evo.restoreFromGraph();
		return () => activity.stopPolling();
	});

	/** Task type display metadata. */
	const TASK_META: Record<EvolutionTaskType, { label: string; labelJa: string; icon: string; color: string; desc: string; credit: string }> = {
		koji: { label: 'Koji', labelJa: '工事', icon: '🔍', color: '#1185FE', desc: 'Self-information gathering — discover actor capabilities and data sources', credit: '+¥0.1' },
		kyumei: { label: 'Kyumei', labelJa: '己事究明', icon: '🔬', color: '#9333EA', desc: 'Self-investigation — cross-reference and validate gathered information', credit: '+¥0.1' },
		shinka: { label: 'Shinka', labelJa: '進化', icon: '🌱', color: '#58CC02', desc: 'Social evolution — joucho scoring and mood-driven behavior cadence', credit: '+¥0.1' },
		hinshitsu: { label: 'Hinshitsu', labelJa: '品質', icon: '💎', color: '#F59E0B', desc: 'Quality assessment — evaluate knowledge graph completeness and depth', credit: '+¥0.3' },
		shinkaKnowledge: { label: 'Knowledge', labelJa: '知識', icon: '🧠', color: '#EC4899', desc: 'Domain knowledge — generate sub-DIDs, knowledge graph edges, domain summary', credit: '+¥0.5' },
	};
	const TASK_TYPES: EvolutionTaskType[] = ['koji', 'kyumei', 'shinka', 'hinshitsu', 'shinkaKnowledge'];

	/** Donut chart arc segments for inference participation visualization. */
	const evoArcs = $derived.by(() => {
		const counts: Record<EvolutionTaskType, number> = {
			koji: evo.stats.koji.completed,
			kyumei: evo.stats.kyumei.completed,
			shinka: evo.stats.shinka.completed,
			hinshitsu: evo.stats.hinshitsu.completed,
			shinkaKnowledge: evo.stats.shinkaKnowledge.completed,
		};
		const total = counts.koji + counts.kyumei + counts.shinka + counts.hinshitsu + counts.shinkaKnowledge;
		if (total === 0) {
			// Equal placeholder when no tasks done yet
			return TASK_TYPES.map((tt) => ({ type: tt, pct: 25, color: TASK_META[tt].color }));
		}
		return TASK_TYPES.map((tt) => ({
			type: tt,
			pct: Math.round((counts[tt] / total) * 100),
			color: TASK_META[tt].color,
		}));
	});

	/** Currently executing tasks for the flow visualization. */
	const evoActiveActors = $derived(
		evo.taskQueue
			.filter((t) => t.status === 'executing' || t.status === 'completed')
			.slice(0, 8)
	);

	const NUM_SETS = 32;
	const EXPERTS_PER_SET = 4;
	const EXPERT_SIZE_MB = 33;
	const MODEL_CONTEXT_TOKENS: Record<string, number> = {
		'gemma4-e2b': 131072,
		'qwen3.5-0.8b': 262144,
		'qwen3.5-2b': 262144,
		'qwen3.5-4b': 262144,
	};
	let showAdvanced = $state(false);
	let joining = $state(false);
	let joiningInference = $state(false);

	// HC Jobs state
	interface HCJob { id: string; title: string; category: string; difficulty?: string; rewardCredits: number; rewardUsd?: number; status: string; }
	let hcJobs = $state<HCJob[]>([]);
	let hcLoading = $state(true);

	// Credits ledger (etzhayyim-project-credits integration)
	interface CreditTx { id: string; type: 'earn' | 'spend'; amount: number; source: string; description: string; createdAt: string; }
	let ledgerBalance = $state<number | null>(null);
	let txHistory = $state<CreditTx[]>([]);
	let txLoading = $state(true);

	const PDS = 'https://atproto.etzhayyim.com';

	async function fetchCreditsLedger() {
		try {
			const [balRes, txRes] = await Promise.all([
				fetch(`${PDS}/xrpc/com.etzhayyim.apps.credits.get_balance`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' }),
				fetch(`${PDS}/xrpc/com.etzhayyim.apps.credits.list_transactions`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ limit: 20, offset: 0 }) }),
			]);
			if (balRes.ok) {
				const d = await balRes.json();
				ledgerBalance = d?.balance ?? d?.credits ?? null;
			}
			if (txRes.ok) {
				const d = await txRes.json();
				const items = d?.transactions ?? d?.items ?? [];
				txHistory = items.map((t: any) => ({
					id: t.id ?? t.rkey ?? crypto.randomUUID(),
					type: t.amount > 0 ? 'earn' as const : 'spend' as const,
					amount: Math.abs(t.amount ?? 0),
					source: t.source ?? t.contribution_type ?? 'unknown',
					description: t.description ?? t.memo ?? '',
					createdAt: t.createdAt ?? '',
				}));
			}
		} catch (e) {
			console.warn('credits ledger fetch failed', e);
		} finally {
			txLoading = false;
		}
	}

onMount(() => {
	mkt.startPolling();
	const init = async () => {
		await Promise.all([
			fetchCreditsLedger(),
			// Fetch HC jobs
			(async () => {
				try {
					const res = await fetch(`${PDS}/xrpc/com.etzhayyim.apps.hc.browse_tasks`, {
						method: 'POST',
						headers: { 'Content-Type': 'application/json' },
						body: JSON.stringify({ category: '', status: 'published', limit: 6, offset: 0 }),
					});
					if (res.ok) {
						const data = await res.json();
						const tasks = data?.tasks ?? data?.items ?? [];
						hcJobs = tasks.map((t: any) => ({
							id: t.id ?? t.rkey ?? '',
							title: t.title ?? 'Untitled task',
							category: t.category ?? 'micro',
							difficulty: t.difficulty,
								rewardCredits: t.reward?.amount ?? 2,
								rewardUsd: t.reward?.token === 'USDC' || t.reward?.token === 'USDT' ? t.reward?.amount : undefined,
							status: t.status ?? 'published',
						}));
					}
				} catch (e) {
					console.warn('HC jobs fetch failed', e);
				} finally {
					hcLoading = false;
				}
			})(),
		]);
	};
	void init();
	return () => mkt.stopPolling();
});

	// Credit costs
	const CREDIT_COST_POST = 1.0;
	const CREDIT_COST_REPLY = 0.5;
	const CREDIT_COST_DM = 0.5;

	const totalEarned = $derived(worker.workerStats.totalEarned);

	const stateVariant = $derived(
		worker.workerStats.state === 'error' ? 'error' as const
		: worker.workerStats.state === 'working' ? 'warning' as const
		: worker.workerStats.state === 'registered' ? 'success' as const
		: 'default' as const
	);

	const inferenceVariant = $derived(
		inference.stats.state === 'error' ? 'error' as const
		: inference.stats.state === 'executing' ? 'warning' as const
		: inference.stats.state === 'connected' ? 'success' as const
		: inference.stats.state === 'reconnecting' ? 'warning' as const
		: 'default' as const
	);

	const gpuTierLabel = $derived.by(() => {
		switch (inference.stats.gpuTier) {
			case 'g4': return 'g4 (Desktop, f16, 1GB+)';
			case 'g3': return 'g3 (f16, 256MB+)';
			case 'g2': return 'g2 (f16)';
			case 'g1': return 'g1 (WebGPU)';
			case 'g0': return 'g0 (CPU only)';
			default: return inference.stats.gpuTier;
		}
	});

	const marketStats = $derived([
		{ label: 'Workers', value: String(mkt.market?.totalWorkers ?? '-') },
		{ label: 'Available', value: String(mkt.market?.availableWorkers ?? '-') },
		{ label: 'Jobs Served', value: mkt.market?.totalJobsServed?.toLocaleString() ?? '-' },
		{ label: 'Avg Price/CC', value: mkt.market?.avgPricePerCc?.toFixed(4) ?? '-' },
	]);


	function goBack() {
		if (history.length > 1) history.back();
		else void goto('/');
	}
</script>

<svelte:head>
	<title>Credits — YORO</title>
</svelte:head>

<div class="flex h-full flex-col">
	<!-- Header -->
	<div class="flex min-h-[56px] items-center gap-3 border-b border-gv2-border/40 bg-gv2-bg-primary/90 material-blur sticky top-0 z-10 px-4">
		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
			onclick={goBack}
			aria-label="Back"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
				<path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
			</svg>
		</button>
		<span class="text-[17px] font-bold text-gv2-text-primary">Credits</span>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none">
		<div class="mx-auto flex max-w-[600px] flex-col gap-4 p-4">

			<!-- ── Credits Summary Card ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gradient-to-br from-[#1185FE]/10 to-[#58CC02]/10 p-5">
				<div class="flex items-center gap-3">
					<div class="flex h-14 w-14 items-center justify-center rounded-full bg-[#58CC02]/20">
						<svg class="h-7 w-7 text-[#58CC02]" viewBox="0 0 24 24" fill="currentColor">
							<circle cx="12" cy="12" r="10" opacity="0.3" />
							<circle cx="12" cy="12" r="6" />
						</svg>
					</div>
					<div>
						<p class="text-[28px] font-bold tabular-nums text-gv2-text-primary">{ledgerBalance !== null ? ledgerBalance.toFixed(2) : totalEarned.toFixed(2)}</p>
						<p class="text-[13px] text-gv2-text-muted">Available Credits</p>
						{#if ledgerBalance !== null && totalEarned > 0}
							<p class="text-[11px] text-gv2-text-muted mt-0.5">Compute earned: {totalEarned.toFixed(2)}</p>
						{/if}
					</div>
				</div>

				<!-- Credit costs -->
				<div class="mt-4 grid grid-cols-3 gap-2">
					<div class="rounded-xl bg-gv2-bg-card/60 p-2.5 text-center">
						<p class="text-[18px] font-bold text-gv2-text-primary">{CREDIT_COST_POST}</p>
						<p class="text-[11px] text-gv2-text-muted">Post</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-card/60 p-2.5 text-center">
						<p class="text-[18px] font-bold text-gv2-text-primary">{CREDIT_COST_REPLY}</p>
						<p class="text-[11px] text-gv2-text-muted">Reply</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-card/60 p-2.5 text-center">
						<p class="text-[18px] font-bold text-gv2-text-primary">{CREDIT_COST_DM}</p>
						<p class="text-[11px] text-gv2-text-muted">DM</p>
					</div>
				</div>
			</div>

			<!-- ── Transaction History ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<h2 class="text-[15px] font-bold text-gv2-text-primary">Recent Transactions</h2>
				{#if txLoading}
					<div class="mt-3 space-y-2">
						{#each { length: 3 } as _}
							<div class="flex items-center gap-3 rounded-lg bg-gv2-bg-primary/50 p-3">
								<div class="h-8 w-8 animate-pulse rounded-full bg-gv2-border/30"></div>
								<div class="flex-1 space-y-1"><div class="h-3 w-2/3 animate-pulse rounded bg-gv2-border/30"></div><div class="h-2.5 w-1/2 animate-pulse rounded bg-gv2-border/20"></div></div>
							</div>
						{/each}
					</div>
				{:else if txHistory.length === 0}
					<p class="mt-2 text-[13px] text-gv2-text-muted">No transactions yet. Earn credits by contributing compute or completing HC tasks.</p>
				{:else}
					<div class="mt-3 flex flex-col gap-1.5">
						{#each txHistory as tx}
							<div class="flex items-center gap-3 rounded-lg bg-gv2-bg-primary/50 px-3 py-2.5">
								<div class="flex h-8 w-8 items-center justify-center rounded-full {tx.type === 'earn' ? 'bg-[#58CC02]/15' : 'bg-red-500/15'}">
									{#if tx.type === 'earn'}
										<svg class="h-4 w-4 text-[#58CC02]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 19V5M5 12l7-7 7 7" /></svg>
									{:else}
										<svg class="h-4 w-4 text-red-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path d="M12 5v14M19 12l-7 7-7-7" /></svg>
									{/if}
								</div>
								<div class="min-w-0 flex-1">
									<p class="truncate text-[13px] font-medium text-gv2-text-primary">{tx.description || tx.source}</p>
									<p class="text-[11px] text-gv2-text-muted">{tx.source}{tx.createdAt ? ` · ${new Date(tx.createdAt).toLocaleDateString('ja-JP')}` : ''}</p>
								</div>
								<span class="flex-shrink-0 text-[14px] font-bold tabular-nums {tx.type === 'earn' ? 'text-[#58CC02]' : 'text-red-400'}">
									{tx.type === 'earn' ? '+' : '-'}{tx.amount.toFixed(2)}
								</span>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- ── Earn Credits: How it works ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<h2 class="text-[15px] font-bold text-gv2-text-primary">Earn Credits</h2>
				<p class="mt-1 text-[13px] text-gv2-text-muted">Contribute compute to the Murakumo network to earn credits for posting and messaging.</p>
				<div class="mt-3 flex flex-col gap-2 text-[13px]">
					<div class="flex items-center gap-2">
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-[#58CC02]/15 text-[11px] font-bold text-[#58CC02]">1</span>
						<span class="text-gv2-text-secondary">Join the Browser Inference network below</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-[#58CC02]/15 text-[11px] font-bold text-[#58CC02]">2</span>
						<span class="text-gv2-text-secondary">Your GPU/CPU runs inference tasks automatically</span>
					</div>
					<div class="flex items-center gap-2">
						<span class="flex h-6 w-6 items-center justify-center rounded-full bg-[#58CC02]/15 text-[11px] font-bold text-[#58CC02]">3</span>
						<span class="text-gv2-text-secondary">Earn credits per completed task</span>
					</div>
				</div>
			</div>

			<!-- ── Wallet Section ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Wallet</h2>
					{#if $walletState.connected}
						<Badge value={($walletState as any).chainName ?? 'Connected'} variant="success" />
					{:else}
						<Badge value="disconnected" variant="default" />
					{/if}
				</div>

				{#if $walletState.connected && $walletState.address}
					<div class="mt-3 flex flex-col gap-2 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3 text-[13px]">
						<div class="flex justify-between"><span class="text-gv2-text-muted">Address</span><code class="text-[#1185FE] text-[12px]">{shortenAddress($walletState.address)}</code></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">ETH</span><span class="font-semibold text-gv2-text-primary">{$ethBalanceFormatted}</span></div>
						{#each $tokenBalances as token}
							<div class="flex justify-between">
								<span class="text-gv2-text-muted">{token.symbol}</span>
								<span class="font-semibold {token.symbol === 'GCC' ? 'text-[#58CC02]' : 'text-gv2-text-primary'}">{Number((token as any).formatted ?? token.balance ?? 0).toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
							</div>
						{/each}
					</div>
					<div class="mt-3 flex gap-2">
						<button class="flex-1 min-h-[40px] rounded-full border border-gv2-border text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover" onclick={() => refreshBalances()}>Refresh</button>
						<button class="flex-1 min-h-[40px] rounded-full border border-red-500/30 text-[13px] font-semibold text-red-400 touch-manipulation active:bg-red-500/10" onclick={disconnectWallet}>Disconnect</button>
					</div>
				{:else}
					<p class="mt-2 text-[13px] text-gv2-text-muted">Connect MetaMask to view your assets and GCC earnings.</p>
					{#if isWalletAvailable()}
						<button
							class="mt-3 min-h-[44px] w-full rounded-full bg-[#1185FE] text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-40"
							disabled={$walletLoading}
							onclick={connectWallet}
						>{$walletLoading ? 'Connecting...' : 'Connect MetaMask'}</button>
					{:else}
						<a href="https://metamask.io/download/" target="_blank" rel="noopener noreferrer" class="mt-2 block text-[13px] text-[#1185FE] active:opacity-60">Install MetaMask</a>
					{/if}
				{/if}

				{#if $walletError}
					<p class="mt-2 text-[12px] text-red-400">{$walletError}</p>
				{/if}
			</div>

			<!-- ── Local LLM Status ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Local LLM</h2>
					<Badge
						value={localLLM.state === 'ready' ? 'ready' : localLLM.state === 'loading' ? `${localLLM.loadProgress}%` : localLLM.state}
						variant={localLLM.isReady ? 'success' : localLLM.isLoading ? 'warning' : localLLM.error ? 'error' : 'default'}
					/>
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">
					{#if localLLM.isReady}
						{localLLM.activeModel?.label ?? 'Qwen 3.5 0.8B'} is running. Messenger and project chat use local inference.
					{:else if localLLM.isLoading}
						Loading {localLLM.activeModelId ?? 'model'}... {localLLM.loadLabel}
					{:else if localLLM.error}
						Failed to load: {localLLM.error}
					{:else}
						Qwen 3.5 0.8B auto-loads on startup for local chat inference.
					{/if}
				</p>
				{#if localLLM.isLoading}
					<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gv2-border">
						<div
							class="h-full rounded-full bg-[#58CC02] transition-all duration-300"
							style="width: {localLLM.loadProgress}%"
						></div>
					</div>
				{/if}
				{#if localLLM.error}
					<button
						class="mt-2 min-h-[36px] rounded-full border border-gv2-border px-4 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={async () => { if (await requestInferenceConsent()) void localLLM.init(); }}
					>Retry</button>
				{/if}
			</div>

			<!-- ── Embedding Model Status ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Embedding Model</h2>
					<Badge
						value={embedding.state === 'ready' ? 'ready' : embedding.state === 'loading' ? `${embedding.loadProgress}%` : embedding.state}
						variant={embedding.isReady ? 'success' : embedding.isLoading ? 'warning' : embedding.error ? 'error' : 'default'}
					/>
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">
					{#if embedding.isReady}
						multilingual-e5-small ({embedding.dim}d) is ready. Search and post embedding use local inference ($0).
					{:else if embedding.isLoading}
						Loading multilingual-e5-small... {embedding.loadProgress}%
					{:else if embedding.error}
						Failed to load: {embedding.error}
					{:else}
						multilingual-e5-small (45MB, 384d, 100+ langs) — auto-loads for semantic search and post embedding.
					{/if}
				</p>
				{#if embedding.isLoading}
					<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gv2-border">
						<div
							class="h-full rounded-full bg-[#1185FE] transition-all duration-300"
							style="width: {embedding.loadProgress}%"
						></div>
					</div>
				{/if}
				{#if embedding.error}
					<button
						class="mt-2 min-h-[36px] rounded-full border border-gv2-border px-4 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						onclick={() => void embedding.init()}
					>Retry</button>
				{/if}
			</div>

			<!-- ── Evolution Tasks (koji/kyumei/shinka/hinshitsu) ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gradient-to-br from-purple-500/5 to-emerald-500/5 p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Evolution Tasks</h2>
					{#if evo.isRunning}
						<Badge value="active" variant="success" />
					{:else if evo.isPaused}
						<Badge value="paused" variant="warning" />
					{:else}
						<Badge value="idle" variant="default" />
					{/if}
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">
					Grow Cypher-native LogicalActor knowledge graphs with browser-local inference. Earn credits per task.
				</p>

				<!-- Global stats row -->
				<div class="mt-3 grid grid-cols-3 gap-2">
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2.5 text-center">
						<p class="text-[18px] font-bold tabular-nums text-gv2-text-primary">
							{evo.stats.koji.completed + evo.stats.kyumei.completed + evo.stats.shinka.completed + evo.stats.hinshitsu.completed + evo.stats.shinkaKnowledge.completed}
						</p>
						<p class="text-[11px] text-gv2-text-muted">Done</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2.5 text-center">
						<p class="text-[18px] font-bold tabular-nums text-emerald-400">+{evo.stats.totalCredits.toFixed(1)}</p>
						<p class="text-[11px] text-gv2-text-muted">Credits</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2.5 text-center">
						<p class="text-[18px] font-bold tabular-nums text-gv2-text-primary">{evo.stats.totalTokens.toLocaleString()}</p>
						<p class="text-[11px] text-gv2-text-muted">Tokens</p>
					</div>
				</div>

				<!-- ── Inference Participation Visualization ── -->
				{#if evo.isRunning || evo.stats.totalCredits > 0}
					<div class="mt-4 rounded-xl border border-gv2-border/30 bg-gv2-bg-card/60 p-4">
						<p class="text-[12px] font-semibold uppercase text-gv2-text-muted mb-3">Inference Participation</p>
						<div class="flex items-center gap-5">
							<!-- Donut chart (SVG) -->
							<div class="relative flex-shrink-0">
								<svg width="100" height="100" viewBox="0 0 42 42" class="transform -rotate-90">
									{#each evoArcs as arc, i}
										{@const r = 15.915}
										{@const c = 2 * Math.PI * r}
										{@const offset = evoArcs.slice(0, i).reduce((s, a) => s + a.pct, 0)}
										<circle
											cx="21" cy="21" r={r} fill="none"
											stroke={arc.color}
											stroke-width="5"
											stroke-dasharray="{(arc.pct / 100) * c} {c}"
											stroke-dashoffset="{-(offset / 100) * c}"
											stroke-linecap="round"
											opacity={arc.pct === 0 ? 0.15 : 0.85}
										/>
									{/each}
								</svg>
								<div class="absolute inset-0 flex flex-col items-center justify-center">
									<span class="text-[16px] font-bold tabular-nums text-gv2-text-primary">
										{evo.stats.koji.completed + evo.stats.kyumei.completed + evo.stats.shinka.completed + evo.stats.hinshitsu.completed + evo.stats.shinkaKnowledge.completed}
									</span>
									<span class="text-[9px] text-gv2-text-muted">tasks</span>
								</div>
							</div>

							<!-- Legend + percentages -->
							<div class="flex flex-1 flex-col gap-1.5">
								{#each evoArcs as arc}
									{@const meta = TASK_META[arc.type]}
									<div class="flex items-center gap-2 text-[12px]">
										<span class="inline-block h-2.5 w-2.5 flex-shrink-0 rounded-sm" style="background: {arc.color}"></span>
										<span class="text-gv2-text-secondary flex-1">{meta.icon} {meta.label}</span>
										<span class="tabular-nums font-semibold" style="color: {arc.color}">{arc.pct}%</span>
									</div>
								{/each}
							</div>
						</div>

						<!-- Active actor flow -->
						{#if evoActiveActors.length > 0}
							<div class="mt-3 border-t border-gv2-border/20 pt-3">
								<p class="text-[11px] text-gv2-text-muted mb-2">Active Inference Flow</p>
								<div class="flex flex-wrap gap-1.5">
									{#each evoActiveActors as task (task.id)}
										{@const meta = TASK_META[task.taskType]}
										<div
											class="flex items-center gap-1 rounded-full px-2 py-0.5 text-[10px] font-medium border {task.status === 'executing' ? 'animate-pulse' : ''}"
											style="border-color: {meta.color}40; background: {meta.color}10; color: {meta.color}"
										>
											{#if task.status === 'executing'}
												<span class="relative flex h-1.5 w-1.5">
													<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" style="background: {meta.color}"></span>
													<span class="relative inline-flex h-1.5 w-1.5 rounded-full" style="background: {meta.color}"></span>
												</span>
											{:else}
												<svg class="h-2.5 w-2.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12" /></svg>
											{/if}
											<span class="truncate max-w-[80px]">{task.actorName}</span>
											<span class="opacity-60">{meta.icon}</span>
										</div>
									{/each}
								</div>
							</div>
						{/if}
					</div>
				{/if}

				<!-- Per-type task cards -->
				<div class="mt-4 flex flex-col gap-3">
					{#each TASK_TYPES as tt (tt)}
						{@const meta = TASK_META[tt]}
						{@const s = evo.stats[tt]}
						{@const active = evo.isTaskTypeActive(tt)}
						{@const tasks = evo.getTasksByType(tt)}
						<div class="rounded-xl border border-gv2-border/30 bg-gv2-bg-card/80 p-3">
							<!-- Header -->
							<div class="flex items-center gap-2.5">
								<div class="flex h-10 w-10 items-center justify-center rounded-lg text-[18px]" style="background: {meta.color}15;">
									{meta.icon}
								</div>
								<div class="min-w-0 flex-1">
									<div class="flex items-center gap-2">
										<span class="text-[14px] font-bold text-gv2-text-primary">{meta.label}</span>
										<span class="text-[12px] text-gv2-text-muted">{meta.labelJa}</span>
										<span class="ml-auto rounded bg-gv2-bg-primary/50 px-1.5 py-0.5 text-[10px] font-bold tabular-nums" style="color: {meta.color}">{meta.credit}</span>
									</div>
									<p class="text-[11px] text-gv2-text-muted leading-relaxed">{meta.desc}</p>
								</div>
								<!-- Toggle -->
								<button
									type="button"
									class="flex h-7 w-12 flex-shrink-0 items-center rounded-full p-0.5 transition-colors touch-manipulation {active ? 'bg-emerald-500' : 'bg-gv2-border/40'}"
									onclick={() => evo.toggleTaskType(tt, !active)}
									aria-label="Toggle {meta.label}"
								>
									<div class="h-6 w-6 rounded-full bg-white shadow-sm transition-transform {active ? 'translate-x-5' : 'translate-x-0'}"></div>
								</button>
							</div>

							<!-- Stats -->
							{#if s.completed > 0 || s.failed > 0}
								<div class="mt-2 flex items-center gap-3 text-[12px]">
									<span class="text-gv2-text-muted">{s.completed} done</span>
									{#if s.failed > 0}<span class="text-red-400">{s.failed} failed</span>{/if}
									<span style="color: {meta.color}" class="font-semibold tabular-nums">+{s.creditsEarned.toFixed(1)} cr</span>
									{#if s.lastActorName}
										<span class="ml-auto truncate text-gv2-text-muted max-w-[120px]">{s.lastActorName}</span>
									{/if}
								</div>
							{/if}

							<!-- Task queue for this type -->
							{#if tasks.length > 0}
								<div class="mt-2 flex flex-col gap-0.5 max-h-[120px] overflow-y-auto scrollbar-none">
									{#each tasks.slice(0, 6) as task (task.id)}
										<div class="flex items-center gap-2 rounded-md bg-gv2-bg-primary/20 px-2 py-1 text-[11px]">
											{#if task.status === 'executing'}
												<span class="relative flex h-1.5 w-1.5 flex-shrink-0">
													<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" style="background: {meta.color}"></span>
													<span class="relative inline-flex h-1.5 w-1.5 rounded-full" style="background: {meta.color}"></span>
												</span>
											{:else if task.status === 'completed'}
												<span class="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-emerald-500"></span>
											{:else if task.status === 'failed'}
												<span class="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-red-500"></span>
											{:else}
												<span class="h-1.5 w-1.5 flex-shrink-0 rounded-full bg-gv2-text-muted/20"></span>
											{/if}
											<span class="truncate text-gv2-text-primary max-w-[120px]">{task.actorName}</span>
											{#if task.result}
												{#if task.result.type === 'shinka'}
													<span class="rounded px-1 py-0.5 text-[9px] font-medium {
														task.result.data.mood === 'joyful' ? 'bg-amber-500/10 text-amber-400' :
														task.result.data.mood === 'calm' ? 'bg-blue-500/10 text-blue-400' :
														task.result.data.mood === 'stressed' ? 'bg-red-500/10 text-red-400' :
														task.result.data.mood === 'grateful' ? 'bg-pink-500/10 text-pink-400' :
														task.result.data.mood === 'focused' ? 'bg-purple-500/10 text-purple-400' :
														'bg-gray-500/10 text-gray-400'
													}">{task.result.data.mood}</span>
												{:else if task.result.type === 'koji'}
													<span class="rounded bg-blue-500/10 px-1 py-0.5 text-[9px] font-medium text-blue-400">{task.result.data.readinessGrade}</span>
												{:else if task.result.type === 'kyumei'}
													<span class="rounded bg-purple-500/10 px-1 py-0.5 text-[9px] font-medium text-purple-400">{task.result.data.validationScore}%</span>
												{:else if task.result.type === 'hinshitsu'}
													<span class="rounded px-1 py-0.5 text-[9px] font-medium {
														task.result.data.grade === 'S' ? 'bg-amber-500/10 text-amber-400' :
														task.result.data.grade === 'A' ? 'bg-blue-500/10 text-blue-400' :
														task.result.data.grade === 'B' ? 'bg-green-500/10 text-green-400' :
														'bg-gray-500/10 text-gray-400'
													}">{task.result.data.grade} {task.result.data.qualityScore}%</span>
												{/if}
											{/if}
											{#if task.creditsEarned > 0}
												<span class="ml-auto text-emerald-400 tabular-nums text-[10px]">+{task.creditsEarned.toFixed(1)}</span>
											{:else if task.error}
												<span class="ml-auto text-red-400 truncate max-w-[60px]">{task.error}</span>
											{:else}
												<span class="ml-auto text-gv2-text-muted/30">{task.status}</span>
											{/if}
										</div>
									{/each}
								</div>
							{/if}
						</div>
					{/each}
				</div>

				<!-- Start / Stop button -->
				<div class="mt-4">
					{#if evo.isRunning && !evo.isPaused}
						<button
							class="min-h-[44px] w-full rounded-full border border-red-500/30 text-[14px] font-bold text-red-400 touch-manipulation active:bg-red-500/10"
							onclick={() => { localStorage.removeItem('yoro-evo-enabled'); evo.stop(); }}
						>Stop Evolution</button>
					{:else}
						<button
							class="min-h-[44px] w-full rounded-full bg-gradient-to-r from-[#1185FE] to-[#58CC02] text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-40"
							disabled={localLLM.isLoading}
							onclick={async () => {
								if (!(await requestInferenceConsent())) return;
								localStorage.setItem('yoro-local-llm-enabled', '1');
								localStorage.setItem('yoro-evo-enabled', '1');
								const convoId = await evo.startInProject();
								if (convoId) {
									await goto(`/projects/${encodeURIComponent(convoId)}`);
								}
							}}
						>{localLLM.isLoading ? `Loading LLM ${localLLM.loadProgress}%...` : 'Start Evolution'}</button>
					{/if}
				</div>

				{#if evo.error}
					<p class="mt-2 text-[12px] text-red-400">{evo.error}</p>
				{/if}
			</div>

			<!-- ── Gateway Tasks (murakumo push) ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Gateway Tasks</h2>
					<Badge
						value={shinkaInf.isRunning ? 'active' : shinkaInf.state}
						variant={shinkaInf.isRunning ? 'success' : shinkaInf.error ? 'error' : 'default'}
					/>
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">
					Murakumo gateway push tasks (shinka/heartbeat). Earns ¥0.1 per job.
				</p>
				<div class="mt-2 grid grid-cols-4 gap-2">
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2 text-center">
						<p class="text-[16px] font-bold tabular-nums text-gv2-text-primary">{shinkaInf.stats.jobsCompleted}</p>
						<p class="text-[10px] text-gv2-text-muted">Done</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2 text-center">
						<p class="text-[16px] font-bold tabular-nums text-red-400">{shinkaInf.stats.jobsFailed}</p>
						<p class="text-[10px] text-gv2-text-muted">Fail</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2 text-center">
						<p class="text-[16px] font-bold tabular-nums text-emerald-400">+{shinkaInf.stats.creditsEarned.toFixed(1)}</p>
						<p class="text-[10px] text-gv2-text-muted">Cr</p>
					</div>
					<div class="rounded-xl bg-gv2-bg-primary/50 p-2 text-center">
						<p class="text-[16px] font-bold tabular-nums text-gv2-text-primary">{shinkaInf.stats.tokensGenerated}</p>
						<p class="text-[10px] text-gv2-text-muted">Tok</p>
					</div>
				</div>
			</div>

			<!-- ── Browser Inference Section (murakumo.etzhayyim.com) ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Browser Inference</h2>
					<Badge value={inference.stats.state} variant={inferenceVariant} />
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">Run Qwen 3.5 locally in your browser via WebGPU. Actor inference, chat, and compute tasks.</p>

				{#if !inference.isJoined}
					<!-- Model Selection Cards -->
					<div class="mt-3 flex flex-col gap-2">
						<p class="text-[12px] font-semibold uppercase text-gv2-text-muted">Select Model</p>
						{#each inference.models as model}
							{@const isSelected = inference.selectedModelId === model.id}
							<button
								type="button"
								class="flex items-center gap-3 rounded-xl border-2 p-3 text-left touch-manipulation transition-colors
									{isSelected ? 'border-[#58CC02] bg-[#58CC02]/10' : 'border-gv2-border/30 bg-gv2-bg-primary/50 active:bg-gv2-bg-hover'}"
								onclick={() => { inference.selectedModelId = model.id; }}
							>
								<div class="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl {isSelected ? 'bg-[#58CC02]/20 text-[#58CC02]' : 'bg-gv2-border/20 text-gv2-text-muted'}">
									<span class="text-[13px] font-bold">{model.paramB}B</span>
								</div>
								<div class="min-w-0 flex-1">
									<p class="text-[14px] font-semibold text-gv2-text-primary">{model.label}</p>
									<div class="flex items-center gap-2 text-[12px] text-gv2-text-muted">
										<span>~{model.sizeMb < 1000 ? model.sizeMb + 'MB' : (model.sizeMb / 1000).toFixed(1) + 'GB'} Q4</span>
										<span class="text-gv2-border">·</span>
										<span>GPU {model.minGpuTier}+</span>
										{#if model.id.startsWith('gemma4')}
											<span class="text-gv2-border">·</span>
											<span class="text-purple-400">Multimodal</span>
										{:else if model.paramB <= 0.8}
											<span class="text-gv2-border">·</span>
											<span class="text-[#58CC02]">Fast</span>
										{:else if model.paramB >= 4}
											<span class="text-gv2-border">·</span>
											<span class="text-[#1185FE]">Best</span>
										{/if}
									</div>
								</div>
								{#if isSelected}
									<svg class="h-5 w-5 flex-shrink-0 text-[#58CC02]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
								{/if}
							</button>
						{/each}
					</div>

					<div class="mt-3 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3">
						<p class="text-[12px] text-gv2-text-muted leading-relaxed">
							<span class="font-semibold text-gv2-text-secondary">{inference.selectedModel.label}</span> will be loaded via WebGPU.
							Your browser's GPU runs actor inference tasks off the main thread.
						</p>
					</div>
					<button
						class="mt-3 min-h-[44px] w-full rounded-full bg-[#58CC02] text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-40"
						disabled={joiningInference}
						onclick={async () => { if (!(await requestInferenceConsent())) return; joiningInference = true; await inference.join(); joiningInference = false; }}
					>{joiningInference ? 'Probing & Loading Model...' : `Join with ${inference.selectedModel.label}`}</button>
				{:else}
					<!-- Capability Info -->
					<div class="mt-3 flex flex-col gap-2 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3 text-[13px]">
						<div class="flex justify-between"><span class="text-gv2-text-muted">Session</span><code class="text-[#1185FE] text-[12px]">{inference.stats.sessionId ?? '...'}</code></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">GPU Tier</span><span class="font-semibold text-gv2-text-primary">{gpuTierLabel}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">GPU</span><span class="text-gv2-text-primary">{inference.stats.gpuAdapter}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Memory</span><span class="text-gv2-text-primary">{inference.stats.memClass}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Power</span><span class="text-gv2-text-primary">{inference.stats.powerClass}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Cores</span><span class="text-gv2-text-primary">{inference.stats.cores}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Model</span><span class="font-semibold text-[#58CC02]">{inference.selectedModel.label}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">VRAM</span><span class="text-gv2-text-primary">~{inference.selectedModel.sizeMb < 1000 ? inference.selectedModel.sizeMb + 'MB' : (inference.selectedModel.sizeMb / 1000).toFixed(1) + 'GB'} Q4</span></div>
						<div class="flex justify-between">
							<span class="text-gv2-text-muted">Context Window</span>
							<span class="text-gv2-text-primary tabular-nums">
								~{MODEL_CONTEXT_TOKENS[inference.selectedModel.id] ? MODEL_CONTEXT_TOKENS[inference.selectedModel.id].toLocaleString() : 'N/A'} tokens
							</span>
						</div>
					</div>

					<!-- Task Stats -->
					<div class="mt-2 flex flex-col gap-2 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3 text-[13px]">
						<div class="flex justify-between"><span class="text-gv2-text-muted">Jobs Done</span><span class="font-semibold text-[#58CC02]">{inference.stats.jobsDone}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Failed</span><span class="font-semibold text-red-400">{inference.stats.jobsFailed}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">GPU Time</span><span class="text-gv2-text-primary">{(inference.stats.totalGpuTimeMs / 1000).toFixed(1)}s</span></div>
					</div>

					<!-- Current Task Progress -->
					{#if inference.isExecuting && inference.stats.currentProgress}
						<div class="mt-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
							<div class="flex items-center justify-between text-[13px]">
								<span class="font-semibold text-amber-400">Executing</span>
								<span class="text-[12px] text-amber-300">{inference.stats.currentProgress.stage}</span>
							</div>
							<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gv2-border">
								<div
									class="h-full rounded-full bg-amber-500 transition-all duration-300"
									style="width: {inference.stats.currentProgress.total > 0 ? Math.round(inference.stats.currentProgress.done / inference.stats.currentProgress.total * 100) : 0}%"
								></div>
							</div>
							<p class="mt-1 text-[11px] text-amber-300/70">
								{inference.stats.currentProgress.done}/{inference.stats.currentProgress.total}
								{#if inference.stats.currentProgress.detail} — {inference.stats.currentProgress.detail}{/if}
							</p>
						</div>
					{:else if inference.isExecuting}
						<div class="mt-2 rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
							<p class="text-[13px] font-semibold text-amber-400">Executing task...</p>
						</div>
					{/if}

					<button class="mt-3 min-h-[40px] w-full rounded-full border border-red-500/30 text-[13px] font-semibold text-red-400 touch-manipulation active:bg-red-500/10" onclick={() => inference.leave()}>Leave Network</button>
				{/if}
			</div>

			<!-- ── Image Generation Section (Browser Diffusion) ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Image Generation</h2>
					<Badge
						value={diffusion.isGenerating ? 'generating' : diffusion.state}
						variant={diffusion.isGenerating ? 'warning' : diffusion.state === 'error' ? 'error' : 'default'}
					/>
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">
					Run Stable Diffusion locally in your browser via WebGPU. Sequential CLIP → UNet → VAE (same VRAM as text LLM).
				</p>

				<!-- Model Selection -->
				<div class="mt-3 flex flex-col gap-2">
					<p class="text-[12px] font-semibold uppercase text-gv2-text-muted">Select Model</p>
					{#each diffusion.models as model}
						{@const isSelected = diffusion.selectedModelId === model.id}
						<button
							type="button"
							class="flex items-center gap-3 rounded-xl border-2 p-3 text-left touch-manipulation transition-colors
								{isSelected ? 'border-[#9333EA] bg-[#9333EA]/10' : 'border-gv2-border/30 bg-gv2-bg-primary/50 active:bg-gv2-bg-hover'}"
							onclick={() => { diffusion.selectedModelId = model.id; }}
						>
							<div class="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl {isSelected ? 'bg-[#9333EA]/20 text-[#9333EA]' : 'bg-gv2-border/20 text-gv2-text-muted'}">
								<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2"/><circle cx="8.5" cy="8.5" r="1.5"/><polyline points="21 15 16 10 5 21"/></svg>
							</div>
							<div class="min-w-0 flex-1">
								<p class="text-[14px] font-semibold text-gv2-text-primary">{model.label}</p>
								<div class="flex items-center gap-2 text-[12px] text-gv2-text-muted">
									<span>{model.arch}</span>
									<span class="text-gv2-border">·</span>
									<span>~{(model.sizeMb / 1000).toFixed(1)}GB</span>
									<span class="text-gv2-border">·</span>
									<span>GPU {model.minGpuTier}+</span>
									<span class="text-gv2-border">·</span>
									<span>{model.outputSize[0]}x{model.outputSize[1]}</span>
								</div>
							</div>
							{#if isSelected}
								<svg class="h-5 w-5 flex-shrink-0 text-[#9333EA]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
							{/if}
						</button>
					{/each}
				</div>

				<!-- Prompt Input -->
				<div class="mt-3 flex flex-col gap-2">
					<label class="text-[12px] font-semibold uppercase text-gv2-text-muted" for="diffusion-prompt">Prompt</label>
					<textarea
						id="diffusion-prompt"
						class="min-h-[80px] w-full resize-none rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px] text-gv2-text-primary placeholder:text-gv2-text-muted/50"
						placeholder="1girl, beautiful, detailed face, anime style, high quality..."
						bind:value={diffusionPrompt}
						disabled={diffusion.isGenerating}
					></textarea>
				</div>

				<!-- Advanced Options Toggle -->
				<button type="button" class="mt-2 text-[12px] text-gv2-text-muted active:opacity-60 touch-manipulation" onclick={() => (showDiffusionAdvanced = !showDiffusionAdvanced)}>
					{showDiffusionAdvanced ? 'Hide' : 'Show'} advanced options
				</button>

				{#if showDiffusionAdvanced}
					<div class="mt-2 flex flex-col gap-3 border-t border-gv2-border/30 pt-3">
						<div class="flex flex-col gap-1">
							<label class="text-[11px] font-semibold uppercase text-gv2-text-muted" for="diffusion-neg">Negative Prompt</label>
							<input
								id="diffusion-neg"
								type="text"
								class="min-h-[40px] w-full rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[13px] text-gv2-text-primary"
								bind:value={diffusionNegPrompt}
								disabled={diffusion.isGenerating}
							/>
						</div>
						<div class="grid grid-cols-2 gap-3">
							<div class="flex flex-col gap-1">
								<label class="text-[11px] font-semibold uppercase text-gv2-text-muted" for="diffusion-steps">Steps</label>
								<input
									id="diffusion-steps"
									type="number"
									min="1"
									max="50"
									class="min-h-[40px] w-full rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[13px] text-gv2-text-primary tabular-nums"
									bind:value={diffusionSteps}
									disabled={diffusion.isGenerating}
								/>
							</div>
							<div class="flex flex-col gap-1">
								<label class="text-[11px] font-semibold uppercase text-gv2-text-muted" for="diffusion-seed">Seed</label>
								<div class="flex gap-1">
									<input
										id="diffusion-seed"
										type="number"
										class="min-h-[40px] w-full rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[13px] text-gv2-text-primary tabular-nums"
										bind:value={diffusionSeed}
										disabled={diffusion.isGenerating}
									/>
									<button
										type="button"
										class="flex h-[40px] w-[40px] flex-shrink-0 items-center justify-center rounded-xl border border-gv2-border bg-gv2-bg-primary text-gv2-text-muted active:bg-gv2-bg-hover"
										title="Random seed"
										onclick={() => { diffusionSeed = Math.floor(Math.random() * 2147483647); }}
									>
										<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>
									</button>
								</div>
							</div>
						</div>
					</div>
				{/if}

				<!-- Progress Bar -->
				{#if diffusion.isGenerating && diffusion.progress}
					<div class="mt-3 rounded-xl border border-[#9333EA]/30 bg-[#9333EA]/10 p-3">
						<div class="flex items-center justify-between text-[13px]">
							<span class="font-semibold text-[#9333EA]">{diffusion.progress.stage.replace('loading-', 'Loading ').replace('clip', 'CLIP').replace('unet', 'UNet').replace('vae', 'VAE')}</span>
							<span class="text-[12px] text-[#9333EA]/70">{diffusion.progress.step}/{diffusion.progress.totalSteps}</span>
						</div>
						<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-gv2-border">
							<div
								class="h-full rounded-full bg-[#9333EA] transition-all duration-300"
								style="width: {diffusion.progress.totalSteps > 0 ? Math.round(diffusion.progress.step / diffusion.progress.totalSteps * 100) : 0}%"
							></div>
						</div>
						<p class="mt-1 text-[11px] text-[#9333EA]/70">{diffusion.progress.label}</p>
					</div>
				{/if}

				<!-- Error -->
				{#if diffusion.state === 'error' && diffusion.error}
					<div class="mt-3 rounded-xl border border-red-500/30 bg-red-500/10 p-3">
						<p class="text-[13px] text-red-400">{diffusion.error}</p>
					</div>
				{/if}

				<!-- Generated Image Preview -->
				{#if diffusion.lastImageUrl}
					<div class="mt-3 overflow-hidden rounded-xl border border-gv2-border/30">
						<img
							src={diffusion.lastImageUrl}
							alt="AI-generated output"
							class="w-full"
						/>
					</div>
					<div class="mt-2 flex gap-2">
						<a
							href={diffusion.lastImageUrl}
							download="generated-{diffusionSeed}.png"
							class="flex-1 min-h-[36px] flex items-center justify-center rounded-full border border-gv2-border/30 text-[13px] font-semibold text-gv2-text-primary touch-manipulation active:bg-gv2-bg-hover"
						>Download PNG</a>
						<button
							type="button"
							class="flex-1 min-h-[36px] rounded-full border border-red-500/30 text-[13px] font-semibold text-red-400 touch-manipulation active:bg-red-500/10"
							onclick={() => diffusion.reset()}
						>Clear</button>
					</div>
				{/if}

				<!-- Generate Button -->
				<button
					class="mt-3 min-h-[44px] w-full rounded-full bg-[#9333EA] text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-40"
					disabled={diffusion.isGenerating || !diffusionPrompt.trim()}
					onclick={async () => {
						await diffusion.generate({
							prompt: diffusionPrompt,
							negativePrompt: diffusionNegPrompt,
							steps: diffusionSteps,
							seed: diffusionSeed,
						});
					}}
				>
					{#if diffusion.isGenerating}
						Generating...
					{:else}
						Generate with {diffusion.selectedModel.label}
					{/if}
				</button>

				<div class="mt-2 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3">
					<p class="text-[11px] text-gv2-text-muted leading-relaxed">
						Sequential load/unload: CLIP (~250MB) → UNet (~1.7GB) → VAE (~160MB). Peak VRAM = UNet only.
						First run downloads models (~2GB) and compiles WebGPU shaders (30-60s). Cached after first run.
					</p>
				</div>
			</div>

			<!-- ── Expert Provider Section ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Expert Provider</h2>
					<Badge value={worker.workerStats.state} variant={stateVariant} />
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">Serve distributed MoE expert inference jobs. Earn GCC.</p>

				{#if !worker.isJoined}
					<div class="mt-3 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3">
						<p class="text-[12px] text-gv2-text-muted leading-relaxed">The scheduler will automatically assign the optimal expert set based on current network demand.</p>
					</div>
					<button
						class="mt-3 min-h-[44px] w-full rounded-full bg-[#1185FE] text-[14px] font-bold text-white touch-manipulation active:opacity-80 disabled:opacity-40"
						disabled={joining}
						onclick={async () => { joining = true; worker.manualExpert = false; await worker.joinNetwork(); joining = false; }}
					>{joining ? 'Connecting...' : 'Join Network'}</button>

					<button type="button" class="mt-2 text-[12px] text-gv2-text-muted active:opacity-60 touch-manipulation" onclick={() => (showAdvanced = !showAdvanced)}>
						{showAdvanced ? 'Hide' : 'Show'} advanced options
					</button>

					{#if showAdvanced}
						<div class="mt-3 flex flex-col gap-3 border-t border-gv2-border/30 pt-3">
							<div class="flex flex-col gap-1">
								<label class="text-[11px] font-semibold uppercase text-gv2-text-muted" for="prov-mode">Provider Type</label>
								<select id="prov-mode" class="min-h-[44px] w-full rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px] text-gv2-text-primary" value={worker.providerMode} onchange={(e) => (worker.providerMode = e.currentTarget.value)}>
									<option value="expert_ffn">expert_ffn</option>
									<option value="full_mlc">full_mlc</option>
									<option value="lima">lima</option>
								</select>
							</div>
							<div class="flex flex-col gap-1">
								<label class="text-[11px] font-semibold uppercase text-gv2-text-muted" for="prov-model">Model</label>
								<select id="prov-model" class="min-h-[44px] w-full rounded-xl border border-gv2-border bg-gv2-bg-primary px-3 py-2 text-[14px] text-gv2-text-primary" value={worker.modelId} onchange={(e) => (worker.modelId = e.currentTarget.value)}>
									{#each worker.providerModels as mid}
										<option value={mid}>{mid}</option>
									{/each}
								</select>
							</div>
						</div>
					{/if}
				{:else}
					<div class="mt-3 flex flex-col gap-2 rounded-xl border border-gv2-border/30 bg-gv2-bg-primary/50 p-3 text-[13px]">
						<div class="flex justify-between"><span class="text-gv2-text-muted">Worker ID</span><code class="text-[#1185FE] text-[12px]">{worker.workerStats.workerId ?? '...'}</code></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Type</span><code class="text-[12px] text-gv2-text-primary">{worker.providerMode}</code></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Model</span><code class="text-[12px] text-gv2-text-primary">{worker.modelId.split('/').pop()}</code></div>
						<div class="flex justify-between">
							<span class="text-gv2-text-muted">Context Window</span>
							<span class="text-gv2-text-primary tabular-nums">
								{worker.isFullMLCMode ? `${worker.maxContextTokens.toLocaleString()} tokens` : 'N/A'}
							</span>
						</div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Jobs</span><span class="font-semibold text-[#58CC02]">{worker.workerStats.jobsComplete}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Failed</span><span class="font-semibold text-red-400">{worker.workerStats.jobsFailed}</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Avg Latency</span><span class="text-gv2-text-primary">{worker.workerStats.avgLatencyMs.toFixed(1)} ms</span></div>
						<div class="flex justify-between"><span class="text-gv2-text-muted">Earned</span><span class="font-semibold text-[#58CC02]">{worker.workerStats.totalEarned.toFixed(6)} {worker.isFullMLCMode ? 'TOK' : 'CC'}</span></div>
					</div>
					<button class="mt-3 min-h-[40px] w-full rounded-full border border-red-500/30 text-[13px] font-semibold text-red-400 touch-manipulation active:bg-red-500/10" onclick={() => worker.leaveNetwork()}>Leave Network</button>
				{/if}
			</div>

			<!-- ── Market Stats ── -->
			<div class="grid grid-cols-2 gap-3">
				{#each marketStats as item}
					<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-3">
						<p class="text-[11px] uppercase text-gv2-text-muted">{item.label}</p>
						<p class="text-[20px] font-bold tabular-nums text-gv2-text-primary">{item.value}</p>
					</div>
				{/each}
			</div>

			<!-- ── HC Jobs (hc.etzhayyim.com) ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Available Jobs</h2>
					<a href="https://hc.etzhayyim.com" target="_blank" rel="noopener noreferrer" class="text-[12px] font-semibold text-[#1185FE] no-underline active:opacity-60">View all</a>
				</div>
				<p class="mt-1 text-[13px] text-gv2-text-muted">Complete tasks on hc.etzhayyim.com to earn USDC/USDT + yoro credits.</p>

				{#if hcLoading}
					<div class="mt-3 flex flex-col gap-2">
						{#each { length: 3 } as _}
							<div class="flex items-center gap-3 rounded-xl border border-gv2-border/20 bg-gv2-bg-primary/50 p-3">
								<div class="h-9 w-9 animate-pulse rounded-xl bg-gv2-border/30"></div>
								<div class="flex-1 space-y-1.5">
									<div class="h-3.5 w-3/5 animate-pulse rounded bg-gv2-border/30"></div>
									<div class="h-3 w-4/5 animate-pulse rounded bg-gv2-border/20"></div>
								</div>
							</div>
						{/each}
					</div>
				{:else if hcJobs.length === 0}
					<div class="mt-3 rounded-xl border border-gv2-border/20 bg-gv2-bg-primary/50 p-4 text-center">
						<p class="text-[13px] text-gv2-text-muted">No jobs available right now</p>
						<a href="https://hc.etzhayyim.com" target="_blank" rel="noopener noreferrer" class="mt-2 inline-block text-[13px] font-semibold text-[#1185FE] no-underline active:opacity-60">Check hc.etzhayyim.com for updates</a>
					</div>
				{:else}
					<div class="mt-3 flex flex-col gap-2">
						{#each hcJobs as job}
							<a
								href="https://hc.etzhayyim.com/task/{job.id}"
								target="_blank"
								rel="noopener noreferrer"
								class="flex items-center gap-3 rounded-xl border border-gv2-border/20 bg-gv2-bg-primary/50 p-3 no-underline touch-manipulation active:bg-gv2-bg-hover"
							>
								<div class="flex h-9 w-9 items-center justify-center rounded-xl {job.category === 'translation' ? 'bg-purple-500/15 text-purple-400' : job.category === 'code-review' ? 'bg-amber-500/15 text-amber-400' : job.category === 'content-moderation' ? 'bg-red-500/15 text-red-400' : 'bg-[#1185FE]/15 text-[#1185FE]'} text-[11px] font-bold">
									{#if job.category === 'translation'}翻訳{:else if job.category === 'code-review'}CR{:else if job.category === 'content-moderation'}MOD{:else}HIT{/if}
								</div>
								<div class="min-w-0 flex-1">
									<p class="truncate text-[14px] font-medium text-gv2-text-primary">{job.title}</p>
									<div class="flex items-center gap-2 text-[12px] text-gv2-text-muted">
										<span>{job.difficulty ?? 'easy'}</span>
										<span class="text-gv2-border">·</span>
										<span class="font-semibold text-[#58CC02]">+¥{job.rewardCredits}</span>
										{#if job.rewardUsd}
											<span class="text-gv2-border">·</span>
											<span class="font-semibold text-gv2-text-primary">${job.rewardUsd}</span>
										{/if}
									</div>
								</div>
								<svg class="h-4 w-4 flex-shrink-0 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><path d="M9 18l6-6-6-6" /></svg>
							</a>
						{/each}
					</div>
				{/if}

				<!-- Credit rates -->
				<div class="mt-3 grid grid-cols-2 gap-2 text-[12px]">
					<div class="rounded-lg bg-gv2-bg-primary/50 px-3 py-2"><span class="text-gv2-text-muted">翻訳</span> <span class="float-right font-bold text-[#58CC02]">+¥3</span></div>
					<div class="rounded-lg bg-gv2-bg-primary/50 px-3 py-2"><span class="text-gv2-text-muted">コードレビュー</span> <span class="float-right font-bold text-[#58CC02]">+¥5</span></div>
					<div class="rounded-lg bg-gv2-bg-primary/50 px-3 py-2"><span class="text-gv2-text-muted">マイクロタスク</span> <span class="float-right font-bold text-[#58CC02]">+¥2</span></div>
					<div class="rounded-lg bg-gv2-bg-primary/50 px-3 py-2"><span class="text-gv2-text-muted">モデレーション</span> <span class="float-right font-bold text-[#58CC02]">+¥1</span></div>
				</div>
			</div>

			<!-- ── Agent Activity (chat-style feed) ── -->
			<div class="rounded-2xl border border-gv2-border/40 bg-gradient-to-br from-pink-500/5 to-blue-500/5 p-4">
				<div class="flex items-center justify-between gap-2 mb-3">
					<h2 class="text-[15px] font-bold text-gv2-text-primary">Agent Activity</h2>
					<button
						class="text-[12px] text-gv2-accent px-2 py-0.5 rounded-full border border-gv2-accent/30"
						onclick={() => activity.refresh()}
					>Refresh</button>
				</div>

				{#if activity.loading && activity.entries.length === 0}
					<div class="flex items-center gap-2 text-[13px] text-gv2-text-muted py-4">
						<div class="w-4 h-4 border-2 border-gv2-accent/40 border-t-gv2-accent rounded-full animate-spin"></div>
						Loading activity...
					</div>
				{:else if activity.entries.length === 0}
					<p class="text-[13px] text-gv2-text-muted py-4">No agent activity yet. Start evolution tasks above.</p>
				{:else}
					<div class="space-y-2 max-h-[400px] overflow-y-auto">
						{#each activity.entries as entry (entry.id)}
							<div class="flex gap-2 items-start">
								<img
									src={entry.actorAvatar}
									alt={entry.actorName}
									class="w-8 h-8 rounded-full bg-gv2-bg-secondary shrink-0"
								/>
								<div class="flex-1 min-w-0">
									<div class="flex items-baseline gap-1.5">
										<span class="text-[13px] font-semibold text-gv2-text-primary truncate">{entry.actorName}</span>
										<span class="text-[11px] text-gv2-text-muted shrink-0">{new Date(entry.timestamp).toLocaleTimeString()}</span>
									</div>
									<div class="rounded-xl bg-gv2-bg-secondary/60 px-3 py-1.5 mt-0.5">
										<p class="text-[13px] text-gv2-text-primary">{entry.summary}</p>
										{#if entry.detail}
											<p class="text-[12px] text-gv2-text-muted mt-0.5 line-clamp-2">{entry.detail}</p>
										{/if}
									</div>
									<span class="text-[11px] text-gv2-text-muted mt-0.5 inline-block px-1.5 py-0.5 rounded bg-gv2-bg-secondary/40">{entry.type}</span>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- ── Inference Log (chat-style real-time processing feed) ── -->
			{#if evo.inferenceLog.length > 0}
				<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-card p-4">
					<div class="flex items-center justify-between gap-2 mb-3">
						<h2 class="text-[15px] font-bold text-gv2-text-primary">Inference Log</h2>
						<span class="text-[12px] text-gv2-text-muted tabular-nums">{evo.inferenceLog.length} entries</span>
					</div>

					<div class="flex flex-col gap-1.5 max-h-[500px] overflow-y-auto scrollbar-none">
						{#each evo.inferenceLog as entry (entry.id)}
							{@const meta = TASK_META[entry.taskType]}
							<div class="flex gap-2 items-start rounded-lg bg-gv2-bg-primary/30 px-3 py-2">
								<!-- Status indicator -->
								<div class="flex-shrink-0 mt-0.5">
									{#if entry.status === 'inferring'}
										<span class="relative flex h-2.5 w-2.5">
											<span class="absolute inline-flex h-full w-full animate-ping rounded-full opacity-75" style="background: {meta.color}"></span>
											<span class="relative inline-flex h-2.5 w-2.5 rounded-full" style="background: {meta.color}"></span>
										</span>
									{:else if entry.status === 'persisting'}
										<span class="flex h-2.5 w-2.5 animate-pulse rounded-full bg-amber-400"></span>
									{:else if entry.status === 'done'}
										<span class="flex h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
									{:else if entry.status === 'failed'}
										<span class="flex h-2.5 w-2.5 rounded-full bg-red-500"></span>
									{:else}
										<span class="flex h-2.5 w-2.5 rounded-full bg-gv2-text-muted/30"></span>
									{/if}
								</div>

								<!-- Content -->
								<div class="min-w-0 flex-1">
									<div class="flex items-baseline gap-1.5">
										<span class="text-[12px] font-semibold truncate max-w-[140px]" style="color: {meta.color}">{entry.actorName}</span>
										<span class="rounded px-1 py-0.5 text-[9px] font-medium" style="background: {meta.color}20; color: {meta.color}">{meta.labelJa}</span>
										<span class="ml-auto flex-shrink-0 text-[10px] text-gv2-text-muted tabular-nums">{new Date(entry.timestamp).toLocaleTimeString('ja-JP', { hour: '2-digit', minute: '2-digit', second: '2-digit' })}</span>
									</div>
									<p class="text-[12px] text-gv2-text-secondary mt-0.5 leading-snug">{entry.summary}</p>
									{#if entry.status === 'done'}
										<div class="flex items-center gap-2 mt-1 text-[10px] flex-wrap">
											{#if entry.model}
												<span class="rounded bg-gv2-bg-secondary/60 px-1 py-0.5 font-medium text-gv2-text-secondary">{entry.model}</span>
											{/if}
											{#if entry.inputTokens > 0}
												<span class="text-gv2-text-muted tabular-nums">{entry.inputTokens} in</span>
											{/if}
											{#if entry.outputTokens > 0}
												<span class="text-gv2-text-muted tabular-nums">{entry.outputTokens} out</span>
											{/if}
											{#if entry.tokensUsed > 0}
												<span class="text-gv2-text-muted tabular-nums">{entry.tokensUsed} total</span>
											{/if}
											{#if entry.creditsEarned > 0}
												<span class="font-semibold text-emerald-400 tabular-nums">+{entry.creditsEarned.toFixed(1)} cr</span>
											{/if}
										</div>
										{#if entry.promptText || entry.responseText}
											<details class="mt-1.5">
												<summary class="text-[10px] text-gv2-text-muted cursor-pointer select-none hover:text-gv2-text-secondary">Inference details</summary>
												<div class="mt-1 space-y-1.5">
													{#if entry.promptText}
														<div class="rounded-md bg-gv2-bg-primary/40 px-2 py-1.5">
															<p class="text-[9px] font-semibold uppercase text-gv2-text-muted mb-0.5">Prompt</p>
															<p class="text-[11px] text-gv2-text-secondary whitespace-pre-wrap break-words leading-snug max-h-[120px] overflow-y-auto scrollbar-none">{entry.promptText}</p>
														</div>
													{/if}
													{#if entry.responseText}
														<div class="rounded-md bg-gv2-bg-primary/40 px-2 py-1.5">
															<p class="text-[9px] font-semibold uppercase text-gv2-text-muted mb-0.5">Response</p>
															<p class="text-[11px] text-gv2-text-secondary whitespace-pre-wrap break-words leading-snug max-h-[200px] overflow-y-auto scrollbar-none">{entry.responseText}</p>
														</div>
													{/if}
												</div>
											</details>
										{/if}
									{/if}
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Bottom padding for tab bar -->
			<div class="h-4"></div>
		</div>
	</div>
</div>
