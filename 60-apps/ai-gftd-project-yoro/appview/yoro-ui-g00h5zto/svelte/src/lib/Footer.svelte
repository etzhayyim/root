<script lang="ts">
  import type { Snippet } from 'svelte';
  import { Link } from '@etzhayyim/design-system';
  import { openSupportRoom } from './superapp.js';

  interface Props {
    left?: Snippet;
    right?: Snippet;
    children?: Snippet;
    class?: string;
    showStandardLinks?: boolean;
    privacyHref?: string;
    termsHref?: string;
    helpHref?: string;
    copyrightText?: string;
  }

  const {
    left,
    right,
    children,
    class: className = '',
    showStandardLinks = true,
    privacyHref = '/privacy',
    termsHref = '/terms',
    helpHref = '/support',
    copyrightText = '© amanomibashira — 宗教法人 (任意団体・blockchain 登記)'
  }: Props = $props();

  let openingSupport = $state(false);

  async function handleSupportClick() {
    if (openingSupport) return;
    openingSupport = true;
    try {
      await openSupportRoom();
    } finally {
      openingSupport = false;
    }
  }
</script>

<footer
  class={`flex min-h-[var(--gv2-footer-height,44px)] items-center justify-between gap-3 border-t border-[var(--gv2-border,#333333)] bg-[var(--gv2-bg-primary,#1a1a1a)] px-3 md:px-4 ${className}`}
>
  <div class="flex min-w-0 items-center gap-3">
    {#if left}
      {@render left()}
    {:else}
      <span class="whitespace-nowrap text-xs text-[var(--gv2-text-muted,#666666)]">{copyrightText}</span>
    {/if}
  </div>

  <div class="flex min-w-0 flex-1 justify-center">
    {#if children}
      {@render children()}
    {:else if showStandardLinks}
      <nav class="inline-flex min-h-8 items-center gap-3.5 max-md:gap-2.5" aria-label="Footer links">
        <Link href="/support/operator" class="whitespace-nowrap text-xs">Operator</Link>
        <Link href={privacyHref} class="whitespace-nowrap text-xs">Privacy Policy</Link>
        <Link href={termsHref} class="whitespace-nowrap text-xs">Terms</Link>
        {#if helpHref === '/support'}
          <button
            type="button"
            class="whitespace-nowrap text-xs text-[var(--gv2-link,#6c8cff)] underline-offset-2 hover:underline disabled:opacity-60"
            onclick={handleSupportClick}
            disabled={openingSupport}
          >
            Support
          </button>
        {:else}
          <Link href={helpHref} class="whitespace-nowrap text-xs">Support</Link>
        {/if}
      </nav>
    {/if}
  </div>

  <div class="flex min-w-0 items-center gap-3">
    {#if right}
      {@render right()}
    {/if}
  </div>
</footer>
