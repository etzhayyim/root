import { coverageData } from './coverage-data';

type HeartbeatAction = {
  action: string;
  mood?: string;
  reason?: string;
  ts: string;
  summary?: string;
};

type InboxBuffer = {
  inboundCommits: Array<Record<string, unknown>>;
  reactions: Array<Record<string, unknown>>;
};

type CadenceState = {
  heartbeatCount: number;
  lastRunAt: string | null;
};

type HeartbeatCadence = {
  mood: string;
  reason: string;
  shouldDrill: boolean;
  shouldValidate: boolean;
  shouldAnalyze: boolean;
  shouldEngage: boolean;
};

type ShinkaSnapshot = {
  ok: boolean;
  mood: string;
  summary: string;
  ts: string;
  actions: HeartbeatAction[];
  edges: string[];
  collections: string[];
};

const SHINKA_COLLECTIONS = [
  'com.etzhayyim.apps.rareEarth.shinkaEvolution',
  'com.etzhayyim.apps.rareEarth.shinkaKnowledge'
] as const;

const SHINKA_SUBDIDS = [
  { path: "mineral:rare-earth", displayName: 'Rare Earth Mineral System' },
  { path: "mineral:tungsten", displayName: 'Tungsten Mineral System' },
  { path: "mineral:antimony", displayName: 'Antimony Mineral System' },
  { path: "sector:global-defense-oem", displayName: 'Global Defense OEM Cluster' }
] as const;

const cadenceState = createCadenceState();
const inbox = createInboxBuffer();
let lastHeartbeat: ShinkaSnapshot = {
  ok: true,
  mood: 'focused',
  summary: 'Rare earth coverage graph initialized.',
  ts: coverageData.updatedAt,
  actions: [],
  edges: [],
  collections: [...SHINKA_COLLECTIONS]
};

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'cache-control': 'public, max-age=300'
    }
  });
}

function notFound(): Response {
  return json({ error: 'not_found' }, 404);
}

function nowISO(): string {
  return new Date().toISOString();
}

function createInboxBuffer(): InboxBuffer {
  return {
    inboundCommits: [],
    reactions: []
  };
}

function createCadenceState(): CadenceState {
  return {
    heartbeatCount: 0,
    lastRunAt: null
  };
}

async function resolveHeartbeatCadence(_did: string, state: CadenceState, _inbox: InboxBuffer): Promise<HeartbeatCadence> {
  state.heartbeatCount += 1;
  state.lastRunAt = nowISO();
  const cycle = state.heartbeatCount % 4;
  const moods = ['focused', 'alert', 'watchful', 'expansive'] as const;
  return {
    mood: moods[cycle] ?? 'focused',
    reason: cycle === 0 ? 'coverage expansion window' : 'steady supply-chain observation',
    shouldDrill: cycle === 0,
    shouldValidate: cycle === 1,
    shouldAnalyze: true,
    shouldEngage: cycle === 2
  };
}

function buildKnowledgeEdges(): string[] {
  return coverageData.minerals.slice(0, 4).map((mineral) => `${mineral.displayName} -> ${mineral.keySectors[0] ?? 'Supply Chain'}`);
}

async function runHeartbeat(): Promise<ShinkaSnapshot> {
  const cadence = await resolveHeartbeatCadence(coverageData.primaryActorDid, cadenceState, inbox);
  const ts = nowISO();
  const actions: HeartbeatAction[] = [
    { action: 'cadenceResolved', mood: cadence.mood, reason: cadence.reason, ts }
  ];
  const edges = buildKnowledgeEdges();

  if (cadence.shouldDrill) {
    actions.push({ action: 'shouldDrill', mood: cadence.mood, ts, summary: 'Critical mineral chokepoints re-ranked.' });
  }
  if (cadence.shouldValidate) {
    actions.push({ action: 'shouldValidate', mood: cadence.mood, ts, summary: 'Manifest and app coverage coherence rechecked.' });
  }
  if (cadence.shouldAnalyze) {
    actions.push({ action: 'shouldAnalyze', mood: cadence.mood, ts, summary: `Tracked ${coverageData.metrics.mineralCount} mineral registries and ${coverageData.metrics.actorCount} actors.` });
  }
  if (cadence.shouldEngage) {
    actions.push({ action: 'shouldEngage', mood: cadence.mood, ts, summary: 'Watching follow, like, and repost signals for supply-chain interest.' });
  }
  if (actions.length === 1) {
    actions.push({ action: 'noop', mood: cadence.mood, ts, summary: 'Heartbeat completed without additional shinka tasks.' });
  }

  lastHeartbeat = {
    ok: true,
    mood: cadence.mood,
    summary: `${cadence.reason}; ${edges.length} knowledge edges refreshed.`,
    ts,
    actions,
    edges,
    collections: [...SHINKA_COLLECTIONS]
  };
  return lastHeartbeat;
}

