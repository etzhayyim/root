<script lang="ts">
	import { goto } from '$app/navigation';
	import { Avatar, Badge, Skeleton } from '@etzhayyim/design-system';
	import { staggerFade } from '@etzhayyim/design-system/motion';
		import { getCurrentDID, getProfile, setProfile, uploadBlob, listDevices } from '$lib/atproto-agent';
	import { signOut } from '$lib/auth/passkey.js';
	import { isSignedIn } from '$lib/auth/stores.js';
	import {
		getDeviceImportPermissionStatus,
		importContactsToAT,
		importSmsToAT,
		isAndroidDeviceImportAvailable,
		requestDeviceImportPermissions,
		type DeviceImportPermissionStatus,
	} from '$lib/device-import.js';
	import { onMount } from 'svelte';
	import { fade } from 'svelte/transition';

	let loading = $state(true);
	let did = $state('');
	let displayName = $state('');
	let avatarUrl = $state('');
	let editingName = $state(false);
	let nameValue = $state('');
	let saving = $state(false);
	let devices = $state<Array<{ deviceId: string; displayName: string }>>([]);
	let deviceImportAvailable = $state(false);
	let deviceImportPermissions = $state<DeviceImportPermissionStatus>({ contacts: 'denied', sms: 'denied' });
	let contactsImportBusy = $state(false);
	let smsImportBusy = $state(false);
	let contactsImportStatus = $state('');
	let smsImportStatus = $state('');

	onMount(async () => {
		deviceImportAvailable = isAndroidDeviceImportAvailable();
		try {
			did = await getCurrentDID();
			const profile = await getProfile(did || undefined);
			displayName = profile.displayName ?? '';
			avatarUrl = profile.avatarUrl ?? '';
			devices = await listDevices();
			if (deviceImportAvailable) {
				deviceImportPermissions = await getDeviceImportPermissionStatus();
			}
		} catch {
			/* anonymous */
		} finally {
			loading = false;
		}
	});

	async function saveName() {
		const trimmed = nameValue.trim();
		if (!trimmed || trimmed === displayName) {
			editingName = false;
			return;
		}
		saving = true;
		try {
			await setProfile({ displayName: trimmed, avatarUrl: avatarUrl || undefined });
			displayName = trimmed;
			editingName = false;
		} catch (e) {
			console.error('Failed to update display name:', e);
		} finally {
			saving = false;
		}
	}

	async function handleAvatarUpload(event: Event) {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (!file) return;

		saving = true;
		try {
			const currentDid = await getCurrentDID();
			if (!currentDid) {
				throw new Error('ログインが必要です。再ログインしてください。');
			}
			const result = await uploadBlob(file);

			const blobUri = result.blob?.ref;
			if (blobUri) {
				await setProfile({ displayName: displayName || undefined, avatarUrl: blobUri });
				avatarUrl = blobUri;
			}
		} catch (e) {
			console.error('Failed to upload avatar:', e);
		} finally {
			saving = false;
			if (target) target.value = '';
		}
	}

	function goBack() {
		if (history.length > 1) {
			history.back();
		} else {
			goto('/');
		}
	}

	async function refreshImportPermissions() {
		if (!deviceImportAvailable) return;
		deviceImportPermissions = await getDeviceImportPermissionStatus();
	}

	async function handleContactsImport() {
		if (!deviceImportAvailable || contactsImportBusy) return;
		contactsImportBusy = true;
		contactsImportStatus = '';
		try {
			if (deviceImportPermissions.contacts !== 'granted') {
				deviceImportPermissions = await requestDeviceImportPermissions({ contacts: true });
			}
			if (deviceImportPermissions.contacts !== 'granted') {
				throw new Error('Contacts permission was not granted');
			}
			const result = await importContactsToAT();
			contactsImportStatus = `Imported ${result.importedCount} contacts`;
		} catch (error) {
			contactsImportStatus = error instanceof Error ? error.message : 'Failed to import contacts';
		} finally {
			contactsImportBusy = false;
			await refreshImportPermissions();
		}
	}

	async function handleSmsImport() {
		if (!deviceImportAvailable || smsImportBusy) return;
		smsImportBusy = true;
		smsImportStatus = '';
		try {
			if (deviceImportPermissions.sms !== 'granted') {
				deviceImportPermissions = await requestDeviceImportPermissions({ sms: true });
			}
			if (deviceImportPermissions.sms !== 'granted') {
				throw new Error('SMS permission was not granted');
			}
			const result = await importSmsToAT();
			smsImportStatus = `Imported ${result.importedCount} SMS messages`;
		} catch (error) {
			smsImportStatus = error instanceof Error ? error.message : 'Failed to import SMS';
		} finally {
			smsImportBusy = false;
			await refreshImportPermissions();
		}
	}
</script>

<svelte:head>
	<title>設定 — YORO</title>
