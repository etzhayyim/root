<script lang="ts">
	import { onMount } from 'svelte';
	import { Badge, Button, Card, Input, Toggle } from '@etzhayyim/design-system';
	import { useProviderWorker } from '../provider/worker-state.svelte.js';
	import { useProviderMarket } from '../provider/market-state.svelte.js';
	import { useBrowserInference } from '../provider/browser-inference-state.svelte.js';
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
	} from '../wallet/web3.js';

	const worker = useProviderWorker();
	const mkt = useProviderMarket();
	const inference = useBrowserInference();

	const NUM_SETS = 32;
	const EXPERTS_PER_SET = 4;
	const EXPERT_SIZE_MB = 33;
	let showAdvanced = $state(false);
	let joining = $state(false);
	let joiningInference = $state(false);

	const numberValue = (event: Event): number =>
		Number((event.currentTarget as HTMLInputElement).value);

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
		const tier = inference.stats.gpuTier;
		switch (tier) {
			case 'g4': return 'g4 (Desktop, f16, 1GB+)';
			case 'g3': return 'g3 (f16, 256MB+)';
			case 'g2': return 'g2 (f16)';
			case 'g1': return 'g1 (WebGPU)';
			case 'g0': return 'g0 (CPU only)';
			default: return tier;
		}
	});

	const stats = $derived([
		{ label: 'Workers', value: String(mkt.market?.totalWorkers ?? '-') },
		{ label: 'Available', value: String(mkt.market?.availableWorkers ?? '-') },
		{ label: 'Jobs Served', value: mkt.market?.totalJobsServed?.toLocaleString() ?? '-' },
		{ label: 'Avg Price/CC', value: mkt.market?.avgPricePerCc?.toFixed(4) ?? '-' },
	]);

	onMount(() => {
		mkt.startPolling();
		return () => mkt.stopPolling();
	});
</script>

