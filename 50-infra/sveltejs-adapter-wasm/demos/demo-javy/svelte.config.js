import adapter from '@gftdcojp/sveltejs-adapter-wasm';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter({ runtime: 'javy' })
	}
};

export default config;
