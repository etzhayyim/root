import { Command } from 'commander';
import { execa } from 'execa';
import fs from 'fs/promises';
import path from 'path';
import { findRepoRoot } from '../lib/root.js';

async function applicatorDir(): Promise<string> {
  const root = await findRepoRoot();
  const dir = path.join(root, '70-tools', 'charter-rider-applicator');
  try {
    await fs.access(dir);
  } catch {
    throw new Error(`charter-rider-applicator missing at ${dir}`);
  }
  return dir;
}

export const charterCmd = new Command('charter').description('Charter Compliance Rider v2.0 ops (per ADR-2605192200)');

charterCmd
  .command('check')
  .description('Verify every Apache-2.0 sub-repo has correct NOTICE + CHARTER-RIDER.md symlink')
  .action(async () => {
    const dir = await applicatorDir();
    const script = path.join(dir, 'verify.sh');
    try {
      await execa('bash', [script], { stdio: 'inherit' });
    } catch (err: any) {
      process.exit(err?.exitCode ?? 1);
    }
  });

charterCmd
  .command('apply')
  .description('Apply NOTICE + CHARTER-RIDER.md symlink to every Apache-2.0 sub-repo')
  .action(async () => {
    const dir = await applicatorDir();
    const script = path.join(dir, 'apply.sh');
    try {
      await execa('bash', [script], { stdio: 'inherit' });
    } catch (err: any) {
      process.exit(err?.exitCode ?? 1);
    }
  });
