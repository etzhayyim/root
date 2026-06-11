<script lang="ts">
	import { Badge, Button, Toggle } from '@etzhayyim/design-system';
	import {
		setConvoEncryption, listConvoMembers, memberLabel,
		updateConvo, archiveConvo, inviteConvoMember, updateConvoMemberRole,
		rotateGroupKey,
	} from '$lib/atproto-agent';
	import type { ConvoMember, ConvoParticipantType } from '$lib/atproto-agent';

	interface Props {
		convoId: string;
		convoName?: string;
		description?: string;
		isEncrypted?: boolean;
		isDirect?: boolean;
		peerDid?: string;
		selfDid?: string;
		onClose?: () => void;
		onEncryptionChange?: () => void;
		onArchived?: () => void;
	}

	let {
		convoId,
		convoName = '',
		description = '',
		isEncrypted = false,
		isDirect = false,
		peerDid = '',
		selfDid = '',
		onClose,
		onEncryptionChange,
		onArchived,
	}: Props = $props();

	let encryptionToggle = $state(false);
	$effect(() => { encryptionToggle = isEncrypted; });
	let members = $state<ConvoMember[]>([]);
	let loadingMembers = $state(true);

	// Edit state
	let editingName = $state(false);
	let editName = $state('');
	let editDesc = $state('');
	$effect(() => { editName = convoName; editDesc = description; });
	let saving = $state(false);

	// Invite state
	let inviteDid = $state('');
	let inviting = $state(false);
	let inviteError = $state('');

	// Archive state
	let archiving = $state(false);

	const selfRole = $derived(members.find((m) => m.did === selfDid)?.role ?? 'member');
	const canManage = $derived(selfRole === 'owner' || selfRole === 'admin');

	$effect(() => {
		void loadMembers();
	});

	async function loadMembers() {
		loadingMembers = true;
		try {
			members = await listConvoMembers(convoId);
		} catch { /* ignore */ }
		finally { loadingMembers = false; }
	}

	async function handleEncryptionToggle() {
		encryptionToggle = !encryptionToggle;
		try {
			await setConvoEncryption(convoId, encryptionToggle);
			onEncryptionChange?.();
		} catch {
			encryptionToggle = !encryptionToggle;
		}
	}

	async function handleSave() {
		saving = true;
		try {
			await updateConvo(convoId, {
				name: editName !== convoName ? editName : undefined,
				description: editDesc !== description ? editDesc : undefined,
			});
			editingName = false;
		} catch { /* ignore */ }
		finally { saving = false; }
	}

	async function handleArchive() {
		if (!confirm('Archive this conversation? This cannot be undone.')) return;
		archiving = true;
		try {
			await archiveConvo(convoId);
			onArchived?.();
			onClose?.();
		} catch { /* ignore */ }
		finally { archiving = false; }
	}

	async function handleInvite() {
		if (!inviteDid.trim()) return;
		inviting = true;
		inviteError = '';
		try {
			await inviteConvoMember(convoId, inviteDid.trim());
			inviteDid = '';
			await loadMembers();
		} catch (e) {
			inviteError = e instanceof Error ? e.message : 'Failed to invite';
		} finally { inviting = false; }
	}

	async function handleRoleChange(targetDid: string, newRole: 'owner' | 'admin' | 'member') {
		try {
			await updateConvoMemberRole(convoId, targetDid, newRole);
			await loadMembers();
		} catch { /* ignore */ }
	}

	function participantBadge(type?: ConvoParticipantType): { label: string; variant: 'accent' | 'warning' } | null {
		if (type === 'agent') return { label: 'Agent', variant: 'accent' };
		if (type === 'service') return { label: 'Service', variant: 'warning' };
		return null;
	}
</script>

