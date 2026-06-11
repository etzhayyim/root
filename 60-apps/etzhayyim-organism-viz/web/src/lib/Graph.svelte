<script lang="ts">
  import { onMount } from "svelte";
  import type { Snapshot, NodePos } from "./types";
  import { buildLayout, buildEdges } from "./layout";
  import { kotodamaPath, leafPath, fanPath, sealSquarePath, brushPath } from "./shapes";

  export let snap: Snapshot;
  export let selected: string | null;
  export let onSelect: (id: string) => void;

  let positions: NodePos[] = [];
  let edges: any[] = [];

  const W = 1200, H = 900;
  $: if (snap) {
    positions = buildLayout(snap, W, H);
    edges = buildEdges(snap, positions);
  }

  function edgeColor(kind: string): string {
    return ({ sacred: "var(--shinshu)", inheritance: "var(--ai)", ring: "var(--kincha)", default: "var(--sumi)" } as any)[kind];
  }
  function edgeOpacity(kind: string): number {
    return ({ sacred: 0.55, inheritance: 0.5, ring: 0.35, default: 0.32 } as any)[kind];
  }
  function isHighlighted(id: string): boolean {
    if (!selected) return false;
    if (id === selected) return true;
    const ent = snap.entities[selected];
    return !!ent && ent.neighbors.includes(id);
  }
  function dim(p: NodePos): boolean {
    if (!selected) return false;
    return !isHighlighted(p.id);
  }
</script>

