import {
  App,
  asAgentTool,
  createWorkerExport,
  createKyselyDb,
  nowISO,
  str,
  llmAsk,
  withCapabilityTags,
  withOCELEvent,
  type ComAtprotoSyncSubscribeReposCommit,
  type HostSDK, resolveHeartbeatCadence, createCadenceState, createInboxBuffer, genID, decodeJson,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();

let appId = ""
let actorDID = ""
const COLLECTION = "com.etzhayyim.apps.kami.sabiotoshi";

// --- Write Helpers ---

// --- Helpers ---

// --- Item Catalog ---

interface RustyItem {
  id: string;
  name: string;
  'nameJa': string;
  difficulty: number;
  zones: RustZone[];
  'baseScore': number;
  'perfectBonus': number;
  'cpcCode': string;
  'unspscCode': string;
  'cpcDesc': string;
  'unspscDesc': string;
}

interface RustZone {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
  'rustLevel': number;
  'rustType': "surface" | "deep" | "pitted";
}

const ITEM_CATALOG: RustyItem[] = [
  {
    id: "wrench",
    name: "Vintage Wrench",
    'nameJa': "ヴィンテージレンチ",
    difficulty: 1,
    'baseScore': 100,
    'perfectBonus': 50,
    'cpcCode': "42322", 'cpcDesc': "Hand tools for metalworking",
    'unspscCode': "27111700", 'unspscDesc': "Hand tools",
    zones: [
      { id: "head", x: 0.1, y: 0.2, width: 0.3, height: 0.2, 'rustLevel': 80, 'rustType': "surface" },
      { id: "jaw", x: 0.05, y: 0.4, width: 0.25, height: 0.15, 'rustLevel': 60, 'rustType': "surface" },
      { id: "shaft", x: 0.3, y: 0.35, width: 0.5, height: 0.1, 'rustLevel': 40, 'rustType': "surface" },
      { id: "handle", x: 0.7, y: 0.3, width: 0.25, height: 0.2, 'rustLevel': 30, 'rustType': "surface" },
    ],
  },
  {
    id: "skeletonKey",
    name: "Skeleton Key",
    'nameJa': "アンティーク鍵",
    difficulty: 2,
    'baseScore': 200,
    'perfectBonus': 100,
    'cpcCode': "42995", 'cpcDesc': "Locks, keys and hinges",
    'unspscCode': "46171500", 'unspscDesc': "Locks and hardware",
    zones: [
      { id: "bow", x: 0.05, y: 0.15, width: 0.25, height: 0.3, 'rustLevel': 90, 'rustType': "deep" },
      { id: "collar", x: 0.25, y: 0.25, width: 0.1, height: 0.1, 'rustLevel': 70, 'rustType': "surface" },
      { id: "shaft", x: 0.3, y: 0.27, width: 0.4, height: 0.06, 'rustLevel': 50, 'rustType': "surface" },
      { id: "bit", x: 0.65, y: 0.2, width: 0.3, height: 0.2, 'rustLevel': 85, 'rustType': "pitted" },
    ],
  },
  {
    id: "gear",
    name: "Clock Gear",
    'nameJa': "時計の歯車",
    difficulty: 2,
    'cpcCode': "43142", 'cpcDesc': "Gears and gearing",
    'unspscCode': "40161512", 'unspscDesc': "Gears",
    'baseScore': 250,
    'perfectBonus': 125,
    zones: [
      { id: "teethTop", x: 0.1, y: 0.0, width: 0.8, height: 0.15, 'rustLevel': 75, 'rustType': "surface" },
      { id: "teethBottom", x: 0.1, y: 0.85, width: 0.8, height: 0.15, 'rustLevel': 75, 'rustType': "surface" },
      { id: "faceLeft", x: 0.0, y: 0.15, width: 0.5, height: 0.7, 'rustLevel': 60, 'rustType': "deep" },
      { id: "faceRight", x: 0.5, y: 0.15, width: 0.5, height: 0.7, 'rustLevel': 60, 'rustType': "deep" },
      { id: "hub", x: 0.35, y: 0.35, width: 0.3, height: 0.3, 'rustLevel': 95, 'rustType': "pitted" },
    ],
  },
  {
    id: "compass",
    name: "Brass Compass",
    'nameJa': "真鍮コンパス",
    difficulty: 3,
    'baseScore': 350,
    'perfectBonus': 175,
    'cpcCode': "45122", 'cpcDesc': "Navigation instruments",
    'unspscCode': "41111900", 'unspscDesc': "Navigational instruments",
    zones: [
      { id: "lidOuter", x: 0.05, y: 0.05, width: 0.9, height: 0.2, 'rustLevel': 70, 'rustType': "surface" },
      { id: "lidInner", x: 0.15, y: 0.2, width: 0.7, height: 0.15, 'rustLevel': 50, 'rustType': "surface" },
      { id: "bezel", x: 0.1, y: 0.35, width: 0.8, height: 0.1, 'rustLevel': 85, 'rustType': "deep" },
      { id: "dial", x: 0.2, y: 0.45, width: 0.6, height: 0.3, 'rustLevel': 40, 'rustType': "surface" },
      { id: "hinge", x: 0.45, y: 0.75, width: 0.1, height: 0.2, 'rustLevel': 95, 'rustType': "pitted" },
      { id: "clasp", x: 0.45, y: 0.0, width: 0.1, height: 0.1, 'rustLevel': 90, 'rustType': "pitted" },
    ],
  },
  {
    id: "padlock",
    name: "Iron Padlock",
    'nameJa': "南京錠",
    difficulty: 3,
    'baseScore': 300,
    'perfectBonus': 150,
    'cpcCode': "42995", 'cpcDesc': "Locks, keys and hinges",
    'unspscCode': "46171500", 'unspscDesc': "Locks and hardware",
    zones: [
      { id: "shackle", x: 0.25, y: 0.0, width: 0.5, height: 0.3, 'rustLevel': 90, 'rustType': "deep" },
      { id: "bodyFront", x: 0.15, y: 0.3, width: 0.7, height: 0.5, 'rustLevel': 80, 'rustType': "deep" },
      { id: "keyhole", x: 0.4, y: 0.5, width: 0.2, height: 0.15, 'rustLevel': 95, 'rustType': "pitted" },
      { id: "bodyBack", x: 0.2, y: 0.75, width: 0.6, height: 0.25, 'rustLevel': 70, 'rustType': "surface" },
    ],
  },
  {
    id: "scissors",
    name: "Tailor Scissors",
    'nameJa': "裁ちバサミ",
    difficulty: 4,
    'baseScore': 400,
    'perfectBonus': 200,
    'cpcCode': "42223", 'cpcDesc': "Scissors and shears",
    'unspscCode': "27111801", 'unspscDesc': "Scissors",
    zones: [
      { id: "bladeLeft", x: 0.0, y: 0.1, width: 0.5, height: 0.12, 'rustLevel': 85, 'rustType': "deep" },
      { id: "bladeRight", x: 0.0, y: 0.25, width: 0.5, height: 0.12, 'rustLevel': 85, 'rustType': "deep" },
      { id: "pivot", x: 0.45, y: 0.15, width: 0.12, height: 0.12, 'rustLevel': 95, 'rustType': "pitted" },
      { id: "handleTop", x: 0.55, y: 0.05, width: 0.4, height: 0.15, 'rustLevel': 60, 'rustType': "surface" },
      { id: "handleBottom", x: 0.55, y: 0.3, width: 0.4, height: 0.15, 'rustLevel': 60, 'rustType': "surface" },
      { id: "edge", x: 0.0, y: 0.17, width: 0.45, height: 0.04, 'rustLevel': 70, 'rustType': "surface" },
    ],
  },
  {
    id: "pocketWatch",
    name: "Pocket Watch",
    'nameJa': "懐中時計",
    difficulty: 5,
    'baseScore': 500,
    'perfectBonus': 250,
    'cpcCode': "45121", 'cpcDesc': "Watches and clocks",
    'unspscCode': "54111600", 'unspscDesc': "Watches",
    zones: [
      { id: "caseTop", x: 0.1, y: 0.05, width: 0.8, height: 0.25, 'rustLevel': 75, 'rustType': "deep" },
      { id: "caseBottom", x: 0.1, y: 0.7, width: 0.8, height: 0.25, 'rustLevel': 75, 'rustType': "deep" },
      { id: "caseLeft", x: 0.05, y: 0.2, width: 0.15, height: 0.6, 'rustLevel': 80, 'rustType': "deep" },
      { id: "caseRight", x: 0.8, y: 0.2, width: 0.15, height: 0.6, 'rustLevel': 80, 'rustType': "deep" },
      { id: "face", x: 0.2, y: 0.25, width: 0.6, height: 0.5, 'rustLevel': 45, 'rustType': "surface" },
      { id: "crown", x: 0.45, y: 0.0, width: 0.1, height: 0.08, 'rustLevel': 90, 'rustType': "pitted" },
      { id: "chainLoop", x: 0.42, y: 0.92, width: 0.16, height: 0.08, 'rustLevel': 95, 'rustType': "pitted" },
    ],
  },
  {
    id: "katanaTsuba",
    name: "Katana Tsuba",
    'nameJa': "刀の鍔",
    difficulty: 5,
    'baseScore': 600,
    'perfectBonus': 300,
    'cpcCode': "42925", 'cpcDesc': "Swords, cutlery and flatware",
    'unspscCode': "46181500", 'unspscDesc': "Knives and cutting instruments",
    zones: [
      { id: "rimTop", x: 0.1, y: 0.05, width: 0.8, height: 0.1, 'rustLevel': 80, 'rustType': "deep" },
      { id: "rimBottom", x: 0.1, y: 0.85, width: 0.8, height: 0.1, 'rustLevel': 80, 'rustType': "deep" },
      { id: "rimLeft", x: 0.05, y: 0.1, width: 0.1, height: 0.8, 'rustLevel': 80, 'rustType': "deep" },
      { id: "rimRight", x: 0.85, y: 0.1, width: 0.1, height: 0.8, 'rustLevel': 80, 'rustType': "deep" },
      { id: "faceA", x: 0.15, y: 0.15, width: 0.35, height: 0.7, 'rustLevel': 65, 'rustType': "surface" },
      { id: "faceB", x: 0.5, y: 0.15, width: 0.35, height: 0.7, 'rustLevel': 65, 'rustType': "surface" },
      { id: "nakagoAna", x: 0.4, y: 0.4, width: 0.2, height: 0.2, 'rustLevel': 95, 'rustType': "pitted" },
      { id: "engraving", x: 0.25, y: 0.3, width: 0.15, height: 0.4, 'rustLevel': 50, 'rustType': "surface" },
    ],
  },
];

// --- Nozzle Types ---

interface Nozzle {
  id: string;
  name: string;
  spread: number;
  power: number;
  precision: number;
}

const NOZZLES: Nozzle[] = [
  { id: "wide", name: "Wide Fan", spread: 3.0, power: 1.0, precision: 0.5 },
  { id: "standard", name: "Standard", spread: 1.5, power: 2.0, precision: 1.0 },
  { id: "turbo", name: "Turbo Jet", spread: 0.8, power: 3.5, precision: 1.5 },
  { id: "needle", name: "Needle Point", spread: 0.3, power: 5.0, precision: 3.0 },
];

// --- Game State ---

interface GameState {
  'itemIndex': number;
  'zonesRemaining': Record<string, number>;
  score: number;
  combo: number;
  'maxCombo': number;
  nozzle: string;
  'timeRemaining': number;
  'itemsCompleted': number;
  'totalItems': number;
  phase: "playing" | "complete" | "timeout";
}

function newGameState(itemCount: number): GameState {
  const items = ITEM_CATALOG.slice(0, Math.min(itemCount, ITEM_CATALOG.length));
  const first = items[0];
  const zones: Record<string, number> = {};
  for (const z of first.zones) {
    zones[z.id] = z.rustLevel;
  }
  return {
    'itemIndex': 0,
    'zonesRemaining': zones,
    score: 0,
    combo: 0,
    'maxCombo': 0,
    nozzle: "standard",
    'timeRemaining': 120,
    'itemsCompleted': 0,
    'totalItems': items.length,
    phase: "playing",
  };
}

function computeSprayDamage(nozzle: Nozzle, zone: RustZone): number {
  const typeMult = zone.rustType === "surface" ? 1.0 : zone.rustType === "deep" ? 0.6 : 0.35;
  return Math.floor(nozzle.power * typeMult * 10);
}

// --- Commands ---

async function cmdNewGame(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.newGame", body);
  const count = Math.min(Math.max(Number(args.itemCount) || 3, 1), ITEM_CATALOG.length);
  const state = newGameState(count);
  const item = ITEM_CATALOG[0];
  const gameRkey = genID("game");
  await createKyselyDb().insertInto("vertex_kami_sabiotoshi_game" as any).values({
    vertex_id: `at://${actorDID || "did:web:s4b10t05.etzhayyim.com"}/com.etzhayyim.apps.kami.sabiotoshi.game/${gameRkey}`,
    sensitivity_ord: 2,
    owner_did: actorDID || "did:web:s4b10t05.etzhayyim.com",
    actor_id: appId || "s4b10t05",
    item_count: count,
    status: "started",
    created_at: nowISO(),
    org_id: "anon",
    user_id: "anon",
  }).execute();
  return {
    state,
    item: { id: item.id, name: item.name, 'nameJa': item.nameJa, difficulty: item.difficulty, zones: item.zones },
    nozzles: NOZZLES,
  };
}

async function cmdSpray(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.spray", body);
  const zoneId = str(args.zoneId ?? "");
  const nozzleId = str(args.nozzle ?? "standard");
  const stateIn: GameState = args.state;

  if (!stateIn || stateIn.phase !== "playing") return { error: "game not active" };

  const item = ITEM_CATALOG[stateIn.itemIndex];
  if (!item) return { error: "invalid item index" };

  const zone = item.zones.find(z => z.id === zoneId);
  if (!zone) return { error: "unknown zone" };

  const nozzle = NOZZLES.find(n => n.id === nozzleId) ?? NOZZLES[1];
  const damage = computeSprayDamage(nozzle, zone);
  const current = stateIn.zonesRemaining[zoneId] ?? 0;
  const newLevel = Math.max(0, current - damage);

  stateIn.zonesRemaining[zoneId] = newLevel;
  stateIn.nozzle = nozzleId;

  let zoneCleared = false;
  if (newLevel === 0 && current > 0) {
    zoneCleared = true;
    stateIn.combo++;
    if (stateIn.combo > stateIn.maxCombo) stateIn.maxCombo = stateIn.combo;
    const comboBonus = Math.min(stateIn.combo, 10) * 5;
    stateIn.score += 10 + comboBonus;
  }

  const allClean = Object.values(stateIn.zonesRemaining).every(v => v === 0);
  let itemCompleted = false;
  let nextItem: RustyItem | null = null;

  if (allClean) {
    itemCompleted = true;
    stateIn.itemsCompleted++;
    const perfectClean = stateIn.combo >= item.zones.length;
    stateIn.score += item.baseScore + (perfectClean ? item.perfectBonus: 0);

    if (stateIn.itemsCompleted < stateIn.totalItems) {
      stateIn.itemIndex++;
      nextItem = ITEM_CATALOG[stateIn.itemIndex];
      const zones: Record<string, number> = {};
      for (const z of nextItem.zones) {
        zones[z.id] = z.rustLevel;
      }
      stateIn.zonesRemaining = zones;
      stateIn.combo = 0;
    } else {
      stateIn.phase = "complete";
      const sprayScoreRkey = genID("score");
      await createKyselyDb().insertInto("vertex_kami_sabiotoshi_score" as any).values({
        vertex_id: `at://${actorDID || "did:web:s4b10t05.etzhayyim.com"}/com.etzhayyim.apps.kami.sabiotoshi.score/${sprayScoreRkey}`,
        sensitivity_ord: 2,
        owner_did: actorDID || "did:web:s4b10t05.etzhayyim.com",
        actor_id: appId || "s4b10t05",
        score: stateIn.score,
        items_completed: stateIn.itemsCompleted,
        max_combo: stateIn.maxCombo,
        created_at: nowISO(),
        org_id: "anon",
        user_id: "anon",
      }).execute();
    }
  }

  return {
    state: stateIn,
    'sprayResult': {
      'zoneId': zoneId,
      damage,
      remaining: newLevel,
      'zoneCleared': zoneCleared,
      'itemCompleted': itemCompleted,
      combo: stateIn.combo,
    },
    'nextItem': nextItem ? { id: nextItem.id, name: nextItem.name, 'nameJa': nextItem.nameJa, difficulty: nextItem.difficulty, zones: nextItem.zones } : null,
  };
}

function cmdSelectItem(sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.selectItem", body);
  const itemId = str(args.itemId ?? "");
  const item = ITEM_CATALOG.find(i => i.id === itemId);
  if (!item) return { error: "unknown item", available: ITEM_CATALOG.map(i => i.id) };
  return { item: { id: item.id, name: item.name, 'nameJa': item.nameJa, difficulty: item.difficulty, zones: item.zones, 'baseScore': item.baseScore } };
}

function cmdGetState(_sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.getState", body);
  return {
    catalog: ITEM_CATALOG.map(i => ({ id: i.id, name: i.name, 'nameJa': i.nameJa, difficulty: i.difficulty, 'baseScore': i.baseScore })),
    nozzles: NOZZLES,
  };
}

async function cmdGetLeaderboard(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.getLeaderboard", body);
  const limit = Math.min(Number(args.limit) || 20, 100);
  const rows = ([] as Record<string, unknown>[]);
  return { leaderboard: rows };
}

async function cmdSubmitScore(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.submitScore", body);
  const score = Number(args.score) || 0;
  const items = Number(args.itemsCompleted) || 0;
  const combo = Number(args.maxCombo) || 0;
  const id = genID("score");
  await createKyselyDb().insertInto("vertex_kami_sabiotoshi_score" as any).values({
    vertex_id: `at://${actorDID || "did:web:s4b10t05.etzhayyim.com"}/com.etzhayyim.apps.kami.sabiotoshi.score/${id}`,
    sensitivity_ord: 2,
    owner_did: actorDID || "did:web:s4b10t05.etzhayyim.com",
    actor_id: appId || "s4b10t05",
    score,
    items_completed: items,
    max_combo: combo,
    created_at: nowISO(),
    org_id: "anon",
    user_id: "anon",
  }).execute();
  return { id, status: "submitted" };
}

function cmdWave(sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.wave", body);
  const msg = str(args.message ?? "Hello");
  return { ok: true, agent: "Sabi-Otoshi!!", nanoid: appId };
}

// --- Reactive Pipeline (Layer 1: ComAtprotoSyncSubscribeRepos) ---

function handleComAtprotoSyncSubscribeReposCommit(sdk: HostSDK, commit: ComAtprotoSyncSubscribeReposCommit): { ok: true; detail: string } {
  if (commit.action !== "create") return { ok: true, detail: "skip non-create" };

  const collection = str(commit.collection ?? "");

  if (collection.startsWith("com.etzhayyim.apps.kami.")) {
    return { ok: true, detail: `processed ${collection}` };
  }

  if (collection === "app.bsky.feed.like") {
    return { ok: true, detail: "engagement noted" };
  }

  return { ok: true, detail: "commit accepted" };
}

// --- Graph Queries ---

// --- Extended Commands ---

async function cmdStats(sdk: HostSDK, _p: Uint8Array): Promise<unknown> {
  const data = ([] as Record<string, unknown>[]);
  return { stats: data, agent: "Sabi-Otoshi!!" };
}

async function cmdExportData(sdk: HostSDK, p: Uint8Array): Promise<unknown> {
  const args = JSON.parse(str(p) || "{}");
  const lim = Math.min(Number(args.limit) || 100, 1000);
  const data = ([] as Record<string, unknown>[]);
  return { format: "json", data };
}

function cmdHealth(_sdk: HostSDK, _body: Uint8Array): unknown {
  return { status: "healthy", agent: "Sabi-Otoshi!!", nanoid: appId, did: actorDID, ts: nowISO() };
}

function cmdDescribe(_sdk: HostSDK, _p: Uint8Array): unknown {
  return {
    name: "Sabi-Otoshi!!", did: actorDID, nanoid: appId, domain: "kami",
    capabilities: ["new-game", "spray", "select-item", "get-state", "get-leaderboard", "submit-score", "stats", "export", "describe"],
    protocols: ["xrpc", "w-protocol", "mcp"],
  };
}

async function cmdAudit(sdk: HostSDK, p: Uint8Array): Promise<unknown> {
  const args = JSON.parse(str(p) || "{}");
  const lim = Math.min(Number(args.limit) || 50, 200);
  const rows = ([] as Record<string, unknown>[]);
  return { audit: rows, count: rows.length };
}
async function cmdSummarize(sdk: HostSDK, p: Uint8Array): Promise<unknown> {
  const args = JSON.parse(str(p) || "{}");
  const topic = str(args.topic ?? "Sabi-Otoshi!!");
  const data = ([] as Record<string, unknown>[]);
  const summary = await llmAsk(`Summarize ${topic} data: ${JSON.stringify(data)}. Be concise.`);
  return { summary, topic };
}

// --- CPC/UNSPSC Classification Commands ---

async function cmdClassifyItem(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.classifyItem", body);
  const itemId = str(args.itemId ?? "");
  const item = ITEM_CATALOG.find(i => i.id === itemId);
  if (!item) return { error: "unknown item" };
  const classifiedRkey = genID("classified");
  await createKyselyDb().insertInto("vertex_kami_sabiotoshi_classified_item" as any).values({
    vertex_id: `at://${actorDID || "did:web:s4b10t05.etzhayyim.com"}/com.etzhayyim.apps.kami.sabiotoshi.classifiedItem/${classifiedRkey}`,
    sensitivity_ord: 2,
    owner_did: actorDID || "did:web:s4b10t05.etzhayyim.com",
    actor_id: appId || "s4b10t05",
    item_id: item.id,
    name: item.name,
    name_ja: item.nameJa,
    cpc_code: item.cpcCode,
    cpc_desc: item.cpcDesc,
    unspsc_code: item.unspscCode,
    unspsc_desc: item.unspscDesc,
    difficulty: item.difficulty,
    created_at: nowISO(),
    org_id: "anon",
    user_id: "anon",
  }).execute();
  return { classification: { cpc: item.cpcCode, 'cpcDesc': item.cpcDesc, unspsc: item.unspscCode, 'unspscDesc': item.unspscDesc } };
}

function cmdSearchByCpc(sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.searchByCpc", body);
  const code = str(args.cpcCode ?? "");
  if (!code) return { items: ITEM_CATALOG.map(i => ({ id: i.id, name: i.name, cpc: i.cpcCode, 'cpcDesc': i.cpcDesc })) };
  const matches = ITEM_CATALOG.filter(i => i.cpcCode.startsWith(code));
  return { items: matches.map(i => ({ id: i.id, name: i.name, 'nameJa': i.nameJa, cpc: i.cpcCode, 'cpcDesc': i.cpcDesc })) };
}

function cmdSearchByUnspsc(sdk: HostSDK, body: Uint8Array): unknown {
  const args = parseLexiconInput("com.etzhayyim.apps.kami.searchByUnspsc", body);
  const code = str(args.unspscCode ?? "");
  if (!code) return { items: ITEM_CATALOG.map(i => ({ id: i.id, name: i.name, unspsc: i.unspscCode, 'unspscDesc': i.unspscDesc })) };
  const matches = ITEM_CATALOG.filter(i => i.unspscCode.startsWith(code));
  return { items: matches.map(i => ({ id: i.id, name: i.name, 'nameJa': i.nameJa, unspsc: i.unspscCode, 'unspscDesc': i.unspscDesc })) };
}

// --- SDK + App Setup ---

// Layer 3: Shinka (Social Evolution)
const shinkaEnabled = true;

export async function runHeartbeat(sdk: HostSDK): Promise<{ ok: boolean; actions: Array<Record<string, unknown>> }> {
  const actions: Array<Record<string, unknown>> = [];
  const ts = nowISO();
  const cadence = await resolveHeartbeatCadence("did:web:s4b10t05.etzhayyim.com", cadenceState, inbox);
  actions.push({ action: "cadenceResolved", mood: cadence.mood, reason: cadence.reason, ts });

  // --- shouldDrill: kyumei-koji self-research ---

  // --- shouldAnalyze: domain data analysis ---

  // --- shouldValidate: data quality check ---

  if (actions.length === 1) actions.push({ action: "noop", mood: cadence.mood, ts });
  return { ok: true, actions };
}

// --- Multi-DID ---

// --- Domain Validation ---

function validateRecord(record: Record<string, unknown>): { valid: boolean; errors: string[] } {
  const errors: string[] = [];
  if (!record.id) errors.push("id is required");
  if (typeof record.id === "string" && record.id.length > 128) errors.push("id exceeds 128 chars");
  if (record.orgId && typeof record.orgId !== "string") errors.push("orgId must be string");
  if (record.createdAt && typeof record.createdAt === "string") {
    if (isNaN(Date.parse(record.createdAt as string))) errors.push("createdAt is not valid ISO date");
  }
  return { valid: errors.length === 0, errors };
}

// --- cross-actor invoke ---

export { handleComAtprotoSyncSubscribeReposCommit };

export default createWorkerExport((sdk) => {
  appId = sdk.pds.selfNanoid ?? "";
  actorDID = sdk.pds.selfRepo ?? "";
  sdk.app
      .command(nsid("com.etzhayyim.apps.kami.newGame"), (ctx, body) => cmdNewGame(sdk, body),
      asAgentTool("Start a new Sabi-Otoshi game"),
      withCapabilityTags("game", "kami"),
      withOCELEvent("governance.audit"),
      )
      .command(nsid("com.etzhayyim.apps.kami.spray"), (ctx, body) => cmdSpray(sdk, body),
      asAgentTool("Spray water at a rust zone"),
      withCapabilityTags("game", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.selectItem"), (ctx, body) => cmdSelectItem(sdk, body),
      asAgentTool("View item details"),
      withCapabilityTags("query", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.getState"), (ctx, body) => cmdGetState(sdk, body),
      asAgentTool("Get game catalog and nozzles"),
      withCapabilityTags("query", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.getLeaderboard"), (ctx, body) => cmdGetLeaderboard(sdk, body),
      asAgentTool("Get Sabi-Otoshi leaderboard"),
      withCapabilityTags("query", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.submitScore"), (ctx, body) => cmdSubmitScore(sdk, body),
      asAgentTool("Submit a score"),
      withCapabilityTags("write", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.wave"), (ctx, body) => cmdWave(sdk, body),
      asAgentTool("Respond to wave greeting"),
      withCapabilityTags("social", "greeting"),
      )
      .command(nsid("com.etzhayyim.apps.kami.statsSabiotoshi"), (ctx, body) => cmdStats(sdk, body),
      asAgentTool("Get Sabi-Otoshi statistics"),
      withCapabilityTags("analytics", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.exportSabiotoshi"), (ctx, body) => cmdExportData(sdk, body),
      asAgentTool("Export Sabi-Otoshi data"),
      withCapabilityTags("export", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.healthSabiotoshi"), (ctx, body) => cmdHealth(sdk, body),
      asAgentTool("Sabi-Otoshi health check"),
      withCapabilityTags("diagnostics", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.describeSabiotoshi"), (ctx, body) => cmdDescribe(sdk, body),
      asAgentTool("Describe Sabi-Otoshi capabilities"),
      withCapabilityTags("meta", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.summarizeSabiotoshi"), (ctx, body) => cmdSummarize(sdk, body),
      asAgentTool("AI summary of Sabi-Otoshi"),
      withCapabilityTags("ai", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.auditSabiotoshi"), (ctx, body) => cmdAudit(sdk, body),
      asAgentTool("Audit log for Sabi-Otoshi"),
      withCapabilityTags("audit", "kami"),
      )
      .command(nsid("com.etzhayyim.apps.kami.classifyItem"), (ctx, body) => cmdClassifyItem(sdk, body),
      asAgentTool("Classify item with CPC/UNSPSC codes"),
      withCapabilityTags("classification", "cpc", "unspsc"),
      )
      .command(nsid("com.etzhayyim.apps.kami.searchByCpc"), (ctx, body) => cmdSearchByCpc(sdk, body),
      asAgentTool("Search items by CPC product code"),
      withCapabilityTags("query", "cpc"),
      )
      .command(nsid("com.etzhayyim.apps.kami.searchByUnspsc"), (ctx, body) => cmdSearchByUnspsc(sdk, body),
      asAgentTool("Search items by UNSPSC code"),
      withCapabilityTags("query", "unspsc"),
      );
});
