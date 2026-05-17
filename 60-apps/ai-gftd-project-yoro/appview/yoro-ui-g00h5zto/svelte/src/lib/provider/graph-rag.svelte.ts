/**
 * graph-rag.svelte.ts — GraphRAG: XRPC-backed context retrieval + Local LLM inference.
 *
 * Design: Domain-aware lazy loading + federated XRPC query.
 *
 * Flow: user message → Gemma 4 E2B classify labels → lazy-load needed labels
 *       → local cache query → if insufficient, federated PDS query → merge
 *       → context injection → local LLM grounded response
 */

import * as kagamiStore from '$lib/graph/kagami-store.svelte.js';
import { useLocalLLM, type ChatMessage } from './local-llm.svelte.js';
import { useAmeno } from './ameno.svelte.js';

/** Maximum graph context tokens to inject (approximate by characters). */
const MAX_CONTEXT_CHARS = 3000;
/** Maximum rows to retrieve per query. */
const MAX_CONTEXT_ROWS = 30;
/** Target context window for browser-local inference. */
const TARGET_CONTEXT_TOKENS = 4096;
/** Keep chat history below this token budget (excluding system/context prompt). */
const HISTORY_BUDGET_TOKENS = 2200;
/** Stage-down plan for output tokens. */
const TOKEN_FALLBACK_CHAIN = [2048, 1024, 512, 256] as const;
/** Large -> small model downgrade order on OOM. */
const MODEL_FALLBACK_ORDER = ['qwen3.5-4b', 'gemma4-e2b', 'qwen3.5-2b', 'qwen3.5-0.8b'] as const;

// ── Label classification ──

/**
 * Domain label mapping: keyword → likely graph labels.
 *
 * Used for fast classification without LLM. Gemma 4 E2B refines when ready.
 */
const DOMAIN_LABEL_MAP: Record<string, string[]> = {
  // Technology / Industry
  '半導体': ['Article', 'CohortCompany', 'Post'],
  'semiconductor': ['Article', 'CohortCompany', 'Post'],
  'handotai': ['Article', 'CohortCompany'],
  'ai': ['Article', 'Post', 'CohortCompany'],
  // Legal / Government
  '法律': ['Statute', 'Profile', 'Post'],
  '判例': ['CaseDecision', 'Post'],
  '法人': ['LegalEntity', 'Profile'],
  '破産': ['BankruptcyCase', 'Post'],
  // Financial
  'isin': ['SecurityIdentifier', 'Profile'],
  '証券': ['SecurityIdentifier', 'Post'],
  '株': ['SecurityIdentifier', 'CohortCompany'],
  // Geography
  '土地': ['LandRegistry', 'Profile'],
  '地図': ['SpatialEntity', 'Profile'],
  // Workforce
  '職業': ['OccupationUnit', 'Profile'],
  'isco': ['OccupationUnit', 'Profile'],
  // Product
  '製品': ['ProductIdentifier', 'Post'],
  'gtin': ['ProductIdentifier'],
  'isbn': ['BookIdentifier'],
  // People / Actors
  'エージェント': ['Profile', 'App'],
  'agent': ['Profile', 'App'],
  'プロフィール': ['Profile'],
  // News / Content
  'ニュース': ['Article', 'Post'],
  'news': ['Article', 'Post'],
  '記事': ['Article', 'Post'],
};

/** Core labels always checked first (already loaded by feed). */
const CORE_LABELS = ['Post', 'Profile'];

function estimateTokens(text: string): number {
  return Math.ceil((text?.length ?? 0) / 4);
}

function truncateText(text: string, maxChars: number): string {
  if (!text || text.length <= maxChars) return text;
  return `${text.slice(0, maxChars)}…`;
}