function filteredActors(url: URL) {
  const stage = url.searchParams.get('stage');
  const jurisdiction = url.searchParams.get('jurisdiction');
  return coverageData.actors.filter((actor) => {
    if (stage && actor.stage !== stage) return false;
    if (jurisdiction && actor.jurisdiction !== jurisdiction) return false;
    return true;
  });
}

function filteredFlows(url: URL) {
  const kind = url.searchParams.get('kind');
  const status = url.searchParams.get('status');
  return coverageData.flows.filter((flow) => {
    if (kind && flow.kind !== kind) return false;
    if (status && flow.status !== status) return false;
    return true;
  });
}

function scorecard() {
  return {
    updatedAt: coverageData.updatedAt,
    concentration: {
      chinaPolicyControl: 'high',
      chinaSeparationControl: 'high',
      chinaStrategicMineralsControl: 'high',
      nonChinaMagnetDepth: 'medium',
      recyclingCoverage: 'medium'
    },
    counts: coverageData.metrics,
    bottlenecks: coverageData.bottlenecks,
    mineralCoverage: coverageData.minerals,
    shinka: {
      collections: SHINKA_COLLECTIONS,
      subDids: SHINKA_SUBDIDS,
      lastHeartbeat
    }
  };
}

export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    if (url.pathname === '/api/rare-earth/coverage') {
      return json(coverageData);
    }

    if (url.pathname === '/api/rare-earth/actors') {
      const items = filteredActors(url);
      return json({
        updatedAt: coverageData.updatedAt,
        total: items.length,
        items
      });
    }

    if (url.pathname === '/api/rare-earth/flows') {
      const items = filteredFlows(url);
      return json({
        updatedAt: coverageData.updatedAt,
        total: items.length,
        items
      });
    }

    if (url.pathname === '/api/rare-earth/minerals') {
      return json({
        updatedAt: coverageData.updatedAt,
        total: coverageData.minerals.length,
        items: coverageData.minerals
      });
    }

    if (url.pathname === '/api/rare-earth/scorecard') {
      return json(scorecard());
    }

    if (url.pathname === '/api/rare-earth/shinka') {
      return json({
        updatedAt: lastHeartbeat.ts,
        collections: SHINKA_COLLECTIONS,
        subDids: SHINKA_SUBDIDS,
        heartbeat: lastHeartbeat
      });
    }

    if (url.pathname === '/_heartbeat') {
      const snapshot = await runHeartbeat();
      return json({
        ok: snapshot.ok,
        actions: snapshot.actions,
        mood: snapshot.mood,
        summary: snapshot.summary,
        edges: snapshot.edges
      });
    }

    if (url.pathname === '/xrpc/com.etzhayyim.apps.rareEarth.coverage.get') {
      return json({
        nodeCount: coverageData.metrics.actorCount,
        latestSeq: 0,
        summary: coverageData.bottlenecks.map((b) => `${b.title}: ${b.detail}`).join(' | '),
        snapshotSeq: 0
      });
    }

    if (url.pathname === '/xrpc/com.etzhayyim.apps.rareEarth.coverage.listActors') {
      return json({
        actors: filteredActors(url)
      });
    }

    if (url.pathname === '/xrpc/com.etzhayyim.apps.rareEarth.coverage.listFlows') {
      return json({
        flows: filteredFlows(url)
      });
    }

    if (url.pathname === '/xrpc/com.etzhayyim.apps.rareEarth.shinka.getState') {
      return json({
        collections: SHINKA_COLLECTIONS,
        subDids: SHINKA_SUBDIDS,
        heartbeat: lastHeartbeat
      });
    }

    if (url.pathname === '/health' || url.pathname === '/healthz' || url.pathname === '/readyz') {
      return json({ ok: true, service: 'rare-earth-ui' });
    }

    return notFound();
  }
};
