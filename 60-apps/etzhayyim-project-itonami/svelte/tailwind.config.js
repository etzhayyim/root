/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        'gv2-bg-primary': '#0f1115',
        'gv2-bg-secondary': '#1a1d24',
        'gv2-bg-tertiary': '#242831',
        'gv2-text-primary': '#f1f5f9',
        'gv2-text-secondary': '#94a3b8',
        'gv2-text-tertiary': '#64748b',
        'gv2-accent': '#3b82f6',
        'gv2-border': '#334155'
      }
    }
  },
  plugins: []
};
