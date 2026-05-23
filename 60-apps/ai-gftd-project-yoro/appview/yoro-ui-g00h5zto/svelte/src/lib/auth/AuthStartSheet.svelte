<script lang="ts">
	import { Badge, BottomSheet, Button, Card } from '@etzhayyim/design-system';
	import type { CreateAgentInput } from './types.js';
	import { randomCharacterAppearance } from './types.js';
	import type { CharacterAppearance } from './types.js';

	interface Props {
		open: boolean;
		onclose?: () => void;
		onClerk: () => Promise<void> | void;
		onCreateAgent: (input: CreateAgentInput) => Promise<void> | void;
	}

	let {
		open = $bindable(false),
		onclose,
		onClerk,
		onCreateAgent,
	}: Props = $props();

	let step = $state<'owner-auth' | 'character'>('owner-auth');
	let appearance = $state<CharacterAppearance>(randomCharacterAppearance());
	let errorMessage = $state('');
	let busyAction = $state<'clerk' | 'create' | null>(null);

	function closeSheet() {
		open = false;
		step = 'owner-auth';
		errorMessage = '';
		onclose?.();
	}

	// Primary signin is passkey-only (ADR-0074 Phase 1). Ethereum / additional
	// passkeys / OAuth providers are linked methods, added after signin from
	// /settings/account/linked-methods, never as a primary path.
	async function runOwnerAuth(
		action: 'clerk',
		callback: () => Promise<void> | void,
	) {
		errorMessage = '';
		busyAction = action;
		try {
			await callback();
			appearance = randomCharacterAppearance();
			step = 'character';
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Authentication failed';
		} finally {
			busyAction = null;
		}
	}

	function reroll() {
		appearance = randomCharacterAppearance();
	}

	async function submitCharacter() {
		errorMessage = '';
		busyAction = 'create';
		try {
			await onCreateAgent({ appearance });
			closeSheet();
		} catch (error) {
			errorMessage = error instanceof Error ? error.message : 'Failed to create agent';
		} finally {
			busyAction = null;
		}
	}

	// SVG face preview helpers
	function skinColor(a: CharacterAppearance): string {
		return `hsl(${a.skinHue * 40}deg ${30 + a.skinLightness * 30}% ${40 + a.skinLightness * 45}%)`;
	}
	function hairColor(a: CharacterAppearance): string {
		return `hsl(${a.hairColorHue * 360}deg ${40}% ${15 + a.hairColorLightness * 50}%)`;
	}
	function eyeColor(a: CharacterAppearance): string {
		return `hsl(${a.eyeColorHue * 360}deg 60% 45%)`;
	}
	function faceRx(a: CharacterAppearance): number {
		const map: Record<string, number> = { round: 50, oval: 42, square: 20, heart: 38, long: 35, diamond: 30 };
		return map[a.face] ?? 42;
	}

	function slider(label: string, value: number, min: number, max: number, step: number, onChange: (v: number) => void) {
		return { label, value, min, max, step, onChange };
	}
</script>

