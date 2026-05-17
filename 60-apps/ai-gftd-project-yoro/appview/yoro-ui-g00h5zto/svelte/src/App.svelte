<script lang="ts">
  import RootLayout from "./routes/+layout.svelte";
  import ProfileHandlePage from "./routes/profile/[handle]/+page.svelte";
  import { pageStore, routeState } from "./spa/router";

  const activeMatch = $derived($routeState.match);
  const fallbackHandle = $derived($pageStore.params.handle ?? "");
</script>

<RootLayout>
  {#snippet children()}
    {#if activeMatch}
      <activeMatch.component data={{}} />
    {:else if fallbackHandle}
      <ProfileHandlePage data={{}} />
    {:else}
      <main class="mx-auto w-full max-w-[600px] px-6 py-10 text-gv2-text-primary">
        <h1 class="text-[22px] font-bold">Page Not Found</h1>
        <p class="mt-3 text-[14px] text-gv2-text-muted">The requested route is not available in SPA mode.</p>
      </main>
    {/if}
  {/snippet}
</RootLayout>
