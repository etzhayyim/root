import { etzhayyimUIKit } from '@etzhayyim/design-system/plugin';

/** @type {import('tailwindcss').Config} */
export default {
	content: [
		'./src/**/*.{html,js,svelte,ts}',
		'../../../../../packages/ts/design-system/dist/**/*.{svelte,js}',
		'../../../../../packages/ts/design-system/dist/**/*.{svelte,js}'
	],
	darkMode: ['selector', '[data-theme="dark"]'],
	theme: {
		extend: {
			colors: {
				pharma: {
					bg: '#f8faf8',
					surface: '#ffffff',
					card: '#ffffff',
					text: '#1a1a1a',
					muted: '#6b7280',
					accent: '#059669',
					'accent-hover': '#047857',
					border: '#e5e7eb',
					otc1: '#dc2626',
					otc2d: '#ea580c',
					otc2: '#16a34a',
					otc3: '#2563eb',
					supplement: '#8b5cf6',
					cosmetic: '#ec4899',
					warning: '#f59e0b',
					danger: '#ef4444'
				}
			},
			fontFamily: {
				sans: ["'Noto Sans JP'", '-apple-system', 'BlinkMacSystemFont', "'Segoe UI'", 'sans-serif']
			}
		}
	},
	plugins: [etzhayyimUIKit]
};
