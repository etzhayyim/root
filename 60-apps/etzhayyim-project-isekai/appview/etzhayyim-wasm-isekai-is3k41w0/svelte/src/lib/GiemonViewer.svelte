<script lang="ts">
  // Shared GIEMON viewer component. Loads the kami-app-giemon WASM bundle
  // (served from static/giemon/) on the client and runs the selected model —
  // default = Kabitori 黴取り mold-removal sim. Used by both the `/giemon` and
  // `/giemon.htm` SvelteKit routes (the static .htm harness is retired).
  import { onMount } from 'svelte';

  type Model = { id: string; name: string; desc: string; fn: string; physics?: boolean };
  const MODELS: Model[] = [
    { id: 'kabitori',    name: 'Kabitori 黴取り — Mold-Removal Sim', desc: 'autonomous probe feeds into a walled gap + scrubs mold off the surface (green→clean)', fn: 'run_giemon_kabitori_sim_v1' },
    { id: 'physics-arm', name: 'Arm6 — 3-D Physics Sim',             desc: '6-DOF spatial solver + contact (1–6 select · J/L torque)', fn: 'run_giemon_sim_v1', physics: true },
    { id: 'otete',       name: 'Otete 御手 — 7-DOF arm sim',          desc: 'Giemon Otete kit: 6-axis arm + prismatic gripper (DH-faithful · 1–6 select · J/L torque)', fn: 'run_giemon_otete_sim_v1', physics: true },
    { id: 'armcrawler',  name: 'ArmCrawler — Viewer',                desc: '6-DOF arm + rubber-track crawler', fn: 'run_giemon_v1' },
    { id: 'hitogata',    name: 'Hitogata — Biped',                   desc: '17-DOF humanoid (~285mm)', fn: 'run_giemon_hitogata_v1' },
    { id: 'caterpillar', name: 'Caterpillar — UGV',                  desc: 'dual-track + LiDAR + stereo cam', fn: 'run_giemon_caterpillar_v1' }
  ];

  let status = 'loading…';
  let err = '';
  let selected = 'kabitori';

  function pick(id: string) {
    sessionStorage.setItem('giemon-model', id);
    location.reload();
  }

  onMount(async () => {
    try {
      selected = sessionStorage.getItem('giemon-model') ?? 'kabitori';
      const model = MODELS.find((m) => m.id === selected) ?? MODELS[0];
      // The bundle lives in static/ (Vite's /public): it is copied as-is and
      // must NOT be import-analyzed. Build the URL at runtime so Vite leaves
      // this as a native browser dynamic import (a string literal here triggers
      // "Cannot import non-asset file … inside /public"). init() then fetches
      // kami_app_giemon_bg.wasm relative to the module URL (/giemon/).
      const jsUrl = `${location.origin}/giemon/kami_app_giemon.js`;
      const mod: any = await import(/* @vite-ignore */ jsUrl);
      await mod.default(); // wasm-bindgen init()
      status = `running (${model.name})`;
      // Arm6 keyboard controls (no-op for other models).
      window.addEventListener('keydown', (e) => {
        if (e.repeat) return;
        if (e.key >= '1' && e.key <= '6') mod.giemonSelectJoint?.(Number(e.key));
        else if (e.key === 'j' || e.key === 'J') mod.giemonSetJointTorque?.(-8);
        else if (e.key === 'l' || e.key === 'L') mod.giemonSetJointTorque?.(8);
      });
      window.addEventListener('keyup', (e) => {
        if (['j', 'J', 'l', 'L'].includes(e.key)) mod.giemonSetJointTorque?.(0);
      });
      await mod[model.fn]('gc');
    } catch (e: any) {
      status = 'error';
      err = e?.message ?? String(e);
      console.error('[giemon]', e);
    }
  });
</script>

<svelte:head><title>GIEMON 五右衛門 — kami-engine (Svelte)</title></svelte:head>

<canvas id="gc"></canvas>

<div class="hud">
  <div class="title">GIEMON 五右衛門 <span class="badge">Svelte</span></div>
  <div class="status">{status}</div>
  {#if err}<div class="err">{err}</div>{/if}
  <div class="models">
    {#each MODELS as m}
      <button class:active={m.id === selected} on:click={() => pick(m.id)}>
        <span class="n">{m.name}</span>
        <span class="d">{m.desc}</span>
      </button>
    {/each}
  </div>
  <div class="hint">drag = orbit · scroll = zoom · Arm6: 1–6 select joint, J/L torque</div>
</div>

<style>
  :global(html, body) { margin: 0; height: 100%; background: #0d0f12; overflow: hidden; }
  #gc { position: fixed; inset: 0; width: 100vw; height: 100vh; display: block; }
  .hud {
    position: fixed; top: 12px; left: 12px; max-width: 44ch; padding: 12px 14px;
    background: rgba(20, 24, 30, 0.82); border: 1px solid #2a2f37; border-radius: 12px;
    color: #e6e8ea; font: 13px/1.5 -apple-system, Segoe UI, Roboto, sans-serif;
  }
  .title { font-weight: 700; }
  .badge { font-size: 11px; background: #ff6b35; color: #fff; border-radius: 6px; padding: 1px 6px; margin-left: 6px; }
  .status { color: #5fd38a; margin: 4px 0; }
  .err { color: #ff6b6b; white-space: pre-wrap; }
  .models { display: flex; flex-direction: column; gap: 6px; margin: 8px 0; }
  .models button {
    text-align: left; background: #181d24; border: 1px solid #2a2f37; border-radius: 8px;
    color: #e6e8ea; padding: 6px 8px; cursor: pointer; display: flex; flex-direction: column;
  }
  .models button.active { border-color: #ffd23f; background: #20262e; }
  .models .n { font-weight: 600; }
  .models .d { font-size: 11px; color: #9aa3ad; }
  .hint { font-size: 11px; color: #9aa3ad; }
</style>
