import plugin from 'tailwindcss/plugin';
import { etzhayyimUIKit } from '@etzhayyim/design-system/plugin';

export default {
	content: [
		'./src/**/*.{html,js,svelte,ts}',
		'../../../../../packages/ts/design-system/dist/**/*.{svelte,js}',
		'../../../../../packages/ts/design-system/dist/**/*.{svelte,js}',
	],
	theme: {
		extend: {
			colors: {
				etzhayyim: {
					bg: 'var(--gv2-bg-primary)',
					text: 'var(--gv2-text-primary)',
					secondary: 'var(--gv2-text-secondary)',
					muted: 'var(--gv2-text-muted)',
					accent: 'var(--gv2-accent)',
					border: 'var(--gv2-border)',
					hover: 'var(--gv2-bg-hover)',
					input: 'var(--gv2-bg-input)',
					card: 'var(--gv2-bg-card)',
				},
			},
		},
	},
	plugins: [
		etzhayyimUIKit,
		plugin(({ addBase }) => {
			addBase({
				':root': {
					'--gv2-bg-primary': '#0a0a0a',
					'--gv2-text-primary': '#f5f5f5',
					'--gv2-text-secondary': '#a0a0a0',
					'--gv2-text-muted': '#666666',
					'--gv2-border': '#2f2f2f',
					'--gv2-accent': '#d4a017',
					'--gv2-bg-hover': '#1a1a1a',
					'--gv2-bg-input': '#141414',
					'--gv2-bg-card': '#141414',
					'--gv2-header-height': '48px',
					'--gv2-sidebar-width': '0px',
					'--safe-area-bottom': 'env(safe-area-inset-bottom, 0px)',
				},
				'html, body': { height: '100%', overflow: 'hidden' },
				'button, input, select, textarea, a': { 'touch-action': 'manipulation' },
			});
		}),
	],
};
