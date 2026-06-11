<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import type { Snapshot } from "./lib/types";
  import { fetchState, openEvents } from "./lib/api";
  import Graph from "./lib/Graph.svelte";
  import Sidebar from "./lib/Sidebar.svelte";
  import Aliveness from "./lib/Aliveness.svelte";

  let snap: Snapshot | null = null;
  let selected: string | null = null;
  let activity: any[] = [];
  let es: EventSource | null = null;
  let connected = false;

  onMount(async () => {
    try {
      snap = await fetchState();
      activity = snap.activity || [];
    } catch (e) {
      console.error("initial state failed", e);
    }
    es = openEvents((ev) => {
      connected = true;
      if (ev.type === "hello" || ev.type === "tick") {
        if (ev.state) snap = ev.state;
      }
      if (ev.type !== "heartbeat") {
        activity = [ev, ...activity].slice(0, 60);
      }
    });
    if (es) {
      es.onopen = () => connected = true;
      es.onerror = () => connected = false;
    }
  });

  onDestroy(() => { es?.close(); });

  function selectEntity(id: string) {
    selected = id;
  }
</script>

{#if snap}
  <Aliveness {snap} />
  <main>
    <section class="canvas" on:click={() => selected = null}>
      <Graph {snap} {selected} onSelect={selectEntity} />
    </section>
    <Sidebar {snap} {selected} {activity} onSelect={selectEntity} />
  </main>
{:else}
  <div class="boot">
    <p>etzhayyim · 縁起トポロジー</p>
    <small>観測 接続中…</small>
  </div>
{/if}

<svg class="kohan" viewBox="0 0 64 64" aria-hidden="true">
  <rect x="6" y="6" width="52" height="52" fill="var(--shinshu)"
        transform="rotate(-3 32 32)" />
  <text x="32" y="29" text-anchor="middle" fill="var(--washi)"
        font-size="14" font-weight="700" transform="rotate(-3 32 32)">縁起</text>
  <text x="32" y="46" text-anchor="middle" fill="var(--washi)"
        font-size="10" transform="rotate(-3 32 32)">{snap ? "cycle " + Object.keys(snap.entities).filter(k=>k.startsWith("adr/")).length : "—"}</text>
</svg>

<style>
  main {
    grid-row: 2;
    display: grid;
    grid-template-columns: 1.45fr 1fr;
    min-height: 0;
  }
  .canvas {
    position: relative;
    background:
      radial-gradient(ellipse 70% 50% at 50% 50%, rgba(255,251,236,0.65), transparent 60%),
      var(--washi);
    overflow: hidden;
  }
  .boot {
    grid-row: 1 / -1;
    display: grid; place-items: center;
    font-family: var(--font-mincho);
    color: var(--sumi-soft);
  }
  .boot p { font-size: 20px; margin: 0 0 6px; color: var(--shinshu); }
  .boot small { color: var(--sumi-pale); }
</style>
