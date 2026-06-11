/**
 * kotoba-grounded conversation for browser-local gemma4-e4b (ameno).
 *
 * Makes the in-browser conversation proceed ON A KOTOBA BASIS: instead of the
 * LLM answering from parametric memory, it answers from etzhayyim's published
 * kotoba government-procedure records (`/.well-known/gov-procedures.json`, the
 * apex Worker surface compiled from the ooyake `:gov.procedure` Datom data).
 *
 * Flow (all client-side, zero egress beyond the public JSON fetch):
 *   1. fetchGovProcedures(baseUrl)  — load the published kotoba records once.
 *   2. retrieveProcedures(query, …) — pure lexical retrieval (CJK-aware), no GPU.
 *   3. groundedMessages(query, hits) — build the ChatMessage[] (a grounded
 *      system prompt + the user turn) to hand to inference.generate().
 *
 * Charter posture (mirror, ADR-2606021600 / 2606042330): the grounding prompt
 * forbids the model from claiming to BE the government, to be an official
 * channel, or to file on the member's behalf (that is toritsugi, gated). It must
 * answer only from the supplied records and cite each record's provenance; if no
 * record covers the question it must say so rather than invent a procedure. All
 * records are :representative / :unverified-seed — the prompt says so.
 *
 * Murakumo-only invariant (ADR-2605215000): inference itself is the browser edge
 * carve-out (gemma4-e4b via ameno, ADR-2605241900) — this module only shapes the
 * prompt; it never calls a server LLM.
 */

/** One published kotoba government-procedure record (gov-procedures.json shape). */
export interface KotobaProcedure {
  id: string;
  title: string;
  titleLocal?: string;
  ownerUnit: string;
  ownerHandle: string;
  jurisdiction: string;
  authority?: string;
  channel?: readonly string[];
  requiredDocs?: readonly string[];
  legalBasis?: string;
  toritsugiRef?: string;
  provenance?: string;
  sourcing?: string;
  verificationStatus?: string;
}

/** Minimal chat-message shape (matches inference.ChatMessage). */
export interface GroundChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
}

/** A retrieved record plus its lexical score. */
export interface RetrievedProcedure {
  procedure: KotobaProcedure;
  score: number;
}

const DEFAULT_INDEX_PATH = "/.well-known/gov-procedures.json";

/**
 * Fetch the published kotoba procedure index from the apex Worker.
 * `baseUrl` defaults to the current origin in a browser; pass an explicit
 * origin (e.g. "https://etzhayyim.com") in non-browser contexts.
 */
export async function fetchGovProcedures(
  baseUrl?: string,
  fetchImpl: typeof fetch = fetch,
): Promise<KotobaProcedure[]> {
  const origin =
    baseUrl ??
    (typeof location !== "undefined" ? location.origin : "https://etzhayyim.com");
  const res = await fetchImpl(`${origin}${DEFAULT_INDEX_PATH}`);
  if (!res.ok) throw new Error(`gov-procedures fetch failed: ${res.status}`);
  const body = (await res.json()) as { procedures?: KotobaProcedure[] };
  return Array.isArray(body.procedures) ? body.procedures : [];
}

/**
 * Tokenise a query for lexical retrieval. Lowercased word tokens PLUS CJK
 * character bigrams (so "運転免許" matches "運転免許 取得" without a segmenter),
 * matching the kotoba ingest BM25 CJK-aware tokenizer in spirit.
 */
export function tokenize(text: string): string[] {
  const lower = (text || "").toLowerCase();
  const words = lower.match(/[a-z0-9]+/g) ?? [];
  const cjk = lower.match(/[぀-ヿ㐀-鿿豈-﫿]/g) ?? [];
  const bigrams: string[] = [];
  for (let i = 0; i < cjk.length - 1; i++) bigrams.push(cjk[i] + cjk[i + 1]);
  // single CJK chars too (so a 1-char query still matches)
  return [...words, ...cjk, ...bigrams];
}

