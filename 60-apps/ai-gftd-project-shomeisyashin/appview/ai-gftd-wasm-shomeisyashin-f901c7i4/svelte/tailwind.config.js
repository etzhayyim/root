import { gftdUIKit } from '@gftdcojp/design-system/plugin';

/** @type {import('tailwindcss').Config} */
export default {
	content: [
		'./src/**/*.{html,js,svelte,ts}',
		'../../../../../../packages/ts/design-system/dist/**/*.{svelte,js}',
		'../../../../../../packages/ts/design-system/dist/**/*.{svelte,js}'
	],
	theme: { extend: {} },
	plugins: [gftdUIKit]
};
