// mitate.etzhayyim.com — religious-corp self-care advisory PWA
// Per ADR-2605260100 (master) + ADR-2605260200 (R1 self-care advisory PWA).
//
// R0 phase: scaffold only — Worker contract locked, runtime returns 503 until R1
// baseline attestations land per ADR-2605260200 §Decision 2 (8 silenMitateReview
// + 5 condition Bayesian prior + ≥1 licensed MD + 1 emergency medicine specialist).
//
// Constitutional invariants enforced at the routing layer (tests/ verify each):
//   G3 — disclaimer-first flow: triage / treatment / medication-audit responses
//        MUST be preceded by /disclaimer ack within same session.
//   G5 — emergency_screen pass-through: /intake → /emergency_screen ALWAYS;
//        bypass to /triage is architecturally impossible at this routing layer.
//   G11 — push notification limited to 3 urgency-only channels
//         (emergency-ack / appointment-reminder / ae-followup); no other endpoints.
//   G14 — substrate boundary: all patient-data writes proxy via @etzhayyim/sdk
//         endpoint, never direct AT MST / IPFS / Base L2 calls from Worker.

import type { ExportedHandler, Request as CFRequest, Response as CFResponse } from "@cloudflare/workers-types";

interface SecretBinding { get(): Promise<string>; }
interface Env {
  // Phase gate — R0 = "locked"; R1 = "active-attestations-CID-here" after Council ratification
  MITATE_R1_PHASE_GATE?: string;
  // App metadata (auto-injected by e7m actor deploy from kotodama.jsonld)
  APP_NANOID?: string;
  APP_DISPLAY_NAME?: string;
  // Religious-corp SDK proxy endpoint (substrate boundary G14)
  ETZHAYYIM_SDK_PROXY_URL?: string;
  ETZHAYYIM_SDK_INTERNAL_SECRET?: string | SecretBinding;
  // Murakumo LiteLLM gateway (G12 — Murakumo only inference)
  MURAKUMO_LITELLM_GATEWAY_URL?: string;
  // CF Assets binding for static disclaimer / intake / triage HTML pages
  ASSETS?: { fetch(req: CFRequest): Promise<CFResponse> };
}

const ACTOR_DID = "did:web:mitate.etzhayyim.com";
const NSID_PREFIX = "com.etzhayyim.mitate.";

// R1 ACTIVE lexicon NSIDs (4 cells unlocked when MITATE_R1_PHASE_GATE !== "locked")
const R1_ACTIVE_NSIDS = new Set([
  "com.etzhayyim.mitate.rhinitisIntake",
  "com.etzhayyim.mitate.triageVerdict",
  "com.etzhayyim.mitate.emergencyEscalation",
]);

// R2+ GATED lexicon NSIDs (return 503 with R2-pending message)
const R2_GATED_NSIDS = new Set([
  "com.etzhayyim.mitate.diagnosticOrder",
  "com.etzhayyim.mitate.diagnosticResult",
  "com.etzhayyim.mitate.treatmentPlan",
  "com.etzhayyim.mitate.outcomeFollowup",
]);

// G11 — push notification only for these 3 urgency-only channels
const G11_ALLOWED_NOTIFICATION_CHANNELS = new Set([
  "emergency-ack",
  "appointment-reminder",
  "ae-followup",
]);

