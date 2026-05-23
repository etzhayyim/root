import { readFileSync } from 'fs';
import { createServer } from 'http';
import { join } from 'path';

const PORT = process.env.PORT || 3000;
const BUILD_DIR = join(import.meta.dirname, 'build');

const envScript = `<script>window.__ENV__ = ${JSON.stringify({
	VITE_GRPC_API_URL: process.env.VITE_GRPC_API_URL || '/'
})}</script>`;

createServer((req, res) => {
	const url = new URL(req.url, `http://localhost:${PORT}`);
	let filePath = join(BUILD_DIR, url.pathname);

	try {
		const stat = require('fs').statSync(filePath);
		if (stat.isDirectory()) filePath = join(filePath, 'index.html');
	} catch {
		filePath = join(BUILD_DIR, 'index.html');
	}

	try {
		let content = readFileSync(filePath);
		const ext = filePath.split('.').pop();
		const mimeTypes = {
			html: 'text/html',
			js: 'application/javascript',
			css: 'text/css',
			svg: 'image/svg+xml',
			json: 'application/json',
			png: 'image/png',
			ico: 'image/x-icon'
		};
		const contentType = mimeTypes[ext] || 'application/octet-stream';

		if (ext === 'html') {
			content = content.toString().replace('</head>', `${envScript}</head>`);
		}

		res.writeHead(200, { 'Content-Type': contentType });
		res.end(content);
	} catch {
		const html = readFileSync(join(BUILD_DIR, 'index.html'), 'utf-8');
		res.writeHead(200, { 'Content-Type': 'text/html' });
		res.end(html.replace('</head>', `${envScript}</head>`));
	}
}).listen(PORT, () => {
	console.log(`translate-ui serving on http://localhost:${PORT}`);
});
