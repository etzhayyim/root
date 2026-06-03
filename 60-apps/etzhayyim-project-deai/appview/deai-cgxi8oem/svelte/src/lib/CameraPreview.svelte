<script lang="ts">
  import { onMount, onDestroy } from "svelte";

  export let stream: MediaStream | null = null;
  export let recording = false;

  let videoEl: HTMLVideoElement;
  let dotPhase = false;

  $: if (videoEl && stream) {
    videoEl.srcObject = stream;
    videoEl.play().catch(() => {});
  }

  // Dispatch video element so HumeRecorder can draw frames
  import { createEventDispatcher } from "svelte";
  const dispatch = createEventDispatcher<{ videoready: HTMLVideoElement }>();

  onMount(() => {
    if (videoEl) dispatch("videoready", videoEl);
  });

  let blinkTimer: ReturnType<typeof setInterval>;
  onMount(() => {
    blinkTimer = setInterval(() => { dotPhase = !dotPhase; }, 800);
  });
  onDestroy(() => clearInterval(blinkTimer));
</script>

{#if stream}
  <div class="cam-preview">
    <!-- svelte-ignore a11y-media-has-caption -->
    <video bind:this={videoEl} muted playsinline class="cam-video"></video>
    <div class="rec-badge" class:active={recording}>
      <span class="rec-dot" class:blink={dotPhase && recording}></span>
      {recording ? "REC" : "CAM"}
    </div>
  </div>
{/if}

<style>
  .cam-preview {
    position: fixed; bottom: 100px; right: 16px; z-index: 100;
    width: 88px; height: 66px; border-radius: 10px; overflow: hidden;
    border: 1.5px solid rgba(192,132,252,0.3);
    box-shadow: 0 4px 20px rgba(0,0,0,0.6);
  }
  .cam-video {
    width: 100%; height: 100%; object-fit: cover;
    transform: scaleX(-1); /* mirror */
  }
  .rec-badge {
    position: absolute; bottom: 4px; left: 50%; transform: translateX(-50%);
    display: flex; align-items: center; gap: 4px;
    background: rgba(0,0,0,0.65); border-radius: 6px; padding: 2px 6px;
    font-size: 9px; font-weight: 700; color: rgba(255,255,255,0.6);
    letter-spacing: 0.08em;
  }
  .rec-badge.active { color: #f87171; }
  .rec-dot {
    width: 5px; height: 5px; border-radius: 50%;
    background: rgba(255,255,255,0.3);
  }
  .rec-badge.active .rec-dot { background: #f87171; }
  .rec-dot.blink { opacity: 0.1; }
</style>
