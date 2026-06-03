<script lang="ts">
	/**
	 * SplashScreen — Game-style app boot screen with logo, particles, and floating shapes.
	 * Auto-dismisses after content is ready or timeout.
	 */
	import { onMount } from 'svelte';
	import { fade, scale } from 'svelte/transition';
	import { playSuccess } from '@etzhayyim/design-system/audio';
	import { elasticEase } from '@etzhayyim/design-system/motion';

	interface Props {
		/** App display name. */
		appName?: string;
		/** Accent color for logo glow. */
		accent?: string;
		/** Minimum display time in ms (default: 1200). */
		minDuration?: number;
		/** Whether content is ready (splash dismisses when true + minDuration passed). */
		ready?: boolean;
		/** Called when splash finishes. */
		ondismiss?: () => void;
		class?: string;
	}

	let {
		appName = 'etzhayyim',
		accent = '#2563eb',
		minDuration = 1200,
		ready = false,
		ondismiss,
		class: className = '',
	}: Props = $props();

	let mounted = $state(false);
	let visible = $state(true);
	let minTimeElapsed = $state(false);
	let logoReady = $state(false);
	let canvasEl: HTMLCanvasElement | undefined = $state();
	let animId = 0;

	// Floating geometric shapes
	type Shape = {
		x: number;
		y: number;
		vx: number;
		vy: number;
		size: number;
		rotation: number;
		rotSpeed: number;
		type: 'circle' | 'diamond' | 'ring' | 'dot';
		alpha: number;
	};

	function hexToRgb(hex: string): [number, number, number] {
		const h = hex.replace('#', '');
		return [
			parseInt(h.substring(0, 2), 16),
			parseInt(h.substring(2, 4), 16),
			parseInt(h.substring(4, 6), 16),
		];
	}

	onMount(() => {
		mounted = true;
		// Logo entrance delay
		setTimeout(() => { logoReady = true; }, 100);

		// Min display time
		setTimeout(() => { minTimeElapsed = true; }, minDuration);

		// Canvas animation
		if (canvasEl) {
			const ctx = canvasEl.getContext('2d');
			if (ctx) {
				const dpr = window.devicePixelRatio > 1 ? 1.5 : 1;
				canvasEl.width = canvasEl.offsetWidth * dpr;
				canvasEl.height = canvasEl.offsetHeight * dpr;
				const w = canvasEl.width;
				const h = canvasEl.height;

				const shapes: Shape[] = [];
				const types: Shape['type'][] = ['circle', 'diamond', 'ring', 'dot'];
				for (let i = 0; i < 25; i++) {
					shapes.push({
						x: Math.random() * w,
						y: Math.random() * h,
						vx: (Math.random() - 0.5) * 0.8,
						vy: (Math.random() - 0.5) * 0.8,
						size: Math.random() * 12 + 4,
						rotation: Math.random() * Math.PI * 2,
						rotSpeed: (Math.random() - 0.5) * 0.02,
						type: types[Math.floor(Math.random() * types.length)],
						alpha: Math.random() * 0.15 + 0.03,
					});
				}

				let lastTime = 0;
				const FPS = 1000 / 30;

				function draw(now: number) {
					animId = requestAnimationFrame(draw);
					if (!ctx || !canvasEl) return;
					if (now - lastTime < FPS) return;
					lastTime = now;

					const [r, g, b] = hexToRgb(accent);
					ctx.clearRect(0, 0, w, h);

					// Radial gradient pulse
					const pulseT = Math.sin(now * 0.001) * 0.5 + 0.5;
					const grad = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w * 0.5);
					grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${0.06 + pulseT * 0.04})`);
					grad.addColorStop(1, 'transparent');
					ctx.fillStyle = grad;
					ctx.fillRect(0, 0, w, h);

					for (const s of shapes) {
						s.x += s.vx;
						s.y += s.vy;
						s.rotation += s.rotSpeed;
						if (s.x < -20) s.x = w + 20;
						if (s.x > w + 20) s.x = -20;
						if (s.y < -20) s.y = h + 20;
						if (s.y > h + 20) s.y = -20;

						ctx.save();
						ctx.translate(s.x, s.y);
						ctx.rotate(s.rotation);
						ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${s.alpha})`;
						ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${s.alpha * 0.7})`;
						ctx.lineWidth = 1;

						if (s.type === 'circle') {
							ctx.beginPath();
							ctx.arc(0, 0, s.size, 0, Math.PI * 2);
							ctx.fill();
						} else if (s.type === 'diamond') {
							ctx.beginPath();
							ctx.moveTo(0, -s.size);
							ctx.lineTo(s.size * 0.6, 0);
							ctx.lineTo(0, s.size);
							ctx.lineTo(-s.size * 0.6, 0);
							ctx.closePath();
							ctx.fill();
						} else if (s.type === 'ring') {
							ctx.beginPath();
							ctx.arc(0, 0, s.size, 0, Math.PI * 2);
							ctx.stroke();
						} else {
							ctx.beginPath();
							ctx.arc(0, 0, s.size * 0.3, 0, Math.PI * 2);
							ctx.fill();
						}
						ctx.restore();
					}
				}
				animId = requestAnimationFrame(draw);
			}
		}

		return () => { cancelAnimationFrame(animId); };
	});

	// Dismiss when both ready and min time elapsed
	$effect(() => {
		if (minTimeElapsed && ready && visible) {
			playSuccess();
			setTimeout(() => {
				visible = false;
				ondismiss?.();
			}, 300);
		}
	});

	// Fallback: auto-dismiss after 3s even if not ready
	onMount(() => {
		const timer = setTimeout(() => {
			if (visible) {
				visible = false;
				ondismiss?.();
			}
		}, 3000);
		return () => clearTimeout(timer);
	});
</script>

{#if mounted && visible}
	<div
		class="fixed inset-0 z-[200] flex flex-col items-center justify-center bg-[#0a0a0a] {className}"
		out:fade={{ duration: 400 }}
	>
		<!-- Animated background -->
		<canvas
			bind:this={canvasEl}
			class="absolute inset-0 h-full w-full"
			aria-hidden="true"
		></canvas>

		<!-- Logo -->
		<div class="relative z-10 flex flex-col items-center gap-4">
			{#if logoReady}
				<!-- Yoro-kun mascot -->
				<div
					class="splash-yoro"
					in:scale={{ start: 0.3, duration: 600, easing: elasticEase }}
				>
					<img
						src="/yoro-final.svg"
						alt="YORO mascot"
						class="w-28 h-28 drop-shadow-[0_0_24px_rgba(88,204,2,0.4)]"
					/>
				</div>

				<!-- App name -->
				<div
					class="text-center"
					in:scale={{ start: 0.8, duration: 400, delay: 200, easing: elasticEase }}
				>
					<h1 class="text-xl font-bold tracking-wide text-white">{appName}</h1>
					<p class="mt-1 text-xs text-white/40">Powered by etzhayyim</p>
				</div>

				<!-- Loading dots -->
				<div class="flex gap-1.5 mt-4" in:fade={{ delay: 500, duration: 300 }}>
					{#each [0, 1, 2] as i}
						<span
							class="w-1.5 h-1.5 rounded-full bg-white/30"
							style="animation: splash-dot 1.2s ease-in-out {i * 0.2}s infinite"
						></span>
					{/each}
				</div>
			{/if}
		</div>
	</div>
{/if}

<style>
	@keyframes splash-dot {
		0%, 100% { opacity: 0.3; transform: scale(1); }
		50% { opacity: 1; transform: scale(1.4); }
	}
	.splash-yoro {
		animation: splash-yoro-float 2s ease-in-out infinite;
	}
	@keyframes splash-yoro-float {
		0%, 100% { transform: translateY(0); }
		50% { transform: translateY(-8px); }
	}
</style>
