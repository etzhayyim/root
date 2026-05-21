import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		// In dev, proxy yatabase.gftd.ai surfaces (XRPC + storage + auth) to
		// production so the Studio can be developed against real data
		// without standing up a local Worker. Override per-developer via
		// VITE_YATABASE_ORIGIN.
		proxy: process.env.VITE_YATABASE_ORIGIN
			? {
					'/xrpc': { target: process.env.VITE_YATABASE_ORIGIN, changeOrigin: true },
					'/storage': { target: process.env.VITE_YATABASE_ORIGIN, changeOrigin: true },
					'/auth': { target: process.env.VITE_YATABASE_ORIGIN, changeOrigin: true },
					'/api': { target: process.env.VITE_YATABASE_ORIGIN, changeOrigin: true },
					'/cypher': { target: process.env.VITE_YATABASE_ORIGIN, changeOrigin: true },
					'/mcp': { target: process.env.VITE_YATABASE_ORIGIN, changeOrigin: true },
				}
			: undefined,
	},
});
