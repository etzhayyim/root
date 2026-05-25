// auth-signup.ts — self-service signup (P5).
//
// Flow:
//   POST /auth/v1/signup (no auth)
//     → generate a fresh tenant org_did (`did:web:t-<rand>.yata-tenant.etzhayyim.com`)
//     → generate a `sk_live_yata_*` raw key (32 chars) + sha256 hash
//     → INSERT vertex_api_key row directly via Hyperdrive — schema matches
//       the canonical createApiKey handler (atproto/handlers/register.ts).
//       PDS resolveAuth picks up new keys immediately because both writers
//       hit the same RW table.
//     → return { apiKey, orgDid } once. Customer saves the key.
//
// This bypasses PDS XRPC `app.etzhayyim.auth.createApiKey` because that endpoint
// requires session auth — yatabase signup is anonymous by design and
// owns its own tenant boundary.
//
// Anti-abuse: each Worker IP gets a soft rate limit (Phase 2). Real
// production also gates this behind email verification + atproto OAuth
// handshake; MVP P5 is anonymous to demonstrate the BaaS self-serve loop.

// Must match atproto Worker `INTERNAL_MINT_HEADER` (50-infra/cloudflare/workers/atproto/src/app.ts).
export interface SignupEnv {
  HYPERDRIVE?: unknown;
  YATA_VERSION?: string;
  RESEND_API_KEY?: string;
  EMAIL_FROM?: string;
  /** lg-yatabase Granian pod URL — when set, signup forwards there (post-ADR-2605111200 path). */
  LG_YATABASE_URL?: string;
  DISPATCHER_INTERNAL_SECRET?: string;
}

interface AnyKyselyDb {
  insertInto(table: string): {
    values(row: Record<string, unknown>): {
      execute(): Promise<unknown>;
    };
  };
}

async function getDb(env: SignupEnv): Promise<AnyKyselyDb | null> {
  if (!env.HYPERDRIVE) {
    console.warn("[yatabase][signup] env.HYPERDRIVE falsy at request time");
    return null;
  }
  try {
    const sdk = await import("@etzhayyim/magatama-host-sdk");
    const factory = (sdk as { createKyselyDb?: unknown }).createKyselyDb;
    if (typeof factory !== "function") {
      console.warn("[yatabase][signup] @etzhayyim/magatama-host-sdk has no createKyselyDb export");
      return null;
    }
    return (factory as (h: unknown) => unknown)(env.HYPERDRIVE) as unknown as AnyKyselyDb;
  } catch (e) {
    console.warn("[yatabase][signup] createKyselyDb threw:", e instanceof Error ? e.message : e);
    return null;
  }
}

function generateApiKey(): string {
  const buf = new Uint8Array(24);
  crypto.getRandomValues(buf);
  const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  let out = "sk_live_yata_";
  for (const b of buf) out += chars[b % chars.length];
  return out;
}

function generateAwsAccessKey(): { id: string; secret: string } {
  const buf = new Uint8Array(20);
  crypto.getRandomValues(buf);
  const idChars = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789";
  let id = "gftd_";
  for (const b of buf) id += idChars[b % idChars.length];
  const sbuf = new Uint8Array(40);
  crypto.getRandomValues(sbuf);
  const secret = Array.from(sbuf)
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
  return { id, secret };
}

async function sha256Hex(text: string): Promise<string> {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(text));
  return Array.from(new Uint8Array(buf))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}

interface SignupRequestBody {
  email?: string;
  name?: string;
  utm_source?: string;
  utm_medium?: string;
  utm_campaign?: string;
  referrer?: string;
}

// Writes a `signup_index:v1:{YYYY-MM-DD}` KV entry so the day-7 retention
// cron can find tenants by signup date without a full-table scan.
async function recordSignupIndex(
  kv: KVNamespace,
  orgDid: string,
  email: string,
  name: string,
): Promise<void> {
  const today = new Date().toISOString().slice(0, 10);
  const key = `signup_index:v1:${today}`;
  let entries: Array<{ orgDid: string; email: string; name: string }> = [];
  try {
    const raw = await kv.get(key);
    if (raw) entries = JSON.parse(raw) as typeof entries;
  } catch { /* start fresh */ }
  if (!entries.some((e) => e.orgDid === orgDid)) {
    entries.push({ orgDid, email, name });
  }
  // TTL: 40 days. The day-7 cron reads date -7d; 40d headroom covers retries.
  await kv.put(key, JSON.stringify(entries), { expirationTtl: 40 * 24 * 3600 });
}

