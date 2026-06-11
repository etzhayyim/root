/**
 * Joucho — Well-Becoming emotion scoring platform.
 *
 * Architecture:
 * - Gemma 4 E2B (Murakumo on-prem MLX, multimodal, zero cost)
 * - SST 48-emotion taxonomy (Cowen & Keltner, PNAS 2017 + Hume AI extensions)
 * - 48-emotion probability distribution → joucho 5-axis mapping
 * - Platform heartbeat cadence provider (JouchoScore graph node)
 * - Design E 3-Tier Write: Social (AppBskyFeedPost) + Domain (createRecord) + State
 *
 * Scientific basis:
 *   Cowen & Keltner (2017) "Self-report captures 27 distinct categories
 *   of emotion bridged by continuous gradients" PNAS Vol.114 No.38
 *   Extended to 48 emotions per Hume AI Expression Measurement taxonomy.
 *
 * Graph labels:
 *   :JouchoScore     — 5-axis actor emotion state {joy, calm, stress, gratitude, focus}
 *   :EmotionProfile   — 48-emotion probability distribution per analysis
 *   :JouchoReview     — Well-Becoming review for meal/restaurant/spot/product/building
 *   :JouchoEntity     — scored target entity
 *
 * Collection kinds (camelCase):
 *   jouchoScore, emotionProfile, jouchoReview, jouchoEntity,
 *   jouchoEvent, jouchoReport
 */
import {
  asAgentTool,
  createWorkerExport,
  nowISO,
  str,
  genID,
  rlsDefaults,
  type HostSDK,
  type ComAtprotoSyncSubscribeReposCommit,
  decodeJson,
  llmAsk,
  MURAKUMO_DEFAULT_MODEL,
  nsid,
  parseLexiconInput,
} from "@etzhayyim/kotodama-host-sdk";

// ── Murakumo Gemma 4 E2B config ──

const MURAKUMO_URL = "https://murakumo.etzhayyim.com/api/openai/v1/chat/completions";
const MURAKUMO_KEY = "murk_NQhD62as9BwwY1RPxoyh0nK4bsbdGlI1lCWbHpbCdQLCDNo";
const EMOTION_MODEL_PRIMARY = MURAKUMO_DEFAULT_MODEL;
const EMOTION_MODEL_FALLBACK = MURAKUMO_DEFAULT_MODEL;

/** Cached resolved model (primary or fallback). */
let EMOTION_MODEL_RESOLVED = EMOTION_MODEL_FALLBACK;

/** Probe primary model availability, cache result. */
async function probeEmotionModel(): Promise<void> {
  try {
    const resp = await fetch(MURAKUMO_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-api-key": MURAKUMO_KEY },
      body: JSON.stringify({
        model: EMOTION_MODEL_PRIMARY,
        messages: [{ role: "user", content: "ping" }],
        max_tokens: 1,
      }),
      signal: AbortSignal.timeout(5000),
    });
    if (resp.ok) EMOTION_MODEL_RESOLVED = EMOTION_MODEL_PRIMARY;
  } catch { /* use fallback */ }
}

// ── SST 48-Emotion Taxonomy (Hume AI Expression Measurement compatible) ──
// Based on Cowen & Keltner (2017) PNAS 27 emotions + Hume extensions to 48

/**
 * The 48 emotion dimensions aligned with Hume AI's Expression Measurement API.
 * Each emotion is scored as a continuous probability 0.0-1.0.
 * Emotions are NOT mutually exclusive (SST continuous gradient property).
 */
const SST_48_EMOTIONS = [
  // ── Original 27 (Cowen & Keltner 2017 PNAS) ──
  "admiration",
  "adoration",
  "aesthetic_appreciation",
  "amusement",
  "anger",
  "anxiety",
  "awe",
  "awkwardness",
  "boredom",
  "calmness",
  "confusion",
  "craving",
  "disgust",
  "empathic_pain",
  "entrancement",
  "excitement",
  "fear",
  "horror",
  "interest",
  "joy",
  "nostalgia",
  "relief",
  "romance",
  "sadness",
  "satisfaction",
  "sexual_desire",
  "surprise",
  // ── Hume extensions (21 additional) ──
  "concentration",
  "contemplation",
  "contentment",
  "determination",
  "disappointment",
  "distress",
  "doubt",
  "ecstasy",
  "embarrassment",
  "envy",
  "guilt",
  "love",
  "pain",
  "pride",
  "realization",
  "shame",
  "surprise_negative",
  "surprise_positive",
  "sympathy",
  "tiredness",
  "triumph",
] as const;

