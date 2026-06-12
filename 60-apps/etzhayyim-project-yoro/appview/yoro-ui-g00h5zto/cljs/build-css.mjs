// Build Tailwind CSS for the cljs UI using the svelte package's local
// tailwindcss v4 (@tailwindcss/postcss) — no CDN, no extra install.
// Usage: node build-css.mjs   (or: pnpm css)
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { createRequire } from 'node:module';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const here = path.dirname(fileURLToPath(import.meta.url));
const svelteDir = path.join(here, '..', 'svelte');
const require = createRequire(path.join(svelteDir, 'package.json'));
const postcss = require('postcss');
const tailwindcss = require('@tailwindcss/postcss');

const input = path.join(svelteDir, 'cljs-tailwind.css');
const output = path.join(here, 'public', 'css', 'tailwind.css');

const css = await readFile(input, 'utf8');
const result = await postcss([tailwindcss()]).process(css, { from: input, to: output });
await mkdir(path.dirname(output), { recursive: true });
await writeFile(output, result.css);
console.log(`wrote ${output} (${result.css.length} bytes)`);
