/**
 * llm-worker.ts — Dedicated Web Worker hosting the WebLLM MLC engine.
 *
 * Runs model weight downloading, WebGPU shader compilation, and all LLM
 * inference off the main thread. The main thread creates this worker via
 * `new Worker(new URL('./llm-worker.ts', import.meta.url), { type: 'module' })`
 * and communicates through `CreateWebWorkerMLCEngine` (message-passing proxy).
 *
 * Responsibilities (all happen in this worker's V8 isolate):
 * - Model weight download and caching (IndexedDB / Cache API).
 * - WebGPU shader compilation and buffer allocation.
 * - Chat completion inference (both streaming and non-streaming).
 *
 * The main thread never touches GPU buffers or model weights directly,
 * preventing OOM crashes and UI jank during heavy inference workloads.
 *
 * @module
 */

import { WebWorkerMLCEngineHandler } from '@mlc-ai/web-llm';

/** Singleton handler that bridges `self.onmessage` to the WebLLM engine. */
const handler = new WebWorkerMLCEngineHandler();

self.onmessage = (msg: MessageEvent) => {
	handler.onmessage(msg);
};