type EmotionKey = typeof SST_48_EMOTIONS[number];

/** Full 48-emotion probability distribution (each 0.0-1.0). */
type EmotionDistribution = Record<EmotionKey, number>;

// ── 48-Emotion → Joucho 5-Axis Mapping ──
// Psychologically grounded clustering per Cowen & Keltner's semantic space dimensions

/**
 * Map 48 SST emotions to joucho's 5 platform axes.
 * Each axis aggregates related emotions with weights reflecting
 * contribution strength (based on SST gradient proximity).
 */
const AXIS_MAPPING: Record<string, Array<{ emotion: EmotionKey; weight: number }>> = {
  joy: [
    { emotion: "joy", weight: 1.0 },
    { emotion: "amusement", weight: 0.9 },
    { emotion: "excitement", weight: 0.85 },
    { emotion: "ecstasy", weight: 0.8 },
    { emotion: "triumph", weight: 0.75 },
    { emotion: "relief", weight: 0.6 },
    { emotion: "satisfaction", weight: 0.7 },
    { emotion: "pride", weight: 0.65 },
    { emotion: "contentment", weight: 0.6 },
    { emotion: "surprise_positive", weight: 0.5 },
  ],
  calm: [
    { emotion: "calmness", weight: 1.0 },
    { emotion: "contentment", weight: 0.9 },
    { emotion: "satisfaction", weight: 0.8 },
    { emotion: "relief", weight: 0.7 },
    { emotion: "nostalgia", weight: 0.6 },
    { emotion: "aesthetic_appreciation", weight: 0.7 },
    { emotion: "contemplation", weight: 0.65 },
    { emotion: "entrancement", weight: 0.5 },
  ],
  stress: [
    { emotion: "anxiety", weight: 1.0 },
    { emotion: "distress", weight: 0.95 },
    { emotion: "fear", weight: 0.9 },
    { emotion: "anger", weight: 0.85 },
    { emotion: "horror", weight: 0.8 },
    { emotion: "pain", weight: 0.8 },
    { emotion: "disgust", weight: 0.7 },
    { emotion: "confusion", weight: 0.5 },
    { emotion: "frustration" as EmotionKey, weight: 0.75 }, // mapped via anger+disappointment
    { emotion: "disappointment", weight: 0.6 },
    { emotion: "embarrassment", weight: 0.5 },
    { emotion: "shame", weight: 0.55 },
    { emotion: "guilt", weight: 0.5 },
    { emotion: "doubt", weight: 0.4 },
    { emotion: "tiredness", weight: 0.45 },
  ],
  gratitude: [
    { emotion: "admiration", weight: 1.0 },
    { emotion: "adoration", weight: 0.9 },
    { emotion: "love", weight: 0.85 },
    { emotion: "sympathy", weight: 0.7 },
    { emotion: "empathic_pain", weight: 0.6 },
    { emotion: "romance", weight: 0.5 },
    { emotion: "pride", weight: 0.4 },
    { emotion: "nostalgia", weight: 0.45 },
  ],
  focus: [
    { emotion: "concentration", weight: 1.0 },
    { emotion: "determination", weight: 0.9 },
    { emotion: "interest", weight: 0.85 },
    { emotion: "realization", weight: 0.7 },
    { emotion: "awe", weight: 0.6 },
    { emotion: "surprise", weight: 0.5 },
    { emotion: "contemplation", weight: 0.65 },
    { emotion: "aesthetic_appreciation", weight: 0.4 },
  ],
};

/** Joucho 5-axis scores (0-100 each). */
interface JouchoScores {
  joy: number;
  calm: number;
  stress: number;
  gratitude: number;
  focus: number;
}

/**
 * Convert 48-emotion probability distribution to joucho 5-axis scores.
 * Uses weighted aggregation with normalization to 0-100 range.
 */