export async function handleSignup(env: SignupEnv, req?: Request): Promise<Response> {
  // Optional email + display name in body. If email is provided we'll
  // emit a welcome email (Resend if configured, outbox otherwise).
  let bodyJson: SignupRequestBody = {};
  if (req) {
    try { bodyJson = await req.json(); } catch { /* ignore empty body */ }
  }
  const recipientEmail = (bodyJson.email ?? "").trim().slice(0, 256);
  const recipientName = (bodyJson.name ?? "").trim().slice(0, 128) || "there";
  const utmSource = (bodyJson.utm_source ?? "").trim().slice(0, 64);
  const utmMedium = (bodyJson.utm_medium ?? "").trim().slice(0, 64);
  const utmCampaign = (bodyJson.utm_campaign ?? "").trim().slice(0, 64);
  const refererHeader = (req?.headers.get("referer") ?? bodyJson.referrer ?? "").slice(0, 256);

  // PRIMARY PATH (post ADR-2605111200): forward to lg-yatabase pod for
  // the vertex_api_key INSERT. The pod is the only writer; this Worker
  // is edge-only. We still own the email outbox emit (it goes through
  // the same email-outbox path which the migration agent will move
  // next).
  if (env.LG_YATABASE_URL) {
    const { forwardSignup } = await import("./auth-forward");
    const fwd = await forwardSignup(env, { email: recipientEmail || undefined, name: recipientName === "there" ? undefined : recipientName });
    if (!fwd.ok) {
      return new Response(
        JSON.stringify({
          error: "ServiceUnavailable",
          message: `signup forward failed (status=${fwd.status}): ${fwd.error ?? "unknown"}`,
        }),
        { status: 503, headers: { "content-type": "application/json", "x-yatabase-surface": "signup" } },
      );
    }
    const podBody = fwd.data as Record<string, unknown>;
    // Cache the freshly-minted key resolution in Workers Cache so subsequent
    // bearer auth works for 24h at this edge POP even if RisingWave durability
    // is degraded. P62 (2026-05-12) workaround for stuck-DDL blast radius.
    if (typeof podBody.apiKey === "string" && typeof podBody.orgDid === "string") {
      try {
        const { rememberApiKeyResolution, rememberAwsCreds } = await import("./auth-cache");
        await rememberApiKeyResolution(env as never, podBody.apiKey, podBody.orgDid);
        // P86: also cache the AWS SigV4 secret so /s3/* path verification
        // doesn't need to round-trip to RW (blocked by ADR-2605111200).
        if (typeof podBody.awsAccessKeyId === "string" && typeof podBody.awsSecretAccessKey === "string") {
          await rememberAwsCreds(
            env as never,
            podBody.awsAccessKeyId,
            podBody.awsSecretAccessKey,
            podBody.orgDid,
          );
        }
      } catch (e) {
        console.warn("[yatabase][signup] auth-cache fill failed:", e);
      }
    }
    // Fire welcome email locally (operator-side outbox still here for now;
    // when email-outbox is migrated, this will forward too).
    let emailStatus = String(podBody.emailStatus ?? "skipped-no-email");
    if (recipientEmail && typeof podBody.apiKey === "string" && typeof podBody.orgDid === "string") {
      try {
        const sdk = await import("./email-outbox");
        const tpl = sdk.welcomeEmail(podBody.orgDid, podBody.apiKey, recipientName);
        const result = await sdk.emitOutbox(env as never, {
          orgDid: podBody.orgDid,
          recipientEmail,
          recipientName,
          kind: "signup-welcome",
          subject: tpl.subject,
          bodyText: tpl.text,
          bodyHtml: tpl.html,
        });
        emailStatus = result.status;
      } catch (e) {
        emailStatus = "outbox-error";
        console.warn("[yatabase][signup] outbox emit failed (pod path):", e);
      }
    }
    // P45: record signup date for day-7 retention cron.
    if (typeof podBody.orgDid === "string" && (env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE) {
      try {
        await recordSignupIndex(
          (env as { YATABASE_AUTH_CACHE: KVNamespace }).YATABASE_AUTH_CACHE,
          podBody.orgDid as string,
          recipientEmail,
          recipientName,
        );
      } catch (e) {
        console.warn("[yatabase][signup] signup_index write failed:", e);
      }
      // Sprint 1 H1: referrer funnel tracking.
      try {
        const { recordReferrer } = await import("./referrer");
        await recordReferrer(
          env as never,
          podBody.orgDid as string,
          utmSource,
          utmMedium,
          utmCampaign,
          refererHeader,
        );
      } catch (e) {
        console.warn("[yatabase][signup] referrer record failed:", e);
      }
    }
    return new Response(
      JSON.stringify({
        ...podBody,
        emailStatus,
        welcome: recipientEmail
          ? `Welcome email queued to ${recipientEmail} (status: ${emailStatus}). Save your API key — yatabase does not show it again.`
          : "Save your API key — yatabase does not show it again. Paste it into Studio Settings → API key.",
      }),
      {
        status: 200,
        headers: {
          "content-type": "application/json",
          "x-yatabase-surface": "signup",
          "x-yatabase-signup-path": "lg-yatabase-pod",
          "cache-control": "no-store",
        },
      },
    );
  }

  // FALLBACK PATH (pre-cutover or pod unreachable): direct Hyperdrive.
  // Will fail with `Hyperdrive binding missing` when ADR-2605111200 is
  // enforced in @etzhayyim/magatama-host-sdk — that's by design; surfaces
  // the gap explicitly so the operator wires LG_YATABASE_URL.
  const db = await getDb(env);
  if (!db) {
    return new Response(
      JSON.stringify({
        error: "ServiceUnavailable",
        message: "Hyperdrive binding missing. Set LG_YATABASE_URL on the Worker to forward to the lg-yatabase pod (post-ADR-2605111200 path).",
      }),
      { status: 503, headers: { "content-type": "application/json" } },
    );
  }

  const ts = Date.now();
  const randSuffix = Math.floor(Math.random() * 1e9).toString(36) +
                     Math.floor(Math.random() * 1e9).toString(36);
  const orgDid = `did:web:t-${randSuffix.slice(0, 16)}.yata-tenant.etzhayyim.com`;
  const tenantName = `yata-tenant-${ts}`;

  const rawKey = generateApiKey();
  const keyHash = await sha256Hex(rawKey);
  const keyId = `apikey:${keyHash.slice(0, 16)}`;
  const aws = generateAwsAccessKey();
  const nowIso = new Date(ts).toISOString();

  try {
    await db.insertInto("vertex_api_key").values({
      vertex_id: keyId,
      owner_did: orgDid,
      key_hash: keyHash,
      key_prefix: "sk_live_yata_",
      name: tenantName,
      scopes: "atproto,include:app.etzhayyim.apps.yata",
      status: "active",
      product_scope: "yata",
      aws_access_key_id: aws.id,
      aws_secret_access_key: aws.secret,
      created_at: nowIso,
    }).execute();
  } catch (e) {
    console.warn("[yatabase][signup] vertex_api_key insert failed:", e);
    return new Response(
      JSON.stringify({
        error: "PersistFailed",
        message: e instanceof Error ? e.message.slice(0, 300) : "INSERT failed",
      }),
      { status: 500, headers: { "content-type": "application/json" } },
    );
  }

  // Fire welcome email (Resend if RESEND_API_KEY set, otherwise outbox-only).
  let emailStatus = "skipped-no-email";
  if (recipientEmail) {
    try {
      const sdk = await import("./email-outbox");
      const tpl = sdk.welcomeEmail(orgDid, rawKey, recipientName);
      const result = await sdk.emitOutbox(env, {
        orgDid,
        recipientEmail,
        recipientName,
        kind: "signup-welcome",
        subject: tpl.subject,
        bodyText: tpl.text,
        bodyHtml: tpl.html,
      });
      emailStatus = result.status;
    } catch (e) {
      emailStatus = "outbox-error";
      console.warn("[yatabase][signup] outbox emit failed:", e);
    }
  }
  // P45: record signup date for day-7 retention cron.
  if ((env as { YATABASE_AUTH_CACHE?: KVNamespace }).YATABASE_AUTH_CACHE) {
    try {
      await recordSignupIndex(
        (env as { YATABASE_AUTH_CACHE: KVNamespace }).YATABASE_AUTH_CACHE,
        orgDid,
        recipientEmail,
        recipientName,
      );
    } catch (e) {
      console.warn("[yatabase][signup] signup_index write failed:", e);
    }
    // Sprint 1 H1: referrer funnel tracking.
    try {
      const { recordReferrer } = await import("./referrer");
      await recordReferrer(env as never, orgDid, utmSource, utmMedium, utmCampaign, refererHeader);
    } catch (e) {
      console.warn("[yatabase][signup] referrer record failed:", e);
    }
  }

  return new Response(
    JSON.stringify({
      ok: true,
      apiKey: rawKey,
      keyId,
      orgDid,
      tenantName,
      awsAccessKeyId: aws.id,
      emailStatus,
      welcome: recipientEmail
        ? `Welcome email queued to ${recipientEmail} (status: ${emailStatus}). Save your API key — yatabase does not show it again.`
        : "Save your API key — yatabase does not show it again. Paste it into Studio Settings → API key.",
      next: "First Cypher call auto-provisions your tenant schema with a vertex_demo + welcome row.",
      pricing: "Free tier: $0/month. See Studio → Plan for upgrade options.",
    }),
    {
      status: 200,
      headers: {
        "content-type": "application/json",
        "x-yatabase-surface": "signup",
        "cache-control": "no-store",
      },
    },
  );
}
