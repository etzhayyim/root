<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Button,
		Input,
		Textarea,
		Badge,
		EmptyState,
		NotificationBanner,
		Skeleton,
	} from '@etzhayyim/design-system';
	import { adminKey } from '$lib/stores';
	import { outbox, ApiError, type OutboxRow } from '$lib/api';

	let draftAdminKey = $state($adminKey);

	type FilterStatus = 'queued-no-recipient' | 'queued' | 'rejected' | 'sent' | 'failed' | '';
	type FilterKind = '' | 'marketing-outbound' | 'sales-onboarding' | 'sales-usage-recap' | 'sales-upgrade' | 'sales-book-call' | 'sales-escalate-human';

	let statusFilter = $state<FilterStatus>('queued-no-recipient');
	let kindFilter = $state<FilterKind>('');
	let rows = $state<OutboxRow[]>([]);
	let total = $state(0);
	let loading = $state(false);
	let error = $state('');
	let info = $state('');
	let expanded = $state<string>('');
	let mutating = $state<string>('');

	// Per-row reviewer edits (recipient + optional body override).
	let recipientByRow = $state<Record<string, { email: string; name: string }>>({});

	onMount(() => {
		if ($adminKey) void load();
	});

	async function saveAdminKey() {
		adminKey.set(draftAdminKey.trim());
		error = '';
		info = '';
		await load();
	}

	async function load() {
		if (!$adminKey) return;
		loading = true;
		error = '';
		try {
			const r = await outbox.list($adminKey, {
				status: statusFilter || undefined,
				kind: kindFilter || undefined,
				limit: 100,
			});
			rows = r.rows ?? [];
			total = r.total ?? rows.length;
			// Seed per-row recipient drafts.
			for (const row of rows) {
				if (!recipientByRow[row.vertex_id]) {
					recipientByRow[row.vertex_id] = {
						email: row.recipient_email ?? '',
						name: row.recipient_name ?? '',
					};
				}
			}
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			loading = false;
		}
	}

	async function approve(row: OutboxRow) {
		const draft = recipientByRow[row.vertex_id];
		if (!draft?.email?.trim()) {
			error = `recipient email required for ${row.vertex_id}`;
			return;
		}
		mutating = row.vertex_id;
		error = '';
		info = '';
		try {
			const r = await outbox.approve($adminKey, {
				vertex_id: row.vertex_id,
				recipient_email: draft.email.trim(),
				recipient_name: draft.name.trim() || undefined,
			});
			info = r.message || 'approved';
			await load();
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			mutating = '';
		}
	}

	async function reject(row: OutboxRow) {
		const reason = prompt(`Reject ${row.vertex_id}? Add a reason:`, '') ?? '';
		mutating = row.vertex_id;
		error = '';
		info = '';
		try {
			const r = await outbox.reject($adminKey, row.vertex_id, reason);
			info = r.message || 'rejected';
			await load();
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			mutating = '';
		}
	}

	function kindBadge(kind?: string | null) {
		if (!kind) return 'tertiary';
		if (kind.startsWith('sales-escalate')) return 'tertiary';
		if (kind.startsWith('sales-')) return 'primary';
		if (kind === 'marketing-outbound') return 'tertiary';
		return 'tertiary';
	}

	function detectsPlaceholder(text?: string | null): boolean {
		if (!text) return false;
		return /\[\[[A-Z_]+\]\]/.test(text);
	}
</script>

