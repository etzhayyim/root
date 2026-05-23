<script lang="ts">
  /**
   * 3D rotating dual-radar pentagon for the featured match card.
   * Self vector (violet) + partner vector (accent) shown as two
   * extruded pentagons rotating slowly in 3D space.
   */
  import { Canvas } from "@threlte/core";
  import SpiritRadar3DScene from "./SpiritRadar3DScene.svelte";
  import type { EmotionVec5 } from "./spirit-match";

  export let selfVec: EmotionVec5 = [0.5, 0.5, 0.5, 0.5, 0.5];
  export let partnerVec: EmotionVec5 = [0.5, 0.5, 0.5, 0.5, 0.5];
  export let accentColor = "#ef4444";
  export let size = 120;
</script>

<div class="radar3d-wrap" style="width:{size}px; height:{size}px">
  <Canvas rendererParameters={{ alpha: true, antialias: true }}>
    <SpiritRadar3DScene {selfVec} {partnerVec} {accentColor} />
  </Canvas>
</div>

<style>
  .radar3d-wrap {
    flex-shrink: 0;
    background: transparent;
  }
  .radar3d-wrap :global(canvas) {
    background: transparent !important;
  }
</style>
