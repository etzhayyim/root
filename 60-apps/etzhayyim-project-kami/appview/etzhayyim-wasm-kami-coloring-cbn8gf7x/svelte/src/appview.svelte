<script lang="ts">
  import type { ActorContext } from '$lib/types';

  let { ctx }: { ctx: ActorContext } = $props();

  const CMD = 'etzhayyim.kami.v1.KamiColoringCommandService';

  // ── State ──
  let view = $state<'browse' | 'canvas' | 'create'>('browse');
  let loading = $state(false);
  let error = $state('');

  // Browse
  let canvases = $state<Canvas[]>([]);

  // Canvas view
  let currentCanvas = $state<CanvasData | null>(null);
  let selectedColor = $state('#FF6B6B');
  let palette = $state<string[]>([
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
    '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
    '#F8C471', '#82E0AA', '#F1948A', '#AED6F1', '#D7BDE2',
    '#A3E4D7',
  ]);

  // Create
  let newName = $state('');
  let newWidth = $state(10);
  let newHeight = $state(10);

  // ── Types ──
  interface Canvas {
    'canvas_id': string;
    name: string;
    width: number;
    height: number;
    'cell_count': number;
    visibility: string;
    'created_at': string;
  }

  interface Cell {
    index: number;
    row: number;
    col: number;
    'color_number': number;
    'filled_color': string;
    'filled_by': string;
  }

  interface CanvasData {
    'canvas_id': string;
    name: string;
    width: number;
    height: number;
    'cell_count': number;
    palette: string[];
    cells: Cell[];
  }

  // ── API helpers ──
  async function rpc(method: string, body: Record<string, unknown>) {
    loading = true;
    error = '';
    try {
      const res = await ctx.backend.call<Record<string, any>>(CMD, method, body);
      return res;
    } catch (e: any) {
      error = e?.message || 'Request failed';
      return null;
    } finally {
      loading = false;
    }
  }

  // ── Actions ──
  async function browseCanvases() {
    const res = await rpc('BrowseCanvases', { visibility: 'public', limit: 50, offset: 0 });
    if (res) {
      canvases = res.canvases || [];
    }
  }

  async function openCanvas(id: string) {
    const res = await rpc('GetCanvas', { 'canvas_id': id });
    if (res) {
      currentCanvas = res as CanvasData;
      if (res.palette?.length) palette = res.palette;
      view = 'canvas';
    }
  }

  async function paintCell(cellIndex: number) {
    if (!currentCanvas) return;
    const res = await rpc('PaintCell', {
      'canvas_id': currentCanvas.canvas_id,
      'cell_index': cellIndex,
      'filled_color': selectedColor,
    });
    if (res && currentCanvas) {
      const cells = [...currentCanvas.cells];
      const idx = cells.findIndex((c) => c.index === cellIndex);
      if (idx >= 0) {
        cells[idx] = { ...cells[idx], 'filled_color': selectedColor };
        currentCanvas = { ...currentCanvas, cells };
      }
    }
  }

  async function createCanvas() {
    if (!newName.trim()) return;
    const res = await rpc('CreateCanvas', {
      name: newName,
      width: newWidth,
      height: newHeight,
      visibility: 'public',
    });
    if (res?.canvas_id) {
      newName = '';
      await openCanvas(res.canvas_id);
    }
  }

  // ── Computed ──
  let progress = $derived(() => {
    if (!currentCanvas) return 0;
    const filled = currentCanvas.cells.filter((c) => c.filled_color).length;
    return Math.round((filled / currentCanvas.cell_count) * 100);
  });

  // ── Init ──
  $effect(() => {
    browseCanvases();
  });
</script>

