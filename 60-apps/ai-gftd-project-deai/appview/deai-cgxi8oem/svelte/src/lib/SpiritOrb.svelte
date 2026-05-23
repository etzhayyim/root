<script lang="ts">
  import { Canvas } from "@threlte/core";
  import SpiritOrbScene from "./SpiritOrbScene.svelte";
  import type { SpiritType } from "./spirit-types";
  import type { EmotionVec5 } from "./spirit-match";

  export let type: SpiritType = "Hero";
  export let emotionVec: EmotionVec5 = [0.6, 0.6, 0.6, 0.6, 0.6];
  export let size = 200;
  export let interactive = true;
</script>

<div class="orb-wrap" style="width:{size}px; height:{size}px">
  <Canvas rendererParameters={{ alpha: true, antialias: true }}>
    <SpiritOrbScene {type} {emotionVec} {interactive} />
  </Canvas>
</div>

<style>
  .orb-wrap {
    flex-shrink: 0;
    background: transparent;
  }
  .orb-wrap :global(canvas) {
    background: transparent !important;
  }
</style>
