<script lang="ts">
  import { resolvedTheme, setTheme, theme, toggleTheme, type Theme, type ColorTheme } from './theme';

  interface Props {
    showSystem?: boolean;
    size?: number;
  }

  const {
    showSystem = false,
    size = 32
  }: Props = $props();

  let currentTheme = $state<Theme>('dark');
  let resolved = $state<ColorTheme>('dark');

  $effect(() => {
    const unsubTheme = theme.subscribe((value) => {
      currentTheme = value;
    });

    const unsubResolved = resolvedTheme.subscribe((value) => {
      resolved = value;
    });

    return () => {
      unsubTheme();
      unsubResolved();
    };
  });
</script>

{#if showSystem}
  <div class="flex gap-0.5 rounded-lg border border-[var(--gv2-border,#333)] bg-[var(--gv2-bg-input,#2a2a2a)] p-0.5" style="--size: {size}px">
    <button class="flex h-[calc(var(--size)-8px)] w-[calc(var(--size)-4px)] items-center justify-center rounded-md bg-transparent text-[var(--gv2-text-muted,#666)] hover:bg-[var(--gv2-bg-hover,#333)] hover:text-[var(--gv2-text-secondary,#a0a0a0)]" class:bg-[var(--gv2-bg-hover,#333)]={currentTheme === 'dark'} class:text-[var(--gv2-text-primary,#fff)]={currentTheme === 'dark'} onclick={() => setTheme('dark')} title="Dark" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    </button>

    <button class="flex h-[calc(var(--size)-8px)] w-[calc(var(--size)-4px)] items-center justify-center rounded-md bg-transparent text-[var(--gv2-text-muted,#666)] hover:bg-[var(--gv2-bg-hover,#333)] hover:text-[var(--gv2-text-secondary,#a0a0a0)]" class:bg-[var(--gv2-bg-hover,#333)]={currentTheme === 'system'} class:text-[var(--gv2-text-primary,#fff)]={currentTheme === 'system'} onclick={() => setTheme('system')} title="System" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
        <line x1="8" y1="21" x2="16" y2="21" />
        <line x1="12" y1="17" x2="12" y2="21" />
      </svg>
    </button>

    <button class="flex h-[calc(var(--size)-8px)] w-[calc(var(--size)-4px)] items-center justify-center rounded-md bg-transparent text-[var(--gv2-text-muted,#666)] hover:bg-[var(--gv2-bg-hover,#333)] hover:text-[var(--gv2-text-secondary,#a0a0a0)]" class:bg-[var(--gv2-bg-hover,#333)]={currentTheme === 'light'} class:text-[var(--gv2-text-primary,#fff)]={currentTheme === 'light'} onclick={() => setTheme('light')} title="Light" type="button">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
    </button>
  </div>
{:else}
  <button
    class="flex items-center justify-center rounded-md border border-[var(--gv2-border,#333)] bg-transparent text-[var(--gv2-text-secondary,#a0a0a0)] hover:bg-[var(--gv2-bg-hover,#333)] hover:text-[var(--gv2-text-primary,#fff)]"
    style="--size: {size}px; width: var(--size); height: var(--size);"
    onclick={toggleTheme}
    title={resolved === 'dark' ? 'Switch to light' : 'Switch to dark'}
    type="button"
  >
    {#if resolved === 'dark'}
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <circle cx="12" cy="12" r="5" />
        <line x1="12" y1="1" x2="12" y2="3" />
        <line x1="12" y1="21" x2="12" y2="23" />
        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" />
        <line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
        <line x1="1" y1="12" x2="3" y2="12" />
        <line x1="21" y1="12" x2="23" y2="12" />
        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" />
        <line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
      </svg>
    {:else}
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
      </svg>
    {/if}
  </button>
{/if}
