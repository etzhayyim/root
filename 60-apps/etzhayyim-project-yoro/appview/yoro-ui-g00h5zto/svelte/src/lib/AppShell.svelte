<script lang="ts">
  import type { Snippet } from 'svelte';
  import { onMount } from 'svelte';
  import './theme/tokens.css';

  interface Props {
    sidebar?: Snippet;
    header?: Snippet;
    footer?: Snippet;
    bottomBar?: Snippet;
    children?: Snippet;
    class?: string;
    style?: string;
    sidebarOpen?: boolean;
    onCloseSidebar?: () => void;
    mobileMode?: boolean;
  }

  let {
    sidebar,
    header,
    footer,
    bottomBar,
    children,
    class: className = '',
    style: styleStr = '',
    sidebarOpen = false,
    onCloseSidebar,
    mobileMode
  }: Props = $props();

  let isMobile = $state(false);

  $effect(() => {
    if (mobileMode !== undefined) {
      isMobile = mobileMode;
    }
  });

  onMount(() => {
    if (mobileMode !== undefined) {
      return;
    }
    const mediaQuery = window.matchMedia('(max-width: 1023px)');
    isMobile = mediaQuery.matches;
    const handler = (event: MediaQueryListEvent) => {
      isMobile = event.matches;
    };
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  });

  function closeSidebar() {
    onCloseSidebar?.();
  }
</script>

<div
  class={`flex h-dvh overflow-hidden bg-[var(--gv2-bg-primary,#1a1a1a)] text-[var(--gv2-text-primary,#ffffff)] ${className}`}
  style="{styleStr ? styleStr + '; ' : ''}flex-direction: {isMobile ? 'column' : 'row'}"
>
  {#if sidebar && !isMobile}
    <div class="shrink-0">
      {@render sidebar()}
    </div>
  {/if}

  <div class="relative z-0 flex min-w-0 min-h-0 flex-1 flex-col">
    {#if header}
      <div class="relative z-10 shrink-0">
        {@render header()}
      </div>
    {/if}

    <div class="relative flex-1 min-h-0 flex flex-col overflow-hidden">
      {#if children}
        {@render children()}
      {/if}
    </div>

    {#if bottomBar}
      <div class="shrink-0">
        {@render bottomBar()}
      </div>
    {/if}

    {#if footer}
      <div class="shrink-0">
        {@render footer()}
      </div>
    {/if}
  </div>

  {#if sidebar && isMobile}
    <div
      class="fixed inset-0 z-[79] bg-black/55 backdrop-blur-[2px] transition-opacity duration-200"
      style:opacity={sidebarOpen ? 1 : 0}
      style:pointer-events={sidebarOpen ? 'auto' : 'none'}
      onclick={closeSidebar}
      onkeydown={(event) => {
        if (event.key === 'Enter' || event.key === ' ') closeSidebar();
      }}
      role="button"
      tabindex={sidebarOpen ? 0 : -1}
      aria-label="Close navigation drawer"
    ></div>
    <div
      class="fixed inset-y-0 left-0 z-[80] max-w-[85vw] transition-transform duration-200"
      style:transform={sidebarOpen ? 'translateX(0)' : 'translateX(-100%)'}
    >
      {@render sidebar()}
    </div>
  {/if}
</div>
