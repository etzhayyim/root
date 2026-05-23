<script lang="ts">
  import { onMount } from 'svelte';
  import { searchHotels, type YadoyaHotel } from '../lib/yadoya-xrpc';

  let { data = { title: 'yadoya.etzhayyim.com' } } = $props();

  let region = $state('asia');
  let city = $state('');
  let priceJpyMax = $state<number | undefined>(undefined);
  let hotels = $state<YadoyaHotel[]>([]);
  let total = $state(0);
  let loading = $state(false);
  let error = $state<string | null>(null);

  async function runSearch() {
    loading = true;
    error = null;
    try {
      const out = await searchHotels({ region, city: city || undefined, priceJpyMax, limit: 50 });
      hotels = out.hotels ?? [];
      total = out.total ?? hotels.length;
    } catch (err) {
      error = err instanceof Error ? err.message : String(err);
      hotels = [];
      total = 0;
    } finally {
      loading = false;
    }
  }

  onMount(runSearch);
</script>

<svelte:head>
  <title>{data.title}</title>
</svelte:head>

<main class="mx-auto max-w-4xl space-y-6 p-6">
  <header class="space-y-1">
    <h1 class="text-2xl font-bold">yadoya.etzhayyim.com</h1>
    <p class="text-sm text-gray-600">
      Hotel search & reservation — ISIC I5510 catalog, ADR-0036 Worker-direct,
      bridged to <code>did:web:hospitality.etzhayyim.com</code>.
    </p>
  </header>

  <form
    class="grid grid-cols-1 gap-3 rounded-md border border-gray-200 p-4 sm:grid-cols-4"
    onsubmit={(e) => { e.preventDefault(); runSearch(); }}
  >
    <label class="flex flex-col gap-1 text-sm">
      Region
      <select bind:value={region} class="rounded border px-2 py-1">
        <option value="">(any)</option>
        <option value="asia">asia</option>
        <option value="europe">europe</option>
        <option value="mena">mena</option>
        <option value="americas">americas</option>
        <option value="africa">africa</option>
        <option value="oceania">oceania</option>
      </select>
    </label>
    <label class="flex flex-col gap-1 text-sm">
      City
      <input bind:value={city} placeholder="Tokyo" class="rounded border px-2 py-1" />
    </label>
    <label class="flex flex-col gap-1 text-sm">
      Max JPY / night
      <input type="number" bind:value={priceJpyMax} min="0" class="rounded border px-2 py-1" />
    </label>
    <div class="flex items-end">
      <button
        type="submit"
        disabled={loading}
        class="w-full rounded bg-black px-4 py-2 text-white disabled:opacity-50"
      >
        {loading ? 'Searching…' : 'Search'}
      </button>
    </div>
  </form>

  {#if error}
    <div class="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-800">
      {error}
    </div>
  {/if}

  <section>
    <p class="mb-2 text-sm text-gray-600">{total} hotel(s)</p>
    <ul class="divide-y divide-gray-100 rounded-md border border-gray-200">
      {#each hotels as h (h.vertex_id)}
        <li class="flex flex-col gap-1 p-3 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p class="font-medium">{h.name}</p>
            <p class="text-xs text-gray-500">
              {h.city ?? ''} {h.country} · {h.isic_code}
              {#if h.osm_id}· OSM {h.osm_id}{/if}
            </p>
          </div>
          {#if h.source_url}
            <a class="text-sm text-blue-700 underline" href={h.source_url} target="_blank" rel="noopener">source</a>
          {/if}
        </li>
      {:else}
        {#if !loading}
          <li class="p-4 text-sm text-gray-500">No hotels match. Try widening the filter.</li>
        {/if}
      {/each}
    </ul>
  </section>
</main>