function compressChatHistory(chatHistory: ChatMessage[]): ChatMessage[] {
  const kept: ChatMessage[] = [];
  const omitted: string[] = [];
  let omittedCount = 0;
  let used = 0;

  for (let i = chatHistory.length - 1; i >= 0; i--) {
    const msg = chatHistory[i];
    const compact = truncateText(msg.content, 800);
    const tokens = estimateTokens(compact);
    if (used + tokens > HISTORY_BUDGET_TOKENS) {
      omittedCount++;
      if (omitted.length < 6) {
        const tag = msg.role === 'user' ? 'U' : msg.role === 'assistant' ? 'A' : 'S';
        omitted.push(`${tag}: ${truncateText(msg.content.replace(/\s+/g, ' '), 90)}`);
      }
      continue;
    }
    used += tokens;
    kept.push({ role: msg.role, content: compact });
  }

  kept.reverse();
  if (omittedCount > 0) {
    const summary = `Previous conversation compressed (${omittedCount} messages):\n${omitted.reverse().join('\n')}`;
    return [{ role: 'system', content: summary }, ...kept];
  }
  return kept;
}

function tokenPlanForMessages(messages: ChatMessage[]): number[] {
  const promptTokens = messages.reduce((sum, m) => sum + estimateTokens(m.content), 0);
  const remaining = Math.max(256, TARGET_CONTEXT_TOKENS - promptTokens - 256);
  const dynamicCap = remaining >= 2048 ? 2048 : remaining >= 1024 ? 1024 : remaining >= 512 ? 512 : 256;
  return [...new Set([dynamicCap, ...TOKEN_FALLBACK_CHAIN])];
}

function isOomLikeError(msg: string | null | undefined): boolean {
  const s = (msg ?? '').toLowerCase();
  return s.includes('out of memory')
    || s.includes('oom')
    || s.includes('gpu device lost')
    || s.includes('device lost')
    || s.includes('allocation failed')
    || s.includes('insufficient memory');
}

function nextFallbackModel(currentModelId: string | null): string | null {
  const current = currentModelId ?? 'gemma4-e2b';
  const idx = MODEL_FALLBACK_ORDER.indexOf(current as (typeof MODEL_FALLBACK_ORDER)[number]);
  if (idx === -1) return MODEL_FALLBACK_ORDER[MODEL_FALLBACK_ORDER.length - 1];
  if (idx >= MODEL_FALLBACK_ORDER.length - 1) return null;
  return MODEL_FALLBACK_ORDER[idx + 1];
}

async function downgradeModelOnOom(localLLM: ReturnType<typeof useLocalLLM>): Promise<boolean> {
  const next = nextFallbackModel(localLLM.activeModelId);
  if (!next) return false;
  try {
    await localLLM.reset();
    await localLLM.init(next);
    try { localStorage.setItem('yoro-local-llm-model', next); } catch { /* ignore */ }
    return localLLM.isReady;
  } catch (e) {
    console.warn('[graph-rag] model downgrade failed:', e);
    return false;
  }
}

async function chatCompletionResilient(
  localLLM: ReturnType<typeof useLocalLLM>,
  messages: ChatMessage[],
): Promise<string | null> {
  const plan = tokenPlanForMessages(messages);
  for (const maxTokens of plan) {
    const reply = await localLLM.chatCompletion(messages, { maxTokens, temperature: 0.6 });
    if (reply) return reply;
    if (isOomLikeError(localLLM.lastInferenceError)) {
      const downgraded = await downgradeModelOnOom(localLLM);
      if (!downgraded) break;
    }
  }
  return null;
}

/**
 * Classify user query into relevant graph labels.
 *
 * Fast path: keyword matching against DOMAIN_LABEL_MAP.
 * Enhanced path: Gemma 4 E2B classification (when LLM is ready).
 */
async function classifyLabels(
  userMessage: string,
  localLLM: ReturnType<typeof useLocalLLM>,
): Promise<string[]> {
  const labels = new Set<string>(CORE_LABELS);
  const msgLower = userMessage.toLowerCase();

  // Fast path: keyword-based classification
  for (const [keyword, labelList] of Object.entries(DOMAIN_LABEL_MAP)) {
    if (msgLower.includes(keyword.toLowerCase())) {
      for (const l of labelList) labels.add(l);
    }
  }

  // Enhanced path: LLM classification (non-blocking, best-effort)
  if (localLLM.isReady && labels.size <= CORE_LABELS.length + 1) {
    try {
      const availableLabels = await kagamiStore.listAvailableLabels();
      if (availableLabels.length > 0) {
        const labelNames = availableLabels.map(l => l.label).join(', ');
        const classifyResult = await localLLM.chatCompletion([
          { role: 'system', content: `You are a label classifier. Given a user query and available graph labels, return ONLY a JSON array of the most relevant label names (max 5). No explanation.\nAvailable labels: ${labelNames}` },
          { role: 'user', content: userMessage },
        ], { maxTokens: 100, temperature: 0 });

        if (classifyResult) {
          try {
            const match = classifyResult.match(/\[[\s\S]*?\]/);
            if (match) {
              const parsed = JSON.parse(match[0]) as string[];
              for (const l of parsed) {
                if (typeof l === 'string' && l.length > 0) labels.add(l);
              }
            }
          } catch { /* parse failed, use keyword results */ }
        }
      }
    } catch { /* LLM classify failed, use keyword results */ }
  }

  return Array.from(labels);
}

