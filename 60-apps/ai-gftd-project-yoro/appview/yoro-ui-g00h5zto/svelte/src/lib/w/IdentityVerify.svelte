<script lang="ts">
	import { getIdentityFingerprint, verifyIdentityKey, memberLabel } from '$lib/atproto-agent';

	interface Props {
		peerDid: string;
		deviceId?: number;
	}

	let { peerDid, deviceId = 1 }: Props = $props();

	let fingerprint = $state('');
	let identityKey = $state('');
	let verified = $state(false);
	let loading = $state(true);

	$effect(() => {
		void loadFingerprint();
	});

	async function loadFingerprint() {
		loading = true;
		try {
			const result = await getIdentityFingerprint(peerDid, deviceId);
			fingerprint = result.fingerprint;
			identityKey = result.identityKey;
			verified = result.verified;
		} finally {
			loading = false;
		}
	}

	async function handleVerify() {
		await verifyIdentityKey(peerDid, deviceId);
		verified = true;
	}
</script>

<div class="space-y-4">
	<h3 class="text-[15px] font-bold text-gv2-text-primary">🔐 Identity 検証</h3>
	<p class="text-[13px] text-gv2-text-muted">{memberLabel(peerDid)}</p>

	{#if loading}
		<p class="text-[14px] text-gv2-text-muted">読み込み中...</p>
	{:else if !fingerprint}
		<p class="text-[14px] text-gv2-text-muted">フィンガープリントを取得できませんでした。</p>
	{:else}
		<div class="rounded-2xl bg-gv2-bg-card p-4">
			<p class="mb-2 text-[11px] font-bold uppercase tracking-wider text-gv2-text-muted">Safety Number</p>
			<p class="break-all font-mono text-[14px] leading-relaxed text-gv2-text-primary">{fingerprint}</p>
		</div>

		{#if verified}
			<div class="flex items-center gap-2 rounded-2xl bg-[#58CC02]/10 px-4 py-3">
				<span class="text-[16px]">✅</span>
				<span class="text-[14px] font-semibold text-[#58CC02]">検証済み</span>
			</div>
		{:else}
			<button
				type="button"
				class="w-full rounded-2xl bg-[#58CC02] py-3 text-[15px] font-bold text-white shadow-[0_4px_0_#3D8A00] touch-manipulation active:shadow-none active:translate-y-[4px] transition-all"
				onclick={() => void handleVerify()}
			>検証済みとしてマーク</button>
		{/if}
	{/if}
</div>
