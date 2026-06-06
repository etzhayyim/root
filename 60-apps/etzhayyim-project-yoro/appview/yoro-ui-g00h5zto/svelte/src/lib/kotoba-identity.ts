/**
 * kotoba-identity.ts — bind the in-page kotoba signing key to the member's
 * passkey via the WebAuthn PRF (hmac-secret) extension.
 *
 * The kotoba Service Worker signs every committed root with an ed25519 key
 * (no-server-key, ADR-2605231525). By default that key is SW-local and
 * ephemeral. This derives a STABLE 32-byte seed from the member's passkey —
 * `prf.results.first` for a fixed app salt is deterministic per credential and
 * never leaves the device — and hands it to the SW (`setIdentity`), so commits
 * are signed by the MEMBER's own authenticator-bound key.
 *
 * R0 honesty: requires a PRF-capable authenticator + a passkey registered for
 * etzhayyim.com. Where PRF is unavailable the SW keeps its local key (the write
 * path still works). This is the page-side derivation; the registration ceremony
 * (creating a prf-enabled credential) is handled by the existing passkey flow.
 */

const PRF_SALT_LABEL = "etzhayyim:kotoba-identity:v1";

function toHex(buf: ArrayBuffer): string {
  return Array.from(new Uint8Array(buf), (b) => b.toString(16).padStart(2, "0")).join("");
}

async function prfSalt(): Promise<Uint8Array> {
  // Fixed, app-specific salt → deterministic per-credential secret across calls.
  const d = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(PRF_SALT_LABEL));
  return new Uint8Array(d);
}

/** True if the browser exposes WebAuthn + (best-effort) PRF. Real PRF support is
 *  only known after an assertion, so this is a necessary-not-sufficient gate. */
export function passkeyIdentityAvailable(): boolean {
  return (
    typeof window !== "undefined" &&
    !!window.PublicKeyCredential &&
    !!navigator.credentials &&
    typeof navigator.credentials.get === "function"
  );
}

/** Derive the 32-byte kotoba seed (hex) from the member's passkey via PRF.
 *  Returns null if PRF is unavailable / the user cancels. Prompts for the
 *  passkey (user verification), so call on an explicit user action. */
export async function derivePasskeySeed(): Promise<string | null> {
  if (!passkeyIdentityAvailable()) return null;
  try {
    const challenge = crypto.getRandomValues(new Uint8Array(32));
    const assertion = (await navigator.credentials.get({
      publicKey: {
        challenge,
        rpId: location.hostname.replace(/^www\./, ""),
        userVerification: "preferred",
        // Discoverable credential — no allowCredentials needed.
        extensions: { prf: { eval: { first: await prfSalt() } } } as AuthenticationExtensionsClientInputs,
      },
    })) as PublicKeyCredential | null;
    if (!assertion) return null;
    const ext = assertion.getClientExtensionResults() as {
      prf?: { results?: { first?: ArrayBuffer } };
    };
    const first = ext.prf?.results?.first;
    if (!first || first.byteLength < 32) return null; // authenticator lacks PRF
    return toHex(first.slice(0, 32)); // 32-byte ed25519 seed
  } catch {
    return null; // user cancelled / no credential / PRF unsupported
  }
}

/** Hand a 32-byte seed (hex) to the kotoba Service Worker; it persists + uses it
 *  to sign commits. Returns the resulting did:key (or null). */
export async function setKotobaIdentity(seedHex: string): Promise<string | null> {
  if (!("serviceWorker" in navigator)) return null;
  const reg = await navigator.serviceWorker.ready;
  const target = reg.active || navigator.serviceWorker.controller;
  if (!target) return null;
  return new Promise((resolve) => {
    const ch = new MessageChannel();
    ch.port1.onmessage = (e) => resolve(e.data && e.data.ok ? e.data.did : null);
    target.postMessage({ type: "setIdentity", seedHex }, [ch.port2]);
    setTimeout(() => resolve(null), 5000);
  });
}

/** One-shot: derive from the passkey and bind into the SW. Returns the member
 *  did:key on success, null otherwise. Call from an explicit "sign my edits with
 *  my passkey" UI action (it prompts for the passkey). */
export async function bindPasskeyIdentity(): Promise<string | null> {
  const seed = await derivePasskeySeed();
  if (!seed) return null;
  const did = await setKotobaIdentity(seed);
  if (did) {
    try {
      localStorage.setItem("kotoba-passkey-identity", "1");
    } catch {
      /* ignore */
    }
  }
  return did;
}

/** Opportunistic rebind on load IF the member already opted in (so the SW key
 *  stays the passkey-derived one across SW restarts). No-op otherwise — never
 *  prompts unprompted. */
export async function maybeRebindPasskeyIdentity(): Promise<void> {
  try {
    if (localStorage.getItem("kotoba-passkey-identity") !== "1") return;
    await bindPasskeyIdentity();
  } catch {
    /* best-effort */
  }
}
