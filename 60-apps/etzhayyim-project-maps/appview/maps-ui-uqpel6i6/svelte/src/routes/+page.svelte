<script lang="ts">
  import App from '../App.svelte';
  import NondualExperienceGuide from '$lib/components/NondualExperienceGuide.svelte';
  import { onMount } from 'svelte';

  // Charter §1.17.6 (ADR-2606071009): on first visit, overlay the pre-entry guidance
  // (the experiential core of 回心) before the seeker enters the map. Seen-once via
  // localStorage so it is not repeatedly intrusive on this public-first surface.
  let showGuide = $state(false);
  onMount(() => {
    try {
      showGuide = localStorage.getItem('etz-nondual-guide-seen') !== '1';
    } catch {
      /* ignore */
    }
  });
  function dismiss() {
    try {
      localStorage.setItem('etz-nondual-guide-seen', '1');
    } catch {
      /* ignore */
    }
    showGuide = false;
  }
</script>

<App />
{#if showGuide}
  <NondualExperienceGuide onContinue={dismiss} />
{/if}