function procedureHaystack(p: KotobaProcedure): string {
  return [
    p.title,
    p.titleLocal,
    p.authority,
    p.jurisdiction,
    p.ownerHandle,
    p.legalBasis,
    ...(p.requiredDocs ?? []),
  ]
    .filter(Boolean)
    .join(" ");
}

/**
 * Pure lexical retrieval over the published records. Scores each procedure by
 * overlap of query tokens with its searchable text (title weighted highest),
 * returns the top-k by score (ties broken by id for determinism). No network,
 * no GPU — deterministic and unit-testable.
 */
export function retrieveProcedures(
  query: string,
  procedures: readonly KotobaProcedure[],
  k = 5,
): RetrievedProcedure[] {
  const qTokens = new Set(tokenize(query));
  if (qTokens.size === 0) return [];
  const scored: RetrievedProcedure[] = [];
  for (const p of procedures) {
    const titleTokens = new Set(tokenize(`${p.title} ${p.titleLocal ?? ""}`));
    const bodyTokens = new Set(tokenize(procedureHaystack(p)));
    let score = 0;
    for (const t of qTokens) {
      if (titleTokens.has(t)) score += 3;
      else if (bodyTokens.has(t)) score += 1;
    }
    if (score > 0) scored.push({ procedure: p, score });
  }
  scored.sort((a, b) =>
    b.score - a.score || a.procedure.id.localeCompare(b.procedure.id),
  );
  return scored.slice(0, k);
}

/** Render one record as a compact, citation-bearing context block. */
function renderProcedure(p: KotobaProcedure): string {
  const lines = [
    `- ${p.title}${p.titleLocal && p.titleLocal !== p.title ? ` (${p.titleLocal})` : ""}`,
    `  jurisdiction: ${p.jurisdiction}; authority: ${p.authority || "(see provenance)"}`,
  ];
  if (p.channel?.length) lines.push(`  channel: ${p.channel.join(", ")}`);
  if (p.requiredDocs?.length)
    lines.push(`  documents: ${p.requiredDocs.join("; ")}`);
  if (p.legalBasis) lines.push(`  legal basis: ${p.legalBasis}`);
  if (p.provenance) lines.push(`  source: ${p.provenance}`);
  lines.push(
    `  status: ${p.sourcing || "representative"} / ${p.verificationStatus || "unverified-seed"} (unverified — confirm at source)`,
  );
  return lines.join("\n");
}

const GROUND_PREAMBLE =
  "You are etzhayyim's civic wayfinding assistant. Answer the user's question " +
  "about government administrative procedures USING ONLY the kotoba records " +
  "below. Cite the `source:` URL for any procedure you describe. If the records " +
  "do not cover the question, say so plainly and suggest checking the official " +
  "source — do NOT invent a procedure, fee, or legal citation. The records are a " +
  "MIRROR catalog (where/how a public procedure is done): you are NOT the " +
  "government, NOT an official channel, and you must NEVER offer to file, submit, " +
  "or act on the user's behalf (that is the gated 'toritsugi' service). The " +
  "records are :representative / :unverified-seed — remind the user to confirm at " +
  "the official source before acting.";

/**
 * Build the grounded context string from retrieved records (the kotoba basis).
 * Returned separately so a caller can inject it into an existing system prompt
 * (e.g. inference.generate's ragContext path) if preferred.
 */
export function buildKotobaContext(hits: readonly RetrievedProcedure[]): string {
  if (hits.length === 0) {
    return `${GROUND_PREAMBLE}\n\n[kotoba records]\n(none matched this question)`;
  }
  return `${GROUND_PREAMBLE}\n\n[kotoba records]\n${hits
    .map((h) => renderProcedure(h.procedure))
    .join("\n")}`;
}

/**
 * Produce the full ChatMessage[] for a kotoba-grounded turn: a grounded system
 * message (preamble + retrieved records) followed by the user's question. Hand
 * the result straight to inference.generate(messages, onToken).
 */
export function groundedMessages(
  query: string,
  procedures: readonly KotobaProcedure[],
  k = 5,
): GroundChatMessage[] {
  const hits = retrieveProcedures(query, procedures, k);
  return [
    { role: "system", content: buildKotobaContext(hits) },
    { role: "user", content: query },
  ];
}
