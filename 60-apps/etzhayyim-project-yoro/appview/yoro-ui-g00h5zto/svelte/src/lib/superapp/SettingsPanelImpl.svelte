<script lang="ts">
	import { onMount } from 'svelte';
	import { get } from 'svelte/store';
	import { Avatar, Badge, Button, Input } from '@etzhayyim/design-system';
	import {
		clerkLoaded,
		isSignedIn,
		clerkUser,
		currentOrg,
		userOrganizations,
		orgLoading,
		displayName,
		userPlan,
		trustSummary,
	} from '../auth/stores.js';
	import {
		initClerk,
		signIn,
		signUp,
		signUpWithUsername,
		signOut,
		openUserProfile,
		switchOrganization,
		createOrganization,
	} from '../auth/passkey.js';
	import {
		hasEthereumProvider,
		linkEthereumAddress,
		unlinkEthereumAddress,
	} from '../auth/ethereum.js';
	import {
		linkAdditionalPasskey,
		unlinkAdditionalPasskey,
	} from '../auth/passkey-additional.js';
	import { trustVariantFromScore } from '../auth/trust.js';
	import { ThemeToggle } from '../index.js';
	import { filterLanguages } from '../language.js';

	interface Props {
		appName?: string;
		accentColor?: string;
		whatsappNumber?: string;
		privacyHref?: string;
		termsHref?: string;
		supportHref?: string;
		/** Override the language list shown. Default: ja, en */
		languageCodes?: string[];
		/** External language change handler. If not set, stores in localStorage only. */
		onLanguageChange?: (code: string) => void;
	}

	let {
		appName = 'etzhayyim',
		accentColor = 'bg-etzhayyim-accent',
		whatsappNumber = '',
		privacyHref = 'https://etzhayyim.com/privacy/',
		termsHref = 'https://etzhayyim.com/terms/',
		supportHref = '',
		languageCodes = ['ja', 'en'],
		onLanguageChange,
	}: Props = $props();

	const LANG_STORAGE_KEY = 'gv2-lang';

	function getInitialLang(): string {
		if (typeof window === 'undefined') return 'ja';
		const stored = localStorage.getItem(LANG_STORAGE_KEY);
		if (stored && languageCodes.includes(stored)) return stored;
		const browserLang = navigator.language?.split('-')[0];
		if (browserLang && languageCodes.includes(browserLang)) return browserLang;
		return languageCodes[0] ?? 'ja';
	}

	let currentLang = $state(getInitialLang());
	let clerkInitialized = $state(false);
	let usernameDraft = $state('');
	let newOrgName = $state('');
	let accountError = $state('');
	let workspaceError = $state('');
	let accountBusy = $state<'sign-in' | 'clerk' | 'username' | null>(null);
	let workspaceBusy = $state<'create' | string | null>(null);

	// ── Staked claims (ADR-2604261717 Phase 3) ─────────────────────────────
	interface ClaimItem {
		claimId: string;
		state: 'pending' | 'challenged' | 'upheld' | 'slashed' | 'refunded' | 'none' | 'error';
		bondGcc?: string;
		atRecordCid?: string;
		postedAt?: number;
		challenger?: string;
		counterBond?: string;
	}
	let claimsLoading = $state(false);
	let claims = $state<ClaimItem[]>([]);

	const CLAIM_STATE_LABELS: Record<string, string> = {
		pending: 'Pending',
		challenged: 'Challenged',
		upheld: 'Upheld ✓',
		slashed: 'Slashed ✗',
		refunded: 'Refunded',
		none: 'Gone',
		error: 'Error',
	};
	const CLAIM_STATE_VARIANTS: Record<string, 'success' | 'warning' | 'error' | 'muted'> = {
		pending: 'warning',
		challenged: 'error',
		upheld: 'success',
		slashed: 'error',
		refunded: 'muted',
		none: 'muted',
		error: 'muted',
	};

	async function reloadClaims() {
		if (!get(isSignedIn)) { claims = []; return; }
		claimsLoading = true;
		try {
			const resp = await fetch('https://authz.etzhayyim.com/xrpc/com.etzhayyim.claim.listStakedAttestations?limit=20', {
				credentials: 'include',
			});
			if (!resp.ok) { claims = []; return; }
			const body = (await resp.json()) as { claims?: ClaimItem[] };
			claims = body.claims ?? [];
		} catch (err) {
			console.warn('[settings] reloadClaims failed', err);
			claims = [];
		} finally {
			claimsLoading = false;
		}
	}

	// ── Linked methods (ADR-0074 Phase 1) ──────────────────────────────────
	interface LinkedMethod {
		provider: string;
		providerSubject: string;
		displayLabel: string;
		verified: boolean;
	}
	let linkedMethods = $state<LinkedMethod[]>([]);
	let linkedMethodsLoading = $state(false);
	let linkedBusy = $state<'eth' | 'passkey' | string | null>(null);
	let linkedError = $state('');
	let additionalPasskeyLabel = $state('');
	const ethereumAvailable = $derived.by(() => hasEthereumProvider());

	async function reloadLinkedMethods() {
		if (!get(isSignedIn)) {
			linkedMethods = [];
			return;
		}
		linkedMethodsLoading = true;
		try {
			const resp = await fetch('https://authz.etzhayyim.com/xrpc/com.etzhayyim.authz.getSession', {
				credentials: 'include',
			});
			if (!resp.ok) return;
			const body = (await resp.json()) as { linkedMethods?: LinkedMethod[] };
			linkedMethods = body.linkedMethods ?? [];
		} catch (error) {
			console.warn('[settings] reloadLinkedMethods failed', error);
		} finally {
			linkedMethodsLoading = false;
		}
	}

	async function runLinkAction(action: 'eth' | 'passkey' | string, fn: () => Promise<unknown>) {
		linkedBusy = action;
		linkedError = '';
		try {
			await fn();
			await reloadLinkedMethods();
		} catch (error) {
			linkedError = error instanceof Error ? error.message : 'Link operation failed';
		} finally {
			linkedBusy = null;
		}
	}

	// ── Smart account (ADR-0074 Phase 2-B) ─────────────────────────────────
	// Resolved by `com.etzhayyim.authz.getActorAccount` (eth_call into
	// etzhayyimActorRegistry on the etzhayyim private chain 260425). When the account
	// hasn't been activated yet, `smartAccount` is null — display will show
	// "Not yet activated" and the user can opt in via a future activation
	// flow (Phase 2-C, sealer-sponsored tx). Read failure is non-fatal:
	// authz auth still works without it (link methods, etc.).
	interface ActorAccountSnapshot {
		accountDid: string;
		didHash: string;
		activated: boolean;
		smartAccount?: string | null;
		chainId?: number;
		registryAddr?: string;
	}
	let actorAccount = $state<ActorAccountSnapshot | null>(null);
	let actorAccountLoading = $state(false);
	let actorAccountError = $state('');

	async function reloadActorAccount() {
		if (!get(isSignedIn)) {
			actorAccount = null;
			return;
		}
		actorAccountLoading = true;
		actorAccountError = '';
		try {
			const resp = await fetch('https://authz.etzhayyim.com/xrpc/com.etzhayyim.authz.getActorAccount', {
				credentials: 'include',
			});
			if (!resp.ok) {
				if (resp.status !== 401) {
					actorAccountError = `getActorAccount HTTP ${resp.status}`;
				}
				actorAccount = null;
				return;
			}
			actorAccount = (await resp.json()) as ActorAccountSnapshot;
		} catch (error) {
			actorAccountError = error instanceof Error ? error.message : 'rpc failed';
			actorAccount = null;
		} finally {
			actorAccountLoading = false;
		}
	}

	async function copySmartAccount() {
		if (!actorAccount?.smartAccount) return;
		try { await navigator.clipboard.writeText(actorAccount.smartAccount); }
		catch (error) { console.warn('[settings] clipboard write failed', error); }
	}

	let activating = $state(false);
	async function activateSmartAccount() {
		if (activating) return;
		activating = true;
		actorAccountError = '';
		try {
			const resp = await fetch('https://authz.etzhayyim.com/xrpc/com.etzhayyim.authz.activateActorAccount', {
				method: 'POST',
				credentials: 'include',
				headers: { 'Content-Type': 'application/json' },
				body: '{}',
			});
			if (!resp.ok) {
				const body = (await resp.json().catch((error) => {
					console.warn('activateActorAccount error body parse failed:', error);
					return {};
				})) as { error?: string; message?: string };
				actorAccountError = body.message || `activate HTTP ${resp.status}`;
				return;
			}
			actorAccount = (await resp.json()) as ActorAccountSnapshot;
		} catch (error) {
			actorAccountError = error instanceof Error ? error.message : 'activation failed';
		} finally {
			activating = false;
		}
	}

	const languages = $derived(filterLanguages(languageCodes));

	function slugifyOrgName(name: string): string {
		return name
			.trim()
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, '-')
			.replace(/^-+|-+$/g, '')
			.slice(0, 48);
	}

	function selectLang(code: string) {
		currentLang = code;
		if (typeof window !== 'undefined') {
			localStorage.setItem(LANG_STORAGE_KEY, code);
			document.documentElement.setAttribute('lang', code);
		}
		onLanguageChange?.(code);
	}

	async function runAccountAction(
		action: 'sign-in' | 'clerk' | 'username',
		callback: () => Promise<void>,
	) {
		accountBusy = action;
		accountError = '';
		try {
			await callback();
		} catch (error) {
			accountError = error instanceof Error ? error.message : 'Authentication failed';
		} finally {
			accountBusy = null;
		}
	}

	async function handleUsernameSignUp() {
		const normalized = usernameDraft.trim();
		if (!normalized) {
			accountError = 'Choose a username first.';
			return;
		}
		await runAccountAction('username', async () => {
			await signUpWithUsername({ username: normalized });
		});
	}

	async function handleWorkspaceSwitch(orgId: string) {
		workspaceBusy = orgId;
		workspaceError = '';
		try {
			await switchOrganization(orgId);
		} catch (error) {
			workspaceError = error instanceof Error ? error.message : 'Failed to switch workspace';
		} finally {
			workspaceBusy = null;
		}
	}

	async function handleWorkspaceCreate() {
		const normalized = newOrgName.trim();
		if (!normalized) {
			workspaceError = 'Workspace name is required.';
			return;
		}
		workspaceBusy = 'create';
		workspaceError = '';
		try {
			const orgId = await createOrganization(normalized, slugifyOrgName(normalized));
			if (orgId) {
				await switchOrganization(orgId);
				newOrgName = '';
			}
		} catch (error) {
			workspaceError = error instanceof Error ? error.message : 'Failed to create workspace';
		} finally {
			workspaceBusy = null;
		}
	}

	onMount(() => {
		if (!get(clerkLoaded) && !clerkInitialized) {
			clerkInitialized = true;
			initClerk().catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/superapp/SettingsPanelImpl.svelte: suppressed async error", error); });
		}
		document.documentElement.setAttribute('lang', currentLang);
		reloadLinkedMethods();
		reloadActorAccount();
		reloadClaims();
	});

	$effect(() => {
		if ($isSignedIn) {
			reloadLinkedMethods();
			reloadActorAccount();
			reloadClaims();
		} else {
			linkedMethods = [];
			actorAccount = null;
			claims = [];
		}
	});
