// Thin TypeScript shell — all routing/logic lives in the ClojureScript core
// (cljs/src/saisei_worker/{core,ui,data_gen}.cljs, compiled by shadow-cljs to
// ../cljs-out/worker_core.js). Unlike etzhayyim-did-web this Worker has no
// legacy TS to migrate away from, so there is no fallback handler and no
// deps-injection object — `handle` is called directly with the standard
// Workers fetch-handler triple; ClojureScript reaches bound env properties
// (e.g. env.SAISEI_ANALYTICS) via ordinary JS interop.
// @ts-expect-error — generated ESM bundle, no .d.ts (string-keyed interop).
import { handle as cljsHandle } from "../cljs-out/worker_core.js";

export interface Env {
  SAISEI_ANALYTICS?: AnalyticsEngineDataset;
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