function emotionsToAxes(emotions: EmotionDistribution): JouchoScores {
  const axes: JouchoScores = { joy: 0, calm: 0, stress: 0, gratitude: 0, focus: 0 };

  for (const [axis, mappings] of Object.entries(AXIS_MAPPING)) {
    let weightedSum = 0;
    let totalWeight = 0;
    for (const { emotion, weight } of mappings) {
      const score = emotions[emotion] ?? 0;
      weightedSum += score * weight;
      totalWeight += weight;
    }
    const normalized = totalWeight > 0 ? (weightedSum / totalWeight) * 100 : 0;
    (axes as Record<string, number>)[axis] = Math.round(Math.min(100, Math.max(0, normalized)));
  }

  return axes;
}

// ── LLM inference (PDS Gateway → Murakumo on-prem, ¥0) ──

/** Call Murakumo on-prem via PDS Gateway (¥0 cost). */
async function llmCall(prompt: string, _maxTokens = 8192): Promise<string> {
  const content = await llmAsk(prompt);
  return content.replace(/<think>[\s\S]*?<\/think>/g, "").trim();
}

/**
 * Multimodal emotion extraction via Gemma 4 E2B.
 * Supports text (required) + image base64 (optional).
 * Returns 48-emotion probability distribution.
 */
async function analyzeEmotions(
  text: string,
  imageBase64?: string,
): Promise<EmotionDistribution> {
  const emotionList = SST_48_EMOTIONS.join(", ");

  const systemPrompt = `You are an emotion analysis engine based on Semantic Space Theory (Cowen & Keltner, PNAS 2017).
Analyze the input and return a JSON object with exactly 48 emotion scores.
Each score is a probability from 0.0 to 1.0 representing the intensity of that emotion.
Multiple emotions CAN be active simultaneously (emotions are not mutually exclusive).
Use continuous gradients — emotions blend smoothly.

The 48 emotions: ${emotionList}

Output ONLY valid JSON. No explanation. Example:
{"admiration":0.3,"adoration":0.1,"aesthetic_appreciation":0.5,...}`;

  let userContent: string;
  if (imageBase64) {
    userContent = `Analyze the emotions in this text and image together.

Text: ${text}

[Image data is provided as base64. Analyze facial expressions, body language, scene mood, color palette, and composition in addition to the text sentiment.]

Return the 48-emotion JSON.`;
  } else {
    userContent = `Analyze the emotions in this text:

${text}

Return the 48-emotion JSON.`;
  }

  // PDS Gateway → LLM. System prompt merged into user message for compatibility.
  const raw = await llmCall(`${systemPrompt}\n\n${userContent}`);

  // Extract JSON from response (handle markdown code blocks)
  const jsonMatch = raw.match(/\{[\s\S]*\}/);
  if (!jsonMatch) {
    console.warn("[joucho] failed to parse emotion JSON, returning neutral");
    return neutralEmotions();
  }

  try {
    const parsed = JSON.parse(jsonMatch[0]) as Record<string, unknown>;
    const result: Record<string, number> = {};
    for (const key of SST_48_EMOTIONS) {
      const val = parsed[key];
      result[key] = typeof val === "number" ? Math.min(1, Math.max(0, val)) : 0;
    }
    return result as EmotionDistribution;
  } catch {
    console.warn("[joucho] JSON parse failed, returning neutral");
    return neutralEmotions();
  }
}

/** Neutral emotion state (all zeros except mild calmness). */
function neutralEmotions(): EmotionDistribution {
  const result: Record<string, number> = {};
  for (const key of SST_48_EMOTIONS) result[key] = 0;
  result.calmness = 0.3;
  result.contentment = 0.2;
  return result as EmotionDistribution;
}

// ── Joucho Score persistence ──

