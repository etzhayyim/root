// Spirit-in-Physics Research API client
// SSoT: spirit-in-physics.com/api (Cloudflare Worker + D1 + R2)
// deai は研究データ収集フロントエンド。全データをこのエンドポイントに送信する。

const SIP_BASE = "https://spirit-in-physics.com/api";

async function sipPost<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`${SIP_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`SIP API ${path} ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}

async function sipGet<T>(path: string, params?: Record<string, string>): Promise<T> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  const res = await fetch(`${SIP_BASE}${path}${qs}`);
  if (!res.ok) throw new Error(`SIP API ${path} ${res.status}`);
  return res.json() as Promise<T>;
}

// ── Participant ──────────────────────────────────────────────

export interface SipParticipant {
  id: string;
  email?: string;
  ageGroup?: string;
  gender?: string;
  ethnicity?: string;
  incomeRange?: string;
  medicalHistory?: string[];
  isPublic?: boolean;
}

export const sipApi = {
  /** Register or update participant (upsert by ID). ID = deai cohort hash (anonymized). */
  registerParticipant: (p: SipParticipant) =>
    sipPost<{ id: string; created: boolean }>("/participants", {
      id: p.id,
      email: p.email ?? "",
      ageGroup: p.ageGroup ?? "",
      gender: p.gender ?? "",
      ethnicity: p.ethnicity ?? "",
      incomeRange: p.incomeRange ?? "",
      medicalHistory: p.medicalHistory ?? [],
      isPublic: p.isPublic ?? false, // デフォルト非公開
    }),

  getParticipantByEmail: (email: string) =>
    sipGet<{ participant: SipParticipant | null }>("/participants/by-email", { email }),

  // ── Assessment workflow ──────────────────────────────────

  /** Start assessment workflow for participant. Returns workflowId. */
  startAssessment: (participantId: string) =>
    sipPost<{ workflowId: string; runId: string; eventId: string }>("/assessments/start", {
      participantId,
      eventId: crypto.randomUUID(),
    }),

  /** Start a new session (sub-batch of stimulus words). */
  startSession: (participantId: string, sessionIndex: number) =>
    sipPost<{ success: boolean; runId: string; eventId: string }>("/assessments/session-start", {
      participantId,
      session: sessionIndex,
      eventId: crypto.randomUUID(),
    }),

  /** Submit one word association response with reaction time and Hume emotion scores. */
  submitWordResponse: (params: {
    participantId: string;
    session: number;
    stimulusWordId: number;   // 1-100 (Jung stimulus word ID)
    responseWord?: string;    // user's association word (spoken/typed)
    reactionTimeMs: number;
    humeScores?: Record<string, number>; // emotion scores to attach as artifact
  }) =>
    sipPost<{ success: boolean; runId: string; eventId: string }>("/assessments/word-response", {
      participantId: params.participantId,
      session: params.session,
      stimulusWordId: params.stimulusWordId,
      responseWord: params.responseWord ?? "",
      reactionTimeMs: params.reactionTimeMs,
      eventId: crypto.randomUUID(),
    }),

  /** Upload Hume emotion snapshot as artifact (JSON blob). */
  uploadArtifact: (params: {
    participantId: string;
    session: number;
    artifactType: "hume-face" | "hume-voice" | "hume-text" | "physiological" | "recording-ref";
    payload: unknown;
  }) =>
    sipPost<{ success: boolean; runId: string; eventId: string }>("/assessments/artifact", {
      participantId: params.participantId,
      session: params.session,
      artifactType: params.artifactType,
      payload: params.payload,
      eventId: crypto.randomUUID(),
    }),

  /** Mark session complete. Triggers Spirit Type classification on server. */
  completeSession: (participantId: string, session: number) =>
    sipPost<{ success: boolean; runId: string; eventId: string }>("/assessments/complete", {
      participantId,
      session,
      eventId: crypto.randomUUID(),
    }),

  // ── Research data retrieval ──────────────────────────────

  /** Get all stimulus words (100 Jung words). */
  getStimulusWords: () =>
    sipGet<{ words: Array<{ id: number; japanese: string; english: string; pronunciation: string }> }>(
      "/stimulus-words",
    ),

  /** Get integrated timeline analysis for a participant. */
  getTimeline: (participantId: string, sessionId?: string) =>
    sipGet<{ points: unknown[]; analysis: unknown }>(
      "/timeline/integrated",
      { participantId, ...(sessionId ? { sessionId } : {}) },
    ),

  /** Get emotion vectors for visualization. */
  getEmotionVectors: (participantId: string) =>
    sipGet<{ vectors: unknown[] }>("/timeline/emotion-vectors", { participantId }),

  /** Get word statistics (reaction time distribution per word). */
  getWordStatistics: (participantId: string) =>
    sipGet<{ statistics: unknown[] }>("/timeline/word-statistics", { participantId }),
};

// ── Stimulus words (cached from SIP API or fallback) ────────

