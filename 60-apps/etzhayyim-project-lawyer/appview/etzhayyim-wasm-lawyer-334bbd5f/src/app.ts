// lawyer.etzhayyim.com thin edge facade.
// Lawyer-specific operations: com.etzhayyim.apps.lawyer.*
// Shared lawfirm operations (firmDid=did:web:lawyer.etzhayyim.com): com.etzhayyim.apps.lawfirm.*
// All business logic runs in LangServer pods via dispatcher.

interface SecretBinding {
  get(): Promise<string>;
}

interface Env {
  DISPATCHER_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string | SecretBinding;
  APP_NANOID?: string;
  FIRM_DID_HINT?: string;
  LAWYER_DID_HINT?: string;
}

interface ExportedHandler<E> {
  fetch(req: Request, env: E): Promise<Response>;
}

const ROUTED_PREFIXES = ["com.etzhayyim.apps.lawyer.", "com.etzhayyim.apps.lawfirm."];

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const firmDid = env.FIRM_DID_HINT ?? "did:web:lawyer.etzhayyim.com";
    const lawyerDid = env.LAWYER_DID_HINT ?? "";

    if (url.pathname === "/health" || url.pathname === "/_worker/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        nanoid: env.APP_NANOID ?? "334bbd5f",
        handle: "lawyer.etzhayyim.com",
        tenant: "etzhayyim",
        firmDid,
        lawyerDid,
        execution: "edge-langserver",
        commands: [
          "com.etzhayyim.apps.lawyer.getDashboard",
          "com.etzhayyim.apps.lawyer.listAssignedMatters",
          "com.etzhayyim.apps.lawyer.listPendingGrants",
          "com.etzhayyim.apps.lawyer.acceptGrant",
          "com.etzhayyim.apps.lawyer.logWorkNote",
          "com.etzhayyim.apps.lawyer.submitDocumentDraft",
        ],
        sharedCommands: [
          "com.etzhayyim.apps.lawfirm.recordTimeEntry",
          "com.etzhayyim.apps.lawfirm.listInvoices",
          "com.etzhayyim.apps.lawfirm.scheduleHearing",
          "com.etzhayyim.apps.lawfirm.uploadDocument",
          "com.etzhayyim.apps.lawfirm.searchPrecedent",
        ],
        graphs: ["lawyer-matter-workspace", "lawyer-document-drafting"],
        note: "Attorney portal. Shares com.etzhayyim.apps.lawfirm.* lexicons with firmDid scoping.",
      });
    }

    const nsid = url.pathname.startsWith("/xrpc/") ? url.pathname.slice("/xrpc/".length) : "";
    if (ROUTED_PREFIXES.some((p) => nsid.startsWith(p)) && (req.method === "POST" || req.method === "GET")) {
      const body = await bodyWithQuery(req, url, firmDid, lawyerDid);
      if (body.__invalidJson) return json({ error: "InvalidJson" }, 400);
      return proxyToDispatcher(env, nsid, body);
    }

    return json({ error: "NotFound", message: "lawyer: endpoint not found" }, 404);
  },
} satisfies ExportedHandler<Env>;

async function bodyWithQuery(
  req: Request,
  url: URL,
  firmDid: string,
  lawyerDid: string,
): Promise<Record<string, unknown>> {
  let body: Record<string, unknown> = {};
  if (req.method === "POST") {
    const text = await req.text();
    try {
      body = text ? (JSON.parse(text) as Record<string, unknown>) : {};
    } catch {
      return { __invalidJson: true };
    }
  }
  url.searchParams.forEach((v, k) => {
    if (!(k in body)) body[k] = v;
  });
  if (!("firmDid" in body)) body.firmDid = firmDid;
  if (!("lawyerDid" in body) && lawyerDid) body.lawyerDid = lawyerDid;
  return body;
}

async function proxyToDispatcher(env: Env, nsid: string, body: Record<string, unknown>): Promise<Response> {
  const base = (env.DISPATCHER_URL ?? "https://dispatcher.etzhayyim.com").replace(/\/+$/, "");
  const headers: Record<string, string> = { "content-type": "application/json" };
  const trust = await internalTrustSecret(env);
  if (trust) headers["x-internal-trust"] = trust;
  const resp = await fetch(`${base}/xrpc/${nsid}`, { method: "POST", headers, body: JSON.stringify(body) });
  const text = await resp.text();
  return new Response(text, {
    status: resp.status,
    headers: {
      "content-type": resp.headers.get("content-type") ?? "application/json",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
}

async function internalTrustSecret(env: Env): Promise<string> {
  const binding = env.DISPATCHER_INTERNAL_SECRET;
  if (!binding) return "";
  try {
    return typeof binding === "string" ? binding : await binding.get();
  } catch {
    return "";
  }
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: {
      "content-type": "application/json",
      "cache-control": "no-store",
      "access-control-allow-origin": "*",
    },
  });
}
