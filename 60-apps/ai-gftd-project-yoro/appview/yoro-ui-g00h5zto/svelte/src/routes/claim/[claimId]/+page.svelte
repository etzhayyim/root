<!--
  /claim/[claimId] — staked-claim viewer + challenge action.

  ADR-2604261717 worker pipeline. Calls
  `https://authz.etzhayyim.com/xrpc/com.etzhayyim.claim.getStakedAttestation?claimId=...`
  to read the on-chain Claim + (optional) Challenge struct from
  ClaimStakeEscrow. When state=pending and the window is open, surfaces
  a counter-bond + rebuttal form that POSTs to
  `com.etzhayyim.claim.challengeStakedAttestation`.

  Discovery + action path for non-claimant users (anyone with the claimId
  can audit + challenge). The staker themselves receive the claimId in
  the postStakedAttestation response and get this page as a deep-link.
-->
<script lang="ts">
	import { page } from '$app/stores';
	import { onMount } from 'svelte';
	import { getSessionToken } from '$lib/auth/passkey';
	import { isSignedIn } from '$lib/auth/stores';

	type ClaimState = 'none' | 'pending' | 'challenged' | 'upheld' | 'slashed' | 'refunded';

	interface ClaimSnapshot {
		claimId: string;
		state: ClaimState;
		didHash: string;
		atRecordCid: string;
		bond: string;
		postedAt: number;
		challengePeriodSec: number;
		claimant: string;
		challenger?: string;
		challengerDidHash?: string;
		counterBond?: string;
		challengePostedAt?: number;
		chainId: number;
		escrowAddr: string;
	}

	const AUTHZ_BASE = 'https://authz.etzhayyim.com';
	const STAKE_OPTIONS = [1, 5, 10, 25] as const;

	let claimId = $derived($page.params.claimId);
	let snap = $state<ClaimSnapshot | null>(null);
	let loading = $state(true);
	let loadError = $state('');

	let counterBondGcc = $state(1);
	let rebuttal = $state('');
	let submitting = $state(false);
	let submitError = $state('');
	let submitOk = $state('');

	function fmtGcc(weiHex: string): string {
		try {
			const wei = BigInt(weiHex);
			const whole = wei / 10n ** 18n;
			const frac = wei % 10n ** 18n;
			if (frac === 0n) return whole.toString();
			const fracStr = frac.toString().padStart(18, '0').replace(/0+$/, '').slice(0, 4);
			return `${whole}.${fracStr}`;
		} catch {
			return weiHex;
		}
	}

	function fmtDate(unixSec: number): string {
		if (!unixSec) return '—';
		return new Date(unixSec * 1000).toLocaleString();
	}

	let challengeDeadline = $derived.by(() => {
		if (!snap || snap.state !== 'pending') return 0;
		return snap.postedAt + snap.challengePeriodSec;
	});

	let challengeWindowOpen = $derived.by(() => {
		if (!snap || snap.state !== 'pending') return false;
		return Math.floor(Date.now() / 1000) < challengeDeadline;
	});

	let stateBadge = $derived.by(() => {
		if (!snap) return { label: '—', color: 'gray' };
		switch (snap.state) {
			case 'pending':
				return challengeWindowOpen
					? { label: 'Pending — challenge window open', color: 'amber' }
					: { label: 'Pending — window closed (claim can refund)', color: 'gray' };
			case 'challenged':
				return { label: 'Challenged — awaiting arbiter', color: 'orange' };
			case 'upheld':
				return { label: 'Upheld — claim won', color: 'emerald' };
			case 'slashed':
				return { label: 'Slashed — challenger won', color: 'red' };
			case 'refunded':
				return { label: 'Refunded — both sides repaid', color: 'gray' };
			default:
				return { label: snap.state, color: 'gray' };
		}
	});
	let stateBadgeClasses = $derived.by(() => {
		switch (stateBadge.color) {
			case 'amber':   return { icon: 'text-amber-400',   text: 'text-amber-300' };
			case 'orange':  return { icon: 'text-orange-400',  text: 'text-orange-300' };
			case 'emerald': return { icon: 'text-emerald-400', text: 'text-emerald-300' };
			case 'red':     return { icon: 'text-red-400',     text: 'text-red-300' };
			default:        return { icon: 'text-gray-400',    text: 'text-gray-300' };
		}
	});

	async function loadClaim() {
		loading = true;
		loadError = '';
		try {
			const url = `${AUTHZ_BASE}/xrpc/com.etzhayyim.claim.getStakedAttestation?claimId=${encodeURIComponent(claimId)}`;
			const resp = await fetch(url);
			if (resp.status === 404) {
				loadError = 'No claim with this id (it may not exist on-chain yet).';
				snap = null;
				return;
			}
			if (!resp.ok) {
				const body = await resp.text().catch(() => '');
				throw new Error(`HTTP ${resp.status}: ${body.slice(0, 200)}`);
			}
			snap = (await resp.json()) as ClaimSnapshot;
		} catch (e) {
			loadError = e instanceof Error ? e.message : String(e);
			snap = null;
		} finally {
			loading = false;
		}
	}

	async function submitChallenge() {
		submitError = '';
		submitOk = '';
		if (!rebuttal.trim()) { submitError = 'Rebuttal is required.'; return; }
		if (counterBondGcc < 1) { submitError = 'Counter-bond must be at least 1 GCC.'; return; }
		if (!snap || snap.state !== 'pending' || !challengeWindowOpen) {
			submitError = 'This claim is no longer challengeable.';
			return;
		}
		submitting = true;
		try {
			const token = await getSessionToken();
			if (!token) throw new Error('Sign in to file a challenge.');
			const resp = await fetch(`${AUTHZ_BASE}/xrpc/com.etzhayyim.claim.challengeStakedAttestation`, {
				method: 'POST',
				headers: { 'authorization': `Bearer ${token}`, 'content-type': 'application/json' },
				body: JSON.stringify({
					claimId,
					counterBond: counterBondGcc.toString(),
					rebuttal: rebuttal.trim(),
				}),
			});
			if (!resp.ok) {
				const body = await resp.text().catch(() => '');
				throw new Error(`HTTP ${resp.status}: ${body.slice(0, 200)}`);
			}
			const result = await resp.json();
			submitOk = `Challenge filed. tx ${result.txHash ?? ''}`;
			rebuttal = '';
			await loadClaim();
		} catch (e) {
			submitError = e instanceof Error ? e.message : String(e);
		} finally {
			submitting = false;
		}
	}

	onMount(() => { void loadClaim(); });