export default {
  async fetch(req: CFRequest, env: Env): Promise<CFResponse> {
    const url = new URL(req.url);

    // Public meta / health endpoints (no phase gate)
    if (url.pathname === "/health" || url.pathname === "/_app/meta") {
      return json({
        ok: true,
        actor: ACTOR_DID,
        nanoid: env.APP_NANOID ?? "m1t4tp01",
        displayName: env.APP_DISPLAY_NAME ?? "見立て (mitate) 鼻詰まり advisory",
        phaseGate: env.MITATE_R1_PHASE_GATE ?? "locked",
        r1ActiveLexicons: Array.from(R1_ACTIVE_NSIDS),
        r2GatedLexicons: Array.from(R2_GATED_NSIDS),
        advisoryOnly: true,
        embedDisabled: true,
      });
    }

    // R1 phase gate — return 503 with explanatory body until Council attestations land
    if ((env.MITATE_R1_PHASE_GATE ?? "locked") === "locked") {
      return json({
        error: "MitateR1PhaseGateLocked",
        message:
          "mitate-pwa is scaffold-only (R0). Deploy requires R1 ADR-2605260200 baseline " +
          "attestations: 8 silenMitateReview baselines (charter / G3 disclaimer / G5 " +
          "emergency keyword / G5 false-negative adversarial / G6 escalation / G11 " +
          "intake form text / G11 notification channel) + 5 per-condition Bayesian prior " +
          "+ ≥1 licensed MD on Council medical advisory + 1 emergency medicine specialist. " +
          "Do not deploy.",
        adr: "https://github.com/etzhayyim/root/blob/main/90-docs/adr/2605260200-mitate-r1-advisory-self-care-pwa.md",
      }, 503);
    }

    // ─── G3 disclaimer-first routing layer ──────────────────────────────────
    // Triage / medication-audit responses require prior disclaimer acknowledgment
    // recorded within the same session (consent receipt CID via @etzhayyim/sdk).
    // Implementation R1: verify via session cookie + consent receipt resolution.
    // Architectural invariant: triage HTML page MUST NOT render posterior probabilities
    // before disclaimer ack — enforced by routing redirect.
    if (url.pathname === "/triage" || url.pathname === "/medication-audit") {
      const ack = await verifyDisclaimerAck(req, env);
      if (!ack) {
        return redirect(`/disclaimer?next=${encodeURIComponent(url.pathname)}`, 303);
      }
    }

    // ─── G5 architectural invariant: intake → emergency_screen pass-through ──
    // /xrpc/com.etzhayyim.mitate.rhinitisIntake POST always triggers emergency_screen
    // cell as next-cell message at the substrate layer. No direct /triage POST allowed
    // from client — triage is read-only display of pre-computed verdict.
    if (req.method === "POST" && url.pathname === "/xrpc/com.etzhayyim.mitate.triageVerdict") {
      return json({
        error: "G5InvariantBlocked",
        message:
          "Direct POST to triageVerdict is not permitted. Patient intake must POST " +
          "to rhinitisIntake; emergency_screen cell pass-through is architectural " +
          "invariant per ADR-2605260100 §G5. Clients GET triageVerdict by AT URI " +
          "after the substrate-side cell chain completes.",
      }, 405);
    }

    // ─── G11 notification channel filter ───────────────────────────────────
    if (url.pathname.startsWith("/notify/")) {
      const channel = url.pathname.slice("/notify/".length).split("/")[0];
      if (!G11_ALLOWED_NOTIFICATION_CHANNELS.has(channel)) {
        return json({
          error: "G11NotificationChannelBlocked",
          message: `Notification channel '${channel}' not in allowed urgency-only set. Allowed: ${Array.from(G11_ALLOWED_NOTIFICATION_CHANNELS).join(", ")}.`,
        }, 403);
      }
      // Channel permitted — proxy to substrate
      return proxyToSubstrate(env, `notify/${channel}`, await req.text());
    }

    // ─── XRPC lexicon proxy (substrate boundary G14) ───────────────────────
    if (url.pathname.startsWith("/xrpc/")) {
      const nsid = url.pathname.slice("/xrpc/".length);
      if (R2_GATED_NSIDS.has(nsid)) {
        return json({
          error: "MitateR2GatedLexicon",
          message: `Lexicon '${nsid}' is R2-gated. R1 advisory tier does not order tests or generate treatment plans. See ADR-2605260200 §Decision 1.`,
          adr: "https://github.com/etzhayyim/root/blob/main/90-docs/adr/2605260200-mitate-r1-advisory-self-care-pwa.md",
        }, 503);
      }
      if (!nsid.startsWith(NSID_PREFIX)) {
        return json({ error: "NsidOutsideMitateNamespace" }, 400);
      }
      if (!R1_ACTIVE_NSIDS.has(nsid)) {
        return json({ error: "NsidNotInR1ActiveSet", nsid }, 503);
      }
      const body = req.method === "POST" ? await req.text() : "";
      return proxyToSubstrate(env, nsid, body);
    }

    // ─── Static asset / patient-facing HTML pages ──────────────────────────
    if (env.ASSETS) {
      return env.ASSETS.fetch(req);
    }

    return json({ error: "NotFound" }, 404);
  },
} satisfies ExportedHandler<Env>;

// G14 — all substrate writes go through @etzhayyim/sdk proxy, never direct
async function proxyToSubstrate(env: Env, nsidOrPath: string, body: string): Promise<CFResponse> {
  const proxyUrl = env.ETZHAYYIM_SDK_PROXY_URL ?? "https://substrate-proxy.etzhayyim.com";
  const secret = typeof env.ETZHAYYIM_SDK_INTERNAL_SECRET === "object"
    ? await env.ETZHAYYIM_SDK_INTERNAL_SECRET.get()
    : (env.ETZHAYYIM_SDK_INTERNAL_SECRET ?? "");
  const res = await fetch(`${proxyUrl}/${nsidOrPath}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "x-mitate-actor-did": ACTOR_DID,
      "x-internal-secret": secret,
    },
    body,
  });
  const data = await res.text();
  return new Response(data, {
    status: res.status,
    headers: { "Content-Type": "application/json" },
  }) as unknown as CFResponse;
}

// G3 — disclaimer acknowledgment verification
// R1 implementation: session cookie (HttpOnly, SameSite=Strict, 30-min TTL) with
// consent receipt CID resolved against MST. Scaffold returns false to enforce
// disclaimer flow until R1 implementation lands.
async function verifyDisclaimerAck(_req: CFRequest, _env: Env): Promise<boolean> {
  return false;
}

function json(data: unknown, status = 200): CFResponse {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { "Content-Type": "application/json" },
  }) as unknown as CFResponse;
}

function redirect(location: string, status = 303): CFResponse {
  return new Response(null, {
    status,
    headers: { Location: location },
  }) as unknown as CFResponse;
}
