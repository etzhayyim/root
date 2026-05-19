/**
 * graph.ts — ameno browser-side LangGraph (Pregel) runtime.
 *
 * Single StateGraph: generate → critique → (revise → critique)* → finalize.
 * Each node calls `mediapipeGenerate` (or `transformersGenerate`) directly,
 * so the LLM stays in the browser. Token streaming is surfaced via
 * LangGraph's `writer()` and consumed by App.svelte through
 * `graph.stream(_, { streamMode: "custom" })`.
 *
 * Authoritative ADR: 90-docs/adr/2605191000-ameno-browser-pregel-reflection.md
 */
import {
  Annotation,
  END,
  MemorySaver,
  START,
  StateGraph,
  type LangGraphRunnableConfig,
} from "@langchain/langgraph";
import { mediapipeGenerate } from "./mediapipe-runtime";
import { generate as transformersGenerate, type ChatMessage, type GenerationStats } from "./inference";

/**
 * Browser-safe writer accessor. LangGraph v1.x ships `writer()` as a free
 * function that reads `AsyncLocalStorageProviderSingleton.getRunnableConfig()`
 * to find the current node's stream writer — but `AsyncLocalStorage` is a
 * Node-only API and is not polyfilled in browser bundles, so the free
 * function throws "Called interrupt() outside the context of a graph."
 * here. We bypass it by pulling the writer straight off the node's
 * `config.configurable.writer` (which LangGraph populates per super-step
 * when `streamMode` includes `"custom"`). When run with no custom-mode
 * consumer the writer is undefined; we fall back to a no-op.
 */
type ChunkWriter = (chunk: GraphChunk) => void;
function getNodeWriter(config: LangGraphRunnableConfig): ChunkWriter {
  const w = (config?.configurable as { writer?: ChunkWriter } | undefined)?.writer;
  return w ?? (() => {});
}

export type GraphPhase = "generate" | "critique" | "revise" | "finalize";

export interface GraphTokenChunk {
  type: "token";
  phase: GraphPhase;
  token: string;
}

export interface GraphPhaseStartChunk {
  type: "phase";
  phase: GraphPhase;
  iteration: number;
}

export interface GraphCritiqueChunk {
  type: "critique";
  score: number;
  feedback: string;
  iteration: number;
}

export interface GraphStatsChunk {
  type: "stats";
  phase: GraphPhase;
  stats: GenerationStats;
}

export type GraphChunk =
  | GraphTokenChunk
  | GraphPhaseStartChunk
  | GraphCritiqueChunk
  | GraphStatsChunk;

/** Critique payload parsed out of the critic LLM. */
interface CritiqueResult {
  score: number;
  feedback: string;
}

const StateAnnotation = Annotation.Root({
  /** Conversation history. Reducer concatenates, so nodes return only
   *  the newly-added messages instead of the full list. */
  messages: Annotation<ChatMessage[]>({
    reducer: (a, b) => a.concat(b),
    default: () => [],
  }),
  /** Current draft response under review. */
  draft: Annotation<string>({
    reducer: (_, b) => b,
    default: () => "",
  }),
  /** Last critique result, or null before the critic has run. */
  critique: Annotation<CritiqueResult | null>({
    reducer: (_, b) => b,
    default: () => null,
  }),
  /** Number of revise cycles completed (0 = only initial draft). */
  iteration: Annotation<number>({
    reducer: (_, b) => b,
    default: () => 0,
  }),
  /** Reflection cap — 0 disables critic entirely. */
  maxIterations: Annotation<number>({
    reducer: (_, b) => b,
    default: () => 1,
  }),
  /** Which kernel to dispatch to. */
  kernel: Annotation<"mediapipe" | "transformers">({
    reducer: (_, b) => b,
    default: () => "mediapipe",
  }),
});

type GraphState = typeof StateAnnotation.State;

