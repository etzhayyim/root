<script lang="ts">
	type HostConfig = {
		'app_name': string;
		'runtime_mode': string;
		'guest_relative_path': string;
		startup_relative_path?: string;
		bundle_id?: string;
	};

	type ScanRoot = {
		path: string;
		'total_bytes': number;
	};

	type ScanSummary = {
		'scanned_roots': ScanRoot[];
		'duplicate_groups': number;
		'reclaimable_bytes': number;
	};

	type GuestAPI = {
		name: string;
		version: string;
		runtime: string;
		endpoints: Array<{ path: string; method: string; description: string }>;
	};

	let hostConfig: HostConfig | null = null;
	let summary: ScanSummary | null = null;
	let guestAPI: GuestAPI | null = null;
	let error = '';

	const load = async () => {
		try {
			const [hostRes, summaryRes, apiRes] = await Promise.all([
				fetch('/api/host-config'),
				fetch('/api/guest-summary'),
				fetch('/api/guest-api')
			]);

			if (!hostRes.ok || !summaryRes.ok || !apiRes.ok) {
				throw new Error(`Failed to load desktop host assets (${hostRes.status}, ${summaryRes.status}, ${apiRes.status})`);
			}

			hostConfig = (await hostRes.json()) as HostConfig;
			summary = (await summaryRes.json()) as ScanSummary;
			guestAPI = (await apiRes.json()) as GuestAPI;
		} catch (err) {
			error = err instanceof Error ? err.message : String(err);
		}
	};

	load();

	const formatBytes = (value: number) =>
		new Intl.NumberFormat('en-US', {
			style: 'unit',
			unit: 'gigabyte',
			maximumFractionDigits: 2
		}).format(value / 1024 / 1024 / 1024);
</script>

<svelte:head>
	<title>Disk Cleaner</title>
</svelte:head>

{#if error}
	<main class="shell">
		<section class="hero panel">
			<p class="eyebrow">Desktop Boot Failed</p>
			<h1>{error}</h1>
		</section>
	</main>
{:else if !hostConfig || !summary || !guestAPI}
	<main class="shell">
		<section class="hero panel">
			<p class="eyebrow">Kotodama Desktop</p>
			<h1>Loading disk cleaner preview</h1>
		</section>
	</main>
{:else}
	<main class="shell">
		<section class="hero panel">
			<div>
				<p class="eyebrow">Kotodama Desktop WASM</p>
				<h1>{hostConfig.app_name}</h1>
				<p class="lede">
					The pure Rust desktop host is serving this UI locally and exposing the desktop-wasm guest ABI as HTTP endpoints.
				</p>
			</div>
			<div class="runtime-card">
				<div>
					<span>Runtime</span>
					<strong>{hostConfig.runtime_mode}</strong>
				</div>
				<div>
					<span>Bundle ID</span>
					<strong>{hostConfig.bundle_id}</strong>
				</div>
				<div>
					<span>Guest Artifact</span>
					<strong>{hostConfig.guest_relative_path}</strong>
				</div>
			</div>
		</section>

		<section class="stats">
			<article class="panel stat">
				<span>Scanned Roots</span>
				<strong>{summary.scanned_roots.length}</strong>
			</article>
			<article class="panel stat">
				<span>Duplicate Groups</span>
				<strong>{summary.duplicate_groups}</strong>
			</article>
			<article class="panel stat">
				<span>Reclaimable</span>
				<strong>{formatBytes(summary.reclaimable_bytes)}</strong>
			</article>
		</section>

		<section class="grid">
			<article class="panel">
				<p class="eyebrow">Scan Summary</p>
				<ul class="roots">
					{#each summary.scanned_roots as root}
						<li>
							<div>
								<strong>{root.path}</strong>
								<span>{formatBytes(root.total_bytes)}</span>
							</div>
						</li>
					{/each}
				</ul>
			</article>

			<article class="panel">
				<p class="eyebrow">Guest ABI</p>
				<ul class="api-list">
					{#each guestAPI.endpoints as endpoint}
						<li>
							<code>{endpoint.method}</code>
							<div>
								<strong>{endpoint.path}</strong>
								<span>{endpoint.description}</span>
							</div>
						</li>
					{/each}
				</ul>
			</article>
		</section>
	</main>
{/if}

<style>
	:global(body) {
		margin: 0;
		font-family: 'Iowan Old Style', 'Palatino Linotype', 'Book Antiqua', Palatino, serif;
		color: #1f1611;
		background:
			radial-gradient(circle at top left, rgba(15, 111, 94, 0.2), transparent 28%),
			radial-gradient(circle at 85% 15%, rgba(192, 122, 61, 0.24), transparent 20%),
			linear-gradient(180deg, #f6efe2 0%, #efe4d1 100%);
	}

	.shell {
		max-width: 1180px;
		margin: 0 auto;
		padding: 32px 20px 56px;
	}

	.panel {
		background: rgba(255, 250, 240, 0.84);
		border: 1px solid rgba(116, 92, 60, 0.18);
		border-radius: 28px;
		box-shadow: 0 24px 80px rgba(41, 31, 23, 0.1);
		backdrop-filter: blur(16px);
	}

	.hero {
		display: grid;
		grid-template-columns: 1.8fr 1fr;
		gap: 24px;
		padding: 28px;
		align-items: start;
	}

	.eyebrow {
		margin: 0 0 12px;
		text-transform: uppercase;
		letter-spacing: 0.16em;
		font-size: 12px;
		color: #0f6f5e;
	}

	h1 {
		margin: 0;
		font-size: clamp(2.6rem, 5vw, 4.8rem);
		line-height: 0.95;
	}

	.lede {
		max-width: 48rem;
		font-size: 1.05rem;
		line-height: 1.7;
	}

	.runtime-card {
		display: grid;
		gap: 14px;
		padding: 18px;
		border-radius: 22px;
		background: linear-gradient(180deg, rgba(15, 111, 94, 0.12), rgba(255, 255, 255, 0.7));
	}

	.runtime-card span,
	.api-list span,
	.roots span {
		display: block;
		color: #6d5b4c;
		font-size: 0.92rem;
	}

	.stats {
		display: grid;
		grid-template-columns: repeat(3, minmax(0, 1fr));
		gap: 18px;
		margin-top: 20px;
	}

	.stat {
		padding: 22px;
	}

	.stat span {
		display: block;
		color: #6d5b4c;
		margin-bottom: 12px;
	}

	.stat strong {
		font-size: 2rem;
	}

	.grid {
		display: grid;
		grid-template-columns: repeat(2, minmax(0, 1fr));
		gap: 18px;
		margin-top: 18px;
	}

	.grid article {
		padding: 22px;
	}

	.roots,
	.api-list {
		list-style: none;
		padding: 0;
		margin: 0;
		display: grid;
		gap: 16px;
	}

	.roots li,
	.api-list li {
		padding: 14px 16px;
		border-radius: 18px;
		background: rgba(255, 255, 255, 0.7);
		border: 1px solid rgba(116, 92, 60, 0.14);
	}

	.api-list li {
		display: grid;
		grid-template-columns: auto 1fr;
		gap: 14px;
		align-items: start;
	}

	code {
		display: inline-flex;
		padding: 5px 8px;
		border-radius: 999px;
		background: #0f6f5e;
		color: #fff8ef;
		font-size: 0.8rem;
		font-family: 'SF Mono', 'Cascadia Code', monospace;
	}

	@media (max-width: 860px) {
		.hero,
		.stats,
		.grid {
			grid-template-columns: 1fr;
		}
	}
</style>
