<script lang="ts">
  import type { ActorContext } from '$lib/types';

  let { ctx }: { ctx: ActorContext } = $props();

  const CMD = 'etzhayyim.kami.v1.KamiCommandService';
  const QRY = 'etzhayyim.kami.v1.KamiQueryService';

  // ── Types ──
  interface Island {
    'island_id': string;
    title: string;
    genre: string;
    state: string;
    max_players?: number;
  }
  interface SceneData {
    name?: string;
    entities?: unknown[];
  }

  // ── State ──
  type View = 'home' | 'create' | 'browse' | 'play' | 'preview';
  let view = $state<View>('home');
  let title = $state('');
  let genre = $state('sandbox');
  let prompt = $state('');
  let template = $state('minecraft');
  let islandId = $state<string | null>(null);
  let sceneJson = $state<string | null>(null);
  let generating = $state(false);
  let publishing = $state(false);
  let published = $state(false);
  let error = $state<string | null>(null);
  let islands = $state<Island[]>([]);
  let playingIslandId = $state<string | null>(null);
  let guestId = $state<string>(generateGuestId());
  let webgpuSupported = $state(true);

  const genres = ['sandbox', 'action', 'puzzle', 'rpg', 'social', 'racing', 'rhythm', 'strategy'];
  const templates = [
    { id: 'minecraft', name: 'Survival Craft', desc: 'Minecraft-style voxel world with trees, caves, ores', icon: '\u{1F333}', color: '#4ade80' },
    { id: 'fortnite', name: 'Battle Royale', desc: 'Fortnite-style arena with buildings, loot, storm', icon: '\u{1F3AF}', color: '#f97316' },
    { id: 'roblox', name: 'Obby Course', desc: 'Roblox-style obstacle course with jumps and coins', icon: '\u{1F3AE}', color: '#a855f7' },
    { id: 'flat', name: 'Flat Creative', desc: 'Empty flat world — build anything from scratch', icon: '\u{1F4D0}', color: '#3b82f6' },
  ];

  function generateGuestId(): string {
    return `did:web:kami.etzhayyim.com:guest:${Date.now().toString(36)}${Math.random().toString(36).slice(2, 6)}`;
  }

  // ── API ──
  async function api<T = Record<string, unknown>>(method: string, body: Record<string, unknown>): Promise<T> {
    return ctx.backend.call<T>(CMD, method, body);
  }
  async function query<T = Record<string, unknown>>(method: string, body: Record<string, unknown>): Promise<T> {
    return ctx.backend.call<T>(QRY, method, body);
  }

  // ── Actions ──
  async function browseWorlds() {
    error = null;
    try {
      const result = await api<Island[]>('browse-worlds', { limit: 50 });
      islands = Array.isArray(result) ? result : [];
    } catch { islands = []; }
    view = 'browse';
  }

  async function createWorld() {
    error = null;
    generating = true;
    try {
      const result = await api<{ 'island_id': string; scene: SceneData; 'guest_id': string; error?: string }>('guest-create-island', {
        title: title || 'My World',
        genre,
        template,
        'max_players': 16,
        'guest_id': guestId,
      });
      if (result.error) { error = result.error; generating = false; return; }
      islandId = result.island_id;
      sceneJson = typeof result.scene === 'string' ? result.scene : JSON.stringify(result.scene);
      view = 'preview';
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to create world';
    } finally {
      generating = false;
    }
  }

  async function regenerate() {
    generating = true;
    error = null;
    try {
      const result = await api<{ scene: SceneData; error?: string }>('guest-generate-island', {
        'island_id': islandId,
        prompt: prompt || `a ${genre} world called ${title}`,
        genre,
        template,
        'guest_id': guestId,
      });
      if (result.error) { error = result.error; generating = false; return; }
      sceneJson = typeof result.scene === 'string' ? result.scene : JSON.stringify(result.scene);
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to regenerate';
    } finally {
      generating = false;
    }
  }

  async function publishWorld() {
    publishing = true;
    error = null;
    try {
      const result = await api<{ error?: string }>('publish-island', {
        'island_id': islandId,
        title: title || 'My World',
        tags: [genre, template],
      });
      if (result.error) { error = result.error; publishing = false; return; }
      published = true;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Publish failed';
    } finally {
      publishing = false;
    }
  }

  async function playWorld(id: string) {
    error = null;
    playingIslandId = id;
    try {
      // Get scene for this world
      const result = await api<Array<{ source?: string }>>('get-world-scene', { 'island_id': id });
      if (Array.isArray(result) && result.length > 0 && result[0].source) {
        sceneJson = result[0].source;
      } else {
        // Fallback: generate a fresh scene
        sceneJson = null;
      }
    } catch {
      sceneJson = null;
    }
    view = 'play';
    // Initialize WebGPU after DOM update
    requestAnimationFrame(() => initWebGPU());
  }

  async function playCurrentWorld() {
    if (!islandId) return;
    playingIslandId = islandId;
    view = 'play';
    requestAnimationFrame(() => initWebGPU());
  }

  async function initWebGPU() {
    if (!('gpu' in navigator)) {
      webgpuSupported = false;
      return;
    }
    try {
      // Dynamic import of kami-web WASM
      // @ts-ignore — loaded at runtime from CDN
      const kami = await import('https://cdn.etzhayyim.com/k4m1w0rk/kami_web.js');
      await kami.default(); // init WASM
      if (sceneJson) {
        await kami.run_with_scene('kami-play-canvas', sceneJson);
      } else {
        await kami.run('kami-play-canvas');
      }
    } catch (e) {
      console.error('WebGPU init failed:', e);
      webgpuSupported = false;
    }
  }

  function resetForm() {
    view = 'home';
    islandId = null;
    published = false;
    sceneJson = null;
    title = '';
    prompt = '';
    playingIslandId = null;
  }

  function entityCount(json: string | null): number {
    if (!json) return 0;
    try { return JSON.parse(json).entities?.length ?? 0; } catch { return 0; }
  }

  function sceneName(json: string | null): string {
    if (!json) return '';
    try { return JSON.parse(json).name ?? ''; } catch { return ''; }
  }

  // Load published worlds on mount
  browseWorlds().then(() => { view = 'home'; });