<!-- ── Browse View ── -->
{#if view === 'browse'}
  <div style="padding: 16px; max-width: 600px; margin: 0 auto;">
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px;">
      <h2 style="margin: 0; font-size: 20px;">KAMI Coloring</h2>
      <button
        onclick={() => { view = 'create'; }}
        style="padding: 8px 16px; background: #4ECDC4; color: white; border: none; border-radius: 8px; font-weight: 600; cursor: pointer;"
      >
        + New Canvas
      </button>
    </div>

    {#if error}
      <div style="padding: 8px 12px; background: #fef2f2; color: #dc2626; border-radius: 8px; margin-bottom: 12px; font-size: 13px;">
        {error}
      </div>
    {/if}

    {#if loading}
      <div style="text-align: center; padding: 40px; color: #9ca3af;">Loading...</div>
    {:else if canvases.length === 0}
      <div style="text-align: center; padding: 40px; color: #9ca3af;">
        <div style="font-size: 48px; margin-bottom: 8px;">🎨</div>
        <div>No canvases yet. Create one!</div>
      </div>
    {:else}
      <div style="display: grid; gap: 12px;">
        {#each canvases as c}
          <button
            onclick={() => openCanvas(c.canvas_id)}
            style="display: flex; align-items: center; gap: 12px; padding: 12px 16px; background: white; border: 1px solid #e5e7eb; border-radius: 12px; text-align: left; cursor: pointer; width: 100%;"
          >
            <div style="width: 48px; height: 48px; background: linear-gradient(135deg, #FF6B6B, #4ECDC4); border-radius: 8px; display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 14px;">
              {c.width}x{c.height}
            </div>
            <div style="flex: 1; min-width: 0;">
              <div style="font-weight: 600; font-size: 15px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{c.name}</div>
              <div style="font-size: 12px; color: #9ca3af;">{c.cell_count} cells</div>
            </div>
          </button>
        {/each}
      </div>
    {/if}
  </div>

<!-- ── Create View ── -->
{:else if view === 'create'}
  <div style="padding: 16px; max-width: 600px; margin: 0 auto;">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 20px;">
      <button aria-label="Back" onclick={() => { view = 'browse'; }} style="background: none; border: none; font-size: 20px; cursor: pointer; padding: 4px;">←</button>
      <h2 style="margin: 0; font-size: 20px;">New Canvas</h2>
    </div>

    <div style="display: flex; flex-direction: column; gap: 16px;">
      <div>
        <label for="canvas-name" style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #374151;">Name</label>
        <input
          id="canvas-name"
          bind:value={newName}
          placeholder="My pixel art"
          style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 15px; box-sizing: border-box;"
        />
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
        <div>
          <label for="canvas-width" style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #374151;">Width</label>
          <input
            id="canvas-width"
            type="number" bind:value={newWidth} min="3" max="50"
            style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 15px; box-sizing: border-box;"
          />
        </div>
        <div>
          <label for="canvas-height" style="display: block; font-size: 13px; font-weight: 600; margin-bottom: 4px; color: #374151;">Height</label>
          <input
            id="canvas-height"
            type="number" bind:value={newHeight} min="3" max="50"
            style="width: 100%; padding: 10px 12px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 15px; box-sizing: border-box;"
          />
        </div>
      </div>

      <div style="text-align: center; padding: 20px; background: #f9fafb; border-radius: 12px; color: #6b7280;">
        Preview: {newWidth} x {newHeight} = {newWidth * newHeight} cells
      </div>

      <button
        onclick={createCanvas}
        disabled={loading || !newName.trim()}
        style="padding: 12px; background: {newName.trim() ? '#4ECDC4' : '#d1d5db'}; color: white; border: none; border-radius: 8px; font-weight: 600; font-size: 16px; cursor: pointer;"
      >
        {loading ? 'Creating...' : 'Create Canvas'}
      </button>
    </div>
  </div>

<!-- ── Canvas View ── -->
{:else if view === 'canvas' && currentCanvas}
  <div style="padding: 12px; max-width: 600px; margin: 0 auto;">
    <!-- Header -->
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
      <button aria-label="Back" onclick={() => { view = 'browse'; currentCanvas = null; browseCanvases(); }} style="background: none; border: none; font-size: 20px; cursor: pointer; padding: 4px;">←</button>
      <div style="flex: 1; min-width: 0;">
        <div style="font-weight: 600; font-size: 16px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
          {currentCanvas.name}
        </div>
        <div style="font-size: 12px; color: #9ca3af;">{progress()}% complete</div>
      </div>
    </div>

    <!-- Progress bar -->
    <div style="height: 4px; background: #e5e7eb; border-radius: 2px; margin-bottom: 12px; overflow: hidden;">
      <div style="height: 100%; background: #4ECDC4; border-radius: 2px; transition: width 0.3s; width: {progress()}%;"></div>
    </div>

    <!-- Grid -->
    <div
      style="display: grid; grid-template-columns: repeat({currentCanvas.width}, 1fr); gap: 1px; background: #d1d5db; border-radius: 8px; overflow: hidden; aspect-ratio: {currentCanvas.width} / {currentCanvas.height}; margin-bottom: 12px;"
    >
      {#each currentCanvas.cells as cell}
        <button
          onclick={() => paintCell(cell.index)}
          disabled={loading}
          style="
            aspect-ratio: 1;
            border: none;
            cursor: pointer;
            background: {cell.filled_color || '#f9fafb'};
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: {currentCanvas.width > 20 ? '6px' : currentCanvas.width > 10 ? '8px' : '11px'};
            color: {cell.filled_color ? 'transparent' : '#9ca3af'};
            padding: 0;
            min-width: 0;
          "
        >
          {#if !cell.filled_color && cell.color_number > 0}
            {cell.color_number}
          {/if}
        </button>
      {/each}
    </div>

    <!-- Palette -->
    <div style="display: flex; gap: 6px; flex-wrap: wrap; justify-content: center; padding: 8px; background: white; border-radius: 12px; border: 1px solid #e5e7eb;">
      {#each palette as color}
        <button
          aria-label="Select color {color}"
          onclick={() => { selectedColor = color; }}
          style="
            width: 32px; height: 32px;
            border-radius: 50%;
            border: 3px solid {selectedColor === color ? '#1f2937' : 'transparent'};
            background: {color};
            cursor: pointer;
            box-shadow: {selectedColor === color ? '0 0 0 2px white, 0 0 0 4px ' + color : 'none'};
            transition: all 0.15s;
          "
        ></button>
      {/each}
    </div>

    {#if error}
      <div style="padding: 8px 12px; background: #fef2f2; color: #dc2626; border-radius: 8px; margin-top: 8px; font-size: 13px;">
        {error}
      </div>
    {/if}
  </div>
{/if}
