/**
 * One-off: register junkawasaki.com as a did:etzhayyim actor DID profile.
 *
 * Steps:
 *   1. Ed25519 keypair (node:crypto)
 *   2. Multikey encoding (0xED 0x01 + base58btc)
 *   3. Genesis op → CIDv1 → did:etzhayyim
 *   4. Private key JWK → macOS Keychain (etzhayyim.identity / junkawasaki.com)
 *   5. INSERT vertex_etzhayyim_identity + vertex_actor_profile + vertex_etzhayyim_op_log
 */
import crypto from "node:crypto";
import { execSync } from "node:child_process";
import pg from "pg";
import { createGenesis } from "../../../10-protocol/did-etzhayyim/src/genesis.js";
import { multibaseEncode } from "../../../10-protocol/did-etzhayyim/src/multibase.js";

const HANDLE = "junkawasaki.com";
const DISPLAY_NAME = "Jun Kawasaki";
const DESCRIPTION = "Founder @ etzhayyim Japan";
const COUNTRY = "JP";

async function main() {
  const url = process.env.DATABASE_URL;
  if (!url) throw new Error("DATABASE_URL required");

  // ── 1. Ed25519 keypair ─────────────────────────────────────────────
  const { publicKey, privateKey } = crypto.generateKeyPairSync("ed25519");
  const pubJwk = publicKey.export({ format: "jwk" }) as { x: string };
  const privJwk = privateKey.export({ format: "jwk" });
  const rawPub = new Uint8Array(Buffer.from(pubJwk.x, "base64url")); // 32 bytes

  // ── 2. Multikey (multicodec ed25519-pub = 0xED 0x01) ───────────────
  const multikeyBytes = new Uint8Array(34);
  multikeyBytes[0] = 0xed;
  multikeyBytes[1] = 0x01;
  multikeyBytes.set(rawPub, 2);
  const publicKeyMultibase = multibaseEncode("z", multikeyBytes);

  // ── 3. Genesis op → did:etzhayyim ───────────────────────────────────────
  const createdAt = new Date().toISOString();
  const genesis = await createGenesis({
    type: "root",
    vm: [{ id: "#key-0", type: "Multikey", publicKeyMultibase }],
    alsoKnownAs: [`at://${HANDLE}`, `https://${HANDLE}`],
    createdAt,
  });

  console.log("DID:            ", genesis.did);
  console.log("handle:         ", HANDLE);
  console.log("publicKey:      ", publicKeyMultibase);
  console.log("genesis op CID: ", genesis.cidString);
  console.log("depth:          ", genesis.depth);

  // ── 4. Private key → macOS Keychain ────────────────────────────────
  const privJson = JSON.stringify(privJwk);
  try {
    execSync(
      `security add-generic-password -s etzhayyim.identity -a ${HANDLE} -w ${JSON.stringify(privJson)} -U`,
      { stdio: ["ignore", "ignore", "pipe"] },
    );
    console.log("privKey stored: macOS Keychain (etzhayyim.identity / junkawasaki.com)");
  } catch (e: any) {
    console.error("Keychain write failed:", e.message);
  }

  // ── 5. INSERT into RisingWave ──────────────────────────────────────
  const pool = new pg.Pool({ connectionString: url, max: 2 });
  try {
    const existing = await pool.query(
      `SELECT did FROM vertex_etzhayyim_identity WHERE handle = $1 OR did = $2 LIMIT 1`,
      [HANDLE, genesis.did],
    );
    if ((existing.rowCount ?? 0) > 0) {
      console.log("SKIP: already registered:", existing.rows[0].did);
      return;
    }

    const nowIso = new Date().toISOString();
    const today = nowIso.slice(0, 10);

    await pool.query(
      `INSERT INTO vertex_etzhayyim_identity (
        vertex_id, did, entity_type, performer_type, handle,
        display_name, description, controller_did,
        public_key_multibase, status, pii_tier,
        parent_did, depth, root_did, path_segment,
        cid_version, multicodec, multihash_code, multibase_prefix, genesis_op_cid,
        created_at, updated_at,
        _seq, created_date, sensitivity_ord, owner_did
      ) VALUES (
        $1, $1, 'person', 'person', $2,
        $3, $4, $1,
        $5, 'active', 3,
        NULL, 0, $1, NULL,
        1, 'raw', 'sha2-256', 'b', $6,
        $7, $7,
        0, $8, 3, $1
      )`,
      [genesis.did, HANDLE, DISPLAY_NAME, DESCRIPTION, publicKeyMultibase, genesis.cidString, nowIso, today],
    );
    console.log("INSERT vertex_etzhayyim_identity OK");

    await pool.query(
      `INSERT INTO vertex_actor_profile (
        vertex_id, did, handle, display_name, description,
        execution_tier, performer_type, country, status,
        created_at, _seq, created_date, sensitivity_ord, owner_did
      ) VALUES (
        $1, $1, $2, $3, $4,
        'T0', 'person', $5, 'active',
        $6, 0, $7, 3, $1
      )`,
      [genesis.did, HANDLE, DISPLAY_NAME, DESCRIPTION, COUNTRY, nowIso, today],
    );
    console.log("INSERT vertex_actor_profile OK");

    await pool.query(
      `INSERT INTO vertex_etzhayyim_op_log (
        vertex_id, did, op_seq, op_type, op_cid, prev_cid,
        op_cbor_hex, sig, sig_kid, created_at,
        _seq, created_date, sensitivity_ord, owner_did
      ) VALUES (
        $1, $2, 0, 'create', $3, NULL,
        $4, NULL, $5, $6,
        0, $7, 3, $2
      )`,
      [
        `${genesis.did}:0`,
        genesis.did,
        genesis.cidString,
        Buffer.from(genesis.cborBytes).toString("hex"),
        `${genesis.did}#key-0`,
        nowIso,
        today,
      ],
    );
    console.log("INSERT vertex_etzhayyim_op_log OK");

    await pool.query("FLUSH");

    const check = await pool.query(
      `SELECT did, handle, display_name, execution_tier, public_key_multibase, depth
       FROM view_actor_unified WHERE did = $1`,
      [genesis.did],
    );
    console.log("view_actor_unified round-trip:", check.rows[0]);
  } finally {
    await pool.end();
  }
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