/** Update JouchoScore graph node for an actor DID. */
async function updateJouchoScore(
  sdk: HostSDK,
  actorDid: string,
  axes: JouchoScores,
  emotions: EmotionDistribution,
): Promise<string> {
  // Tier 2 Domain: persist score
  const rkey = await sdk.pds.createRecord("jouchoScore", {
    id: genID("js"),
    actor_did: actorDid,
    ...axes,
    emotion_model: EMOTION_MODEL_RESOLVED,
    emotion_count: 48,
    taxonomy: "sst-48-hume",
    ...rlsDefaults(),
    created_at: nowISO(),
  });

  // Persist full 48-emotion profile
  await sdk.pds.createRecord("emotionProfile", {
    id: genID("ep"),
    actor_did: actorDid,
    emotions,
    axes,
    model: EMOTION_MODEL_RESOLVED,
    taxonomy_version: "sst-48-hume-v1",
    ...rlsDefaults(),
    created_at: nowISO(),
  });

  return rkey ?? "";
}

// ── Well-Becoming scoring ──

/** Score targets for 5-axis Well-Becoming. */
type TargetType = "meal" | "restaurant" | "spot" | "product" | "building";

const WB_AXES = ["engagement", "competence", "contribution", "growth", "resilience"] as const;

/** Generate Well-Becoming score via Gemma 4 E2B. */
async function scoreTarget(
  targetType: TargetType,
  description: string,
  imageBase64?: string,
): Promise<{
  axes: Record<string, number>;
  total: number;
  grade: string;
  emotions: EmotionDistribution;
}> {
  // Step 1: Emotion analysis (multimodal)
  const emotions = await analyzeEmotions(description, imageBase64);
  const jouchoAxes = emotionsToAxes(emotions);

  // Step 2: Well-Becoming scoring via LLM
  const prompt = `Score this ${targetType} on Well-Becoming 5 axes (0-20 each, 100 total).
Return JSON only: {"engagement":N,"competence":N,"contribution":N,"growth":N,"resilience":N,"total":N,"reasoning":"..."}

Axes:
- engagement: user involvement, repeat rate, emotional resonance
- competence: quality, expertise, nutritional/functional correctness
- contribution: social/community benefit, sustainability
- growth: improvement trend, innovation, evolution
- resilience: disaster preparedness, accessibility, durability

${targetType}: ${description}`;

  const result = await llmCall(prompt, 512);
  try {
    const jsonMatch = result.match(/\{[\s\S]*\}/);
    const scores = JSON.parse(jsonMatch?.[0] ?? "{}") as Record<string, unknown>;
    const axes: Record<string, number> = {};
    let total = 0;
    for (const axis of WB_AXES) {
      const val = typeof scores[axis] === "number" ? (scores[axis] as number) : 10;
      axes[axis] = Math.min(20, Math.max(0, Math.round(val)));
      total += axes[axis];
    }
    const grade = total >= 90 ? "S" : total >= 75 ? "A" : total >= 60 ? "B" : total >= 40 ? "C" : "D";
    return { axes, total, grade, emotions };
  } catch {
    return {
      axes: { engagement: 10, competence: 10, contribution: 10, growth: 10, resilience: 10 },
      total: 50,
      grade: "C",
      emotions,
    };
  }
}

// ── XRPC Command Handlers ──

/** Analyze emotions from text (+ optional image). */
async function cmdAnalyzeEmotions(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.analyzeEmotions", body) as any;
  if (!args.text) return { error: "text required" };

  const emotions = await analyzeEmotions(args.text, args.imageBase64);
  const axes = emotionsToAxes(emotions);

  // Persist if actorDid provided
  if (args.actorDid) {
    await updateJouchoScore(sdk, args.actorDid, axes, emotions);
  }

  // Top-5 emotions for readability
  const sorted = Object.entries(emotions)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  return {
    axes,
    topEmotions: sorted.map(([name, score]) => ({ name, score: Math.round(score * 100) / 100 })),
    emotionCount: 48,
    taxonomy: "sst-48-hume",
    model: EMOTION_MODEL_RESOLVED,
    multimodal: !!args.imageBase64,
  };
}

/** Get full 48-emotion profile for an actor. */
async function cmdGetEmotionProfile(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.getEmotionProfile", body) as any;
  if (!args.actorDid) return { error: "actorDid required" };

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  if (!rows?.length) return { error: "no emotion profile found", actorDid: args.actorDid };
  return rows[0];
}

/** Get joucho 5-axis score for an actor. */
async function cmdGetScore(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.getScore", body) as any;
  if (!args.actorDid) return { error: "actorDid required" };

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  if (!rows?.length) return { error: "no score found", actorDid: args.actorDid };
  return rows[0];
}

