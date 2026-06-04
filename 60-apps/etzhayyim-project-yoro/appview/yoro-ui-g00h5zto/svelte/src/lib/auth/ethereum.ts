/**
 * Ethereum (private chain) link flow — ADR-0074 Phase 1.
 *
 * Caller must already hold a yoro session (passkey-first policy). This module
 * only adds an Ethereum address or Coinbase Smart Wallet as a *linked method*
 * on the existing ERC725 root / legacy did:etzhayyim account; it never creates a
 * new account. Use after primary passkey signin.
 *
 * Wire path:
 *   browser EIP-1193 wallet
 *     → eth_requestAccounts → address
 *     → POST authz.etzhayyim.com/xrpc/com.etzhayyim.authz.linkEthereumBegin
 *     → personal_sign (window.ethereum)
 *     → POST authz.etzhayyim.com/xrpc/com.etzhayyim.authz.linkEthereumVerify
 */

import { getSessionToken } from './passkey';

const AUTHZ_BASE = 'https://authz.etzhayyim.com';

export interface EthereumLinkResult {
	ok: boolean;
	address: string;
	didPkh: string;
	linkedMethods: Array<Record<string, unknown>>;
	actorScore: Record<string, unknown>;
	provider?: string;
	verificationKind?: string;
}

interface EthereumProvider {
	request<T = unknown>(args: { method: string; params?: unknown[] }): Promise<T>;
	isMetaMask?: boolean;
	isCoinbaseWallet?: boolean;
}

/** True iff a browser EIP-1193 provider (Coinbase Wallet, MetaMask, Rabby, etc.) is installed. */
export function hasEthereumProvider(): boolean {
	if (typeof window === 'undefined') return false;
	return Boolean((window as unknown as { ethereum?: EthereumProvider }).ethereum);
}

function getProvider(): EthereumProvider {
	if (typeof window === 'undefined') {
		throw new Error('Ethereum provider only available in the browser');
	}
	const provider = (window as unknown as { ethereum?: EthereumProvider }).ethereum;
	if (!provider) throw new Error('No Ethereum wallet found. Install Coinbase Wallet or another EIP-1193 wallet.');
	return provider;
}

async function authzPost<T>(path: string, body: unknown): Promise<T> {
	const token = await getSessionToken();
	if (!token) throw new Error('Not signed in. Sign in with your passkey first.');
	const resp = await fetch(`${AUTHZ_BASE}${path}`, {
		method: 'POST',
		headers: {
			'Content-Type': 'application/json',
			Authorization: `Bearer ${token}`,
		},
		credentials: 'include',
		body: JSON.stringify(body),
	});
	if (!resp.ok) {
		const text = await resp.text().catch((_err) => '');
		throw new Error(`${path} failed: ${resp.status} ${text}`);
	}
	return resp.json() as Promise<T>;
}

/**
 * Run the full link dance: prompt the wallet for an address, ask the server
 * for a SIWE message, sign it with personal_sign, and submit it back. On
 * success the linked-methods table includes the new ethereum entry and
 * `getSession` will surface it on subsequent reads.
 */
export async function linkEthereumAddress(opts: { statement?: string } = {}): Promise<EthereumLinkResult> {
	const provider = getProvider();
	const walletKind = provider.isCoinbaseWallet ? 'coinbase-smart-wallet' : 'ethereum';

	// 1. Request accounts (this triggers the wallet's connect dialog the first
	//    time; subsequent calls return cached accounts).
	const accounts = await provider.request<string[]>({ method: 'eth_requestAccounts' });
	if (!Array.isArray(accounts) || accounts.length === 0) {
		throw new Error('No accounts returned from the wallet');
	}
	const address = accounts[0].toLowerCase();

	// 2. Server issues SIWE message + nonce, bound to (accountDid, address).
	const begin = await authzPost<{
		message: string;
		nonce: string;
		chainId: number;
		expiresAt: number;
	}>('/xrpc/com.etzhayyim.authz.linkEthereumBegin', {
		address,
		statement: opts.statement,
		walletKind,
	});

	// 3. personal_sign — wallet hashes "\x19Ethereum Signed Message:\n…" and
	//    signs with secp256k1. Address must already be unlocked, hence the
	//    eth_requestAccounts step above.
	const signature = await provider.request<string>({
		method: 'personal_sign',
		params: [begin.message, address],
	});

	// 4. Server recovers the address from the signature and persists the link.
	const verify = await authzPost<EthereumLinkResult>(
		'/xrpc/com.etzhayyim.authz.linkEthereumVerify',
		{ message: begin.message, signature, walletKind },
	);
	return verify;
}

/** Remove a previously linked Ethereum address. */
export async function unlinkEthereumAddress(address: string, provider = 'ethereum'): Promise<{ ok: boolean }> {
	return authzPost('/xrpc/com.etzhayyim.authz.unlinkMethod', {
		provider,
		providerSubject: address.toLowerCase(),
	});
}
