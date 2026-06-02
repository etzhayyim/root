/**
 * etzhayyim.com free legal-aid intake front-end (ADR-2605302345 §D1).
 *
 * This Worker is the adherent-facing door to the free legal clinic. It is
 * substrate + orchestration ONLY: it opens a matter and relays it to the
 * chigiri_legal_aid_clinic cell. It renders NO legal advice (G14) — advice
 * comes exclusively from the licensed counsel the cell assigns out of the
 * Public Fund.
 *
 * Constitutional posture:
 *   - G14: no advice is produced here. The endpoint accepts the adherent's
 *     OWN description and returns intake status, never an answer.
 *   - G15: nothing is charged. There is no payment path, no fee field.
 *   - no-server-key (ADR-2605231525): this Worker holds no signing key.
 *     Intake writes are member-signed (the request carries the member's
 *     passkey-derived session); the Worker relays them through @etzhayyim/sdk.
 *   - no-cookie / no-ads: no Set-Cookie, no trackers, identity is DID-bound.
 *   - substrate-boundary: all substrate access via @etzhayyim/sdk only.
 */
import { Etzhayyim } from "@etzhayyim/sdk";

export interface Env {
  PDS_URL: string;
  KOTOBA_URL: string;
}

const INTAKE_NSID = "com.etzhayyim.chigiri.legalAidMatter";

const NO_ADVICE_NOTICE =
  "etzhayyim provides no legal advice at this step. Your matter is routed to " +
  "a lawyer licensed in your jurisdiction, retained free of charge from the " +
  "Public Fund. This service is gratuitous (zero fee).";

function json(body: unknown, status = 200): Response {
  // no-cookie: identity is DID-bound; no Set-Cookie header is ever emitted.
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json; charset=utf-8" },
  });
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const sdk = new Etzhayyim({ service: env.PDS_URL });

    // ── POST intake — open a free matter (member-signed) ──
    if (req.method === "POST" &&
        url.pathname === "/xrpc/com.etzhayyim.chigiri.legalAid.intake") {
      const auth = req.headers.get("authorization"); // member session (ES256)
      if (!auth) {
        return json({ error: "AuthRequired",
          message: "Intake is a member-signed write; present your session." }, 401);
      }
      let input: { adherentDid?: string; jurisdiction?: string; summaryCid?: string };
      try { input = await req.json(); } catch { return json({ error: "BadRequest" }, 400); }
      if (!input.adherentDid || !input.jurisdiction || !input.summaryCid) {
        return json({ error: "BadRequest",
          message: "adherentDid, jurisdiction, summaryCid required" }, 400);
      }

      // The intake record opens at `intake`; the cell assigns counsel (G16)
      // and flips intakeState to `counsel-assigned`. zeroCompensation is
      // pinned true (G15) and there is no fee field to set.
      const record = {
        adherentDid: input.adherentDid,
        jurisdiction: input.jurisdiction,
        lane: "advice",
        zeroCompensation: true,
        intakeState: "intake",
        summaryCid: input.summaryCid,
        createdAt: new Date().toISOString(),
      };

      // Relay the member-signed write through the SDK seam. The Worker holds
      // no key; `auth` carries the member's credential.
      const receipt = await sdk.write({
        collection: INTAKE_NSID,
        record,
        auth,
      } as never);

      return json({
        ok: true,
        matterUri: (receipt as { uri?: string })?.uri ?? null,
        intakeState: "intake",
        notice: NO_ADVICE_NOTICE,
      }, 201);
    }

    // ── GET status — read-only matter status ──
    if (req.method === "GET" &&
        url.pathname === "/xrpc/com.etzhayyim.chigiri.legalAid.status") {
      // no-server-key: read-only — anonymous read through the SDK seam.
      const matter = url.searchParams.get("matter");
      if (!matter) return json({ error: "BadRequest", message: "matter uri required" }, 400);
      const res = await sdk.read({ uri: matter } as never);
      return json({ ok: true, matter, status: res ?? null, notice: NO_ADVICE_NOTICE });
    }

    if (url.pathname === "/health") return json({ status: "ok" });
    return json({ error: "NotFound", notice: NO_ADVICE_NOTICE }, 404);
  },
};
