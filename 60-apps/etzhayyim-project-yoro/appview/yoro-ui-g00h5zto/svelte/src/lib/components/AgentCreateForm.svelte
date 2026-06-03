<script lang="ts">
	import { Badge, Button } from '@etzhayyim/design-system';
	import { playClick, playSuccess } from '$lib/sound';
	import type { CharacterAppearance, CreateAgentInput } from '$lib/auth';
	import { randomCharacterAppearance } from '$lib/auth';

	interface Props {
		oncreate: (input: CreateAgentInput) => Promise<void> | void;
		oncancel?: () => void;
	}

	const { oncreate, oncancel }: Props = $props();

	let appearance = $state<CharacterAppearance>(randomCharacterAppearance());
	let errorMessage = $state('');
	let busy = $state(false);

	function reroll() {
		playClick();
		appearance = randomCharacterAppearance();
	}

	async function submit() {
		errorMessage = '';
		busy = true;
		try {
			await oncreate({ appearance });
			playSuccess();
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to create agent';
		} finally {
			busy = false;
		}
	}

	function skinColor(a: CharacterAppearance): string {
		return `hsl(${a.skinHue * 40}deg ${30 + a.skinLightness * 30}% ${40 + a.skinLightness * 45}%)`;
	}
	function hairColor(a: CharacterAppearance): string {
		return `hsl(${a.hairColorHue * 360}deg 40% ${15 + a.hairColorLightness * 50}%)`;
	}
	function eyeColor(a: CharacterAppearance): string {
		return `hsl(${a.eyeColorHue * 360}deg 60% 45%)`;
	}
	function faceRx(a: CharacterAppearance): number {
		const map: Record<string, number> = { round: 50, oval: 42, square: 20, heart: 38, long: 35, diamond: 30 };
		return map[a.face] ?? 42;
	}
</script>

