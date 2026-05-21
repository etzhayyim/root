import plugin from 'tailwindcss/plugin';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gftdUIKit } from '@etzhayyim/design-system/plugin';

const rootDir = fileURLToPath(new URL('.', import.meta.url));
const designSystemDist = path.resolve(
  rootDir,
  'node_modules/@etzhayyim/design-system/dist/**/*.{svelte,js}'
);

export default {
  content: ['./src/**/*.{html,js,svelte,ts}', designSystemDist],
  theme: {
    extend: {
      colors: {
        gftd: {
          bg: 'var(--gv2-bg-primary)',
          text: 'var(--gv2-text-primary)',
          secondary: 'var(--gv2-text-secondary)',
          muted: 'var(--gv2-text-muted)',
          accent: 'var(--gv2-accent)',
          border: 'var(--gv2-border)',
          card: 'var(--gv2-bg-card)',
        },
      },
    },
  },
  plugins: [
    gftdUIKit,
    plugin(({ addBase }) => {
      addBase({
        ':root': {
          '--gv2-bg-primary': '#0a0a0a',
          '--gv2-bg-card': '#141414',
          '--gv2-text-primary': '#e8e8e8',
          '--gv2-text-secondary': '#9a9a9a',
          '--gv2-text-muted': '#5a5a5a',
          '--gv2-border': '#262626',
          '--gv2-accent': '#6366f1',
        },
        'html, body': { 'min-height': '100vh' },
      });
    }),
  ],
};
