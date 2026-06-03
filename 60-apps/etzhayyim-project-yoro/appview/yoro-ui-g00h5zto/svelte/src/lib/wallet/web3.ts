// Stub: wallet/web3 removed (viem not needed for yoro)
import { writable, derived } from 'svelte/store';

export const walletState = writable({ connected: false, address: '', chainId: 0, balances: {} as Record<string, string> });
export const ethBalanceFormatted = derived(walletState, () => '0.0');
export const tokenBalances = derived(walletState, () => [] as Array<{ symbol: string; balance: string }>);
export const walletError = writable<string | null>(null);
export const walletLoading = writable(false);
export function getWalletAddress(): string | null { return null; }
export function connectWallet(): Promise<void> { return Promise.resolve(); }
export function disconnectWallet(): Promise<void> { return Promise.resolve(); }
export function refreshBalances(): Promise<void> { return Promise.resolve(); }
export function shortenAddress(addr: string): string { return addr ? `${addr.slice(0, 6)}...${addr.slice(-4)}` : ''; }
export function isWalletAvailable(): boolean { return false; }
export const walletConnected = writable(false);
