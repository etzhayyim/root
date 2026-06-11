import { writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import esbuild from 'esbuild';
import type { Adapter, Builder } from '@sveltejs/kit';

const __dirname = dirname(fileURLToPath(import.meta.url));

export interface AdapterOptions {
	runtime?: 'javy' | 'tinygo-qjs';
	out?: string;
}

export default function (options: AdapterOptions = {}): Adapter {
	const { runtime = 'javy', out = 'build' } = options;

	return {
		name: '@etzhayyim/sveltejs-adapter-wasm',
		async adapt(builder) {
			const tmp = builder.getBuildDirectory('wasm');

			builder.log.minor('Cleaning build directory...');
			builder.rimraf(out);
			builder.mkdirp(out);

			builder.log.minor('Copying assets...');
			builder.writeClient(join(out, 'client'));
			builder.writePrerendered(join(out, 'prerendered'));

			builder.log.minor('Generating server bundle...');
			await builder.writeServer(tmp);

			const server_entry = join(tmp, 'index.js');
			const manifest = join(tmp, 'manifest.js');

			// Find the runtime handler relative to this file's location in the package
			const runtime_path = join(__dirname, '../src/runtime/handler.js');

			// Bundle the server-side code into a single file suitable for QuickJS
			await esbuild.build({
				entryPoints: [runtime_path],
				outfile: join(out, 'index.js'),
				bundle: true,
				minify: true,
				format: 'esm',
				platform: 'browser', // QuickJS doesn't have Node APIs
				external: ['node:crypto'],
				define: {
					'process.env.NODE_ENV': '"production"'
				},
				alias: {
					$server: server_entry,
					$manifest: manifest
				}
			});

			if (runtime === 'javy') {
				builder.log.minor('Compiling with Javy...');
				const javy = '/usr/local/bin/javy';
				const input = join(out, 'index.js');
				const output = join(out, 'component.wasm');
				
				// Javy v8+ uses 'build' command to create a component
				builder.log.minor(`Executing: ${javy} build ${input} -o ${output}`);
				try {
					const { execSync } = await import('node:child_process');
					execSync(`${javy} build ${input} -o ${output}.core`);
					
					// Wrap core module into a component with WASI 0.2.0 support using the adapter
					builder.log.minor('Adapting to WASI 0.2.0 component with Preview 1 adapter...');
					const adapter_path = join(__dirname, '../src/runtime/adapter.wasm');
					execSync(`npx wasm-tools component new ${output}.core -o ${output} --adapt wasi_snapshot_preview1=${adapter_path}`);
					
					builder.log.minor(`Javy build and component adaptation successful: ${output}`);
				} catch (e: any) {
					builder.log.error(`Javy build failed: ${e.message}`);
				}
			} else if (runtime === 'tinygo-qjs') {
				builder.log.minor('Preparing TinyGo orchestration build...');
				const runtime_dir = fileURLToPath(new URL('../../wasm/runtime', import.meta.url));
				const build_dir = join(runtime_dir, 'build');
				
				builder.rimraf(build_dir);
				builder.mkdirp(build_dir);

				// Copy all build artifacts (index.js, client/, prerendered/) to TinyGo build directory
				const { cpSync } = await import('node:fs');
				try {
					cpSync(out, build_dir, { recursive: true });
					builder.log.minor(`Copied build artifacts to ${build_dir}`);
				} catch (e: any) {
					builder.log.error(`Failed to copy build artifacts: ${e.message}`);
				}
				
				builder.log.info('Ready to build TinyGo performer: wash build inside projects/sveltejs-adapter-wasm/wasm/runtime');
			}
		}
	};
}