</script>

<svelte:head>
	<title>Staked claim {claimId.slice(0, 10)}…</title>
</svelte:head>

<div class="mx-auto max-w-2xl px-4 py-8">
	<div class="mb-6">
		<a href="/" class="text-[13px] text-[var(--gv2-text-muted,#777)] hover:text-[var(--gv2-text-primary,#fff)]">← Back to feed</a>
	</div>

	<h1 class="text-[20px] font-bold text-[var(--gv2-text-primary,#fff)] mb-1">Staked Claim</h1>
	<div class="text-[12px] font-mono text-[var(--gv2-text-muted,#777)] mb-6 break-all">{claimId}</div>

	{#if loading}
		<div class="rounded-xl border border-[var(--gv2-border,#2f2f2f)] p-6">
			<div class="h-4 w-32 bg-[var(--gv2-bg-hover,#252525)] rounded animate-pulse mb-3"></div>
			<div class="h-3 w-full bg-[var(--gv2-bg-hover,#252525)] rounded animate-pulse mb-2"></div>
			<div class="h-3 w-2/3 bg-[var(--gv2-bg-hover,#252525)] rounded animate-pulse"></div>
		</div>
	{:else if loadError}
		<div class="rounded-xl border border-red-500/30 bg-red-500/5 p-4">
			<div class="text-[14px] text-red-400">{loadError}</div>
			<button class="mt-3 text-[13px] text-[#1185FE] hover:underline" onclick={() => void loadClaim()}>Retry</button>
		</div>
	{:else if snap}
		<div class="rounded-xl border border-[var(--gv2-border,#2f2f2f)] bg-[var(--gv2-bg-card,#1f1f1f)] p-4 mb-4">
			<div class="flex items-center gap-2 mb-3">
				<svg class="h-5 w-5 {stateBadgeClasses.icon}" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2L4 6v6c0 5 4 9 8 10 4-1 8-5 8-10V6l-8-4z" /></svg>
				<span class="text-[14px] font-semibold {stateBadgeClasses.text}">{stateBadge.label}</span>
			</div>
			<dl class="grid grid-cols-[auto,1fr] gap-x-4 gap-y-2 text-[13px]">
				<dt class="text-[var(--gv2-text-muted,#777)]">Bond</dt>
				<dd class="font-mono text-[var(--gv2-text-primary,#fff)]">{fmtGcc(snap.bond)} GCC</dd>
				<dt class="text-[var(--gv2-text-muted,#777)]">Claimant</dt>
				<dd class="font-mono text-[var(--gv2-text-primary,#fff)] truncate">{snap.claimant}</dd>
				<dt class="text-[var(--gv2-text-muted,#777)]">Posted</dt>
				<dd class="text-[var(--gv2-text-primary,#fff)]">{fmtDate(snap.postedAt)}</dd>
				<dt class="text-[var(--gv2-text-muted,#777)]">Challenge window</dt>
				<dd class="text-[var(--gv2-text-primary,#fff)]">
					{Math.round(snap.challengePeriodSec / 86400)}d
					{#if snap.state === 'pending'}(closes {fmtDate(challengeDeadline)}){/if}
				</dd>
				<dt class="text-[var(--gv2-text-muted,#777)]">AT Record CID</dt>
				<dd class="font-mono text-[var(--gv2-text-primary,#fff)] truncate">{snap.atRecordCid}</dd>
				<dt class="text-[var(--gv2-text-muted,#777)]">Escrow</dt>
				<dd class="font-mono text-[var(--gv2-text-muted,#777)] truncate">{snap.escrowAddr} (chain {snap.chainId})</dd>
				{#if snap.challenger}
					<dt class="text-[var(--gv2-text-muted,#777)]">Challenger</dt>
					<dd class="font-mono text-[var(--gv2-text-primary,#fff)] truncate">{snap.challenger}</dd>
					<dt class="text-[var(--gv2-text-muted,#777)]">Counter-bond</dt>
					<dd class="font-mono text-[var(--gv2-text-primary,#fff)]">{snap.counterBond ? fmtGcc(snap.counterBond) : '—'} GCC</dd>
					<dt class="text-[var(--gv2-text-muted,#777)]">Challenged at</dt>
					<dd class="text-[var(--gv2-text-primary,#fff)]">{fmtDate(snap.challengePostedAt ?? 0)}</dd>
				{/if}
			</dl>
		</div>

		{#if snap.state === 'pending' && challengeWindowOpen}
			<div class="rounded-xl border border-orange-500/30 bg-orange-500/5 p-4 mb-4">
				<h2 class="text-[15px] font-semibold text-orange-300 mb-3">Challenge this claim</h2>
				<p class="text-[12px] text-orange-300/70 mb-3 leading-relaxed">
					Lock a counter-bond ≥ 50% of {fmtGcc(snap.bond)} GCC. An arbiter rules within 14 days.
					If you win, you receive your counter-bond + 85% of the claimant's bond.
				</p>

				<label class="block mb-3">
					<span class="text-[12px] text-[var(--gv2-text-muted,#777)] mb-1 block">Counter-bond (GCC)</span>
					<div class="flex gap-2">
						{#each STAKE_OPTIONS as option}
							<button
								type="button"
								class="flex-1 rounded-lg border px-3 py-2 text-[13px] font-semibold transition-colors {counterBondGcc === option ? 'border-orange-500 bg-orange-500/10 text-orange-300' : 'border-[var(--gv2-border,#2f2f2f)] text-[var(--gv2-text-muted,#777)] hover:border-[var(--gv2-border-hover,#3a3a3a)]'}"
								onclick={() => counterBondGcc = option}
							>{option}</button>
						{/each}
					</div>
				</label>

				<label class="block mb-3">
					<span class="text-[12px] text-[var(--gv2-text-muted,#777)] mb-1 block">Rebuttal (publicly visible)</span>
					<textarea
						bind:value={rebuttal}
						maxlength="4096"
						rows="4"
						placeholder="Why is this claim false? Cite evidence."
						class="w-full rounded-lg border border-[var(--gv2-border,#2f2f2f)] bg-[var(--gv2-bg-primary,#0a0a0a)] px-3 py-2 text-[14px] text-[var(--gv2-text-primary,#fff)] placeholder:text-[var(--gv2-text-muted,#555)] resize-none focus:outline-none focus:border-orange-500/50"
					></textarea>
					<div class="text-[11px] text-[var(--gv2-text-muted,#555)] text-right mt-1">{rebuttal.length} / 4096</div>
				</label>

				{#if submitError}
					<div class="rounded-lg bg-red-500/10 border border-red-500/30 px-3 py-2 mb-3 text-[12px] text-red-400">{submitError}</div>
				{/if}
				{#if submitOk}
					<div class="rounded-lg bg-emerald-500/10 border border-emerald-500/30 px-3 py-2 mb-3 text-[12px] text-emerald-300">{submitOk}</div>
				{/if}

				{#if !$isSignedIn}
					<a href="/sign-in" class="block w-full rounded-lg bg-[#1185FE] py-2.5 text-center text-[14px] font-semibold text-white hover:opacity-90">Sign in to challenge</a>
				{:else}
					<button
						type="button"
						onclick={() => void submitChallenge()}
						disabled={submitting || !rebuttal.trim()}
						class="block w-full rounded-lg bg-orange-600 py-2.5 text-center text-[14px] font-semibold text-white hover:bg-orange-500 disabled:opacity-40 disabled:cursor-not-allowed"
					>{submitting ? 'Filing challenge…' : `Lock ${counterBondGcc} GCC + Challenge`}</button>
				{/if}
			</div>
		{:else if snap.state === 'pending'}
			<div class="rounded-xl border border-[var(--gv2-border,#2f2f2f)] bg-[var(--gv2-bg-card,#1f1f1f)] p-4 text-[13px] text-[var(--gv2-text-muted,#777)]">
				Challenge window has closed. The claimant can now call <span class="font-mono">claimUnchallenged</span> to refund the bond.
			</div>
		{:else if snap.state === 'challenged'}
			<div class="rounded-xl border border-[var(--gv2-border,#2f2f2f)] bg-[var(--gv2-bg-card,#1f1f1f)] p-4 text-[13px] text-[var(--gv2-text-muted,#777)]">
				Awaiting arbiter resolution. The arbiter has up to 14 days from challenge timestamp; after that, either party can call <span class="font-mono">noShow</span> for a full refund.
			</div>
		{/if}
	{/if}
</div>
