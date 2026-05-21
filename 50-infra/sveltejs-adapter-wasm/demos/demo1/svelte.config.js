import adapter from '@etzhayyim/sveltejs-adapter-wasm';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	kit: {
		adapter: adapter()
	}
};

export default config;
