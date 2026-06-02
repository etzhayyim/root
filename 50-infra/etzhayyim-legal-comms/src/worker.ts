/**
 * etzhayyim-legal-comms Worker — XRPC face of the counsel-operated gateway.
 *
 * POST /xrpc/com.etzhayyim.legal.sendLegalAct
 *   body: { artifact: LegalActArtifact, counselActuation: CounselActuation }
 *   The request MUST carry a counselActuation; sendLegalAct (G18) throws
 *   otherwise. The Worker holds no signing key — the lawyer's signature
 *   reference is supplied by counsel in the request (no-server-key).
 */
import {
  sendLegalAct,
  transmitNonLegalAct,
  type TransportAdapters,
} from "./gateway";

export interface Env {
  // Transport adapter endpoints are operator-configured; none holds a
  // platform legal-act signing key (no-server-key ADR-2605231525).
  FAX_RELAY_URL?: string;
}

function json(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

// Production transport adapters are injected at deploy; stubbed here so the
// G18 gate is exercised without a live court endpoint.
function adapters(_env: Env): TransportAdapters {
  const noop = { async transmit() {} };
  return { fax: noop, email: noop, "e-filing": noop, "secure-message": noop, postal: noop };
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    if (req.method === "POST" &&
        url.pathname === "/xrpc/com.etzhayyim.legal.sendLegalAct") {
      let body: { artifact?: unknown; counselActuation?: unknown };
      try { body = await req.json(); } catch { return json({ error: "BadRequest" }, 400); }
      try {
        const receipt = await sendLegalAct(
          body.artifact as never,
          body.counselActuation as never, // undefined → G18 throws
          adapters(env),
        );
        return json(receipt, 200);
      } catch (e) {
        // G18 refusal surfaces as 422 — the act is structurally impossible
        // without counsel actuation.
        return json({ error: "CounselActuationRequired",
          message: (e as Error).message }, 422);
      }
    }

    if (req.method === "POST" &&
        url.pathname === "/xrpc/com.etzhayyim.legal.sendNonLegalAct") {
      const b = await req.json() as {
        kind: "appointment" | "document-delivery" | "scheduling";
        transport: never; endpoint: string; payloadCid: string;
      };
      const receipt = await transmitNonLegalAct(
        b.kind, b.transport, b.endpoint, b.payloadCid, adapters(env));
      return json(receipt, 200);
    }

    if (url.pathname === "/health") return json({ status: "ok" });
    return json({ error: "NotFound" }, 404);
  },
};
