<script lang="ts">
  import type { Snippet } from 'svelte';
  import { Badge, Button } from '@etzhayyim/design-system';
  import { playTap, haptic } from '@etzhayyim/design-system/audio';
  import AppLauncher from './apps/AppLauncher.svelte';
  import Tuner from './tuner/Tuner.svelte';
  import HeaderYoroAnimation from './components/HeaderYoroAnimation.svelte';
  import type { GfAppLink } from './apps/types';
  import AuthStartSheet from './auth/AuthStartSheet.svelte';
  import OrgWorkspaceSheet from './auth/OrgWorkspaceSheet.svelte';
  import { trustVariantFromScore } from './auth/trust.js';
  import {
    isSignedIn,
    clerkUser,
    currentOrg,
    userOrganizations,
    orgLoading,
    displayName,
    trustSummary,
    initClerk,
    signIn,
    signUp,
    signUpWithUsername,
    openUserProfile,
    switchOrganization,
    createOrganization,
  } from './auth/index.js';
  import { goto } from '$app/navigation';
  import { useProviderWorker } from './provider/worker-state.svelte.js';

  interface Props {
    left?: Snippet;
    right?: Snippet;
    children?: Snippet;
    class?: string;
    style?: string;
    showAppLauncher?: boolean;
    showTuner?: boolean;
    launcherApps?: GfAppLink[];
    showStandardActions?: boolean;
    showCredits?: boolean;
    signInHref?: string;
    signUpHref?: string;
    walletHref?: string;
    walletLabel?: string;
    appName?: string;
    homeHref?: string;
    showMenuButton?: boolean;
    onMenuClick?: () => void;
  }

  const {
    left,
    right,
    children,
    class: className = '',
    style: styleStr = '',
    showAppLauncher = true,
    showTuner = true,
    launcherApps,
    showStandardActions = true,
    showCredits = true,
    signInHref = 'https://authn.etzhayyim.com/sign-in',
    signUpHref = 'https://authn.etzhayyim.com/sign-up',
    walletHref = 'https://metamask.io/download/',
    walletLabel = 'MetaMask',
    appName = 'etzhayyim',
    homeHref = '/',
    showMenuButton = false,
    onMenuClick,
  }: Props = $props();

  const worker = useProviderWorker();
  let authSheetOpen = $state(false);
  let workspaceSheetOpen = $state(false);

  function accountsBaseUrl(): string | undefined {
    const candidate = signUpHref || signInHref;
    if (!candidate) return undefined;
    try {
      return new URL(candidate, typeof window !== 'undefined' ? window.location.origin : 'https://auth.etzhayyim.com').origin;
    } catch {
      return undefined;
    }
  }

  async function handleSignIn() {
    await initClerk({ publishableKey: '', accountsBaseUrl: accountsBaseUrl() }).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/Header.svelte: suppressed async error", error); });
    await signIn();
  }

  async function handleClerkSignUp() {
    await initClerk({ publishableKey: '', accountsBaseUrl: accountsBaseUrl() }).catch((error) => { console.warn("[silent-fail] projects/etzhayyim-project-yoro/wasm/yoro-ui-g00h5zto/svelte/src/lib/Header.svelte: suppressed async error", error); });
    await signUp();
  }

  async function handleCreateAgent(input: import('./auth/types.js').CreateAgentInput) {
    // Agent creation: send character appearance to server for auto-generation
    console.log('[Header] Create agent with appearance:', input.appearance);
  }

  function slugifyOrgName(name: string): string {
    return name
      .trim()
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 48);
  }

  async function handleCreateOrganization(name: string) {
    const orgId = await createOrganization(name, slugifyOrgName(name));
    if (orgId) {
      await switchOrganization(orgId);
    }
  }

</script>

<header
  class={`relative flex shrink-0 items-center justify-between overflow-hidden border-b border-[var(--gv2-border,#333333)] bg-[var(--gv2-bg-primary,#1a1a1a)] px-3 md:px-4 ${className}`}
  style="padding-top: env(safe-area-inset-top); height: calc(var(--gv2-header-height, 56px) + env(safe-area-inset-top)); {styleStr}"
