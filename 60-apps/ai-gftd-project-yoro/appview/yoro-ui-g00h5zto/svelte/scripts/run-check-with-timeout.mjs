import { spawn } from 'node:child_process';

const [tool, configPath] = process.argv.slice(2);

if (!tool || !configPath) {
	console.error('usage: node scripts/run-check-with-timeout.mjs <tsc|svelte-check> <tsconfig>');
	process.exit(2);
}

const defaultTimeoutMs = tool === 'svelte-check' ? 30000 : 15000;
const timeoutMs = Number(process.env.CHECK_TIMEOUT_MS || defaultTimeoutMs);

const commandMap = {
	tsc: [process.execPath, ['./node_modules/typescript/bin/tsc', '-p', configPath, '--noEmit']],
	'svelte-check': [process.execPath, ['./node_modules/svelte-check/bin/svelte-check', '--tsconfig', configPath]],
};

const command = commandMap[tool];
if (!command) {
	console.error(`unsupported tool: ${tool}`);
	process.exit(2);
}

const [bin, args] = command;
const child = spawn(bin, args, {
	stdio: 'inherit',
	env: process.env,
});

let timedOut = false;
const timer = setTimeout(() => {
	timedOut = true;
	child.kill('SIGTERM');
}, timeoutMs);

child.on('close', (code, signal) => {
	clearTimeout(timer);
	if (timedOut) {
		console.error(
			`[check-timeout] ${tool} exceeded ${timeoutMs}ms with ${configPath}. ` +
			'The focused check config returned control, but the checker did not finish. ' +
			'Investigate remaining type-graph hotspots before widening the scope.',
		);
		process.exit(124);
	}
	if (signal) {
		process.exit(1);
	}
	process.exit(code ?? 1);
});
