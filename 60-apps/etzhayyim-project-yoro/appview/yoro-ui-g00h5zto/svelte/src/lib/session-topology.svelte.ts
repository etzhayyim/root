/**
 * Session topology tracker — lightweight client-side TDA-analogue.
 *
 * Maintains a bounded ring buffer of topic bucket keys the viewer has
 * interacted with during the current session (post tap, scroll dwell,
 * reaction, search). Computes:
 *   - `echoPersistence` = 1 - (distinct / total)      (H1 loop proxy)
 *   - `distinctTopics`  = |set(buffer)|               (b0 analogue)
 *   - `dwellMs`         = now - sessionStart
 *
 * Privacy: the raw topic history **never leaves the browser**. Only the
 * three aggregated scalars are sent to `getRankedFeed`. See ADR-0018
 * PII Tier 3 — these three values are cohort-level and non-identifying.
 *
 * Plan: /root/.claude/plans/yoro-etzhayyim-ai-facebook-zazzy-teapot.md
 */

const BUFFER_SIZE = 50;
const STORAGE_KEY = "yoro-session-topology-v1";

interface Persisted {
  sessionStart: number;     // ms epoch
  topics: string[];         // ring buffer (most-recent last)
}

function loadPersisted(): Persisted {
  if (typeof sessionStorage === "undefined") return { sessionStart: Date.now(), topics: [] };
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return { sessionStart: Date.now(), topics: [] };
    const parsed = JSON.parse(raw) as Partial<Persisted>;
    const sessionStart = typeof parsed.sessionStart === "number" ? parsed.sessionStart : Date.now();
    const topics = Array.isArray(parsed.topics) ? parsed.topics.filter((t): t is string => typeof t === "string").slice(-BUFFER_SIZE) : [];
    return { sessionStart, topics };
  } catch {
    return { sessionStart: Date.now(), topics: [] };
  }
}

function savePersisted(state: Persisted): void {
  if (typeof sessionStorage === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  } catch {
    /* quota exceeded — drop silently */
  }
}

let _state: Persisted = loadPersisted();

/** Record a topic visit. Called from feed-card tap / scroll detent. */
export function recordTopicVisit(topic: string | null | undefined): void {
  if (!topic) return;
  const t = String(topic).slice(0, 64);
  _state.topics.push(t);
  if (_state.topics.length > BUFFER_SIZE) {
    _state.topics.splice(0, _state.topics.length - BUFFER_SIZE);
  }
  savePersisted(_state);
}

/** Clear the session buffer (on explicit feed-pause resume). */
export function resetSessionTopology(): void {
  _state = { sessionStart: Date.now(), topics: [] };
  savePersisted(_state);
}

export interface SessionTopologySnapshot {
  echoPersistence: number;     // 0..1
  distinctTopics: number;
  dwellMs: number;
  sampleSize: number;          // debug / diagnostic only
}

/**
 * Compute the current session signature. Safe to call arbitrarily often
 * (O(N) over BUFFER_SIZE, so ~50 string ops).
 */
export function getSessionTopology(): SessionTopologySnapshot {
  const topics = _state.topics;
  const total = topics.length;
  const distinct = new Set(topics).size;
  const echoPersistence = total === 0 ? 0 : 1 - distinct / total;
  return {
    echoPersistence,
    distinctTopics: distinct,
    dwellMs: Math.max(0, Date.now() - _state.sessionStart),
    sampleSize: total,
  };
}

/**
 * Returns true when the viewer has crossed the doom-scroll threshold.
 * Mirrors the server-side `deriveGuardrails.doomScroll` logic so the UI
 * can surface a pause modal even when offline.
 */
export function isDoomScrolling(opts: {
  nightMode?: boolean;
  stressIdx?: number;
} = {}): boolean {
  const { nightMode = false, stressIdx = 0 } = opts;
  const limit = nightMode ? 20 * 60 * 1000 : 45 * 60 * 1000;
  const snap = getSessionTopology();
  return snap.dwellMs > limit && (stressIdx > 70 || nightMode);
}

/** Testing hook — do not use from production code. */
export const _testing = {
  load: loadPersisted,
  reset: resetSessionTopology,
  get state(): Persisted { return _state; },
  setState(s: Persisted): void { _state = s; savePersisted(s); },
};