<div class="flex flex-col gap-3 p-3">
	<!-- Wallet Section -->
	<Card aspect="auto" class="!bg-etzhayyim-card !rounded-2xl !border !border-etzhayyim-border">
		{#snippet children()}
			<div class="flex flex-col gap-3 p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[16px] font-bold text-etzhayyim-text">Wallet</h2>
					{#if $walletState.connected}
						<Badge value={'Connected'} variant="success" />
					{:else}
						<Badge value="disconnected" variant="default" />
					{/if}
				</div>

				{#if $walletState.connected && $walletState.address}
					<div class="flex flex-col gap-2 rounded-xl border border-etzhayyim-border bg-etzhayyim-input p-3 text-[13px]">
						<div class="flex justify-between"><span class="text-etzhayyim-muted">Address</span><code class="text-etzhayyim-accent text-[12px]">{shortenAddress($walletState.address)}</code></div>
						<div class="flex justify-between"><span class="text-etzhayyim-muted">ETH</span><span class="font-semibold text-etzhayyim-text">{$ethBalanceFormatted}</span></div>
						{#each $tokenBalances as token}
							<div class="flex justify-between">
								<span class="text-etzhayyim-muted">{token.symbol}</span>
								<span class="font-semibold {token.symbol === 'GCC' ? 'text-emerald-500' : 'text-etzhayyim-text'}">{Number(token.balance).toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
							</div>
						{/each}
					</div>
					<div class="flex gap-2">
						<Button variant="outline" size="sm" onclick={() => refreshBalances()}>Refresh</Button>
						<Button variant="outline" size="sm" class="!text-red-500 !border-red-500/30" onclick={disconnectWallet}>Disconnect</Button>
					</div>
				{:else}
					<p class="text-[13px] text-etzhayyim-secondary">Connect MetaMask to view your assets and GCC earnings.</p>
					{#if isWalletAvailable()}
						<Button variant="solid-fill" size="sm" disabled={$walletLoading} onclick={connectWallet}>
							{$walletLoading ? 'Connecting...' : 'Connect MetaMask'}
						</Button>
					{:else}
						<a href="https://metamask.io/download/" target="_blank" rel="noopener noreferrer" class="text-[13px] text-etzhayyim-accent active:opacity-60">Install MetaMask</a>
					{/if}
				{/if}

				{#if $walletError}
					<p class="text-[12px] text-red-500">{$walletError}</p>
				{/if}
			</div>
		{/snippet}
	</Card>

	<!-- Browser Inference Section (murakumo.etzhayyim.com) -->
	<Card aspect="auto" class="!bg-etzhayyim-card !rounded-2xl !border !border-etzhayyim-border">
		{#snippet children()}
			<div class="flex flex-col gap-3 p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[16px] font-bold text-etzhayyim-text">Browser Inference</h2>
					<Badge value={inference.stats.state} variant={inferenceVariant} />
				</div>
				<p class="text-[13px] text-etzhayyim-secondary">Contribute your browser's compute to murakumo.etzhayyim.com distributed inference network.</p>

				{#if !inference.isJoined}
					<div class="flex flex-col gap-3">
						<div class="rounded-xl border border-etzhayyim-border bg-etzhayyim-input p-3">
							<p class="text-[12px] text-etzhayyim-secondary leading-relaxed">Your browser's GPU and CPU will be probed for capabilities. Tasks are pushed from the gateway and executed off the main thread.</p>
						</div>
						<Button variant="solid-fill" size="sm" disabled={joiningInference} onclick={async () => { joiningInference = true; await inference.join(); joiningInference = false; }}>
							{joiningInference ? 'Probing...' : 'Join Inference Network'}
						</Button>
					</div>
				{:else}
					<div class="flex flex-col gap-3">
						<!-- Capability Info -->
						<div class="flex flex-col gap-2 rounded-xl border border-etzhayyim-border bg-etzhayyim-input p-3 text-[13px]">
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Session</span><code class="text-etzhayyim-accent text-[12px]">{inference.stats.sessionId ?? '...'}</code></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">GPU Tier</span><span class="font-semibold text-etzhayyim-text">{gpuTierLabel}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">GPU</span><span class="text-etzhayyim-text">{inference.stats.gpuAdapter}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Memory</span><span class="text-etzhayyim-text">{inference.stats.memClass}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Power</span><span class="text-etzhayyim-text">{inference.stats.powerClass}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Cores</span><span class="text-etzhayyim-text">{inference.stats.cores}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Transport</span><span class="text-etzhayyim-text">{inference.stats.transportType}</span></div>
						</div>

						<!-- Task Stats -->
						<div class="flex flex-col gap-2 rounded-xl border border-etzhayyim-border bg-etzhayyim-input p-3 text-[13px]">
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Jobs Done</span><span class="font-semibold text-emerald-600">{inference.stats.jobsDone}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Failed</span><span class="font-semibold text-red-500">{inference.stats.jobsFailed}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">GPU Time</span><span>{(inference.stats.totalGpuTimeMs / 1000).toFixed(1)}s</span></div>
							{#if inference.stats.lastHeartbeatAck}
								<div class="flex justify-between"><span class="text-etzhayyim-muted">Last Heartbeat</span><span class="text-[12px] text-etzhayyim-muted">{inference.stats.lastHeartbeatAck}</span></div>
							{/if}
						</div>

						<!-- Current Task Progress -->
						{#if inference.isExecuting && inference.stats.currentProgress}
							<div class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
								<div class="flex items-center justify-between text-[13px]">
									<span class="font-semibold text-amber-400">Executing</span>
									<span class="text-[12px] text-amber-300">{inference.stats.currentProgress.stage}</span>
								</div>
								<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-etzhayyim-border">
									<div
										class="h-full rounded-full bg-amber-500 transition-all duration-300"
										style="width: {inference.stats.currentProgress.total > 0 ? Math.round(inference.stats.currentProgress.done / inference.stats.currentProgress.total * 100) : 0}%"
									></div>
								</div>
								<p class="mt-1 text-[11px] text-amber-300/70">
									{inference.stats.currentProgress.done}/{inference.stats.currentProgress.total}
									{#if inference.stats.currentProgress.detail}
										— {inference.stats.currentProgress.detail}
									{/if}
								</p>
							</div>
						{:else if inference.isExecuting}
							<div class="rounded-xl border border-amber-500/30 bg-amber-500/10 p-3">
								<p class="text-[13px] font-semibold text-amber-400">Executing task...</p>
							</div>
						{/if}

						<Button variant="outline" size="sm" class="!text-red-500 !border-red-500/30" onclick={() => inference.leave()}>Leave Network</Button>
					</div>
				{/if}
			</div>
		{/snippet}
	</Card>

	<!-- Provider Section -->
	<Card aspect="auto" class="!bg-etzhayyim-card !rounded-2xl !border !border-etzhayyim-border">
		{#snippet children()}
			<div class="flex flex-col gap-3 p-4">
				<div class="flex items-center justify-between gap-2">
					<h2 class="text-[16px] font-bold text-etzhayyim-text">Expert Provider</h2>
					<Badge value={worker.workerStats.state} variant={stateVariant} />
				</div>
				<p class="text-[13px] text-etzhayyim-secondary">Serve distributed MoE expert inference jobs on web4.etzhayyim.com. Earn GCC.</p>

				{#if !worker.isJoined}
					<div class="flex flex-col gap-3">
						<div class="rounded-xl border border-etzhayyim-border bg-etzhayyim-input p-3">
							<p class="text-[12px] text-etzhayyim-secondary leading-relaxed">The scheduler will automatically assign the optimal expert set based on current network demand.</p>
						</div>
						<Button variant="solid-fill" size="sm" disabled={joining} onclick={async () => { joining = true; worker.manualExpert = false; await worker.joinNetwork(); joining = false; }}>
							{joining ? 'Connecting...' : 'Join Network'}
						</Button>

						<button type="button" class="text-[12px] text-etzhayyim-muted active:opacity-60 touch-manipulation text-left" onclick={() => (showAdvanced = !showAdvanced)}>
							{showAdvanced ? 'Hide' : 'Show'} advanced options
						</button>

						{#if showAdvanced}
							<div class="flex flex-col gap-3 border-t border-etzhayyim-border pt-3">
								<div class="flex flex-col gap-1">
									<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-mode">Provider Type</label>
									<select id="prov-mode" class="min-h-[44px] w-full rounded-lg border border-etzhayyim-border bg-etzhayyim-input px-3 py-2 text-[14px] text-etzhayyim-text" value={worker.providerMode} onchange={(e) => (worker.providerMode = e.currentTarget.value)}>
										<option value="expert_ffn">expert_ffn</option>
										<option value="full_mlc">full_mlc</option>
										<option value="lima">lima</option>
									</select>
								</div>
								<div class="flex flex-col gap-1">
									<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-model">Model</label>
									<select id="prov-model" class="min-h-[44px] w-full rounded-lg border border-etzhayyim-border bg-etzhayyim-input px-3 py-2 text-[14px] text-etzhayyim-text" value={worker.modelId} onchange={(e) => (worker.modelId = e.currentTarget.value)}>
										{#each worker.providerModels as mid}
											<option value={mid}>{mid}</option>
										{/each}
									</select>
								</div>
								{#if !worker.isFullMLCMode}
									<div class="flex items-center justify-between">
										<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-manual">Manual Expert Selection</label>
										<Toggle checked={worker.manualExpert} onchange={(checked: boolean) => (worker.manualExpert = checked)} />
									</div>
									{#if worker.manualExpert}
										<div class="flex flex-col gap-1">
											<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-expert">Expert Set (0-{NUM_SETS - 1})</label>
											<Input id="prov-expert" type="number" value={worker.expertId} onchange={(event: Event) => (worker.expertId = numberValue(event))} min="0" max={NUM_SETS - 1} />
											<p class="text-[11px] text-etzhayyim-muted">{EXPERTS_PER_SET} experts/set, ~{EXPERT_SIZE_MB * EXPERTS_PER_SET}MB</p>
										</div>
									{/if}
									<div class="flex flex-col gap-1">
										<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-price">Price per CC</label>
										<Input id="prov-price" type="number" value={worker.pricePerCC} onchange={(event: Event) => (worker.pricePerCC = numberValue(event))} min="0" max="1" step="0.0001" />
									</div>
								{:else}
									<div class="flex flex-col gap-1">
										<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-pti">Price / Input Token</label>
										<Input id="prov-pti" type="number" value={worker.pricePerTokenIn} onchange={(event: Event) => (worker.pricePerTokenIn = numberValue(event))} min="0" max="1" step="0.000001" />
									</div>
									<div class="flex flex-col gap-1">
										<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-pto">Price / Output Token</label>
										<Input id="prov-pto" type="number" value={worker.pricePerTokenOut} onchange={(event: Event) => (worker.pricePerTokenOut = numberValue(event))} min="0" max="1" step="0.000001" />
									</div>
									<div class="flex flex-col gap-1">
										<label class="text-[11px] font-semibold uppercase text-etzhayyim-muted" for="prov-ctx">Max Context Tokens</label>
										<Input id="prov-ctx" type="number" value={worker.maxContextTokens} onchange={(event: Event) => (worker.maxContextTokens = numberValue(event))} min="256" max="32768" step="256" />
									</div>
								{/if}
							</div>
						{/if}
					</div>
				{:else}
					<div class="flex flex-col gap-3">
						<div class="flex flex-col gap-2 rounded-xl border border-etzhayyim-border bg-etzhayyim-input p-3 text-[13px]">
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Worker ID</span><code class="text-etzhayyim-accent text-[12px]">{worker.workerStats.workerId ?? '...'}</code></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Type</span><code class="text-etzhayyim-accent text-[12px]">{worker.providerMode}</code></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Model</span><code class="text-etzhayyim-accent text-[12px]">{worker.modelId.split('/').pop()}</code></div>
							{#if !worker.isFullMLCMode}
								<div class="flex justify-between"><span class="text-etzhayyim-muted">Expert Set</span><code class="text-etzhayyim-accent text-[12px]">{worker.expertId}</code></div>
							{/if}
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Jobs</span><span class="font-semibold text-emerald-600">{worker.workerStats.jobsComplete}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Failed</span><span class="font-semibold text-red-500">{worker.workerStats.jobsFailed}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Avg Latency</span><span>{worker.workerStats.avgLatencyMs.toFixed(1)} ms</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Earned</span><span class="font-semibold text-emerald-600">{worker.workerStats.totalEarned.toFixed(6)} {worker.isFullMLCMode ? 'TOK' : 'CC'}</span></div>
							<div class="flex justify-between"><span class="text-etzhayyim-muted">Connected</span><span class="text-[12px]">{worker.workerStats.connectedAt?.toLocaleTimeString() ?? '-'}</span></div>
						</div>
						<Button variant="outline" size="sm" class="!text-red-500 !border-red-500/30" onclick={() => worker.leaveNetwork()}>Leave Network</Button>
					</div>
				{/if}
			</div>
		{/snippet}
	</Card>

	<!-- Market Stats -->
	<div class="grid grid-cols-2 gap-2">
		{#each stats as item}
			<Card aspect="auto" class="!bg-etzhayyim-card !rounded-2xl !border !border-etzhayyim-border">
				{#snippet children()}
					<div class="flex flex-col gap-1 p-3">
						<p class="text-[11px] uppercase text-etzhayyim-muted">{item.label}</p>
						<p class="text-[18px] font-semibold text-etzhayyim-text">{item.value}</p>
					</div>
				{/snippet}
			</Card>
		{/each}
	</div>

	<!-- Quick Links -->
	<Card aspect="auto" class="!bg-etzhayyim-card !rounded-2xl !border !border-etzhayyim-border">
		{#snippet children()}
			<div class="flex flex-col gap-2 p-4">
				<h3 class="text-[13px] font-bold uppercase text-etzhayyim-muted">Quick Links</h3>
				<a href="https://web4.etzhayyim.com/provider" class="flex items-center gap-3 rounded-xl p-3 active:opacity-80" target="_blank" rel="noopener noreferrer">
					<div class="flex h-9 w-9 items-center justify-center rounded-xl bg-etzhayyim-hover text-[13px] font-semibold text-etzhayyim-accent">W4</div>
					<div class="min-w-0">
						<p class="text-[13px] font-semibold text-etzhayyim-text">Web4 Provider Dashboard</p>
						<p class="text-[12px] text-etzhayyim-secondary">Full provider workspace on web4.etzhayyim.com</p>
					</div>
				</a>
				<a href="https://murakumo.etzhayyim.com" class="flex items-center gap-3 rounded-xl p-3 active:opacity-80" target="_blank" rel="noopener noreferrer">
					<div class="flex h-9 w-9 items-center justify-center rounded-xl bg-etzhayyim-hover text-[13px] font-semibold text-etzhayyim-accent">MK</div>
					<div class="min-w-0">
						<p class="text-[13px] font-semibold text-etzhayyim-text">Murakumo Compute Network</p>
						<p class="text-[12px] text-etzhayyim-secondary">Distributed inference marketplace</p>
					</div>
				</a>
			</div>
		{/snippet}
	</Card>
</div>
