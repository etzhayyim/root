<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    children?: Snippet;
    class?: string;
    padding?: string;
  }

  const {
    children,
    class: className = '',
    padding = '16px'
  }: Props = $props();
</script>

<main class={`box-border h-full w-full overflow-auto ${className}`} style:padding>
  {#if children}
    {@render children()}
  {/if}
</main>
