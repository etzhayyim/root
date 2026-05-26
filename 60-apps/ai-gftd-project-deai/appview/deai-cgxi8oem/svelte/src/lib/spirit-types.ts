// Spirit Type taxonomy — Spirit in Physics (Kawasaki et al. 2026)
export type SpiritType = "Hero" | "Sage" | "Lover" | "Caregiver";
export type GhostPattern = "Individual Shadow" | "Collective Meme" | null;

export interface HumeEmotionScores extends Record<string, number> {
  joy: number; sadness: number; anger: number; fear: number;
  disgust: number; calm: number; focus: number;
  surprise: number; confusion: number; awe: number;
}

export interface SpiritProfile {
  cohortDid: string;
  spiritType: SpiritType;
  shadowType?: GhostPattern;
  emotionCentroid: number[]; // 10D permille
  assessedAt: string;
  checkinCount: number;
  resonanceField?: string; // JSON [x,y,z] in tensegrity space
}

export interface MatchRecord {
  cohortDid: string;
  spiritType: SpiritType;
  resonanceScore: number; // 0-1000
  spiritCompatibility: number; // 0-1000
  separationDelta: number; // -1000 to 1000
  compatibilityReason: string;
  matchedAt: string;
  hasConversation: boolean;
}

export const SPIRIT_TYPE_META: Record<SpiritType, { emoji: string; ja: string; desc: string; color: string }> = {
  Hero:      { emoji: "⚔️",  ja: "英雄",   desc: "使命・勇気・保護",  color: "#e74c3c" },
  Sage:      { emoji: "🦉",  ja: "賢者",   desc: "知恵・真実・探求",  color: "#3498db" },
  Lover:     { emoji: "🌸",  ja: "愛人",   desc: "美・感性・つながり", color: "#e91e8c" },
  Caregiver: { emoji: "🌿",  ja: "養育者", desc: "養育・共感・奉仕",  color: "#27ae60" },
};

// Tensegrity compatibility: complementary types form stable bonds
export const COMPATIBILITY: Record<SpiritType, Record<SpiritType, number>> = {
  Hero:      { Hero: 700, Sage: 600, Lover: 800, Caregiver: 950 },
  Sage:      { Hero: 600, Sage: 650, Lover: 950, Caregiver: 700 },
  Lover:     { Hero: 800, Sage: 950, Lover: 600, Caregiver: 700 },
  Caregiver: { Hero: 950, Sage: 700, Lover: 700, Caregiver: 650 },
};

// 10 Hume emotion keys (order matches emotionCentroid array)
export const HUME_EMOTION_KEYS: (keyof HumeEmotionScores)[] = [
  "joy", "sadness", "anger", "fear", "disgust",
  "calm", "focus", "surprise", "confusion", "awe",
];

// Call Hume Expression API (face or voice) client-side
// Raw image/audio MUST NOT be sent to deai server
export async function callHumeFaceApi(imageBlob: Blob, apiKey: string): Promise<HumeEmotionScores> {
  const form = new FormData();
  form.append("file", imageBlob, "frame.jpg");
  const res = await fetch("https://api.hume.ai/v0/batch/jobs", {
    method: "POST",
    headers: { "X-Hume-Api-Key": apiKey },
    body: form,
  });
  if (!res.ok) throw new Error(`Hume API error: ${res.status}`);
  // Parse Hume response into normalized 10D vector (0-1000 permille)
  const data = await res.json();
  return parseHumeResponse(data);
}

function parseHumeResponse(data: unknown): HumeEmotionScores {
  // Hume returns predictions[].models.face.grouped_predictions[].predictions[].emotions[]
  // Each emotion: { name, score } where score ∈ [0,1]
  const emotions: Record<string, number> = {};
  try {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const preds = (data as any)?.predictions?.[0];
    const facePreds = preds?.models?.face?.grouped_predictions?.[0]?.predictions?.[0]?.emotions ?? [];
    for (const e of facePreds as Array<{ name: string; score: number }>) {
      emotions[e.name.toLowerCase()] = Math.round(e.score * 1000);
    }
  } catch {}
  return {
    joy:       emotions["joy"] ?? emotions["happiness"] ?? 0,
    sadness:   emotions["sadness"] ?? 0,
    anger:     emotions["anger"] ?? 0,
    fear:      emotions["fear"] ?? 0,
    disgust:   emotions["disgust"] ?? 0,
    calm:      emotions["calmness"] ?? emotions["calm"] ?? 0,
    focus:     emotions["determination"] ?? emotions["concentration"] ?? 0,
    surprise:  emotions["surprise"] ?? 0,
    confusion: emotions["confusion"] ?? 0,
    awe:       emotions["awe"] ?? 0,
  };
}

// Client-side spirit type classification from word association responses
export function classifySpiritType(
  responses: Array<{ word: string; humeScores: HumeEmotionScores; reactionTimeMs: number }>,
): SpiritType {
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
      const rt = r.reactionTimeMs > 0 ? 1000 / r.reactionTimeMs : 0;
      const e = r.humeScores;
      const score = (
        type === "Hero"      ? e.focus + e.surprise + rt * 0.3 :
        type === "Sage"      ? e.calm + e.awe + rt * 0.2 :
        type === "Lover"     ? e.joy + e.awe + rt * 0.25 :
                               e.calm + e.joy + rt * 0.15
      );
      axisScores[type] += score;
    }
  }
  return (Object.entries(axisScores) as [SpiritType, number][])
    .reduce((a, b) => (b[1] > a[1] ? b : a))[0];
}