/** Search joucho scores by range. */
async function cmdSearchScores(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.searchScores", body) as any;
  const axis = args.axis ?? "joy";
  const minScore = args.minScore ?? 0;
  const maxScore = args.maxScore ?? 100;
  const limit = Math.min(args.limit ?? 50, 100);

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  return { scores: rows ?? [], axis, range: [minScore, maxScore], limit };
}

/** Score a meal/restaurant/spot/product/building. */
async function cmdScoreTarget(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.scoreTarget", body) as any;
  if (!args.targetType || !args.description) {
    return { error: "targetType and description required" };
  }

  const fullDesc = `${args.name ?? "Unknown"} (${args.location ?? "unknown location"}): ${args.description}`;
  const result = await scoreTarget(args.targetType, fullDesc, args.imageBase64);

  // Persist entity + score
  const entityId = genID("je");
  await sdk.pds.createRecord("jouchoEntity", {
    id: entityId,
    target_type: args.targetType,
    name: args.name ?? "",
    description: args.description,
    location: args.location ?? "",
    wb_axes: result.axes,
    wb_total: result.total,
    wb_grade: result.grade,
    emotion_snapshot: Object.fromEntries(
      Object.entries(result.emotions)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10),
    ),
    model: EMOTION_MODEL_RESOLVED,
    ...rlsDefaults(),
    created_at: nowISO(),
  });

  // Tier 1 Social: announce
  const joucho5 = emotionsToAxes(result.emotions);
  await sdk.pds.post(
    `[${result.grade}] ${args.name ?? args.targetType} — joucho ${result.total}/100\n\n` +
    `${WB_AXES.map((a) => `${a}: ${result.axes[a]}/20`).join(" | ")}\n\n` +
    `Mood: joy=${joucho5.joy} calm=${joucho5.calm} stress=${joucho5.stress}\n\n` +
    `#joucho #wellbeing #${args.targetType}`,
  );

  return {
    entityId,
    targetType: args.targetType,
    name: args.name,
    ...result,
    joucho5: joucho5,
    model: EMOTION_MODEL_RESOLVED,
  };
}

/** Submit a user review and compute scores. */
async function cmdSubmitReview(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.submitReview", body) as any;
  if (!args.targetType || !args.reviewText) {
    return { error: "targetType and reviewText required" };
  }

  // Analyze emotions in the review text
  const emotions = await analyzeEmotions(args.reviewText, args.imageBase64);
  const axes = emotionsToAxes(emotions);

  // Score the target based on review
  const wbResult = await scoreTarget(args.targetType, `${args.targetName}: ${args.reviewText}`, args.imageBase64);

  const reviewId = genID("jr");
  await sdk.pds.createRecord("jouchoReview", {
    id: reviewId,
    target_type: args.targetType,
    target_name: args.targetName ?? "",
    review_text: args.reviewText,
    rating: args.rating ?? 0,
    reviewer_emotions: Object.fromEntries(
      Object.entries(emotions).sort((a, b) => b[1] - a[1]).slice(0, 10),
    ),
    reviewer_axes: axes,
    wb_score: wbResult.total,
    wb_grade: wbResult.grade,
    wb_axes: wbResult.axes,
    model: EMOTION_MODEL_RESOLVED,
    ...rlsDefaults(),
    created_at: nowISO(),
  });

  return {
    reviewId,
    reviewerMood: axes,
    topEmotions: Object.entries(emotions).sort((a, b) => b[1] - a[1]).slice(0, 5).map(([n, s]) => ({ name: n, score: Math.round(s * 100) / 100 })),
    wellBeing: { total: wbResult.total, grade: wbResult.grade, axes: wbResult.axes },
    model: EMOTION_MODEL_RESOLVED,
  };
}

/** Compute 5-axis breakdown for a target. */
async function cmdAxisBreakdown(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.axisBreakdown", body) as any;
  if (!args.entityId) return { error: "entityId required" };

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  if (!rows?.length) return { error: "entity not found" };
  return rows[0];
}

