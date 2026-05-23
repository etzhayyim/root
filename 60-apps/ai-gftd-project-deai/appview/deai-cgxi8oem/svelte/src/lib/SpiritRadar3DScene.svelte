<script lang="ts">
  import { T, useTask, useThrelte } from "@threlte/core";
  import { onMount } from "svelte";
  import * as THREE from "three";
  import type { EmotionVec5 } from "./spirit-match";

  const { renderer } = useThrelte();
  onMount(() => {
    renderer.setClearColor(0x000000, 0);
    renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  });

  export let selfVec: EmotionVec5 = [0.5, 0.5, 0.5, 0.5, 0.5];
  export let partnerVec: EmotionVec5 = [0.5, 0.5, 0.5, 0.5, 0.5];
  export let accentColor = "#ef4444";

  const SCALE = 1.4;

  function makeShape(vec: EmotionVec5, r: number): THREE.Shape {
    const shape = new THREE.Shape();
    const pts = vec.map((v, i) => {
      const angle = (i / 5) * Math.PI * 2 - Math.PI / 2;
      return new THREE.Vector2(
        Math.cos(angle) * v * r,
        Math.sin(angle) * v * r,
      );
    });
    shape.moveTo(pts[0].x, pts[0].y);
    pts.slice(1).forEach(p => shape.lineTo(p.x, p.y));
    shape.closePath();
    return shape;
  }

  $: selfShape    = makeShape(selfVec,    SCALE);
  $: partnerShape = makeShape(partnerVec, SCALE);

  const extOpts: THREE.ExtrudeGeometryOptions = {
    depth: 0.04, bevelEnabled: true, bevelSize: 0.02, bevelThickness: 0.01, bevelSegments: 2,
  };

  $: selfGeo    = new THREE.ExtrudeGeometry(selfShape,    extOpts);
  $: partnerGeo = new THREE.ExtrudeGeometry(partnerShape, extOpts);

  // Grid rings (3 regular pentagons)
  function makeRingGeo(frac: number): THREE.BufferGeometry {
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 5; i++) {
      const angle = (i / 5) * Math.PI * 2 - Math.PI / 2;
      pts.push(new THREE.Vector3(Math.cos(angle) * frac * SCALE, Math.sin(angle) * frac * SCALE, 0));
    }
    return new THREE.BufferGeometry().setFromPoints(pts);
  }
  const ringGeos = [0.33, 0.66, 1.0].map(makeRingGeo);

  // Axis lines
  const axisGeos = Array.from({ length: 5 }, (_, i) => {
    const angle = (i / 5) * Math.PI * 2 - Math.PI / 2;
    return new THREE.BufferGeometry().setFromPoints([
      new THREE.Vector3(0, 0, 0),
      new THREE.Vector3(Math.cos(angle) * SCALE, Math.sin(angle) * SCALE, 0),
    ]);
  });

  // Group ref for rotation
  let groupRef: THREE.Group;
  let t = 0;

  useTask((delta) => {
    t += delta;
    if (groupRef) {
      groupRef.rotation.y = t * 0.55;
      groupRef.rotation.x = Math.sin(t * 0.3) * 0.35;
    }
  });

  const accentHex = parseInt(accentColor.replace("#", ""), 16);

  const camPos: [number, number, number] = [0, 0, 4.2];
</script>

<T.PerspectiveCamera makeDefault position={camPos} fov={38} />
<T.AmbientLight intensity={0.5} />
<T.PointLight position={[2, 3, 3]} intensity={1.8} color={accentHex} />
<T.PointLight position={[-2, -2, 2]} intensity={0.8} color={0xffffff} />

<T.Group bind:ref={groupRef}>
  <!-- Grid rings -->
  {#each ringGeos as geo}
    <T.Line {geo}>
      <T.LineBasicMaterial color={0xffffff} transparent opacity={0.1} />
    </T.Line>
  {/each}

  <!-- Axis lines -->
  {#each axisGeos as geo}
    <T.Line {geo}>
      <T.LineBasicMaterial color={0xffffff} transparent opacity={0.08} />
    </T.Line>
  {/each}

  <!-- Self pentagon (violet, dashed look via wireframe) -->
  <T.Mesh geometry={selfGeo} position={[0, 0, -0.02]}>
    <T.MeshStandardMaterial
      color={0xc084fc}
      emissive={0xc084fc}
      emissiveIntensity={0.45}
      transparent opacity={0.22}
      side={THREE.DoubleSide}
    />
  </T.Mesh>
  <!-- Self outline -->
  <T.LineLoop geometry={new THREE.BufferGeometry().setFromPoints(
    selfVec.map((v, i) => {
      const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
      return new THREE.Vector3(Math.cos(a)*v*SCALE, Math.sin(a)*v*SCALE, 0.03);
    })
  )}>
    <T.LineBasicMaterial color={0xc084fc} transparent opacity={0.7} />
  </T.LineLoop>

  <!-- Partner pentagon (accent) -->
  <T.Mesh geometry={partnerGeo} position={[0, 0, 0.02]}>
    <T.MeshStandardMaterial
      color={accentHex}
      emissive={accentHex}
      emissiveIntensity={0.7}
      transparent opacity={0.32}
      side={THREE.DoubleSide}
    />
  </T.Mesh>
  <!-- Partner outline -->
  <T.LineLoop geometry={new THREE.BufferGeometry().setFromPoints(
    partnerVec.map((v, i) => {
      const a = (i / 5) * Math.PI * 2 - Math.PI / 2;
      return new THREE.Vector3(Math.cos(a)*v*SCALE, Math.sin(a)*v*SCALE, 0.06);
    })
  )}>
    <T.LineBasicMaterial color={accentHex} transparent opacity={0.9} />
  </T.LineLoop>
</T.Group>