</svelte:head>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center gap-2 border-b border-gv2-border/50 px-4">
		<button
			type="button"
			class="flex h-11 w-11 items-center justify-center rounded-full text-gv2-text-muted tap-target-44 touch-manipulation active:text-gv2-text-primary"
			onclick={goBack}
			aria-label="戻る"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
				<path d="M15 19l-7-7 7-7" />
			</svg>
		</button>
		<h3 class="text-[17px] font-bold text-gv2-text-primary">⚙️ 設定</h3>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none pb-20 safe-area-bottom">
		{#if loading}
			<!-- Loading skeleton -->
			<div class="border-b border-gv2-border/30 px-4 py-6">
				<div class="flex flex-col items-center gap-3" in:fade={staggerFade(0, { duration: 300 })}>
					<div class="h-20 w-20 animate-pulse rounded-full bg-gv2-bg-hover"></div>
					<Skeleton variant="text" class="w-32" />
					<Skeleton variant="text" class="w-48" />
				</div>
			</div>
			<div class="px-4 py-3" in:fade={staggerFade(1, { duration: 300 })}>
				{#each [0, 1, 2] as _}
					<div class="flex h-[44px] items-center gap-3">
						<div class="h-8 w-8 animate-pulse rounded-lg bg-gv2-bg-hover"></div>
						<div class="h-4 w-32 animate-pulse rounded bg-gv2-bg-hover"></div>
					</div>
				{/each}
			</div>
		{:else}
			<!-- Profile section -->
			<div class="border-b border-gv2-border/30 px-4 py-6">
				<div class="flex flex-col items-center gap-3">
					<!-- Avatar with upload -->
					<button
						type="button"
						class="group relative tap-target-44 touch-manipulation"
						onclick={() => document.getElementById('avatar-upload')?.click()}
						aria-label="Change avatar"
					>
						<Avatar
							src={avatarUrl || undefined}
							fallback={(displayName || did || '?').slice(0, 2).toUpperCase()}
							size="lg"
							class="!h-20 !w-20 !text-xl"
						/>
						<div class="absolute inset-0 flex items-center justify-center rounded-full bg-black/40 opacity-0 transition-opacity group-active:opacity-100">
							<svg class="h-6 w-6 text-white" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
								<path stroke-linecap="round" stroke-linejoin="round" d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
								<path stroke-linecap="round" stroke-linejoin="round" d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0z" />
							</svg>
						</div>
						{#if saving}
							<div class="absolute inset-0 flex items-center justify-center rounded-full bg-black/50">
								<div class="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></div>
							</div>
						{/if}
					</button>
					<input
						id="avatar-upload"
						type="file"
						accept="image/*"
						class="hidden"
						onchange={handleAvatarUpload}
					/>

					<!-- Display Name -->
					{#if editingName}
						<div class="flex w-full items-center gap-2">
							<input
								type="text"
								bind:value={nameValue}
								class="min-h-[44px] flex-1 rounded-xl bg-gv2-bg-hover/60 px-3 py-2 text-center text-[17px] font-bold text-gv2-text-primary focus:outline-none focus:ring-2 focus:ring-discord-accent/50"
								onkeydown={(e) => { if (e.key === 'Enter') void saveName(); if (e.key === 'Escape') editingName = false; }}
								disabled={saving}
							/>
							<button
								type="button"
								class="flex h-11 w-11 items-center justify-center rounded-full bg-discord-accent text-white tap-target-44 touch-manipulation active:bg-discord-accent-hover"
								onclick={() => void saveName()}
								disabled={saving}
								aria-label="Save display name"
							>
								<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round">
									<path d="M5 13l4 4L19 7" />
								</svg>
							</button>
						</div>
					{:else}
						<button
							type="button"
							class="text-[17px] font-bold text-gv2-text-primary tap-target-44 touch-manipulation active:opacity-70"
							onclick={() => { nameValue = displayName; editingName = true; }}
						>
							{displayName || '名前を設定する'}
						</button>
					{/if}

					<p class="max-w-[280px] truncate text-[13px] text-gv2-text-muted">{did}</p>
				</div>
			</div>

			<!-- Signal Devices section -->
			{#if devices.length > 0}
				<div class="border-b border-gv2-border/30 px-4 py-4">
					<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">
						Signal デバイス
					</h4>
					<div class="space-y-2">
						{#each devices as device}
							<div class="flex min-h-[44px] items-center justify-between rounded-xl bg-gv2-bg-hover/30 px-3 py-2">
								<div class="flex items-center gap-2">
									<svg class="h-4 w-4 text-[#58CC02]" viewBox="0 0 16 16" fill="currentColor">
										<path d="M8 1a4 4 0 00-4 4v2H3a1 1 0 00-1 1v6a1 1 0 001 1h10a1 1 0 001-1V8a1 1 0 00-1-1h-1V5a4 4 0 00-4-4zm2 6H6V5a2 2 0 114 0v2z" />
									</svg>
									<span class="text-[14px] font-medium text-gv2-text-primary">
										{device.displayName || device.deviceId}
									</span>
								</div>
								<Badge value={device.deviceId} variant="default" />
							</div>
						{/each}
					</div>
				</div>
			{/if}

			<!-- Android Import section -->
			<div class="border-b border-gv2-border/30 px-4 py-4">
				<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">
					Android インポート
				</h4>
				{#if deviceImportAvailable}
					<div class="space-y-3">
						<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-secondary/40 p-3">
							<div class="flex items-center justify-between gap-3">
								<div>
									<p class="text-[14px] font-medium text-gv2-text-primary">連絡先</p>
									<p class="text-[12px] text-gv2-text-muted">権限: {deviceImportPermissions.contacts}</p>
								</div>
								<button
									type="button"
									class="min-h-[44px] rounded-xl bg-discord-accent px-4 text-[13px] font-semibold text-white tap-target-44 touch-manipulation active:bg-discord-accent-hover disabled:opacity-50"
									onclick={() => void handleContactsImport()}
									disabled={contactsImportBusy}
								>
									{contactsImportBusy ? 'インポート中...' : 'インポート'}
								</button>
							</div>
							{#if contactsImportStatus}
								<p class="mt-2 text-[12px] text-gv2-text-muted">{contactsImportStatus}</p>
							{/if}
						</div>

						<div class="rounded-2xl border border-gv2-border/40 bg-gv2-bg-secondary/40 p-3">
							<div class="flex items-center justify-between gap-3">
								<div>
									<p class="text-[14px] font-medium text-gv2-text-primary">SMS</p>
									<p class="text-[12px] text-gv2-text-muted">権限: {deviceImportPermissions.sms}</p>
								</div>
								<button
									type="button"
									class="min-h-[44px] rounded-xl bg-discord-accent px-4 text-[13px] font-semibold text-white tap-target-44 touch-manipulation active:bg-discord-accent-hover disabled:opacity-50"
									onclick={() => void handleSmsImport()}
									disabled={smsImportBusy}
								>
									{smsImportBusy ? 'インポート中...' : 'インポート'}
								</button>
							</div>
							{#if smsImportStatus}
								<p class="mt-2 text-[12px] text-gv2-text-muted">{smsImportStatus}</p>
							{/if}
						</div>
					</div>
				{:else}
					<p class="text-[13px] text-gv2-text-muted">このインポート機能は Android アプリのみ対応しています。</p>
				{/if}
			</div>

			<!-- Developer section -->
			<div class="border-b border-gv2-border/30 px-4 py-4">
				<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">
					Developer
				</h4>
				<a
					href="/settings/developer"
					class="flex min-h-[44px] items-center justify-between rounded-lg px-2 py-1.5 active:bg-gv2-bg-hover/40"
				>
					<div class="flex items-center gap-3">
						<svg class="h-5 w-5 text-gv2-text-muted" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
							<path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
						</svg>
						<div>
							<span class="text-[14px] font-medium text-gv2-text-primary">API Keys</span>
							<p class="text-[12px] text-gv2-text-muted">CLI, SDK, LLM Agent access</p>
						</div>
					</div>
					<svg class="h-4 w-4 text-gv2-text-muted/50" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
						<path d="M9 5l7 7-7 7" />
					</svg>
				</a>
			</div>

			<!-- About section -->
			<div class="px-4 py-4">
				<h4 class="mb-2 text-[12px] font-bold uppercase tracking-wider text-gv2-text-muted">
					このアプリについて
				</h4>
				<div class="space-y-0.5">
					<div class="flex min-h-[44px] items-center justify-between rounded-lg px-2 py-1.5">
						<span class="text-[14px] text-gv2-text-primary">アプリバージョン</span>
						<span class="text-[13px] text-gv2-text-muted">1.0.0</span>
					</div>
					<div class="flex min-h-[44px] items-center justify-between rounded-lg px-2 py-1.5">
						<span class="text-[14px] text-gv2-text-primary">プロトコル</span>
						<span class="text-[13px] text-gv2-text-muted">AT Protocol + Signal</span>
					</div>
					<div class="flex min-h-[44px] items-center justify-between rounded-lg px-2 py-1.5">
						<span class="text-[14px] text-gv2-text-primary">DID</span>
						<span class="max-w-[180px] truncate pl-4 text-[13px] text-gv2-text-muted">{did}</span>
					</div>
				</div>
			</div>
		{/if}

		{#if $isSignedIn}
		<div class="mt-6">
			<button
				onclick={() => { signOut(); goto('/'); }}
				class="flex w-full items-center justify-center gap-2 rounded-xl bg-red-500/10 px-4 py-3 text-[15px] font-semibold text-red-400 transition-colors hover:bg-red-500/20"
			>
				<svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2"><path stroke-linecap="round" stroke-linejoin="round" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"/></svg>
				ログアウト
			</button>
		</div>
		{/if}
	</div>
</div>