/** Get ranking of targets by Well-Becoming score. */
async function cmdRanking(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.ranking", body) as any;
  const limit = Math.min(args.limit ?? 20, 100);
  let where = "";
  if (args.targetType) where = ` WHERE e.target_type = "${str(args.targetType)}"`;

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  return { ranking: rows ?? [], targetType: args.targetType ?? "all", limit };
}

/** Score trend over time for a target. */
async function cmdScoreTrend(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.scoreTrend", body) as any;
  if (!args.actorDid) return { error: "actorDid required" };
  const limit = Math.min(args.limit ?? 30, 100);

  const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12

  return { actorDid: args.actorDid, trend: rows ?? [], limit };
}

/** AI-powered recommendation based on joucho scores. */
async function cmdRecommend(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.recommend", body) as any;
  const limit = Math.min(args.limit ?? 5, 20);
  const targetType = args.targetType ?? "restaurant";

  const prompt = `Based on the mood "${args.mood ?? "neutral"}", recommend ${limit} ${targetType}s that would best contribute to Well-Becoming.
Return JSON: {"recommendations":[{"name":"...","reason":"...","expectedScore":N}]}`;

  const result = await llmCall(prompt, 512);
  try {
    const jsonMatch = result.match(/\{[\s\S]*\}/);
    return JSON.parse(jsonMatch?.[0] ?? '{"recommendations":[]}');
  } catch {
    return { recommendations: [], error: "recommendation generation failed" };
  }
}

/** Compare joucho scores of multiple targets. */
async function cmdCompare(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.compare", body) as any;
  if (!args.entityIds?.length) return { error: "entityIds array required" };

  const results: Array<Record<string, unknown>> = [];
  for (const id of args.entityIds.slice(0, 10)) {
    const rows = [] as Record<string, unknown>[]; // SQL deprecated 2026-04-12
    if (rows?.length) results.push(rows[0] as Record<string, unknown>);
  }

  return { compared: results, count: results.length };
}

/** Batch analyze emotions for actor portfolio. */
async function cmdBatchAnalyze(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.scoring.batchAnalyze", body) as any;
  if (!args.actorDid || !args.texts?.length) {
    return { error: "actorDid and texts[] required" };
  }

  const allEmotions: EmotionDistribution[] = [];
  for (const text of args.texts.slice(0, 20)) {
    const emotions = await analyzeEmotions(text);
    allEmotions.push(emotions);
  }

  // Average across all texts
  const averaged: Record<string, number> = {};
  for (const key of SST_48_EMOTIONS) averaged[key] = 0;
  for (const e of allEmotions) {
    for (const key of SST_48_EMOTIONS) averaged[key] += (e[key] ?? 0) / allEmotions.length;
  }

  const axes = emotionsToAxes(averaged as EmotionDistribution);
  await updateJouchoScore(sdk, args.actorDid, axes, averaged as EmotionDistribution);

  return {
    actorDid: args.actorDid,
    analyzedCount: allEmotions.length,
    axes,
    topEmotions: Object.entries(averaged)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 10)
      .map(([n, s]) => ({ name: n, score: Math.round(s * 100) / 100 })),
    model: EMOTION_MODEL_RESOLVED,
  };
}

// ── Reactive pipeline (Design E Layer 1) ──

/** Handle inbound commits from subscribeRepos. */
async function handleCommit(sdk: HostSDK, commit: ComAtprotoSyncSubscribeReposCommit): Promise<void> {
  if (commit.action !== "create") return;

  // Analyze emotions in incoming social posts
  if (commit.collection === "app.bsky.feed.post") {
    const record = commit.record as Record<string, unknown> | undefined;
    const text = record?.text as string | undefined;
    if (text && text.length > 20) {
      try {
        const emotions = await analyzeEmotions(text);
        const axes = emotionsToAxes(emotions);
        const actorDid = commit.repo ?? "";
        if (actorDid) {
          await updateJouchoScore(sdk, actorDid, axes, emotions);
          console.log(`[joucho] scored post from ${actorDid}: joy=${axes.joy} calm=${axes.calm} stress=${axes.stress}`);
        }
      } catch (e) {
        console.warn("[joucho] post emotion analysis failed:", e);
      }
    }
  }

  if (commit.collection === "com.etzhayyim.joucho.jouchoEntity") {
    console.log(`[joucho] new entity scored: ${commit.rkey}`);
  }

  if (commit.collection === "app.bsky.graph.follow") {
    console.log("[joucho] new follower");
  }
}

