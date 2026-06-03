<script lang="ts">
	import { cn } from '@etzhayyim/design-system';
	import { resolveConsent } from '$lib/atproto-agent';
	import type { ConsentGrant } from '$lib/atproto-agent';
	import { fade } from 'svelte/transition';

	interface ConsentRequestPayload {
		id: string;
		granteeDid: string;
		scope: string;
		resourceIds: string[];
		disclosedClaims: string[];
		purpose: string;
		maxSensitivity: string;
	}

	interface Props {
		request: ConsentRequestPayload;
		appName: string;
		appIcon?: string;
		onresolved: (grant: ConsentGrant | null) => void;
	}

	let { request, appName, appIcon = '', onresolved }: Props = $props();

	let busy = $state(false);
	let selectedClaims = $state<Set<string>>(new Set());

	$effect(() => {
		selectedClaims = new Set(request.disclosedClaims);
	});

	function toggleClaim(claim: string) {
		const next = new Set(selectedClaims);
		if (next.has(claim)) {
			next.delete(claim);
		} else {
			next.add(claim);
		}
		selectedClaims = next;
	}

	const scopeLabel: Record<string, string> = {
		field: 'Specific fields',
		record: 'Full record',
		collection: 'Collection',
		capability: 'Capability result',
	};

	const sensitivityLabel: Record<string, string> = {
		public: 'Public',
		internal: 'Internal',
		confidential: 'Confidential',
		restricted: 'Restricted',
	};

	const sensitivityColor: Record<string, string> = {
		public: 'text-green-400',
		internal: 'text-blue-400',
		confidential: 'text-yellow-400',
		restricted: 'text-red-400',
	};

	async function handleApprove() {
		busy = true;
		try {
			const grant = await resolveConsent(request.id, true);
			onresolved(grant);
		} catch (e) {
			console.warn('consent approve failed', e);
			onresolved(null);
		} finally {
			busy = false;
		}
	}

	async function handleDeny() {
		busy = true;
		try {
			await resolveConsent(request.id, false);
			onresolved(null);
		} catch (e) {
			console.warn('consent deny failed', e);
		} finally {
			busy = false;
		}
	}
</script>

<div
	class="mx-3 my-2 rounded-2xl border border-purple-500/30 bg-purple-500/5 overflow-hidden"
	transition:fade={{ duration: 150 }}
>
	<!-- Header -->
	<div class="flex items-center gap-3 px-4 pt-4 pb-3">
		{#if appIcon}
			<span class="flex items-center justify-center w-10 h-10 rounded-xl bg-purple-500/10 text-xl shrink-0">{appIcon}</span>
		{:else}
			<div class="flex items-center justify-center w-10 h-10 rounded-xl bg-purple-500/10 shrink-0">
				<svg class="w-5 h-5 text-purple-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
				</svg>
			</div>
		{/if}
		<div class="min-w-0 flex-1">
			<p class="text-[14px] font-bold text-gv2-text-primary truncate">{appName}</p>
			<p class="text-[12px] text-purple-400">requests access to your data</p>
		</div>
	</div>

	<!-- Purpose -->
	<div class="px-4 pb-3">
		<p class="text-[13px] text-gv2-text-muted leading-relaxed">{request.purpose}</p>
	</div>

	<!-- Scope & Sensitivity -->
	<div class="flex items-center gap-3 px-4 pb-3">
		<span class="inline-flex items-center gap-1 rounded-full bg-purple-500/10 px-2.5 py-1 text-[11px] font-medium text-purple-400">
			{scopeLabel[request.scope] ?? request.scope}
		</span>
		<span class={cn(
			'inline-flex items-center gap-1 rounded-full bg-gv2-bg-hover px-2.5 py-1 text-[11px] font-medium',
			sensitivityColor[request.maxSensitivity] ?? 'text-gv2-text-muted'
		)}>
			{sensitivityLabel[request.maxSensitivity] ?? request.maxSensitivity}
		</span>
	</div>

	<!-- Claims (selective disclosure) -->
	{#if request.disclosedClaims.length > 0}
		<div class="px-4 pb-3">
			<p class="text-[11px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-2">Data to share</p>
			<div class="flex flex-col gap-1">
				{#each request.disclosedClaims as claim}
					<button
						class={cn(
							'flex items-center gap-2.5 w-full px-3 py-2 rounded-xl text-left transition-colors touch-manipulation',
							selectedClaims.has(claim)
								? 'bg-purple-500/10 border border-purple-500/30'
								: 'bg-gv2-bg-hover/50 border border-transparent'
						)}
						onclick={() => toggleClaim(claim)}
					>
						<div class={cn(
							'flex items-center justify-center w-4 h-4 rounded border-2 transition-colors shrink-0',
							selectedClaims.has(claim)
								? 'bg-purple-500 border-purple-500'
								: 'bg-transparent border-gv2-text-muted/30'
						)}>
							{#if selectedClaims.has(claim)}
								<svg class="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
									<polyline points="20 6 9 17 4 12" />
								</svg>
							{/if}
						</div>
						<span class="text-[13px] text-gv2-text-primary">{claim}</span>
					</button>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Resource IDs -->
	{#if request.resourceIds.length > 0 && request.resourceIds.length <= 5}
		<div class="px-4 pb-3">
			<p class="text-[11px] font-semibold text-gv2-text-muted uppercase tracking-wider mb-1.5">Resources</p>
			<div class="flex flex-wrap gap-1">
				{#each request.resourceIds as rid}
					<span class="inline-block rounded bg-gv2-bg-hover px-2 py-0.5 text-[11px] text-gv2-text-muted font-mono truncate max-w-[200px]">{rid}</span>
				{/each}
			</div>
		</div>
	{/if}

	<!-- Actions -->
	<div class="flex gap-2.5 px-4 pb-4">
		<button
			class="flex-1 py-2.5 rounded-xl border border-gv2-border text-[14px] font-medium text-gv2-text-muted active:bg-gv2-bg-hover transition-colors touch-manipulation min-h-[44px]"
			onclick={handleDeny}
			disabled={busy}
		>
			Deny
		</button>
		<button
			class={cn(
				'flex-1 py-2.5 rounded-xl text-[14px] font-medium text-white transition-colors touch-manipulation min-h-[44px]',
				busy ? 'bg-purple-500/60' : 'bg-purple-500 active:bg-purple-600'
			)}
			onclick={handleApprove}
			disabled={busy}
		>
			{busy ? 'Processing...' : 'Allow'}
		</button>
	</div>
</div>