>
  <div class="flex min-w-0 items-center gap-3">
    {#if showMenuButton}
      <button
        class="inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-xl border border-[var(--gv2-border,#e6e6e6)] bg-transparent text-[var(--gv2-text-secondary,#4d4d4d)] hover:border-[var(--gv2-accent,#0031d8)] hover:text-[var(--gv2-accent,#0031d8)] focus-glow active:scale-95 transition-transform duration-100"
        onclick={() => { playTap(); haptic('light'); onMenuClick?.(); }}
        aria-label="Menu"
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
      </button>
    {/if}
    {#if showTuner}
      <Tuner
        buttonClass="min-h-[44px] min-w-[44px] rounded-xl border border-[var(--gv2-border,#e6e6e6)]"
      />
    {:else if showAppLauncher}
      <AppLauncher
        apps={launcherApps}
        buttonClass="min-h-[44px] min-w-[44px] rounded-xl border border-[var(--gv2-border,#e6e6e6)]"
      />
    {/if}
    {#if left}
      {@render left()}
    {/if}
  </div>

  <div class="flex min-w-0 flex-1 items-center justify-center gap-1.5">
    {#if children}
      {@render children()}
    {:else if homeHref}
      <HeaderYoroAnimation />
      <a href={homeHref} class="overflow-hidden text-ellipsis whitespace-nowrap text-sm font-semibold text-[var(--gv2-text-primary,#ffffff)] no-underline hover:opacity-80">{appName}</a>
    {:else}
      <HeaderYoroAnimation />
      <div class="overflow-hidden text-ellipsis whitespace-nowrap text-sm font-semibold text-[var(--gv2-text-primary,#ffffff)]">{appName}</div>
    {/if}
  </div>

  {#if showCredits && $isSignedIn}
    <button
      class="flex items-center gap-1 rounded-lg border border-[var(--gv2-border,#e6e6e6)] px-2 py-1 active:opacity-80 transition-all duration-100 touch-manipulation focus-glow active:scale-95"
      onclick={() => { playTap(); haptic('light'); void goto('/credits'); }}
    >
      <svg class="h-3.5 w-3.5 text-[var(--gv2-accent,#06c755)]" viewBox="0 0 24 24" fill="currentColor"><circle cx="12" cy="12" r="10" opacity="0.2" /><circle cx="12" cy="12" r="6" /></svg>
      <span class="text-[11px] font-semibold tabular-nums text-[var(--gv2-text-primary,#ffffff)]">{worker.workerStats.totalEarned.toFixed(2)}</span>
      <span class="text-[10px] text-[var(--gv2-text-muted,#666)]">Credits</span>
    </button>
  {/if}

  <div class="flex min-w-0 items-center gap-3">
    {#if showStandardActions}
      {#if $isSignedIn && $clerkUser}
        <Badge value={`T${$trustSummary.score}`} variant={trustVariantFromScore($trustSummary.score)} />
        <Button
          variant="outline"
          size="xs"
          onclick={() => workspaceSheetOpen = true}
          class="!border-[var(--gv2-border,#e6e6e6)] !bg-transparent !text-[var(--gv2-text-primary,#ffffff)]"
          title="Switch workspace"
        >
          {$currentOrg?.name || ($orgLoading ? 'Loading...' : 'Workspace')}
        </Button>
        <Button
          variant="outline"
          size="xs"
          onclick={() => openUserProfile()}
          class="!border-[var(--gv2-border,#e6e6e6)] !bg-transparent !text-[var(--gv2-text-primary,#ffffff)]"
          title="Open profile"
        >
          {$displayName}
        </Button>
      {:else}
        <Button variant="outline" size="xs" onclick={handleSignIn}>Sign in</Button>
        <Button variant="solid-fill" size="xs" onclick={() => authSheetOpen = true}>
          <span class="hidden sm:inline">Create Agent</span>
          <span class="sm:hidden">Agent</span>
        </Button>
      {/if}
    {/if}
    {#if right}
      {@render right()}
    {/if}
  </div>
</header>

<AuthStartSheet
  bind:open={authSheetOpen}
  onClerk={handleClerkSignUp}
  onCreateAgent={handleCreateAgent}
/>

<OrgWorkspaceSheet
  bind:open={workspaceSheetOpen}
  currentOrg={$currentOrg}
  organizations={$userOrganizations}
  loading={$orgLoading}
  trust={$trustSummary}
  onSwitch={switchOrganization}
  onCreate={handleCreateOrganization}
/>
