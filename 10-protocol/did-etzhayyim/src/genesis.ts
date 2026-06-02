/**
 * did:etzhayyim genesis operation (ADR-0029).
 *
 * Genesis op shape (canonical DAG-CBOR):
 *   {
 *     v:           1,
 *     type:        "root" | "child",
 *     parent:      "<parent did:etzhayyim | null>",
 *     segment:     "<utf-8 segment string | null>",
 *     vm:          [ { id, type, publicKeyMultibase } ],
 *     alsoKnownAs: [ "at://...", "did:web:..." ],
 *     service:     [],
 *     createdAt:   "<RFC 3339>"
 *   }
 *
 * DID derivation:
 *   cid = CIDv1(raw, sha2-256, dag_cbor_canonical(genesis_op))
 *   did = "did:etzhayyim:" + cid_string                 (root)
 *       | parent_did + ":" + cid_string            (child)
 */

import { encodeCanonicalCbor, type CborValue } from "./cbor";
import { createCidV1, type CIDv1, cidv1ToString } from "./cid";

export const DID_etzhayyim_PREFIX = "did:etzhayyim:";
export const MAX_PATH_DEPTH = 6;

export interface VerificationMethodInput {
  id: string;                  // e.g. "#key-1"
  type: "Multikey";
  publicKeyMultibase: string;  // e.g. "z..."
}

export interface RootGenesisInput {
  type: "root";
  vm: VerificationMethodInput[];
  alsoKnownAs?: string[];
  service?: CborValue[];
  createdAt: string;
}

export interface ChildGenesisInput {
  type: "child";
  parent: string;        // did:etzhayyim of the immediate parent (depth ≥ 0, < MAX_PATH_DEPTH)
  segment: string;       // UTF-8 segment, e.g. "wiki:1968_flu_pandemic"
  vm: VerificationMethodInput[];
  alsoKnownAs?: string[];
  service?: CborValue[];
  createdAt: string;
}

export type GenesisInput = RootGenesisInput | ChildGenesisInput;

export interface GenesisResult {
  did: string;
  parent: string | null;
  segment: string | null;
  depth: number;
  cid: CIDv1;
  cidString: string;
  cborBytes: Uint8Array;
  op: Record<string, CborValue>;
}

export function isValidDidetzhayyim(did: string): boolean {
  if (!did.startsWith(DID_etzhayyim_PREFIX)) return false;
  const tail = did.slice(DID_etzhayyim_PREFIX.length);
  if (tail.length === 0) return false;
  const segs = tail.split(":");
  if (segs.length === 0 || segs.length > MAX_PATH_DEPTH + 1) return false;
  for (const seg of segs) {
    if (!/^[a-zA-Z0-9]+$/.test(seg)) return false;  // multibase alphanumeric body
  }
  return true;
}

export function didDepth(did: string): number {
  if (!did.startsWith(DID_etzhayyim_PREFIX)) throw new Error(`not a did:etzhayyim: ${did}`);
  return did.slice(DID_etzhayyim_PREFIX.length).split(":").length - 1;
}

export function didParent(did: string): string | null {
  const depth = didDepth(did);
  if (depth === 0) return null;
  const idx = did.lastIndexOf(":");
  return did.slice(0, idx);
}

export function didRoot(did: string): string {
  if (!did.startsWith(DID_etzhayyim_PREFIX)) throw new Error(`not a did:etzhayyim: ${did}`);
  const tail = did.slice(DID_etzhayyim_PREFIX.length);
  const rootSeg = tail.split(":")[0];
  return DID_etzhayyim_PREFIX + rootSeg;
}

function buildCanonicalOp(input: GenesisInput): Record<string, CborValue> {
  const isRoot = input.type === "root";
  const op: Record<string, CborValue> = {
    v: 1,
    type: input.type,
    parent: isRoot ? null : (input as ChildGenesisInput).parent,
    segment: isRoot ? null : (input as ChildGenesisInput).segment,
    vm: input.vm.map((m) => ({
      id: m.id,
      type: m.type,
      publicKeyMultibase: m.publicKeyMultibase,
    })),
    alsoKnownAs: input.alsoKnownAs ?? [],
    service: input.service ?? [],
    createdAt: input.createdAt,
  };
  return op;
}

export async function createGenesis(input: GenesisInput): Promise<GenesisResult> {
  if (input.type === "child") {
    if (!isValidDidetzhayyim(input.parent)) throw new Error(`invalid parent did:etzhayyim: ${input.parent}`);
    if (didDepth(input.parent) >= MAX_PATH_DEPTH) {
      throw new Error(`MAX_PATH_DEPTH exceeded (${MAX_PATH_DEPTH})`);
    }
    if (input.segment.length === 0) throw new Error("child segment must be non-empty");
  }
  if (input.vm.length === 0) throw new Error("genesis op requires at least one verificationMethod");

  const op = buildCanonicalOp(input);
  const cborBytes = encodeCanonicalCbor(op);
  const cid = await createCidV1(cborBytes, { codec: "raw", multihash: "sha2-256", multibase: "b" });
  const cidString = cidv1ToString(cid);

  const did = input.type === "root"
    ? DID_etzhayyim_PREFIX + cidString
    : (input as ChildGenesisInput).parent + ":" + cidString;

  const depth = input.type === "root" ? 0 : didDepth((input as ChildGenesisInput).parent) + 1;

  return {
    did,
    parent: input.type === "root" ? null : (input as ChildGenesisInput).parent,
    segment: input.type === "root" ? null : (input as ChildGenesisInput).segment,
    depth,
    cid,
    cidString,
    cborBytes,
    op,
  };
}

export async function verifyGenesis(did: string, op: Record<string, CborValue>): Promise<boolean> {
  if (!isValidDidetzhayyim(did)) return false;
  const cidString = did.split(":").pop()!;
  const cborBytes = encodeCanonicalCbor(op);
  const cid = await createCidV1(cborBytes, { codec: "raw", multihash: "sha2-256", multibase: "b" });
  return cidv1ToString(cid) === cidString;
}