// ── Keyword extraction ──

const STOPWORDS = new Set([
  'の', 'に', 'は', 'を', 'た', 'が', 'で', 'て', 'と', 'し', 'れ', 'さ',
  'ある', 'いる', 'も', 'する', 'から', 'な', 'こと', 'として', 'い', 'や',
  'れる', 'など', 'なっ', 'ない', 'この', 'ため', 'その', 'あっ', 'よう',
  'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
  'should', 'may', 'might', 'shall', 'can', 'need', 'to', 'of', 'in',
  'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into', 'through',
  'and', 'but', 'or', 'not', 'so', 'yet', 'what', 'which', 'who',
  'this', 'that', 'these', 'those', 'i', 'me', 'my', 'we', 'you', 'he',
  'she', 'it', 'they', 'about', 'how', 'tell', 'show', '教えて', '調べて',
  '集めて', '情報', 'について', 'ください', '何', 'どう', 'どの',
]);

function extractKeywords(text: string): string[] {
  return text
    .toLowerCase()
    .replace(/[^\w\s\u3000-\u9fff\uff00-\uffef]/g, ' ')
    .split(/[\s\u3000]+/)
    .filter((w) => w.length >= 2 && !STOPWORDS.has(w))
    .slice(0, 8);
}

// ── Context retrieval (PDS XRPC single path) ──

/**
 * Retrieve graph context via PDS XRPC → graph SQL path → RisingWave.
 *
 * Single path: federatedQuery per target label → local cache query.
 */
async function retrieveGraphContext(
  userMessage: string,
  targetLabels: string[],
): Promise<string> {
  const keywords = extractKeywords(userMessage);
  if (keywords.length === 0) return '';

  const likeConditions = keywords
    .map((kw) => `(val LIKE '%${kw.replace(/'/g, "''")}%' OR text LIKE '%${kw.replace(/'/g, "''")}%')`)
    .join(' OR ');

  // Single path: PDS XRPC federatedQuery for each label (graph SQL path → RisingWave)
  const filterKeyword = keywords[0];
  const fedPromises = targetLabels.slice(0, 5).map((label) =>
    kagamiStore.federatedQuery(label, filterKeyword, MAX_CONTEXT_ROWS).catch((error) => {
      console.warn("[silent-fail] graph-rag.svelte.ts: federatedQuery failed", { label, error });
      return 0;
    }),
  );
  await Promise.allSettled(fedPromises);

  // Query merged cache (populated by federatedQuery)
  let rows: Array<{ label: string; vertex_id: string; val: string; did: string; text: string; updated_at: string }> = [];
  try {
    rows = await kagamiStore.sql(`
      SELECT label, vertex_id, val, did, text, updated_at
      FROM local_graph
      WHERE (${likeConditions})
      ORDER BY updated_at DESC
      LIMIT ${MAX_CONTEXT_ROWS}
    `);
  } catch (e) {
    console.warn('[graph-rag] cache query failed:', e);
  }

  if (rows.length === 0) return '';

  // Format rows into compact context block
  const contextLines: string[] = [];
  let charCount = 0;

  for (const row of rows) {
    const rawVal = String(row.val ?? '');
    let summary = (row.text || rawVal || '').slice(0, 150);
    if ((rawVal.startsWith('{') && rawVal.endsWith('}')) || (rawVal.startsWith('[') && rawVal.endsWith(']'))) {
      try {
        const parsed = JSON.parse(rawVal);
        const fields: string[] = [];
        for (const [k, v] of Object.entries(parsed as Record<string, unknown>)) {
          if (k === 'val' || k === 'record_type') continue;
          if (typeof v === 'string' && v.length > 0 && v.length < 200) {
            fields.push(`${k}: ${v}`);
          } else if (typeof v === 'number') {
            fields.push(`${k}: ${v}`);
          }
        }
        if (fields.length > 0) summary = fields.slice(0, 6).join(', ');
      } catch {
        // Keep scalar/text fallback.
      }
    }

    const line = `[${row.label}] ${summary}`;
    if (charCount + line.length > MAX_CONTEXT_CHARS) break;
    contextLines.push(line);
    charCount += line.length;
  }

  return contextLines.join('\n');
}