<div class="flex flex-col gap-4">
	<div class="flex items-center justify-between">
		<h2 class="text-[18px] font-bold text-gv2-text-primary">Create New Agent</h2>
		<Badge value="KAMI Character" variant="accent" />
	</div>

	<!-- Character Preview -->
	<div class="flex flex-col items-center gap-3">
		<div class="rounded-3xl bg-gradient-to-b from-gv2-bg-card to-gv2-bg-primary p-4">
			<svg viewBox="0 0 200 240" class="h-48 w-48">
				{#if appearance.hair !== 'bald' && appearance.hair !== 'buzz'}
					<ellipse cx="100" cy="75" rx={55 + (appearance.hair === 'afro' ? 15 : 0)} ry={60 + (appearance.hair === 'long' ? 30 : appearance.hair === 'afro' ? 20 : 0)} fill={hairColor(appearance)} />
				{/if}
				<ellipse cx="100" cy="100" rx={faceRx(appearance)} ry="55" fill={skinColor(appearance)} />
				{#if true}
				{@const eyeY = 85 + (appearance.eyeHeight - 0.5) * 30}
				{@const eyeW = 8 * appearance.eyeSize}
				{@const eyeH = (appearance.eye === 'narrow' ? 4 : appearance.eye === 'wide' ? 8 : 6) * appearance.eyeSize}
				{@const eyeGap = 15 * appearance.eyeSpacing}
				{@const browY = eyeY - eyeH - 5}
				{@const noseS = 4 * appearance.noseSize}
				{@const mouthW = 12 * appearance.mouthSize}
				<ellipse cx={100 - eyeGap} cy={eyeY} rx={eyeW} ry={eyeH} fill="white" />
				<ellipse cx={100 + eyeGap} cy={eyeY} rx={eyeW} ry={eyeH} fill="white" />
				<circle cx={100 - eyeGap} cy={eyeY} r={eyeH * 0.7} fill={eyeColor(appearance)} />
				<circle cx={100 + eyeGap} cy={eyeY} r={eyeH * 0.7} fill={eyeColor(appearance)} />
				<circle cx={100 - eyeGap} cy={eyeY} r={eyeH * 0.35} fill="#111" />
				<circle cx={100 + eyeGap} cy={eyeY} r={eyeH * 0.35} fill="#111" />
				<line x1={100 - eyeGap - eyeW} y1={browY + appearance.eyebrowAngle * 8} x2={100 - eyeGap + eyeW} y2={browY - appearance.eyebrowAngle * 8} stroke={hairColor(appearance)} stroke-width={2 * appearance.eyebrowThickness} stroke-linecap="round" />
				<line x1={100 + eyeGap - eyeW} y1={browY - appearance.eyebrowAngle * 8} x2={100 + eyeGap + eyeW} y2={browY + appearance.eyebrowAngle * 8} stroke={hairColor(appearance)} stroke-width={2 * appearance.eyebrowThickness} stroke-linecap="round" />
				<ellipse cx="100" cy="108" rx={noseS} ry={noseS * 0.7} fill="none" stroke={skinColor(appearance)} stroke-width="1.5" opacity="0.5" />
				{#if appearance.mouth === 'smile' || appearance.mouth === 'grin'}
					<path d="M{100 - mouthW} 122 Q100 {122 + mouthW * 0.8} {100 + mouthW} 122" fill="none" stroke="#c0392b" stroke-width="2.5" stroke-linecap="round" />
				{:else if appearance.mouth === 'pout'}
					<ellipse cx="100" cy="124" rx={mouthW * 0.6} ry={mouthW * 0.35} fill="#c0392b" />
				{:else}
					<line x1={100 - mouthW} y1="123" x2={100 + mouthW} y2="123" stroke="#c0392b" stroke-width="2" stroke-linecap="round" />
				{/if}
				{#if appearance.hair === 'spiky'}
					{#each [-25, -10, 5, 20] as dx}
						<polygon points="{100 + dx - 8},70 {100 + dx},35 {100 + dx + 8},70" fill={hairColor(appearance)} />
					{/each}
				{:else if appearance.hair !== 'bald'}
					<ellipse cx="100" cy="60" rx={faceRx(appearance) + 5} ry="20" fill={hairColor(appearance)} />
				{/if}
				{#if appearance.accessory1 === 'glasses' || appearance.accessory1 === 'sunglasses'}
					{@const lensFill = appearance.accessory1 === 'sunglasses' ? '#333' : 'none'}
					<circle cx={100 - eyeGap} cy={eyeY} r={eyeW + 3} fill={lensFill} stroke="#555" stroke-width="1.5" opacity="0.8" />
					<circle cx={100 + eyeGap} cy={eyeY} r={eyeW + 3} fill={lensFill} stroke="#555" stroke-width="1.5" opacity="0.8" />
					<line x1={100 - eyeGap + eyeW + 3} y1={eyeY} x2={100 + eyeGap - eyeW - 3} y2={eyeY} stroke="#555" stroke-width="1.5" />
				{/if}
				<rect x="75" y="155" width="50" height="60" rx="15" fill={skinColor(appearance)} opacity="0.3" />
				{/if}
			</svg>
		</div>

		<button type="button"
			class="flex items-center gap-2 rounded-full bg-gv2-bg-card px-5 py-2.5 text-[14px] font-semibold text-gv2-text-primary touch-manipulation active:opacity-80 transition-opacity"
			onclick={reroll}>
			<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 4v6h6M23 20v-6h-6" /><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" /></svg>
			Shuffle
		</button>
	</div>

	<!-- Compact sliders -->
	<div class="flex flex-col gap-2 max-h-[28vh] overflow-y-auto rounded-2xl bg-gv2-bg-card p-3 border border-gv2-border">
		{#each [
			{ label: 'Skin tone', value: appearance.skinLightness, min: 0.15, max: 0.95, step: 0.01, set: (v: number) => { appearance.skinLightness = v; } },
			{ label: 'Eye size', value: appearance.eyeSize, min: 0.5, max: 1.5, step: 0.05, set: (v: number) => { appearance.eyeSize = v; } },
			{ label: 'Eye spacing', value: appearance.eyeSpacing, min: 0.6, max: 1.4, step: 0.05, set: (v: number) => { appearance.eyeSpacing = v; } },
			{ label: 'Brow angle', value: appearance.eyebrowAngle, min: -0.4, max: 0.4, step: 0.05, set: (v: number) => { appearance.eyebrowAngle = v; } },
			{ label: 'Mouth size', value: appearance.mouthSize, min: 0.5, max: 1.5, step: 0.05, set: (v: number) => { appearance.mouthSize = v; } },
			{ label: 'Hair color', value: appearance.hairColorHue, min: 0, max: 1, step: 0.01, set: (v: number) => { appearance.hairColorHue = v; } },
			{ label: 'Eye color', value: appearance.eyeColorHue, min: 0, max: 1, step: 0.01, set: (v: number) => { appearance.eyeColorHue = v; } },
		] as s}
			<div class="flex items-center gap-2">
				<span class="w-20 shrink-0 text-[11px] text-gv2-text-muted">{s.label}</span>
				<input type="range" min={s.min} max={s.max} step={s.step} value={s.value} oninput={(e) => s.set(+(e.target as HTMLInputElement).value)}
					class="flex-1 h-1.5 appearance-none rounded-full bg-gv2-border accent-[#58CC02]" />
			</div>
		{/each}
	</div>

	<!-- Face + Hair chips -->
	<div class="flex flex-wrap gap-1">
		{#each (['round', 'oval', 'square', 'heart', 'long', 'diamond'] as const) as f}
			<button type="button" class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold touch-manipulation {appearance.face === f ? 'bg-[#58CC02] text-white' : 'bg-gv2-bg-input text-gv2-text-muted'}" onclick={() => { playClick(); appearance.face = f; }}>{f}</button>
		{/each}
	</div>
	<div class="flex flex-wrap gap-1">
		{#each (['short', 'medium', 'long', 'buzz', 'curly', 'wavy', 'spiky', 'ponytail', 'bun', 'bald', 'afro', 'mohawk'] as const) as h}
			<button type="button" class="rounded-full px-2.5 py-0.5 text-[10px] font-semibold touch-manipulation {appearance.hair === h ? 'bg-[#58CC02] text-white' : 'bg-gv2-bg-input text-gv2-text-muted'}" onclick={() => { playClick(); appearance.hair = h; }}>{h}</button>
		{/each}
	</div>

	{#if errorMessage}
		<p class="text-[12px] text-red-400 px-1">{errorMessage}</p>
	{/if}

	<div class="flex gap-3">
		{#if oncancel}
			<Button variant="outline" size="lg" onclick={oncancel} class="flex-1 justify-center" disabled={busy}>Cancel</Button>
		{/if}
		<Button variant="solid-fill" size="lg" onclick={submit} class="flex-1 justify-center" disabled={busy}>
			{busy ? 'Generating...' : 'Create Agent'}
		</Button>
	</div>
</div>
