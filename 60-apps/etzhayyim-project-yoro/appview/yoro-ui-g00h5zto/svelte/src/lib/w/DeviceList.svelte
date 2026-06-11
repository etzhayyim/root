<script lang="ts">
	import { Badge, Button } from '@etzhayyim/design-system';
	import { listDevices, ensureDevice, revokeDevice, renameDevice, replenishOtpks } from '$lib/atproto-agent';
	import { ensureSignalIdentity, hasIdentity } from '$lib/atproto-agent';
	import { getCurrentDID } from '$lib/atproto-agent';

	let devices = $state<Array<{ deviceId: string; displayName: string }>>([]);
	let loading = $state(true);
	let renaming = $state<string | null>(null);
	let renameValue = $state('');
	let replenishing = $state(false);
	let otpkCount = $state<number | null>(null);

	$effect(() => {
		void loadDevices();
	});

	async function loadDevices() {
		loading = true;
		try {
			devices = await listDevices();
		} finally {
			loading = false;
		}
	}

	async function handleProvision() {
		try {
			const did = await getCurrentDID();
			if (did) await ensureSignalIdentity(did, '1');
			await ensureDevice();
			await loadDevices();
		} catch { /* ignore */ }
	}

	async function handleRevoke(deviceId: string) {
		if (!confirm('Revoke this device? Signal sessions will be reset.')) return;
		await revokeDevice(deviceId);
		await loadDevices();
	}

	async function handleRename(deviceId: string) {
		if (!renameValue.trim()) return;
		await renameDevice(deviceId, renameValue.trim());
		renaming = null;
		renameValue = '';
		await loadDevices();
	}

	async function handleReplenish() {
		replenishing = true;
		try {
			// Generate 10 new one-time prekeys
			const keys: number[][] = [];
			const keyIds: number[] = [];
			for (let i = 0; i < 10; i++) {
				const rawKeyPair = await crypto.subtle.generateKey({ name: 'X25519' }, true, ['deriveBits']);
				if (!('publicKey' in rawKeyPair)) continue;
				const keyPair = rawKeyPair;
				const publicRaw = new Uint8Array(await crypto.subtle.exportKey('raw', keyPair.publicKey));
				keys.push(Array.from(publicRaw));
				keyIds.push(Date.now() + i);
			}
			const deviceId = devices[0]?.deviceId ?? '1';
			otpkCount = await replenishOtpks(deviceId, keys, keyIds);
		} catch { /* ignore */ }
		finally { replenishing = false; }
	}
</script>

<div class="space-y-3">
	<div class="flex items-center justify-between">
		<h3 class="text-[15px] font-bold text-gv2-text-primary">Signal Devices</h3>
		<Button variant="solid-fill" size="sm" onclick={() => void handleProvision()}>
			+ Add device
		</Button>
	</div>

	{#if loading}
		<p class="text-[14px] text-gv2-text-muted">Loading...</p>
	{:else if devices.length === 0}
		<div class="rounded-2xl bg-gv2-bg-card p-4 text-center">
			<p class="text-[14px] text-gv2-text-muted">No devices registered.</p>
			<p class="mt-1 text-[12px] text-gv2-text-muted/60">Add a device to enable end-to-end encryption.</p>
		</div>
	{:else}
		{#each devices as device}
			<div class="flex items-center gap-3 rounded-2xl bg-gv2-bg-card p-3">
				<div class="flex h-9 w-9 items-center justify-center rounded-xl bg-[var(--gv2-accent,#06c755)]/20 text-[14px]">
					<svg class="h-5 w-5 text-[var(--gv2-accent,#06c755)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="5" y="2" width="14" height="20" rx="2" /><line x1="12" y1="18" x2="12.01" y2="18" /></svg>
				</div>
				<div class="min-w-0 flex-1">
					{#if renaming === device.deviceId}
						<input
							class="w-full rounded-lg bg-gv2-bg-input px-2 py-1 text-[14px] outline-none border border-gv2-border"
							bind:value={renameValue}
							onkeydown={(e) => { if (e.key === 'Enter') void handleRename(device.deviceId); if (e.key === 'Escape') renaming = null; }}
							placeholder="Device name"
						/>
					{:else}
						<p class="text-[14px] font-medium text-gv2-text-primary">{device.displayName}</p>
						<p class="text-[11px] text-gv2-text-muted">ID: {device.deviceId}</p>
					{/if}
				</div>
				<button
					type="button"
					class="flex h-8 w-8 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
					onclick={() => { renaming = device.deviceId; renameValue = device.displayName; }}
					aria-label="Rename"
				>
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
				</button>
				<button
					type="button"
					class="flex h-8 w-8 items-center justify-center rounded-full text-red-400 touch-manipulation active:bg-red-400/10"
					onclick={() => void handleRevoke(device.deviceId)}
					aria-label="Revoke"
				>
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6" /><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" /></svg>
				</button>
			</div>
		{/each}

		<!-- OTPK replenish -->
		<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-2">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-[13px] font-semibold text-gv2-text-primary">One-time prekeys</p>
					<p class="text-[11px] text-gv2-text-muted">
						{#if otpkCount !== null}
							{otpkCount} keys available
							{#if otpkCount < 5}
								<Badge value="Low" variant="warning" class="!text-[9px] !h-4 !min-w-0 !px-1.5 ml-1" />
							{/if}
						{:else}
							Generates keys for new Signal sessions
						{/if}
					</p>
				</div>
				<Button variant="outline" size="sm" disabled={replenishing} onclick={handleReplenish}>
					{replenishing ? '...' : 'Replenish'}
				</Button>
			</div>
		</div>
	{/if}
</div>
