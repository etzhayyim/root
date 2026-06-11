/**
 * @etzhayyim/lexicons-bundle — runtime @atproto/lexicon Lexicons instance built
 * from 00-contracts/lexicons (SSoT). Used for XRPC client/server validation
 * so that yoro extension fields (performerType, viewerFollowing, nanoid, ...)
 * pass strict validation instead of triggering a fallback path that hides bugs.
 */
import { Lexicons, type LexiconDoc } from "@atproto/lexicon";
import bundle from "./lexicons.gen.json" with { type: "json" };

let _lex: Lexicons | null = null;

/** Returns the shared Lexicons instance (lazy-initialised). */
export function getLexicons(): Lexicons {
  if (_lex) return _lex;
  const docs = bundle as unknown as LexiconDoc[];
  _lex = new Lexicons(docs);
  return _lex;
}

/** Total lexicon doc count in the bundle (for diagnostics). */
export function bundleSize(): number {
  return (bundle as unknown as LexiconDoc[]).length;
}

/** Re-export type for downstream consumers. */
export type { LexiconDoc, Lexicons };