/** Dispatch generate to the right backend without re-importing in nodes. */
async function runtimeGenerate(
  kernel: "mediapipe" | "transformers",
  messages: ChatMessage[],
  onToken: (token: string) => void,
): Promise<GenerationStats> {
  if (kernel === "mediapipe") return mediapipeGenerate(messages, onToken);
  return transformersGenerate(messages, onToken);
}

/**
 * generateNode — produce the initial draft.
 */
async function generateNode(
  state: GraphState,
  config: LangGraphRunnableConfig,
): Promise<Partial<GraphState>> {
  const write = getNodeWriter(config);
  write({ type: "phase", phase: "generate", iteration: 0 });
  let draft = "";
  const stats = await runtimeGenerate(state.kernel, state.messages, (tok) => {
    draft += tok;
    write({ type: "token", phase: "generate", token: tok });
  });
  write({ type: "stats", phase: "generate", stats });
  return { draft };
}

/**
 * critiqueNode — same LLM scores its own draft.
 *
 * We use a tight JSON-only prompt so we can parse a 0-10 score and a single
 * actionable suggestion. Falls back to "accept" (score=7) when parsing fails
 * so a confused critic does not block progress.
 */
async function critiqueNode(
  state: GraphState,
  config: LangGraphRunnableConfig,
): Promise<Partial<GraphState>> {
  const write = getNodeWriter(config);
  write({ type: "phase", phase: "critique", iteration: state.iteration });

  const lastUser = [...state.messages].reverse().find((m) => m.role === "user");
  const critiquePrompt: ChatMessage[] = [
    {
      role: "system",
      content:
        "You are a strict reviewer. Read the user request and the assistant draft. " +
        "Score the draft from 0 (terrible) to 10 (excellent) and give ONE specific " +
        "actionable improvement. Reply with ONLY this JSON object on a single line, " +
        'no prose: {"score": <int 0-10>, "feedback": "<one sentence>"}',
    },
    {
      role: "user",
      content:
        `# User request\n${lastUser?.content ?? ""}\n\n` +
        `# Assistant draft\n${state.draft}\n\n` +
        `Reply with the JSON object now.`,
    },
  ];

  let raw = "";
  const stats = await runtimeGenerate(state.kernel, critiquePrompt, (tok) => {
    raw += tok;
    write({ type: "token", phase: "critique", token: tok });
  });
  write({ type: "stats", phase: "critique", stats });

  const parsed = parseCritique(raw);
  write({
    type: "critique",
    score: parsed.score,
    feedback: parsed.feedback,
    iteration: state.iteration,
  });
  return { critique: parsed };
}

/**
 * reviseNode — regenerate the draft with the critic's feedback in the
 * system prompt. iteration is incremented BEFORE the rewrite so the
 * stream phase chunk and the conditional edge agree on the count.
 */
async function reviseNode(
  state: GraphState,
  config: LangGraphRunnableConfig,
): Promise<Partial<GraphState>> {
  const write = getNodeWriter(config);
  const nextIter = state.iteration + 1;
  write({ type: "phase", phase: "revise", iteration: nextIter });

  const reviseMessages: ChatMessage[] = [
    ...state.messages,
    {
      role: "system",
      content:
        `Your previous draft was:\n---\n${state.draft}\n---\n\n` +
        `A reviewer scored it ${state.critique?.score ?? "?"}/10 and suggested: ` +
        `${state.critique?.feedback ?? "(no feedback)"}\n\n` +
        `Rewrite the response addressing the suggestion. Output only the improved reply.`,
    },
  ];

  let draft = "";
  const stats = await runtimeGenerate(state.kernel, reviseMessages, (tok) => {
    draft += tok;
    write({ type: "token", phase: "revise", token: tok });
  });
  write({ type: "stats", phase: "revise", stats });

  return { draft, iteration: nextIter };
}

/**
 * finalizeNode — commit the final draft to messages as an assistant turn.
 */
function finalizeNode(
  state: GraphState,
  config: LangGraphRunnableConfig,
): Partial<GraphState> {
  const write = getNodeWriter(config);
  write({ type: "phase", phase: "finalize", iteration: state.iteration });
  return {
    messages: [{ role: "assistant", content: state.draft }],
  };
}