// ── System prompt construction ──

function buildGraphRAGSystemPrompt(basePrompt: string, graphContext: string, loadedLabels: string[]): string {
  const labelInfo = loadedLabels.length > 0
    ? `\nLoaded graph labels: ${loadedLabels.join(', ')}`
    : '';

  if (!graphContext) return basePrompt + labelInfo;

  return `${basePrompt}

## Knowledge Graph Context (from local cache — ${loadedLabels.length} labels)
The following data was retrieved from the local graph cache (XRPC-sourced). Use it to provide accurate, grounded responses. If the context is not relevant to the question, ignore it.

${graphContext}

Answer based on the above context when relevant. If the context doesn't contain the answer, say so and respond based on your general knowledge.${labelInfo}`;
}

// ── Reactive state ──

let _lastContextLabels = $state(0);
let _lastContextChars = $state(0);
let _lastClassifiedLabels = $state<string[]>([]);
let _lastFederatedCount = $state(0);

/**
 * GraphRAG query engine: domain-aware lazy loading + federated XRPC fallback.
 *
 * Design 1+5: Gemma 4 E2B classifies query → lazy-load relevant labels →
 * local cache query → federated PDS query if insufficient → LLM grounded response.
 */
export function useGraphRAG() {
  const localLLM = useLocalLLM();
  const ameno = useAmeno();

  return {
    get lastContextLabels() { return _lastContextLabels; },
    get lastContextChars() { return _lastContextChars; },
    get lastClassifiedLabels() { return _lastClassifiedLabels; },
    get lastFederatedCount() { return _lastFederatedCount; },
    get isReady() { return (localLLM.isReady || ameno.isReady) && kagamiStore.isReady(); },
    get isLLMReady() { return localLLM.isReady || ameno.isReady; },
    /** Whether ameno (transformers.js ONNX + LoRA) is the active backend. */
    get isAmenoActive() { return ameno.isReady; },
    get loadedLabels() { return kagamiStore.getLoadedLabels(); },
    /** Ameno inference stats from last generation. */
    get amenoStats() { return ameno.lastStats; },

    /**
     * Run a GraphRAG query with domain-aware lazy loading + federated fallback.
     */
    async query(
      chatHistory: ChatMessage[],
      userMessage: string,
      baseSystemPrompt?: string,
    ): Promise<string | null> {
      if (!localLLM.isReady && !ameno.isReady) return null;

      // Step 1: Classify query → relevant labels
      const classifyLLM = localLLM.isReady ? localLLM : { isReady: false, chatCompletion: async () => null, lastInferenceError: null } as any;
      const targetLabels = await classifyLabels(userMessage, classifyLLM);
      _lastClassifiedLabels = targetLabels;

      // Step 2: Retrieve context (lazy load + federated)
      const graphContext = await retrieveGraphContext(userMessage, targetLabels);
      _lastContextLabels = graphContext ? graphContext.split('\n').length : 0;
      _lastContextChars = graphContext.length;

      // Step 3: Build grounded system prompt
      const defaultPrompt = 'You are a helpful AI assistant on yoro.etzhayyim.com. Respond concisely in the same language as the user.';
      const systemPrompt = buildGraphRAGSystemPrompt(
        baseSystemPrompt ?? defaultPrompt,
        graphContext,
        kagamiStore.getLoadedLabels(),
      );

      // Step 4: Run LLM — ameno (transformers.js + LoRA) preferred, WebLLM fallback
      const compactHistory = compressChatHistory(chatHistory);
      const messages: ChatMessage[] = [
        { role: 'system', content: systemPrompt },
        ...compactHistory,
        { role: 'user', content: userMessage },
      ];

      if (ameno.isReady) {
        const result = await ameno.chatCompletion(messages, { maxTokens: 1024 });
        if (result) return result;
        // Ameno failed — fall through to WebLLM
      }

      if (localLLM.isReady) {
        return chatCompletionResilient(localLLM, messages);
      }

      return null;
    },

    /**
     * Run a streaming GraphRAG query — yields tokens as they arrive.
     *
     * Same pipeline as query() but uses chatCompletionStream() for
     * real-time token-by-token UI rendering.
     */
    async *queryStream(
      chatHistory: ChatMessage[],
      userMessage: string,
      baseSystemPrompt?: string,
    ): AsyncGenerator<string, void, unknown> {
      if (!localLLM.isReady && !ameno.isReady) return;

      const classifyLLM = localLLM.isReady ? localLLM : { isReady: false, chatCompletion: async () => null, lastInferenceError: null } as any;
      const targetLabels = await classifyLabels(userMessage, classifyLLM);
      _lastClassifiedLabels = targetLabels;

      const graphContext = await retrieveGraphContext(userMessage, targetLabels);
      _lastContextLabels = graphContext ? graphContext.split('\n').length : 0;
      _lastContextChars = graphContext.length;

      const defaultPrompt = 'You are a helpful AI assistant on yoro.etzhayyim.com. Respond concisely in the same language as the user.';
      const systemPrompt = buildGraphRAGSystemPrompt(
        baseSystemPrompt ?? defaultPrompt,
        graphContext,
        kagamiStore.getLoadedLabels(),
      );

      const compactHistory = compressChatHistory(chatHistory);
      const messages: ChatMessage[] = [
        { role: 'system', content: systemPrompt },
        ...compactHistory,
        { role: 'user', content: userMessage },
      ];

      // Ameno preferred (transformers.js + LoRA), WebLLM fallback
      if (ameno.isReady) {
        yield* ameno.chatCompletionStream(messages, { maxTokens: 512 });
        return;
      }

      yield* localLLM.chatCompletionStream(messages, { maxTokens: 512, temperature: 0.6 });
    },

    /**
     * Multi-hop graph query: follow edges to gather deeper context.
     *
     * Example: "Who follows accounts that post about semiconductors?"
     * Step 1: Find Post vertices matching keywords
     * Step 2: Follow FOLLOWS edges to find connected profiles
     * Step 3: Merge both hops into context
     */
    async queryMultiHop(
      chatHistory: ChatMessage[],
      userMessage: string,
      baseSystemPrompt?: string,
    ): Promise<string | null> {
      if (!localLLM.isReady || !kagamiStore.isReady()) return null;

      const targetLabels = await classifyLabels(userMessage, localLLM);
      _lastClassifiedLabels = targetLabels;

      // Hop 1: direct keyword match
      const directContext = await retrieveGraphContext(userMessage, targetLabels);

      const combinedContext = directContext ?? '';
      _lastContextLabels = combinedContext ? combinedContext.split('\n').length : 0;
      _lastContextChars = combinedContext.length;

      const defaultPrompt = 'You are a helpful AI assistant on yoro.etzhayyim.com. Respond concisely in the same language as the user.';
      const systemPrompt = buildGraphRAGSystemPrompt(
        baseSystemPrompt ?? defaultPrompt,
        combinedContext,
        kagamiStore.getLoadedLabels(),
      );

      const compactHistory = compressChatHistory(chatHistory);
      const messages: ChatMessage[] = [
        { role: 'system', content: systemPrompt },
        ...compactHistory,
        { role: 'user', content: userMessage },
      ];

      return chatCompletionResilient(localLLM, messages);
    },

    /** Pre-load labels for a specific domain context. */
    async preloadLabels(labels: string[]): Promise<void> {
      for (const label of labels) {
        if (kagamiStore.isStale(label)) {
          await kagamiStore.loadLabel(label, 5000);
        }
      }
    },
  };
}