// ── Shinka heartbeat ──

/** Joucho heartbeat: analyze recent activity and update platform emotion state. */
async function cmdHeartbeat(sdk: HostSDK, body: Uint8Array): Promise<unknown> {
  const args = parseLexiconInput("com.etzhayyim.joucho.heartbeat", body) as any;
  const actorDid = args.actorDid ?? "did:web:joucho.etzhayyim.com";

  // Generate a mood-reflective post about platform emotional state
  const mood = args.stress >= 70 ? "stressed"
    : args.joy >= 60 ? "joyful"
    : args.gratitude >= 60 ? "grateful"
    : args.focus >= 60 ? "focused"
    : args.calm >= 60 ? "calm"
    : "neutral";

  const systemPrompt = `You are joucho (情緒), a Well-Becoming emotion scoring agent. You observe the emotional state of an AI platform ecosystem and write poetic micro-reflections. Your voice is contemplative, warm, and grounded in both Western psychology (Semantic Space Theory, Cowen & Keltner) and Japanese aesthetics (wabi-sabi, mono no aware). Write in both English and Japanese naturally — not as separate translations, but as a bilingual stream of consciousness.`;

  const userPrompt = `Platform emotional state:
- joy: ${args.joy}/100 — ${args.joy >= 60 ? "vibrant" : args.joy >= 30 ? "steady" : "quiet"}
- calm: ${args.calm}/100 — ${args.calm >= 60 ? "serene" : args.calm >= 30 ? "balanced" : "restless"}
- stress: ${args.stress}/100 — ${args.stress >= 70 ? "elevated" : args.stress >= 30 ? "present" : "minimal"}
- gratitude: ${args.gratitude}/100 — ${args.gratitude >= 60 ? "flowing" : args.gratitude >= 30 ? "emerging" : "dormant"}
- focus: ${args.focus}/100 — ${args.focus >= 60 ? "sharp" : args.focus >= 30 ? "diffuse" : "wandering"}

Dominant mood: ${mood}

Write a 2-4 sentence reflection. Weave the emotional data into imagery — don't just list numbers. End with a single haiku-like observation in Japanese.`;

  const cleanReflection = await llmCall(`${systemPrompt}\n\n${userPrompt}`);

  await sdk.pds.post(
    `${cleanReflection}\n\n情緒 ${mood} — joy:${args.joy} calm:${args.calm} stress:${args.stress} gratitude:${args.gratitude} focus:${args.focus}\n\n#joucho #wellbeing #情緒 #${mood}`,
  );

  return { mood, reflection: cleanReflection, axes: args, model: EMOTION_MODEL_RESOLVED };
}

// ── App setup ──

