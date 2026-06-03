<script lang="ts">
	/**
	 * ActorGame — game mode renderer.
	 *
	 * Loads Godot or HTML games via assets served from /_game/assets/*,
	 * sets up the JS bridge (window.etzhayyimBridgeSend → /api/game/{convo}),
	 * and renders a floating leaderboard overlay during gameplay.
	 */
	import { onMount, onDestroy } from 'svelte';
	import type { ActorProfile, ActorGameConfig } from './types.js';
	import { setupGameBridge } from './game-bridge.js';

	interface Props {
		profile: ActorProfile;
		appBaseUrl: string;
	}

	let { profile, appBaseUrl }: Props = $props();

	let containerEl: HTMLDivElement | undefined = $state();
	let loading = $state(true);
	let loadError = $state('');
	let progress = $state(0);
	let playerScore = $state(0);
	let showLeaderboard = $state(true);
	let leaderboard = $state<{ name: string; score: number; isPlayer?: boolean }[]>([
		{ name: 'You', score: 0, isPlayer: true },
	]);
	let cleanupBridge: (() => void) | undefined;
	let disposeEngine: (() => void) | undefined;

	const gameConfig = $derived(profile.gameConfig as ActorGameConfig | undefined);
	const assetsBase = $derived(gameConfig?.assetsBaseUrl ?? `${appBaseUrl}/_game/assets`);
	const entry = $derived(gameConfig?.entry ?? '');
	const runtime = $derived(gameConfig?.runtime ?? 'godot');

	function updateScore(score: number) {
		playerScore = score;
		const idx = leaderboard.findIndex((e) => e.isPlayer);
		if (idx !== -1) {
			leaderboard[idx].score = score;
			leaderboard = [...leaderboard].sort((a, b) => b.score - a.score);
		}
		fetch(`${appBaseUrl}/api/game/score`, {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ action: 'submit', score }),
		}).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/actor/ActorGame.svelte: suppressed async error", error); });
	}

	onMount(async () => {
		if (!gameConfig || !entry) {
			loadError = 'Game configuration missing';
			loading = false;
			return;
		}

		cleanupBridge = setupGameBridge(appBaseUrl);

		const origReceive = window.etzhayyimBridgeReceive;
		window.etzhayyimBridgeReceive = (json: string) => {
			origReceive?.(json);
			try {
				const msg = JSON.parse(json);
				if (msg.convo === 'score' && typeof msg.payload?.value === 'number') {
					updateScore(msg.payload.value);
				}
			} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/actor/ActorGame.svelte: suppressed error", error); }
		};

		(window as any).onGameScore = (score: number) => updateScore(score);

		try {
			const resp = await fetch(`${appBaseUrl}/api/game/score`, {
				method: 'POST',
				headers: { 'Content-Type': 'application/json' },
				body: JSON.stringify({ action: 'leaderboard', limit: 10 }),
			});
			if (resp.ok) {
				const data = await resp.json();
				if (Array.isArray(data.entries)) {
					leaderboard = [
						{ name: 'You', score: 0, isPlayer: true },
						...data.entries.map((e: any) => ({ name: e.display_name || e.player_id, score: e.value || 0 })),
					].sort((a, b) => b.score - a.score);
				}
			}
		} catch (error) { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/actor/ActorGame.svelte: suppressed error", error); }

		if (runtime === 'html') {
			loading = false;
			return;
		}

		const scriptUrl = `${assetsBase}/${entry}/${entry}.js`;
		const script = document.createElement('script');
		script.src = scriptUrl;
		script.onload = () => {
			try {
				const EngineCtor = (window as any).Engine;
				if (typeof EngineCtor !== 'function') {
					loadError = 'Godot Engine constructor not found';
					loading = false;
					return;
				}
				const engine = new EngineCtor({
					args: [],
					canvasId: 'game-canvas',
					canvasResizePolicy: 2,
					executable: `${assetsBase}/${entry}/${entry}`,
					fileSizes: {},
					onProgress: (current: number, total: number) => {
						if (total > 0) progress = Math.round((current / total) * 100);
					},
				});
				engine
					.startGame()
					.then(() => {
						loading = false;
						disposeEngine = () => {
							if (typeof engine.requestQuit === 'function') engine.requestQuit();
						};
					})
					.catch((e: Error) => {
						loadError = e.message || 'Failed to start game engine';
						loading = false;
					});
			} catch (e) {
				loadError = e instanceof Error ? e.message : 'Engine initialization failed';
				loading = false;
			}
		};
		script.onerror = () => {
			loadError = 'Failed to load game engine script';
			loading = false;
		};
		document.body.appendChild(script);
	});

	onDestroy(() => {
		cleanupBridge?.();
		disposeEngine?.();
		delete (window as any).onGameScore;
	});
</script>

<div class="flex h-full w-full flex-col overflow-hidden" bind:this={containerEl}>
	{#if loadError}
		<div class="flex h-full items-center justify-center px-8">
			<div class="flex flex-col items-center gap-3 text-center">
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-[var(--gv2-bg-hover,#252525)]">
					<svg class="h-8 w-8 text-[var(--gv2-text-muted,#666)]" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
						<circle cx="12" cy="12" r="10" />
						<path d="M12 8v4M12 16h.01" />
					</svg>
				</div>
				<p class="text-[15px] font-semibold text-[var(--gv2-text-primary,#fff)]">Game failed to load</p>
				<p class="text-[13px] text-[var(--gv2-text-muted,#777)] max-w-[300px] break-words">{loadError}</p>
				<a
					href={appBaseUrl}
					target="_blank"
					rel="noopener"
					class="mt-2 rounded-xl bg-[var(--gv2-accent,#3b82f6)] px-6 py-2.5 text-[14px] font-semibold text-white touch-manipulation active:opacity-80"
				>Open in new tab</a>
			</div>
		</div>
	{:else}
		<div class="relative flex-1 min-h-0 bg-black">
			{#if runtime === 'html' && entry}
				<iframe
					src="{assetsBase}/{entry}/index.html"
					title={profile.name}
					class="absolute inset-0 h-full w-full border-0"
					sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-pointer-lock"
				></iframe>
			{:else}
				{#if loading}
					<div class="flex h-full flex-col items-center justify-center">
						<div class="h-8 w-8 animate-spin rounded-full border-2 border-[var(--gv2-accent,#3b82f6)] border-t-transparent"></div>
						<span class="mt-3 text-[13px] text-[var(--gv2-text-muted,#777)]">Loading game...</span>
						{#if progress > 0}
							<div class="mt-3 h-1 w-32 overflow-hidden rounded-full bg-[var(--gv2-bg-hover,#252525)]">
								<div class="h-full bg-[var(--gv2-accent,#3b82f6)] transition-all duration-300" style="width: {progress}%"></div>
							</div>
							<span class="mt-1 text-[11px] text-[var(--gv2-text-muted,#777)]">{progress}%</span>
						{/if}
					</div>
				{/if}
				<canvas
					id="game-canvas"
					class="absolute inset-0 h-full w-full {loading ? 'pointer-events-none opacity-0' : 'opacity-100'}"
				></canvas>
			{/if}

			{#if !loading && !loadError && playerScore > 0}
				<div class="absolute bottom-3 left-3 rounded-xl bg-black/70 px-3 py-2 text-white backdrop-blur-sm">
					<div class="text-[10px] font-bold uppercase tracking-widest text-[var(--gv2-text-muted,#777)]">Score</div>
					<div class="text-lg font-black">{playerScore}</div>
				</div>
			{/if}

			{#if !loading && !loadError}
				<button
					type="button"
					class="absolute top-3 right-3 flex h-10 w-10 items-center justify-center rounded-full bg-black/70 text-white backdrop-blur-sm touch-manipulation active:opacity-80"
					onclick={() => showLeaderboard = !showLeaderboard}
					aria-label="Toggle leaderboard"
				>
					<svg class="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
						<path d="M10 2a1 1 0 011 1v1.323l3.954.99a1 1 0 01.546 1.687l-2.5 2.5a1 1 0 01-.707.293H7.707a1 1 0 01-.707-.293l-2.5-2.5A1 1 0 015.046 5.313L9 4.323V3a1 1 0 011-1zM5.5 16a1.5 1.5 0 01-3 0V12a1.5 1.5 0 013 0v4zm5.5 0a1.5 1.5 0 01-3 0V10a1.5 1.5 0 013 0v6zm5.5 0a1.5 1.5 0 01-3 0V14a1.5 1.5 0 013 0v2z" />
					</svg>
				</button>
			{/if}

			{#if showLeaderboard && !loading && !loadError && leaderboard.length > 1}
				<div class="absolute top-14 right-3 w-48 rounded-xl bg-black/80 p-3 text-white backdrop-blur-sm">
					<div class="mb-2 text-[11px] font-bold uppercase tracking-widest text-[var(--gv2-text-muted,#777)]">Leaderboard</div>
					{#each leaderboard.slice(0, 5) as entry, i}
						<div class="flex items-center justify-between py-1 text-[12px] {entry.isPlayer ? 'font-bold text-[var(--gv2-accent,#3b82f6)]' : 'text-[var(--gv2-text-secondary,#aaa)]'}">
							<span class="truncate">{i + 1}. {entry.name}</span>
							<span class="ml-2 tabular-nums">{entry.score}</span>
						</div>
					{/each}
				</div>
			{/if}
		</div>
	{/if}
</div>