<BottomSheet bind:open onclose={closeSheet} snapHeight="85vh" class="!bg-[var(--gv2-bg-primary,#111827)]">
	<div class="flex flex-col gap-4 px-4 pb-6 text-[var(--gv2-text-primary,#ffffff)]">

		{#if step === 'owner-auth'}
			<div class="flex flex-col gap-2">
				<div class="flex items-center justify-between gap-3">
					<h3 class="text-[18px] font-semibold">Create Agent</h3>
					<Badge value="Step 1" variant="accent" />
				</div>
				<p class="text-[13px] text-[var(--gv2-text-secondary,#9ca3af)]">
					Authenticate as agent owner first.
				</p>
			</div>

			<Card class="border border-[var(--gv2-border,#334155)] bg-[var(--gv2-bg-card,#111827)] p-4">
				<div class="flex flex-col gap-3">
					<div class="flex items-center justify-between gap-3">
						<div>
							<div class="text-[15px] font-semibold">Passkey</div>
							<div class="text-[12px] text-[var(--gv2-text-secondary,#9ca3af)]">Touch ID / Face ID / device PIN. Phishing-resistant, no password.</div>
						</div>
						<Badge value="Owner" variant="warning" />
					</div>
					<Button variant="solid-fill" size="sm" onclick={() => runOwnerAuth('clerk', onClerk)} disabled={busyAction !== null}>
						{busyAction === 'clerk' ? 'Opening...' : 'Continue with Passkey'}
					</Button>
				</div>
			</Card>

			<p class="text-[11px] text-[var(--gv2-text-muted,#9ca3af)] leading-relaxed">
				After signing in you can link an Ethereum wallet, a Google or Microsoft account, or additional devices from
				<span class="font-mono">Settings → Linked methods</span>.
			</p>

		{:else}
			<!-- Step 2: Character Editor -->
			<div class="flex flex-col gap-2">
				<div class="flex items-center justify-between gap-3">
					<h3 class="text-[18px] font-semibold">Design Your Agent</h3>
					<Badge value="KAMI Character" variant="accent" />
				</div>
				<p class="text-[13px] text-[var(--gv2-text-secondary,#9ca3af)]">
					Create your agent's avatar. Tap shuffle or tweak the sliders. Name and personality are auto-generated.
				</p>
			</div>

			<!-- Character Preview (SVG) -->
			<div class="flex flex-col items-center gap-3">
				<div class="rounded-3xl bg-gradient-to-b from-[var(--gv2-bg-card,#1e293b)] to-[var(--gv2-bg-primary,#111827)] p-4">
					<svg viewBox="0 0 200 240" class="h-48 w-48">
						<!-- Hair back -->
						{#if appearance.hair !== 'bald' && appearance.hair !== 'buzz'}
							<ellipse cx="100" cy="75" rx={55 + (appearance.hair === 'afro' ? 15 : 0)} ry={60 + (appearance.hair === 'long' ? 30 : appearance.hair === 'afro' ? 20 : 0)} fill={hairColor(appearance)} />
						{/if}
						<!-- Face -->
						<ellipse cx="100" cy="100" rx={faceRx(appearance)} ry="55" fill={skinColor(appearance)} />
						<!-- Eyes + Eyebrows + Nose + Mouth -->
						{#if true}
						{@const eyeY = 85 + (appearance.eyeHeight - 0.5) * 30}
						{@const eyeW = 8 * appearance.eyeSize}
						{@const eyeH = (appearance.eye === 'narrow' ? 4 : appearance.eye === 'wide' ? 8 : 6) * appearance.eyeSize}
						{@const eyeGap = 15 * appearance.eyeSpacing}
						<ellipse cx={100 - eyeGap} cy={eyeY} rx={eyeW} ry={eyeH} fill="white" />
						<ellipse cx={100 + eyeGap} cy={eyeY} rx={eyeW} ry={eyeH} fill="white" />
						<circle cx={100 - eyeGap} cy={eyeY} r={eyeH * 0.7} fill={eyeColor(appearance)} />
						<circle cx={100 + eyeGap} cy={eyeY} r={eyeH * 0.7} fill={eyeColor(appearance)} />
						<circle cx={100 - eyeGap} cy={eyeY} r={eyeH * 0.35} fill="#111" />
						<circle cx={100 + eyeGap} cy={eyeY} r={eyeH * 0.35} fill="#111" />
						{@const browY = eyeY - eyeH - 5}
						<line x1={100 - eyeGap - eyeW} y1={browY + appearance.eyebrowAngle * 8} x2={100 - eyeGap + eyeW} y2={browY - appearance.eyebrowAngle * 8} stroke={hairColor(appearance)} stroke-width={2 * appearance.eyebrowThickness} stroke-linecap="round" />
						<line x1={100 + eyeGap - eyeW} y1={browY - appearance.eyebrowAngle * 8} x2={100 + eyeGap + eyeW} y2={browY + appearance.eyebrowAngle * 8} stroke={hairColor(appearance)} stroke-width={2 * appearance.eyebrowThickness} stroke-linecap="round" />
						{@const noseS = 4 * appearance.noseSize}
						<ellipse cx="100" cy="108" rx={noseS} ry={noseS * 0.7} fill="none" stroke={skinColor(appearance)} stroke-width="1.5" opacity="0.5" />
						{@const mouthW = 12 * appearance.mouthSize}
						{#if appearance.mouth === 'smile' || appearance.mouth === 'grin'}
							<path d="M{100 - mouthW} 122 Q100 {122 + mouthW * 0.8} {100 + mouthW} 122" fill="none" stroke="#c0392b" stroke-width="2.5" stroke-linecap="round" />
						{:else if appearance.mouth === 'pout'}
							<ellipse cx="100" cy="124" rx={mouthW * 0.6} ry={mouthW * 0.35} fill="#c0392b" />
						{:else}
							<line x1={100 - mouthW} y1="123" x2={100 + mouthW} y2="123" stroke="#c0392b" stroke-width="2" stroke-linecap="round" />
						{/if}
						<!-- Hair front -->
						{#if appearance.hair === 'spiky'}
							{#each [-25, -10, 5, 20] as dx}
								<polygon points="{100 + dx - 8},70 {100 + dx},35 {100 + dx + 8},70" fill={hairColor(appearance)} />
							{/each}
						{:else if appearance.hair !== 'bald'}
							<ellipse cx="100" cy="60" rx={faceRx(appearance) + 5} ry="20" fill={hairColor(appearance)} />
						{/if}
						<!-- Accessories -->
						{#if appearance.accessory1 === 'glasses' || appearance.accessory1 === 'sunglasses'}
							{@const lensFill = appearance.accessory1 === 'sunglasses' ? '#333' : 'none'}
							<circle cx={100 - eyeGap} cy={eyeY} r={eyeW + 3} fill={lensFill} stroke="#555" stroke-width="1.5" opacity="0.8" />
							<circle cx={100 + eyeGap} cy={eyeY} r={eyeW + 3} fill={lensFill} stroke="#555" stroke-width="1.5" opacity="0.8" />
							<line x1={100 - eyeGap + eyeW + 3} y1={eyeY} x2={100 + eyeGap - eyeW - 3} y2={eyeY} stroke="#555" stroke-width="1.5" />
						{/if}
						{/if}
						{#if appearance.accessory1 === 'hat' || appearance.accessory2 === 'hat'}
							<rect x="60" y="40" width="80" height="12" rx="3" fill="#2c3e50" />
							<rect x="75" y="20" width="50" height="24" rx="8" fill="#2c3e50" />
						{/if}
						<!-- Body hint -->
						<rect x="75" y="155" width="50" height="60" rx="15" fill={skinColor(appearance)} opacity="0.3" />
					</svg>
				</div>

				<!-- Shuffle button -->
				<button
					type="button"
					class="flex items-center gap-2 rounded-full bg-[var(--gv2-bg-card,#1e293b)] px-5 py-2.5 text-[14px] font-semibold text-gv2-text-primary
					       touch-manipulation active:opacity-80 transition-opacity"
					onclick={reroll}
				>
					<svg class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M1 4v6h6M23 20v-6h-6" /><path d="M20.49 9A9 9 0 005.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 013.51 15" /></svg>
					Shuffle
				</button>
			</div>

			<!-- Compact sliders -->
			<div class="flex flex-col gap-2 max-h-[30vh] overflow-y-auto rounded-2xl bg-[var(--gv2-bg-card,#111827)] p-3 border border-[var(--gv2-border,#334155)]">
				{#each [
					slider('Skin tone', appearance.skinLightness, 0.15, 0.95, 0.01, (v) => { appearance.skinLightness = v; }),
					slider('Eye size', appearance.eyeSize, 0.5, 1.5, 0.05, (v) => { appearance.eyeSize = v; }),
					slider('Eye spacing', appearance.eyeSpacing, 0.6, 1.4, 0.05, (v) => { appearance.eyeSpacing = v; }),
					slider('Eye height', appearance.eyeHeight, 0.3, 0.65, 0.01, (v) => { appearance.eyeHeight = v; }),
					slider('Eyebrow angle', appearance.eyebrowAngle, -0.4, 0.4, 0.05, (v) => { appearance.eyebrowAngle = v; }),
					slider('Nose size', appearance.noseSize, 0.5, 1.5, 0.05, (v) => { appearance.noseSize = v; }),
					slider('Mouth size', appearance.mouthSize, 0.5, 1.5, 0.05, (v) => { appearance.mouthSize = v; }),
					slider('Hair color', appearance.hairColorHue, 0, 1, 0.01, (v) => { appearance.hairColorHue = v; }),
					slider('Eye color', appearance.eyeColorHue, 0, 1, 0.01, (v) => { appearance.eyeColorHue = v; }),
					slider('Height', appearance.height, 0.8, 1.2, 0.02, (v) => { appearance.height = v; }),
				] as s}
					<div class="flex items-center gap-2">
						<span class="w-24 shrink-0 text-[11px] text-[var(--gv2-text-muted,#9ca3af)]">{s.label}</span>
						<input type="range" min={s.min} max={s.max} step={s.step} value={s.value} oninput={(e) => s.onChange(+(e.target as HTMLInputElement).value)}
							class="flex-1 h-1.5 appearance-none rounded-full bg-[var(--gv2-border,#334155)] accent-[#58CC02]" />
					</div>
				{/each}
			</div>

			<!-- Type chips -->
			<div class="flex flex-wrap gap-1.5">
				{#each (['round', 'oval', 'square', 'heart', 'long', 'diamond'] as const) as f}
					<button type="button"
						class="rounded-full px-3 py-1 text-[11px] font-semibold touch-manipulation transition-colors
						       {appearance.face === f ? 'bg-[#58CC02] text-white' : 'bg-[var(--gv2-bg-input,#0f172a)] text-gv2-text-muted'}"
						onclick={() => { appearance.face = f; }}>{f}</button>
				{/each}
			</div>
			<div class="flex flex-wrap gap-1.5">
				{#each (['short', 'medium', 'long', 'buzz', 'curly', 'wavy', 'spiky', 'ponytail', 'bun', 'bald', 'afro', 'mohawk'] as const) as h}
					<button type="button"
						class="rounded-full px-3 py-1 text-[11px] font-semibold touch-manipulation transition-colors
						       {appearance.hair === h ? 'bg-[#58CC02] text-white' : 'bg-[var(--gv2-bg-input,#0f172a)] text-gv2-text-muted'}"
						onclick={() => { appearance.hair = h; }}>{h}</button>
				{/each}
			</div>

			<!-- Submit -->
			<Button variant="solid-fill" size="lg" onclick={submitCharacter} disabled={busyAction !== null} class="w-full justify-center">
				{busyAction === 'create' ? 'Generating Agent...' : 'Create Agent'}
			</Button>

			<button type="button"
				class="text-center text-[13px] text-[var(--gv2-text-muted,#9ca3af)] touch-manipulation active:text-[var(--gv2-text-primary)]"
				onclick={() => { step = 'owner-auth'; }}>
				Back to owner authentication
			</button>
		{/if}

		{#if errorMessage}
			<p class="text-[12px] text-red-400">{errorMessage}</p>
		{/if}
	</div>
</BottomSheet>
