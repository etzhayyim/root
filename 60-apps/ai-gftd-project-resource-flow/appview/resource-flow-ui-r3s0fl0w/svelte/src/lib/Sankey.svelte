<script lang="ts">
  import { onMount } from 'svelte';
  import { sankey, sankeyLinkHorizontal, sankeyJustify } from 'd3-sankey';
  import { schemeTableau10 } from 'd3-scale-chromatic';
  import type { SankeyEdge } from './rf-xrpc';
  import { resolveProfiles, shortLabel } from './rf-xrpc';

  type Props = {
    edges: SankeyEdge[];
    valueKey: 'amount_sum' | 'total_count' | 'event_count' | 'headcount_sum';
    width?: number;
    height?: number;
  };

  let { edges, valueKey, width = 960, height = 540 }: Props = $props();

  let svgEl: SVGSVGElement | undefined = $state();
  let labelMap = $state<Record<string, string>>({});

  // Build the d3-sankey graph from the edge list.
  function buildGraph(rows: SankeyEdge[]) {
    const nodeIds = new Set<string>();
    for (const e of rows) {
      if (e.source_did) nodeIds.add(e.source_did);
      if (e.counterparty_did) nodeIds.add(e.counterparty_did);
    }
    const nodes = Array.from(nodeIds).map((id) => ({ id, name: labelMap[id] ?? shortLabel(id) }));
    const idx = new Map<string, number>(nodes.map((n, i) => [n.id, i]));
    const links: { source: number; target: number; value: number; row: SankeyEdge }[] = [];
    for (const e of rows) {
      const s = idx.get(e.source_did);
      const t = idx.get(e.counterparty_did);
      const raw = Number((e as any)[valueKey] ?? 0);
      const v = Number.isFinite(raw) ? raw : 0;
      // d3-sankey rejects non-positive link values; fall back to event_count.
      const value = v > 0 ? v : Math.max(1, Number(e.event_count ?? 1));
      if (s != null && t != null && s !== t) {
        links.push({ source: s, target: t, value, row: e });
      }
    }
    return { nodes, links };
  }

  function render() {
    if (!svgEl) return;
    while (svgEl.firstChild) svgEl.removeChild(svgEl.firstChild);
    const graph = buildGraph(edges);
    if (graph.links.length === 0) return;

    const layout = sankey<{ id: string; name: string }, { row: SankeyEdge }>()
      .nodeId((d: any) => d.id)
      .nodeAlign(sankeyJustify)
      .nodeWidth(14)
      .nodePadding(10)
      .extent([[1, 1], [width - 1, height - 6]]);

    const { nodes: laidNodes, links: laidLinks } = layout({
      nodes: graph.nodes.map((n) => ({ ...n })),
      links: graph.links.map((l) => ({ ...l })),
    } as any);

    // links first (under nodes)
    for (let i = 0; i < laidLinks.length; i++) {
      const l: any = laidLinks[i];
      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      path.setAttribute('d', sankeyLinkHorizontal()(l) ?? '');
      path.setAttribute('fill', 'none');
      path.setAttribute('stroke', schemeTableau10[i % 10]);
      path.setAttribute('stroke-opacity', '0.45');
      path.setAttribute('stroke-width', String(Math.max(1, l.width ?? 1)));
      const title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
      const r = l.row as SankeyEdge;
      title.textContent =
        `${(l.source as any).name} → ${(l.target as any).name}\n` +
        `${valueKey} = ${l.value}\n` +
        `period=${r.fiscal_period}  isic=${r.industry_code}` +
        (r.currency ? `  ${r.currency}` : '') +
        (r.service_class ? `  ${r.service_class}` : '');
      path.appendChild(title);
      svgEl.appendChild(path);
    }
    // nodes
    for (const n of laidNodes as any[]) {
      const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect');
      rect.setAttribute('x', n.x0);
      rect.setAttribute('y', n.y0);
      rect.setAttribute('width', n.x1 - n.x0);
      rect.setAttribute('height', Math.max(1, n.y1 - n.y0));
      rect.setAttribute('fill', '#9ec1ff');
      svgEl.appendChild(rect);

      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      const onLeft = n.x0 < width / 2;
      text.setAttribute('x', String(onLeft ? n.x1 + 6 : n.x0 - 6));
      text.setAttribute('y', String((n.y0 + n.y1) / 2));
      text.setAttribute('dy', '0.35em');
      text.setAttribute('text-anchor', onLeft ? 'start' : 'end');
      text.setAttribute('fill', '#e6e6e6');
      text.setAttribute('font-size', '11');
      text.textContent = n.name;
      svgEl.appendChild(text);
    }
  }

  // Resolve display names for every distinct DID in the edge list and re-render.
  $effect(() => {
    const ids = new Set<string>();
    for (const e of edges) {
      if (e.source_did) ids.add(e.source_did);
      if (e.counterparty_did) ids.add(e.counterparty_did);
    }
    const todo: string[] = [];
    for (const id of ids) if (!(id in labelMap)) todo.push(id);
    if (todo.length === 0) {
      render();
      return;
    }
    // ADR-0074 bulk resolver — single round-trip via getActorLabels,
    // falls back to N getProfile calls when the cluster view is empty.
    resolveProfiles(todo).then((map) => {
      const next = { ...labelMap };
      for (const id of todo) {
        const p = map[id];
        next[id] = p?.displayName ?? p?.handle ?? shortLabel(id);
      }
      labelMap = next;
      render();
    });
  });

  onMount(render);
</script>

<svg bind:this={svgEl} width={width} height={height} role="img" aria-label="Resource flow sankey"></svg>
