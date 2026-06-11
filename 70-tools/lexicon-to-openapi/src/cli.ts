#!/usr/bin/env node

/**
 * CLI: Read AT Protocol Lexicon files and generate OpenAPI specs
 * Usage: lexicon-to-openapi [LEXICON_ROOT] [OUT_DIR]
 * Example: lexicon-to-openapi 00-contracts/lexicons/com/etzhayyim 90-docs/openapi
 */

import { readdir, readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join, basename } from "node:path";
import { lexiconsToOpenApi } from "./index.js";
import type { LexiconDoc } from "./types.js";

const LEXICON_ROOT = process.argv[2] ?? "00-contracts/lexicons/com/etzhayyim";
const OUT_DIR = process.argv[3] ?? "90-docs/openapi";

async function main() {
  try {
    const entries = await readdir(LEXICON_ROOT, { withFileTypes: true });
    let successCount = 0;

    for (const ent of entries) {
      if (!ent.isDirectory()) continue;
      if (ent.name.startsWith(".")) continue;

      const actorDir = join(LEXICON_ROOT, ent.name);
      const lexicons = await collectLexicons(actorDir);

      if (lexicons.length === 0) continue;

      const spec = lexiconsToOpenApi(lexicons, {
        title: `${ent.name} XRPC API`,
        version: "0.1.0",
        baseUrl: `https://${ent.name}.etzhayyim.com`,
      });

      const outPath = join(OUT_DIR, `${ent.name}.openapi.json`);
      await mkdir(dirname(outPath), { recursive: true });
      await writeFile(outPath, JSON.stringify(spec, null, 2));

      console.log(`✓ ${ent.name}: ${lexicons.length} lexicons → ${outPath}`);
      successCount++;
    }

    console.log(`\n✓ Generated ${successCount} OpenAPI specs`);
  } catch (e) {
    console.error("Error:", e);
    process.exit(1);
  }
}

async function collectLexicons(dir: string): Promise<LexiconDoc[]> {
  const out: LexiconDoc[] = [];
  const stack = [dir];

  while (stack.length > 0) {
    const cur = stack.pop()!;

    try {
      const entries = await readdir(cur, { withFileTypes: true });

      for (const e of entries) {
        const p = join(cur, e.name);

        if (e.isDirectory()) {
          stack.push(p);
        } else if (e.name.endsWith(".json")) {
          try {
            const txt = await readFile(p, "utf8");
            const parsed = JSON.parse(txt) as Record<string, unknown>;

            if (
              parsed.lexicon === 1 &&
              typeof parsed.id === "string" &&
              parsed.defs &&
              typeof parsed.defs === "object"
            ) {
              out.push(parsed as unknown as LexiconDoc);
            }
          } catch (parseErr) {
            // Skip unparseable files silently
          }
        }
      }
    } catch (readErr) {
      // Skip directories we can't read
    }
  }

  return out;
}

main().catch((e) => {
  console.error(e);
  process.exit(1);
});
