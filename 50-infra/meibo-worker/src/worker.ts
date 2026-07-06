// Thin TypeScript shell — all routing/logic lives in the ClojureScript core
// (cljs/src/meibo_worker/{core,ui,data_gen}.cljs, compiled by shadow-cljs to
// ../cljs-out/worker_core.js). Mirrors saisei-worker/src/worker.ts.
// @ts-expect-error — generated ESM bundle, no .d.ts (string-keyed interop).
import { handle as cljsHandle } from "../cljs-out/worker_core.js";

export interface Env {
  MEIBO_ANALYTICS?: AnalyticsEngineDataset;
}

export default {
  async fetch(
    request: Request,
    env: Env,
    ctx: ExecutionContext,
  ): Promise<Response> {
    return cljsHandle(request, env, ctx);
  },
} satisfies ExportedHandler<Env>;