/**
 * Conditional edge from critique. Accept early when the score is high
 * enough OR we've spent the iteration budget. iteration counts revisions,
 * so iteration >= maxIterations means we cannot revise any more.
 */
function decideContinue(state: GraphState): "revise" | "finalize" {
  const score = state.critique?.score ?? 10;
  if (score >= 7) return "finalize";
  if (state.iteration >= state.maxIterations) return "finalize";
  return "revise";
}

/**
 * Critic JSON parser. Extracts the first `{...}` block, parses it, clamps
 * the score, and trims feedback to 240 chars. Lenient by design — never
 * throws.
 */
function parseCritique(raw: string): CritiqueResult {
  const match = raw.match(/\{[\s\S]*?\}/);
  if (!match) return { score: 7, feedback: "(critic returned no JSON; accepting)" };
  try {
    const obj = JSON.parse(match[0]) as { score?: unknown; feedback?: unknown };
    const score = typeof obj.score === "number" ? clamp(Math.round(obj.score), 0, 10) : 7;
    const feedback =
      typeof obj.feedback === "string" ? obj.feedback.slice(0, 240) : "(no feedback)";
    return { score, feedback };
  } catch {
    return { score: 7, feedback: "(critic JSON unparseable; accepting)" };
  }
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, n));
}

/**
 * Build the compiled StateGraph. We compile lazily — once on first use —
 * because MediaPipe model load is asynchronous and the graph itself is
 * pure structure.
 */
let compiled: ReturnType<typeof buildGraph> | null = null;

function buildGraph() {
  const graph = new StateGraph(StateAnnotation)
    .addNode("generate", generateNode)
    .addNode("critic", critiqueNode)
    .addNode("revise", reviseNode)
    .addNode("finalize", finalizeNode)
    .addEdge(START, "generate")
    .addConditionalEdges("generate", (state: GraphState) =>
      state.maxIterations > 0 ? "critic" : "finalize",
    )
    .addConditionalEdges("critic", decideContinue)
    .addEdge("revise", "critic")
    .addEdge("finalize", END);

  return graph.compile({ checkpointer: new MemorySaver() });
}

export function getAmenoGraph() {
  if (!compiled) compiled = buildGraph();
  return compiled;
}

export interface InvokeAmenoOptions {
  /** Conversation history INCLUDING the new user turn. */
  messages: ChatMessage[];
  /** 0..2. 0 disables reflection entirely. */
  maxIterations: number;
  /** Which inference kernel to use for this turn. */
  kernel: "mediapipe" | "transformers";
  /** thread_id for MemorySaver — defaults to "default" so a single tab keeps state. */
  threadId?: string;
  /** Per-chunk callback. */
  onChunk: (chunk: GraphChunk) => void;
}

/**
 * Convenience wrapper around `graph.stream(_, { streamMode: "custom" })`.
 * Drains the stream and returns the final assistant text.
 */
export async function invokeAmeno(opts: InvokeAmenoOptions): Promise<string> {
  const graph = getAmenoGraph();
  const stream = await graph.stream(
    {
      messages: opts.messages,
      maxIterations: opts.maxIterations,
      kernel: opts.kernel,
      iteration: 0,
      draft: "",
      critique: null,
    },
    {
      configurable: { thread_id: opts.threadId ?? "default" },
      streamMode: "custom",
    },
  );

  let lastDraft = "";
  for await (const chunk of stream) {
    const payload = chunk as GraphChunk;
    opts.onChunk(payload);
    if (payload.type === "token") {
      // We don't accumulate here — the graph state owns truth — but we keep
      // the most recent stream of tokens for the UI fallback.
      lastDraft += payload.token;
    }
  }

  // Pull the canonical final draft from the graph state.
  const finalState = (await graph.getState({
    configurable: { thread_id: opts.threadId ?? "default" },
  })) as { values?: GraphState } | undefined;
  return finalState?.values?.draft ?? lastDraft;
}