// Jung's Word Association Experiment — 100語（日本語適応版）
// Source: com-junkawasaki/spirit-in-physics/apps/api-worker/src/stimulus-words.ts
export const JUNG_STIMULUS_WORDS = [
  { id: 1,  japanese: "頭",         english: "head",           pronunciation: "あたま" },
  { id: 2,  japanese: "緑",         english: "green",          pronunciation: "みどり" },
  { id: 3,  japanese: "水",         english: "water",          pronunciation: "みず" },
  { id: 4,  japanese: "歌う",       english: "to sing",        pronunciation: "うたう" },
  { id: 5,  japanese: "亡くなる",   english: "death",          pronunciation: "なくなる" },
  { id: 6,  japanese: "長い",       english: "long",           pronunciation: "ながい" },
  { id: 7,  japanese: "船",         english: "ship",           pronunciation: "ふね" },
  { id: 8,  japanese: "支払い",     english: "to pay",         pronunciation: "しはらい" },
  { id: 9,  japanese: "窓",         english: "window",         pronunciation: "まど" },
  { id: 10, japanese: "親切な",     english: "friendly",       pronunciation: "しんせつ" },
  { id: 11, japanese: "机",         english: "table",          pronunciation: "つくえ" },
  { id: 12, japanese: "聞く",       english: "to ask",         pronunciation: "きく" },
  { id: 13, japanese: "村",         english: "village",        pronunciation: "むら" },
  { id: 14, japanese: "冷たい",     english: "cold",           pronunciation: "つめたい" },
  { id: 15, japanese: "茎",         english: "stem",           pronunciation: "くき" },
  { id: 16, japanese: "踊る",       english: "to dance",       pronunciation: "おどる" },
  { id: 17, japanese: "海",         english: "lake",           pronunciation: "うみ" },
  { id: 18, japanese: "病気",       english: "sick",           pronunciation: "びょうき" },
  { id: 19, japanese: "プライド",   english: "pride",          pronunciation: "プライド" },
  { id: 20, japanese: "料理",       english: "to cook",        pronunciation: "りょうり" },
  { id: 21, japanese: "インク",     english: "ink",            pronunciation: "インク" },
  { id: 22, japanese: "怒り",       english: "angry",          pronunciation: "いかり" },
  { id: 23, japanese: "針",         english: "needle",         pronunciation: "はり" },
  { id: 24, japanese: "泳ぐ",       english: "to swim",        pronunciation: "およぐ" },
  { id: 25, japanese: "旅行",       english: "journey",        pronunciation: "りょこう" },
  { id: 26, japanese: "青い",       english: "blue",           pronunciation: "あおい" },
  { id: 27, japanese: "電気",       english: "lamp",           pronunciation: "でんき" },
  { id: 28, japanese: "罪",         english: "to sin",         pronunciation: "つみ" },
  { id: 29, japanese: "ご飯",       english: "bread",          pronunciation: "ごはん" },
  { id: 30, japanese: "金持ち",     english: "rich",           pronunciation: "かねもち" },
  { id: 31, japanese: "木",         english: "tree",           pronunciation: "き" },
  { id: 32, japanese: "刺す",       english: "to prick",       pronunciation: "さす" },
  { id: 33, japanese: "同情",       english: "pity",           pronunciation: "どうじょう" },
  { id: 34, japanese: "黄色",       english: "yellow",         pronunciation: "きいろ" },
  { id: 35, japanese: "山",         english: "mountain",       pronunciation: "やま" },
  { id: 36, japanese: "死ぬ",       english: "to die",         pronunciation: "しぬ" },
  { id: 37, japanese: "塩",         english: "salt",           pronunciation: "しお" },
  { id: 38, japanese: "新しい",     english: "new",            pronunciation: "あたらしい" },
  { id: 39, japanese: "癖",         english: "custom",         pronunciation: "くせ" },
  { id: 40, japanese: "祈る",       english: "to pray",        pronunciation: "いのる" },
  { id: 41, japanese: "お金",       english: "money",          pronunciation: "おかね" },
  { id: 42, japanese: "馬鹿",       english: "stupid",         pronunciation: "ばか" },
  { id: 43, japanese: "ノート",     english: "exercise-book",  pronunciation: "ノート" },
  { id: 44, japanese: "軽蔑",       english: "to despise",     pronunciation: "けいべつ" },
  { id: 45, japanese: "指",         english: "finger",         pronunciation: "ゆび" },
  { id: 46, japanese: "高価な",     english: "dear",           pronunciation: "こうかな" },
  { id: 47, japanese: "鳥",         english: "bird",           pronunciation: "とり" },
  { id: 48, japanese: "落ちる",     english: "to fall",        pronunciation: "おちる" },
  { id: 49, japanese: "本",         english: "book",           pronunciation: "ほん" },
  { id: 50, japanese: "不正",       english: "unjust",         pronunciation: "ふせい" },
  { id: 51, japanese: "蛙",         english: "frog",           pronunciation: "かえる" },
  { id: 52, japanese: "別れる",     english: "to part",        pronunciation: "わかれる" },
  { id: 53, japanese: "空腹",       english: "hunger",         pronunciation: "くうふく" },
  { id: 54, japanese: "白い",       english: "white",          pronunciation: "しろい" },
  { id: 55, japanese: "子供",       english: "child",          pronunciation: "こども" },
  { id: 56, japanese: "注意",       english: "to pay attention", pronunciation: "ちゅうい" },
  { id: 57, japanese: "鉛筆",       english: "pencil",         pronunciation: "えんぴつ" },
  { id: 58, japanese: "悲しい",     english: "sad",            pronunciation: "かなしい" },
  { id: 59, japanese: "りんご",     english: "plum",           pronunciation: "りんご" },
  { id: 60, japanese: "結婚",       english: "to marry",       pronunciation: "けっこん" },
  { id: 61, japanese: "家",         english: "house",          pronunciation: "いえ" },
  { id: 62, japanese: "かわいい",   english: "darling",        pronunciation: "かわいい" },
  { id: 63, japanese: "ガラス",     english: "glass",          pronunciation: "ガラス" },
  { id: 64, japanese: "争う",       english: "to quarrel",     pronunciation: "あらそう" },
  { id: 65, japanese: "毛皮",       english: "fur",            pronunciation: "けがわ" },
  { id: 66, japanese: "大きい",     english: "big",            pronunciation: "おおきい" },
  { id: 67, japanese: "人参",       english: "carrot",         pronunciation: "にんじん" },
  { id: 68, japanese: "塗る",       english: "to paint",       pronunciation: "ぬる" },
  { id: 69, japanese: "部分",       english: "part",           pronunciation: "ぶぶん" },
  { id: 70, japanese: "古い",       english: "old",            pronunciation: "ふるい" },
  { id: 71, japanese: "花",         english: "flower",         pronunciation: "はな" },
  { id: 72, japanese: "打つ",       english: "to beat",        pronunciation: "うつ" },
  { id: 73, japanese: "箱",         english: "box",            pronunciation: "はこ" },
  { id: 74, japanese: "荒い",       english: "wild",           pronunciation: "あらい" },
  { id: 75, japanese: "家族",       english: "family",         pronunciation: "かぞく" },
  { id: 76, japanese: "洗う",       english: "to wash",        pronunciation: "あらう" },
  { id: 77, japanese: "牛",         english: "cow",            pronunciation: "うし" },
  { id: 78, japanese: "変",         english: "strange",        pronunciation: "へん" },
  { id: 79, japanese: "幸運",       english: "happiness",      pronunciation: "こううん" },
  { id: 80, japanese: "嘘",         english: "lie",            pronunciation: "うそ" },
  { id: 81, japanese: "礼儀",       english: "deportment",     pronunciation: "れいぎ" },
  { id: 82, japanese: "狭い",       english: "narrow",         pronunciation: "せまい" },
  { id: 83, japanese: "兄弟",       english: "brother",        pronunciation: "きょうだい" },
  { id: 84, japanese: "怖がる",     english: "to fear",        pronunciation: "こわがる" },
  { id: 85, japanese: "コウノトリ", english: "stork",          pronunciation: "こうのとり" },
  { id: 86, japanese: "間違い",     english: "false",          pronunciation: "まちがい" },
  { id: 87, japanese: "心配",       english: "anxiety",        pronunciation: "しんぱい" },
  { id: 88, japanese: "キス",       english: "to kiss",        pronunciation: "キス" },
  { id: 89, japanese: "花嫁",       english: "bride",          pronunciation: "はなよめ" },
  { id: 90, japanese: "純粋な",     english: "pure",           pronunciation: "じゅんすいな" },
  { id: 91, japanese: "ドア",       english: "door",           pronunciation: "ドア" },
  { id: 92, japanese: "選ぶ",       english: "to choose",      pronunciation: "えらぶ" },
  { id: 93, japanese: "干し草",     english: "hay",            pronunciation: "ほしくさ" },
  { id: 94, japanese: "嬉しい",     english: "contented",      pronunciation: "うれしい" },
  { id: 95, japanese: "虐める",     english: "ridicule",       pronunciation: "いじめる" },
  { id: 96, japanese: "眠る",       english: "to sleep",       pronunciation: "ねむる" },
  { id: 97, japanese: "年月",       english: "month",          pronunciation: "ねんげつ" },
  { id: 98, japanese: "きれいな",   english: "nice",           pronunciation: "きれいな" },
  { id: 99, japanese: "女",         english: "woman",          pronunciation: "おんな" },
  { id: 100, japanese: "侮辱",      english: "to abuse",       pronunciation: "ぶじょく" },
] as const;

export type StimulusWord = (typeof JUNG_STIMULUS_WORDS)[number];