<div class="flex h-full flex-col bg-gv2-bg-primary">
	<!-- Header -->
	<div class="flex min-h-[48px] items-center gap-3 border-b border-gv2-border/40 px-4">
		<button
			type="button"
			class="flex h-9 w-9 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
			onclick={onClose}
			aria-label="Close"
		>
			<svg class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round">
				<path d="M15 19l-7-7 7-7" />
			</svg>
		</button>
		<span class="text-[15px] font-bold text-gv2-text-primary">Conversation settings</span>
	</div>

	<div class="flex-1 overflow-y-auto scrollbar-none p-4 space-y-4">
		<!-- Convo info (editable) -->
		<div class="rounded-2xl bg-gv2-bg-card p-4">
			{#if editingName && canManage}
				<input
					class="w-full rounded-xl bg-gv2-bg-input px-3 py-2 text-[17px] font-bold text-gv2-text-primary outline-none border border-gv2-border focus:border-[var(--gv2-accent,#06c755)]"
					bind:value={editName}
				/>
				<textarea
					class="mt-2 w-full rounded-xl bg-gv2-bg-input px-3 py-2 text-[14px] text-gv2-text-muted outline-none border border-gv2-border focus:border-[var(--gv2-accent,#06c755)] resize-none"
					rows="2"
					bind:value={editDesc}
					placeholder="Description"
				></textarea>
				<div class="mt-2 flex gap-2">
					<Button variant="outline" size="sm" onclick={() => { editingName = false; editName = convoName; editDesc = description; }}>Cancel</Button>
					<Button variant="solid-fill" size="sm" disabled={saving} onclick={handleSave}>{saving ? 'Saving...' : 'Save'}</Button>
				</div>
			{:else}
				<div class="flex items-start justify-between">
					<div>
						<h3 class="text-[17px] font-bold text-gv2-text-primary">{convoName}</h3>
						{#if description}
							<p class="mt-1 text-[14px] text-gv2-text-muted">{description}</p>
						{/if}
					</div>
					{#if canManage}
						<button
							type="button"
							class="flex h-8 w-8 items-center justify-center rounded-full text-gv2-text-muted touch-manipulation active:bg-gv2-bg-hover"
							onclick={() => { editingName = true; }}
							aria-label="Edit"
						>
							<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" /><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" /></svg>
						</button>
					{/if}
				</div>
			{/if}
		</div>

		<!-- Encryption -->
		<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-3">
			<div class="flex items-center justify-between">
				<div>
					<p class="text-[15px] font-semibold text-gv2-text-primary">E2E Encryption</p>
					<p class="text-[12px] text-gv2-text-muted">Signal Protocol end-to-end encryption</p>
				</div>
				<Toggle checked={encryptionToggle} onchange={handleEncryptionToggle} />
			</div>
		</div>

		<!-- Invite member -->
		{#if canManage && !isDirect}
			<div class="rounded-2xl bg-gv2-bg-card p-4">
				<h4 class="mb-2 text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted">Invite member</h4>
				<div class="flex gap-2">
					<input
						class="flex-1 min-h-[44px] rounded-xl bg-gv2-bg-input px-3 text-[14px] text-gv2-text-primary outline-none border border-gv2-border focus:border-[var(--gv2-accent,#06c755)] placeholder:text-gv2-text-muted"
						placeholder="did:plc:..."
						bind:value={inviteDid}
						onkeydown={(e) => { if (e.key === 'Enter') void handleInvite(); }}
					/>
					<Button variant="solid-fill" size="sm" disabled={inviting || !inviteDid.trim()} onclick={handleInvite}>
						{inviting ? '...' : 'Invite'}
					</Button>
				</div>
				{#if inviteError}
					<p class="mt-1 text-[12px] text-red-400">{inviteError}</p>
				{/if}
			</div>
		{/if}

		<!-- Members -->
		<div class="rounded-2xl bg-gv2-bg-card p-4">
			<h4 class="mb-2 text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted">Members</h4>
			{#if loadingMembers}
				<p class="text-[14px] text-gv2-text-muted">Loading...</p>
			{:else}
				<div class="space-y-2">
					{#each members as member}
						{@const badge = participantBadge(member.participantType)}
						<div class="flex items-center gap-3 py-1">
							<div class="flex h-8 w-8 items-center justify-center rounded-full bg-[var(--gv2-accent,#06c755)]/20 text-[11px] font-bold text-[var(--gv2-accent,#06c755)]">
								{memberLabel(member.did).slice(0, 2).toUpperCase()}
							</div>
							<div class="min-w-0 flex-1">
								<div class="flex items-center gap-1.5">
									<p class="truncate text-[14px] font-medium text-gv2-text-primary">{memberLabel(member.did)}</p>
									{#if badge}
										<Badge value={badge.label} variant={badge.variant} class="!text-[9px] !h-4 !min-w-0 !px-1.5" />
									{/if}
								</div>
								<div class="flex items-center gap-1.5">
									{#if canManage && member.did !== selfDid}
										<select
											class="bg-transparent text-[11px] text-gv2-text-muted outline-none cursor-pointer"
											value={member.role}
											onchange={(e) => handleRoleChange(member.did, e.currentTarget.value as 'owner' | 'admin' | 'member')}
										>
											<option value="owner">Owner</option>
											<option value="admin">Admin</option>
											<option value="member">Member</option>
										</select>
									{:else}
										<p class="text-[11px] text-gv2-text-muted">{member.role}</p>
									{/if}
								</div>
							</div>
							{#if member.did === selfDid}
								<span class="text-[11px] text-gv2-text-muted">You</span>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
		</div>

		<!-- Group key rotation (encrypted convos only) -->
		{#if encryptionToggle && canManage}
			<div class="rounded-2xl bg-gv2-bg-card p-4 space-y-2">
				<p class="text-[13px] font-semibold text-gv2-text-primary">Group key rotation</p>
				<p class="text-[12px] text-gv2-text-muted">Force re-key for all members. Use after removing a member from an encrypted conversation.</p>
				<Button variant="outline" size="sm" onclick={async () => { await rotateGroupKey(convoId); }}>
					Rotate key
				</Button>
			</div>
		{/if}

		<!-- Push notifications -->
		{#await import('./PushSettings.svelte') then { default: PushSettings }}
			<PushSettings {convoId} convoName={convoName} />
		{/await}

		<!-- Convo ID -->
		<div class="rounded-2xl bg-gv2-bg-card p-4">
			<h4 class="mb-1 text-[13px] font-bold uppercase tracking-wider text-gv2-text-muted">Convo ID</h4>
			<p class="break-all text-[12px] font-mono text-gv2-text-muted/70">{convoId}</p>
		</div>

		<!-- Archive (danger zone) -->
		{#if canManage && !isDirect}
			<div class="rounded-2xl border border-red-500/20 bg-red-500/5 p-4">
				<h4 class="mb-2 text-[13px] font-bold uppercase tracking-wider text-red-400">Danger zone</h4>
				<Button
					variant="outline"
					size="sm"
					class="!text-red-400 !border-red-400/30"
					disabled={archiving}
					onclick={handleArchive}
				>
					{archiving ? 'Archiving...' : 'Archive conversation'}
				</Button>
			</div>
		{/if}
	</div>
</div>
