import { Command } from 'commander';
import { execa } from 'execa';
import path from 'path';
import fs from 'fs/promises';
import { findRepoRoot } from '../lib/root.js';

async function resolveWitDir(extension: boolean): Promise<string> {
  if (process.env.MAGATAMA_WIT_DIR) return process.env.MAGATAMA_WIT_DIR;
  const root = await findRepoRoot();
  return extension
    ? path.join(root, '10-protocol', 'wproto', 'wit')
    : path.join(root, '20-actors', 'magatama', 'wit');
}

export const actorCmd = new Command('actor').description('Manage Magatama/WASM Actors');

actorCmd
  .command('build <dir>')
  .description('Build WASM component')
  .option('--extension', 'Build as W Protocol extension')
  .action(async (dir: string, options: { extension?: boolean }) => {
    const compDir = path.resolve(process.cwd(), dir);
    try {
      const stats = await fs.stat(compDir);
      if (!stats.isDirectory()) throw new Error('not a directory');
    } catch {
      console.error(`Directory not found: ${compDir}`);
      process.exit(1);
    }

    const outputName = path.basename(compDir);
    const outputWasm = path.join(compDir, `${outputName}.wasm`);
    const buildDir = path.join(compDir, 'build');
    const coreWasm = path.join(buildDir, `${outputName}_core.wasm`);
    const embeddedWasm = path.join(buildDir, `${outputName}_embedded.wasm`);
    const witDir = await resolveWitDir(!!options.extension);
    const witWorld = options.extension ? 'etzhayyim:w/w-extension' : 'magatama:runtime/magatama-component';

    console.log(`>> Building actor ${outputName} (wit=${witDir}, world=${witWorld})`);

    try {
      await fs.mkdir(buildDir, { recursive: true });

      await execa('tinygo', [
        'build', '-target=wasip1', '-gc=leaking', '-buildmode=c-shared', '-no-debug',
        '-o', coreWasm, '.',
      ], { cwd: compDir, stdio: 'inherit' });

      await execa('wasm-tools', [
        'component', 'embed', '-w', witWorld, witDir, coreWasm, '-o', embeddedWasm,
      ], { cwd: compDir, stdio: 'inherit' });

      const adapter = path.join(compDir, '.cache', 'wasi_snapshot_preview1.reactor.wasm');
      const componentNewArgs = ['component', 'new', embeddedWasm];
      try {
        await fs.stat(adapter);
        componentNewArgs.push('--adapt', `wasi_snapshot_preview1=${adapter}`);
      } catch {
        console.log(`   (skip preview1 adapter: ${adapter} not found)`);
      }
      componentNewArgs.push('-o', outputWasm);
      await execa('wasm-tools', componentNewArgs, { cwd: compDir, stdio: 'inherit' });

      console.log(`OK ${path.basename(outputWasm)}`);
    } catch (err) {
      console.error('Actor build failed.', err);
      process.exit(1);
    } finally {
      await fs.unlink(coreWasm).catch(() => {});
      await fs.unlink(embeddedWasm).catch(() => {});
    }
  });

actorCmd
  .command('deploy <dir>')
  .description('Deploy actor to Cloudflare Containers (wrangler deploy) — legacy CF path')
  .action(async (dir: string) => {
    const compDir = path.resolve(process.cwd(), dir);
    console.log(`>> Deploying actor at ${compDir}`);
    try {
      await execa('npx', ['wrangler', 'deploy'], { cwd: compDir, stdio: 'inherit' });
      console.log('OK deployed.');
    } catch (err) {
      console.error('Actor deploy failed.', err);
      process.exit(1);
    }
  });

actorCmd
  .command('deploy-kotoba <wasm>')
  .description('Deploy a WASM actor the kotoba-premise way: content-address → pin to IPFS → register in the kotoba Datom log (Cloudflare-free, ADR-2606064500)')
  .option('--actor <handle>', 'actor handle (defaults to the wasm filename stem)')
  .option('--did <did>', 'actor DID (defaults to did:web:etzhayyim.com:actor:<handle>)')
  .option('--pin <mode>', 'IPFS pin mode: kubo | pinner | none', 'none')
  .option('--kubo <url>', 'kubo HTTP API for --pin kubo', 'http://127.0.0.1:5001')
  .option('--pinner-dir <dir>', 'ipfs-pinner data dir for --pin pinner')
  .option('--graph <graph>', 'kotoba graph (defaults to com.etzhayyim.<actor>)')
  .option('--kotoba <url>', 'kotoba node URL', 'http://127.0.0.1:8077')
  .option('--out <file>', 'deploy manifest output path')
  .action(async (
    wasm: string,
    opts: { actor?: string; did?: string; pin: string; kubo: string; pinnerDir?: string; graph?: string; kotoba: string; out?: string },
  ) => {
    const wasmPath = path.resolve(process.cwd(), wasm);
    try {
      await fs.stat(wasmPath);
    } catch {
      console.error(`WASM file not found: ${wasmPath}`);
      process.exit(1);
    }
    const root = await findRepoRoot();
    const deployScript = path.join(root, '50-infra', 'e7m-wasm-runner', 'deploy.mjs');
    const args = ['--file', wasmPath, '--pin', opts.pin, '--kubo', opts.kubo, '--kotoba', opts.kotoba];
    if (opts.actor) args.push('--actor', opts.actor);
    if (opts.did) args.push('--did', opts.did);
    if (opts.pinnerDir) args.push('--pinner-dir', opts.pinnerDir);
    if (opts.graph) args.push('--graph', opts.graph);
    if (opts.out) args.push('--out', opts.out);
    console.log(`>> kotoba-premise deploy: ${path.basename(wasmPath)} (pin=${opts.pin})`);
    if (!process.env.KOTOBA_TOKEN) {
      console.log('   (no KOTOBA_TOKEN → kotoba registration is a DRY RUN; no-server-key posture)');
    }
    try {
      // Node ≥ 23 strips the runner's .ts imports natively; no build step.
      await execa('node', [deployScript, ...args], { cwd: process.cwd(), stdio: 'inherit' });
    } catch (err) {
      console.error('kotoba deploy failed.', err);
      process.exit(1);
    }
  });
