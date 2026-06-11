/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{html,js,svelte,ts}'],
  theme: {
    extend: {
      colors: {
        bami: {
          bg: '#0a0a0f',
          surface: '#14141f',
          'surface-hover': '#1e1e2e',
          text: '#e8e8f0',
          muted: '#8888aa',
          accent: '#7c3aed',
          'accent-hover': '#8b5cf6',
          pink: '#ec4899',
          cyan: '#06b6d4',
          border: '#2a2a3a',
          card: '#18182a',
          live: '#ef4444',
          gold: '#f59e0b'
        }
      }
    }
  },
  plugins: []
};
