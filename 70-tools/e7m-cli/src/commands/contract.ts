import { Command } from 'commander';
import { execa } from 'execa';
import fs from 'fs/promises';
import path from 'path';
import { resolveLayer } from '../lib/root.js';

export const contractCmd = new Command('contract').description('Manage Contracts (Lexicon, JSON Schema, BPMN)');

async function walkJson(dir: string, out: string[] = []): Promise<string[]> {
  let entries;
  try {
    entries = await fs.readdir(dir, { withFileTypes: true });
  } catch { return out; }
  for (const e of entries) {
    const full = path.join(dir, e.name);
    if (e.isDirectory()) await walkJson(full, out);
    else if (e.isFile() && e.name.endsWith('.json')) out.push(full);
  }
  return out;
}

contractCmd
  .command('gen')
  .argument('<kind>', 'lexicons | schemas')
  .description('Generate types from contracts. Currently: lexicons (via @atproto/lex-cli).')
  .option('-o, --out <dir>', 'output directory (relative to repo root)', 'orgs/etzhayyim/com-etzhayyim-sdk/src/generated')
  .action(async (kind: string, opts: { out: string }) => {
    if (kind !== 'lexicons') {
      console.error(`Unsupported kind: ${kind}. Supported: lexicons`);
      process.exit(2);
    }
    const contracts = await resolveLayer('00-contracts');
    const lexiconsDir = path.join(contracts, 'lexicons');
    const outDir = path.isAbsolute(opts.out) ? opts.out : path.join(await resolveLayer('20-actors'), '..', opts.out);
    console.log(`>> lex-cli gen ${lexiconsDir} -> ${outDir}`);
    try {
      await execa('npx', ['-y', '@atproto/lex-cli', 'gen-api', outDir, `${lexiconsDir}/**/*.json`], {
        stdio: 'inherit',
      });
      console.log('OK lexicons generated.');
    } catch (err) {
      console.error('Lexicon generation failed (is @atproto/lex-cli available?).', err);
      process.exit(1);
    }
  });

contractCmd
  .command('validate [target]')
  .description('Validate lexicons / schemas as parseable JSON. Default: 00-contracts/lexicons + 00-contracts/schemas.')
  .action(async (target?: string) => {
    const contracts = await resolveLayer('00-contracts');
    const roots = target
      ? [path.resolve(process.cwd(), target)]
      : [path.join(contracts, 'lexicons'), path.join(contracts, 'schemas')];

    let ok = 0;
    const bad: { file: string; error: string }[] = [];
    for (const r of roots) {
      const files = await walkJson(r);
      for (const f of files) {
        try {
          const raw = await fs.readFile(f, 'utf8');
          JSON.parse(raw);
          ok++;
        } catch (e) {
          bad.push({ file: f, error: (e as Error).message });
        }
      }
    }
    console.log(`OK ${ok} files parsed`);
    if (bad.length) {
      console.log(`FAIL ${bad.length} files:`);
      for (const b of bad) console.log(`   ${b.file}: ${b.error}`);
      process.exit(1);
    }
  });
