<script lang="ts">
	import { Toggle } from '@etzhayyim/design-system';
	import { setupConvoPush, unsubscribePush } from '$lib/atproto-agent';

	interface Props {
		convoId: string;
		convoName?: string;
	}

	let { convoId, convoName = '' }: Props = $props();

	let pushEnabled = $state(false);
	let permissionState = $state<'default' | 'granted' | 'denied'>('default');
	let processing = $state(false);
	let error = $state('');
	let supported = $state(false);
	let subscription = $state<PushSubscription | null>(null);

	$effect(() => {
		if (typeof window === 'undefined') return;
		supported = 'serviceWorker' in navigator && 'PushManager' in window;
		if ('Notification' in window) {
			permissionState = Notification.permission;
		}
		void checkExisting();
	});

	async function checkExisting() {
		if (!supported) return;
		try {
			const reg = await navigator.serviceWorker.getRegistration('/');
			if (reg) {
				subscription = await reg.pushManager.getSubscription();
				pushEnabled = subscription !== null;
			}
		} catch { /* ignore */ }
	}

	async function handleToggle() {
		processing = true;
		error = '';
		try {
			if (!pushEnabled) {
				const ok = await setupConvoPush(convoId);
				if (!ok) {
					error = permissionState === 'denied'
						? 'Notification permission denied. Enable in browser settings.'
						: 'Failed to enable push notifications.';
					return;
				}
				pushEnabled = true;
				permissionState = 'granted';
			} else {
				if (subscription) {
					await unsubscribePush(subscription.endpoint, convoId);
					await subscription.unsubscribe();
				}
				pushEnabled = false;
				subscription = null;
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Push setup failed';
		} finally {
			processing = false;
		}
	}
</script>

<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-3">
	<div class="flex items-center justify-between">
		<div>
			<p class="text-[15px] font-semibold text-gv2-text-primary">Push notifications</p>
			<p class="text-[12px] text-gv2-text-muted">
				{#if !supported}
					Not supported in this browser
				{:else if permissionState === 'denied'}
					Blocked by browser settings
				{:else}
					{convoName ? `Notify for ${convoName}` : 'Receive push alerts for new messages'}
				{/if}
			</p>
		</div>
		{#if supported && permissionState !== 'denied'}
			<Toggle checked={pushEnabled} disabled={processing} onchange={handleToggle} />
		{/if}
	</div>
	{#if error}
		<p class="text-[12px] text-red-400">{error}</p>
	{/if}
</div>
