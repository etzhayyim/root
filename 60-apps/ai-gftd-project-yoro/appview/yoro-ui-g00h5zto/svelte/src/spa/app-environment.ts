export const browser = typeof window !== 'undefined';
export const dev = !!import.meta.env.DEV;
export const building = false;
export const version = String(import.meta.env.VITE_APP_VERSION ?? '');
