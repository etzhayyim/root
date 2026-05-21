<script lang="ts">
	import { onMount } from 'svelte';
	import {
		Button,
		Input,
		Badge,
		EmptyState,
		NotificationBanner,
		Skeleton,
	} from '@gftdcojp/design-system';
	import { apiKey } from '$lib/stores';
	import { storage, ApiError, type BucketRow, type ObjectRow } from '$lib/api';

	let buckets = $state<BucketRow[]>([]);
	let bucketsLoading = $state(true);
	let selected = $state<string>('');
	let objects = $state<ObjectRow[]>([]);
	let objectsLoading = $state(false);
	let error = $state('');
	let uploadName = $state('');
	let signedUrl = $state('');
	let dragging = $state(false);

	onMount(() => {
		void loadBuckets();
	});

	async function loadBuckets() {
		bucketsLoading = true;
		error = '';
		try {
			const r = await storage.buckets($apiKey);
			buckets = r.buckets ?? [];
			if (!selected && buckets.length > 0) selected = buckets[0].name;
			if (selected) void loadObjects(selected);
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			bucketsLoading = false;
		}
	}

	async function loadObjects(bucket: string) {
		objectsLoading = true;
		error = '';
		signedUrl = '';
		try {
			const r = await storage.list($apiKey, bucket, '', 200);
			objects = r.objects ?? [];
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		} finally {
			objectsLoading = false;
		}
	}

	function pickBucket(name: string) {
		selected = name;
		void loadObjects(name);
	}

	async function uploadFile(file: File) {
		if (!selected) return;
		const key = uploadName.trim() || file.name;
		error = '';
		try {
			await storage.putObject($apiKey, selected, key, file);
			uploadName = '';
			await loadObjects(selected);
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		}
	}

	function onFilePicked(ev: Event) {
		const f = (ev.target as HTMLInputElement).files?.[0];
		if (f) void uploadFile(f);
	}

	function onDrop(ev: DragEvent) {
		ev.preventDefault();
		dragging = false;
		const f = ev.dataTransfer?.files?.[0];
		if (f) void uploadFile(f);
	}

	async function deleteObject(key: string) {
		if (!selected) return;
		if (!confirm(`Delete ${key} from ${selected}?`)) return;
		error = '';
		try {
			await storage.delete($apiKey, selected, key);
			await loadObjects(selected);
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		}
	}

	async function sign(key: string) {
		if (!selected) return;
		error = '';
		try {
			const r = await storage.mintSignedUrl($apiKey, selected, key, 3600);
			signedUrl = r.signedUrl;
			void navigator.clipboard.writeText(r.signedUrl).catch(() => undefined);
		} catch (e: any) {
			error = e instanceof ApiError ? `HTTP ${e.status}: ${e.message}` : e?.message || String(e);
		}
	}

	function humanSize(n?: number): string {
		if (!n && n !== 0) return '—';
		if (n < 1024) return `${n} B`;
		if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KiB`;
		if (n < 1024 * 1024 * 1024) return `${(n / 1024 / 1024).toFixed(1)} MiB`;
		return `${(n / 1024 / 1024 / 1024).toFixed(2)} GiB`;
	}
</script>

<div class="mx-auto w-full max-w-6xl space-y-6 px-6 py-10">
	<div>
		<h1 class="text-2xl font-semibold text-gftd-text">Storage</h1>
		<p class="mt-1 text-sm text-gftd-secondary">
			S3-compat object storage. R2-primary with KV fallback for small (&lt; 1 MiB) objects per
			tenant.
		</p>
	</div>

	{#if error}
		<NotificationBanner type="error">
			<span class="font-mono text-xs">{error}</span>
		</NotificationBanner>
	{/if}

	<div class="grid gap-6 lg:grid-cols-[220px_1fr]">
		<!-- Bucket list -->
		<aside class="space-y-2">
			<div class="flex items-center justify-between">
				<h2 class="text-sm font-medium text-gftd-secondary">Buckets</h2>
				<button
					class="text-xs text-gftd-muted hover:text-gftd-text"
					onclick={loadBuckets}
					type="button">refresh</button
				>
			</div>
			{#if bucketsLoading}
				<Skeleton class="h-9 w-full" />
				<Skeleton class="h-9 w-full" />
			{:else if buckets.length === 0}
				<p class="text-xs text-gftd-muted">No buckets yet — PUT to any path creates one.</p>
			{:else}
				<ul class="space-y-1">
					{#each buckets as b (b.name)}
						<li>
							<button
								class={`flex w-full items-center justify-between rounded-md px-3 py-2 text-sm transition
									${selected === b.name ? 'bg-gftd-accent/15 text-gftd-text' : 'text-gftd-secondary hover:bg-white/5'}`}
								onclick={() => pickBucket(b.name)}
								type="button"
							>
								<span class="truncate font-mono text-xs">{b.name}</span>
								{#if b.public_read}
									<Badge type="tertiary">public</Badge>
								{/if}
							</button>
						</li>
					{/each}
				</ul>
			{/if}
		</aside>

		<!-- Object list + upload -->
		<section class="space-y-4">
			{#if selected}
				<div
					class={`rounded-xl border-2 border-dashed bg-gftd-card/40 p-4 transition
						${dragging ? 'border-gftd-accent bg-gftd-accent/10' : 'border-gftd-border'}`}
					ondragover={(e) => {
						e.preventDefault();
						dragging = true;
					}}
					ondragleave={() => (dragging = false)}
					ondrop={onDrop}
					role="region"
					aria-label="Upload drop zone"
				>
					<div class="flex flex-wrap items-center gap-3">
						<div class="flex-1">
							<Input
								blockSize="md"
								placeholder="optional/key/name.png (defaults to filename)"
								bind:value={uploadName}
								class="w-full font-mono text-sm"
							/>
						</div>
						<label
							class="cursor-pointer rounded-md border border-gftd-border bg-gftd-card px-4 py-2 text-sm text-gftd-text hover:bg-white/5"
						>
							Choose file
							<input type="file" class="hidden" onchange={onFilePicked} />
						</label>
					</div>
					<p class="mt-2 text-xs text-gftd-muted">
						…or drag a file anywhere on this strip. PUTs to
						<code class="font-mono">/storage/v1/object/{selected}/&lt;key&gt;</code>.
					</p>
				</div>

				{#if signedUrl}
					<NotificationBanner type="success">
						Signed URL copied to clipboard (expires in 1h):
						<code class="ml-2 break-all font-mono text-xs">{signedUrl}</code>
					</NotificationBanner>
				{/if}

				<div class="rounded-xl border border-gftd-border bg-gftd-card">
					<div
						class="flex items-center justify-between border-b border-gftd-border px-4 py-2 text-sm text-gftd-secondary"
					>
						<span>{objects.length} object(s) in <code class="font-mono">{selected}</code></span>
					</div>
					{#if objectsLoading}
						<div class="space-y-2 p-4">
							{#each [1, 2, 3] as _}
								<Skeleton class="h-6 w-full" />
							{/each}
						</div>
					{:else if objects.length === 0}
						<div class="px-6 py-10">
							<EmptyState
								title="No objects"
								description="Upload one via drag-drop or PUT to /storage/v1/object/{selected}/<key>."
							/>
						</div>
					{:else}
						<table class="w-full border-collapse text-sm">
							<thead>
								<tr class="border-b border-gftd-border bg-black/20 text-left text-gftd-muted">
									<th class="px-4 py-2 font-medium">Key</th>
									<th class="px-4 py-2 font-medium">Size</th>
									<th class="px-4 py-2 font-medium">Tier</th>
									<th class="px-4 py-2 font-medium">Updated</th>
									<th class="px-4 py-2 font-medium" />
								</tr>
							</thead>
							<tbody>
								{#each objects as o (o.name)}
									<tr class="border-b border-gftd-border/60 last:border-0">
										<td class="truncate px-4 py-2 font-mono text-xs text-gftd-text">{o.name}</td>
										<td class="px-4 py-2 text-xs text-gftd-secondary">{humanSize(o.size)}</td>
										<td class="px-4 py-2 text-xs">
											<Badge type={o.source === 'r2' ? 'primary' : 'tertiary'}>
												{o.source ?? '—'}
											</Badge>
										</td>
										<td class="px-4 py-2 text-xs text-gftd-muted">
											{o.updatedAt ? new Date(o.updatedAt).toLocaleString() : '—'}
										</td>
										<td class="px-4 py-2 text-right">
											<button
												class="px-2 text-xs text-gftd-accent hover:underline"
												onclick={() => sign(o.name)}
												type="button">sign</button
											>
											<button
												class="px-2 text-xs text-red-400 hover:underline"
												onclick={() => deleteObject(o.name)}
												type="button">delete</button
											>
										</td>
									</tr>
								{/each}
							</tbody>
						</table>
					{/if}
				</div>
			{:else}
				<EmptyState
					title="Pick a bucket"
					description="Buckets are auto-created on first PUT. Select a bucket on the left to browse its objects."
				/>
			{/if}
		</section>
	</div>
</div>
