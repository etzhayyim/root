<script lang="ts">
  import type { Snippet } from 'svelte';

  interface Props {
    width?: string;
    header?: Snippet;
    footer?: Snippet;
    children?: Snippet;
    class?: string;
  }

  const {
    width,
    header,
    footer,
    children,
    class: className = ''
  }: Props = $props();
</script>

<aside
  class={`flex h-full w-[var(--gv2-sidebar-width,296px)] flex-col overflow-hidden border-r border-[var(--gv2-border,#333333)] bg-[var(--gv2-bg-sidebar,#1f1f1f)] ${className}`}
  style:width
>
  {#if header}
    <div class="shrink-0">
      {@render header()}
    </div>
  {/if}

  <div class="flex-1 overflow-x-hidden overflow-y-auto">
    {#if children}
      {@render children()}
    {/if}
  </div>

  {#if footer}
    <div class="mt-auto shrink-0 border-t border-[var(--gv2-border,#333333)]">
      {@render footer()}
    </div>
  {/if}
</aside>
