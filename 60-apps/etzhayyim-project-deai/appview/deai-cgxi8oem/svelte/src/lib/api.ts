// deai API client — calls decom.etzhayyim.ai XRPC endpoints
const BASE = "https://decom.etzhayyim.ai/xrpc";

async function post<T>(nsid: string, body: unknown, headers?: Record<string, string>): Promise<T> {
  const res = await fetch(`${BASE}/${nsid}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...headers },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${nsid} ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

async function get<T>(nsid: string, params?: Record<string, string>, headers?: Record<string, string>): Promise<T> {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  const res = await fetch(`${BASE}/${nsid}${qs}`, { headers });
  if (!res.ok) throw new Error(`${nsid} ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const deaiApi = {
  startAssessment: (locale?: string) =>
    post<{ sessionId: string; stimulusWords: string[]; expiresAt: string }>(
      "com.etzhayyim.apps.deai.startAssessment",
      { locale: locale ?? "ja" },
    ),

  submitResponse: (body: {
    sessionId: string; word: string; responseWord?: string;
    reactionTimeMs: number; humeScores: Record<string, number>; spDelta?: number;
  }) => post<{ accepted: boolean; progress: number }>("com.etzhayyim.apps.deai.submitResponse", body),

  getProfile: (did: string) =>
    get<{
      cohortDid: string; spiritType: string; emotionCentroid: number[];
      assessedAt: string; checkinCount: number;
    }>("com.etzhayyim.apps.deai.getProfile", { did }),

  listMatches: (did: string, limit?: number) =>
    get<{ matches: unknown[] }>("com.etzhayyim.apps.deai.listMatches", { did, limit: String(limit ?? 20) }),

  createCheckin: (
    body: { humeScores: Record<string, number>; modality: string; note?: string },
    actorDid: string,
  ) => post<{ checkinId: string; updatedSpiritType: string; spiritDelta: number; nextCheckinAfter: string }>(
    "com.etzhayyim.apps.deai.createCheckin", body, { "x-actor-did": actorDid },
  ),

  sendMessage: (
    body: { toCohortDid: string; ciphertext: string; iv: string; replyToId?: string },
    actorDid: string,
  ) => post<{ messageId: string; sentAt: string }>(
    "com.etzhayyim.apps.deai.sendMessage", body, { "x-actor-did": actorDid },
  ),

  listMessages: (withCohortDid: string, actorDid: string, limit?: number) =>
    get<{ messages: unknown[] }>(
      "com.etzhayyim.apps.deai.listMessages",
      { withCohortDid, limit: String(limit ?? 50) },
      { "x-actor-did": actorDid },
    ),
};
