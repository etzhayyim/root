<script lang="ts">
  import { onMount } from 'svelte';

  interface Candidate {
    institutionId: string;
    nameJa: string;
    nameEn: string;
    country: string;
    score: number;
    referralPathIds: string[];
  }

  let substrateClass = 'nerve_aplasia';
  let localeCountry = 'JP';
  let dfnb9Confirmed = false;
  
  let candidates: Candidate[] = [];
  let loading = false;
  let error = '';

  async function fetchMatch() {
    loading = true;
    error = '';
    try {
      const url = `https://open-otology-uhl-r.etzhayyim.com/xrpc/jp.etzhayyim.med.uhl.institution.matchQuery?substrateClass=${encodeURIComponent(substrateClass)}&localeCountry=${encodeURIComponent(localeCountry)}&dfnb9Confirmed=${dfnb9Confirmed}`;
      
      const res = await fetch(url);
      if (!res.ok) {
        throw new Error(await res.text());
      }
      
      const data = await res.json();
      candidates = data.candidates || [];
    } catch (e: any) {
      error = e.message;
    } finally {
      loading = false;
    }
  }

  onMount(() => {
    // Optional initial fetch or setup
  });
</script>

<main class="container">
  <h1>UHL-R Clinician Review UI</h1>
  <p>Decision support interface for congenital right-sided sensorineural hearing loss (UHL-R).</p>

  <section class="controls">
    <label>
      Substrate Class:
      <select bind:value={substrateClass}>
        <option value="sgn_present_hc_loss">SGN Present / HC Loss</option>
        <option value="sgn_degenerating_nerve_present">SGN Degenerating</option>
        <option value="sgn_absent_nerve_present">SGN Absent / Nerve Present</option>
        <option value="nerve_aplasia">Nerve Aplasia</option>
        <option value="indeterminate">Indeterminate</option>
      </select>
    </label>

    <label>
      Locale (Country):
      <input type="text" bind:value={localeCountry} placeholder="JP" />
    </label>

    <label>
      <input type="checkbox" bind:value={dfnb9Confirmed} />
      DFNB9 (OTOF) Confirmed
    </label>

    <button on:click={fetchMatch} disabled={loading}>
      {loading ? 'Matching...' : 'Find Institutions'}
    </button>
  </section>

  {#if error}
    <div class="error">
      <strong>Error:</strong> {error}
    </div>
  {/if}

  <section class="results">
    <h2>Matched Candidates</h2>
    {#if candidates.length === 0}
      <p>No candidates found or query not executed.</p>
    {:else}
      <ul>
        {#each candidates as candidate}
          <li>
            <strong>{candidate.nameJa} ({candidate.nameEn})</strong> — Score: {candidate.score}
            <div><small>{candidate.institutionId} | Country: {candidate.country}</small></div>
            {#if candidate.referralPathIds && candidate.referralPathIds.length > 0}
              <div class="paths">
                Pathways: {candidate.referralPathIds.join(', ')}
              </div>
            {/if}
          </li>
        {/each}
      </ul>
    {/if}
  </section>
  
  <div class="disclaimer">
    <p>⚠️ <strong>Human Review Required:</strong> This output must be reviewed by a qualified clinician. Ethics committee review may be required.</p>
  </div>
</main>

<style>
  .container {
    max-width: 800px;
    margin: 0 auto;
    font-family: system-ui, -apple-system, sans-serif;
    line-height: 1.5;
  }
  .controls {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    background: #f9f9f9;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
  }
  .controls label {
    display: flex;
    gap: 0.5rem;
    align-items: center;
  }
  .error {
    color: red;
    background: #ffe6e6;
    padding: 1rem;
    border-radius: 8px;
    margin-bottom: 2rem;
  }
  .results ul {
    list-style: none;
    padding: 0;
  }
  .results li {
    padding: 1rem;
    border: 1px solid #ccc;
    border-radius: 8px;
    margin-bottom: 1rem;
  }
  .paths {
    margin-top: 0.5rem;
    color: #0056b3;
    font-size: 0.9em;
  }
  .disclaimer {
    margin-top: 2rem;
    padding: 1rem;
    border-left: 4px solid orange;
    background: #fffdf5;
  }
</style>
