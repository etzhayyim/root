import { Command } from 'commander';
import { execa } from 'execa';
import { findRepoRoot } from '../lib/root.js';

type Check = { name: string; argv: string[]; note?: string };

const CHECKS: Check[] = [
  { name: 'node',       argv: ['node', '--version'] },
  { name: 'pnpm',       argv: ['pnpm', '--version'] },
  { name: 'npm',        argv: ['npm', '--version'] },
  { name: 'tinygo',     argv: ['tinygo', 'version'],    note: 'required for actor build' },
  { name: 'wasm-tools', argv: ['wasm-tools', '--version'], note: 'required for actor build' },
  { name: 'wrangler',   argv: ['npx', '-y', 'wrangler', '--version'], note: 'required for actor deploy / CF Worker' },
  { name: 'docker',     argv: ['docker', '--version'],   note: 'required for dev infra' },
  { name: 'forge',      argv: ['forge', '--version'],    note: 'foundry — required for chain contracts' },
  { name: 'anvil',      argv: ['anvil', '--version'],    note: 'foundry — required for local L2 smoke' },
  { name: 'cast',       argv: ['cast', '--version'],     note: 'foundry — required for chain calls' },
  { name: 'go',         argv: ['go', 'version'],         note: 'used by some tools / etzhayyim-cli Go scaffold' },
];

async function runCheck(c: Check): Promise<{ ok: boolean; out: string }> {
  try {
    const r = await execa(c.argv[0], c.argv.slice(1), { stdio: 'pipe', timeout: 15_000 });
    const first = (r.stdout || r.stderr || '').split('\n')[0].trim();
    return { ok: true, out: first };
  } catch (err: any) {
    return { ok: false, out: err?.shortMessage ?? String(err) };
  }
}

export const doctorCmd = new Command('doctor')
  .description('Diagnose local tool dependencies for the etzhayyim monorepo')
  .action(async () => {
    let root: string;
    try {
      root = await findRepoRoot();
      console.log(`repo root: ${root}`);
    } catch (e) {
      console.log(`repo root: (not found) — ${(e as Error).message}`);
    }
    console.log('');
    let missing = 0;
    for (const c of CHECKS) {
      const r = await runCheck(c);
      const status = r.ok ? 'OK  ' : 'MISS';
      const line = `${status}  ${c.name.padEnd(11)}  ${r.ok ? r.out : (c.note ?? '')}`;
      console.log(line);
      if (!r.ok) missing++;
    }
    console.log('');
    console.log(`${CHECKS.length - missing} / ${CHECKS.length} tools present`);
    if (missing > 0) process.exitCode = 1;
  });
