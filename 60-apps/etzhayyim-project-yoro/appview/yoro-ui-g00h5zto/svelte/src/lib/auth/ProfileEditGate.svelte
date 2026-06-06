<script lang="ts">
	// Same-origin /profile auth gate (ADR-2606060000). Lets a member prove DID
	// control via passkey OR wallet/SIWE directly on etzhayyim.com/profile — no
	// auth.etzhayyim.com hop, no server key. On success the parent flips into
	// edit-mode (`onVerified`). The actual profile write is a CACAO-authorized
	// datom:transact to kotoba (this only gates the UI).
	import { Button } from '@etzhayyim/design-system';
	import type { SessionKey } from './session-key.js';
	import { signInWithPasskey, signInWithWallet, type VerifyCacaoResult } from './profile-signin.js';
	import type { Eip1193Provider } from './cacao.js';

	interface Props {
		/** The passkey-derived Ed25519 session key (from the key hierarchy). */
		sessionKey?: SessionKey;
		/** kotoba graph CID the edit capability is scoped to (actor-profile graph). */
		graphCid: string;
		/** Called with the resolved DID once a CACAO verifies. */
		onVerified?: (result: VerifyCacaoResult) => void;
	}

	const { sessionKey, graphCid, onVerified }: Props = $props();

	let status = $state<'idle' | 'signing' | 'verified' | 'gated' | 'error'>('idle');
	let message = $state('');

	function deps() {
		return {
			now: () => Date.now(),
			nonce: () => {
				const b = crypto.getRandomValues(new Uint8Array(16));
				return Array.from(b, (x) => x.toString(16).padStart(2, '0')).join('');
			},
			// same-origin: empty base → POST /xrpc/... on the current host.
			origin: '',
		};
	}

	async function withPasskey() {
		if (!sessionKey) {
			status = 'error';
			message = 'Unlock your passkey first to derive a session key.';
			return;
		}
		status = 'signing';
		try {
			const res = await signInWithPasskey(sessionKey, graphCid, deps());
			if (res.valid) {
				status = 'verified';
				message = `Verified as ${res.did}`;
				onVerified?.(res);
			} else {
				status = 'error';
				message = res.reason ?? 'Verification failed.';
			}
		} catch (e) {
			status = 'error';
			message = e instanceof Error ? e.message : String(e);
		}
	}

	async function withWallet() {
		const eth = (globalThis as { ethereum?: Eip1193Provider }).ethereum;
		if (!eth) {
			status = 'error';
			message = 'No EIP-1193 wallet found.';
			return;
		}
		status = 'signing';
		try {
			const accounts = await eth.request<string[]>({ method: 'eth_requestAccounts' });
			const address = accounts?.[0];
			if (!address) throw new Error('No wallet account authorized.');
			const res = await signInWithWallet(eth, address, graphCid, deps());
			if (res.valid) {
				status = 'verified';
				message = `Verified as ${res.did}`;
				onVerified?.(res);
			} else if (res.gated) {
				// honest: SIWE recovery runs on the kotoba node; not a false session.
				status = 'gated';
				message = 'Wallet signature accepted — verification completes on the kotoba node.';
				onVerified?.(res);
			} else {
				status = 'error';
				message = res.reason ?? 'Verification failed.';
			}
		} catch (e) {
			status = 'error';
			message = e instanceof Error ? e.message : String(e);
		}
	}
</script>

<div class="profile-edit-gate">
	<p class="gate-title">Sign in to edit your profile</p>
	<div class="gate-actions">
		<Button onclick={withPasskey} disabled={status === 'signing'}>Passkey</Button>
		<Button variant="secondary" onclick={withWallet} disabled={status === 'signing'}>
			Wallet (SIWE)
		</Button>
	</div>
	{#if message}
		<p class="gate-message" data-status={status}>{message}</p>
	{/if}
</div>

<style>
	.profile-edit-gate {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}
	.gate-actions {
		display: flex;
		gap: 0.5rem;
	}
	.gate-message[data-status='error'] {
		color: var(--color-danger, #c0392b);
	}
</style>
