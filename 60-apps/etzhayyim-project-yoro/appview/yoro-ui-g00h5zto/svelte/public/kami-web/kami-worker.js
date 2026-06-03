/**
 * KAMI Engine WebGPU Worker — runs WASM + WebGPU on OffscreenCanvas.
 * Host sends: { type: 'init', canvas: OffscreenCanvas, width, height, scene }
 * Worker sends: { type: 'ready' } | { type: 'error', message }
 */

let kamiMod = null;

self.onmessage = async (e) => {
  const { type } = e.data;

  if (type === 'init') {
    const { canvas, width, height, scene } = e.data;

    try {
      // 1. Check WebGPU in Worker
      if (!navigator.gpu) {
        self.postMessage({ type: 'error', message: 'No WebGPU in Worker' });
        return;
      }

      const adapter = await navigator.gpu.requestAdapter();
      if (!adapter) {
        self.postMessage({ type: 'error', message: 'No WebGPU adapter' });
        return;
      }

      // 2. Load KAMI WASM
      const mod = await import('/kami-web/kami_web.js');
      await mod.default('/kami-web/kami_web_bg.wasm');
      kamiMod = mod;

      // 3. Set canvas size
      canvas.width = width * 2;
      canvas.height = height * 2;

      // 4. Run scene on OffscreenCanvas
      // Note: kami_web expects canvas_id for document.getElementById
      // For OffscreenCanvas, we need to use the canvas directly
      // This requires kami_web to support OffscreenCanvas (future)
      // For now, post ready and let it render
      self.postMessage({ type: 'ready' });

    } catch (err) {
      self.postMessage({ type: 'error', message: err?.message || 'Unknown error' });
    }
  }
};
