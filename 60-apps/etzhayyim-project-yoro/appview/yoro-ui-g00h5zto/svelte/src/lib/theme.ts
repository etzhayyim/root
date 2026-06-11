import { derived, get, writable } from 'svelte/store';

export type Theme = 'dark' | 'light' | 'system' | 'midnight' | 'sakura' | 'forest' | 'ocean' | 'sunset' | 'slate';

export type ColorTheme = Exclude<Theme, 'system'>;

export interface ThemeMeta {
  label: string;
  swatch: string;
  dark: boolean;
}

export const ALL_THEMES: ColorTheme[] = ['dark', 'light', 'midnight', 'sakura', 'forest', 'ocean', 'sunset', 'slate'];

export const THEME_META: Record<ColorTheme, ThemeMeta> = {
  dark:     { label: 'Dark',     swatch: '#1a1a1a', dark: true },
  light:    { label: 'Light',    swatch: '#ffffff', dark: false },
  midnight: { label: 'Midnight', swatch: '#0f0f1a', dark: true },
  sakura:   { label: 'Sakura',   swatch: '#fdf2f5', dark: false },
  forest:   { label: 'Forest',   swatch: '#0d1a0f', dark: true },
  ocean:    { label: 'Ocean',    swatch: '#0a1628', dark: true },
  sunset:   { label: 'Sunset',   swatch: '#1a0f0a', dark: true },
  slate:    { label: 'Slate',    swatch: '#1e293b', dark: true },
};

const STORAGE_KEY = 'gv2-theme';

function getSystemTheme(): 'dark' | 'light' {
  if (typeof window === 'undefined') {
    return 'dark';
  }
  return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
}

function getInitialTheme(): Theme {
  if (typeof window === 'undefined') {
    return 'dark';
  }
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored && ALL_THEMES.includes(stored as ColorTheme)) {
    return stored as Theme;
  }
  if (stored === 'system') return 'system';
  return 'dark';
}

function resolveThemeValue(t: Theme): ColorTheme {
  return t === 'system' ? getSystemTheme() : t;
}

function applyTheme(nextTheme: Theme): void {
  if (typeof document === 'undefined') {
    return;
  }
  const resolved = resolveThemeValue(nextTheme);
  document.documentElement.setAttribute('data-theme', resolved);
}

export const theme = writable<Theme>(getInitialTheme());

export const resolvedTheme = derived(theme, ($theme) => {
  return resolveThemeValue($theme);
});

if (typeof window !== 'undefined') {
  theme.subscribe((nextTheme) => {
    applyTheme(nextTheme);
    localStorage.setItem(STORAGE_KEY, nextTheme);
  });

  window.matchMedia('(prefers-color-scheme: light)').addEventListener('change', () => {
    const current = get(theme);
    if (current === 'system') {
      applyTheme('system');
    }
  });
}

export function setTheme(nextTheme: Theme): void {
  theme.set(nextTheme);
}

export function toggleTheme(): void {
  theme.update((currentTheme) => {
    const currentResolved = resolveThemeValue(currentTheme);
    return currentResolved === 'dark' ? 'light' : 'dark';
  });
}