<svg viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid meet" class="graph"
     class:has-selection={selected !== null}>
  <!-- brush edges: outer halo + inner stroke -->
  <g class="edges">
    {#each edges as e, i}
      {#if !selected || isHighlighted(e.a.id) || isHighlighted(e.b.id)}
        <path d={brushPath(e.a.x, e.a.y, e.b.x, e.b.y, i * 1337)}
              stroke={edgeColor(e.kind)} stroke-width="5"
              opacity={edgeOpacity(e.kind) * 0.35}
              fill="none" stroke-linecap="round"
              style="filter: blur(0.6px)" />
        <path d={brushPath(e.a.x, e.a.y, e.b.x, e.b.y, i * 1337)}
              stroke={edgeColor(e.kind)} stroke-width="1.4"
              opacity={edgeOpacity(e.kind)}
              fill="none" stroke-linecap="round" />
      {/if}
    {/each}
  </g>

  <!-- nodes by kind -->
  <g class="nodes">
    {#each positions as p}
      {@const ent = snap.entities[p.id]}
      {#if ent}
        <g class="node node-{p.kind}"
           class:is-selected={p.id === selected}
           class:is-neighbor={isHighlighted(p.id) && p.id !== selected}
           class:is-dim={dim(p)}
           class:is-blooming={snap.flowers.includes(p.id)}
           class:is-pruning={ent.pruning_severity > 0}
           on:click|stopPropagation={() => onSelect(p.id)}
           style="--phase: {p.phase}s">

          {#if p.kind === "ecosystem"}
            <circle cx={p.x} cy={p.y} r={p.r * 1.35}
                    fill="var(--shinshu)" stroke="var(--sumi)" stroke-width="2.2"
                    style="filter: drop-shadow(0 1px 0 rgba(0,0,0,0.15))" />
            <text x={p.x} y={p.y + 7} text-anchor="middle"
                  fill="var(--washi)" font-size="22" font-weight="700">縁</text>
          {:else if p.kind === "organism"}
            <path d={sealSquarePath(p.x, p.y, p.r)}
                  fill="var(--sumi)" stroke="var(--shinshu)" stroke-width="2.2" />
            <text x={p.x} y={p.y + 6} text-anchor="middle"
                  fill="var(--washi)" font-size="18" font-weight="700">中</text>
          {:else if p.kind === "axis"}
            {@const score = snap.axis_scores[p.id.replace("axis/", "")] || 0}
            <path d={sealSquarePath(p.x, p.y, p.r)}
                  fill={score >= 8 ? "var(--moegi)" : (score >= 5 ? "var(--kincha)" : "var(--suou)")}
                  stroke="var(--sumi)" stroke-width="1.6" />
            <text x={p.x} y={p.y + 4} text-anchor="middle"
                  fill="var(--washi)" font-size="11">{score}</text>
          {:else if p.kind === "cell"}
            <path d={leafPath(p.x, p.y, p.r)}
                  fill="var(--moegi)" stroke="var(--sumi)" stroke-width="1.0"
                  opacity={ent.pruning_severity > 0 ? 0.5 : 0.9} />
          {:else if p.kind === "app"}
            <path d={fanPath(p.x, p.y, p.r)}
                  fill="var(--washi-deep)" stroke="var(--sumi-soft)" stroke-width="0.9" />
          {:else if p.kind === "adr"}
            <circle cx={p.x} cy={p.y} r={p.r}        fill="none" stroke="var(--kincha)" stroke-width="0.6" opacity="0.55" />
            <circle cx={p.x} cy={p.y} r={p.r * 0.65} fill="none" stroke="var(--kincha)" stroke-width="0.6" opacity="0.7" />
            <circle cx={p.x} cy={p.y} r={p.r * 0.32} fill="var(--kincha)" opacity="0.6" />
          {:else if p.kind === "fruit"}
            <circle cx={p.x} cy={p.y} r={p.r}
                    fill="var(--shinshu)" stroke="var(--sumi)" stroke-width="1.4" />
            <path d={`M ${p.x - p.r * 0.35} ${p.y - p.r * 0.65} Q ${p.x} ${p.y - p.r * 0.95}, ${p.x + p.r * 0.45} ${p.y - p.r * 0.5}`}
                  fill="none" stroke="var(--sumi)" stroke-width="1.0" opacity="0.7" />
          {:else if p.kind === "seed"}
            <path d={kotodamaPath(p.x, p.y, p.r)}
                  fill="var(--ai)" stroke="var(--sumi)" stroke-width="0.9" />
            <circle cx={p.x + p.r * 0.45} cy={p.y - p.r * 0.45} r="1.4" fill="var(--washi)" opacity="0.7" />
          {/if}

          {#if p.kind === "axis" || p.kind === "ecosystem" || p.kind === "organism"}
            <text x={p.x} y={p.y + p.r + 14} text-anchor="middle"
                  class="node-label" font-size="11">
              {ent.title.split(" ")[0]}
            </text>
          {/if}
          {#if ent.pruning_severity > 0}
            <circle cx={p.x + p.r * 0.7} cy={p.y - p.r * 0.7} r="3"
                    fill="var(--suou)" stroke="var(--washi)" stroke-width="0.8" />
          {/if}
        </g>
      {/if}
    {/each}
  </g>

  <!-- ink-bleed pulse on selection -->
  {#if selected}
    {@const sp = positions.find(p => p.id === selected)}
    {#if sp}
      <circle cx={sp.x} cy={sp.y} r="6"
              fill="none" stroke="var(--shinshu)" stroke-width="1.8" opacity="0.4">
        <animate attributeName="r" from="6" to="80" dur="1.4s" repeatCount="indefinite" />
        <animate attributeName="opacity" from="0.55" to="0" dur="1.4s" repeatCount="indefinite" />
      </circle>
    {/if}
  {/if}
</svg>

<style>
  svg.graph { width: 100%; height: 100%; display: block; }
  .node { cursor: pointer; transition: opacity 0.25s var(--ease-settle); transform-origin: center; }
  .node-label { fill: var(--sumi); font-family: var(--font-mincho); letter-spacing: 0.02em; }
  .is-dim { opacity: 0.22; }
  .is-neighbor { filter: drop-shadow(0 0 6px rgba(185, 50, 47, 0.35)); }
  .is-selected { filter: drop-shadow(0 0 10px rgba(185, 50, 47, 0.7)); }
  .is-pruning { filter: saturate(0.4); }

  /* Breathing — each node has a randomized phase via inline --phase */
  .node {
    animation: breathe 6.4s ease-in-out infinite;
    animation-delay: var(--phase);
  }
  @keyframes breathe {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.025); }
  }
  .is-blooming {
    animation: bloom 4.5s ease-in-out infinite;
  }
  @keyframes bloom {
    0%, 100% { transform: scale(1); }
    50%      { transform: scale(1.07); filter: drop-shadow(0 0 6px rgba(217, 122, 109, 0.45)); }
  }
</style>