</script>

<div class="w-full max-w-[600px] mx-auto p-4 flex flex-col gap-4">
	<h2 class="text-[17px] font-bold text-etzhayyim-text">Settings</h2>

	<!-- Account -->
	<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
		<div class="px-4 py-3 border-b border-etzhayyim-border">
			<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Account</span>
		</div>
		{#if $isSignedIn}
			<div class="p-4 flex items-center gap-3">
				<Avatar
					src={$clerkUser?.imageUrl}
					fallback={$displayName}
					size="lg"
					class="!{accentColor} !text-white"
				/>
				<div class="flex-1 min-w-0">
					<div class="text-[15px] font-bold text-etzhayyim-text truncate">{$displayName}</div>
					<div class="text-[12px] text-etzhayyim-muted">{$userPlan}</div>
					<div class="mt-1 flex flex-wrap items-center gap-2">
						<Badge value={`T${$trustSummary.score}`} variant={trustVariantFromScore($trustSummary.score)} />
						{#if $clerkUser?.username}
							<span class="text-[12px] text-etzhayyim-secondary">@{$clerkUser.username}</span>
						{/if}
						{#if $clerkUser?.phoneNumber}
							<span class="text-[12px] text-etzhayyim-secondary">{$clerkUser.phoneNumber}</span>
						{/if}
					</div>
					{#if $clerkUser?.emailAddress}
						<div class="text-[12px] text-etzhayyim-secondary truncate">{$clerkUser.emailAddress}</div>
					{/if}
				</div>
			</div>
			<div class="border-t border-etzhayyim-border divide-y divide-etzhayyim-border">
				<button
					class="w-full flex items-center gap-3 px-4 py-3 text-[15px] text-etzhayyim-text active:bg-etzhayyim-hover transition-colors min-h-[44px] touch-manipulation"
					onclick={() => openUserProfile()}
				>
					<svg class="w-5 h-5 text-etzhayyim-secondary shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" /><circle cx="12" cy="7" r="4" />
					</svg>
					Profile
				</button>
				<button
					class="w-full flex items-center gap-3 px-4 py-3 text-[15px] text-red-500 active:bg-red-50 transition-colors min-h-[44px] touch-manipulation"
					onclick={() => signOut()}
				>
					<svg class="w-5 h-5 shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" />
					</svg>
					Sign Out
				</button>
			</div>
		{:else}
			<div class="p-4 flex flex-col gap-3">
				<p class="text-[14px] text-etzhayyim-secondary">
					Sign in with a passkey (Touch ID / Face ID / device PIN). Ethereum wallets, Google,
					Microsoft, and additional devices can be linked once you're signed in.
				</p>
				<div class="grid grid-cols-1 gap-3">
					<Button
						variant="outline"
						size="md"
						onclick={() => runAccountAction('sign-in', signIn)}
						disabled={accountBusy !== null}
					>
						{accountBusy === 'sign-in' ? 'Opening...' : 'Sign in with passkey'}
					</Button>
					<Button
						variant="solid-fill"
						size="md"
						onclick={() => runAccountAction('clerk', signUp)}
						disabled={accountBusy !== null}
					>
						{accountBusy === 'clerk' ? 'Opening...' : 'Create account with passkey'}
					</Button>
					<div class="rounded-2xl border border-etzhayyim-border p-3 flex flex-col gap-3">
						<div class="flex items-center justify-between gap-3">
							<div>
								<div class="text-[14px] font-semibold text-etzhayyim-text">Create with username</div>
								<div class="text-[12px] text-etzhayyim-secondary">Great for lightweight org creation before stronger verification.</div>
							</div>
							<Badge value="+15" variant="accent" />
						</div>
						<Input
							bind:value={usernameDraft}
							placeholder="your-handle"
							autocomplete="username"
							class="!border-etzhayyim-border !bg-etzhayyim-hover !text-etzhayyim-text"
						/>
						<Button
							variant="outline"
							size="sm"
							onclick={handleUsernameSignUp}
							disabled={accountBusy !== null}
						>
							{accountBusy === 'username' ? 'Preparing...' : 'Create username account'}
						</Button>
					</div>
				</div>
				{#if accountError}
					<p class="text-[12px] text-red-500">{accountError}</p>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Smart account (ADR-0074 Phase 2-B: ERC-4337 wallet on etzhayyim private chain 260425) -->
	{#if $isSignedIn}
		<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
			<div class="px-4 py-3 border-b border-etzhayyim-border flex items-center justify-between">
				<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Smart account</span>
				<span class="text-[11px] text-etzhayyim-secondary">etzhayyim private chain · 260425</span>
			</div>
			<div class="p-4 flex flex-col gap-3">
				{#if actorAccountLoading}
					<p class="text-[13px] text-etzhayyim-secondary">Resolving on chain…</p>
				{:else if actorAccount?.activated && actorAccount.smartAccount}
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="text-[13px] text-etzhayyim-secondary">ERC-4337 wallet</div>
							<div class="text-[14px] font-mono text-etzhayyim-text break-all">{actorAccount.smartAccount}</div>
						</div>
						<Badge value="Activated" variant="success" />
					</div>
					<button
						type="button"
						class="self-start text-[12px] underline text-etzhayyim-secondary hover:text-etzhayyim-text"
						onclick={copySmartAccount}
					>
						Copy address
					</button>
				{:else if actorAccount && !actorAccount.activated}
					<div class="flex items-start justify-between gap-3">
						<div class="min-w-0">
							<div class="text-[13px] text-etzhayyim-secondary">Status</div>
							<div class="text-[14px] text-etzhayyim-text">Not yet activated</div>
							<div class="text-[12px] text-etzhayyim-muted mt-1">
								Deploy your ERC-4337 smart account now (sealer-sponsored, gasless). Your passkey becomes a P-256 owner of the wallet.
							</div>
						</div>
						<Badge value={activating ? 'Deploying…' : 'Pending'} variant="warning" />
					</div>
					<Button
						variant="primary"
						size="sm"
						disabled={activating}
						onclick={activateSmartAccount}
					>
						{activating ? 'Deploying smart account…' : 'Activate now'}
					</Button>
					{#if actorAccountError}
						<p class="text-[12px] text-amber-500">{actorAccountError}</p>
					{/if}
				{:else if actorAccountError}
					<p class="text-[12px] text-amber-500">Could not resolve smart account: {actorAccountError}</p>
				{:else}
					<p class="text-[13px] text-etzhayyim-secondary">Sign in to view your smart account.</p>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Staked claims (ADR-2604261717 Phase 3) -->
	{#if $isSignedIn}
		<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
			<div class="px-4 py-3 border-b border-etzhayyim-border flex items-center justify-between">
				<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Staked Claims</span>
				<span class="text-[11px] text-etzhayyim-secondary">GCC bond · 7-day challenge window</span>
			</div>
			<div class="p-4 flex flex-col gap-3">
				{#if claimsLoading && claims.length === 0}
					<p class="text-[13px] text-etzhayyim-secondary">Loading…</p>
				{:else if claims.length === 0}
					<p class="text-[13px] text-etzhayyim-secondary">No staked claims yet. Use the ⚖ button in the post composer to stake GCC on a claim.</p>
				{:else}
					<ul class="flex flex-col gap-2">
						{#each claims as claim (claim.claimId)}
							<li>
								<a
									href="/claim/{claim.claimId}"
									class="flex items-start justify-between gap-3 rounded-xl border border-etzhayyim-border px-3 py-2 no-underline active:bg-etzhayyim-hover transition-colors"
								>
									<div class="min-w-0 flex-1">
										<div class="text-[12px] font-mono text-etzhayyim-muted truncate">{claim.claimId.slice(0, 18)}…</div>
										<div class="flex flex-wrap items-center gap-2 mt-1">
											{#if claim.bondGcc && Number(claim.bondGcc) > 0}
												<span class="text-[11px] text-etzhayyim-secondary">{claim.bondGcc} GCC staked</span>
											{/if}
											{#if claim.postedAt}
												<span class="text-[11px] text-etzhayyim-muted">{new Date(claim.postedAt * 1000).toLocaleDateString()}</span>
											{/if}
											{#if claim.state === 'challenged' && claim.counterBond}
												<span class="text-[11px] text-amber-500">Counter-bond: {claim.counterBond} GCC</span>
											{/if}
										</div>
									</div>
									<Badge
										value={CLAIM_STATE_LABELS[claim.state] ?? claim.state}
										variant={CLAIM_STATE_VARIANTS[claim.state] ?? 'muted'}
									/>
								</a>
							</li>
						{/each}
					</ul>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Linked methods (ADR-0074 Phase 1: passkey-required, Ethereum private chain + multi-device) -->
	{#if $isSignedIn}
		<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
			<div class="px-4 py-3 border-b border-etzhayyim-border flex items-center justify-between">
				<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Linked methods</span>
				<span class="text-[11px] text-etzhayyim-secondary">Each verified method = +25 trust (max 100)</span>
			</div>
			<div class="p-4 flex flex-col gap-3">
				{#if linkedMethodsLoading && linkedMethods.length === 0}
					<p class="text-[13px] text-etzhayyim-secondary">Loading…</p>
				{:else if linkedMethods.length === 0}
					<p class="text-[13px] text-etzhayyim-secondary">No methods linked yet. Link a wallet or another device below.</p>
				{:else}
					<ul class="flex flex-col gap-2">
						{#each linkedMethods as method (method.provider + ':' + method.providerSubject)}
							<li class="flex items-center justify-between gap-3 rounded-xl border border-etzhayyim-border px-3 py-2">
								<div class="min-w-0">
									<div class="flex items-center gap-2">
										<span class="text-[14px] font-semibold text-etzhayyim-text">{method.displayLabel}</span>
										<Badge value={method.provider} variant={method.verified ? 'success' : 'warning'} />
									</div>
									<div class="text-[11px] font-mono text-etzhayyim-muted truncate">{method.providerSubject}</div>
								</div>
								{#if method.provider !== 'passkey'}
									<Button
										variant="outline"
										size="xs"
										disabled={linkedBusy !== null}
										onclick={() => runLinkAction(method.provider + ':' + method.providerSubject, async () => {
											if (method.provider === 'ethereum' || method.provider === 'coinbase-smart-wallet') {
												await unlinkEthereumAddress(method.providerSubject, method.provider);
											}
											else if (method.provider === 'webauthn-additional') await unlinkAdditionalPasskey(method.providerSubject);
											else await fetch('https://authz.etzhayyim.com/xrpc/com.etzhayyim.authz.unlinkMethod', {
												method: 'POST',
												credentials: 'include',
												headers: { 'Content-Type': 'application/json' },
												body: JSON.stringify({ provider: method.provider, providerSubject: method.providerSubject }),
											});
										})}
									>
										{linkedBusy === method.provider + ':' + method.providerSubject ? 'Removing…' : 'Remove'}
									</Button>
								{/if}
							</li>
						{/each}
					</ul>
				{/if}

				<div class="border-t border-etzhayyim-border pt-3 flex flex-col gap-2">
					<div class="flex items-center justify-between gap-3">
						<div class="min-w-0">
							<div class="text-[14px] font-semibold text-etzhayyim-text">Coinbase Smart Wallet / Ethereum wallet</div>
							<div class="text-[12px] text-etzhayyim-secondary">
								Sign a SIWE message on the etzhayyim private chain (chainId 260425, native token NETH, base unit wu).
								{#if !ethereumAvailable}<span class="text-amber-500"> Install Coinbase Wallet or another EIP-1193 wallet.</span>{/if}
							</div>
						</div>
						<Button
							variant="solid-fill"
							size="sm"
							disabled={linkedBusy !== null || !ethereumAvailable}
							onclick={() => runLinkAction('eth', linkEthereumAddress)}
						>
							{linkedBusy === 'eth' ? 'Signing…' : 'Link wallet'}
						</Button>
					</div>
					<div class="flex items-center justify-between gap-3">
						<div class="min-w-0 flex-1">
							<div class="text-[14px] font-semibold text-etzhayyim-text">Additional device passkey</div>
							<div class="text-[12px] text-etzhayyim-secondary">Enrol another device (iPhone / MacBook / hardware key) so either can sign in.</div>
							<Input
								bind:value={additionalPasskeyLabel}
								placeholder="Label (optional, e.g. iPhone 15)"
								class="!border-etzhayyim-border !bg-etzhayyim-hover !text-etzhayyim-text mt-2"
							/>
						</div>
						<Button
							variant="solid-fill"
							size="sm"
							disabled={linkedBusy !== null}
							onclick={() => runLinkAction('passkey', () => linkAdditionalPasskey(additionalPasskeyLabel.trim() || undefined))}
						>
							{linkedBusy === 'passkey' ? 'Enrolling…' : 'Add passkey'}
						</Button>
					</div>
				</div>

				{#if linkedError}
					<p class="text-[12px] text-red-500">{linkedError}</p>
				{/if}
			</div>
		</div>
	{/if}

	<!-- Workspace -->
	<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
		<div class="px-4 py-3 border-b border-etzhayyim-border">
			<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Workspace</span>
		</div>
		{#if !$isSignedIn}
			<div class="p-4">
				<p class="text-[14px] text-etzhayyim-secondary">Sign in to switch orgs and create workspaces.</p>
			</div>
		{:else}
			<div class="p-4 flex flex-col gap-3">
				<div class="rounded-2xl border border-etzhayyim-border p-4 flex items-start justify-between gap-3">
					<div class="min-w-0">
						<div class="text-[12px] uppercase tracking-wider text-etzhayyim-muted">Active</div>
						<div class="text-[15px] font-bold text-etzhayyim-text truncate">{$currentOrg?.name || 'No org selected'}</div>
						<div class="mt-1 flex flex-wrap gap-2 text-[12px] text-etzhayyim-secondary">
							<span>{$currentOrg?.category || 'individual'}</span>
							{#if $currentOrg?.role}
								<span>{$currentOrg.role.replace('org:', '')}</span>
							{/if}
							{#if $currentOrg?.requiredTrustScore}
								<span>Trust {$currentOrg.requiredTrustScore}+</span>
							{/if}
							{#if $currentOrg?.minimumAge}
								<span>Age {$currentOrg.minimumAge}+</span>
							{/if}
						</div>
					</div>
					<Badge value={`T${$trustSummary.score}`} variant={trustVariantFromScore($trustSummary.score)} />
				</div>
				<div class="flex flex-col gap-2">
					{#if $orgLoading}
						<p class="text-[13px] text-etzhayyim-secondary">Loading orgs...</p>
					{:else if $userOrganizations.length === 0}
						<p class="text-[13px] text-etzhayyim-secondary">Create your first workspace below.</p>
					{:else}
						{#each $userOrganizations as org (org.id)}
							<button
								class="w-full rounded-2xl border border-etzhayyim-border px-4 py-3 text-left active:bg-etzhayyim-hover transition-colors"
								onclick={() => handleWorkspaceSwitch(org.id)}
							>
								<div class="flex items-center justify-between gap-3">
									<div class="min-w-0">
										<div class="truncate text-[14px] font-semibold text-etzhayyim-text">{org.name}</div>
										<div class="flex flex-wrap gap-2 text-[12px] text-etzhayyim-secondary">
											<span>{org.category}</span>
											{#if org.memberCount}
												<span>{org.memberCount} members</span>
											{/if}
											{#if org.requiredTrustScore}
												<span>Trust {org.requiredTrustScore}+</span>
											{/if}
										</div>
									</div>
									{#if $currentOrg?.id === org.id}
										<Badge value="Active" variant="success" />
									{:else if workspaceBusy === org.id}
										<Badge value="..." variant="warning" />
									{/if}
								</div>
							</button>
						{/each}
					{/if}
				</div>
				<div class="rounded-2xl border border-dashed border-etzhayyim-border p-4 flex flex-col gap-3">
					<div>
						<div class="text-[14px] font-semibold text-etzhayyim-text">Create org</div>
						<div class="text-[12px] text-etzhayyim-secondary">Spin up a new org for a project, client, or community.</div>
					</div>
					<Input
						bind:value={newOrgName}
						placeholder="Acme Labs"
						class="!border-etzhayyim-border !bg-etzhayyim-hover !text-etzhayyim-text"
					/>
					<Button
						variant="solid-fill"
						size="sm"
						onclick={handleWorkspaceCreate}
						disabled={workspaceBusy !== null}
					>
						{workspaceBusy === 'create' ? 'Creating...' : 'Create workspace'}
					</Button>
				</div>
				{#if workspaceError}
					<p class="text-[12px] text-red-500">{workspaceError}</p>
				{/if}
			</div>
		{/if}
	</div>

	<!-- Trust -->
	<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
		<div class="px-4 py-3 border-b border-etzhayyim-border">
			<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Trust & Access</span>
		</div>
		<div class="p-4 flex flex-col gap-3">
			<div class="flex items-start justify-between gap-3">
				<div>
					<div class="text-[15px] font-bold text-etzhayyim-text">Trust score {$trustSummary.score}</div>
					<div class="text-[12px] text-etzhayyim-secondary">
						Level {$trustSummary.label}. SpinApps can gate actions with trust score and age rules.
					</div>
				</div>
				<Badge value={`T${$trustSummary.score}`} variant={trustVariantFromScore($trustSummary.score)} />
			</div>
			{#if $trustSummary.methods.length > 0}
				<div class="flex flex-wrap gap-2 text-[12px] text-etzhayyim-secondary">
					{#each $trustSummary.methods as method}
						<span class="rounded-full bg-etzhayyim-hover px-3 py-1">{method}</span>
					{/each}
				</div>
			{/if}
			<div class="flex flex-col gap-2">
				{#each $trustSummary.steps as step (step.id)}
					<div class="rounded-2xl border border-etzhayyim-border px-4 py-3">
						<div class="flex items-center justify-between gap-3">
							<div>
								<div class="text-[14px] font-semibold text-etzhayyim-text">{step.label}</div>
								<div class="text-[12px] text-etzhayyim-secondary">{step.description}</div>
							</div>
							<Badge
								value={step.completed ? 'Done' : `+${step.trustGain}`}
								variant={step.completed ? 'success' : 'warning'}
							/>
						</div>
					</div>
				{/each}
			</div>
			{#if !$trustSummary.accessReady}
				<div class="rounded-2xl border border-yellow-500/40 bg-yellow-500/10 px-4 py-3">
					<div class="text-[13px] font-semibold text-etzhayyim-text">Current access gaps</div>
					<div class="mt-1 flex flex-wrap gap-2 text-[12px] text-etzhayyim-secondary">
						{#each $trustSummary.accessReasons as reason}
							<span class="rounded-full bg-white/10 px-3 py-1">{reason}</span>
						{/each}
					</div>
				</div>
			{/if}
		</div>
	</div>

	<!-- Appearance -->
	<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
		<div class="px-4 py-3 border-b border-etzhayyim-border">
			<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Appearance</span>
		</div>
		<div class="p-4 flex items-center justify-between min-h-[44px]">
			<span class="text-[15px] text-etzhayyim-text">Theme</span>
			<ThemeToggle showSystem={true} size={36} />
		</div>
	</div>

	<!-- Language -->
	{#if languages.length > 1}
		<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
			<div class="px-4 py-3 border-b border-etzhayyim-border">
				<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Language</span>
			</div>
			<div class="p-4">
				<div class="flex flex-wrap gap-2">
					{#each languages as lang}
						<button
							class="px-3 py-1.5 rounded-full text-[13px] font-medium touch-manipulation transition-colors min-h-[36px] {currentLang === lang.code ? 'bg-etzhayyim-accent text-white' : 'bg-etzhayyim-hover text-etzhayyim-secondary active:bg-etzhayyim-border'}"
							onclick={() => selectLang(lang.code)}
						>{lang.name}</button>
					{/each}
				</div>
			</div>
		</div>
	{/if}

	<!-- Support -->
	<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
		<div class="px-4 py-3 border-b border-etzhayyim-border">
			<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Support</span>
		</div>
		<div class="divide-y divide-etzhayyim-border">
			{#if whatsappNumber}
				<a
					href="https://wa.me/{whatsappNumber}"
					target="_blank"
					rel="noopener"
					class="w-full flex items-center gap-3 px-4 py-3 text-[15px] text-etzhayyim-text active:bg-etzhayyim-hover transition-colors min-h-[44px] touch-manipulation no-underline"
				>
					<svg class="w-5 h-5 text-green-500 shrink-0" viewBox="0 0 24 24" fill="currentColor">
						<path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
					</svg>
					WhatsApp Support
				</a>
			{/if}
			{#if supportHref}
				<a
					href={supportHref}
					target="_blank"
					rel="noopener"
					class="w-full flex items-center gap-3 px-4 py-3 text-[15px] text-etzhayyim-text active:bg-etzhayyim-hover transition-colors min-h-[44px] touch-manipulation no-underline"
				>
					<svg class="w-5 h-5 text-etzhayyim-secondary shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
						<circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" />
					</svg>
					Help Center
				</a>
			{/if}
		</div>
	</div>

	<!-- Legal -->
	<div class="bg-etzhayyim-card rounded-2xl border border-etzhayyim-border overflow-hidden">
		<div class="px-4 py-3 border-b border-etzhayyim-border">
			<span class="text-[12px] font-semibold text-etzhayyim-muted uppercase tracking-wider">Legal</span>
		</div>
		<div class="divide-y divide-etzhayyim-border">
			<a
				href={privacyHref}
				target="_blank"
				rel="noopener"
				class="w-full flex items-center justify-between px-4 py-3 text-[15px] text-etzhayyim-text active:bg-etzhayyim-hover transition-colors min-h-[44px] touch-manipulation no-underline"
			>
				Privacy Policy
				<svg class="w-4 h-4 text-etzhayyim-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
			</a>
			<a
				href={termsHref}
				target="_blank"
				rel="noopener"
				class="w-full flex items-center justify-between px-4 py-3 text-[15px] text-etzhayyim-text active:bg-etzhayyim-hover transition-colors min-h-[44px] touch-manipulation no-underline"
			>
				Terms of Use
				<svg class="w-4 h-4 text-etzhayyim-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="9 18 15 12 9 6" /></svg>
			</a>
		</div>
	</div>

	<!-- App Info -->
	<div class="text-center py-4">
		<p class="text-[12px] text-etzhayyim-muted">{appName}</p>
		<p class="text-[11px] text-etzhayyim-muted mt-0.5">&copy; {new Date().getFullYear()} etzhayyim.com</p>
	</div>
</div>
