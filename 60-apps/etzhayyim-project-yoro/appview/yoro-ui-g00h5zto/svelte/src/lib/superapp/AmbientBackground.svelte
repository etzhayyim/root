<script lang="ts">
	/**
	 * AmbientBackground — Nintendo Switch 2 style floating particle + shape background.
	 * Canvas 2D (GPU lightweight). Mood-reactive. Geometric shapes float and rotate.
	 * Reduced-motion: falls back to static gradient.
	 */
	import { onMount } from 'svelte';
	import { vibesTuning, MOOD_META } from '../tuner/vibes-store.js';

	interface Props {
		class?: string;
	}

	let { class: className = '' }: Props = $props();

	let canvasEl: HTMLCanvasElement | undefined = $state();
	let animId = 0;

	type Particle = {
		x: number;
		y: number;
		vx: number;
		vy: number;
		r: number;
		alpha: number;
	};

	type FloatingShape = {
		x: number;
		y: number;
		vx: number;
		vy: number;
		size: number;
		rotation: number;
		rotSpeed: number;
		shape: number; // 0=circle, 1=diamond, 2=ring, 3=rounded-rect
		alpha: number;
		pulsePhase: number;
	};

	const MAX_PARTICLES = 30;
	const MAX_SHAPES = 8;

	function hexToRgb(hex: string): [number, number, number] {
		const h = hex.replace('#', '');
		return [
			parseInt(h.substring(0, 2), 16),
			parseInt(h.substring(2, 4), 16),
			parseInt(h.substring(4, 6), 16),
		];
	}

	function initObjects(w: number, h: number): { particles: Particle[]; shapes: FloatingShape[] } {
		const particles: Particle[] = [];
		for (let i = 0; i < MAX_PARTICLES; i++) {
			particles.push({
				x: Math.random() * w,
				y: Math.random() * h,
				vx: (Math.random() - 0.5) * 0.3,
				vy: (Math.random() - 0.5) * 0.3,
				r: Math.random() * 2.5 + 0.5,
				alpha: Math.random() * 0.2 + 0.03,
			});
		}

		const shapes: FloatingShape[] = [];
		for (let i = 0; i < MAX_SHAPES; i++) {
			shapes.push({
				x: Math.random() * w,
				y: Math.random() * h,
				vx: (Math.random() - 0.5) * 0.15,
				vy: (Math.random() - 0.5) * 0.15,
				size: Math.random() * 30 + 15,
				rotation: Math.random() * Math.PI * 2,
				rotSpeed: (Math.random() - 0.5) * 0.005,
				shape: Math.floor(Math.random() * 4),
				alpha: Math.random() * 0.04 + 0.01,
				pulsePhase: Math.random() * Math.PI * 2,
			});
		}

		return { particles, shapes };
	}

	onMount(() => {
		const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
		if (prefersReducedMotion || !canvasEl) return;

		const ctx = canvasEl.getContext('2d');
		if (!ctx) return;

		let objects: ReturnType<typeof initObjects> | null = null;

		function resize() {
			if (!canvasEl) return;
			const dpr = window.devicePixelRatio > 1 ? 1.5 : 1;
			canvasEl.width = canvasEl.offsetWidth * dpr;
			canvasEl.height = canvasEl.offsetHeight * dpr;
			if (!objects) objects = initObjects(canvasEl.width, canvasEl.height);
		}
		resize();
		window.addEventListener('resize', resize);

		let lastTime = 0;
		const FPS_INTERVAL = 1000 / 24; // 24fps

		function draw(now: number) {
			animId = requestAnimationFrame(draw);
			if (!ctx || !canvasEl || !objects) return;

			const elapsed = now - lastTime;
			if (elapsed < FPS_INTERVAL) return;
			lastTime = now - (elapsed % FPS_INTERVAL);

			const w = canvasEl.width;
			const h = canvasEl.height;
			const mood = $vibesTuning.mood;
			const energy = $vibesTuning.energy;
			const color = MOOD_META[mood]?.color ?? '#60a5fa';
			const [r, g, b] = hexToRgb(color);
			const speedMult = 0.3 + (energy / 100) * 1.0;

			ctx.clearRect(0, 0, w, h);

			// Background gradient
			const grad = ctx.createRadialGradient(w / 2, h / 2, 0, w / 2, h / 2, w * 0.7);
			grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${0.02 + energy * 0.0004})`);
			grad.addColorStop(1, 'transparent');
			ctx.fillStyle = grad;
			ctx.fillRect(0, 0, w, h);

			// Floating shapes (large, slow, very subtle)
			for (const s of objects.shapes) {
				s.x += s.vx * speedMult;
				s.y += s.vy * speedMult;
				s.rotation += s.rotSpeed * speedMult;
				if (s.x < -50) s.x = w + 50;
				if (s.x > w + 50) s.x = -50;
				if (s.y < -50) s.y = h + 50;
				if (s.y > h + 50) s.y = -50;

				const pulse = Math.sin(now * 0.001 + s.pulsePhase) * 0.3 + 0.7;
				const alpha = s.alpha * pulse;

				ctx.save();
				ctx.translate(s.x, s.y);
				ctx.rotate(s.rotation);
				ctx.strokeStyle = `rgba(${r}, ${g}, ${b}, ${alpha})`;
				ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${alpha * 0.3})`;
				ctx.lineWidth = 1;

				const sz = s.size;
				if (s.shape === 0) {
					ctx.beginPath();
					ctx.arc(0, 0, sz / 2, 0, Math.PI * 2);
					ctx.stroke();
				} else if (s.shape === 1) {
					ctx.beginPath();
					ctx.moveTo(0, -sz / 2);
					ctx.lineTo(sz / 3, 0);
					ctx.lineTo(0, sz / 2);
					ctx.lineTo(-sz / 3, 0);
					ctx.closePath();
					ctx.stroke();
				} else if (s.shape === 2) {
					ctx.beginPath();
					ctx.arc(0, 0, sz / 2, 0, Math.PI * 2);
					ctx.fill();
				} else {
					const hs = sz / 2;
					ctx.beginPath();
					ctx.roundRect(-hs, -hs, sz, sz * 0.6, sz * 0.15);
					ctx.stroke();
				}
				ctx.restore();
			}

			// Particles (small dots)
			for (const p of objects.particles) {
				p.x += p.vx * speedMult;
				p.y += p.vy * speedMult;
				if (p.x < -10) p.x = w + 10;
				if (p.x > w + 10) p.x = -10;
				if (p.y < -10) p.y = h + 10;
				if (p.y > h + 10) p.y = -10;

				ctx.beginPath();
				ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
				ctx.fillStyle = `rgba(${r}, ${g}, ${b}, ${p.alpha})`;
				ctx.fill();
			}
		}

		animId = requestAnimationFrame(draw);

		return () => {
			cancelAnimationFrame(animId);
			window.removeEventListener('resize', resize);
		};
	});
</script>

<canvas
	bind:this={canvasEl}
	class="pointer-events-none absolute inset-0 h-full w-full {className}"
	aria-hidden="true"
></canvas>
