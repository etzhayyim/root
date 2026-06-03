<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import gsap from "gsap";
  import type { SpiritType } from "./spirit-types";

  export let type: SpiritType;
  export let onComplete: () => void = () => {};

  const COLORS: Record<SpiritType, string> = {
    Hero:      "#ef4444",
    Sage:      "#60a5fa",
    Lover:     "#f472b6",
    Caregiver: "#34d399",
  };
  const EMOJIS: Record<SpiritType, string> = {
    Hero: "⚔️", Sage: "🦉", Lover: "🌸", Caregiver: "🌿",
  };
  const NAMES: Record<SpiritType, string> = {
    Hero: "英雄", Sage: "賢者", Lover: "愛人", Caregiver: "養育者",
  };
  const DESCS: Record<SpiritType, string> = {
    Hero:      "使命を帯びし者",
    Sage:      "真実を探求する者",
    Lover:     "美と感性の体現者",
    Caregiver: "慈しみの使者",
  };

  let canvas: HTMLCanvasElement;
  let overlayEl: HTMLDivElement;
  let iconEl: HTMLDivElement;
  let nameEl: HTMLDivElement;
  let subtitleEl: HTMLDivElement;
  let descEl: HTMLDivElement;
  let raf = 0;

  const color = COLORS[type];

  type Particle = { x: number; y: number; vx: number; vy: number; alpha: number; size: number; decay: number };
  let particles: Particle[] = [];

  function burst(cx: number, cy: number, n: number) {
    for (let i = 0; i < n; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 1.5 + Math.random() * 9;
      particles.push({
        x: cx, y: cy,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed - 2.5,
        alpha: 0.7 + Math.random() * 0.3,
        size: 2.5 + Math.random() * 5.5,
        decay: 0.010 + Math.random() * 0.016,
      });
    }
  }

  function tick() {
    if (!canvas) return;
    const ctx = canvas.getContext("2d")!;
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    const hex = color.slice(1);
    const r = parseInt(hex.slice(0, 2), 16);
    const g = parseInt(hex.slice(2, 4), 16);
    const b = parseInt(hex.slice(4, 6), 16);
    particles = particles.filter(p => p.alpha > 0.02);
    for (const p of particles) {
      p.x += p.vx; p.y += p.vy;
      p.vy += 0.18; p.vx *= 0.975;
      p.alpha -= p.decay;
      ctx.beginPath();
      ctx.arc(p.x, p.y, Math.max(0.5, p.size * p.alpha), 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${r},${g},${b},${p.alpha})`;
      ctx.fill();
    }
    if (particles.length > 0) raf = requestAnimationFrame(tick);
  }

  onMount(() => {
    const W = window.innerWidth, H = window.innerHeight;
    canvas.width = W; canvas.height = H;
    const cx = W / 2, cy = H / 2;

    burst(cx, cy, 220);
    setTimeout(() => burst(cx, cy, 120), 140);
    setTimeout(() => burst(cx, cy, 90), 320);
    setTimeout(() => burst(cx, cy, 60), 520);
    raf = requestAnimationFrame(tick);

    const tl = gsap.timeline({
      onComplete: () => gsap.to(overlayEl, {
        opacity: 0, duration: 0.7, delay: 1.8,
        onComplete,
      }),
    });
    tl
      .fromTo(overlayEl, { opacity: 0 }, { opacity: 1, duration: 0.2 })
      .fromTo(iconEl,
        { scale: 0.2, opacity: 0 },
        { scale: 1, opacity: 1, duration: 0.75, ease: "elastic.out(1.3,0.45)" },
        0.15)
      .fromTo(nameEl,
        { y: 28, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.55, ease: "power3.out" },
        0.55)
      .fromTo(subtitleEl,
        { y: 12, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, ease: "power2.out" },
        0.8)
      .fromTo(descEl,
        { y: 8, opacity: 0 },
        { y: 0, opacity: 1, duration: 0.4, ease: "power2.out" },
        0.95);
  });

  onDestroy(() => cancelAnimationFrame(raf));
</script>

<div class="overlay" bind:this={overlayEl} style="--c:{color}">
  <canvas bind:this={canvas} class="pcvs"></canvas>

  <div class="rings">
    <div class="ring r1"></div>
    <div class="ring r2"></div>
    <div class="ring r3"></div>
  </div>

  <div class="content">
    <div class="icon" bind:this={iconEl}>{EMOJIS[type]}</div>
    <div class="type-name" bind:this={nameEl}>{NAMES[type]}</div>
    <div class="subtitle" bind:this={subtitleEl}>{type} Type</div>
    <div class="desc" bind:this={descEl}>{DESCS[type]}</div>
  </div>
</div>

<style>
  .overlay {
    position: fixed; inset: 0; z-index: 200;
    display: flex; align-items: center; justify-content: center;
    background: radial-gradient(ellipse 70% 70% at 50% 50%,
      color-mix(in srgb, var(--c) 22%, #06060f 78%) 0%,
      #06060f 100%);
    pointer-events: none;
  }
  .pcvs {
    position: absolute; inset: 0; width: 100%; height: 100%;
  }
  .rings {
    position: absolute; inset: 0; display: flex; align-items: center; justify-content: center;
  }
  .ring {
    position: absolute; border-radius: 50%;
    border: 1.5px solid var(--c);
    animation: rp 2s ease-out infinite;
  }
  .r1 { width: 160px; height: 160px; animation-delay: 0s; }
  .r2 { width: 280px; height: 280px; animation-delay: 0.25s; }
  .r3 { width: 420px; height: 420px; animation-delay: 0.55s; }
  @keyframes rp {
    from { transform: scale(0.3); opacity: 0.7; }
    to   { transform: scale(1.8); opacity: 0; }
  }
  .content {
    position: relative; z-index: 1;
    text-align: center; display: flex; flex-direction: column; align-items: center; gap: 10px;
  }
  .icon {
    font-size: 88px; line-height: 1; margin-bottom: 4px;
  }
  .type-name {
    font-size: 44px; font-weight: 900; color: #fff;
    text-shadow: 0 0 40px var(--c), 0 0 80px color-mix(in srgb, var(--c) 50%, transparent);
  }
  .subtitle {
    font-size: 14px; color: rgba(255,255,255,0.5); letter-spacing: 0.18em; text-transform: uppercase;
  }
  .desc {
    font-size: 17px; color: rgba(255,255,255,0.75); margin-top: 4px;
    font-style: italic; letter-spacing: 0.02em;
  }
</style>
