// binary/parse.ts — read a kami manifest from URL or local path.

import { readFileSync } from "node:fs";
import { resolve as resolvePath } from "node:path";

import { validateManifest, type KamiManifest } from "./types.js";

export async function readKamiManifest(sourceUrlOrPath: string): Promise<KamiManifest> {
  let raw: string;
  if (sourceUrlOrPath.startsWith("http://") || sourceUrlOrPath.startsWith("https://")) {
    const res = await fetch(sourceUrlOrPath);
    if (!res.ok) throw new Error(`fetch kami manifest failed: ${res.status} ${res.statusText}`);
    raw = await res.text();
  } else {
    raw = readFileSync(resolvePath(process.cwd(), sourceUrlOrPath), "utf-8");
  }
  const parsed = JSON.parse(raw);
  return validateManifest(parsed);
}
