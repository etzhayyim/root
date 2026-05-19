import { Command } from 'commander';
import { execa } from 'execa';
import path from 'path';
import fs from 'fs/promises';

export const actorCmd = new Command('actor')
  .description('Manage Magatama/WASM Actors');

actorCmd
  .command('build <dir>')
  .description('Build WASM component')
  .option('--extension', 'Build as W Protocol extension')
  .option('--no-svelte', 'Skip svelte/pnpm build')
  .action(async (dir: string, options: { extension?: boolean; svelte?: boolean }) => {
    const compDir = path.resolve(process.cwd(), dir);
    console.log(`🔨 Building Actor at ${compDir}...`);

    try {
      const stats = await fs.stat(compDir);
      if (!stats.isDirectory()) {
        throw new Error(`${compDir} is not a directory`);
      }
    } catch {
      console.error(`❌ Directory not found: ${compDir}`);
      process.exit(1);
    }

    const outputName = path.basename(compDir);
    const outputWasm = path.join(compDir, `${outputName}.wasm`);
    const buildDir = path.join(compDir, 'build');
    const coreWasm = path.join(buildDir, `${outputName}_core.wasm`);
    const embeddedWasm = path.join(buildDir, `${outputName}_embedded.wasm`);
    
    // Auto-detect WIT Dir (simplified for e7m)
    let witDir = process.env.MAGATAMA_WIT_DIR;
    if (!witDir) {
      // Traverse up to find root
      witDir = path.resolve(compDir, '../../10-protocol/wproto/wit'); // Defaulting to wproto for now, can be improved
      if (options.extension) {
        console.log('Building as W Protocol extension...');
      }
    }

    try {
      await fs.mkdir(buildDir, { recursive: true });

      // Step 1: TinyGo build
      console.log(`==> tinygo build -> ${path.basename(coreWasm)}`);
      await execa('tinygo', [
        'build',
        '-target=wasip1',
        '-gc=leaking',
        '-buildmode=c-shared',
        '-no-debug',
        '-o', coreWasm,
        '.'
      ], { cwd: compDir, stdio: 'inherit' });

      // Step 2: Wasm-tools embed
      const witWorld = options.extension ? 'gftd:w/w-extension' : 'magatama:runtime/magatama-component';
      console.log(`==> wasm-tools component embed (world: ${witWorld})`);
      await execa('wasm-tools', [
        'component', 'embed',
        '-w', witWorld,
        witDir,
        coreWasm,
        '-o', embeddedWasm
      ], { cwd: compDir, stdio: 'inherit' });

      // Step 3: Wasm-tools new
      console.log(`==> wasm-tools component new -> ${path.basename(outputWasm)}`);
      // Note: In real life we'd need to download the adapter. Using a dummy/local path for scaffold.
      const adapter = path.resolve(compDir, '.cache/wasi_snapshot_preview1.reactor.wasm');
      
      const componentNewArgs = ['component', 'new', embeddedWasm];
      // Only add adapt if adapter exists
      try {
        await fs.stat(adapter);
        componentNewArgs.push('--adapt', `wasi_snapshot_preview1=${adapter}`);
      } catch {
        console.log(`  (Skipping WASI preview1 adapter: ${adapter} not found)`);
      }
      componentNewArgs.push('-o', outputWasm);

      await execa('wasm-tools', componentNewArgs, { cwd: compDir, stdio: 'inherit' });

      console.log(`✅ Successfully built ${path.basename(outputWasm)}`);

    } catch (error) {
      console.error('❌ Actor build failed.', error);
      process.exit(1);
    } finally {
      // Cleanup
      try {
        await fs.unlink(coreWasm);
        await fs.unlink(embeddedWasm);
      } catch {}
    }
  });

actorCmd
  .command('deploy <dir>')
  .description('Deploy actor to Cloudflare Containers')
  .action(async (dir: string) => {
    const compDir = path.resolve(process.cwd(), dir);
    console.log(`🚀 Deploying Actor at ${compDir}...`);

    try {
      await execa('npx', ['wrangler', 'deploy'], {
        cwd: compDir,
        stdio: 'inherit',
      });
      console.log('✅ Deployment complete.');
    } catch (error) {
      console.error('❌ Actor deploy failed.', error);
      process.exit(1);
    }
  });
