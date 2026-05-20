import { Command } from 'commander';
import { execa } from 'execa';
import fs from 'fs/promises';
import path from 'path';
import { resolveApp, resolveLayer } from '../lib/root.js';

export const devCmd = new Command('dev').description('Workspace & Development Environment Management');

devCmd
  .command('infra [service]')
  .description('Start local dependency infrastructure. service= lancedb | yata | all (default: all)')
  .option('--down', 'Stop instead of start')
  .action(async (service: string | undefined, opts: { down?: boolean }) => {
    const infra = await resolveLayer('50-infra');
    const compose: { name: string; file: string }[] = [
      { name: 'lancedb', file: path.join(infra, 'lancedb-wasm', 'docker-compose.yml') },
      { name: 'yata', file: path.join(infra, 'yata', 'docker-compose.test.yml') },
    ];
    const targets = !service || service === 'all'
      ? compose
      : compose.filter((c) => c.name === service);
    if (targets.length === 0) {
      console.error(`Unknown service: ${service}. Available: ${compose.map((c) => c.name).join(', ')}, all`);
      process.exit(2);
    }
    const action = opts.down ? 'down' : 'up';
    const args = opts.down ? ['compose', '-f', '<file>', 'down'] : ['compose', '-f', '<file>', 'up', '-d'];
    for (const t of targets) {
      try { await fs.access(t.file); } catch {
        console.log(`-- skip ${t.name} (file missing: ${t.file})`);
        continue;
      }
      console.log(`>> docker ${action} ${t.name}`);
      const a = args.map((x) => (x === '<file>' ? t.file : x));
      try {
        await execa('docker', a, { stdio: 'inherit' });
      } catch (err) {
        console.error(`docker compose ${action} failed for ${t.name}.`, err);
        process.exit(1);
      }
    }
  });

devCmd
  .command('app <projectName>')
  .description('Start dev server for app under 60-apps/. Tries pnpm dev, npm run dev.')
  .action(async (projectName: string) => {
    const cwd = await resolveApp(projectName);
    const pkgPath = path.join(cwd, 'package.json');
    try { await fs.access(pkgPath); } catch {
      console.error(`No package.json at ${cwd}. Cannot run dev.`);
      process.exit(1);
    }
    const pkg = JSON.parse(await fs.readFile(pkgPath, 'utf8')) as { scripts?: Record<string, string> };
    if (!pkg.scripts || !pkg.scripts.dev) {
      console.error(`No 'dev' script in ${pkgPath}.`);
      process.exit(1);
    }
    const runner = (await execa('which', ['pnpm']).then((r) => r.exitCode === 0).catch(() => false)) ? 'pnpm' : 'npm';
    const args = runner === 'pnpm' ? ['dev'] : ['run', 'dev'];
    console.log(`>> ${runner} ${args.join(' ')} (in ${cwd})`);
    try {
      await execa(runner, args, { cwd, stdio: 'inherit' });
    } catch (err) {
      console.error(`dev failed.`, err);
      process.exit(1);
    }
  });
