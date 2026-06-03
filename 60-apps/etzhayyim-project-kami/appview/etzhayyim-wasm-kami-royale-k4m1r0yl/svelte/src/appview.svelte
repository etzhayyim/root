<script lang="ts">
  import type { ActorContext } from '$lib/types';

  let { ctx }: { ctx: ActorContext } = $props();

  const CMD = 'etzhayyim.kami.v1.KamiRoyaleCommandService';

  // ── State ──
  let selectedChar = $state(0);
  let mode = $state<'casual' | 'ranked'>('casual');
  let leaderboardOpen = $state(false);
  let loading = $state(false);
  let error = $state('');
  let playerCount = $state(47);
  let view = $state<'lobby' | 'game'>('lobby');
  let matchId = $state('');
  let guestNickname = $state('');
  let gameAlive = $state(100);
  let gamePhase = $state<'bus' | 'dropping' | 'playing' | 'eliminated' | 'victory'>('bus');
  let gameKills = $state(0);
  let gamePlacement = $state(0);
  let gameStormPhase = $state(0);
  let gameTimer = $state(0);
  let gameInterval: ReturnType<typeof setInterval> | null = null;

  // ── Characters ──
  interface BrainrotChar {
    id: string;
    name: string;
    role: 'boss' | 'npc';
    body: string;
    bodyIcon: string;
    hair: string;
    accessory: string;
    skinHue: number;
    color: string;
    tagline: string;
  }

  const characters: BrainrotChar[] = [
    { id: 'char-skibidi-commander', name: 'Skibidi Commander', role: 'boss', body: 'stocky', bodyIcon: '\u{1F6BD}', hair: 'buzz', accessory: 'sunglasses', skinHue: 0.08, color: '#3b82f6', tagline: 'Flush the competition' },
    { id: 'char-sigma-male', name: 'Sigma Grindset', role: 'npc', body: 'athletic', bodyIcon: '\u{1F4AA}', hair: 'spiky', accessory: 'sunglasses', skinHue: 0.06, color: '#6b7280', tagline: 'On that grind 24/7' },
    { id: 'char-ohio-boss', name: 'Ohio Final Boss', role: 'boss', body: 'tall', bodyIcon: '\u{1F480}', hair: 'mohawk', accessory: 'mask', skinHue: 0.0, color: '#ef4444', tagline: 'Only in Ohio fr fr' },
    { id: 'char-grimace', name: 'Grimace', role: 'boss', body: 'stocky', bodyIcon: '\u{1F7E3}', hair: 'bald', accessory: 'none', skinHue: 0.75, color: '#a855f7', tagline: 'The shake is eternal' },
    { id: 'char-rizz-master', name: 'Rizz Master', role: 'npc', body: 'slim', bodyIcon: '\u{2728}', hair: 'wavy', accessory: 'earring', skinHue: 0.07, color: '#ec4899', tagline: 'W rizz no cap' },
    { id: 'char-fanum', name: 'Fanum Tax Collector', role: 'npc', body: 'average', bodyIcon: '\u{1F354}', hair: 'afro', accessory: 'hat', skinHue: 0.07, color: '#f97316', tagline: 'Taxing your loot' },
  ];

  // ── POIs ──
  interface POI {
    name: string;
    x: number;
    z: number;
    type: 'brainrot' | 'classic';
    color: string;
    loot: number;
  }

  const pois: POI[] = [
    { name: 'Skibidi Sewers', x: 350, z: 350, type: 'brainrot', color: '#ffffff', loot: 0.8 },
    { name: 'Sigma Summit', x: -450, z: 500, type: 'brainrot', color: '#4b5563', loot: 0.6 },
    { name: 'Ohio Outpost', x: 700, z: -400, type: 'brainrot', color: '#ef4444', loot: 0.9 },
    { name: 'Grimace Grotto', x: -300, z: 600, type: 'brainrot', color: '#a855f7', loot: 0.5 },
    { name: 'Rizz Resort', x: 500, z: 500, type: 'brainrot', color: '#ec4899', loot: 0.9 },
    { name: 'Fanum Food Court', x: -600, z: -300, type: 'brainrot', color: '#f97316', loot: 0.7 },
    { name: 'Tilted Towers', x: 0, z: 0, type: 'classic', color: '#64748b', loot: 0.9 },
    { name: 'Pleasant Park', x: -500, z: -500, type: 'classic', color: '#64748b', loot: 0.7 },
    { name: 'Retail Row', x: 400, z: -200, type: 'classic', color: '#64748b', loot: 0.7 },
    { name: 'Salty Springs', x: 100, z: -300, type: 'classic', color: '#64748b', loot: 0.6 },
    { name: 'Dusty Depot', x: -200, z: 100, type: 'classic', color: '#64748b', loot: 0.5 },
    { name: 'Lonely Lodge', x: 800, z: 200, type: 'classic', color: '#64748b', loot: 0.5 },
    { name: 'Snobby Shores', x: -900, z: 100, type: 'classic', color: '#64748b', loot: 0.6 },
    { name: 'Haunted Hills', x: -800, z: 400, type: 'classic', color: '#64748b', loot: 0.4 },
    { name: 'Junk Junction', x: -700, z: 700, type: 'classic', color: '#64748b', loot: 0.4 },
    { name: 'Lucky Landing', x: 200, z: 900, type: 'classic', color: '#64748b', loot: 0.5 },
    { name: 'Fatal Fields', x: 100, z: 600, type: 'classic', color: '#64748b', loot: 0.6 },
    { name: 'Flush Factory', x: -400, z: 800, type: 'classic', color: '#64748b', loot: 0.5 },
    { name: 'Greasy Grove', x: -600, z: 200, type: 'classic', color: '#64748b', loot: 0.6 },
    { name: 'Anarchy Acres', x: 300, z: -600, type: 'classic', color: '#64748b', loot: 0.5 },
    { name: 'Wailing Woods', x: 600, z: -700, type: 'classic', color: '#64748b', loot: 0.4 },
    { name: 'Tomato Town', x: -100, z: -500, type: 'classic', color: '#64748b', loot: 0.5 },
    { name: 'Loot Lake', x: 0, z: 300, type: 'classic', color: '#64748b', loot: 0.7 },
    { name: 'Shifty Shafts', x: -300, z: -200, type: 'classic', color: '#64748b', loot: 0.6 },
    { name: 'Moisty Mire', x: 900, z: 700, type: 'classic', color: '#64748b', loot: 0.4 },
    { name: 'Risky Reels', x: 500, z: -500, type: 'classic', color: '#64748b', loot: 0.5 },
  ];

  // ── Weapons ──
  interface BrainrotWeapon {
    name: string;
    rarity: string;
    rarityColor: string;
    damage: number;
    fireRate: number;
    magazine: number;
    flavor: string;
  }

  const weapons: BrainrotWeapon[] = [
    { name: 'Skibidi Plunger Launcher', rarity: 'Legendary', rarityColor: '#f97316', damage: 85, fireRate: 1.2, magazine: 4, flavor: 'Fires toilet plungers that stick to surfaces and explode' },
    { name: 'Sigma Grindstone Rifle', rarity: 'Epic', rarityColor: '#a855f7', damage: 42, fireRate: 5.5, magazine: 30, flavor: 'Never stops grinding. Neither does this gun.' },
    { name: 'Ohio Anomaly Cannon', rarity: 'Mythic', rarityColor: '#fbbf24', damage: 120, fireRate: 0.8, magazine: 1, flavor: 'Shoots a miniature Ohio portal that warps enemies' },
    { name: 'Grimace Shake Grenade', rarity: 'Epic', rarityColor: '#a855f7', damage: 60, fireRate: 1.0, magazine: 3, flavor: 'Purple explosion. Victims turn purple for 5 seconds.' },
    { name: 'Rizz Beam', rarity: 'Rare', rarityColor: '#3b82f6', damage: 25, fireRate: 10.0, magazine: 50, flavor: 'Charms enemies into standing still for 1.5 seconds' },
    { name: 'Fanum Tax Collector', rarity: 'Legendary', rarityColor: '#f97316', damage: 55, fireRate: 3.0, magazine: 12, flavor: 'Steals 10% of enemy materials on hit' },
    { name: 'Gyatt RPG', rarity: 'Mythic', rarityColor: '#fbbf24', damage: 110, fireRate: 0.6, magazine: 1, flavor: 'GYATT. Enough said.' },
    { name: 'Mewing Silencer', rarity: 'Rare', rarityColor: '#3b82f6', damage: 28, fireRate: 7.0, magazine: 25, flavor: 'So quiet your opponents won\'t even hear it coming' },
  ];

  // ── Leaderboard ──
  interface LeaderEntry {
    rank: number;
    name: string;
    tier: string;
    tierColor: string;
    kills: number;
    wins: number;
  }

  const leaderboard: LeaderEntry[] = [
    { rank: 1, name: 'xX_SkibidiKing_Xx', tier: 'Unreal', tierColor: '#9d4edd', kills: 2847, wins: 312 },
    { rank: 2, name: 'SigmaGrinder9000', tier: 'Unreal', tierColor: '#9d4edd', kills: 2503, wins: 289 },
    { rank: 3, name: 'OhioFinalForm', tier: 'Champion', tierColor: '#ff6b35', kills: 2201, wins: 256 },
    { rank: 4, name: 'GrimaceShaker', tier: 'Champion', tierColor: '#ff6b35', kills: 1988, wins: 231 },
    { rank: 5, name: 'RizzLordSupreme', tier: 'Diamond', tierColor: '#b9f2ff', kills: 1845, wins: 215 },
    { rank: 6, name: 'FanumTaxEvader', tier: 'Diamond', tierColor: '#b9f2ff', kills: 1702, wins: 198 },
    { rank: 7, name: 'GyattDestroyer', tier: 'Diamond', tierColor: '#b9f2ff', kills: 1589, wins: 184 },
    { rank: 8, name: 'MewingChampion', tier: 'Platinum', tierColor: '#00d4aa', kills: 1456, wins: 170 },
    { rank: 9, name: 'EdgeLord420', tier: 'Platinum', tierColor: '#00d4aa', kills: 1334, wins: 155 },
    { rank: 10, name: 'BrainrotVictim', tier: 'Gold', tierColor: '#ffd700', kills: 1201, wins: 140 },
  ];

  // ── Map helpers ──
  const MAP_SIZE = 2000;
  function mapX(worldX: number): number { return ((worldX + MAP_SIZE) / (MAP_SIZE * 2)) * 100; }
  function mapZ(worldZ: number): number { return (1 - (worldZ + MAP_SIZE) / (MAP_SIZE * 2)) * 100; }

  // ── Avatar SVG ──
  function avatarSvg(char: BrainrotChar): string {
    const h = char.skinHue;
    const skinL = char.id === 'char-grimace' ? '45%' : '70%';
    const skin = `hsl(${Math.round(h * 360)}, 50%, ${skinL})`;
    const headR = char.body === 'stocky' ? 18 : char.body === 'slim' ? 14 : 16;
    const bodyW = char.body === 'stocky' ? 28 : char.body === 'slim' ? 18 : char.body === 'athletic' ? 24 : 22;
    const bodyH = char.body === 'tall' ? 30 : 24;
    let hair = '';
    if (char.hair === 'buzz') hair = `<rect x="${50 - headR}" y="${22 - headR}" width="${headR * 2}" height="${headR * 0.5}" rx="4" fill="${char.color}" opacity="0.8"/>`;
    else if (char.hair === 'spiky') hair = `<polygon points="${50 - 8},${22 - headR} ${50},${22 - headR - 10} ${50 + 8},${22 - headR}" fill="${char.color}"/>`;
    else if (char.hair === 'mohawk') hair = `<rect x="47" y="${22 - headR - 8}" width="6" height="${headR}" rx="2" fill="${char.color}"/>`;
    else if (char.hair === 'wavy') hair = `<path d="M${50 - headR + 2},${22 - headR * 0.3} Q${50},${22 - headR - 6} ${50 + headR - 2},${22 - headR * 0.3}" fill="none" stroke="${char.color}" stroke-width="3"/>`;
    else if (char.hair === 'afro') hair = `<circle cx="50" cy="${22 - headR * 0.3}" r="${headR + 4}" fill="${char.color}" opacity="0.7"/>`;
    let acc = '';
    if (char.accessory === 'sunglasses') acc = `<rect x="38" y="18" width="24" height="6" rx="2" fill="#111" opacity="0.9"/>`;
    else if (char.accessory === 'mask') acc = `<rect x="36" y="20" width="28" height="10" rx="3" fill="#333" opacity="0.8"/>`;
    else if (char.accessory === 'earring') acc = `<circle cx="${50 + headR + 2}" cy="24" r="2" fill="#ffd700"/>`;
    else if (char.accessory === 'hat') acc = `<rect x="36" y="${22 - headR - 2}" width="28" height="6" rx="2" fill="${char.color}"/><rect x="32" y="${22 - headR + 3}" width="36" height="3" rx="1" fill="${char.color}"/>`;
    return `<svg viewBox="0 0 100 80" xmlns="http://www.w3.org/2000/svg">
      ${hair}
      <circle cx="50" cy="22" r="${headR}" fill="${skin}"/>
      ${acc}
      <rect x="${50 - bodyW / 2}" y="${22 + headR - 2}" width="${bodyW}" height="${bodyH}" rx="4" fill="${char.color}" opacity="0.9"/>
      <rect x="${50 - bodyW / 2 - 4}" y="${22 + headR + bodyH - 4}" width="10" height="14" rx="3" fill="${skin}"/>
      <rect x="${50 + bodyW / 2 - 6}" y="${22 + headR + bodyH - 4}" width="10" height="14" rx="3" fill="${skin}"/>
    </svg>`;
  }

  // ── Actions ──
  async function dropIn() {
    error = '';
    loading = true;
    try {
      const guestId = 'did:web:kami.etzhayyim.com:guest:' + Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
      const method = mode === 'ranked' ? 'queue-ranked' : 'queue-casual';
      const body = mode === 'ranked'
        ? { 'player_did': ctx.userId || guestId, 'display_name': ctx.actorId || 'Player', 'character_id': characters[selectedChar].id }
        : { 'guest_id': guestId, 'character_id': characters[selectedChar].id };
      const res = await ctx.backend.call(CMD, method, body) as Record<string, string>;
      matchId = res?.match_id || guestId;
      guestNickname = res?.nickname || characters[selectedChar].name;
    } catch {
      matchId = Date.now().toString(36);
      guestNickname = characters[selectedChar].name;
    }
    loading = false;
    startGame();
  }

  function startGame() {
    gameAlive = 100;
    gamePhase = 'bus';
    gameKills = 0;
    gamePlacement = 0;
    gameStormPhase = 0;
    gameTimer = 0;
    view = 'game';

    // Simulate battle bus → drop → game
    setTimeout(() => { gamePhase = 'dropping'; }, 2000);
    setTimeout(() => {
      gamePhase = 'playing';
      gameInterval = setInterval(gameTick, 800);
    }, 4000);
  }

  function gameTick() {
    gameTimer++;
    // Storm advances every ~15 ticks
    if (gameTimer % 15 === 0 && gameStormPhase < 8) gameStormPhase++;
    // Eliminate players
    const elimRate = Math.max(1, Math.floor(gameAlive * (0.03 + gameStormPhase * 0.01)));
    const elims = Math.min(elimRate, gameAlive - 1);
    if (elims > 0) {
      gameAlive -= elims;
      // Player gets a kill sometimes
      if (Math.random() < 0.15 + gameStormPhase * 0.02) gameKills++;
    }
    // Player elimination chance (increases with storm)
    const deathChance = 0.005 + gameStormPhase * 0.008;
    if (gameAlive > 1 && Math.random() < deathChance) {
      gamePlacement = gameAlive;
      gamePhase = 'eliminated';
      if (gameInterval) { clearInterval(gameInterval); gameInterval = null; }
      return;
    }
    // Victory
    if (gameAlive <= 1) {
      gamePlacement = 1;
      gamePhase = 'victory';
      gameKills++;
      if (gameInterval) { clearInterval(gameInterval); gameInterval = null; }
    }
  }

  function exitGame() {
    if (gameInterval) { clearInterval(gameInterval); gameInterval = null; }
    view = 'lobby';
  }
