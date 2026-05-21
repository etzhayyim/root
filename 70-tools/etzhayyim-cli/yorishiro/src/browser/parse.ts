// browser/parse.ts — read a browser-only kami manifest (JSON).

import { readFileSync } from "node:fs";
import { resolve as resolvePath } from "node:path";

import { validateBrowserManifest, type BrowserKamiManifest } from "./types.js";

export async function readBrowserKamiManifest(sourceUrlOrPath: string): Promise<BrowserKamiManifest> {
  let raw: string;
  if (sourceUrlOrPath.startsWith("http://") || sourceUrlOrPath.startsWith("https://")) {
    const res = await fetch(sourceUrlOrPath);
    if (!res.ok) throw new Error(`fetch browser kami manifest failed: ${res.status} ${res.statusText}`);
    raw = await res.text();
  } else {
    raw = readFileSync(resolvePath(process.cwd(), sourceUrlOrPath), "utf-8");
  }
  return validateBrowserManifest(JSON.parse(raw));
}
