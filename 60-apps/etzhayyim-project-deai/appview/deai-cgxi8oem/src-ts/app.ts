/**
 * deai Worker — Spirit-in-Physics 研究データ収集フロントエンド
 *
 * 主目的: spirit-in-physics.com/api（研究 SSoT）へのデータ中継。
 * マッチング機能は deai 独自（KV ベース）。
 *
 * データフロー:
 *   deai app → deai Worker (本ファイル) → spirit-in-physics.com/api
 *                                        → RisingWave (domain tier)
 */

import { createWorkerExport } from "@etzhayyim/kotodama-host-sdk";
import type { Context } from "hono";

const SIP_BASE = "https://spirit-in-physics.com/api";

async function proxyToSip(path: string, body: unknown): Promise<Response> {
  return fetch(`${SIP_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// Spirit Type taxonomy from Spirit-in-Physics paper (Kawasaki et al. 2026)
const SPIRIT_TYPES = ["Hero", "Sage", "Lover", "Caregiver"] as const;
type SpiritType = (typeof SPIRIT_TYPES)[number];

// Jung type compatibility matrix (tensegrity complementarity, not just similarity)
const COMPATIBILITY: Record<SpiritType, Record<SpiritType, number>> = {
  Hero:      { Hero: 700, Sage: 600, Lover: 800, Caregiver: 950 },
  Sage:      { Hero: 600, Sage: 650, Lover: 950, Caregiver: 700 },
  Lover:     { Hero: 800, Sage: 950, Lover: 600, Caregiver: 700 },
  Caregiver: { Hero: 950, Sage: 700, Lover: 700, Caregiver: 650 },
};

// Stimulus word sets per Spirit Type axis (Word Association Experiment)
const STIMULUS_WORDS_JA = [
  "守る", "挑戦", "使命", "勇気",       // Hero axis
  "知恵", "真実", "探求", "省察",       // Sage axis
  "美", "感性", "つながり", "喜び",     // Lover axis
  "養う", "共感", "奉仕", "温かさ",    // Caregiver axis
  "孤独", "希望", "変化", "静けさ",    // Universal / shadow probes
  "自由", "絆", "成長", "癒し",
];

const STIMULUS_WORDS_EN = [
  "protect", "challenge", "mission", "courage",
  "wisdom", "truth", "explore", "reflect",
  "beauty", "feeling", "connect", "joy",
  "nurture", "empathy", "serve", "warmth",
  "alone", "hope", "change", "stillness",
  "freedom", "bond", "grow", "heal",
];

function generateSessionId(): string {
  return crypto.randomUUID();
}

function computeCohortHash(spiritType: SpiritType, emotionCentroid: number[]): string {
  // DJB2-style hash over spirit type + quantized emotion vector
  const parts = [spiritType, ...emotionCentroid.map((v) => Math.round(v / 100).toString())];
  const canonical = parts.join("|");
  let h = 5381;
  for (let i = 0; i < canonical.length; i++) {
    h = ((h << 5) + h + canonical.charCodeAt(i)) & 0xffffffff;
  }
  const posH = h >>> 0;
  return `d${posH.toString(16).padStart(8, "0")}${(canonical.length & 0xffff).toString(16).padStart(4, "0")}`;
}

function classifySpiritType(responses: Array<{ word: string; humeScores: Record<string, number>; reactionTimeMs: number }>): SpiritType {
  // Spirit-in-Physics scoring:
  // P(w_O|w_I) ∝ exp(w_I·w_O) × r^α × exp(γ·ΔSP/λ) × exp(η·F)
  // Simplified: score each axis by emotion profile of responses to axis words
  const axisScores: Record<SpiritType, number> = { Hero: 0, Sage: 0, Lover: 0, Caregiver: 0 };
  const axisWords: Record<SpiritType, string[]> = {
    Hero:      ["守る", "挑戦", "使命", "勇気", "protect", "challenge", "mission", "courage"],
    Sage:      ["知恵", "真実", "探求", "省察", "wisdom", "truth", "explore", "reflect"],
    Lover:     ["美", "感性", "つながり", "喜び", "beauty", "feeling", "connect", "joy"],
    Caregiver: ["養う", "共感", "奉仕", "温かさ", "nurture", "empathy", "serve", "warmth"],
  };
  for (const r of responses) {
    for (const [type, words] of Object.entries(axisWords) as [SpiritType, string[]][]) {
      if (!words.includes(r.word)) continue;
      // Fast reaction = strong archetype activation
      const reactionBonus = r.reactionTimeMs > 0 ? 1000 / r.reactionTimeMs : 0;
      // Emotion scores contribute to axis
      const e = r.humeScores;
      const typeScore: Record<SpiritType, number> = {
        Hero:      (e.focus ?? 0) + (e.surprise ?? 0) + reactionBonus * 0.3,
        Sage:      (e.calm ?? 0) + (e.awe ?? 0) + reactionBonus * 0.2,
        Lover:     (e.joy ?? 0) + (e.awe ?? 0) + reactionBonus * 0.25,
        Caregiver: (e.calm ?? 0) + (e.joy ?? 0) + reactionBonus * 0.15,
      };
      axisScores[type] += typeScore[type];
    }
  }
  return (Object.entries(axisScores) as [SpiritType, number][]).reduce((a, b) => (b[1] > a[1] ? b : a))[0];
}

function computeResonanceScore(typeA: SpiritType, centroidA: number[], typeB: SpiritType, centroidB: number[]): number {
  // Tensegrity resonance = Jung compatibility × RBF kernel distance
  const jungScore = COMPATIBILITY[typeA][typeB];
  const sigma = 500; // RBF bandwidth (permille scale)
  const dist2 = centroidA.reduce((sum, v, i) => sum + (v - (centroidB[i] ?? 0)) ** 2, 0);
  const rbf = Math.exp(-dist2 / (2 * sigma ** 2));
  // U_spirit: higher resonance = more connection = lower separation entropy
  return Math.round(jungScore * rbf);
}

export default createWorkerExport((sdk) => {
  // ──────────────────────────────────────────
  // Hume AI WebSocket proxy
  // Upgrades to WS and relays frames to wss://api.hume.ai/v0/stream/models
  // ──────────────────────────────────────────
  sdk.router.get("/api/hume-ws", (c) => {
    const upgrade = c.req.header("Upgrade");
    if (upgrade?.toLowerCase() !== "websocket") {
      return c.text("Expected WebSocket upgrade", 426);
    }
    const env = c.env as Record<string, unknown>;
    const apiKey = env["HUME_API_KEY"] as string | undefined;
    if (!apiKey) return c.text("HUME_API_KEY not configured", 503);

    const { 0: client, 1: server } = new WebSocketPair();
    server.accept();

    const hume = new WebSocket(`wss://api.hume.ai/v0/stream/models?apikey=${apiKey}`);

    server.addEventListener("message", (e) => {
      if (hume.readyState === WebSocket.OPEN) hume.send(e.data as string);
    });
    server.addEventListener("close", (e) => {
      if (hume.readyState !== WebSocket.CLOSED) hume.close(e.code, e.reason);
    });
    hume.addEventListener("message", (e) => {
      if (server.readyState === WebSocket.OPEN) server.send(e.data as string);
    });
    hume.addEventListener("close", (e) => {
      if (server.readyState !== WebSocket.CLOSED) server.close(e.code, e.reason);
    });
    hume.addEventListener("error", () => {
      if (server.readyState !== WebSocket.CLOSED) server.close(1011, "upstream error");
    });

    return new Response(null, { status: 101, webSocket: client } as ResponseInit & { webSocket: WebSocket });
  });

  // ──────────────────────────────────────────
  // Assessment
  // ──────────────────────────────────────────
  sdk.app.command(
    "com.etzhayyim.apps.deai.startAssessment",
    async (c: Context) => {
      const body = await c.req.json().catch(() => ({}));
      const locale = body.locale ?? "ja";
      const words = locale === "en" ? STIMULUS_WORDS_EN : STIMULUS_WORDS_JA;
      const sessionId = generateSessionId();
      const expiresAt = new Date(Date.now() + 30 * 60 * 1000).toISOString();
      // Store session in KV (key = session:{sessionId}, TTL 30m)
      await sdk.kv?.put(`session:${sessionId}`, JSON.stringify({ words, responses: [], createdAt: new Date().toISOString() }), { expirationTtl: 1800 }).catch(() => {});
      return c.json({ sessionId, stimulusWords: words, expiresAt });
    },
    { agentTool: "Start a Spirit-in-Physics Word Association assessment session", capabilityTags: ["deai", "assessment"] },
  );

  sdk.app.command(
    "com.etzhayyim.apps.deai.submitResponse",
    async (c: Context) => {
      const body = await c.req.json();
      const { sessionId, word, reactionTimeMs, humeScores, spDelta, stimulusWordId, participantId, sessionIndex } = body;
      if (!sessionId || !word || !humeScores) return c.json({ error: "missing fields" }, 400);

      // spirit-in-physics API に中継（非同期、失敗しても続行）
      if (participantId && stimulusWordId) {
        Promise.all([
          proxyToSip("/assessments/word-response", {
            participantId,
            session: sessionIndex ?? 0,
            stimulusWordId,
            responseWord: body.responseWord ?? "",
            reactionTimeMs: reactionTimeMs ?? 0,
            eventId: crypto.randomUUID(),
          }).catch(() => {}),
          proxyToSip("/assessments/artifact", {
            participantId,
            session: sessionIndex ?? 0,
            artifactType: "hume-face",
            payload: {
              stimulusWordId,
              word,
              reactionTimeMs,
              emotions: Object.entries(humeScores).map(([name, score]) => ({ name, score })),
              spDelta: spDelta ?? 0,
              timestamp: new Date().toISOString(),
            },
            eventId: crypto.randomUUID(),
          }).catch(() => {}),
        ]);
      }

      const raw = await sdk.kv?.get(`session:${sessionId}`);
      if (!raw) return c.json({ error: "session not found or expired" }, 404);
      const session = JSON.parse(raw);
      session.responses.push({ word, reactionTimeMs: reactionTimeMs ?? 0, humeScores, spDelta: spDelta ?? 0 });
      const progress = session.responses.length;

      // If all words answered, classify and persist profile
      if (progress >= session.words.length) {
        const spiritType = classifySpiritType(session.responses);
        const emotionCentroid = [
          "joy", "sadness", "anger", "fear", "disgust", "calm", "focus", "surprise", "confusion", "awe",
        ].map((k) => {
          const vals = session.responses.map((r: { humeScores: Record<string, number> }) => r.humeScores[k] ?? 0);
          return Math.round(vals.reduce((a: number, b: number) => a + b, 0) / vals.length);
        });
        const cohortHash = computeCohortHash(spiritType, emotionCentroid);
        const cohortDid = `did:web:decom.etzhayyim.ai:${cohortHash}`;
        await sdk.kv?.put(
          `profile:${cohortDid}`,
          JSON.stringify({ cohortDid, spiritType, emotionCentroid, assessedAt: new Date().toISOString(), checkinCount: 0 }),
          { expirationTtl: 86400 * 365 },
        ).catch(() => {});
        await sdk.kv?.delete(`session:${sessionId}`).catch(() => {});
      } else {
        await sdk.kv?.put(`session:${sessionId}`, JSON.stringify(session), { expirationTtl: 1800 }).catch(() => {});
      }

      return c.json({ accepted: true, progress });
    },
    { agentTool: "Submit word association response with Hume emotion scores", capabilityTags: ["deai", "assessment"] },
  );

  // ──────────────────────────────────────────
  // Profile
  // ──────────────────────────────────────────
  sdk.app.command(
    "com.etzhayyim.apps.deai.getProfile",
    async (c: Context) => {
      const did = c.req.query("did");
      if (!did) return c.json({ error: "did required" }, 400);
      const raw = await sdk.kv?.get(`profile:${did}`);
      if (!raw) return c.json({ error: "profile not found" }, 404);
      return c.json(JSON.parse(raw));
    },
    { agentTool: "Get Spirit profile by cohort DID", capabilityTags: ["deai", "profile"] },
  );

  // ──────────────────────────────────────────
  // Matches
  // ──────────────────────────────────────────
  sdk.app.command(
    "com.etzhayyim.apps.deai.listMatches",
    async (c: Context) => {
      const did = c.req.query("did");
      const limit = Math.min(parseInt(c.req.query("limit") ?? "20"), 50);
      if (!did) return c.json({ error: "did required" }, 400);

      const raw = await sdk.kv?.get(`profile:${did}`);
      if (!raw) return c.json({ matches: [] });
      const profile = JSON.parse(raw) as { spiritType: SpiritType; emotionCentroid: number[] };

      // Load all profiles from KV (MVP: iterate known DIDs via index)
      const indexRaw = await sdk.kv?.get("profile:index");
      const index: string[] = indexRaw ? JSON.parse(indexRaw) : [];

      const matches = [];
      for (const candidateDid of index.slice(0, 200)) {
        if (candidateDid === did) continue;
        const cRaw = await sdk.kv?.get(`profile:${candidateDid}`);
        if (!cRaw) continue;
        const candidate = JSON.parse(cRaw) as { cohortDid: string; spiritType: SpiritType; emotionCentroid: number[]; assessedAt: string };
        const resonanceScore = computeResonanceScore(
          profile.spiritType, profile.emotionCentroid,
          candidate.spiritType, candidate.emotionCentroid,
        );
        const compatibilityReason = `${profile.spiritType}×${candidate.spiritType}: テンセグリティ共鳴スコア ${resonanceScore}/1000`;
        matches.push({
          cohortDid: candidate.cohortDid,
          spiritType: candidate.spiritType,
          resonanceScore,
          spiritCompatibility: COMPATIBILITY[profile.spiritType][candidate.spiritType],
          separationDelta: resonanceScore - 500,
          compatibilityReason,
          matchedAt: new Date().toISOString(),
          hasConversation: false,
        });
      }
      matches.sort((a, b) => b.resonanceScore - a.resonanceScore);
      return c.json({ matches: matches.slice(0, limit) });
    },
    { agentTool: "List Spirit resonance matches", capabilityTags: ["deai", "match"] },
  );

  // ──────────────────────────────────────────
  // Check-in
  // ──────────────────────────────────────────
  sdk.app.command(
    "com.etzhayyim.apps.deai.createCheckin",
    async (c: Context) => {
      const body = await c.req.json();
      const { humeScores, modality } = body;
      const did = c.req.header("x-actor-did");
      if (!did || !humeScores) return c.json({ error: "missing fields" }, 400);

      // Rate limit: 1 check-in per 20 hours
      const lastRaw = await sdk.kv?.get(`checkin-last:${did}`);
      if (lastRaw) {
        const last = new Date(lastRaw).getTime();
        if (Date.now() - last < 20 * 3600 * 1000) {
          const nextAfter = new Date(last + 20 * 3600 * 1000).toISOString();
          return c.json({ error: "too soon", nextCheckinAfter: nextAfter }, 429);
        }
      }

      const profileRaw = await sdk.kv?.get(`profile:${did}`);
      const profile = profileRaw ? JSON.parse(profileRaw) : null;
      const checkinId = crypto.randomUUID();
      const now = new Date().toISOString();

      // Update emotion centroid (exponential moving average, α=0.2)
      const alpha = 0.2;
      const keys = ["joy", "sadness", "anger", "fear", "disgust", "calm", "focus", "surprise", "confusion", "awe"];
      const newCentroid = profile
        ? keys.map((k, i) => Math.round(alpha * (humeScores[k] ?? 0) + (1 - alpha) * (profile.emotionCentroid?.[i] ?? 0)))
        : keys.map((k) => humeScores[k] ?? 0);

      const updatedSpiritType = profile?.spiritType ?? "Sage";
      const spiritDelta = profile ? Math.round((humeScores.joy ?? 0) - (profile.emotionCentroid?.[0] ?? 500)) : 0;
      const nextCheckinAfter = new Date(Date.now() + 20 * 3600 * 1000).toISOString();

      if (profile) {
        profile.emotionCentroid = newCentroid;
        profile.checkinCount = (profile.checkinCount ?? 0) + 1;
        await sdk.kv?.put(`profile:${did}`, JSON.stringify(profile), { expirationTtl: 86400 * 365 }).catch(() => {});
      }
      await sdk.kv?.put(`checkin-last:${did}`, now, { expirationTtl: 86400 }).catch(() => {});

      return c.json({ checkinId, updatedSpiritType, spiritDelta, nextCheckinAfter, modality });
    },
    { agentTool: "Create daily Spirit check-in with Hume emotion scores", capabilityTags: ["deai", "checkin"] },
  );

  // ──────────────────────────────────────────
  // Messages (E2E encrypted)
  // ──────────────────────────────────────────
  sdk.app.command(
    "com.etzhayyim.apps.deai.sendMessage",
    async (c: Context) => {
      const body = await c.req.json();
      const { toCohortDid, ciphertext, iv, replyToId } = body;
      const fromDid = c.req.header("x-actor-did");
      if (!fromDid || !toCohortDid || !ciphertext || !iv) return c.json({ error: "missing fields" }, 400);
      if (!ciphertext.startsWith("signal:v1:")) return c.json({ error: "ciphertext must use signal:v1: prefix" }, 400);

      const messageId = crypto.randomUUID();
      const sentAt = new Date().toISOString();
      const msg = { messageId, fromCohortDid: fromDid, toCohortDid, ciphertext, iv, replyToId, sentAt };

      const convKey = [fromDid, toCohortDid].sort().join("|");
      const existingRaw = await sdk.kv?.get(`conv:${convKey}`);
      const messages = existingRaw ? JSON.parse(existingRaw) : [];
      messages.push(msg);
      // Keep last 500 messages only
      const trimmed = messages.slice(-500);
      await sdk.kv?.put(`conv:${convKey}`, JSON.stringify(trimmed), { expirationTtl: 86400 * 365 }).catch(() => {});

      return c.json({ messageId, sentAt });
    },
    { agentTool: "Send E2E encrypted message to a Spirit match", capabilityTags: ["deai", "message"] },
  );

  sdk.app.command(
    "com.etzhayyim.apps.deai.listMessages",
    async (c: Context) => {
      const withDid = c.req.query("withCohortDid");
      const selfDid = c.req.header("x-actor-did");
      const limit = Math.min(parseInt(c.req.query("limit") ?? "50"), 100);
      if (!selfDid || !withDid) return c.json({ error: "missing fields" }, 400);

      const convKey = [selfDid, withDid].sort().join("|");
      const raw = await sdk.kv?.get(`conv:${convKey}`);
      const messages = raw ? JSON.parse(raw) : [];
      return c.json({ messages: messages.slice(-limit) });
    },
    { agentTool: "List encrypted messages with a Spirit match", capabilityTags: ["deai", "message"] },
  );
});
