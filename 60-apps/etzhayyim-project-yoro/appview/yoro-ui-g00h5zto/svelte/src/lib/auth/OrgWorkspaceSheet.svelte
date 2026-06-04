<script lang="ts">
	import { Badge, BottomSheet, Button, Card, Input } from '@etzhayyim/design-system';
	import type { Organization, TrustSummary } from './types.js';
	import { trustVariantFromScore } from './trust.js';

	interface Props {
		open: boolean;
		currentOrg: Organization | null;
		organizations: Organization[];
		trust: TrustSummary;
		loading?: boolean;
		onclose?: () => void;
		onSwitch: (orgId: string) => Promise<void> | void;
		onCreate: (name: string) => Promise<void> | void;
	}

	let {
		open = $bindable(false),
		currentOrg,
		organizations,
		trust,
		loading = false,
		onclose,
		onSwitch,
		onCreate,
	}: Props = $props();

	let newOrgName = $state('');
	let errorMessage = $state('');
	let switchingOrgId = $state<string | null>(null);
	let creating = $state(false);

	function closeSheet() {
		open = false;
		onclose?.();
	}

	async function switchOrg(orgId: string) {
		errorMessage = '';
		switchingOrgId = orgId;
		try {
			await onSwitch(orgId);
			closeSheet();
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to switch workspace';
		} finally {
			switchingOrgId = null;
		}
	}

	async function createOrg() {
		const normalized = newOrgName.trim();
		if (!normalized) {
			errorMessage = 'Workspace name is required.';
			return;
		}
		errorMessage = '';
		creating = true;
		try {
			await onCreate(normalized);
			newOrgName = '';
			closeSheet();
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to create workspace';
		} finally {
			creating = false;
		}
	}
</script>

<BottomSheet bind:open onclose={closeSheet} snapHeight="82vh" class="!bg-[var(--gv2-bg-primary,#111827)]">
	<div class="flex flex-col gap-4 px-4 pb-6 text-[var(--gv2-text-primary,#ffffff)]">
		<div class="flex flex-col gap-2">
			<div class="flex items-center justify-between gap-3">
				<h3 class="text-[18px] font-semibold">Workspace</h3>
				<Badge value={`T${trust.score}`} variant={trustVariantFromScore(trust.score)} />
			</div>
			<p class="text-[13px] text-[var(--gv2-text-secondary,#9ca3af)]">
				Keep a personal org and spin up new orgs for clients, projects, or brands without leaving
				the shell.
			</p>
		</div>

		<Card class="border border-[var(--gv2-border,#334155)] bg-[var(--gv2-bg-card,#111827)] p-4">
			<div class="flex flex-col gap-2">
				<div class="flex items-center justify-between gap-3">
					<div class="text-[13px] uppercase tracking-[0.18em] text-[var(--gv2-text-muted,#94a3b8)]">
						Active Org
					</div>
					{#if currentOrg}
						<Badge value="Active" variant="success" />
					{/if}
				</div>
				<div class="text-[17px] font-semibold">
					{currentOrg?.name || 'No org selected'}
				</div>
				<div class="flex flex-wrap gap-2 text-[12px] text-[var(--gv2-text-secondary,#9ca3af)]">
					<span>{currentOrg?.category || 'individual'}</span>
					{#if currentOrg?.role}
						<span>{currentOrg.role.replace('org:', '')}</span>
					{/if}
					{#if currentOrg?.requiredTrustScore}
						<span>Trust {currentOrg.requiredTrustScore}+</span>
					{/if}
					{#if currentOrg?.minimumAge}
						<span>Age {currentOrg.minimumAge}+</span>
					{/if}
				</div>
			</div>
		</Card>

		<div class="flex flex-col gap-3">
			<div class="text-[13px] uppercase tracking-[0.18em] text-[var(--gv2-text-muted,#94a3b8)]">
				Switch Org
			</div>
			{#if loading}
				<p class="text-[13px] text-[var(--gv2-text-secondary,#9ca3af)]">Loading workspaces...</p>
			{:else if organizations.length === 0}
				<p class="text-[13px] text-[var(--gv2-text-secondary,#9ca3af)]">
					Create your first org below.
				</p>
			{:else}
				<div class="flex flex-col gap-2">
					{#each organizations as org (org.id)}
						<Card
							class="border border-[var(--gv2-border,#334155)] bg-[var(--gv2-bg-card,#111827)] p-4"
							onclick={() => switchOrg(org.id)}
						>
							<div class="flex items-center justify-between gap-3">
								<div class="min-w-0">
									<div class="truncate text-[15px] font-semibold">{org.name}</div>
									<div class="flex flex-wrap gap-2 text-[12px] text-[var(--gv2-text-secondary,#9ca3af)]">
										<span>{org.category}</span>
										{#if org.memberCount}
											<span>{org.memberCount} members</span>
										{/if}
										{#if org.requiredTrustScore}
											<span>Trust {org.requiredTrustScore}+</span>
										{/if}
									</div>
								</div>
								{#if currentOrg?.id === org.id}
									<Badge value="Now" variant="success" />
								{:else if switchingOrgId === org.id}
									<Badge value="..." variant="warning" />
								{/if}
							</div>
						</Card>
					{/each}
				</div>
			{/if}
		</div>

		<Card class="border border-dashed border-[var(--gv2-border,#334155)] bg-[var(--gv2-bg-card,#111827)] p-4">
			<div class="flex flex-col gap-3">
				<div>
					<div class="text-[15px] font-semibold">Create Org</div>
					<div class="text-[12px] text-[var(--gv2-text-secondary,#9ca3af)]">
						Use separate orgs for clients, communities, or private experiment spaces.
					</div>
				</div>
				<Input
					bind:value={newOrgName}
					placeholder="Acme Labs"
					class="!border-[var(--gv2-border,#334155)] !bg-[var(--gv2-bg-input,#0f172a)] !text-[var(--gv2-text-primary,#ffffff)]"
				/>
				<Button variant="solid-fill" size="sm" onclick={createOrg} disabled={creating || switchingOrgId !== null}>
					{creating ? 'Creating...' : 'Create workspace'}
				</Button>
			</div>
		</Card>

		{#if errorMessage}
			<p class="text-[12px] text-red-400">{errorMessage}</p>
		{/if}
	</div>
</BottomSheet>
