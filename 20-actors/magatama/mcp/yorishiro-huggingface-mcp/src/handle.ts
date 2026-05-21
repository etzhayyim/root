import type { HuggingfaceHandle } from "./tools.js";

export interface DefaultHandleOptions {
  baseUrl: string;
}

export function createDefaultHuggingfaceHandle(opts: DefaultHandleOptions): HuggingfaceHandle {
  const baseUrl = opts.baseUrl.endsWith("/") ? opts.baseUrl : opts.baseUrl + "/";
  const handle: HuggingfaceHandle = {
  async search_models(input) {
    const params: Record<string, unknown> = { ...input };
    let path = "/api/models";
    for (const key of Object.keys(params)) {
      const token = `{${key}}`;
      if (path.includes(token)) {
        path = path.split(token).join(String(params[key]));
        delete params[key];
      }
    }
    const url = new URL(path, baseUrl);
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      url.searchParams.append(k, String(v));
    }
    const init: RequestInit = { method: "GET", headers: { "User-Agent": "etzhayyim-yorishiro-huggingface-mcp/0.1" } };
    try {
      const res = await fetch(url, init);
      const text = await res.text();
      let json: unknown = undefined;
      try { json = JSON.parse(text); } catch { /* not JSON, keep raw */ }
      return {
        httpStatus: res.status,
        ...(json !== undefined ? { json } : { body: text }),
        ...(res.ok ? {} : { error: text.slice(0, 1000) }),
      };
    } catch (err) {
      return { httpStatus: 0, error: (err as Error).message };
    }
  },
  async search_datasets(input) {
    const params: Record<string, unknown> = { ...input };
    let path = "/api/datasets";
    for (const key of Object.keys(params)) {
      const token = `{${key}}`;
      if (path.includes(token)) {
        path = path.split(token).join(String(params[key]));
        delete params[key];
      }
    }
    const url = new URL(path, baseUrl);
    for (const [k, v] of Object.entries(params)) {
      if (v === undefined || v === null || v === "") continue;
      url.searchParams.append(k, String(v));
    }
    const init: RequestInit = { method: "GET", headers: { "User-Agent": "etzhayyim-yorishiro-huggingface-mcp/0.1" } };
    try {
      const res = await fetch(url, init);
      const text = await res.text();
      let json: unknown = undefined;
      try { json = JSON.parse(text); } catch { /* not JSON, keep raw */ }
      return {
        httpStatus: res.status,
        ...(json !== undefined ? { json } : { body: text }),
        ...(res.ok ? {} : { error: text.slice(0, 1000) }),
      };
    } catch (err) {
      return { httpStatus: 0, error: (err as Error).message };
    }
  },
  };
  return handle;
}
