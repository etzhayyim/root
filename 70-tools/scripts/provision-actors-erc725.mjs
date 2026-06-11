#!/usr/bin/env node
/**
 * Provision ERC725 root identities for the 3 new actors:
 *   nogu (農具・農機具), kogu (工具・設備), sekkei (設計図)
 *
 * For each actor:
 *   1. POST /internal/provision-root-identity with
 *      { stableId: "actor:<name>", label: <name>, facadeDids: [did:web] }
 *   2. authz deploys etzhayyimRootIdentity on chain 260425 and links the
 *      did:web facade so resolveFacade(keccak256(did:web)) → ERC725 root.
 *   3. Logs (did:web → did:erc725, identityAddress, txHash).
 *
 * Update deps.toml [[mitama_actors]] erc725_root_pending=false and
 * add erc725_did after running with --apply.
 *
 * Usage:
 *   node 70-tools/scripts/provision-actors-erc725.mjs           (dry-run)
 *   node 70-tools/scripts/provision-actors-erc725.mjs --apply
 *
 * Required (macOS Keychain):
 *   security find-generic-password -s etzhayyim.cloudflare -a CLAIM_SETTLER_HMAC -w
 */
import { createHmac } from "node:crypto";

const args = Object.fromEntries(
  process.argv.slice(2).flatMap((a) => (a.startsWith("--") ? [[a.slice(2), true]] : []))
);
const apply = !!args.apply;
const authzBase = (process.env.AUTHZ_BASE_URL ?? "https://authz.etzhayyim.com").replace(/\/+$/, "");

const ACTORS = [
  {
    name: "nogu",
    facadeDid: "did:web:nogu.etzhayyim.com",
    label: "農具・農機具 Registry",
    stableId: "actor:nogu",
  },
  {
    name: "kogu",
    facadeDid: "did:web:kogu.etzhayyim.com",
    label: "工具・設備 Registry",
    stableId: "actor:kogu",
  },
  {
    name: "sekkei",
    facadeDid: "did:web:sekkei.etzhayyim.com",
    label: "設計図・技術文書 Registry",
    stableId: "actor:sekkei",
  },
];

function sign(body, hmac) {
  return createHmac("sha256", hmac).update(body).digest("hex");
}

async function provisionActor(actor, hmac) {
  const payload = JSON.stringify({
    stableId: actor.stableId,
    label: actor.label,
    facadeDids: [actor.facadeDid],
  });
  const sig = sign(payload, hmac);

  if (!apply) {
    console.log(`[dry-run] POST /internal/provision-root-identity`, JSON.parse(payload));
    return null;
  }

  const resp = await fetch(`${authzBase}/internal/provision-root-identity`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-claim-settler-auth": sig },
    body: payload,
  });
  const text = await resp.text();
  if (!resp.ok) throw new Error(`HTTP ${resp.status}: ${text.slice(0, 300)}`);
  return JSON.parse(text);
}

async function main() {
  const { execSync } = await import("node:child_process");

  const hmac = process.env.CLAIM_SETTLER_HMAC?.trim() || (() => {
    try {
      return execSync('security find-generic-password -s "etzhayyim.cloudflare" -a "CLAIM_SETTLER_HMAC" -w', {
        stdio: ["pipe", "pipe", "pipe"],
      }).toString().trim();
    } catch { return ""; }
  })();

  if (!hmac) {
    console.error("ERROR: CLAIM_SETTLER_HMAC missing.");
    console.error('  security add-generic-password -s "etzhayyim.cloudflare" -a "CLAIM_SETTLER_HMAC" -w "<hex>" -U');
    process.exit(2);
  }

  console.log(`mode      = ${apply ? "APPLY" : "dry-run"}`);
  console.log(`authzBase = ${authzBase}`);
  console.log();

  const results = [];

  for (const actor of ACTORS) {
    console.log(`→ ${actor.name} (${actor.facadeDid})`);
    try {
      const result = await provisionActor(actor, hmac);
      if (result) {
        console.log(`  rootDid  = ${result.rootDid}`);
        console.log(`  address  = ${result.identityAddress}`);
        console.log(`  tx       = ${result.txHash}`);
        results.push({ ...actor, rootDid: result.rootDid, identityAddress: result.identityAddress });
      } else {
        console.log(`  (dry-run skipped)`);
        results.push({ ...actor, rootDid: null });
      }
    } catch (err) {
      console.error(`  ERROR: ${err.message}`);
      results.push({ ...actor, rootDid: null, error: err.message });
    }
    console.log();
  }

  if (apply && results.some((r) => r.rootDid)) {
    console.log("── deps.toml updates needed ──────────────────────────────");
    for (const r of results) {
      if (r.rootDid) {
        console.log(`[[mitama_actors]] name="${r.name}"`);
        console.log(`  erc725_did = "${r.rootDid}"`);
        console.log(`  erc725_root_pending = false`);
        console.log();
      }
    }
  }
}

main().catch((err) => { console.error(err); process.exit(1); });