</script>

{#if view === 'game'}
  <div class="kr-game-view">
    <div class="kr-game-hud">
      <!-- Top HUD -->
      <div class="kr-hud-top">
        <div class="kr-hud-alive">
          <span class="kr-hud-alive-count">{gameAlive}</span>
          <span class="kr-hud-alive-label">ALIVE</span>
        </div>
        <div class="kr-hud-center">
          {#if gamePhase === 'bus'}
            <div class="kr-hud-phase">BATTLE BUS</div>
          {:else if gamePhase === 'dropping'}
            <div class="kr-hud-phase">DROPPING IN...</div>
          {:else if gamePhase === 'playing'}
            <div class="kr-hud-phase">STORM PHASE {gameStormPhase}</div>
          {:else if gamePhase === 'eliminated'}
            <div class="kr-hud-phase kr-hud-eliminated">ELIMINATED</div>
          {:else if gamePhase === 'victory'}
            <div class="kr-hud-phase kr-hud-victory">VICTORY ROYALE!</div>
          {/if}
        </div>
        <div class="kr-hud-kills">
          <span class="kr-hud-kills-count">{gameKills}</span>
          <span class="kr-hud-kills-label">KILLS</span>
        </div>
      </div>

      <!-- Map Canvas (simulated) -->
      <div class="kr-game-map">
        <div class="kr-game-map-inner">
          <div class="kr-map-grid"></div>
          <!-- Storm circle -->
          <div class="kr-storm-circle" style="--storm-size: {Math.max(10, 100 - gameStormPhase * 11)}%"></div>
          <!-- POIs -->
          {#each pois.filter(p => p.type === 'brainrot') as poi}
            <div class="kr-game-poi" style="left: {mapX(poi.x)}%; top: {mapZ(poi.z)}%; --poi-color: {poi.color}">
              <div class="kr-poi-dot"></div>
              <span class="kr-poi-label">{poi.name}</span>
            </div>
          {/each}
          <!-- Player marker -->
          {#if gamePhase !== 'bus'}
            <div class="kr-player-marker" style="left: {50 + Math.sin(gameTimer * 0.3) * 15}%; top: {50 + Math.cos(gameTimer * 0.2) * 15}%">
              <div class="kr-player-dot"></div>
            </div>
          {/if}
        </div>
      </div>

      <!-- Character + Info -->
      <div class="kr-game-char">
        <div class="kr-game-avatar">{@html avatarSvg(characters[selectedChar])}</div>
        <div class="kr-game-info">
          <div class="kr-game-name">{guestNickname}</div>
          <div class="kr-game-weapon">{weapons[Math.min(gameKills, weapons.length - 1)].name}</div>
        </div>
      </div>

      <!-- Result overlay -->
      {#if gamePhase === 'eliminated' || gamePhase === 'victory'}
        <div class="kr-result-overlay">
          <div class="kr-result-card" class:kr-result-win={gamePhase === 'victory'}>
            <div class="kr-result-title">{gamePhase === 'victory' ? 'VICTORY ROYALE!' : 'ELIMINATED'}</div>
            <div class="kr-result-placement">#{gamePlacement}</div>
            <div class="kr-result-stats">
              <div class="kr-result-stat"><span>{gameKills}</span><span>Kills</span></div>
              <div class="kr-result-stat"><span>{gameTimer}</span><span>Survived</span></div>
              <div class="kr-result-stat"><span>{mode}</span><span>Mode</span></div>
            </div>
            <button class="kr-drop-btn" onclick={exitGame} style="margin-top: 16px; font-size: 16px; padding: 14px;">
              BACK TO LOBBY
            </button>
          </div>
        </div>
      {/if}

      <!-- Exit button -->
      {#if gamePhase !== 'eliminated' && gamePhase !== 'victory'}
        <button class="kr-exit-btn" onclick={exitGame}>EXIT</button>
      {/if}
    </div>
  </div>
{:else}
<div class="kr-root">
  <!-- Header -->
  <header class="kr-header">
    <h1 class="kr-title">KAMI ROYALE</h1>
    <div class="kr-subtitle">BRAINROT EDITION</div>
    <div class="kr-season">Season 1 \u00B7 100 Players \u00B7 26 POIs</div>
  </header>

  {#if error}
    <div class="kr-error">{error}</div>
  {/if}

  <!-- Character Select -->
  <section class="kr-section">
    <h2 class="kr-section-title">SELECT YOUR CHARACTER</h2>
    <div class="kr-char-scroll">
      {#each characters as char, i}
        <button
          class="kr-char-card"
          class:kr-char-selected={selectedChar === i}
          style="--char-color: {char.color}"
          onclick={() => selectedChar = i}
        >
          <div class="kr-char-avatar">
            {@html avatarSvg(char)}
          </div>
          <div class="kr-char-name">{char.name}</div>
          <span class="kr-char-badge" class:kr-badge-boss={char.role === 'boss'}>{char.role.toUpperCase()}</span>
          <div class="kr-char-meta">
            <span>{char.bodyIcon} {char.body}</span>
            <span>\u00B7 {char.accessory}</span>
          </div>
          <div class="kr-char-tagline">{char.tagline}</div>
        </button>
      {/each}
    </div>
  </section>

  <!-- POI Map -->
  <section class="kr-section">
    <h2 class="kr-section-title">BRAINROT ISLAND \u2014 2km \u00D7 2km</h2>
    <div class="kr-map-container">
      <div class="kr-map">
        <div class="kr-map-grid"></div>
        {#each pois as poi}
          <div
            class="kr-poi"
            class:kr-poi-brainrot={poi.type === 'brainrot'}
            style="left: {mapX(poi.x)}%; top: {mapZ(poi.z)}%; --poi-color: {poi.color}"
            title="{poi.name} (Loot: {Math.round(poi.loot * 100)}%)"
          >
            <div class="kr-poi-dot"></div>
            {#if poi.type === 'brainrot'}
              <span class="kr-poi-label">{poi.name}</span>
            {/if}
          </div>
        {/each}
      </div>
      <div class="kr-map-legend">
        {#each pois.filter(p => p.type === 'brainrot') as bp}
          <span class="kr-legend-item">
            <span class="kr-legend-dot" style="background: {bp.color}"></span>
            {bp.name}
          </span>
        {/each}
      </div>
    </div>
  </section>

  <!-- Queue Panel -->
  <section class="kr-section">
    <div class="kr-queue-panel">
      <div class="kr-mode-toggle">
        <button class="kr-mode-btn" class:kr-mode-active={mode === 'casual'} onclick={() => mode = 'casual'}>CASUAL</button>
        <button class="kr-mode-btn" class:kr-mode-active={mode === 'ranked'} onclick={() => mode = 'ranked'}>RANKED</button>
      </div>
      <button class="kr-drop-btn" onclick={dropIn} disabled={loading}>
        {loading ? 'FINDING MATCH...' : 'DROP IN'}
      </button>
      <div class="kr-queue-info">
        <span class="kr-queue-stat">Season 1</span>
        <span class="kr-queue-divider">\u00B7</span>
        <span class="kr-queue-stat">{playerCount} in queue</span>
        <span class="kr-queue-divider">\u00B7</span>
        <span class="kr-queue-stat">{characters[selectedChar].name}</span>
      </div>
    </div>
  </section>

  <!-- Leaderboard -->
  <section class="kr-section">
    <button class="kr-collapse-btn" onclick={() => leaderboardOpen = !leaderboardOpen}>
      <h2 class="kr-section-title" style="margin:0">TOP 10 RANKED</h2>
      <span class="kr-collapse-icon">{leaderboardOpen ? '\u25B2' : '\u25BC'}</span>
    </button>
    {#if leaderboardOpen}
      <div class="kr-leaderboard">
        <div class="kr-lb-header">
          <span class="kr-lb-rank">#</span>
          <span class="kr-lb-name">Player</span>
          <span class="kr-lb-tier">Tier</span>
          <span class="kr-lb-stat">Kills</span>
          <span class="kr-lb-stat">Wins</span>
        </div>
        {#each leaderboard as entry}
          <div class="kr-lb-row" class:kr-lb-top3={entry.rank <= 3}>
            <span class="kr-lb-rank" style="color: {entry.rank <= 3 ? '#ffd700' : 'var(--kr-text-muted)'}">{entry.rank}</span>
            <span class="kr-lb-name">{entry.name}</span>
            <span class="kr-lb-tier" style="color: {entry.tierColor}">{entry.tier}</span>
            <span class="kr-lb-stat">{entry.kills.toLocaleString()}</span>
            <span class="kr-lb-stat">{entry.wins}</span>
          </div>
        {/each}
      </div>
    {/if}
  </section>

  <!-- Weapons Showcase -->
  <section class="kr-section">
    <h2 class="kr-section-title">BRAINROT ARSENAL</h2>
    <div class="kr-weapon-scroll">
      {#each weapons as w}
        <div class="kr-weapon-card" style="--rarity-color: {w.rarityColor}">
          <div class="kr-weapon-rarity">{w.rarity}</div>
          <div class="kr-weapon-name">{w.name}</div>
          <div class="kr-weapon-stats">
            <div class="kr-weapon-stat">
              <span class="kr-ws-label">DMG</span>
              <span class="kr-ws-value">{w.damage}</span>
            </div>
            <div class="kr-weapon-stat">
              <span class="kr-ws-label">RATE</span>
              <span class="kr-ws-value">{w.fireRate}/s</span>
            </div>
            <div class="kr-weapon-stat">
              <span class="kr-ws-label">MAG</span>
              <span class="kr-ws-value">{w.magazine}</span>
            </div>
          </div>
          <div class="kr-weapon-flavor">{w.flavor}</div>
        </div>
      {/each}
    </div>
  </section>
</div>
{/if}

<style>
  /* ── Game View ── */
  .kr-game-view {
    position: fixed;
    inset: 0;
    z-index: 100;
    background: #0a0612;
  }
  .kr-game-hud {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    max-width: 600px;
    margin: 0 auto;
  }
  .kr-exit-btn {
    position: absolute;
    top: 12px;
    left: 12px;
    z-index: 101;
    padding: 8px 16px;
    border: 1px solid rgba(147, 51, 234, 0.5);
    border-radius: 8px;
    background: rgba(15, 10, 26, 0.85);
    backdrop-filter: blur(8px);
    -webkit-backdrop-filter: blur(8px);
    color: #a78bfa;
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 1px;
    cursor: pointer;
    font-family: system-ui, -apple-system, sans-serif;
    transition: background 0.2s, color 0.2s;
  }
  .kr-exit-btn:hover {
    background: rgba(147, 51, 234, 0.3);
    color: #f0e6ff;
  }
  .kr-hud-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 16px;
    z-index: 10;
  }
  .kr-hud-alive, .kr-hud-kills {
    display: flex;
    flex-direction: column;
    align-items: center;
    min-width: 60px;
  }
  .kr-hud-alive-count, .kr-hud-kills-count {
    font-size: 32px;
    font-weight: 900;
    color: #fff;
    line-height: 1;
  }
  .kr-hud-alive-label, .kr-hud-kills-label {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #8b7aa0;
  }
  .kr-hud-center {
    text-align: center;
  }
  .kr-hud-phase {
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 2px;
    color: #a78bfa;
    text-transform: uppercase;
  }
  .kr-hud-eliminated { color: #ef4444; font-size: 18px; }
  .kr-hud-victory {
    color: #fbbf24;
    font-size: 18px;
    text-shadow: 0 0 20px rgba(251, 191, 36, 0.5);
  }
  .kr-game-map {
    flex: 1;
    padding: 0 16px;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .kr-game-map-inner {
    position: relative;
    width: 100%;
    aspect-ratio: 1;
    max-height: 60vh;
    background: linear-gradient(135deg, #0d0818 0%, #150f24 50%, #0d0818 100%);
    border-radius: 12px;
    overflow: hidden;
    border: 1px solid #2d1f3d;
  }
  .kr-storm-circle {
    position: absolute;
    top: 50%;
    left: 50%;
    width: var(--storm-size);
    height: var(--storm-size);
    transform: translate(-50%, -50%);
    border: 2px solid rgba(147, 51, 234, 0.6);
    border-radius: 50%;
    box-shadow: 0 0 40px rgba(147, 51, 234, 0.15) inset;
    transition: width 1s, height 1s;
  }
  .kr-game-poi {
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 1;
  }
  .kr-player-marker {
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 5;
    transition: left 0.8s, top 0.8s;
  }
  .kr-player-dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #06c755;
    box-shadow: 0 0 10px #06c755, 0 0 20px rgba(6, 199, 85, 0.4);
    animation: pulse-player 1.5s infinite;
  }
  @keyframes pulse-player {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.3); }
  }
  .kr-game-char {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 16px;
  }
  .kr-game-avatar {
    width: 48px;
    height: 38px;
  }
  .kr-game-avatar :global(svg) {
    width: 100%;
    height: 100%;
  }
  .kr-game-info {
    flex: 1;
  }
  .kr-game-name {
    font-size: 14px;
    font-weight: 700;
    color: #f0e6ff;
  }
  .kr-game-weapon {
    font-size: 11px;
    color: #8b7aa0;
  }
  .kr-result-overlay {
    position: absolute;
    inset: 0;
    background: rgba(10, 5, 18, 0.85);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 50;
  }
  .kr-result-card {
    text-align: center;
    padding: 32px 40px;
    background: #1a1025;
    border: 2px solid #ef4444;
    border-radius: 20px;
    max-width: 320px;
    width: 100%;
  }
  .kr-result-win {
    border-color: #fbbf24;
    box-shadow: 0 0 40px rgba(251, 191, 36, 0.2);
  }
  .kr-result-title {
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 2px;
    color: #ef4444;
    margin-bottom: 8px;
  }
  .kr-result-win .kr-result-title {
    color: #fbbf24;
  }
  .kr-result-placement {
    font-size: 48px;
    font-weight: 900;
    color: #fff;
    line-height: 1;
    margin-bottom: 16px;
  }
  .kr-result-stats {
    display: flex;
    justify-content: center;
    gap: 24px;
  }
  .kr-result-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
  }
  .kr-result-stat span:first-child {
    font-size: 20px;
    font-weight: 800;
    color: #f0e6ff;
  }
  .kr-result-stat span:last-child {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: #8b7aa0;
    text-transform: uppercase;
  }

  /* ── CSS Custom Properties ── */
  .kr-root {
    --kr-primary: #9333ea;
    --kr-secondary: #ec4899;
    --kr-accent: #f59e0b;
    --kr-bg: #0f0a1a;
    --kr-card: #1a1025;
    --kr-card-border: #2d1f3d;
    --kr-text: #f0e6ff;
    --kr-text-muted: #8b7aa0;
    --kr-text-dim: #5a4d6e;

    max-width: 600px;
    margin: 0 auto;
    padding: 16px;
    font-family: system-ui, -apple-system, sans-serif;
    color: var(--kr-text);
    background: var(--kr-bg);
    min-height: 100vh;
  }

  /* ── Header ── */
  .kr-header {
    text-align: center;
    padding: 32px 0 20px;
  }
  .kr-title {
    font-size: 40px;
    font-weight: 900;
    letter-spacing: -2px;
    margin: 0;
    background: linear-gradient(135deg, var(--kr-primary), var(--kr-secondary));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .kr-subtitle {
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 4px;
    color: var(--kr-accent);
    margin-top: 4px;
  }
  .kr-season {
    font-size: 12px;
    color: var(--kr-text-muted);
    margin-top: 6px;
  }

  /* ── Sections ── */
  .kr-section {
    margin-bottom: 24px;
  }
  .kr-section-title {
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1.5px;
    color: var(--kr-text-muted);
    margin: 0 0 12px 0;
  }

  /* ── Error ── */
  .kr-error {
    background: #2d0a0a;
    border: 1px solid #7f1d1d;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 16px;
    font-size: 13px;
    color: #fca5a5;
  }

  /* ── Character Select ── */
  .kr-char-scroll {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 8px;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
  }
  .kr-char-scroll::-webkit-scrollbar { height: 4px; }
  .kr-char-scroll::-webkit-scrollbar-track { background: transparent; }
  .kr-char-scroll::-webkit-scrollbar-thumb { background: var(--kr-card-border); border-radius: 2px; }

  .kr-char-card {
    flex: 0 0 140px;
    scroll-snap-align: start;
    background: var(--kr-card);
    border: 2px solid var(--kr-card-border);
    border-radius: 12px;
    padding: 12px 10px;
    text-align: center;
    cursor: pointer;
    transition: border-color 0.2s, box-shadow 0.2s;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    color: var(--kr-text);
    font-family: inherit;
  }
  .kr-char-card:hover {
    border-color: var(--char-color);
  }
  .kr-char-selected {
    border-color: var(--char-color);
    box-shadow: 0 0 16px color-mix(in srgb, var(--char-color) 50%, transparent), 0 0 4px var(--char-color);
  }
  .kr-char-avatar {
    width: 72px;
    height: 58px;
  }
  .kr-char-avatar :global(svg) {
    width: 100%;
    height: 100%;
  }
  .kr-char-name {
    font-size: 12px;
    font-weight: 700;
    line-height: 1.2;
  }
  .kr-char-badge {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 2px 6px;
    border-radius: 4px;
    background: var(--kr-primary);
    color: white;
  }
  .kr-badge-boss {
    background: var(--kr-accent);
    color: #0f0a1a;
  }
  .kr-char-meta {
    font-size: 10px;
    color: var(--kr-text-muted);
  }
  .kr-char-tagline {
    font-size: 10px;
    color: var(--kr-text-dim);
    font-style: italic;
    margin-top: 2px;
  }

  /* ── POI Map ── */
  .kr-map-container {
    background: var(--kr-card);
    border: 1px solid var(--kr-card-border);
    border-radius: 12px;
    padding: 12px;
  }
  .kr-map {
    position: relative;
    width: 100%;
    aspect-ratio: 1;
    background: linear-gradient(135deg, #0d0818 0%, #150f24 50%, #0d0818 100%);
    border-radius: 8px;
    overflow: hidden;
  }
  .kr-map-grid {
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(147, 51, 234, 0.08) 1px, transparent 1px),
      linear-gradient(90deg, rgba(147, 51, 234, 0.08) 1px, transparent 1px);
    background-size: 10% 10%;
  }
  .kr-poi {
    position: absolute;
    transform: translate(-50%, -50%);
    z-index: 1;
  }
  .kr-poi-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--poi-color);
    opacity: 0.5;
  }
  .kr-poi-brainrot .kr-poi-dot {
    width: 10px;
    height: 10px;
    opacity: 1;
    box-shadow: 0 0 8px var(--poi-color);
  }
  .kr-poi-label {
    position: absolute;
    top: 14px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 8px;
    font-weight: 700;
    color: var(--poi-color);
    white-space: nowrap;
    text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
  }
  .kr-map-legend {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
    justify-content: center;
  }
  .kr-legend-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 10px;
    color: var(--kr-text-muted);
  }
  .kr-legend-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  /* ── Queue Panel ── */
  .kr-queue-panel {
    display: flex;
    flex-direction: column;
    gap: 12px;
    align-items: center;
  }
  .kr-mode-toggle {
    display: flex;
    gap: 0;
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid var(--kr-card-border);
  }
  .kr-mode-btn {
    padding: 10px 28px;
    border: none;
    background: var(--kr-card);
    color: var(--kr-text-muted);
    font-size: 13px;
    font-weight: 700;
    letter-spacing: 1px;
    cursor: pointer;
    transition: background 0.2s, color 0.2s;
    font-family: inherit;
  }
  .kr-mode-active {
    background: linear-gradient(135deg, var(--kr-primary), var(--kr-secondary));
    color: white;
  }
  .kr-drop-btn {
    width: 100%;
    padding: 20px;
    border: none;
    border-radius: 14px;
    background: linear-gradient(135deg, var(--kr-primary), var(--kr-secondary));
    color: white;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 2px;
    cursor: pointer;
    transition: opacity 0.2s, transform 0.1s;
    font-family: inherit;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
  }
  .kr-drop-btn:hover:not(:disabled) {
    opacity: 0.9;
  }
  .kr-drop-btn:active:not(:disabled) {
    transform: scale(0.98);
  }
  .kr-drop-btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .kr-queue-info {
    display: flex;
    gap: 6px;
    align-items: center;
    font-size: 12px;
    color: var(--kr-text-muted);
  }
  .kr-queue-stat {
    color: var(--kr-text-dim);
  }
  .kr-queue-divider {
    color: var(--kr-text-dim);
    opacity: 0.5;
  }

  /* ── Leaderboard ── */
  .kr-collapse-btn {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    background: none;
    border: none;
    cursor: pointer;
    padding: 0 0 12px 0;
    font-family: inherit;
  }
  .kr-collapse-icon {
    font-size: 12px;
    color: var(--kr-text-muted);
  }
  .kr-leaderboard {
    background: var(--kr-card);
    border: 1px solid var(--kr-card-border);
    border-radius: 10px;
    overflow: hidden;
  }
  .kr-lb-header {
    display: grid;
    grid-template-columns: 32px 1fr 80px 56px 56px;
    padding: 8px 12px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: var(--kr-text-dim);
    border-bottom: 1px solid var(--kr-card-border);
  }
  .kr-lb-row {
    display: grid;
    grid-template-columns: 32px 1fr 80px 56px 56px;
    padding: 8px 12px;
    font-size: 12px;
    border-bottom: 1px solid rgba(45, 31, 61, 0.5);
    align-items: center;
  }
  .kr-lb-row:last-child {
    border-bottom: none;
  }
  .kr-lb-top3 {
    background: rgba(255, 215, 0, 0.03);
  }
  .kr-lb-rank {
    font-weight: 700;
    text-align: center;
  }
  .kr-lb-name {
    font-weight: 600;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  .kr-lb-tier {
    font-weight: 700;
    font-size: 11px;
  }
  .kr-lb-stat {
    text-align: right;
    color: var(--kr-text-muted);
    font-size: 11px;
  }

  /* ── Weapons ── */
  .kr-weapon-scroll {
    display: flex;
    gap: 10px;
    overflow-x: auto;
    padding-bottom: 8px;
    scroll-snap-type: x mandatory;
    -webkit-overflow-scrolling: touch;
  }
  .kr-weapon-scroll::-webkit-scrollbar { height: 4px; }
  .kr-weapon-scroll::-webkit-scrollbar-track { background: transparent; }
  .kr-weapon-scroll::-webkit-scrollbar-thumb { background: var(--kr-card-border); border-radius: 2px; }

  .kr-weapon-card {
    flex: 0 0 200px;
    scroll-snap-align: start;
    background: var(--kr-card);
    border: 2px solid var(--rarity-color);
    border-radius: 12px;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .kr-weapon-rarity {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
    color: var(--rarity-color);
  }
  .kr-weapon-name {
    font-size: 14px;
    font-weight: 700;
    line-height: 1.2;
  }
  .kr-weapon-stats {
    display: flex;
    gap: 12px;
    margin-top: 4px;
  }
  .kr-weapon-stat {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .kr-ws-label {
    font-size: 9px;
    font-weight: 700;
    letter-spacing: 1px;
    color: var(--kr-text-dim);
  }
  .kr-ws-value {
    font-size: 16px;
    font-weight: 800;
    color: var(--kr-text);
  }
  .kr-weapon-flavor {
    font-size: 11px;
    color: var(--kr-text-dim);
    font-style: italic;
    line-height: 1.3;
    margin-top: 2px;
  }
</style>