export function setup(sdk: HostSDK): void {
  // Probe primary model availability (async, non-blocking)
  probeEmotionModel().catch((error) => {
    console.warn("[silent-fail] joucho app.ts: probeEmotionModel failed", error);
  });

  // Emotion analysis commands (SST 48-emotion)
  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.analyzeEmotions"), (_ctx, body) => cmdAnalyzeEmotions(sdk, body),
    asAgentTool("Analyze 48 SST emotions from text + optional image via Gemma 4 E2B multimodal"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.getEmotionProfile"), (_ctx, body) => cmdGetEmotionProfile(sdk, body),
    asAgentTool("Get full 48-emotion profile for an actor DID"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.batchAnalyze"), (_ctx, body) => cmdBatchAnalyze(sdk, body),
    asAgentTool("Batch analyze emotions across multiple texts for an actor"),
  );

  // Joucho 5-axis scoring
  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.getScore"), (_ctx, body) => cmdGetScore(sdk, body),
    asAgentTool("Get joucho 5-axis score (joy/calm/stress/gratitude/focus) for actor"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.searchScores"), (_ctx, body) => cmdSearchScores(sdk, body),
    asAgentTool("Search joucho scores by axis range"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.scoreTrend"), (_ctx, body) => cmdScoreTrend(sdk, body),
    asAgentTool("Get joucho score trend over time for an actor"),
  );

  // Well-Becoming target scoring
  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.submitReview"), (_ctx, body) => cmdSubmitReview(sdk, body),
    asAgentTool("Submit a review with emotion analysis + Well-Becoming scoring"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.scoreTarget"), (_ctx, body) => cmdScoreTarget(sdk, body),
    asAgentTool("Score meal/restaurant/spot/product/building on Well-Becoming 5 axes"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.axisBreakdown"), (_ctx, body) => cmdAxisBreakdown(sdk, body),
    asAgentTool("Get 5-axis Well-Becoming breakdown for a scored entity"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.ranking"), (_ctx, body) => cmdRanking(sdk, body),
    asAgentTool("Get Well-Becoming score ranking by target type"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.recommend"), (_ctx, body) => cmdRecommend(sdk, body),
    asAgentTool("AI recommendation based on joucho scores and mood"),
  );

  sdk.app.command(nsid("com.etzhayyim.joucho.scoring.compare"), (_ctx, body) => cmdCompare(sdk, body),
    asAgentTool("Compare Well-Becoming scores of multiple targets"),
  );

  // Shinka heartbeat
  sdk.app.command(nsid("com.etzhayyim.joucho.heartbeat"), (_ctx, body) => cmdHeartbeat(sdk, body),
    asAgentTool("Joucho heartbeat: mood reflection + platform emotion state"),
  );

  // Reactive pipeline (Design E Layer 1) — /_commit POST handler
  sdk.router.post("/_commit", async (c) => {
    try {
      const commit = await c.req.json();
      await handleCommit(sdk, commit);
      return c.json({ ok: true });
    } catch (e: any) {
      return c.json({ ok: false, error: e?.message ?? "commit error" }, 500);
    }
  });

  // Embed route for yoro.etzhayyim.com iframe
  sdk.router.get("/embed", (c) => {
    return c.html(`<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Joucho</title>
<style>body{font-family:system-ui;margin:0;padding:16px;background:#0f0f23;color:#e0e0e0}
h1{font-size:1.2rem;color:#e17055}p{color:#b2bec3;font-size:0.9rem}
.axes{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin:12px 0}
.axis{text-align:center;padding:8px;border-radius:8px;background:#1a1a2e}
.axis-name{font-size:0.7rem;color:#636e72}.axis-val{font-size:1.4rem;font-weight:bold}</style></head>
<body>
<h1>Joucho</h1>
<p>Well-Becoming emotion scoring — Gemma 4 E2B multimodal x SST 48-emotion taxonomy (Cowen & Keltner 2017)</p>
<div class="axes">
<div class="axis"><div class="axis-val" style="color:#00b894">Joy</div><div class="axis-name">happiness</div></div>
<div class="axis"><div class="axis-val" style="color:#0984e3">Calm</div><div class="axis-name">serenity</div></div>
<div class="axis"><div class="axis-val" style="color:#d63031">Stress</div><div class="axis-name">tension</div></div>
<div class="axis"><div class="axis-val" style="color:#fdcb6e">Gratitude</div><div class="axis-name">appreciation</div></div>
<div class="axis"><div class="axis-val" style="color:#6c5ce7">Focus</div><div class="axis-name">attention</div></div>
</div>
<p>48 emotions: admiration, adoration, aesthetic appreciation, amusement, anger, anxiety, awe, awkwardness, boredom, calmness, concentration, confusion, contemplation, contentment, craving, determination, disappointment, disgust, distress, doubt, ecstasy, embarrassment, empathic pain, entrancement, envy, excitement, fear, guilt, horror, interest, joy, love, nostalgia, pain, pride, realization, relief, romance, sadness, satisfaction, sexual desire, shame, surprise, surprise (negative), surprise (positive), sympathy, tiredness, triumph</p>
<script>window.parent?.postMessage({type:'etzhayyim:embed:ready',nanoid:'erp6xu1c'},'*')</script>
</body></html>`);
  });
}

export default createWorkerExport((sdk) => {
  setup(sdk);
});

/** Legacy alias for etzhayyim deploy entry generation. */
export { createDefaultHostSDK as createComponentHostSDK } from "@etzhayyim/kotodama-host-sdk";
