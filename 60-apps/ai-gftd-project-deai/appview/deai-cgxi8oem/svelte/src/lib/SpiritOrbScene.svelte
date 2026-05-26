<script lang="ts">
  import { T, useTask, useThrelte } from "@threlte/core";
  import { onMount } from "svelte";
  import * as THREE from "three";
  import type { SpiritType } from "./spirit-types";
  import type { EmotionVec5 } from "./spirit-match";

  const { renderer } = useThrelte();
  onMount(() => {
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  });

  export let type: SpiritType = "Hero";
  export let emotionVec: EmotionVec5 = [0.6, 0.6, 0.6, 0.6, 0.6];
  export let interactive = true;

  const SPIRIT_HEX: Record<SpiritType, number> = {
    Hero:      0xef4444,
    Sage:      0x60a5fa,
    Lover:     0xf472b6,
    Caregiver: 0x34d399,
  };

  $: color = SPIRIT_HEX[type] ?? 0xc084fc;
  $: glowColor = color;

  // Core orb mesh ref
  let coreRef: THREE.Mesh;
  let ringRef: THREE.Group;
  let particlesRef: THREE.Points;
  let t = 0;

  // Build particle ring once
  const PARTICLE_COUNT = 120;
  const positions = new Float32Array(PARTICLE_COUNT * 3);
  const sizes = new Float32Array(PARTICLE_COUNT);
  for (let i = 0; i < PARTICLE_COUNT; i++) {
    const angle = (i / PARTICLE_COUNT) * Math.PI * 2;
    const radius = 1.35 + Math.sin(i * 0.7) * 0.18;
    const spread = (Math.random() - 0.5) * 0.22;
    positions[i * 3]     = Math.cos(angle) * radius;
    positions[i * 3 + 1] = spread;
    positions[i * 3 + 2] = Math.sin(angle) * radius;
    sizes[i] = 0.02 + Math.random() * 0.04;
  }
  const particleGeo = new THREE.BufferGeometry();
  particleGeo.setAttribute("position", new THREE.BufferAttribute(positions, 3));

  // Floating secondary orbs (micro-moons)
  const MOON_COUNT = 5;
  const moons = Array.from({ length: MOON_COUNT }, (_, i) => ({
    angle: (i / MOON_COUNT) * Math.PI * 2,
    r: 1.7 + (i % 2) * 0.25,
    speed: 0.3 + i * 0.07,
    size: 0.04 + (emotionVec[i % 5] ?? 0.5) * 0.06,
    elevation: (Math.random() - 0.5) * 0.6,
  }));

  useTask((delta) => {
    t += delta;
    if (coreRef) {
      coreRef.rotation.y = t * 0.4;
      coreRef.rotation.x = Math.sin(t * 0.2) * 0.15;
    }
    if (ringRef) {
      ringRef.rotation.y = t * 0.25;
      ringRef.rotation.x = Math.sin(t * 0.15) * 0.08;
    }
  });

  // Camera pos
  const camPos: [number, number, number] = [0, 0, 4];
</script>

<!-- Camera -->
<T.PerspectiveCamera makeDefault position={camPos} fov={45} />

<!-- Lights -->
<T.AmbientLight intensity={0.15} />
<T.PointLight position={[3, 4, 3]} intensity={2.2} color={color} distance={12} />
<T.PointLight position={[-3, -2, 2]} intensity={0.9} color={0xffffff} distance={10} />
<T.PointLight position={[0, 0, 5]} intensity={0.6} color={color} distance={8} />

<!-- Core sphere -->
<T.Mesh bind:ref={coreRef}>
  <T.SphereGeometry args={[1, 64, 64]} />
  <T.MeshStandardMaterial
    color={color}
    emissive={color}
    emissiveIntensity={0.55}
    roughness={0.18}
    metalness={0.6}
    transparent
    opacity={0.92}
  />
</T.Mesh>

<!-- Inner glow sphere (larger, transparent) -->
<T.Mesh>
  <T.SphereGeometry args={[1.08, 32, 32]} />
  <T.MeshStandardMaterial
    color={color}
    emissive={color}
    emissiveIntensity={0.22}
    roughness={1}
    metalness={0}
    transparent
    opacity={0.18}
    side={THREE.BackSide}
  />
</T.Mesh>

<!-- Particle ring -->
<T.Group bind:ref={ringRef}>
  <T.Points geometry={particleGeo}>
    <T.PointsMaterial
      color={color}
      size={0.045}
      sizeAttenuation
      transparent
      opacity={0.75}
      blending={THREE.AdditiveBlending}
      depthWrite={false}
    />
  </T.Points>

  <!-- Emotion-axis micro-moons -->
  {#each moons as moon, i}
    {@const mx = Math.cos(moon.angle) * moon.r}
    {@const mz = Math.sin(moon.angle) * moon.r}
    <T.Mesh position={[mx, moon.elevation, mz]}>
      <T.SphereGeometry args={[moon.size, 12, 12]} />
      <T.MeshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={0.9}
        roughness={0.3}
        metalness={0.5}
        transparent
        opacity={0.85}
      />
    </T.Mesh>
  {/each}
</T.Group>

<!-- Equatorial ring torus -->
<T.Mesh rotation={[Math.PI / 2, 0, 0]}>
  <T.TorusGeometry args={[1.38, 0.012, 8, 120]} />
  <T.MeshStandardMaterial
    color={color}
    emissive={color}
    emissiveIntensity={1.2}
    roughness={0.1}
    transparent
    opacity={0.5}
    blending={THREE.AdditiveBlending}
    depthWrite={false}
  />
</T.Mesh>