</script>

<div style="max-width: 600px; margin: 0 auto; padding: 16px; color: var(--gv2-text-primary, #e0e0e0); min-height: 100vh;">

  <!-- ═══ PLAY MODE ═══ -->
  {#if view === 'play'}
    <div style="position: relative;">
      <button onclick={resetForm}
        style="position: absolute; top: 8px; left: 8px; z-index: 10; padding: 8px 16px; border: none; border-radius: 8px; background: rgba(0,0,0,0.6); color: #fff; font-size: 13px; cursor: pointer; backdrop-filter: blur(8px); min-height: 36px;">
        Exit
      </button>
      {#if !webgpuSupported}
        <div style="padding: 60px 20px; text-align: center; background: rgba(255,255,255,0.05); border-radius: 12px;">
          <p style="font-size: 18px; font-weight: 700; margin: 0 0 8px;">WebGPU Not Available</p>
          <p style="color: var(--gv2-text-muted, #888); font-size: 14px; margin: 0;">Use Chrome 113+ or Edge 113+ with WebGPU enabled.</p>
        </div>
      {:else}
        <canvas id="kami-play-canvas" width="800" height="500"
          style="width: 100%; aspect-ratio: 16/10; border-radius: 12px; background: #0a0a0f; display: block; cursor: crosshair;"></canvas>
        <div style="display: flex; align-items: center; gap: 8px; padding: 8px 0; color: var(--gv2-text-muted, #888); font-size: 12px;">
          <span>WASD Move</span>
          <span>|</span>
          <span>Mouse Look (click to lock)</span>
          <span>|</span>
          <span>Space/Shift Up/Down</span>
        </div>
      {/if}
    </div>

  <!-- ═══ HOME ═══ -->
  {:else if view === 'home'}
    <header style="text-align: center; margin-bottom: 24px;">
      <h1 style="font-size: 28px; font-weight: 800; margin: 0; background: linear-gradient(135deg, #f59e0b, #ef4444); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">KAMI</h1>
      <p style="color: var(--gv2-text-muted, #888); margin: 4px 0 0; font-size: 14px;">Create and play 3D worlds — no login required</p>
    </header>

    <button onclick={() => { view = 'create'; }}
      style="width: 100%; padding: 16px; border: none; border-radius: 12px; background: linear-gradient(135deg, #f59e0b, #ef4444); color: #000; font-size: 16px; font-weight: 700; cursor: pointer; margin: 0 0 12px; min-height: 52px;">
      Create New World
    </button>

    <button onclick={browseWorlds}
      style="width: 100%; padding: 14px; border: 1px solid rgba(255,255,255,0.12); border-radius: 12px; background: rgba(255,255,255,0.06); color: inherit; font-size: 15px; font-weight: 600; cursor: pointer; margin: 0 0 24px; min-height: 48px;">
      Browse Worlds ({islands.length})
    </button>

    {#if islands.length > 0}
      <h2 style="font-size: 16px; font-weight: 700; margin: 0 0 8px;">Popular Worlds</h2>
      {#each islands.slice(0, 6) as island}
        <button onclick={() => playWorld(island.island_id)}
          style="display: flex; align-items: center; gap: 8px; width: 100%; padding: 12px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; margin: 6px 0; cursor: pointer; color: inherit; text-align: left; min-height: 48px;">
          <strong style="font-size: 14px; flex: 1;">{island.title || island.island_id}</strong>
          <span style="font-size: 11px; padding: 2px 8px; background: rgba(255,255,255,0.1); border-radius: 4px;">{island.genre}</span>
          <span style="font-size: 13px; color: #f59e0b;">Play</span>
        </button>
      {/each}
    {/if}

  <!-- ═══ CREATE ═══ -->
  {:else if view === 'create'}
    <header style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
      <button onclick={resetForm}
        style="padding: 8px 12px; border: none; border-radius: 8px; background: rgba(255,255,255,0.08); color: inherit; cursor: pointer; font-size: 14px; min-height: 36px;">Back</button>
      <h2 style="font-size: 20px; font-weight: 700; margin: 0;">Create World</h2>
    </header>

    <h3 style="font-size: 14px; font-weight: 600; margin: 0 0 8px; color: var(--gv2-text-muted, #aaa);">Choose a template</h3>
    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 16px;">
      {#each templates as t}
        <button onclick={() => { template = t.id; }}
          style="padding: 14px 10px; border: 2px solid {template === t.id ? t.color : 'rgba(255,255,255,0.08)'}; border-radius: 12px; background: {template === t.id ? t.color + '15' : 'rgba(255,255,255,0.03)'}; color: inherit; cursor: pointer; text-align: center; min-height: 80px;">
          <div style="font-size: 24px; margin-bottom: 4px;">{t.icon}</div>
          <div style="font-size: 13px; font-weight: 700;">{t.name}</div>
          <div style="font-size: 11px; color: var(--gv2-text-muted, #888); margin-top: 2px;">{t.desc}</div>
        </button>
      {/each}
    </div>

    <input bind:value={title} placeholder="World name (optional)"
      style="width: 100%; padding: 10px; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(255,255,255,0.06); color: inherit; font-size: 14px; box-sizing: border-box; outline: none;" />

    <select bind:value={genre}
      style="width: 100%; padding: 10px; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(255,255,255,0.06); color: inherit; font-size: 14px; box-sizing: border-box; outline: none;">
      {#each genres as g}
        <option value={g}>{g}</option>
      {/each}
    </select>

    <textarea bind:value={prompt} placeholder="Describe your world (optional — AI fills in the rest)" rows="2"
      style="width: 100%; padding: 10px; margin: 6px 0; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; background: rgba(255,255,255,0.06); color: inherit; font-size: 14px; box-sizing: border-box; outline: none; resize: vertical;"></textarea>

    <button onclick={createWorld} disabled={generating}
      style="width: 100%; padding: 14px; border: none; border-radius: 10px; background: {generating ? 'rgba(255,255,255,0.06)' : 'linear-gradient(135deg, #f59e0b, #ef4444)'}; color: {generating ? 'rgba(255,255,255,0.3)' : '#000'}; font-size: 15px; font-weight: 700; cursor: pointer; margin: 8px 0; min-height: 48px;">
      {generating ? 'Generating...' : 'Create World'}
    </button>

  <!-- ═══ PREVIEW ═══ -->
  {:else if view === 'preview'}
    <header style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
      <button onclick={resetForm}
        style="padding: 8px 12px; border: none; border-radius: 8px; background: rgba(255,255,255,0.08); color: inherit; cursor: pointer; font-size: 14px; min-height: 36px;">Back</button>
      <h2 style="font-size: 18px; font-weight: 700; margin: 0;">{title || 'My World'}</h2>
      <span style="font-size: 11px; padding: 2px 8px; background: rgba(255,255,255,0.1); border-radius: 4px; margin-left: auto;">{template}</span>
    </header>

    {#if generating}
      <div style="padding: 40px; text-align: center; color: #f59e0b; font-size: 14px;">Generating world...</div>
    {:else if sceneJson}
      <div style="background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.08); border-radius: 12px; padding: 12px; margin-bottom: 12px;">
        <p style="margin: 0 0 4px; font-size: 15px; font-weight: 600;">{sceneName(sceneJson) || title || 'My World'}</p>
        <p style="margin: 0; font-size: 12px; color: var(--gv2-text-muted, #888);">{entityCount(sceneJson)} entities | {genre} | {template}</p>
      </div>

      <div style="display: flex; gap: 8px; flex-wrap: wrap;">
        <button onclick={playCurrentWorld}
          style="flex: 1; padding: 14px; border: none; border-radius: 10px; background: linear-gradient(135deg, #f59e0b, #ef4444); color: #000; font-size: 15px; font-weight: 700; cursor: pointer; min-height: 48px;">
          Play Now
        </button>
        <button onclick={regenerate} disabled={generating}
          style="padding: 14px 18px; border: none; border-radius: 10px; background: rgba(255,255,255,0.08); color: inherit; font-size: 14px; cursor: pointer; min-height: 48px;">
          Regenerate
        </button>
      </div>

      {#if !published}
        <button onclick={publishWorld} disabled={publishing}
          style="width: 100%; padding: 12px; border: 1px solid rgba(255,255,255,0.12); border-radius: 10px; background: rgba(255,255,255,0.04); color: inherit; font-size: 14px; cursor: pointer; margin-top: 8px; opacity: {publishing ? 0.5 : 1}; min-height: 44px;">
          {publishing ? 'Publishing...' : 'Publish to KAMI Worlds'}
        </button>
      {:else}
        <div style="text-align: center; padding: 12px; margin-top: 8px; background: rgba(74,222,128,0.1); border-radius: 10px;">
          <p style="margin: 0; font-size: 14px; color: #4ade80; font-weight: 600;">Published! Anyone can play your world.</p>
        </div>
      {/if}
    {/if}

  <!-- ═══ BROWSE ═══ -->
  {:else if view === 'browse'}
    <header style="display: flex; align-items: center; gap: 8px; margin-bottom: 16px;">
      <button onclick={resetForm}
        style="padding: 8px 12px; border: none; border-radius: 8px; background: rgba(255,255,255,0.08); color: inherit; cursor: pointer; font-size: 14px; min-height: 36px;">Back</button>
      <h2 style="font-size: 20px; font-weight: 700; margin: 0;">Browse Worlds</h2>
      <span style="font-size: 12px; color: var(--gv2-text-muted, #888); margin-left: auto;">{islands.length} worlds</span>
    </header>

    {#if islands.length === 0}
      <div style="text-align: center; padding: 40px; color: var(--gv2-text-muted, #888);">
        <p style="font-size: 14px;">No worlds published yet. Be the first!</p>
        <button onclick={() => { view = 'create'; }}
          style="padding: 10px 20px; border: none; border-radius: 8px; background: #f59e0b; color: #000; font-size: 14px; font-weight: 600; cursor: pointer; margin-top: 8px; min-height: 40px;">Create World</button>
      </div>
    {:else}
      {#each islands as island}
        <button onclick={() => playWorld(island.island_id)}
          style="display: flex; align-items: center; gap: 10px; width: 100%; padding: 14px; background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; margin: 6px 0; cursor: pointer; color: inherit; text-align: left; min-height: 52px;">
          <div style="flex: 1;">
            <strong style="font-size: 14px; display: block;">{island.title || island.island_id}</strong>
            <span style="font-size: 12px; color: var(--gv2-text-muted, #888);">{island.genre}{island.max_players ? ` | ${island.max_players} players` : ''}</span>
          </div>
          <span style="padding: 6px 14px; border-radius: 8px; background: linear-gradient(135deg, #f59e0b, #ef4444); color: #000; font-size: 13px; font-weight: 700;">Play</span>
        </button>
      {/each}
    {/if}
  {/if}

  {#if error}
    <div style="background: rgba(239,68,68,0.1); border: 1px solid rgba(239,68,68,0.2); color: #fca5a5; padding: 10px 14px; border-radius: 8px; margin-top: 12px; font-size: 13px;">{error}</div>
  {/if}
</div>