<div class="mx-auto w-full max-w-6xl space-y-6 px-6 py-10">
	<div>
		<p class="text-sm uppercase tracking-wider text-amber-400/80">Operator</p>
		<h1 class="mt-1 text-2xl font-semibold text-etzhayyim-text">Outbox review</h1>
		<p class="mt-1 text-sm text-etzhayyim-secondary">
			Marketing + sales LangGraph nodes write drafts here at
			<code>queued-no-recipient</code>. Fill in the recipient, edit the body if needed, and
			approve to flip to <code>queued</code> for the send worker.
		</p>
	</div>

	{#if !$adminKey}
		<div
			class="mx-auto max-w-xl rounded-2xl border border-amber-700/40 bg-amber-900/10 p-6"
		>
			<h2 class="text-lg font-medium text-etzhayyim-text">Admin key required</h2>
			<p class="mt-2 text-sm text-etzhayyim-secondary">
				Paste your <code>x-yata-admin-key</code> (set in wrangler secrets as
				<code>YATA_AGENT_ADMIN_KEY</code>). Stored locally, never sent except to admin
				surfaces.
			</p>
			<form
				class="mt-4 flex gap-2"
				onsubmit={(e) => {
					e.preventDefault();
					void saveAdminKey();
				}}
			>
				<Input
					type="password"
					placeholder="admin key"
					autocomplete="off"
					bind:value={draftAdminKey}
					class="flex-1"
					blockSize="md"
				/>
				<Button size="md" variant="solid-fill" type="submit">Save</Button>
			</form>
		</div>
	{:else}
		<div class="flex flex-wrap items-center gap-3">
			<label class="flex items-center gap-2 text-xs text-etzhayyim-secondary">
				status
				<select
					class="rounded-md border border-etzhayyim-border bg-etzhayyim-card px-2 py-1 text-sm text-etzhayyim-text"
					bind:value={statusFilter}
					onchange={() => load()}
				>
					<option value="queued-no-recipient">queued-no-recipient</option>
					<option value="queued">queued (approved)</option>
					<option value="rejected">rejected</option>
					<option value="sent">sent</option>
					<option value="failed">failed</option>
					<option value="">all</option>
				</select>
			</label>
			<label class="flex items-center gap-2 text-xs text-etzhayyim-secondary">
				kind
				<select
					class="rounded-md border border-etzhayyim-border bg-etzhayyim-card px-2 py-1 text-sm text-etzhayyim-text"
					bind:value={kindFilter}
					onchange={() => load()}
				>
					<option value="">all kinds</option>
					<option value="marketing-outbound">marketing-outbound</option>
					<option value="sales-onboarding">sales-onboarding</option>
					<option value="sales-usage-recap">sales-usage-recap</option>
					<option value="sales-upgrade">sales-upgrade</option>
					<option value="sales-book-call">sales-book-call</option>
					<option value="sales-escalate-human">sales-escalate-human</option>
				</select>
			</label>
			<Button size="sm" variant="outline" onclick={() => load()} aria-disabled={loading}>
				{loading ? 'Loading…' : 'Refresh'}
			</Button>
			<span class="ml-auto text-xs text-etzhayyim-muted">{total} match · showing {rows.length}</span>
		</div>

		{#if error}
			<NotificationBanner type="error"><span class="font-mono text-xs">{error}</span></NotificationBanner>
		{/if}
		{#if info}
			<NotificationBanner type="success"><span class="text-xs">{info}</span></NotificationBanner>
		{/if}

		{#if loading && rows.length === 0}
			<div class="space-y-3">
				{#each [1, 2, 3] as _}
					<Skeleton class="h-24 w-full" />
				{/each}
			</div>
		{:else if rows.length === 0}
			<EmptyState
				title="No drafts matching this filter"
				description="The cron will populate this list every 6h (marketing) and every hour (sales)."
			/>
		{:else}
			<ul class="space-y-3">
				{#each rows as row (row.vertex_id)}
					{@const isOpen = expanded === row.vertex_id}
					{@const draft = recipientByRow[row.vertex_id] ?? { email: '', name: '' }}
					{@const placeholder = detectsPlaceholder(row.body_text)}
					<li class="rounded-xl border border-etzhayyim-border bg-etzhayyim-card">
						<div class="flex items-start gap-3 px-4 py-3">
							<button
								class="flex-1 text-left"
								type="button"
								onclick={() => (expanded = isOpen ? '' : row.vertex_id)}
							>
								<div class="flex flex-wrap items-center gap-2">
									<Badge type={kindBadge(row.kind)}>{row.kind ?? '—'}</Badge>
									<Badge type={row.status === 'queued' ? 'primary' : 'tertiary'}
										>{row.status ?? '—'}</Badge
									>
									{#if placeholder}
										<Badge type="tertiary"
											><span class="text-amber-300">[[placeholder]]</span></Badge
										>
									{/if}
								</div>
								<p class="mt-1 truncate font-medium text-etzhayyim-text">
									{row.subject ?? '(no subject)'}
								</p>
								<p class="truncate font-mono text-xs text-etzhayyim-muted">
									{row.vertex_id} · {row.scheduled_at
										? new Date(row.scheduled_at).toLocaleString()
										: ''}
								</p>
							</button>
							<span class="text-etzhayyim-muted">{isOpen ? '▾' : '▸'}</span>
						</div>

						{#if isOpen}
							<div class="space-y-4 border-t border-etzhayyim-border px-4 py-4">
								<div class="grid gap-2 sm:grid-cols-2">
									<label class="block text-xs text-etzhayyim-secondary">
										recipient email
										<Input
											type="email"
											placeholder="lead@example.com"
											bind:value={recipientByRow[row.vertex_id].email}
											class="mt-1 w-full font-mono text-sm"
											blockSize="md"
										/>
									</label>
									<label class="block text-xs text-etzhayyim-secondary">
										recipient name (optional)
										<Input
											type="text"
											placeholder="Jane Doe"
											bind:value={recipientByRow[row.vertex_id].name}
											class="mt-1 w-full text-sm"
											blockSize="md"
										/>
									</label>
								</div>

								<div>
									<div class="flex items-center justify-between">
										<p class="text-xs uppercase tracking-wider text-etzhayyim-muted">Body (text)</p>
										{#if placeholder}
											<p class="text-xs text-amber-400">
												Body contains <code>[[PARTNER_NAME]]</code> — edit before approving.
											</p>
										{/if}
									</div>
									<pre
										class="mt-2 max-h-72 overflow-auto whitespace-pre-wrap rounded-md border border-etzhayyim-border bg-black/30 p-3 font-mono text-xs text-etzhayyim-text">{row.body_text ??
											'(no body)'}</pre>
								</div>

								<div class="flex items-center gap-3">
									<Button
										size="md"
										variant="solid-fill"
										onclick={() => approve(row)}
										aria-disabled={mutating === row.vertex_id ||
											!draft.email.trim() ||
											placeholder}
									>
										{mutating === row.vertex_id ? 'Approving…' : 'Approve & queue'}
									</Button>
									<Button
										size="md"
										variant="outline"
										onclick={() => reject(row)}
										aria-disabled={mutating === row.vertex_id}
									>
										Reject
									</Button>
									{#if placeholder}
										<span class="text-xs text-amber-400"
											>Approve disabled until placeholders are filled.</span
										>
									{/if}
								</div>
							</div>
						{/if}
					</li>
				{/each}
			</ul>
		{/if}
	{/if}
</div>
