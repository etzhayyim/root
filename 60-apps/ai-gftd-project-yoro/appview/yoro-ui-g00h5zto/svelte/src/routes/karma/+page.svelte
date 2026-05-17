<!--
  /karma — Karma Hegemon edge graph visualization (因陀羅網).

  Renders the IndraNet component scoped to the current viewer's DID.
  Pure read path — consumes ai.gftd.apps.karma.{coverage,listEdges,wbtBalance}
  XRPCs. No mutation; click a vertex to inspect its WBT balance.

  Karma Hegemon Phase K3 deliverable (last item).
  Authoritative axioms: 90-docs/proof/Karma.lean (Lean 4 verified).
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import IndraNet from '$lib/components/IndraNet.svelte';
  import { getCurrentDID } from '$lib/atproto-agent';

  let viewerDid = $state('');
  let loading = $state(true);

  onMount(async () => {
    try {
      viewerDid = (await getCurrentDID()) || '';
    } catch {
      viewerDid = '';
    } finally {
      loading = false;
    }
  });
</script>

<svelte:head>
  <title>Karma — 因陀羅網</title>
</svelte:head>

<main class="karma-page">
  <header>
    <h1>Karma — 因陀羅網</h1>
    <p class="subtitle">
      Edge-primary Spirit-in-Physic karma graph. Each vertex is an
      organism (DID); each edge is a karma dependency. Karma is in
      the edges, not in the organisms — Karma.lean N1 (relational).
    </p>
  </header>

  {#if loading}
    <div class="loading">resolving viewer DID…</div>
  {:else}
    <IndraNet viewerDid={viewerDid} />
    {#if !viewerDid}
      <p class="hint">
        Sign in to see karma edges scoped to your DID. The coverage
        banner above shows ecosystem-wide totals regardless.
      </p>
    {/if}
  {/if}

  <footer>
    <p class="meta">
      Authoritative axioms: <code>90-docs/proof/Karma.lean</code> (Lean 4 verified).
      5-layer persistence: RisingWave hot · AT-repo · IPFS-self · IPFS-ext · ETH anchor + Filecoin (K3 Phase).
    </p>
  </footer>
</main>

<style>
  .karma-page {
    max-width: 960px;
    margin: 0 auto;
    padding: 1rem 1.25rem 2rem;
    color: var(--ds-color-text, #222);
  }
  header h1 {
    font-size: 1.6rem;
    margin: 0.5rem 0 0.25rem 0;
  }
  .subtitle {
    color: var(--ds-color-text-muted, #666);
    font-size: 0.9rem;
    margin: 0 0 1.25rem 0;
    max-width: 640px;
    line-height: 1.5;
  }
  .loading, .hint {
    padding: 1.5rem;
    text-align: center;
    color: var(--ds-color-text-muted, #888);
    font-size: 0.9rem;
  }
  footer {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid var(--ds-color-border, #eee);
  }
  .meta {
    font-size: 0.75rem;
    color: var(--ds-color-text-muted, #888);
    line-height: 1.5;
  }
  .meta code {
    font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
    font-size: 0.7rem;
    background: var(--ds-color-surface-muted, #f4f4f6);
    padding: 0.05rem 0.3rem;
    border-radius: 3px;
  }
</style>
